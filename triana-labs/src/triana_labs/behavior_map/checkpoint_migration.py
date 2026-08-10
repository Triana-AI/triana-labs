"""Deterministic, provider-free migration of legacy extraction checkpoints."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, cast

from pydantic import ValidationError

from .contracts import ExtractionBatch

JsonObject = dict[str, Any]

_EXTRACTION_STAGE_PREFIX = "demand-episodes-and-agent-behaviors-"
_MIGRATION_REASON = "ADD_EXPLICIT_GROUNDING_CONTRACT_VERSION"


def _canonical(value: Any, *, lf: bool = False) -> bytes:
    payload = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return payload + (b"\n" if lf else b"")


def _digest(domain: str, value: Any) -> str:
    return (
        "sha256:"
        + hashlib.sha256(domain.encode("utf-8") + b"\0" + _canonical(value)).hexdigest()
    )


def _file_hash(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _write_once(path: Path, payload: bytes) -> None:
    if path.exists():
        raise FileExistsError(path)
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    temporary = Path(name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        path.chmod(0o600)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _validated_paths(
    source_checkpoint_dir: str | Path,
    source_report_path: str | Path,
    output_dir: str | Path,
) -> tuple[Path, Path, Path]:
    source = Path(source_checkpoint_dir)
    report = Path(source_report_path)
    output = Path(output_dir)
    if (
        not source.is_absolute()
        or not report.is_absolute()
        or not output.is_absolute()
        or source.is_symlink()
        or report.is_symlink()
        or output.is_symlink()
        or not source.is_dir()
        or not report.is_file()
    ):
        raise ValueError("MIGRATION_PATH_INVALID")
    source_resolved = source.resolve(strict=True)
    report_resolved = report.resolve(strict=True)
    output_resolved = output.resolve()
    if (
        output_resolved == source_resolved
        or output_resolved == report_resolved
        or source_resolved in output_resolved.parents
        or output_resolved in source_resolved.parents
        or report_resolved in output_resolved.parents
    ):
        raise ValueError("MIGRATION_PATH_INVALID")
    return source, report, output


def _read_object(path: Path, *, code: str) -> tuple[JsonObject, bytes]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("MIGRATION_PATH_INVALID")
    try:
        payload = path.read_bytes()
        value = json.loads(payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(code) from error
    if not isinstance(value, dict):
        raise ValueError(code)  # noqa: TRY004
    return cast(JsonObject, value), payload


def _validate_identity(value: JsonObject, checkpoint_id: str) -> JsonObject:
    identity = value.get("identity")
    if (
        not isinstance(identity, dict)
        or _digest("behavior-map-checkpoint-v0", identity) != checkpoint_id
    ):
        raise ValueError("CHECKPOINT_HASH_INVALID")
    return cast(JsonObject, identity)


def _refusal(checkpoint_id: str, checkpoint_sha256: str, code: str) -> JsonObject:
    return {
        "predecessor_checkpoint_id": checkpoint_id,
        "predecessor_checkpoint_sha256": checkpoint_sha256,
        "code": code,
        "stage": "EXTRACTION",
        "retryable": False,
    }


def _grounding_is_complete(episode: JsonObject) -> bool:
    citations = episode.get("citations")
    grounding = episode.get("field_grounding")
    if not isinstance(citations, list) or not isinstance(grounding, dict):
        return False
    citation_count = len(citations)

    def valid_indexes(value: Any, *, required: bool) -> bool:
        return (
            isinstance(value, list)
            and (bool(value) or not required)
            and all(
                isinstance(index, int)
                and not isinstance(index, bool)
                and 0 <= index < citation_count
                for index in value
            )
        )

    if any(
        not valid_indexes(grounding.get(field), required=True)
        for field in ("goal", "requested_action", "subject")
    ):
        return False
    for field in ("constraints", "fallbacks"):
        values = episode.get(field)
        bindings = grounding.get(field)
        if (
            not isinstance(values, list)
            or not isinstance(bindings, list)
            or len(values) != len(bindings)
            or any(not valid_indexes(row, required=True) for row in bindings)
        ):
            return False
    return True


def _sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("sha256:")
        and len(value) == 71
        and all(character in "0123456789abcdef" for character in value[7:])
    )


def _partial_paths(
    source_checkpoint_dir: str | Path,
    source_manifest_path: str | Path,
    output_path: str | Path,
) -> tuple[Path, Path, Path]:
    source = Path(source_checkpoint_dir)
    manifest = Path(source_manifest_path)
    output = Path(output_path)
    if (
        not source.is_absolute()
        or not manifest.is_absolute()
        or not output.is_absolute()
        or source.is_symlink()
        or manifest.is_symlink()
        or output.is_symlink()
        or not source.is_dir()
        or not manifest.is_file()
    ):
        raise ValueError("PARTIAL_CAMPAIGN_INVENTORY_INVALID")
    source_resolved = source.resolve(strict=True)
    manifest_resolved = manifest.resolve(strict=True)
    output_resolved = output.resolve()
    if (
        output_resolved == source_resolved
        or output_resolved == manifest_resolved
        or source_resolved in output_resolved.parents
        or output_resolved in source_resolved.parents
        or manifest_resolved in output_resolved.parents
    ):
        raise ValueError("PARTIAL_CAMPAIGN_INVENTORY_INVALID")
    return source, manifest, output


def _manifest_partial_bindings(manifest_path: Path) -> JsonObject:
    manifest, manifest_bytes = _read_object(
        manifest_path, code="PARTIAL_CAMPAIGN_BINDING_INVALID"
    )
    source = manifest.get("source")
    scope = manifest.get("semantic_scope")
    privacy = manifest.get("privacy")
    method = manifest.get("method")
    budget = manifest.get("semantic_budget")
    if not all(isinstance(item, dict) for item in (source, scope, privacy, budget)):
        raise ValueError("PARTIAL_CAMPAIGN_BINDING_INVALID")
    source = cast(JsonObject, source)
    scope = cast(JsonObject, scope)
    privacy = cast(JsonObject, privacy)
    method = cast(JsonObject, method) if isinstance(method, dict) else {}
    budget = cast(JsonObject, budget)
    selection = scope.get("selection", {})
    if not isinstance(selection, dict):
        raise ValueError("PARTIAL_CAMPAIGN_BINDING_INVALID")  # noqa: TRY004
    selection = cast(JsonObject, selection)
    sealed = scope.get("sealed", scope.get("sealed_counts", {}))
    egress = privacy.get("provider_egress")
    development_ids = scope.get("development_trace_ids", scope.get("allowed_trace_ids"))
    selected_list_sha256 = scope.get(
        "selected_list_sha256", selection.get("selected_list_sha256")
    )
    valid_selection_hashes = (
        {
            "sha256:" + hashlib.sha256(_canonical(sorted(development_ids))).hexdigest(),
            "sha256:"
            + hashlib.sha256(
                ("\n".join(sorted(development_ids)) + "\n").encode()
            ).hexdigest(),
        }
        if isinstance(development_ids, list)
        and all(isinstance(item, str) for item in development_ids)
        else set()
    )
    source_path_value = source.get("path")
    if not isinstance(source_path_value, str):
        raise ValueError("PARTIAL_CAMPAIGN_BINDING_INVALID")  # noqa: TRY004
    source_path = Path(source_path_value)
    if not source_path.is_absolute():
        source_path = manifest_path.parent / source_path
    if source_path.is_symlink() or not source_path.is_file():
        raise ValueError("PARTIAL_CAMPAIGN_BINDING_INVALID")
    try:
        source_bytes = source_path.read_bytes()
    except OSError as error:
        raise ValueError("PARTIAL_CAMPAIGN_BINDING_INVALID") from error
    if (
        manifest.get("artifact_kind") != "evidence_bundle_manifest_v0"
        or manifest.get("schema_version") != 0
        or source.get("sha256") != _file_hash(source_bytes)
        or not isinstance(development_ids, list)
        or any(not isinstance(item, str) for item in development_ids)
        or len(set(development_ids)) != len(development_ids)
        or not _sha256(selected_list_sha256)
        or selected_list_sha256 not in valid_selection_hashes
        or scope.get("development_count", selection.get("development_count"))
        != len(development_ids)
        or not isinstance(sealed, dict)
        or (
            "sealed" in scope
            and (sealed.get("calibration") != 0 or sealed.get("holdout") != 0)
        )
        or not isinstance(egress, dict)
        or privacy.get("execution_location") != "LOCAL_PRIVATE"
        or not isinstance(egress.get("model_id"), str)
        or method.get(
            "retry_policy",
            "NONE" if budget.get("retry_allowed") is False else None,
        )
        != "NONE"
        or method.get(
            "fallback_policy",
            "NONE" if budget.get("fallback_allowed") is False else None,
        )
        != "NONE"
    ):
        raise ValueError("PARTIAL_CAMPAIGN_BINDING_INVALID")
    campaign_reserved = budget.get(
        "campaign_reserved_usd", budget.get("run_max_reserved_usd")
    )
    for value in (
        budget.get("cumulative_limit_usd"),
        budget.get("prior_reserved_usd"),
        campaign_reserved,
    ):
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            raise ValueError("PARTIAL_CAMPAIGN_BINDING_INVALID")
    post_reservation = budget.get("post_reservation_total_usd")
    if post_reservation is not None and post_reservation != (
        budget["prior_reserved_usd"] + campaign_reserved
    ):
        raise ValueError("PARTIAL_CAMPAIGN_BINDING_INVALID")
    provider_binding = {
        "provider": egress.get("provider", "SYNTHETIC_TEST_BOUNDARY")
        if privacy.get("authorization") == "SYNTHETIC_FIXTURE"
        else egress.get("provider"),
        "model_id": egress.get("model_id"),
        "endpoint_origin": egress.get("endpoint_origin"),
        "deployment_version": egress.get("deployment_version"),
        "sku": egress.get("sku"),
        "capacity": egress.get("capacity"),
        "credential_boundary_id": egress.get("credential_boundary_id"),
    }
    return {
        "manifest_sha256": _file_hash(manifest_bytes),
        "source_sha256": source["sha256"],
        "selected_list_sha256": selected_list_sha256,
        "primary_model_id": egress["model_id"],
        "primary_provider_binding_sha256": _digest(
            "behavior-map-provider-binding-v0", provider_binding
        ),
        "development_count": scope.get(
            "development_count", selection.get("development_count")
        ),
        "allowed_count": len(development_ids),
        "selected_count": selection.get("selected_count", len(development_ids)),
        "sealed_calibration_count": sealed.get(
            "calibration", selection.get("sealed_calibration_count")
        ),
        "sealed_holdout_count": sealed.get(
            "holdout", selection.get("sealed_holdout_count")
        ),
        "cumulative_limit_usd": budget["cumulative_limit_usd"],
        "prior_external_reserved_usd": budget["prior_reserved_usd"],
        "campaign_reserved_usd": campaign_reserved,
        "retry_policy": method.get("retry_policy", "NONE"),
        "fallback_policy": method.get("fallback_policy", "NONE"),
        "provider_binding": provider_binding,
    }


def _partial_inventory(source: Path) -> tuple[list[JsonObject], list[str]]:
    paths = sorted(source.glob("*.json"), key=lambda path: path.name)
    if not paths or any(path.is_symlink() for path in paths):
        raise ValueError("PARTIAL_CAMPAIGN_INVENTORY_INVALID")
    inventory: list[JsonObject] = []
    checkpoint_ids: list[str] = []
    stages: list[str] = []
    for path in paths:
        value, payload = _read_object(path, code="PARTIAL_CAMPAIGN_INVENTORY_INVALID")
        checkpoint_id = "sha256:" + path.stem
        try:
            identity = _validate_identity(value, checkpoint_id)
        except ValueError as error:
            raise ValueError("PARTIAL_CAMPAIGN_INVENTORY_INVALID") from error
        artifact_kind = value.get("artifact_kind")
        expected_keys = (
            {
                "artifact_kind",
                "schema_version",
                "identity",
                "result",
                "result_sha256",
                "payload",
            }
            if artifact_kind == "behavior_map_checkpoint_v0"
            else {
                "artifact_kind",
                "schema_version",
                "identity",
                "state",
                "failure_code",
                "payload",
                "payload_descriptor_sha256",
            }
        )
        stage = identity.get("stage")
        if (
            set(value) != expected_keys
            or value.get("schema_version") != 0
            or not isinstance(stage, str)
            or not stage.startswith(_EXTRACTION_STAGE_PREFIX)
            or not isinstance(identity.get("model_id"), str)
        ):
            raise ValueError("PARTIAL_CAMPAIGN_INVENTORY_INVALID")
        if artifact_kind == "behavior_map_checkpoint_v0":
            result = value.get("result")
            if value.get("result_sha256") != _digest(
                "behavior-map-checkpoint-result-v0", result
            ):
                raise ValueError("PARTIAL_CAMPAIGN_INVENTORY_INVALID")
            state = "SUCCEEDED"
            payload_hash = identity.get("payload_sha256")
            result_hash = value.get("result_sha256")
        elif artifact_kind == "behavior_map_attempt_v0":
            descriptor = value.get("payload")
            if value.get("state") not in {"FAILED", "IN_FLIGHT"} or value.get(
                "payload_descriptor_sha256"
            ) != _digest("behavior-map-attempt-descriptor-v0", descriptor):
                raise ValueError("PARTIAL_CAMPAIGN_INVENTORY_INVALID")
            state = value["state"]
            payload_hash = value["payload_descriptor_sha256"]
            result_hash = None
        else:
            raise ValueError("PARTIAL_CAMPAIGN_INVENTORY_INVALID")
        if not _sha256(payload_hash) or (
            result_hash is not None and not _sha256(result_hash)
        ):
            raise ValueError("PARTIAL_CAMPAIGN_INVENTORY_INVALID")
        checkpoint_ids.append(checkpoint_id)
        stages.append(stage)
        inventory.append(
            {
                "checkpoint_id": checkpoint_id,
                "file_sha256": _file_hash(payload),
                "artifact_kind": artifact_kind,
                "state": state,
                "stage": stage,
                "model_id": identity["model_id"],
                "payload_or_descriptor_sha256": payload_hash,
                "result_sha256": result_hash,
            }
        )
    inventory.sort(key=lambda row: cast(str, row["stage"]))
    expected_stages = [
        f"{_EXTRACTION_STAGE_PREFIX}{index:04d}" for index in range(len(inventory))
    ]
    if [row["stage"] for row in inventory] != expected_stages or len(
        set(checkpoint_ids)
    ) != len(checkpoint_ids):
        raise ValueError("PARTIAL_CAMPAIGN_INVENTORY_INVALID")
    return inventory, sorted(checkpoint_ids)


def build_partial_campaign_ledger(
    *,
    source_checkpoint_dir: str | Path,
    source_manifest_path: str | Path,
    output_path: str | Path,
    baseline_predecessor_report_id: str,
    campaign_reserved_usd: float,
    prior_external_reserved_usd: float,
    actual_cost_usd: float | None,
) -> JsonObject:
    """Build a provider-free, non-report ledger for an interrupted campaign."""

    source, manifest_path, output = _partial_paths(
        source_checkpoint_dir, source_manifest_path, output_path
    )
    inventory, checkpoint_ids = _partial_inventory(source)
    manifest_preview, _manifest_bytes = _read_object(
        manifest_path, code="PARTIAL_CAMPAIGN_BINDING_INVALID"
    )
    scope_preview = manifest_preview.get("semantic_scope")
    selection_preview = (
        scope_preview.get("selection", {}) if isinstance(scope_preview, dict) else {}
    )
    declared_development_count = (
        scope_preview.get(
            "development_count",
            selection_preview.get("development_count")
            if isinstance(selection_preview, dict)
            else None,
        )
        if isinstance(scope_preview, dict)
        else None
    )
    if (
        isinstance(declared_development_count, int)
        and not isinstance(declared_development_count, bool)
        and len(inventory) > declared_development_count
    ):
        raise ValueError("PARTIAL_CAMPAIGN_INVENTORY_INVALID")
    bindings = _manifest_partial_bindings(manifest_path)
    if (
        not _sha256(baseline_predecessor_report_id)
        or campaign_reserved_usd != bindings["campaign_reserved_usd"]
        or prior_external_reserved_usd != bindings["prior_external_reserved_usd"]
        or not inventory
        or not isinstance(bindings["sealed_calibration_count"], int)
        or isinstance(bindings["sealed_calibration_count"], bool)
        or bindings["sealed_calibration_count"] < 0
        or not isinstance(bindings["sealed_holdout_count"], int)
        or isinstance(bindings["sealed_holdout_count"], bool)
        or bindings["sealed_holdout_count"] < 0
        or any(row["model_id"] != bindings["primary_model_id"] for row in inventory)
    ):
        raise ValueError("PARTIAL_CAMPAIGN_BINDING_INVALID")
    if actual_cost_usd is not None and (
        isinstance(actual_cost_usd, bool) or actual_cost_usd < 0
    ):
        raise ValueError("PARTIAL_CAMPAIGN_BINDING_INVALID")
    ledger = _partial_ledger_value(
        bindings=bindings,
        inventory=inventory,
        checkpoint_ids=checkpoint_ids,
        baseline_predecessor_report_id=baseline_predecessor_report_id,
        campaign_reserved_usd=campaign_reserved_usd,
        prior_external_reserved_usd=prior_external_reserved_usd,
        actual_cost_usd=actual_cost_usd,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_once(output, _canonical(ledger, lf=True))
    return ledger


def _partial_ledger_value(
    *,
    bindings: JsonObject,
    inventory: list[JsonObject],
    checkpoint_ids: list[str],
    baseline_predecessor_report_id: str,
    campaign_reserved_usd: float,
    prior_external_reserved_usd: float,
    actual_cost_usd: float | None,
) -> JsonObject:
    ledger: JsonObject = {
        "artifact_kind": "behavior_map_partial_campaign_v0",
        "schema_version": 0,
        "state": "INTERRUPTED",
        "source_manifest_sha256": bindings["manifest_sha256"],
        "source_sha256": bindings["source_sha256"],
        "selected_list_sha256": bindings["selected_list_sha256"],
        "primary_model_id": bindings["primary_model_id"],
        "primary_provider_binding_sha256": bindings["primary_provider_binding_sha256"],
        "checkpoint_ids": checkpoint_ids,
        "inventory": inventory,
        "attempted_call_count": len(inventory),
        "reserved_usd": campaign_reserved_usd,
        "cumulative_limit_usd": bindings["cumulative_limit_usd"],
        "prior_external_reserved_usd": prior_external_reserved_usd,
        "campaign_reserved_usd": campaign_reserved_usd,
        "actual_cost_state": "UNKNOWN" if actual_cost_usd is None else "RECORDED",
        "retry_policy": bindings["retry_policy"],
        "fallback_policy": bindings["fallback_policy"],
        "development_count": bindings["development_count"],
        "sealed_calibration_count": bindings["sealed_calibration_count"],
        "sealed_holdout_count": bindings["sealed_holdout_count"],
        "baseline_predecessor_report_id": baseline_predecessor_report_id,
        "report_emitted": False,
        "semantic_evaluation_state": "NOT_EVALUATED",
    }
    ledger["inventory_tree_sha256"] = _digest(
        "behavior-map-partial-campaign-inventory-v0", inventory
    )
    if len(inventory) != bindings["development_count"]:
        ledger.update(
            {
                "allowed_count": bindings["allowed_count"],
                "selected_count": bindings["selected_count"],
                "inventory_count": len(inventory),
            }
        )
    ledger["campaign_id"] = _digest("behavior-map-partial-campaign-v0", ledger)
    return ledger


def _migrate_completed_extraction_checkpoints(
    *,
    source_checkpoint_dir: str | Path,
    source_report_path: str | Path,
    output_dir: str | Path,
    predecessor_report_id: str,
    _partial_authority: JsonObject | None = None,
) -> JsonObject:
    """Migrate exact grounded extraction successes without model execution."""

    if _partial_authority is None:
        source, report_path, destination = _validated_paths(
            source_checkpoint_dir, source_report_path, output_dir
        )
        report, _report_bytes = _read_object(
            report_path, code="PREDECESSOR_REPORT_MISMATCH"
        )
        report_checkpoint_ids = report.get("checkpoint_ids", report.get("checkpoints"))
        if (
            report.get("artifact_kind") != "behavior_map_report_v0"
            or report.get("schema_version") != 0
            or report.get("report_id") != predecessor_report_id
            or not isinstance(report_checkpoint_ids, list)
            or any(not isinstance(item, str) for item in report_checkpoint_ids)
        ):
            raise ValueError("PREDECESSOR_REPORT_MISMATCH")
        authorized_ids = set(cast(list[str], report_checkpoint_ids))
        primary_lineage = report.get("provider_lineage", {}).get("primary", {})
        if not isinstance(primary_lineage, dict):
            raise ValueError("PREDECESSOR_REPORT_MISMATCH")
        provider_binding = {
            key: primary_lineage.get(key)
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
        report_budget = report.get("budget", {})
        if not isinstance(report_budget, dict):
            raise ValueError("PREDECESSOR_REPORT_MISMATCH")
    else:
        source = Path(source_checkpoint_dir)
        destination = Path(output_dir)
        authorized_ids = set(cast(list[str], _partial_authority["checkpoint_ids"]))
        primary_lineage = {
            "model_id": _partial_authority["primary_model_id"],
            "attempted_call_count": _partial_authority["attempted_call_count"],
        }
        provider_binding = cast(JsonObject, _partial_authority["provider_binding"])
        report = {
            "source": {
                "source_sha256": _partial_authority["source_sha256"],
                "selected_list_sha256": _partial_authority["selected_list_sha256"],
            }
        }
        report_budget = {
            "prior_reserved_usd": _partial_authority["prior_external_reserved_usd"]
        }

    checkpoint_paths = sorted(source.glob("*.json"), key=lambda path: path.name)
    if any(path.is_symlink() for path in checkpoint_paths):
        raise ValueError("MIGRATION_PATH_INVALID")
    destination.mkdir(parents=True, exist_ok=False)
    destination.chmod(0o700)
    checkpoints_destination = destination / "behavior-map-checkpoints"
    checkpoints_destination.mkdir(mode=0o700)

    migrations: list[JsonObject] = []
    refusals: list[JsonObject] = []
    for path in checkpoint_paths:
        value, source_bytes = _read_object(path, code="CHECKPOINT_HASH_INVALID")
        checkpoint_id = "sha256:" + path.stem
        if checkpoint_id not in authorized_ids:
            raise ValueError("PREDECESSOR_REPORT_MISMATCH")
        identity = _validate_identity(value, checkpoint_id)
        checkpoint_sha256 = _file_hash(source_bytes)
        artifact_kind = value.get("artifact_kind")
        if artifact_kind == "behavior_map_attempt_v0":
            descriptor = value.get("payload")
            if value.get("schema_version") != 0 or value.get(
                "payload_descriptor_sha256"
            ) != _digest("behavior-map-attempt-descriptor-v0", descriptor):
                raise ValueError("CHECKPOINT_HASH_INVALID")
            state = value.get("state")
            code = (
                "LEGACY_EXTRACTION_ATTEMPT_FAILED"
                if state == "FAILED"
                else "LEGACY_EXTRACTION_ATTEMPT_IN_FLIGHT"
                if state == "IN_FLIGHT"
                else "CHECKPOINT_STATE_NOT_MIGRATABLE"
            )
            refusals.append(_refusal(checkpoint_id, checkpoint_sha256, code))
            continue
        if (
            artifact_kind != "behavior_map_checkpoint_v0"
            or value.get("schema_version") != 0
        ):
            raise ValueError("CHECKPOINT_HASH_INVALID")
        result = value.get("result")
        if not isinstance(result, dict) or value.get("result_sha256") != _digest(
            "behavior-map-checkpoint-result-v0", result
        ):
            raise ValueError("CHECKPOINT_HASH_INVALID")
        if not str(identity.get("stage", "")).startswith(_EXTRACTION_STAGE_PREFIX):
            refusals.append(
                _refusal(
                    checkpoint_id,
                    checkpoint_sha256,
                    "CHECKPOINT_STAGE_NOT_MIGRATABLE",
                )
            )
            continue
        episodes = result.get("episodes")
        if not isinstance(episodes, list) or any(
            not isinstance(row, dict) or "field_grounding" not in row
            for row in episodes
        ):
            refusals.append(
                _refusal(
                    checkpoint_id,
                    checkpoint_sha256,
                    "LEGACY_EXTRACTION_FIELD_GROUNDING_MISSING",
                )
            )
            continue
        if any(not _grounding_is_complete(cast(JsonObject, row)) for row in episodes):
            refusals.append(
                _refusal(
                    checkpoint_id,
                    checkpoint_sha256,
                    "LEGACY_EXTRACTION_FIELD_GROUNDING_INVALID",
                )
            )
            continue
        migrated_result = {
            **result,
            "episodes": [
                {**cast(JsonObject, row), "grounding_contract_version": 1}
                for row in episodes
            ],
        }
        try:
            validated_result = ExtractionBatch.model_validate(
                migrated_result, strict=True
            ).model_dump(mode="json")
        except ValidationError as error:
            raise ValueError("CHECKPOINT_SCHEMA_INVALID") from error
        from . import _EXTRACT_SYSTEM, _checkpoint_identity

        migrated_identity, migrated_checkpoint_hex = _checkpoint_identity(
            stage=cast(str, identity["stage"]),
            model_id=cast(str, identity["model_id"]),
            system=_EXTRACT_SYSTEM,
            payload=cast(JsonObject, value["payload"]),
            schema=ExtractionBatch,
            provider_binding=provider_binding,
        )
        migrated_checkpoint_id = "sha256:" + migrated_checkpoint_hex
        result_sha256 = _digest("behavior-map-checkpoint-result-v0", validated_result)
        migrated_checkpoint: JsonObject = {
            **value,
            "identity": migrated_identity,
            "result": validated_result,
            "result_sha256": result_sha256,
        }
        _write_once(
            checkpoints_destination
            / f"{migrated_checkpoint_id.removeprefix('sha256:')}.json",
            _canonical(migrated_checkpoint, lf=True),
        )
        migrations.append(
            {
                "predecessor_checkpoint_id": checkpoint_id,
                "predecessor_checkpoint_sha256": checkpoint_sha256,
                "checkpoint_id": migrated_checkpoint_id,
                "result_sha256": result_sha256,
                "migration_reason": _MIGRATION_REASON,
            }
        )

    migration: JsonObject = {
        "artifact_kind": "behavior_map_checkpoint_migration_v0",
        "schema_version": 0,
        "summary": {"migrated": len(migrations), "refused": len(refusals)},
        "migrations": migrations,
        "refusals": refusals,
        "runtime_handoff": {
            "primary_model_id": primary_lineage.get("model_id"),
            "primary_provider_binding_sha256": _digest(
                "behavior-map-provider-binding-v0", provider_binding
            ),
            "source_sha256": cast(JsonObject, report.get("source", {})).get(
                "source_sha256"
            ),
            "selected_list_sha256": cast(JsonObject, report.get("source", {})).get(
                "selected_list_sha256"
            ),
            "predecessor_attempted_call_count": primary_lineage.get(
                "attempted_call_count", 0
            ),
            "prior_reserved_usd": report_budget.get(
                "prior_reserved_usd", report_budget.get("total_reserved_usd", 0.0)
            ),
            "refused_conversation_ids": sorted(
                {
                    conversation_id
                    for path in checkpoint_paths
                    for value, _payload in [
                        _read_object(path, code="CHECKPOINT_HASH_INVALID")
                    ]
                    for conversation_id in (
                        [
                            row.get("conversation_id")
                            for row in cast(
                                list[JsonObject],
                                cast(JsonObject, value.get("payload", {})).get(
                                    "conversations", []
                                ),
                            )
                            if isinstance(row.get("conversation_id"), str)
                        ]
                        if value.get("artifact_kind") == "behavior_map_checkpoint_v0"
                        else cast(
                            list[str],
                            cast(JsonObject, value.get("payload", {})).get(
                                "conversation_ids", []
                            ),
                        )
                    )
                    if isinstance(conversation_id, str)
                    and "sha256:" + path.stem
                    in {cast(str, row["predecessor_checkpoint_id"]) for row in refusals}
                }
            ),
        },
    }
    if _partial_authority is None:
        migration["predecessor_report_id"] = predecessor_report_id
    else:
        migration.update(
            {
                "predecessor_campaign_id": predecessor_report_id,
                "baseline_predecessor_report_id": _partial_authority[
                    "baseline_predecessor_report_id"
                ],
                "report_emitted": False,
                "semantic_evaluation_state": "NOT_EVALUATED",
            }
        )
        migration["runtime_handoff"].update(
            {
                "primary_provider_binding_sha256": _partial_authority[
                    "primary_provider_binding_sha256"
                ],
                "next_extraction_index": _partial_authority["attempted_call_count"],
                "attempted_call_floor": _partial_authority["attempted_call_count"],
                "campaign_reserved_usd": _partial_authority["campaign_reserved_usd"],
                "prior_external_reserved_usd": _partial_authority[
                    "prior_external_reserved_usd"
                ],
                "actual_cost_state": _partial_authority["actual_cost_state"],
                "source_manifest_sha256": _partial_authority["source_manifest_sha256"],
            }
        )
    migration["migration_id"] = _digest(
        "behavior-map-checkpoint-migration-v0", migration
    )
    _write_once(
        destination / "checkpoint-migration.json", _canonical(migration, lf=True)
    )
    return migration


def migrate_extraction_checkpoints(
    *,
    source_checkpoint_dir: str | Path,
    output_dir: str | Path,
    source_report_path: str | Path | None = None,
    predecessor_report_id: str | None = None,
    source_manifest_path: str | Path | None = None,
    source_campaign_path: str | Path | None = None,
    predecessor_campaign_id: str | None = None,
) -> JsonObject:
    """Migrate a completed report or an exactly inventoried partial campaign."""

    completed = source_report_path is not None or predecessor_report_id is not None
    partial = any(
        item is not None
        for item in (
            source_manifest_path,
            source_campaign_path,
            predecessor_campaign_id,
        )
    )
    if completed and partial:
        raise ValueError("PARTIAL_CAMPAIGN_INVALID")
    if completed:
        if source_report_path is None or predecessor_report_id is None:
            raise ValueError("PREDECESSOR_REPORT_MISMATCH")
        return _migrate_completed_extraction_checkpoints(
            source_checkpoint_dir=source_checkpoint_dir,
            source_report_path=source_report_path,
            output_dir=output_dir,
            predecessor_report_id=predecessor_report_id,
        )
    if (
        source_manifest_path is None
        or source_campaign_path is None
        or predecessor_campaign_id is None
    ):
        raise ValueError("PARTIAL_CAMPAIGN_INVALID")
    source, manifest_path, destination = _partial_paths(
        source_checkpoint_dir, source_manifest_path, output_dir
    )
    campaign_path = Path(source_campaign_path)
    if (
        not campaign_path.is_absolute()
        or campaign_path.is_symlink()
        or not campaign_path.is_file()
        or campaign_path.resolve(strict=True)
        in {source.resolve(), manifest_path.resolve()}
        or campaign_path.resolve(strict=True) in destination.resolve().parents
    ):
        raise ValueError("PARTIAL_CAMPAIGN_INVALID")
    campaign, _campaign_bytes = _read_object(
        campaign_path, code="PARTIAL_CAMPAIGN_INVALID"
    )
    bindings = _manifest_partial_bindings(manifest_path)
    inventory, checkpoint_ids = _partial_inventory(source)
    actual_cost = (
        None
        if campaign.get("actual_cost_state") == "UNKNOWN"
        else campaign.get("actual_cost_usd")
    )
    try:
        expected = _partial_ledger_value(
            bindings=bindings,
            inventory=inventory,
            checkpoint_ids=checkpoint_ids,
            baseline_predecessor_report_id=cast(
                str, campaign["baseline_predecessor_report_id"]
            ),
            campaign_reserved_usd=cast(float, campaign["campaign_reserved_usd"]),
            prior_external_reserved_usd=cast(
                float, campaign["prior_external_reserved_usd"]
            ),
            actual_cost_usd=cast(float | None, actual_cost),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("PARTIAL_CAMPAIGN_INVALID") from error
    if campaign.get("checkpoint_ids") != checkpoint_ids:
        raise ValueError("PARTIAL_CAMPAIGN_CHECKPOINT_SET_MISMATCH")
    if campaign != expected or predecessor_campaign_id != expected["campaign_id"]:
        raise ValueError("PARTIAL_CAMPAIGN_BINDING_INVALID")
    return _migrate_completed_extraction_checkpoints(
        source_checkpoint_dir=source,
        source_report_path=campaign_path,
        output_dir=destination,
        predecessor_report_id=predecessor_campaign_id,
        _partial_authority={
            **campaign,
            "provider_binding": bindings["provider_binding"],
        },
    )


__all__ = ["build_partial_campaign_ledger", "migrate_extraction_checkpoints"]
