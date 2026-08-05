"""Durable artifacts for executing promoted measurements without discovery."""

from __future__ import annotations

from dataclasses import fields
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from agentagon.evals.trace_bundle import NormalizedTraceBundle

from .compiler import FrozenMeasurementDefinition, execute_frozen_results
from .native_signal import (
    NativeSignalValidationError,
    compile_program,
    evaluate_program,
    validate_program as validate_native_signal_program,
)


BUNDLE_SCHEMA_VERSION = "measurement-bundle-v0.1"


def build_measurement_bundle(
    *,
    result: dict[str, Any],
    run_manifest: dict[str, Any],
    proposal_ids: Iterable[str],
    judge_system: str,
    native_signal_programs: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Package definitions and every artifact needed after discovery.

    `native_signal_programs` maps a proposal_id to a validated NATIVE_SIGNAL
    program (see native_signal.py). Any proposal_id present there is bundled
    with executor="NATIVE_SIGNAL" and its program embedded, in place of the
    semantic judge's baseline labels for that proposal.
    """
    wanted = tuple(dict.fromkeys(str(value) for value in proposal_ids))
    candidates = {
        str(row["proposal_id"]): row for row in result["goal_candidate_library"]
    }
    missing = [proposal_id for proposal_id in wanted if proposal_id not in candidates]
    if missing:
        raise ValueError(f"Unknown promoted proposal IDs: {missing}")
    native_programs = native_signal_programs or {}

    definitions = []
    baseline_labels: dict[str, list[dict[str, Any]]] = {}
    population_ids: set[str] = set()
    for proposal_id in wanted:
        candidate = candidates[proposal_id]
        definition = dict(candidate["frozen_definition"])
        definition["proposal_id"] = proposal_id
        program = native_programs.get(proposal_id)
        if program is not None:
            definition["executor"] = "NATIVE_SIGNAL"
            definition["native_signal_program"] = compile_program(program)
            baseline_labels[proposal_id] = []
        else:
            baseline_labels[proposal_id] = [
                {
                    "evidence_id": str(row["evidence_id"]),
                    "value": str(row.get("value", "ABSTAIN")).upper(),
                    "evidence_quote": str(row.get("evidence_quote", "")),
                    "reason": str(row.get("reason", "")),
                }
                for row in candidate["judge_results"]
            ]
        definitions.append(definition)
        population_ids.update(str(value) for value in definition["population_ids"])

    populations = {
        str(row["population_id"]): row
        for row in result["populations"]
        if str(row["population_id"]) in population_ids
    }
    classifiers = {
        population_id: result["classifiers"][population_id]
        for population_id in sorted(population_ids)
    }
    evaluator = {
        "executor": "PINNED_SEMANTIC_JUDGE",
        "evaluator_version": result["prompt_versions"]["judge"],
        "model": run_manifest["model"],
        "system_prompt": judge_system,
        "system_prompt_hash": _sha256_text(judge_system),
        "result_contract": {
            "required_fields": [
                "proposal_id",
                "evidence_id",
                "value",
                "evidence_quote",
                "reason",
            ],
            "unknown_label": "ABSTAIN",
            "quote_policy": "EXACT_SUBSTRING_OF_COMPACT_EVIDENCE",
        },
    }
    bundle = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "source_hash": result["source_hash"],
        "source_result_hash": run_manifest["artifacts"]["RESULT.json"],
        "authority": "PROPOSED_OPINION",
        "proposal_ids": list(wanted),
        "definitions": definitions,
        "populations": populations,
        "population_classifiers": classifiers,
        "evaluator": evaluator,
        "baseline_labels": baseline_labels,
        "execution_boundary": {
            "ready": "STRUCTURED_LABEL_AGGREGATION",
            "pending": "RAW_TRACE_TO_STRUCTURED_LABEL_EXECUTION",
            "discovery_allowed": False,
        },
    }
    validate_measurement_bundle(bundle)
    return bundle | {"bundle_hash": bundle_hash(bundle)}


def validate_measurement_bundle(bundle: dict[str, Any]) -> None:
    if bundle.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        raise ValueError("Unsupported measurement bundle schema")
    definitions = bundle.get("definitions")
    if not isinstance(definitions, list) or not definitions:
        raise ValueError("Measurement bundle requires definitions")
    classifiers = bundle.get("population_classifiers")
    if not isinstance(classifiers, dict):
        raise ValueError("Measurement bundle requires population classifiers")
    proposal_ids = [str(row["proposal_id"]) for row in definitions]
    if proposal_ids != [str(value) for value in bundle.get("proposal_ids", [])]:
        raise ValueError("Proposal order does not match bundled definitions")
    if len(set(proposal_ids)) != len(proposal_ids):
        raise ValueError("Measurement bundle contains duplicate proposal IDs")
    for row in definitions:
        definition = _definition_from_dict(row)
        for population_id in definition.population_ids:
            classifier = classifiers.get(population_id)
            if classifier is None:
                raise ValueError(f"Missing classifier for {population_id}")
            if classifier.get("artifact_hash") != definition.population_classifier_hash:
                raise ValueError(
                    f"Classifier hash mismatch for {row['proposal_id']}:{population_id}"
                )
        if row.get("executor") == "NATIVE_SIGNAL":
            program = row.get("native_signal_program")
            if not isinstance(program, dict):
                raise ValueError(f"Missing native_signal_program for {row['proposal_id']}")
            try:
                validate_native_signal_program(program)
            except NativeSignalValidationError as error:
                raise ValueError(f"Invalid native_signal_program for {row['proposal_id']}: {error}") from error
            continue
        labels = bundle.get("baseline_labels", {}).get(row["proposal_id"])
        if not isinstance(labels, list):
            raise ValueError(f"Missing baseline labels for {row['proposal_id']}")
        allowed = set(definition.labels) | {"ABSTAIN"}
        if any(str(item.get("value", "ABSTAIN")).upper() not in allowed for item in labels):
            raise ValueError(f"Invalid baseline label for {row['proposal_id']}")
    evaluator = bundle.get("evaluator", {})
    prompt = str(evaluator.get("system_prompt", ""))
    if not prompt or evaluator.get("system_prompt_hash") != _sha256_text(prompt):
        raise ValueError("Pinned evaluator prompt is missing or corrupted")
    expected_hash = bundle.get("bundle_hash")
    if expected_hash is not None and expected_hash != bundle_hash(bundle):
        raise ValueError("Measurement bundle hash mismatch")


def execute_bundled_labels(
    bundle: dict[str, Any],
    labels: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Aggregate one complete structured-label run using frozen definitions.

    Only covers PINNED_SEMANTIC_JUDGE-style definitions (pre-produced per-trace
    labels). NATIVE_SIGNAL definitions are skipped here; use
    `execute_native_signal_bundle` for those, since they compute their own
    labels directly from trace bundles rather than accepting supplied ones.
    """
    validate_measurement_bundle(bundle)
    supplied = labels if labels is not None else bundle["baseline_labels"]
    results = []
    for row in bundle["definitions"]:
        if row.get("executor") == "NATIVE_SIGNAL":
            continue
        proposal_id = str(row["proposal_id"])
        if proposal_id not in supplied:
            raise ValueError(f"Missing result rows for {proposal_id}")
        definition = _definition_from_dict(row)
        results.append(
            {"proposal_id": proposal_id}
            | execute_frozen_results(definition, supplied[proposal_id])
        )
    return {
        "schema_version": "measurement-bundle-execution-v0.1",
        "bundle_hash": bundle_hash(bundle),
        "results": results,
    }


def execute_native_signal_bundle(
    bundle: dict[str, Any],
    trace_bundles: Iterable[NormalizedTraceBundle],
) -> dict[str, Any]:
    """Execute every NATIVE_SIGNAL definition in a bundle directly against trace
    bundles, with no LLM call and no supplied labels. Sibling of
    `execute_bundled_labels` for the deterministic executor route.
    """
    validate_measurement_bundle(bundle)
    ordered_bundles = list(trace_bundles)
    results = []
    for row in bundle["definitions"]:
        if row.get("executor") != "NATIVE_SIGNAL":
            continue
        proposal_id = str(row["proposal_id"])
        program = compile_program(row["native_signal_program"])
        definition = _definition_from_dict(row)
        per_trace = []
        for trace_bundle in ordered_bundles:
            outcome = evaluate_program(program, trace_bundle)
            per_trace.append(
                {
                    "evidence_id": trace_bundle.trace_id,
                    "value": outcome["value"] if outcome["status"] == "OK" else "ABSTAIN",
                    "status": outcome["status"],
                    "evidence_ref": outcome["evidence_ref"],
                }
            )
        results.append(
            {"proposal_id": proposal_id}
            | execute_frozen_results(definition, per_trace)
            | {"per_trace_results": per_trace}
        )
    return {
        "schema_version": "measurement-bundle-native-execution-v0.1",
        "bundle_hash": bundle_hash(bundle),
        "results": results,
    }


def write_measurement_bundle(path: Path, bundle: dict[str, Any]) -> None:
    validate_measurement_bundle(bundle)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical_json(bundle) + "\n", encoding="utf-8")


def load_measurement_bundle(path: Path) -> dict[str, Any]:
    bundle = json.loads(path.read_text(encoding="utf-8"))
    validate_measurement_bundle(bundle)
    return bundle


def bundle_hash(bundle: dict[str, Any]) -> str:
    payload = {key: value for key, value in bundle.items() if key != "bundle_hash"}
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _definition_from_dict(value: dict[str, Any]) -> FrozenMeasurementDefinition:
    allowed = {field.name for field in fields(FrozenMeasurementDefinition)}
    payload = {key: item for key, item in value.items() if key in allowed}
    for key in (
        "source_ids",
        "population_ids",
        "population_labels",
        "labels",
        "required_evidence",
        "supporting_examples",
        "boundary_examples",
    ):
        payload[key] = tuple(payload.get(key, ()))
    return FrozenMeasurementDefinition(**payload)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True)
