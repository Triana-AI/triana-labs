"""Compile proposed questions into immutable, repeatable measurement definitions."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


COMPILER_VERSION = "frozen-measurement-compiler-v0.2"
UNKNOWN_POLICY = "EXCLUDE_FROM_VALUE_REPORT_SEPARATELY"


@dataclass(frozen=True, slots=True)
class FrozenMeasurementDefinition:
    measurement_id: str
    version: str
    name: str
    author_kind: str
    source_ids: tuple[str, ...]
    population_ids: tuple[str, ...]
    population_labels: tuple[str, ...]
    population_classifier_version: str
    population_classifier_hash: str
    slot_id: str
    variant_id: str
    observable_definition: str
    value_type: str
    labels: tuple[str, ...]
    aggregation: str
    unknown_policy: str
    executor: str
    evaluator_version: str
    required_evidence: tuple[str, ...]
    supporting_examples: tuple[str, ...]
    boundary_examples: tuple[str, ...]
    presentation_version: str
    compiler_version: str = COMPILER_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compile_measurement(
    spec: dict[str, Any],
    *,
    author_kind: str,
    population_catalog: list[dict[str, Any]],
    supporting_examples: list[str] | None = None,
    boundary_examples: list[str] | None = None,
    evaluator_version: str = "measurement-judge-v1",
    population_classifier: dict[str, Any] | None = None,
) -> FrozenMeasurementDefinition:
    """Compile a validated proposal through the one shared frozen contract."""
    value_type = str(spec.get("value_type", "")).upper()
    labels = tuple(str(value).upper() for value in spec.get("categories", []))
    population_ids = tuple(str(value) for value in spec.get("population_ids", []))
    if value_type not in {"BOOLEAN", "CATEGORY", "NUMBER", "TEXT"}:
        raise ValueError("Unsupported measurement value_type")
    if value_type == "BOOLEAN" and labels != ("TRUE", "FALSE"):
        raise ValueError("Boolean measurements require TRUE/FALSE labels")
    if not population_ids:
        raise ValueError("A frozen measurement requires a denominator population")
    known = {str(row["population_id"]): str(row["label"]) for row in population_catalog}
    known["GLOBAL"] = "All observed traces"
    if any(population_id not in known for population_id in population_ids):
        raise ValueError("Frozen measurement references an unknown population")
    observable = str(spec.get("observable_definition", "")).strip()
    if not observable:
        raise ValueError("Frozen measurement requires an observable definition")
    executor = str(spec.get("executor") or "PINNED_SEMANTIC_JUDGE")
    source_ids = tuple(
        str(value)
        for value in (
            spec.get("finding_ids")
            or [spec.get("proposal_id") or spec.get("candidate_id") or "customer-authored"]
        )
    )
    classifier_hash = str(
        (population_classifier or {}).get("artifact_hash")
        or spec.get("population_classifier_hash")
        or "UNCOMPILED"
    )
    slot_id = str(spec.get("slot_id") or "CUSTOM")
    variant_id = str(spec.get("variant_id") or "DEFAULT")
    stable = {
        "population_ids": population_ids,
        "population_classifier_hash": classifier_hash,
        "slot_id": slot_id,
        "variant_id": variant_id,
        "executor_parameters": spec.get("executor_parameters", {}),
        "value_type": value_type,
        "labels": labels,
        "aggregation": "RATE_BY_LABEL" if value_type in {"BOOLEAN", "CATEGORY"} else "DISTRIBUTION",
        "unknown_policy": UNKNOWN_POLICY,
        "executor": executor,
        "evaluator_version": evaluator_version if executor != "DETERMINISTIC" else "deterministic-v1",
        "required_evidence": tuple(str(value) for value in spec.get("required_evidence", [])),
        "rubric_hash": str(spec.get("rubric_hash") or "NONE"),
        "compiler_version": COMPILER_VERSION,
    }
    digest = hashlib.sha256(
        json.dumps(stable, sort_keys=True, default=list).encode("utf-8")
    ).hexdigest()
    name = str(spec.get("title") or spec.get("developer_question"))
    presentation = {
        "name": name,
        "observable_definition": observable,
        "source_ids": source_ids,
        "author_kind": author_kind,
    }
    presentation_digest = hashlib.sha256(
        json.dumps(presentation, sort_keys=True, default=list).encode("utf-8")
    ).hexdigest()
    return FrozenMeasurementDefinition(
        measurement_id=f"fm-{digest[:16]}",
        version=digest,
        name=name,
        author_kind=author_kind,
        source_ids=source_ids,
        population_ids=population_ids,
        population_labels=tuple(known[value] for value in population_ids),
        population_classifier_version=str(
            (population_classifier or {}).get("compiler_version")
            or "population-classifier-unavailable"
        ),
        population_classifier_hash=classifier_hash,
        slot_id=slot_id,
        variant_id=variant_id,
        observable_definition=observable,
        value_type=value_type,
        labels=labels,
        aggregation=stable["aggregation"],
        unknown_policy=UNKNOWN_POLICY,
        executor=executor,
        evaluator_version=stable["evaluator_version"],
        required_evidence=stable["required_evidence"],
        supporting_examples=tuple(supporting_examples or [])[:5],
        boundary_examples=tuple(boundary_examples or [])[:5],
        presentation_version=presentation_digest,
    )


def execute_frozen_results(
    definition: FrozenMeasurementDefinition,
    per_trace_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate already-produced trace results without rediscovery or reinterpretation."""
    values = [
        str(row.get("value", "ABSTAIN")).upper()
        for row in per_trace_results
        if str(row.get("value", "ABSTAIN")).upper() != "ABSTAIN"
    ]
    counts = Counter(values)
    return {
        "measurement_id": definition.measurement_id,
        "measurement_version": definition.version,
        "evaluator_version": definition.evaluator_version,
        "eligible": len(per_trace_results),
        "evaluable": len(values),
        "unknown": len(per_trace_results) - len(values),
        "distribution": dict(sorted((key.lower(), value) for key, value in counts.items())),
        "evidence_ids": [
            str(row["evidence_id"])
            for row in per_trace_results
            if row.get("value") != "ABSTAIN" and row.get("evidence_id")
        ][:20],
    }
