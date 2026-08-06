# ruff: noqa: SIM905 -- frozen task identities are clearer as compact split strings.
from __future__ import annotations

import gzip
import hashlib
import io
import json
import tarfile
import threading
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, TypeVar

from .constants import UPSTREAM_COMMIT
from .serde import canonical_bytes

T = TypeVar("T")

DISCOVERY_TASK_IDS = tuple(map(int, (
    "1,2,5,6,7,10,11,15,16,19,21,22,23,24,25,26,27,30,32,34,37,38,39,40,46,"
    "52,53,54,56,58,61,64,65,68,71,75,80,81,83,85,86,88,90,91,94,95,96,97,99,"
    "101,103,104,107,108,109,112,113"
).split(",")))
HOLDOUT_TASK_IDS = tuple(map(int, (
    "0,3,4,8,9,12,13,14,17,18,20,28,29,31,33,35,36,41,42,43,44,45,47,48,49,50,"
    "51,55,57,59,60,62,63,66,67,69,70,72,73,74,76,77,78,79,82,84,87,89,92,93,"
    "98,100,102,105,106,110,111"
).split(",")))
AGGREGATE_MODEL_CAP_USD = Decimal("25.00")
CHECKPOINT_SCHEMA = "tau2-retail-discovery-checkpoint/v1"
CHECKPOINT_DOMAIN = b"tau2-retail-discovery-checkpoint:v1\0"
_MODEL_PRICES = {"terra": (Decimal("2.50"), Decimal("15.00")),
                 "luna": (Decimal("1.00"), Decimal("6.00"))}
_MILLION = Decimal(1_000_000)
_USD_QUANTUM = Decimal("0.000001")


class DiscoveryIdentityError(ValueError):
    pass


class HoldoutTaskRefused(DiscoveryIdentityError):
    pass


class AggregateBudgetExhausted(RuntimeError):
    pass


class RequestEvidenceInvalid(ValueError):
    pass


class DiscoveryCheckpointInvalid(ValueError):
    pass


def study_identity() -> dict[str, Any]:
    return {
        "study_id": "tau2-retail-discovery-v1",
        "panel_id": "tau2-retail-discovery-v1-seed-1729",
        "split_version": "sha256-balanced-retail-v1",
        "arm": "BASELINE_DISCOVERY",
        "domain": "retail",
        "trial": 0,
        "seed": 1729,
        "upstream_commit": UPSTREAM_COMMIT,
    }


def validate_discovery_tasks(task_ids: Sequence[int]) -> tuple[int, ...]:
    observed = tuple(task_ids)
    forbidden = sorted(set(observed).intersection(HOLDOUT_TASK_IDS))
    if forbidden:
        raise HoldoutTaskRefused(f"holdout tasks are forbidden: {forbidden}")
    if observed != DISCOVERY_TASK_IDS:
        raise DiscoveryIdentityError("57-task discovery panel order does not match frozen identity")
    return observed


def _usage(response: Any) -> tuple[int, int] | None:
    if isinstance(response, Mapping):
        projected = response
    elif callable(getattr(response, "model_dump", None)):
        projected = response.model_dump()
    elif callable(getattr(response, "to_dict", None)):
        projected = response.to_dict()
    else:
        return None
    usage = projected.get("usage") if isinstance(projected, Mapping) else None
    if not isinstance(usage, Mapping):
        return None
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    if (
        not isinstance(prompt, int)
        or isinstance(prompt, bool)
        or prompt < 0
        or not isinstance(completion, int)
        or isinstance(completion, bool)
        or completion < 0
    ):
        return None
    return prompt, completion


def _actual_cost(model: str, usage: tuple[int, int]) -> Decimal:
    input_price, output_price = _MODEL_PRICES[model]
    prompt, completion = usage
    return (
        (Decimal(prompt) * input_price + Decimal(completion) * output_price) / _MILLION
    ).quantize(_USD_QUANTUM)


@dataclass(frozen=True)
class StudyReservation:
    reservation_id: str
    model: str
    reserved_usd: Decimal


class SharedStudyBudget:
    """Thread-safe accrued-plus-outstanding authority for the whole study."""

    def __init__(
        self,
        *,
        cap_usd: Decimal = AGGREGATE_MODEL_CAP_USD,
        on_change: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        if cap_usd != AGGREGATE_MODEL_CAP_USD:
            raise ValueError("discovery aggregate model cap must be exactly USD 25.00")
        self.cap_usd = cap_usd
        self.accrued_usd = Decimal("0.00")
        self.outstanding_usd = Decimal("0.00")
        self.ledger: list[dict[str, Any]] = []
        self._reservations: dict[str, StudyReservation] = {}
        self._lock = threading.Lock()
        self._on_change = on_change

    def _projection_unlocked(self) -> dict[str, Any]:
        return {
            "cap_usd": str(self.cap_usd),
            "accrued_usd": str(self.accrued_usd),
            "outstanding_usd": str(self.outstanding_usd),
            "ledger": [
                {
                    key: str(value) if isinstance(value, Decimal) else value
                    for key, value in entry.items()
                }
                for entry in self.ledger
            ],
        }

    def restore(self, projection: Mapping[str, Any]) -> None:
        try:
            accrued = Decimal(str(projection["accrued_usd"]))
            outstanding = Decimal(str(projection["outstanding_usd"]))
            ledger = list(projection["ledger"])
        except (KeyError, TypeError, ValueError) as exc:
            raise AggregateBudgetExhausted("stored aggregate budget evidence is invalid") from exc
        if accrued < 0 or outstanding < 0 or accrued + outstanding > self.cap_usd:
            raise AggregateBudgetExhausted("stored aggregate budget exceeds USD 25.00")
        with self._lock:
            self.accrued_usd = accrued + outstanding
            self.outstanding_usd = Decimal("0.00")
            self.ledger = ledger
            if outstanding:
                self.ledger.append({
                    "model": "unknown",
                    "outcome": "CONSERVATIVE_RECOVERED_OUTSTANDING",
                    "reserved_usd": outstanding,
                    "charged_usd": outstanding,
                })
            if self._on_change is not None:
                self._on_change(self._projection_unlocked())

    def reserve(self, *, model: str, reserved_usd: Decimal) -> StudyReservation:
        if model not in _MODEL_PRICES:
            raise AggregateBudgetExhausted(f"unknown model lane cannot reserve aggregate budget: {model}")
        if not isinstance(reserved_usd, Decimal) or not reserved_usd.is_finite() or reserved_usd <= 0:
            raise AggregateBudgetExhausted("aggregate reservation must be a positive finite Decimal")
        with self._lock:
            if self.accrued_usd + self.outstanding_usd + reserved_usd > self.cap_usd:
                raise AggregateBudgetExhausted("aggregate USD 25.00 ceiling exhausted before egress")
            reservation = StudyReservation(uuid.uuid4().hex, model, reserved_usd)
            self._reservations[reservation.reservation_id] = reservation
            self.outstanding_usd += reserved_usd
            if self._on_change is not None:
                try:
                    self._on_change(self._projection_unlocked())
                except BaseException:
                    self._reservations.pop(reservation.reservation_id)
                    self.outstanding_usd -= reserved_usd
                    raise
            return reservation

    def _settle(
        self,
        reservation: StudyReservation,
        *,
        charged_usd: Decimal,
        outcome: str,
        usage: tuple[int, int] | None = None,
    ) -> None:
        exceeded_reservation = charged_usd > reservation.reserved_usd
        with self._lock:
            current = self._reservations.pop(reservation.reservation_id, None)
            if current != reservation:
                raise RuntimeError("aggregate reservation is missing or already settled")
            if charged_usd > reservation.reserved_usd:
                charged_usd = reservation.reserved_usd
                outcome = "CONSERVATIVE_USAGE_EXCEEDED_RESERVATION"
            self.outstanding_usd -= reservation.reserved_usd
            self.accrued_usd += charged_usd
            entry: dict[str, Any] = {
                "model": reservation.model,
                "outcome": outcome,
                "reserved_usd": reservation.reserved_usd,
                "charged_usd": charged_usd,
            }
            if usage is not None:
                entry.update(prompt_tokens=usage[0], completion_tokens=usage[1])
            self.ledger.append(entry)
            if self._on_change is not None:
                self._on_change(self._projection_unlocked())
        if exceeded_reservation:
            raise RuntimeError("returned usage exceeded the conservative aggregate reservation")

    def call(
        self,
        *,
        model: str,
        reserved_usd: Decimal,
        provider: Callable[[], T],
    ) -> T:
        reservation = self.reserve(model=model, reserved_usd=reserved_usd)
        try:
            response = provider()
        except BaseException:
            self._settle(
                reservation,
                charged_usd=reserved_usd,
                outcome="CONSERVATIVE_FAILED_CALL",
            )
            raise
        usage = _usage(response)
        if usage is None:
            self._settle(
                reservation,
                charged_usd=reserved_usd,
                outcome="CONSERVATIVE_MISSING_USAGE",
            )
        else:
            self._settle(
                reservation,
                charged_usd=_actual_cost(model, usage),
                outcome="ACTUAL_USAGE_DEBIT",
                usage=usage,
            )
        return response

    def projection(self) -> dict[str, Any]:
        with self._lock:
            return self._projection_unlocked()


def build_study_manifest(
    *,
    source_archive_sha256: str,
    worker_revision: str,
    model_deployments: Mapping[str, Any],
    runtime_config: Mapping[str, Any],
    custody: Mapping[str, Any],
) -> dict[str, Any]:
    if len(source_archive_sha256) != 64 or any(c not in "0123456789abcdef" for c in source_archive_sha256):
        raise DiscoveryIdentityError("source archive SHA-256 must be lowercase hexadecimal")
    if not worker_revision:
        raise DiscoveryIdentityError("worker revision is required")
    manifest = {
        **study_identity(),
        "discovery_task_ids": list(DISCOVERY_TASK_IDS),
        "holdout_task_ids": list(HOLDOUT_TASK_IDS),
        "source_archive_sha256": source_archive_sha256,
        "worker_revision": worker_revision,
        "model_deployments": dict(model_deployments),
        "runtime_config": dict(runtime_config),
        "prompt_tool_schema_evidence_policy": {
            "source": "captured model.request bytes only",
            "missing_tool_schema": "null",
            "invention_forbidden": True,
        },
        "aggregate_model_cap_usd": str(AGGREGATE_MODEL_CAP_USD),
        "custody": dict(custody),
    }
    manifest["manifest_sha256"] = hashlib.sha256(canonical_bytes(manifest)).hexdigest()
    return manifest


def project_request_hashes(captured_request: bytes) -> dict[str, str | None]:
    try:
        request = json.loads(captured_request)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RequestEvidenceInvalid("captured request is not valid JSON") from exc
    if not isinstance(request, dict) or not isinstance(request.get("messages"), list):
        raise RequestEvidenceInvalid("captured request has no observable messages list")
    tools = request.get("tools")
    if tools is not None and not isinstance(tools, list):
        raise RequestEvidenceInvalid("captured tools are not a list")
    return {
        "observed_prompt_sha256": hashlib.sha256(
            canonical_bytes(request["messages"])
        ).hexdigest(),
        "observed_tool_schema_sha256": (
            hashlib.sha256(canonical_bytes(tools)).hexdigest() if tools is not None else None
        ),
        "captured_request_sha256": hashlib.sha256(captured_request).hexdigest(),
    }


def _archive_bytes(artifacts: Mapping[str, bytes]) -> bytes:
    output = io.BytesIO()
    with (
        gzip.GzipFile(fileobj=output, mode="wb", filename="", mtime=0) as compressed,
        tarfile.open(fileobj=compressed, mode="w") as archive,
    ):
        for name, data in sorted(artifacts.items()):
            if not name or name.startswith("/") or ".." in name.split("/"):
                raise ValueError(f"unsafe archive artifact name: {name}")
            if not isinstance(data, bytes):
                raise TypeError(f"archive artifact must be bytes: {name}")
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mtime = 0
            info.mode = 0o600
            archive.addfile(info, io.BytesIO(data))
    return output.getvalue()


def publish_terminal_evidence(
    *,
    study_id: str,
    terminal_state: str,
    artifacts: Mapping[str, bytes],
    put: Callable[..., Any],
) -> dict[str, str]:
    if study_id != study_identity()["study_id"]:
        raise DiscoveryIdentityError("terminal evidence study identity mismatch")
    if terminal_state not in {"COMPLETED", "PARTIAL", "BUDGET_STOP", "FAILED"}:
        raise ValueError("terminal state is invalid")
    inventory = [
        {"name": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for name, data in sorted(artifacts.items())
    ]
    archive = _archive_bytes(artifacts)
    archive_hash = hashlib.sha256(archive).hexdigest()
    prefix = f"studies/{study_id}"
    archive_name = f"{prefix}/archives/{archive_hash}.tar.gz"
    manifest_name = f"{prefix}/archives/{archive_hash}.manifest.json"
    status_name = f"{prefix}/status.json"
    archive_manifest = {
        "study_id": study_id,
        "terminal_state": terminal_state,
        "archive_sha256": archive_hash,
        "inventory": inventory,
    }
    status = {
        "study_id": study_id,
        "state": terminal_state,
        "archive_object": archive_name,
        "archive_manifest_object": manifest_name,
        "archive_sha256": archive_hash,
    }
    put(archive_name, archive, overwrite=False)
    put(manifest_name, canonical_bytes(archive_manifest) + b"\n", overwrite=False)
    put(status_name, canonical_bytes(status) + b"\n", overwrite=True)
    return {
        "archive_object": archive_name,
        "archive_manifest_object": manifest_name,
        "archive_sha256": archive_hash,
        "status_object": status_name,
    }


def checkpoint_object_name(run_id: str, task_id: int) -> str:
    if not run_id or task_id not in DISCOVERY_TASK_IDS:
        raise DiscoveryIdentityError("checkpoint requires discovery run and task identity")
    return f"runs/{run_id}/tasks/{task_id}/checkpoint.json"


def hash_checkpoint(
    *, task_id: str, trial: int, attempts: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    if not task_id.isdigit() or int(task_id) not in DISCOVERY_TASK_IDS or trial != 0:
        raise DiscoveryCheckpointInvalid("checkpoint task or trial is not discovery identity")
    checkpoint = {
        "schema_version": CHECKPOINT_SCHEMA,
        "task_id": task_id,
        "trial": trial,
        "attempts": [dict(attempt) for attempt in attempts],
    }
    checkpoint["checkpoint_hash"] = hashlib.sha256(
        CHECKPOINT_DOMAIN + canonical_bytes(checkpoint)
    ).hexdigest()
    return checkpoint


def _validate_checkpoint(checkpoint: Mapping[str, Any], *, task_id: str, trial: int) -> None:
    unsigned = dict(checkpoint)
    supplied = unsigned.pop("checkpoint_hash", None)
    expected = hashlib.sha256(CHECKPOINT_DOMAIN + canonical_bytes(unsigned)).hexdigest()
    if (
        supplied != expected
        or checkpoint.get("schema_version") != CHECKPOINT_SCHEMA
        or checkpoint.get("task_id") != task_id
        or checkpoint.get("trial") != trial
        or not isinstance(checkpoint.get("attempts"), list)
    ):
        raise DiscoveryCheckpointInvalid("discovery checkpoint identity or hash is invalid")


def plan_discovery_resume(
    checkpoint: Mapping[str, Any],
    *,
    task_id: str,
    trial: int,
    attempt_id_factory: Callable[[], str],
    verify_completed: Callable[[Mapping[str, Any]], bool],
) -> dict[str, Any]:
    _validate_checkpoint(checkpoint, task_id=task_id, trial=trial)
    attempts = checkpoint["attempts"]
    for attempt in attempts:
        if not isinstance(attempt, Mapping):
            raise DiscoveryCheckpointInvalid("discovery attempt is malformed")
        if attempt.get("state") == "COMPLETED":
            if verify_completed(attempt):
                return {
                    "action": "SKIP_VERIFIED_COMPLETED",
                    "attempt_id": attempt.get("attempt_id"),
                    "retained_attempt_ids": [item.get("attempt_id") for item in attempts],
                }
            raise DiscoveryCheckpointInvalid("completed attempt failed remote verification")
    attempt_id = attempt_id_factory()
    if not isinstance(attempt_id, str) or not attempt_id:
        raise DiscoveryCheckpointInvalid("new attempt identity is empty")
    return {
        "action": "START_NEW_ATTEMPT",
        "attempt_id": attempt_id,
        "retained_attempt_ids": [attempt.get("attempt_id") for attempt in attempts],
    }
