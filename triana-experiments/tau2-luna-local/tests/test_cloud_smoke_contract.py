from __future__ import annotations

import hashlib
import importlib.util
import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from conftest import SECRET, canonical_bytes
from test_capture import FakeResponse

CLOUD_MODULE = "tau2_luna_local.cloud_smoke"
CHECKPOINT_DOMAIN = b"tau2-luna-cloud-checkpoint:v1\0"


def test_cloud_smoke_module_exists() -> None:
    assert importlib.util.find_spec(CLOUD_MODULE) is not None, (
        "resumable cloud-smoke production behavior is not implemented"
    )


@pytest.fixture(autouse=True)
def require_cloud_module(request: pytest.FixtureRequest) -> None:
    is_sentinel = request.node.name == "test_cloud_smoke_module_exists"
    if not is_sentinel and importlib.util.find_spec(CLOUD_MODULE) is None:
        pytest.skip("cloud-smoke module absent; test_cloud_smoke_module_exists owns the RED signal")


def checkpoint(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result["checkpoint_hash"] = hashlib.sha256(
        CHECKPOINT_DOMAIN + canonical_bytes(result)
    ).hexdigest()
    return result


class MemoryRemote:
    def __init__(self, objects: dict[str, bytes] | None = None, *, fail_at: int | None = None) -> None:
        self.objects = dict(objects or {})
        self.fail_at = fail_at
        self.appends: list[tuple[str, bytes, str]] = []

    def append(self, name: str, line: bytes, digest: str) -> None:
        attempt = len(self.appends) + 1
        if self.fail_at == attempt:
            raise OSError("synthetic durable upload failure")
        assert digest == hashlib.sha256(line).hexdigest()
        self.appends.append((name, line, digest))
        self.objects[name] = self.objects.get(name, b"") + line

    def list(self, prefix: str) -> list[str]:
        return sorted(name for name in self.objects if name.startswith(prefix))

    def download(self, name: str) -> bytes:
        return self.objects[name]


def _local_event(events: list[dict[str, Any]]) -> Callable[[str, dict[str, Any]], dict[str, Any]]:
    def append(name: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = {"event_name": name, "payload": payload, "sequence": len(events) + 1}
        events.append(record)
        return record

    return append


def test_event_and_span_remote_append_complete_before_sink_returns() -> None:
    from tau2_luna_local.cloud_smoke import DurableEventSink, DurableSpanSink

    remote = MemoryRemote()
    local_events: list[dict[str, Any]] = []
    local_spans: list[dict[str, Any]] = []
    event_sink = DurableEventSink(
        local_append=_local_event(local_events),
        remote_append=remote.append,
        object_name="runs/run-1/attempts/attempt-1/events.jsonl",
        secrets=(SECRET,),
    )
    span_sink = DurableSpanSink(
        local_append=lambda value: local_spans.append(value) or value,
        remote_append=remote.append,
        object_name="runs/run-1/attempts/attempt-1/spans.jsonl",
        secrets=(SECRET,),
    )

    event_sink("model.request", {"call_id": "call-1"})
    assert remote.objects[event_sink.object_name].endswith(b"\n")
    span_sink({"name": "model.call", "call_id": "call-1"})
    assert remote.objects[span_sink.object_name].endswith(b"\n")
    assert len(local_events) == len(local_spans) == 1
    assert [name for name, _, _ in remote.appends] == [event_sink.object_name, span_sink.object_name]


def test_request_is_remote_durable_before_provider_and_response_before_return() -> None:
    from tau2_luna_local.cloud_smoke import DurableEventSink

    from tau2_luna_local.capture import CompletionCapture

    order: list[str] = []
    remote = MemoryRemote()
    local_events: list[dict[str, Any]] = []

    def remote_append(name: str, line: bytes, digest: str) -> None:
        remote.append(name, line, digest)
        event_name = json.loads(line)["event_name"]
        order.append(f"remote:{event_name}")

    sink = DurableEventSink(
        local_append=_local_event(local_events),
        remote_append=remote_append,
        object_name="runs/run-1/attempts/attempt-1/events.jsonl",
        secrets=(SECRET,),
    )

    def provider(**_: Any) -> FakeResponse:
        assert order == ["remote:model.request"]
        order.append("provider")
        return FakeResponse()

    target = SimpleNamespace(completion=provider)
    with CompletionCapture(target=target, event_sink=sink, span_sink=lambda _: None):
        target.completion(model="azure/luna-smoke", messages=[])
        order.append("returned")
    assert order == ["remote:model.request", "provider", "remote:model.response", "returned"]


def test_failed_durable_response_upload_poison_stops_next_model_call() -> None:
    from tau2_luna_local.cloud_smoke import DurableAppendError, DurableEventSink

    from tau2_luna_local.capture import CompletionCapture

    remote = MemoryRemote(fail_at=2)
    local_events: list[dict[str, Any]] = []
    provider_calls = 0

    def provider(**_: Any) -> FakeResponse:
        nonlocal provider_calls
        provider_calls += 1
        return FakeResponse()

    sink = DurableEventSink(
        local_append=_local_event(local_events),
        remote_append=remote.append,
        object_name="runs/run-1/attempts/attempt-1/events.jsonl",
        secrets=(SECRET,),
    )
    target = SimpleNamespace(completion=provider)
    with CompletionCapture(target=target, event_sink=sink, span_sink=lambda _: None):
        with pytest.raises(DurableAppendError, match="upload"):
            target.completion(model="azure/luna-smoke", messages=[])
        with pytest.raises(DurableAppendError, match="poison"):
            target.completion(model="azure/luna-smoke", messages=[])
    assert provider_calls == 1


def test_six_calls_admitted_and_seventh_refuses_before_egress() -> None:
    from tau2_luna_local.cloud_smoke import BudgetExhausted, ModelCallBudget

    egress: list[int] = []

    def provider(**_: Any) -> str:
        egress.append(len(egress) + 1)
        return "ok"

    budget = ModelCallBudget(
        max_calls=6,
        reservation_per_call_usd=Decimal("0.50"),
        model_cap_usd=Decimal("3.00"),
    )
    for _ in range(6):
        assert budget.call(provider, model="azure/luna-smoke") == "ok"
    with pytest.raises(BudgetExhausted, match=r"six|6|3\.00"):
        budget.call(provider, model="azure/luna-smoke")
    assert egress == [1, 2, 3, 4, 5, 6]
    assert budget.admitted_calls == 6
    assert budget.reserved_usd == Decimal("3.00")


def test_partial_attempt_is_retained_and_resume_starts_new_identity() -> None:
    from tau2_luna_local.cloud_smoke import plan_resume

    original = checkpoint(
        {
            "schema_version": "tau2-luna-cloud-checkpoint/v1",
            "task_id": "retail-0",
            "trial": 0,
            "attempts": [
                {
                    "attempt_id": "attempt-1",
                    "state": "PARTIAL",
                    "prefix": "runs/run-1/attempts/attempt-1/",
                }
            ],
        }
    )
    before = canonical_bytes(original)
    decision = plan_resume(
        original,
        task_id="retail-0",
        trial=0,
        attempt_id_factory=lambda: "attempt-2",
        verify_completed=lambda _: False,
    )
    assert decision == {
        "action": "START_NEW_ATTEMPT",
        "attempt_id": "attempt-2",
        "retained_attempt_ids": ["attempt-1"],
    }
    assert canonical_bytes(original) == before


def test_verified_completed_attempt_is_skipped_without_allocating_identity() -> None:
    from tau2_luna_local.cloud_smoke import plan_resume

    value = checkpoint(
        {
            "schema_version": "tau2-luna-cloud-checkpoint/v1",
            "task_id": "retail-0",
            "trial": 0,
            "attempts": [{"attempt_id": "attempt-1", "state": "COMPLETED", "bundle_hash": "abc"}],
        }
    )

    def forbidden_factory() -> str:
        raise AssertionError("completed attempt must not allocate a replacement")

    decision = plan_resume(
        value,
        task_id="retail-0",
        trial=0,
        attempt_id_factory=forbidden_factory,
        verify_completed=lambda attempt: attempt["bundle_hash"] == "abc",
    )
    assert decision == {"action": "SKIP_VERIFIED_COMPLETED", "attempt_id": "attempt-1"}


def test_corrupt_checkpoint_refuses_without_new_attempt() -> None:
    from tau2_luna_local.cloud_smoke import CheckpointInvalid, plan_resume

    value = checkpoint(
        {
            "schema_version": "tau2-luna-cloud-checkpoint/v1",
            "task_id": "retail-0",
            "trial": 0,
            "attempts": [],
        }
    )
    value["trial"] = 1
    allocated = False

    def factory() -> str:
        nonlocal allocated
        allocated = True
        return "must-not-exist"

    with pytest.raises(CheckpointInvalid, match="hash|checkpoint"):
        plan_resume(
            value,
            task_id="retail-0",
            trial=0,
            attempt_id_factory=factory,
            verify_completed=lambda _: False,
        )
    assert allocated is False


def _relay_checkpoint(objects: dict[str, bytes]) -> dict[str, Any]:
    return {
        "schema_version": "tau2-luna-relay/v1",
        "prefix": "runs/run-1/attempts/attempt-1/",
        "inventory": [
            {
                "remote_name": name,
                "local_name": name.rsplit("/", 1)[-1],
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            for name, data in sorted(objects.items())
        ],
    }


def test_relay_requires_exact_remote_local_inventory_hashes_and_no_secret(tmp_path: Path) -> None:
    from tau2_luna_local.cloud_smoke import relay_verified_inventory

    objects = {
        "runs/run-1/attempts/attempt-1/events.jsonl": b'{"event":"safe"}\n',
        "runs/run-1/attempts/attempt-1/spans.jsonl": b'{"span":"safe"}\n',
        "runs/run-1/attempts/attempt-1/manifest.json": b'{"valid":true}\n',
    }
    remote = MemoryRemote(objects)
    destination = tmp_path / "relayed"
    report = relay_verified_inventory(
        remote_list=remote.list,
        remote_download=remote.download,
        checkpoint=_relay_checkpoint(objects),
        destination=destination,
        secret_values=(SECRET,),
    )
    assert report["valid"] is True
    assert report["remote_inventory"] == report["local_inventory"]
    assert sorted(path.name for path in destination.iterdir()) == [
        "events.jsonl",
        "manifest.json",
        "spans.jsonl",
    ]
    assert SECRET.encode() not in b"".join(path.read_bytes() for path in destination.iterdir())


@pytest.mark.parametrize("fault", ["extra", "missing", "hash", "secret"])
def test_relay_mismatch_or_secret_refuses_without_success(tmp_path: Path, fault: str) -> None:
    from tau2_luna_local.cloud_smoke import RelayMismatch, relay_verified_inventory

    name = "runs/run-1/attempts/attempt-1/events.jsonl"
    objects = {name: b'{"event":"safe"}\n'}
    declared = _relay_checkpoint(objects)
    if fault == "extra":
        objects["runs/run-1/attempts/attempt-1/extra.txt"] = b"extra"
    elif fault == "missing":
        objects.clear()
    elif fault == "hash":
        objects[name] = b"tampered"
    else:
        objects[name] = SECRET.encode()
        declared = _relay_checkpoint(objects)
    remote = MemoryRemote(objects)
    with pytest.raises(RelayMismatch):
        relay_verified_inventory(
            remote_list=remote.list,
            remote_download=remote.download,
            checkpoint=declared,
            destination=tmp_path / "refused",
            secret_values=(SECRET,),
        )


@pytest.mark.parametrize(
    "identity",
    [
        {"model_name": "gpt-4.1", "model_version": "2026-07-09", "sku": "GlobalStandard"},
        {"model_name": "gpt-5.6-luna", "model_version": "2026-07-08", "sku": "GlobalStandard"},
        {"model_name": "gpt-5.6-luna", "model_version": "2026-07-09", "sku": "Standard"},
    ],
)
def test_model_identity_mismatch_refuses(identity: dict[str, str]) -> None:
    from tau2_luna_local.cloud_smoke import ModelIdentityError, validate_model_identity

    with pytest.raises(ModelIdentityError):
        validate_model_identity(identity)


def test_exact_luna_model_identity_is_accepted() -> None:
    from tau2_luna_local.cloud_smoke import validate_model_identity

    validate_model_identity(
        {
            "model_name": "gpt-5.6-luna",
            "model_version": "2026-07-09",
            "sku": "GlobalStandard",
        }
    )


def _tau2_data_directory(root: Path, *, commit: str) -> Path:
    from conftest import write_json

    data_dir = root / "tau2-source"
    retail = data_dir / "data" / "tau2" / "domains" / "retail"
    retail.mkdir(parents=True)
    write_json(
        data_dir / ".tau2-source.json",
        {
            "repository": "https://github.com/sierra-research/tau2-bench",
            "commit": commit,
        },
    )
    write_json(retail / "tasks.json", [{"id": index} for index in range(114)])
    return data_dir


def test_tau2_data_preflight_accepts_exact_source_and_114_retail_tasks(tmp_path: Path) -> None:
    from tau2_luna_local.cloud_smoke import validate_tau2_data_directory

    data_dir = _tau2_data_directory(
        tmp_path,
        commit="f8de30c298689cbe0117d76a378e7315a17e5bd8",
    )
    assert validate_tau2_data_directory(data_dir) == {
        "commit": "f8de30c298689cbe0117d76a378e7315a17e5bd8",
        "retail_task_count": 114,
    }


@pytest.mark.parametrize("fault", ["absent", "commit", "task_inventory"])
def test_tau2_data_preflight_refuses_missing_or_mismatched_source_before_egress(
    tmp_path: Path,
    fault: str,
) -> None:
    from conftest import write_json
    from tau2_luna_local.cloud_smoke import Tau2DataError, preflight_model_call

    data_dir = tmp_path / "absent"
    if fault != "absent":
        data_dir = _tau2_data_directory(
            tmp_path,
            commit=(
                "0" * 40
                if fault == "commit"
                else "f8de30c298689cbe0117d76a378e7315a17e5bd8"
            ),
        )
        if fault == "task_inventory":
            write_json(
                data_dir / "data" / "tau2" / "domains" / "retail" / "tasks.json",
                [{"id": 18}],
            )
    provider_called = False

    def provider() -> None:
        nonlocal provider_called
        provider_called = True

    with pytest.raises(Tau2DataError):
        preflight_model_call(
            provider=provider,
            tau2_data_dir=data_dir,
            model_identity={
                "model_name": "gpt-5.6-luna",
                "model_version": "2026-07-09",
                "sku": "GlobalStandard",
            },
        )
    assert provider_called is False


@pytest.mark.parametrize("fails", [False, True])
def test_vm_deallocation_attempted_after_finalization_on_success_and_failure(fails: bool) -> None:
    from tau2_luna_local.cloud_smoke import run_with_deallocation

    order: list[str] = []

    def execute() -> str:
        order.append("execute")
        if fails:
            raise RuntimeError("synthetic smoke failure")
        return "result"

    def finalize(error: BaseException | None) -> None:
        order.append(f"finalize:{type(error).__name__ if error else 'success'}")

    def deallocate() -> None:
        order.append("deallocate")

    if fails:
        with pytest.raises(RuntimeError, match="synthetic"):
            run_with_deallocation(execute=execute, finalize=finalize, deallocate=deallocate)
        assert order == ["execute", "finalize:RuntimeError", "deallocate"]
    else:
        assert run_with_deallocation(execute=execute, finalize=finalize, deallocate=deallocate) == "result"
        assert order == ["execute", "finalize:success", "deallocate"]
