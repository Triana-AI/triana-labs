from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from collections.abc import Callable, Iterable, Mapping
from contextlib import suppress
from decimal import Decimal
from pathlib import Path
from typing import Any, TypeVar

from .capture import redact
from .constants import UPSTREAM_COMMIT, UPSTREAM_REPOSITORY
from .serde import canonical_bytes

CHECKPOINT_DOMAIN = b"tau2-luna-cloud-checkpoint:v1\0"
CHECKPOINT_SCHEMA = "tau2-luna-cloud-checkpoint/v1"
EXPECTED_MODEL_IDENTITY = {
    "model_name": "gpt-5.6-luna",
    "model_version": "2026-07-09",
    "sku": "GlobalStandard",
}
INPUT_PRICE_PER_MILLION_USD = Decimal("1.00")
OUTPUT_PRICE_PER_MILLION_USD = Decimal("6.00")
DEFAULT_INPUT_TOKEN_CEILING = 80_000
DEFAULT_OUTPUT_TOKEN_CEILING = 70_000
EXPECTED_RETAIL_TASK_COUNT = 114

RemoteAppend = Callable[[str, bytes, str], None]
T = TypeVar("T")


class DurableAppendError(RuntimeError):
    pass


class BudgetExhausted(RuntimeError):
    pass


class CheckpointInvalid(RuntimeError):
    pass


class RelayMismatch(RuntimeError):
    pass


class ModelIdentityError(RuntimeError):
    pass


class Tau2DataError(RuntimeError):
    pass


def _safe_line(value: Any, secrets: tuple[str, ...]) -> bytes:
    return canonical_bytes(redact(value, secrets=secrets)) + b"\n"


class _DurableSink:
    def __init__(
        self,
        *,
        remote_append: RemoteAppend,
        object_name: str,
        secrets: Iterable[str] = (),
    ) -> None:
        self.remote_append = remote_append
        self.object_name = object_name
        self.secrets = tuple(value for value in secrets if value)
        self._poison: BaseException | None = None
        self._lock = threading.Lock()

    def _upload(self, value: Any, lane: str) -> None:
        if self._poison is not None:
            raise DurableAppendError(
                f"durable {lane} sink is poisoned after an upload failure"
            ) from self._poison
        line = _safe_line(value, self.secrets)
        try:
            self.remote_append(self.object_name, line, hashlib.sha256(line).hexdigest())
        except BaseException as exc:
            self._poison = exc
            raise DurableAppendError(f"synchronous durable {lane} upload failed") from exc


class DurableEventSink(_DurableSink):
    """Local event append followed by synchronous remote durability before return."""

    def __init__(
        self, *, local_append: Callable[[str, dict[str, Any]], dict[str, Any]], **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.local_append = local_append

    def __call__(self, event_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            safe_payload = redact(payload, secrets=self.secrets)
            if not isinstance(safe_payload, dict):
                raise DurableAppendError("event payload did not serialize as an object")
            record = self.local_append(event_name, safe_payload)
            self._upload(record, "event")
            return record


class DurableSpanSink(_DurableSink):
    """Local span append followed by synchronous remote durability before return."""

    def __init__(
        self,
        *,
        local_append: Callable[[dict[str, Any]], Any],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.local_append = local_append

    def __call__(self, span: dict[str, Any]) -> Any:
        with self._lock:
            safe_span = redact(span, secrets=self.secrets)
            if not isinstance(safe_span, dict):
                raise DurableAppendError("span did not serialize as an object")
            result = self.local_append(safe_span)
            self._upload(safe_span, "span")
            return result


class ModelCallBudget:
    """Pre-egress reservations using the frozen conservative Luna price ceiling."""

    def __init__(
        self,
        *,
        max_calls: int = 6,
        reservation_per_call_usd: Decimal = Decimal("0.50"),
        model_cap_usd: Decimal = Decimal("3.00"),
        input_token_ceiling: int = DEFAULT_INPUT_TOKEN_CEILING,
        output_token_ceiling: int = DEFAULT_OUTPUT_TOKEN_CEILING,
        monotonic: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
        minimum_interval_seconds: float = 30.0,
    ) -> None:
        if max_calls != 6:
            raise ValueError("the cloud smoke requires exactly six reserved model calls")
        if reservation_per_call_usd != Decimal("0.50") or model_cap_usd != Decimal("3.00"):
            raise ValueError("the cloud smoke requires $0.50 per call and a $3.00 model cap")
        if input_token_ceiling < 0 or output_token_ceiling <= 0:
            raise ValueError("token ceilings must be positive")
        if minimum_interval_seconds <= 0:
            raise ValueError("model call pacing interval must be positive")
        worst_case = (
            Decimal(input_token_ceiling) * INPUT_PRICE_PER_MILLION_USD
            + Decimal(output_token_ceiling) * OUTPUT_PRICE_PER_MILLION_USD
        ) / Decimal(1_000_000)
        if worst_case > reservation_per_call_usd:
            raise ValueError("token ceilings exceed the per-call USD reservation")
        self.max_calls = max_calls
        self.reservation_per_call_usd = reservation_per_call_usd
        self.model_cap_usd = model_cap_usd
        self.input_token_ceiling = input_token_ceiling
        self.output_token_ceiling = output_token_ceiling
        self.monotonic = monotonic
        self.sleeper = sleeper
        self.minimum_interval_seconds = minimum_interval_seconds
        self.admitted_calls = 0
        self.reserved_usd = Decimal("0.00")
        self._last_egress_at: float | None = None
        self._lock = threading.Lock()

    def call(self, provider: Callable[..., T], /, *args: Any, **kwargs: Any) -> T:
        with self._lock:
            next_reserved = self.reserved_usd + self.reservation_per_call_usd
            if self.admitted_calls >= self.max_calls or next_reserved > self.model_cap_usd:
                raise BudgetExhausted("six-call / USD 3.00 model reservation exhausted before egress")
            requested = kwargs.get("max_completion_tokens", self.output_token_ceiling)
            if not isinstance(requested, int) or requested <= 0 or requested > self.output_token_ceiling:
                raise BudgetExhausted("requested output tokens exceed the pre-egress output ceiling")
            input_bytes = len(
                canonical_bytes(
                    {
                        "messages": kwargs.get("messages", []),
                        "tools": kwargs.get("tools", []),
                        "tool_choice": kwargs.get("tool_choice"),
                    }
                )
            )
            if input_bytes > self.input_token_ceiling:
                raise BudgetExhausted(
                    "serialized input byte upper bound exceeds the pre-egress input token ceiling"
                )
            kwargs.setdefault("max_completion_tokens", self.output_token_ceiling)
            self.admitted_calls += 1
            self.reserved_usd = next_reserved
            now = self.monotonic()
            if self._last_egress_at is not None:
                next_egress_at = self._last_egress_at + self.minimum_interval_seconds
                remaining = next_egress_at - now
                while remaining > 0:
                    self.sleeper(remaining)
                    now = self.monotonic()
                    remaining = next_egress_at - now
            self._last_egress_at = now
        return provider(*args, **kwargs)


def _verify_checkpoint(checkpoint: Mapping[str, Any], *, task_id: str, trial: int) -> None:
    supplied = checkpoint.get("checkpoint_hash")
    unhashed = dict(checkpoint)
    unhashed.pop("checkpoint_hash", None)
    expected = hashlib.sha256(CHECKPOINT_DOMAIN + canonical_bytes(unhashed)).hexdigest()
    if supplied != expected:
        raise CheckpointInvalid("checkpoint hash mismatch")
    if checkpoint.get("schema_version") != CHECKPOINT_SCHEMA:
        raise CheckpointInvalid("checkpoint schema mismatch")
    if checkpoint.get("task_id") != task_id or checkpoint.get("trial") != trial:
        raise CheckpointInvalid("checkpoint task or trial mismatch")
    if not isinstance(checkpoint.get("attempts"), list):
        raise CheckpointInvalid("checkpoint attempts must be a list")


def plan_resume(
    checkpoint: Mapping[str, Any],
    *,
    task_id: str,
    trial: int,
    attempt_id_factory: Callable[[], str],
    verify_completed: Callable[[Mapping[str, Any]], bool],
) -> dict[str, Any]:
    _verify_checkpoint(checkpoint, task_id=task_id, trial=trial)
    attempts = checkpoint["attempts"]
    retained: list[str] = []
    for attempt in attempts:
        if not isinstance(attempt, Mapping) or not isinstance(attempt.get("attempt_id"), str):
            raise CheckpointInvalid("checkpoint contains an invalid attempt")
        attempt_id = str(attempt["attempt_id"])
        retained.append(attempt_id)
        if attempt.get("state") == "COMPLETED":
            if not verify_completed(attempt):
                raise CheckpointInvalid("completed attempt could not be deterministically verified")
            return {"action": "SKIP_VERIFIED_COMPLETED", "attempt_id": attempt_id}
        if attempt.get("state") != "PARTIAL":
            raise CheckpointInvalid("checkpoint attempt state is invalid")
    new_attempt = attempt_id_factory()
    if not new_attempt or new_attempt in retained:
        raise CheckpointInvalid("new attempt identity is empty or already retained")
    return {
        "action": "START_NEW_ATTEMPT",
        "attempt_id": new_attempt,
        "retained_attempt_ids": retained,
    }


def relay_verified_inventory(
    *,
    remote_list: Callable[[str], list[str]],
    remote_download: Callable[[str], bytes],
    checkpoint: Mapping[str, Any],
    destination: Path,
    secret_values: Iterable[str] = (),
) -> dict[str, Any]:
    prefix = checkpoint.get("prefix")
    inventory = checkpoint.get("inventory")
    if not isinstance(prefix, str) or not prefix or not isinstance(inventory, list):
        raise RelayMismatch("relay checkpoint is malformed")
    declared: dict[str, Mapping[str, Any]] = {}
    for item in inventory:
        if not isinstance(item, Mapping):
            raise RelayMismatch("relay inventory item is malformed")
        remote_name = item.get("remote_name")
        local_name = item.get("local_name")
        if (
            not isinstance(remote_name, str)
            or not remote_name.startswith(prefix)
            or not isinstance(local_name, str)
            or Path(local_name).is_absolute()
            or ".." in Path(local_name).parts
            or remote_name in declared
        ):
            raise RelayMismatch("relay inventory identity is unsafe or duplicated")
        declared[remote_name] = item
    remote_names = remote_list(prefix)
    if remote_names != sorted(declared):
        raise RelayMismatch("remote inventory differs from checkpoint")
    secrets = tuple(value.encode() for value in secret_values if value)
    downloaded: dict[str, bytes] = {}
    local_names: set[str] = set()
    for remote_name in remote_names:
        item = declared[remote_name]
        local_name = str(item["local_name"])
        if local_name in local_names:
            raise RelayMismatch("local inventory names collide")
        local_names.add(local_name)
        data = remote_download(remote_name)
        if len(data) != item.get("size") or hashlib.sha256(data).hexdigest() != item.get("sha256"):
            raise RelayMismatch("remote object size or hash mismatch")
        if any(secret in data for secret in secrets):
            raise RelayMismatch("secret reflection detected in remote evidence")
        downloaded[local_name] = data
    try:
        destination.mkdir(parents=True, exist_ok=False)
        for local_name, data in sorted(downloaded.items()):
            local_path = destination / local_name
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with local_path.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
    except OSError as exc:
        raise RelayMismatch("local relay publication failed") from exc
    projected = [dict(item) for item in inventory]
    return {"valid": True, "remote_inventory": projected, "local_inventory": projected}


def validate_model_identity(identity: Mapping[str, Any]) -> None:
    if dict(identity) != EXPECTED_MODEL_IDENTITY:
        raise ModelIdentityError("Azure deployment is not exact gpt-5.6-luna 2026-07-09 GlobalStandard")


def validate_tau2_data_directory(root: Path) -> dict[str, Any]:
    try:
        marker = json.loads((root / ".tau2-source.json").read_text(encoding="utf-8"))
        tasks = json.loads(
            (root / "data" / "tau2" / "domains" / "retail" / "tasks.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Tau2DataError("tau2 source marker or retail task inventory is absent") from exc
    if marker != {"repository": UPSTREAM_REPOSITORY, "commit": UPSTREAM_COMMIT}:
        raise Tau2DataError("tau2 source marker does not match the frozen repository and commit")
    if not isinstance(tasks, list) or len(tasks) != EXPECTED_RETAIL_TASK_COUNT:
        raise Tau2DataError("tau2 retail inventory must contain exactly 114 tasks")
    return {"commit": UPSTREAM_COMMIT, "retail_task_count": len(tasks)}


def preflight_model_call(
    *, provider: Callable[[], T], tau2_data_dir: Path, model_identity: Mapping[str, Any]
) -> T:
    validate_model_identity(model_identity)
    validate_tau2_data_directory(tau2_data_dir)
    return provider()


def run_with_deallocation(
    *,
    execute: Callable[[], T],
    finalize: Callable[[BaseException | None], None],
    deallocate: Callable[[], None],
) -> T:
    primary: BaseException | None = None
    result: T | None = None
    try:
        result = execute()
    except BaseException as exc:
        primary = exc
    try:
        finalize(primary)
    except BaseException as exc:
        if primary is None:
            primary = exc
    try:
        deallocate()
    except BaseException as exc:
        if primary is None:
            primary = exc
    if primary is not None:
        raise primary
    return result  # type: ignore[return-value]


class AzureBlobAuthority:
    """Managed-identity Blob authority with synchronous append and immutable upload."""

    def __init__(self, *, account_url: str, container: str, credential: Any) -> None:
        from azure.storage.blob import BlobServiceClient

        service = BlobServiceClient(account_url=account_url, credential=credential)
        self._container = service.get_container_client(container)
        self._created_append_blobs: set[str] = set()
        self._lock = threading.Lock()

    def append(self, name: str, line: bytes, digest: str) -> None:
        if hashlib.sha256(line).hexdigest() != digest or not line.endswith(b"\n"):
            raise DurableAppendError("append payload digest or line framing is invalid")
        from azure.core.exceptions import ResourceExistsError

        with self._lock:
            blob = self._container.get_blob_client(name)
            if name not in self._created_append_blobs:
                with suppress(ResourceExistsError):
                    blob.create_append_blob()
                self._created_append_blobs.add(name)
            blob.append_block(line, length=len(line), validate_content=True)

    def put(self, name: str, data: bytes, *, overwrite: bool = False) -> None:
        self._container.upload_blob(
            name=name,
            data=data,
            length=len(data),
            overwrite=overwrite,
            validate_content=True,
        )

    def list(self, prefix: str) -> list[str]:
        return sorted(blob.name for blob in self._container.list_blobs(name_starts_with=prefix))

    def download(self, name: str) -> bytes:
        return self._container.download_blob(name).readall()


def managed_identity_clients(
    *,
    account_url: str,
    container: str,
    vault_url: str,
    secret_name: str,
    storage_secret_name: str,
) -> tuple[AzureBlobAuthority, str]:
    """Resolve cloud clients without accepting or printing a credential value."""
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient

    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    client = SecretClient(vault_url=vault_url, credential=credential)
    secret = client.get_secret(secret_name).value
    storage_secret = client.get_secret(storage_secret_name).value
    if not secret or not storage_secret:
        raise RuntimeError("managed identity did not resolve both required vault secrets")
    return AzureBlobAuthority(
        account_url=account_url,
        container=container,
        credential=storage_secret,
    ), secret
