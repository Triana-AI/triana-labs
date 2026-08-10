"""Black-box contract for deterministic legacy extraction-checkpoint migration."""

from __future__ import annotations

import hashlib
import importlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from triana_labs.behavior_map import run_behavior_map
from triana_labs.behavior_map.contracts import ExtractionBatch


def _canonical(value: Any, *, lf: bool = False) -> bytes:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return payload + (b"\n" if lf else b"")


def _digest(domain: str, value: Any) -> str:
    return (
        "sha256:"
        + hashlib.sha256(domain.encode() + b"\0" + _canonical(value)).hexdigest()
    )


def _checkpoint_identity(stage: str) -> dict[str, str]:
    return {
        "stage": stage,
        "model_id": "legacy-author",
        "method_sha256": "sha256:" + "1" * 64,
        "payload_sha256": "sha256:" + "2" * 64,
        "provider_binding_sha256": "sha256:" + "3" * 64,
    }


def _episode(
    *,
    bindings: bool = True,
    conversation_id: str = "synthetic-conversation",
    status: str = "PROPOSED",
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "local_id": "demand",
        "goal": "Locate an order",
        "requested_action": "FIND_ORDER",
        "subject": "order",
        "constraints": [],
        "fallbacks": [],
        "supersedes_local_id": None,
        "start_turn_ordinal": 0,
        "end_turn_ordinal": 0,
        "citations": [
            {
                "conversation_id": conversation_id,
                "event_sequence": 0,
                "quote": "Where is my order?",
            }
        ],
        "status": status,
    }
    if bindings:
        row["field_grounding"] = {
            "goal": [0],
            "requested_action": [0],
            "subject": [0],
            "constraints": [],
            "fallbacks": [],
        }
    return row


def _write_success(
    directory: Path,
    *,
    stage: str = "demand-episodes-and-agent-behaviors-0000",
    bindings: bool = True,
    payload: dict[str, Any] | None = None,
    conversation_id: str = "synthetic-conversation",
    status: str = "PROPOSED",
) -> tuple[Path, dict[str, Any]]:
    payload = payload or {
        "conversations": [{"conversation_id": "synthetic-conversation"}]
    }
    identity = _checkpoint_identity(stage)
    identity["payload_sha256"] = _digest("behavior-map-payload-v0", payload)
    result = {
        "episodes": [
            _episode(
                bindings=bindings,
                conversation_id=conversation_id,
                status=status,
            )
        ],
        "behaviors": [],
    }
    value = {
        "artifact_kind": "behavior_map_checkpoint_v0",
        "schema_version": 0,
        "identity": identity,
        "result": result,
        "result_sha256": _digest("behavior-map-checkpoint-result-v0", result),
        "payload": payload,
    }
    checkpoint_id = _digest("behavior-map-checkpoint-v0", identity)
    path = directory / f"{checkpoint_id.removeprefix('sha256:')}.json"
    path.write_bytes(_canonical(value, lf=True))
    return path, value


def _write_attempt(
    directory: Path,
    state: str,
    *,
    conversation_id: str = "synthetic-conversation",
    stage: str = "demand-episodes-and-agent-behaviors-0000",
) -> tuple[Path, dict[str, Any]]:
    identity = _checkpoint_identity(stage)
    descriptor = {"conversation_ids": [conversation_id]}
    value = {
        "artifact_kind": "behavior_map_attempt_v0",
        "schema_version": 0,
        "identity": identity,
        "state": state,
        "failure_code": "FAILURE" if state == "FAILED" else None,
        "payload": descriptor,
        "payload_descriptor_sha256": _digest(
            "behavior-map-attempt-descriptor-v0", descriptor
        ),
    }
    checkpoint_id = _digest("behavior-map-checkpoint-v0", identity)
    path = directory / f"{checkpoint_id.removeprefix('sha256:')}.json"
    path.write_bytes(_canonical(value, lf=True))
    return path, value


class _ProviderTrap:
    model_id = "legacy-author"

    def __init__(self) -> None:
        self.calls = 0

    def complete_json(self, **_: Any) -> dict[str, Any]:
        self.calls += 1
        raise AssertionError("migration continuation must not call a provider")

    def lineage(self) -> dict[str, Any]:
        return {
            "provider": "SYNTHETIC_TEST_BOUNDARY",
            "model_id": self.model_id,
            "provider_calls": 0,
            "attempted_call_count": 0,
            "budget": {
                "max_reserved_usd": 0.0,
                "reservation_usd_per_call": 0.0,
            },
            "retry_policy": "NONE",
            "fallback_policy": "NONE",
        }


def _trace(conversation_id: str) -> dict[str, Any]:
    return {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": "SYNTHETIC",
        "trace_id": conversation_id,
        "source_trace_id": f"source-{conversation_id}",
        "events": [
            {
                "sequence": 0,
                "event_kind": "USER_MESSAGE",
                "content": "Where is my order?",
            }
        ],
    }


def _write_runtime_manifest(tmp_path: Path, conversation_ids: list[str]) -> Path:
    source = tmp_path / "traces.jsonl"
    traces = [_trace(conversation_id) for conversation_id in conversation_ids]
    source_bytes = b"".join(_canonical(trace, lf=True) for trace in traces)
    source.write_bytes(source_bytes)
    manifest = {
        "artifact_kind": "evidence_bundle_manifest_v0",
        "schema_version": 0,
        "source": {
            "adapter_id": "preview-trace-jsonl",
            "adapter_version": "1",
            "path": str(source),
            "sha256": "sha256:" + hashlib.sha256(source_bytes).hexdigest(),
            "physical_record_count": len(traces),
        },
        "agent": {"workspace_id": "synthetic", "agent_id": "migration-agent"},
        "privacy": {
            "authorization": "SYNTHETIC_FIXTURE",
            "execution_location": "LOCAL_PRIVATE",
            "provider_egress": {
                "authorized": True,
                "model_id": "legacy-author",
                "audit_model_id": None,
            },
        },
        "grouping": {
            "highest_dependency_key": "conversation",
            "assignments": [
                {"group_id": f"group-{item}", "trace_ids": [item]}
                for item in conversation_ids
            ],
        },
        "capabilities": {
            "paired_arms": False,
            "outcomes": False,
            "existing_evals": False,
            "embeddings": False,
        },
        "outcomes": None,
        "existing_evals": None,
    }
    path = tmp_path / "manifest.json"
    path.write_bytes(_canonical(manifest, lf=True))
    return path


def _write_report(
    path: Path,
    report_id: str,
    checkpoint_ids: list[str],
    *,
    attempted_calls: int = 0,
    reserved_usd: float = 0.0,
    source_sha256: str | None = None,
    selected_list_sha256: str | None = None,
) -> None:
    path.write_bytes(
        _canonical(
            {
                "artifact_kind": "behavior_map_report_v0",
                "schema_version": 0,
                "report_id": report_id,
                "checkpoint_ids": checkpoint_ids,
                "source": {
                    "source_sha256": source_sha256,
                    "selected_list_sha256": selected_list_sha256,
                },
                "provider_lineage": {
                    "primary": {
                        "provider": "SYNTHETIC_TEST_BOUNDARY",
                        "model_id": "legacy-author",
                        "attempted_call_count": attempted_calls,
                    }
                },
                "budget": {
                    "cumulative_limit_usd": 100.0,
                    "prior_reserved_usd": reserved_usd,
                    "total_reserved_usd": reserved_usd,
                },
            },
            lf=True,
        )
    )


def _migrate(
    source: Path, report: Path, output: Path, predecessor_report_id: str
) -> dict[str, Any]:
    module = importlib.import_module("triana_labs.behavior_map.checkpoint_migration")
    return module.migrate_extraction_checkpoints(
        source_checkpoint_dir=source,
        source_report_path=report,
        output_dir=output,
        predecessor_report_id=predecessor_report_id,
    )


def _bind_migration(
    manifest_path: Path,
    output: Path,
    migration: dict[str, Any],
    *,
    predecessor_report_id: str,
    attempted_calls: int,
    reserved_usd: float,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_bytes())
    sidecar_path = output / "checkpoint-migration.json"
    provider_binding = {
        "provider": "SYNTHETIC_TEST_BOUNDARY",
        "model_id": "legacy-author",
        "endpoint_origin": None,
        "deployment_version": None,
        "sku": None,
        "capacity": None,
        "credential_boundary_id": None,
    }
    trace_ids = sorted(
        trace_id
        for assignment in manifest["grouping"]["assignments"]
        for trace_id in assignment["trace_ids"]
    )
    manifest["checkpoint_migration"] = {
        "path": str(sidecar_path),
        "sidecar_sha256": "sha256:"
        + hashlib.sha256(sidecar_path.read_bytes()).hexdigest(),
        "migration_id": migration["migration_id"],
        "predecessor_report_id": predecessor_report_id,
        "source_sha256": manifest["source"]["sha256"],
        "selected_list_sha256": "sha256:"
        + hashlib.sha256(_canonical(trace_ids)).hexdigest(),
        "primary_model_id": "legacy-author",
        "primary_provider_binding_sha256": _digest(
            "behavior-map-provider-binding-v0", provider_binding
        ),
        "predecessor_attempted_call_count": attempted_calls,
        "prior_reserved_usd": reserved_usd,
    }
    manifest_path.write_bytes(_canonical(manifest, lf=True))
    return manifest


def test_grounded_legacy_success_migrates_immutably_and_byte_stably(
    tmp_path: Path,
) -> None:
    predecessor_report_id = "sha256:" + "a" * 64
    source = tmp_path / "private-source"
    source.mkdir()
    old_path, old = _write_success(source)
    old_bytes = old_path.read_bytes()
    old_file_hash = "sha256:" + hashlib.sha256(old_bytes).hexdigest()
    old_checkpoint_id = "sha256:" + old_path.stem
    report_path = tmp_path / "private-report.json"
    _write_report(report_path, predecessor_report_id, [old_checkpoint_id])

    first = _migrate(source, report_path, tmp_path / "first", predecessor_report_id)
    second = _migrate(source, report_path, tmp_path / "second", predecessor_report_id)

    assert old_path.read_bytes() == old_bytes
    assert first == second
    assert (tmp_path / "first" / "checkpoint-migration.json").read_bytes() == (
        tmp_path / "second" / "checkpoint-migration.json"
    ).read_bytes()
    assert first["artifact_kind"] == "behavior_map_checkpoint_migration_v0"
    assert first["predecessor_report_id"] == predecessor_report_id
    assert first["summary"] == {"migrated": 1, "refused": 0}
    lineage = first["migrations"][0]
    assert lineage["predecessor_checkpoint_sha256"] == old_file_hash
    assert lineage["predecessor_checkpoint_id"] == old_checkpoint_id
    assert lineage["migration_reason"] == "ADD_EXPLICIT_GROUNDING_CONTRACT_VERSION"
    assert lineage["checkpoint_id"] != old_checkpoint_id
    migrated_path = (
        tmp_path
        / "first"
        / "behavior-map-checkpoints"
        / (lineage["checkpoint_id"].removeprefix("sha256:") + ".json")
    )
    migrated = json.loads(migrated_path.read_bytes())
    assert migrated["identity"] != old["identity"]
    assert migrated["result_sha256"] == _digest(
        "behavior-map-checkpoint-result-v0", migrated["result"]
    )
    assert lineage["result_sha256"] == migrated["result_sha256"]
    assert all(
        row["grounding_contract_version"] == 1 for row in migrated["result"]["episodes"]
    )
    ExtractionBatch.model_validate(migrated["result"], strict=True)
    serialized = json.dumps(first, sort_keys=True)
    assert str(source) not in serialized
    assert str(report_path) not in serialized


def test_any_missing_field_bindings_refuses_the_whole_extraction_unit(
    tmp_path: Path,
) -> None:
    predecessor_report_id = "sha256:" + "b" * 64
    source = tmp_path / "private-source"
    source.mkdir()
    old_path, _ = _write_success(source, bindings=False)
    report_path = tmp_path / "private-report.json"
    _write_report(report_path, predecessor_report_id, ["sha256:" + old_path.stem])

    result = _migrate(source, report_path, tmp_path / "output", predecessor_report_id)

    assert result["summary"] == {"migrated": 0, "refused": 1}
    assert result["refusals"] == [
        {
            "predecessor_checkpoint_id": "sha256:" + old_path.stem,
            "predecessor_checkpoint_sha256": "sha256:"
            + hashlib.sha256(old_path.read_bytes()).hexdigest(),
            "code": "LEGACY_EXTRACTION_FIELD_GROUNDING_MISSING",
            "stage": "EXTRACTION",
            "retryable": False,
        }
    ]
    assert not list((tmp_path / "output" / "behavior-map-checkpoints").glob("*.json"))


@pytest.mark.parametrize(
    ("state", "code"),
    [
        ("FAILED", "LEGACY_EXTRACTION_ATTEMPT_FAILED"),
        ("IN_FLIGHT", "LEGACY_EXTRACTION_ATTEMPT_IN_FLIGHT"),
    ],
)
def test_old_attempts_are_typed_non_callable_refusals(
    tmp_path: Path, state: str, code: str
) -> None:
    predecessor_report_id = "sha256:" + "c" * 64
    source = tmp_path / "private-source"
    source.mkdir()
    attempt_path, _ = _write_attempt(source, state)
    report_path = tmp_path / "private-report.json"
    _write_report(report_path, predecessor_report_id, ["sha256:" + attempt_path.stem])

    result = _migrate(source, report_path, tmp_path / "output", predecessor_report_id)

    assert result["summary"] == {"migrated": 0, "refused": 1}
    assert result["refusals"][0]["code"] == code
    assert result["refusals"][0]["retryable"] is False
    assert not list((tmp_path / "output" / "behavior-map-checkpoints").glob("*.json"))


def test_migration_refuses_non_extraction_tamper_symlink_and_output_alias(
    tmp_path: Path,
) -> None:
    predecessor_report_id = "sha256:" + "d" * 64
    source = tmp_path / "private-source"
    source.mkdir()
    population_path, population = _write_success(source, stage="population-batch-0000")
    report_path = tmp_path / "private-report.json"
    _write_report(
        report_path, predecessor_report_id, ["sha256:" + population_path.stem]
    )
    population_result = _migrate(
        source, report_path, tmp_path / "population-output", predecessor_report_id
    )
    assert population_result["summary"] == {"migrated": 0, "refused": 1}
    assert population_result["refusals"][0]["code"] == "CHECKPOINT_STAGE_NOT_MIGRATABLE"

    population["result_sha256"] = "sha256:" + "0" * 64
    population_path.write_bytes(_canonical(population, lf=True))
    with pytest.raises(ValueError, match="CHECKPOINT_HASH_INVALID"):
        _migrate(
            source, report_path, tmp_path / "tampered-output", predecessor_report_id
        )

    symlink = tmp_path / "source-link"
    symlink.symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match="MIGRATION_PATH_INVALID"):
        _migrate(
            symlink, report_path, tmp_path / "symlink-output", predecessor_report_id
        )
    with pytest.raises(ValueError, match="MIGRATION_PATH_INVALID"):
        _migrate(source, report_path, source, predecessor_report_id)
    with pytest.raises(ValueError, match="PREDECESSOR_REPORT_MISMATCH"):
        _migrate(
            source,
            report_path,
            tmp_path / "wrong-predecessor-output",
            "sha256:" + "e" * 64,
        )


def test_mixed_migration_is_exact_runtime_reusable_non_callable_and_conserves_campaign(
    tmp_path: Path,
) -> None:
    behavior_map = importlib.import_module("triana_labs.behavior_map")
    conversation_ids = ["grounded", "missing", "failed", "in-flight"]
    manifest_path = _write_runtime_manifest(tmp_path, conversation_ids)
    source = tmp_path / "private-source"
    source.mkdir()
    agent_context = "Synthetic support agent."
    projections = {
        conversation_id: behavior_map._projection([_trace(conversation_id)])[0]
        for conversation_id in conversation_ids
    }
    payloads = {
        conversation_id: {
            "agent_context": agent_context,
            "conversations": [projections[conversation_id]],
        }
        for conversation_id in conversation_ids
    }
    stages = {
        conversation_id: f"demand-episodes-and-agent-behaviors-{index:04d}"
        for index, conversation_id in enumerate(sorted(conversation_ids))
    }
    grounded_path, _ = _write_success(
        source,
        stage=stages["grounded"],
        payload=payloads["grounded"],
        conversation_id="grounded",
        status="UNKNOWN",
    )
    missing_path, _ = _write_success(
        source,
        stage=stages["missing"],
        payload=payloads["missing"],
        conversation_id="missing",
        bindings=False,
        status="UNKNOWN",
    )
    failed_path, _ = _write_attempt(
        source,
        "FAILED",
        conversation_id="failed",
        stage=stages["failed"],
    )
    inflight_path, _ = _write_attempt(
        source,
        "IN_FLIGHT",
        conversation_id="in-flight",
        stage=stages["in-flight"],
    )
    source_snapshot = {path.name: path.read_bytes() for path in source.glob("*.json")}
    predecessor_report_id = "sha256:" + "f" * 64
    report_path = tmp_path / "private-report.json"
    manifest = json.loads(manifest_path.read_bytes())
    selected_list_sha256 = (
        "sha256:" + hashlib.sha256(_canonical(sorted(conversation_ids))).hexdigest()
    )
    checkpoint_ids = [
        "sha256:" + path.stem
        for path in (grounded_path, missing_path, failed_path, inflight_path)
    ]
    _write_report(
        report_path,
        predecessor_report_id,
        checkpoint_ids,
        attempted_calls=97,
        reserved_usd=9.7,
        source_sha256=manifest["source"]["sha256"],
        selected_list_sha256=selected_list_sha256,
    )
    report_bytes = report_path.read_bytes()
    output = tmp_path / "migrated-run"

    migration = _migrate(source, report_path, output, predecessor_report_id)

    unbound_output = tmp_path / "unbound-run"
    shutil.copytree(output, unbound_output)
    unbound_trap = _ProviderTrap()
    unbound_report = run_behavior_map(
        manifest_path,
        unbound_output,
        primary_model=unbound_trap,
        audit_model=None,
        agent_context=agent_context,
    )
    assert unbound_trap.calls == 0
    assert "MIGRATION_BINDING_INVALID" in {
        row["code"] for row in unbound_report["gaps"]
    }

    _bind_migration(
        manifest_path,
        output,
        migration,
        predecessor_report_id=predecessor_report_id,
        attempted_calls=97,
        reserved_usd=9.7,
    )

    trap = _ProviderTrap()
    provider_binding = {
        key: trap.lineage().get(key)
        for key in (
            "provider",
            "model_id",
            "endpoint_origin",
            "deployment_version",
            "sku",
            "capacity",
            "credential_boundary_id",
        )
    }
    expected_identity, expected_checkpoint_hex = behavior_map._checkpoint_identity(
        stage=stages["grounded"],
        model_id=trap.model_id,
        system=behavior_map._EXTRACT_SYSTEM,
        payload=payloads["grounded"],
        schema=ExtractionBatch,
        provider_binding=provider_binding,
    )
    migrated_path = (
        output / "behavior-map-checkpoints" / f"{expected_checkpoint_hex}.json"
    )
    assert migrated_path.is_file()
    assert json.loads(migrated_path.read_bytes())["identity"] == expected_identity

    runtime_report = run_behavior_map(
        manifest_path,
        output,
        primary_model=trap,
        audit_model=None,
        agent_context=agent_context,
    )

    assert trap.calls == 0
    assert {
        path.name: path.read_bytes() for path in source.glob("*.json")
    } == source_snapshot
    assert report_path.read_bytes() == report_bytes
    assert migration["summary"] == {"migrated": 1, "refused": 3}
    assert {row["code"] for row in migration["refusals"]} == {
        "LEGACY_EXTRACTION_FIELD_GROUNDING_MISSING",
        "LEGACY_EXTRACTION_ATTEMPT_FAILED",
        "LEGACY_EXTRACTION_ATTEMPT_IN_FLIGHT",
    }
    assert all(row["retryable"] is False for row in migration["refusals"])
    assert {
        row["conversation_id"]
        for row in runtime_report["emerging_unknown"]
        if row["reason"] == "MIGRATION_REFUSED"
    } == {"missing", "failed", "in-flight"}
    assert runtime_report["provider_lineage"]["primary"]["attempted_call_count"] >= 97
    assert runtime_report["budget"]["prior_reserved_usd"] == 9.7
    assert str(output / "checkpoint-migration.json") not in json.dumps(runtime_report)


@pytest.mark.parametrize(
    "mismatch",
    [
        "migration_id",
        "predecessor_report_id",
        "source_sha256",
        "selected_list_sha256",
        "primary_model_id",
        "primary_provider_binding_sha256",
        "predecessor_attempted_call_count",
        "prior_reserved_usd",
    ],
)
def test_runtime_refuses_any_migration_authority_binding_mismatch_before_calls(
    tmp_path: Path, mismatch: str
) -> None:
    conversation_ids = ["grounded"]
    manifest_path = _write_runtime_manifest(tmp_path, conversation_ids)
    behavior_map = importlib.import_module("triana_labs.behavior_map")
    agent_context = "Synthetic support agent."
    payload = {
        "agent_context": agent_context,
        "conversations": [behavior_map._projection([_trace("grounded")])[0]],
    }
    source = tmp_path / "private-source"
    source.mkdir()
    old_path, _ = _write_success(
        source,
        payload=payload,
        conversation_id="grounded",
        status="UNKNOWN",
    )
    predecessor_report_id = "sha256:" + "7" * 64
    report_path = tmp_path / "private-report.json"
    manifest = json.loads(manifest_path.read_bytes())
    selected_list_sha256 = (
        "sha256:" + hashlib.sha256(_canonical(conversation_ids)).hexdigest()
    )
    _write_report(
        report_path,
        predecessor_report_id,
        ["sha256:" + old_path.stem],
        attempted_calls=97,
        reserved_usd=9.7,
        source_sha256=manifest["source"]["sha256"],
        selected_list_sha256=selected_list_sha256,
    )
    output = tmp_path / "output"
    migration = _migrate(source, report_path, output, predecessor_report_id)
    bound = _bind_migration(
        manifest_path,
        output,
        migration,
        predecessor_report_id=predecessor_report_id,
        attempted_calls=97,
        reserved_usd=9.7,
    )
    binding = bound["checkpoint_migration"]
    binding[mismatch] = (
        98
        if mismatch == "predecessor_attempted_call_count"
        else 10.7
        if mismatch == "prior_reserved_usd"
        else "sha256:" + "0" * 64
        if mismatch not in {"primary_model_id"}
        else "wrong-model"
    )
    manifest_path.write_bytes(_canonical(bound, lf=True))

    trap = _ProviderTrap()
    report = run_behavior_map(
        manifest_path,
        output,
        primary_model=trap,
        audit_model=None,
        agent_context=agent_context,
    )

    assert trap.calls == 0
    assert "MIGRATION_BINDING_INVALID" in {row["code"] for row in report["gaps"]}
    assert report["provider_lineage"]["primary"]["attempted_call_count"] < 97
    assert report["budget"]["prior_reserved_usd"] != 9.7
    assert str(output / "checkpoint-migration.json") not in json.dumps(report)


@pytest.mark.parametrize(
    ("field_grounding", "constraints", "fallbacks"),
    [
        (
            {
                "goal": [1],
                "requested_action": [0],
                "subject": [0],
                "constraints": [],
                "fallbacks": [],
            },
            [],
            [],
        ),
        (
            {
                "goal": [0],
                "requested_action": [],
                "subject": [0],
                "constraints": [],
                "fallbacks": [],
            },
            [],
            [],
        ),
        (
            {
                "goal": [0],
                "requested_action": [0],
                "subject": [0],
                "constraints": [],
                "fallbacks": [],
            },
            ["urgent"],
            [],
        ),
        (
            {
                "goal": [0],
                "requested_action": [0],
                "subject": [0],
                "constraints": [],
                "fallbacks": [],
            },
            [],
            ["keep the order"],
        ),
        (
            {
                "goal": [0],
                "requested_action": [0],
                "subject": [0],
                "constraints": [[1]],
                "fallbacks": [],
            },
            ["urgent"],
            [],
        ),
        (
            {
                "goal": [0],
                "requested_action": [0],
                "subject": [0],
                "constraints": [],
                "fallbacks": [[1]],
            },
            [],
            ["keep the order"],
        ),
    ],
)
def test_migration_refuses_out_of_range_or_incomplete_field_bindings(
    tmp_path: Path,
    field_grounding: dict[str, Any],
    constraints: list[str],
    fallbacks: list[str],
) -> None:
    predecessor_report_id = "sha256:" + "9" * 64
    source = tmp_path / "private-source"
    source.mkdir()
    path, checkpoint = _write_success(source)
    episode = checkpoint["result"]["episodes"][0]
    episode["constraints"] = constraints
    episode["fallbacks"] = fallbacks
    episode["field_grounding"] = field_grounding
    checkpoint["result_sha256"] = _digest(
        "behavior-map-checkpoint-result-v0", checkpoint["result"]
    )
    path.write_bytes(_canonical(checkpoint, lf=True))
    report_path = tmp_path / "private-report.json"
    _write_report(report_path, predecessor_report_id, ["sha256:" + path.stem])

    result = _migrate(source, report_path, tmp_path / "output", predecessor_report_id)

    assert result["summary"] == {"migrated": 0, "refused": 1}
    assert result["refusals"][0]["code"] == "LEGACY_EXTRACTION_FIELD_GROUNDING_INVALID"
