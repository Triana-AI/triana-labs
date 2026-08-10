"""RED contract for migrating a real interrupted semantic campaign."""

from __future__ import annotations

import hashlib
import importlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from triana_labs.behavior_map import run_behavior_map


def _canonical(value: Any, *, lf: bool = False) -> bytes:
    payload = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return payload + (b"\n" if lf else b"")


def _digest(domain: str, value: Any) -> str:
    return (
        "sha256:"
        + hashlib.sha256(domain.encode() + b"\0" + _canonical(value)).hexdigest()
    )


def _file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _identity(index: int, payload: dict[str, Any]) -> dict[str, str]:
    return {
        "stage": f"demand-episodes-and-agent-behaviors-{index:04d}",
        "model_id": "legacy-author",
        "method_sha256": "sha256:" + "1" * 64,
        "payload_sha256": _digest("behavior-map-payload-v0", payload),
        "provider_binding_sha256": "sha256:" + "3" * 64,
    }


def _write_campaign(
    root: Path, *, proposed_episodes: bool = False
) -> tuple[Path, Path, Path, dict[str, Any], list[str]]:
    checkpoints = root / "private-checkpoints"
    checkpoints.mkdir(parents=True)
    checkpoint_ids: list[str] = []
    inventory: list[dict[str, Any]] = []
    for index in range(97):
        conversation_id = f"private-conversation-{index:03d}"
        payload = {
            "agent_context": "Synthetic support agent.",
            "conversations": [
                {
                    "conversation_id": conversation_id,
                    "events": [
                        {
                            "event_sequence": 0,
                            "event_kind": "USER_MESSAGE",
                            "conversation_turn_ordinal": 0,
                            "content": "Where is my order?",
                        }
                    ],
                }
            ],
        }
        identity = _identity(index, payload)
        checkpoint_id = _digest("behavior-map-checkpoint-v0", identity)
        checkpoint_ids.append(checkpoint_id)
        path = checkpoints / f"{checkpoint_id.removeprefix('sha256:')}.json"
        if index < 87:
            result = {
                "episodes": [
                    {
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
                        "field_grounding": {
                            "goal": [0],
                            "requested_action": [0],
                            "subject": [0],
                            "constraints": [],
                            "fallbacks": [],
                        },
                        "status": "PROPOSED" if proposed_episodes else "UNKNOWN",
                    }
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
        else:
            descriptor = {"conversation_ids": [conversation_id]}
            value = {
                "artifact_kind": "behavior_map_attempt_v0",
                "schema_version": 0,
                "identity": identity,
                "state": "FAILED" if index % 2 else "IN_FLIGHT",
                "failure_code": "FAILURE" if index % 2 else None,
                "payload": descriptor,
                "payload_descriptor_sha256": _digest(
                    "behavior-map-attempt-descriptor-v0", descriptor
                ),
            }
        path.write_bytes(_canonical(value, lf=True))
        inventory.append(
            {
                "checkpoint_id": checkpoint_id,
                "file_sha256": _file_hash(path),
                "artifact_kind": value["artifact_kind"],
                "state": (
                    "SUCCEEDED"
                    if value["artifact_kind"] == "behavior_map_checkpoint_v0"
                    else value["state"]
                ),
                "stage": identity["stage"],
                "model_id": identity["model_id"],
                "payload_or_descriptor_sha256": (
                    identity["payload_sha256"]
                    if value["artifact_kind"] == "behavior_map_checkpoint_v0"
                    else value["payload_descriptor_sha256"]
                ),
                "result_sha256": value.get("result_sha256"),
            }
        )

    trace_source = root / "traces.jsonl"
    traces = [
        {
            "contract_kind": "preview_trace",
            "schema_version": 1,
            "privacy_class": "SYNTHETIC",
            "trace_id": f"private-conversation-{index:03d}",
            "source_trace_id": f"source-private-conversation-{index:03d}",
            "events": [
                {
                    "sequence": 0,
                    "event_kind": "USER_MESSAGE",
                    "content": "Where is my order?",
                }
            ],
        }
        for index in range(97)
    ]
    trace_bytes = b"".join(_canonical(trace, lf=True) for trace in traces)
    trace_source.write_bytes(trace_bytes)
    source_sha256 = "sha256:" + hashlib.sha256(trace_bytes).hexdigest()
    selected_ids = sorted(trace["trace_id"] for trace in traces)
    selected_list_sha256 = (
        "sha256:" + hashlib.sha256(_canonical(selected_ids)).hexdigest()
    )
    manifest = {
        "artifact_kind": "evidence_bundle_manifest_v0",
        "schema_version": 0,
        "source": {
            "adapter_id": "preview-trace-jsonl",
            "adapter_version": "1",
            "path": str(trace_source),
            "sha256": source_sha256,
            "physical_record_count": 97,
        },
        "semantic_scope": {
            "development_trace_ids": selected_ids,
            "selected_list_sha256": selected_list_sha256,
            "development_count": 97,
            "sealed": {"calibration": 0, "holdout": 0},
        },
        "agent": {"workspace_id": "synthetic", "agent_id": "migration-agent"},
        "privacy": {
            "execution_location": "LOCAL_PRIVATE",
            "authorization": "SYNTHETIC_FIXTURE",
            "provider_egress": {
                "authorized": True,
                "model_id": "legacy-author",
                "audit_model_id": "legacy-auditor",
            },
        },
        "grouping": {
            "highest_dependency_key": "conversation",
            "assignments": [
                {"group_id": f"group-{item}", "trace_ids": [item]}
                for item in selected_ids
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
        "method": {"retry_policy": "NONE", "fallback_policy": "NONE"},
        "semantic_budget": {
            "cumulative_limit_usd": 70.0,
            "prior_reserved_usd": 0.0,
            "campaign_reserved_usd": 69.912,
            "actual_cost_usd": None,
        },
    }
    manifest_path = root / "private-manifest.json"
    manifest_path.write_bytes(_canonical(manifest, lf=True))
    provider_binding = {
        "provider": "SYNTHETIC_TEST_BOUNDARY",
        "model_id": "legacy-author",
        "endpoint_origin": None,
        "deployment_version": None,
        "sku": None,
        "capacity": None,
        "credential_boundary_id": None,
    }
    ledger: dict[str, Any] = {
        "artifact_kind": "behavior_map_partial_campaign_v0",
        "schema_version": 0,
        "state": "INTERRUPTED",
        "source_manifest_sha256": _file_hash(manifest_path),
        "source_sha256": source_sha256,
        "selected_list_sha256": selected_list_sha256,
        "primary_model_id": "legacy-author",
        "primary_provider_binding_sha256": _digest(
            "behavior-map-provider-binding-v0", provider_binding
        ),
        "checkpoint_ids": sorted(checkpoint_ids),
        "inventory": sorted(inventory, key=lambda row: row["stage"]),
        "attempted_call_count": 97,
        "reserved_usd": 69.912,
        "cumulative_limit_usd": 70.0,
        "prior_external_reserved_usd": 0.0,
        "campaign_reserved_usd": 69.912,
        "actual_cost_state": "UNKNOWN",
        "retry_policy": "NONE",
        "fallback_policy": "NONE",
        "development_count": 97,
        "sealed_calibration_count": 0,
        "sealed_holdout_count": 0,
        "baseline_predecessor_report_id": "sha256:" + "6" * 64,
        "report_emitted": False,
        "semantic_evaluation_state": "NOT_EVALUATED",
    }
    ledger["inventory_tree_sha256"] = _digest(
        "behavior-map-partial-campaign-inventory-v0", ledger["inventory"]
    )
    ledger["campaign_id"] = _digest("behavior-map-partial-campaign-v0", ledger)
    ledger_path = root / "partial-campaign.json"
    ledger_path.write_bytes(_canonical(ledger, lf=True))
    return checkpoints, manifest_path, ledger_path, ledger, checkpoint_ids


def _migrate(
    checkpoints: Path,
    manifest: Path,
    ledger: Path,
    output: Path,
    campaign_id: str,
) -> dict[str, Any]:
    module = importlib.import_module("triana_labs.behavior_map.checkpoint_migration")
    return module.migrate_extraction_checkpoints(
        source_checkpoint_dir=checkpoints,
        source_manifest_path=manifest,
        source_campaign_path=ledger,
        output_dir=output,
        predecessor_campaign_id=campaign_id,
    )


class _ProviderTrap:
    model_id = "legacy-author"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def complete_json(self, *, stage: str, **_: Any) -> dict[str, Any]:
        self.calls.append(stage)
        raise AssertionError("partial-campaign continuation called a provider")

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


class _PlannedModel(_ProviderTrap):
    def __init__(self, model_id: str, reserved_usd: float) -> None:
        super().__init__()
        self.model_id = model_id
        self.reserved_usd = reserved_usd

    def lineage(self) -> dict[str, Any]:
        lineage = super().lineage()
        lineage["model_id"] = self.model_id
        lineage["budget"] = {
            "max_reserved_usd": self.reserved_usd,
            "reservation_usd_per_call": 0.0,
            "reservation_method": "CONFIGURED_RUN_MAXIMUM",
        }
        return lineage


class _OneFreshExtractionModel(_PlannedModel):
    def complete_json(
        self, *, stage: str, payload: dict[str, Any], schema: Any, **_: Any
    ) -> dict[str, Any]:
        self.calls.append(stage)
        if stage == "semantic-preflight-population":
            return {
                "populations": [
                    {
                        "label": "Synthetic contract checks",
                        "definition": "Synthetic requests used only for contract validation.",
                        "episode_ids": [payload["episodes"][0]["episode_id"]],
                    }
                ],
                "unassigned_episode_ids": [],
                "ambiguous_episode_ids": [],
            }
        if stage == "semantic-preflight-pattern":
            return {
                "patterns": [
                    {
                        "label": "Checks a synthetic request",
                        "definition": "The agent checks a synthetic request before responding.",
                        "occurrence_ids": [
                            payload["behavior_occurrences"][0]["occurrence_id"]
                        ],
                    }
                ]
            }
        assert "episodes" in schema.model_fields
        conversation_id = payload["conversations"][0]["conversation_id"]
        return {
            "episodes": [
                {
                    "local_id": "fresh-demand",
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
                    "grounding_contract_version": 1,
                    "field_grounding": {
                        "goal": [0],
                        "requested_action": [0],
                        "subject": [0],
                        "constraints": [],
                        "fallbacks": [],
                    },
                    "status": "UNKNOWN",
                }
            ],
            "behaviors": [],
        }


class _SchemaValidContinuationModel(_PlannedModel):
    def complete_json(
        self, *, stage: str, payload: dict[str, Any], schema: Any, **_: Any
    ) -> dict[str, Any]:
        self.calls.append(stage)
        if stage.startswith("demand-episodes-and-agent-behaviors-"):
            raise AssertionError("migrated extraction stage was called again")
        fields = set(schema.model_fields)
        if "populations" in fields:
            episodes = payload.get("episodes", [])
            return {
                "populations": (
                    [
                        {
                            "label": "Order-location requests",
                            "definition": "Customers ask where an order is.",
                            "episode_ids": [row["episode_id"] for row in episodes],
                        }
                    ]
                    if episodes
                    else []
                ),
                "unassigned_episode_ids": [],
                "ambiguous_episode_ids": [],
            }
        if "patterns" in fields:
            return {"patterns": []}
        if "matches" in fields:
            return {"matches": []}
        if "audits" in fields:
            return {
                "audits": [
                    {
                        "item_id": next(
                            row[key]
                            for key in ("episode_id", "population_id", "pattern_id")
                            if key in row
                        ),
                        "decision": "SUPPORTED",
                        "reason": "Synthetic continuation audit.",
                    }
                    for row in payload.get("items", [])
                ]
            }
        raise AssertionError(stage)


def _bind_partial_successor(
    manifest_path: Path,
    output: Path,
    ledger: dict[str, Any],
    migration: dict[str, Any],
) -> None:
    manifest = json.loads(manifest_path.read_bytes())
    migration_path = output / "checkpoint-migration.json"
    manifest["checkpoint_migration"] = {
        "path": str(migration_path),
        "sidecar_sha256": _file_hash(migration_path),
        "migration_id": migration["migration_id"],
        "partial_campaign_id": ledger["campaign_id"],
        "baseline_predecessor_report_id": ledger["baseline_predecessor_report_id"],
        "source_manifest_sha256": ledger["source_manifest_sha256"],
        "source_sha256": ledger["source_sha256"],
        "selected_list_sha256": ledger["selected_list_sha256"],
        "primary_model_id": ledger["primary_model_id"],
        "primary_provider_binding_sha256": ledger["primary_provider_binding_sha256"],
        "attempted_call_floor": 97,
        "next_extraction_index": 97,
        "campaign_reserved_usd": 69.912,
        "prior_external_reserved_usd": 0.0,
        "actual_cost_state": "UNKNOWN",
    }
    manifest_path.write_bytes(_canonical(manifest, lf=True))


def test_provider_free_builder_reconstructs_exact_byte_stable_partial_ledger(
    tmp_path: Path,
) -> None:
    checkpoints, manifest, expected_path, expected, _ids = _write_campaign(tmp_path)
    module = importlib.import_module("triana_labs.behavior_map.checkpoint_migration")
    first_path = tmp_path / "built-first.json"
    second_path = tmp_path / "built-second.json"
    kwargs = {
        "source_checkpoint_dir": checkpoints,
        "source_manifest_path": manifest,
        "baseline_predecessor_report_id": "sha256:" + "6" * 64,
        "campaign_reserved_usd": 69.912,
        "prior_external_reserved_usd": 0.0,
        "actual_cost_usd": None,
    }

    first = module.build_partial_campaign_ledger(output_path=first_path, **kwargs)
    second = module.build_partial_campaign_ledger(output_path=second_path, **kwargs)

    assert first == second == expected
    assert (
        first_path.read_bytes()
        == second_path.read_bytes()
        == expected_path.read_bytes()
    )
    assert len(first["inventory"]) == 97
    assert first["inventory_tree_sha256"] == _digest(
        "behavior-map-partial-campaign-inventory-v0", first["inventory"]
    )
    assert [row["stage"] for row in first["inventory"]] == [
        f"demand-episodes-and-agent-behaviors-{index:04d}" for index in range(97)
    ]
    assert len({row["checkpoint_id"] for row in first["inventory"]}) == 97
    assert all(
        set(row)
        == {
            "checkpoint_id",
            "file_sha256",
            "artifact_kind",
            "state",
            "stage",
            "model_id",
            "payload_or_descriptor_sha256",
            "result_sha256",
        }
        for row in first["inventory"]
    )
    assert first["report_emitted"] is False
    assert first["semantic_evaluation_state"] == "NOT_EVALUATED"


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "extra",
        "duplicate",
        "symlink",
        "rename",
        "file_digest",
        "identity",
        "result",
        "descriptor",
        "duplicate_stage",
    ],
)
def test_partial_ledger_builder_refuses_any_inventory_integrity_defect(
    tmp_path: Path, mutation: str
) -> None:
    checkpoints, manifest, _ledger, _expected, _ids = _write_campaign(tmp_path)
    paths = sorted(checkpoints.glob("*.json"))
    target = paths[0]
    if mutation == "missing":
        target.unlink()
    elif mutation in {"extra", "duplicate"}:
        (checkpoints / ("f" * 64 + ".json")).write_bytes(target.read_bytes())
    elif mutation == "symlink":
        original = tmp_path / "original.json"
        target.replace(original)
        target.symlink_to(original)
    elif mutation == "rename":
        target.rename(checkpoints / ("e" * 64 + ".json"))
    else:
        value = json.loads(target.read_bytes())
        if mutation == "file_digest":
            value["unexpected"] = True
        elif mutation == "identity":
            value["identity"]["model_id"] = "wrong-model"
        elif mutation == "result":
            value["result_sha256"] = "sha256:" + "0" * 64
        elif mutation == "descriptor":
            attempt_path = next(
                path
                for path in paths
                if json.loads(path.read_bytes())["artifact_kind"]
                == "behavior_map_attempt_v0"
            )
            target = attempt_path
            value = json.loads(target.read_bytes())
            value["payload_descriptor_sha256"] = "sha256:" + "0" * 64
        else:
            second = paths[1]
            target = second
            value = json.loads(second.read_bytes())
            value["identity"]["stage"] = "demand-episodes-and-agent-behaviors-0000"
            new_id = _digest("behavior-map-checkpoint-v0", value["identity"])
            target = checkpoints / f"{new_id.removeprefix('sha256:')}.json"
            second.unlink()
        target.write_bytes(_canonical(value, lf=True))

    module = importlib.import_module("triana_labs.behavior_map.checkpoint_migration")
    with pytest.raises(ValueError, match="PARTIAL_CAMPAIGN_INVENTORY_INVALID"):
        module.build_partial_campaign_ledger(
            source_checkpoint_dir=checkpoints,
            source_manifest_path=manifest,
            output_path=tmp_path / "built.json",
            baseline_predecessor_report_id="sha256:" + "6" * 64,
            campaign_reserved_usd=69.912,
            prior_external_reserved_usd=0.0,
            actual_cost_usd=None,
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "source",
        "selection",
        "sealed",
        "provider",
        "budget",
        "retry",
        "fallback",
    ],
)
def test_partial_ledger_builder_refuses_manifest_binding_mismatch(
    tmp_path: Path, mutation: str
) -> None:
    checkpoints, manifest_path, _ledger, _expected, _ids = _write_campaign(tmp_path)
    manifest = json.loads(manifest_path.read_bytes())
    if mutation == "source":
        manifest["source"]["sha256"] = "sha256:" + "0" * 64
    elif mutation == "selection":
        manifest["semantic_scope"]["selected_list_sha256"] = "sha256:" + "0" * 64
    elif mutation == "sealed":
        manifest["semantic_scope"]["sealed"]["holdout"] = 1
    elif mutation == "provider":
        manifest["privacy"]["provider_egress"]["model_id"] = "wrong-model"
    elif mutation == "budget":
        manifest["semantic_budget"]["campaign_reserved_usd"] = 0.0
    elif mutation == "retry":
        manifest["method"]["retry_policy"] = "ONE_RETRY"
    else:
        manifest["method"]["fallback_policy"] = "ANOTHER_MODEL"
    manifest_path.write_bytes(_canonical(manifest, lf=True))

    module = importlib.import_module("triana_labs.behavior_map.checkpoint_migration")
    with pytest.raises(ValueError, match="PARTIAL_CAMPAIGN_BINDING_INVALID"):
        module.build_partial_campaign_ledger(
            source_checkpoint_dir=checkpoints,
            source_manifest_path=manifest_path,
            output_path=tmp_path / "built.json",
            baseline_predecessor_report_id="sha256:" + "6" * 64,
            campaign_reserved_usd=69.912,
            prior_external_reserved_usd=0.0,
            actual_cost_usd=None,
        )


def test_partial_ledger_preserves_374_development_denominator_with_97_attempts(
    tmp_path: Path,
) -> None:
    checkpoints, manifest_path, _ledger, _expected, _ids = _write_campaign(tmp_path)
    manifest = json.loads(manifest_path.read_bytes())
    source_path = Path(manifest["source"]["path"])
    traces = [json.loads(line) for line in source_path.read_text().splitlines()]
    traces.extend(
        {
            "contract_kind": "preview_trace",
            "schema_version": 1,
            "privacy_class": "SYNTHETIC",
            "trace_id": f"private-conversation-{index:03d}",
            "source_trace_id": f"source-private-conversation-{index:03d}",
            "events": [
                {
                    "sequence": 0,
                    "event_kind": "USER_MESSAGE",
                    "content": "Where is my order?",
                }
            ],
        }
        for index in range(97, 374)
    )
    source_bytes = b"".join(_canonical(trace, lf=True) for trace in traces)
    source_path.write_bytes(source_bytes)
    selected_ids = sorted(trace["trace_id"] for trace in traces)
    manifest["source"]["sha256"] = "sha256:" + hashlib.sha256(source_bytes).hexdigest()
    manifest["source"]["physical_record_count"] = 374
    manifest["semantic_scope"].update(
        {
            "allowed_trace_ids": selected_ids,
            "development_trace_ids": selected_ids,
            "selected_list_sha256": "sha256:"
            + hashlib.sha256(_canonical(selected_ids)).hexdigest(),
            "development_count": 374,
        }
    )
    manifest["grouping"]["assignments"] = [
        {"group_id": f"group-{item}", "trace_ids": [item]} for item in selected_ids
    ]
    manifest_path.write_bytes(_canonical(manifest, lf=True))
    module = importlib.import_module("triana_labs.behavior_map.checkpoint_migration")

    ledger = module.build_partial_campaign_ledger(
        source_checkpoint_dir=checkpoints,
        source_manifest_path=manifest_path,
        output_path=tmp_path / "built.json",
        baseline_predecessor_report_id="sha256:" + "6" * 64,
        campaign_reserved_usd=69.912,
        prior_external_reserved_usd=0.0,
        actual_cost_usd=None,
    )

    assert ledger["allowed_count"] == 374
    assert ledger["selected_count"] == 374
    assert ledger["development_count"] == 374
    assert ledger["inventory_count"] == 97
    assert ledger["attempted_call_count"] == 97
    assert [row["stage"] for row in ledger["inventory"]] == [
        f"demand-episodes-and-agent-behaviors-{index:04d}" for index in range(97)
    ]


def test_partial_ledger_refuses_inventory_count_above_development_count(
    tmp_path: Path,
) -> None:
    checkpoints, manifest_path, _ledger, _expected, _ids = _write_campaign(tmp_path)
    manifest = json.loads(manifest_path.read_bytes())
    manifest["semantic_scope"]["development_count"] = 96
    manifest_path.write_bytes(_canonical(manifest, lf=True))
    module = importlib.import_module("triana_labs.behavior_map.checkpoint_migration")

    with pytest.raises(ValueError, match="PARTIAL_CAMPAIGN_INVENTORY_INVALID"):
        module.build_partial_campaign_ledger(
            source_checkpoint_dir=checkpoints,
            source_manifest_path=manifest_path,
            output_path=tmp_path / "built.json",
            baseline_predecessor_report_id="sha256:" + "6" * 64,
            campaign_reserved_usd=69.912,
            prior_external_reserved_usd=0.0,
            actual_cost_usd=None,
        )


def _prepare_bound_partial_resume(
    tmp_path: Path,
    *,
    proposed_episodes: bool = False,
) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    checkpoints, manifest_path, ledger_path, ledger, _ids = _write_campaign(
        tmp_path, proposed_episodes=proposed_episodes
    )
    output = tmp_path / "output"
    migration = _migrate(
        checkpoints,
        manifest_path,
        ledger_path,
        output,
        ledger["campaign_id"],
    )
    _bind_partial_successor(manifest_path, output, ledger, migration)
    return manifest_path, output, ledger, migration


def test_resumed_campaign_reservation_is_authorized_and_counted_exactly_once(
    tmp_path: Path,
) -> None:
    manifest, output, _ledger, _migration = _prepare_bound_partial_resume(
        tmp_path, proposed_episodes=True
    )
    primary = _SchemaValidContinuationModel("legacy-author", 53.892)
    auditor = _SchemaValidContinuationModel("legacy-auditor", 16.02)

    report = run_behavior_map(
        manifest,
        output,
        primary_model=primary,
        audit_model=auditor,
        agent_context="Synthetic support agent.",
    )

    assert all(
        not stage.startswith("demand-episodes-and-agent-behaviors-")
        for stage in [*primary.calls, *auditor.calls]
    )
    assert primary.calls or auditor.calls
    assert "SEMANTIC_BUDGET_EXCEEDED" not in {row["code"] for row in report["gaps"]}
    assert report["budget"]["cumulative_limit_usd"] == 70.0
    assert report["budget"]["prior_reserved_usd"] == 0.0
    assert report["budget"]["primary_reserved_usd"] == 53.892
    assert report["budget"]["audit_reserved_usd"] == 16.02
    assert report["budget"]["total_reserved_usd"] == 69.912
    assert report["budget"]["primary_actual_cost_usd"] is None
    assert report["budget"]["audit_actual_cost_usd"] is None
    assert report["baseline_predecessor_report_id"] == "sha256:" + "6" * 64
    assert report["predecessor_campaign_id"] == _ledger["campaign_id"]
    assert "semantic_evaluation_state" not in report


def test_fresh_successor_semantic_call_does_not_inherit_not_evaluated(
    tmp_path: Path,
) -> None:
    manifest, output, ledger, migration = _prepare_bound_partial_resume(tmp_path)
    migrated_id = migration["migrations"][0]["checkpoint_id"]
    (
        output
        / "behavior-map-checkpoints"
        / f"{migrated_id.removeprefix('sha256:')}.json"
    ).unlink()
    primary = _OneFreshExtractionModel("legacy-author", 0.0)

    report = run_behavior_map(
        manifest,
        output,
        primary_model=primary,
        audit_model=None,
        agent_context="Synthetic support agent.",
    )

    assert primary.calls[:3] == [
        "semantic-preflight-extraction",
        "semantic-preflight-population",
        "semantic-preflight-pattern",
    ]
    assert len(primary.calls) == 4
    assert primary.calls[3].startswith("demand-episodes-and-agent-behaviors-")
    assert "semantic_evaluation_state" not in report
    assert report["baseline_predecessor_report_id"] == "sha256:" + "6" * 64
    assert report["predecessor_campaign_id"] == ledger["campaign_id"]


def test_partial_campaign_migrates_without_forging_a_completed_report(
    tmp_path: Path,
) -> None:
    checkpoints, manifest, ledger_path, ledger, checkpoint_ids = _write_campaign(
        tmp_path
    )
    source_snapshot = {
        path.name: path.read_bytes()
        for path in [manifest, ledger_path, *checkpoints.glob("*.json")]
    }

    result = _migrate(
        checkpoints,
        manifest,
        ledger_path,
        tmp_path / "output",
        ledger["campaign_id"],
    )
    replay = _migrate(
        checkpoints,
        manifest,
        ledger_path,
        tmp_path / "replay-output",
        ledger["campaign_id"],
    )

    assert replay == result
    assert (tmp_path / "replay-output" / "checkpoint-migration.json").read_bytes() == (
        tmp_path / "output" / "checkpoint-migration.json"
    ).read_bytes()
    assert result["predecessor_campaign_id"] == ledger["campaign_id"]
    assert "predecessor_report_id" not in result
    assert result["summary"] == {"migrated": 87, "refused": 10}
    assert result["runtime_handoff"]["predecessor_attempted_call_count"] == 97
    assert result["runtime_handoff"]["prior_reserved_usd"] == 0.0
    assert result["runtime_handoff"]["next_extraction_index"] == 97
    assert result["runtime_handoff"]["attempted_call_floor"] == 97
    assert result["runtime_handoff"]["campaign_reserved_usd"] == 69.912
    assert result["runtime_handoff"]["prior_external_reserved_usd"] == 0.0
    assert result["runtime_handoff"]["actual_cost_state"] == "UNKNOWN"
    assert result["runtime_handoff"]["source_sha256"] == ledger["source_sha256"]
    assert (
        result["runtime_handoff"]["selected_list_sha256"]
        == ledger["selected_list_sha256"]
    )
    assert {
        row["predecessor_checkpoint_id"]
        for row in [*result["migrations"], *result["refusals"]]
    } == set(checkpoint_ids)
    assert {
        path.name: path.read_bytes()
        for path in [manifest, ledger_path, *checkpoints.glob("*.json")]
    } == source_snapshot
    serialized = json.dumps(result, sort_keys=True)
    for private_path in (checkpoints, manifest, ledger_path):
        assert str(private_path) not in serialized
    assert "behavior_map_report_v0" not in serialized
    assert result["baseline_predecessor_report_id"] == "sha256:" + "6" * 64
    assert result["report_emitted"] is False
    assert result["semantic_evaluation_state"] == "NOT_EVALUATED"

    successor_manifest = tmp_path / "successor-manifest.json"
    successor = json.loads(manifest.read_bytes())
    migration_path = tmp_path / "output" / "checkpoint-migration.json"
    successor["checkpoint_migration"] = {
        "path": str(migration_path),
        "sidecar_sha256": _file_hash(migration_path),
        "migration_id": result["migration_id"],
        "partial_campaign_id": ledger["campaign_id"],
        "baseline_predecessor_report_id": "sha256:" + "6" * 64,
        "source_manifest_sha256": ledger["source_manifest_sha256"],
        "source_sha256": ledger["source_sha256"],
        "selected_list_sha256": ledger["selected_list_sha256"],
        "primary_model_id": ledger["primary_model_id"],
        "primary_provider_binding_sha256": ledger["primary_provider_binding_sha256"],
        "attempted_call_floor": 97,
        "next_extraction_index": 97,
        "campaign_reserved_usd": 69.912,
        "prior_external_reserved_usd": 0.0,
        "actual_cost_state": "UNKNOWN",
    }
    successor_manifest.write_bytes(_canonical(successor, lf=True))
    trap = _ProviderTrap()

    runtime = run_behavior_map(
        successor_manifest,
        tmp_path / "output",
        primary_model=trap,
        audit_model=None,
        agent_context="Synthetic support agent.",
    )

    assert trap.calls == []
    assert runtime["provider_lineage"]["primary"]["attempted_call_count"] >= 97
    assert runtime["budget"]["prior_reserved_usd"] == 0.0
    assert runtime["budget"]["total_reserved_usd"] == 69.912
    assert runtime["baseline_predecessor_report_id"] == "sha256:" + "6" * 64
    assert runtime["predecessor_campaign_id"] == ledger["campaign_id"]
    assert runtime["semantic_evaluation_state"] == "NOT_EVALUATED"
    runtime_text = json.dumps(runtime, sort_keys=True)
    assert str(migration_path) not in runtime_text
    assert str(ledger_path) not in runtime_text


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_checkpoint_id",
        "extra_checkpoint_id",
        "campaign_id",
        "source_manifest_sha256",
        "source_sha256",
        "selected_list_sha256",
        "primary_model_id",
        "primary_provider_binding_sha256",
        "attempted_call_count",
        "reserved_usd",
    ],
)
def test_partial_campaign_refuses_any_authority_or_conservation_mismatch(
    tmp_path: Path, mutation: str
) -> None:
    checkpoints, manifest, ledger_path, ledger, _checkpoint_ids = _write_campaign(
        tmp_path
    )
    tampered = deepcopy(ledger)
    if mutation == "missing_checkpoint_id":
        tampered["checkpoint_ids"] = tampered["checkpoint_ids"][:-1]
    elif mutation == "extra_checkpoint_id":
        tampered["checkpoint_ids"] = [
            *tampered["checkpoint_ids"],
            "sha256:" + "e" * 64,
        ]
    elif mutation == "attempted_call_count":
        tampered[mutation] = 96
    elif mutation == "reserved_usd":
        tampered[mutation] = 0.0
    elif mutation == "primary_model_id":
        tampered[mutation] = "wrong-model"
    else:
        tampered[mutation] = "sha256:" + "0" * 64
    if mutation != "campaign_id":
        tampered["campaign_id"] = _digest(
            "behavior-map-partial-campaign-v0",
            {key: value for key, value in tampered.items() if key != "campaign_id"},
        )
    ledger_path.write_bytes(_canonical(tampered, lf=True))

    with pytest.raises(
        ValueError,
        match="PARTIAL_CAMPAIGN_(INVALID|CHECKPOINT_SET_MISMATCH|BINDING_INVALID)",
    ):
        _migrate(
            checkpoints,
            manifest,
            ledger_path,
            tmp_path / "output",
            ledger["campaign_id"],
        )
