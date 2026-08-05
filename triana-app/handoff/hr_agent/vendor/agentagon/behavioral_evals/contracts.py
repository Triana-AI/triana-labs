"""Input contract and measurement model for the behavioral-evals pipeline.

Pure dataclasses only — no I/O, no model calls. See ``agentagon/behavioral_evals/__init__.py``
for how these fit into the overall flow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from agentagon.evals.trace_bundle import NormalizedTraceBundle


class Dimension(StrEnum):
    """The six fixed behavioral-evals dimensions. Nothing else is a dimension.

    SAFETY was added alongside the IssueBench-style failure-category expansion
    (agent_looping, rage/frustration, task_evasion, pii_or_data_leak, silent
    tool errors, incorrect tool args, failed error recovery, context
    explosion, response truncation) — see PROPOSER_SYSTEM in prompts.py for how
    each failure category maps onto one of these six.
    """

    GOAL_CORRECTNESS = "GOAL_CORRECTNESS"
    TOOL_CALL_RELIABILITY = "TOOL_CALL_RELIABILITY"
    PERFORMANCE_UNDER_LOAD = "PERFORMANCE_UNDER_LOAD"
    FAULT_TOLERANCE = "FAULT_TOLERANCE"
    TRACE_OBSERVABILITY = "TRACE_OBSERVABILITY"
    SAFETY = "SAFETY"


class MeasurementKind(StrEnum):
    STATIC = "STATIC"  # deterministic formula over a discovered state field
    EVAL = "EVAL"  # frozen-rubric judge call


class ValueType(StrEnum):
    PERCENT = "PERCENT"
    CATEGORICAL = "CATEGORICAL"
    NUMERIC = "NUMERIC"


class DisplayKind(StrEnum):
    SMALL_PERCENT_BAR = "SMALL_PERCENT_BAR"
    STACKED_BAR = "STACKED_BAR"
    NUMBER = "NUMBER"


@dataclass(frozen=True, slots=True)
class StaticAgentContext:
    """Non-trace context about the agent: what it was told to do and with what tools.

    Required for EVAL measurements that judge adherence to instructions or
    tool-schema correctness — a judge cannot assess "did it follow the system
    prompt" without the system prompt.
    """

    system_prompt: str | None = None
    rubric: str | None = None
    tool_schemas: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class Executor:
    """How a measurement's value is computed. Frozen once a measurement is proposed.

    A STATIC measurement uses ``formula_ref`` (a deterministic aggregation, e.g. the
    same numeric/categorical aggregation ``compute_state_measurement`` already
    performs over a discovered state field). An EVAL measurement uses a frozen
    ``rubric`` + ``label_set`` run through a pinned judge model — never both.
    """

    kind: MeasurementKind
    formula_ref: str | None = None
    rubric: str | None = None
    label_set: tuple[str, ...] = ()
    model_id: str | None = None
    prompt_version: str | None = None

    @staticmethod
    def deterministic(formula_ref: str, *, categories: tuple[str, ...] = ()) -> "Executor":
        """``categories`` is the discovered label set for a CATEGORICAL/PERCENT STATIC
        measurement (e.g. a field's value_set, or ["TRUE","FALSE"] for a boolean share).
        Omit it for a NUMERIC STATIC measurement."""
        return Executor(kind=MeasurementKind.STATIC, formula_ref=formula_ref, label_set=categories)

    @staticmethod
    def judge(
        *, rubric: str, label_set: tuple[str, ...], model_id: str, prompt_version: str
    ) -> "Executor":
        return Executor(
            kind=MeasurementKind.EVAL,
            rubric=rubric,
            label_set=label_set,
            model_id=model_id,
            prompt_version=prompt_version,
        )

    def __post_init__(self) -> None:
        if self.kind is MeasurementKind.STATIC and not self.formula_ref:
            raise ValueError("STATIC executor requires formula_ref")
        if self.kind is MeasurementKind.EVAL and not (self.rubric and self.label_set):
            raise ValueError("EVAL executor requires rubric and a non-empty label_set")

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "formula_ref": self.formula_ref,
            "rubric": self.rubric,
            "label_set": list(self.label_set),
            "model_id": self.model_id,
            "prompt_version": self.prompt_version,
        }

    @staticmethod
    def from_dict(value: dict[str, Any]) -> "Executor":
        return Executor(
            kind=MeasurementKind(str(value["kind"]).upper()),
            formula_ref=value.get("formula_ref"),
            rubric=value.get("rubric"),
            label_set=tuple(str(label) for label in value.get("label_set", [])),
            model_id=value.get("model_id"),
            prompt_version=value.get("prompt_version"),
        )


@dataclass(frozen=True, slots=True)
class Measurement:
    """One proposed measurement. No 'unknown' bucket lives here: a measurement that
    cannot be confidently computed is dropped at discovery, not stored ambiguous."""

    id: str
    title: str
    dimension: Dimension
    kind: MeasurementKind
    value_type: ValueType
    executor: Executor
    display: DisplayKind
    developer_question: str
    definition: str
    population_id: str | None = None
    state_field: str | None = None

    def __post_init__(self) -> None:
        if self.kind != self.executor.kind:
            raise ValueError(
                f"measurement {self.id}: kind {self.kind} does not match executor kind {self.executor.kind}"
            )
        if self.kind is MeasurementKind.STATIC and not self.state_field:
            raise ValueError(f"measurement {self.id}: STATIC measurement requires state_field")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "dimension": self.dimension.value,
            "kind": self.kind.value,
            "value_type": self.value_type.value,
            "executor": self.executor.to_dict(),
            "display": self.display.value,
            "developer_question": self.developer_question,
            "definition": self.definition,
            "population_id": self.population_id,
            "state_field": self.state_field,
        }

    @staticmethod
    def from_dict(value: dict[str, Any]) -> "Measurement":
        """Reload a frozen measurement from its to_dict() form — e.g. to re-run the same
        measurement set from an earlier discovery run as a baseline-vs-candidate diff,
        without re-proposing (and re-paying for) it."""
        return Measurement(
            id=str(value["id"]),
            title=str(value["title"]),
            dimension=Dimension(str(value["dimension"]).upper()),
            kind=MeasurementKind(str(value["kind"]).upper()),
            value_type=ValueType(str(value["value_type"]).upper()),
            executor=Executor.from_dict(value["executor"]),
            display=DisplayKind(str(value["display"]).upper()),
            developer_question=str(value.get("developer_question", "")),
            definition=str(value.get("definition", "")),
            population_id=(str(value["population_id"]) if value.get("population_id") else None),
            state_field=(str(value["state_field"]) if value.get("state_field") else None),
        )


@dataclass(frozen=True, slots=True)
class CoverageGap:
    """A whole dimension with no measurement the proposer could confidently write.

    Distinct from a per-trace abstain: this names the exact data category
    missing (e.g. "needs tool I/O", "needs load runs"), not an unanswered
    individual trace.
    """

    dimension: Dimension
    needs: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"dimension": self.dimension.value, "needs": self.needs, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class CoverageMap:
    """All six dimensions, each either populated with measurements or a typed gap.

    Every dimension appears in exactly one of ``populated`` (as a possibly-empty
    tuple of measurement ids, only when non-empty) or ``gaps`` — never neither,
    never both. This is the honest "here's what your data supports + here's
    what to capture" surface for the report.
    """

    populated: dict[Dimension, tuple[str, ...]]
    gaps: tuple[CoverageGap, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "populated": {
                dimension.value: list(measurement_ids)
                for dimension, measurement_ids in self.populated.items()
            },
            "gaps": [gap.to_dict() for gap in self.gaps],
        }


def build_coverage_map(
    measurements: list[Measurement], gaps: list[CoverageGap]
) -> CoverageMap:
    """Assemble the coverage map and enforce the one-populated-or-one-gap invariant."""
    populated: dict[Dimension, tuple[str, ...]] = {}
    for measurement in measurements:
        populated.setdefault(measurement.dimension, ())
        populated[measurement.dimension] = populated[measurement.dimension] + (measurement.id,)
    gap_dimensions = {gap.dimension for gap in gaps}
    populated_dimensions = set(populated)
    overlap = gap_dimensions & populated_dimensions
    if overlap:
        raise ValueError(
            f"dimensions cannot be both populated and a coverage gap: {sorted(d.value for d in overlap)}"
        )
    missing = set(Dimension) - gap_dimensions - populated_dimensions
    if missing:
        raise ValueError(
            f"dimensions must be populated or a typed coverage gap, missing: {sorted(d.value for d in missing)}"
        )
    return CoverageMap(populated=populated, gaps=tuple(gaps))


@dataclass(frozen=True, slots=True)
class BehavioralEvalsInput:
    """Everything the proposer needs to author measurements for one agent.

    ``trace_bundles`` may be the current (non-enriched) HR AI traces or the
    upcoming enriched export. ``requires_enriched_traces`` names the dimensions
    that cannot be populated from non-enriched traces — TOOL_CALL_RELIABILITY
    and FAULT_TOLERANCE need tool call arguments/results, PERFORMANCE_UNDER_LOAD
    needs timestamps and sub-agent spans under load. Until enriched traces land,
    those dimensions are expected to come back as COVERAGE_GAP.
    """

    profile: dict[str, Any]
    populations: list[dict[str, Any]]
    behavior_clusters: dict[str, Any]
    state_schema_profile: dict[str, Any]
    static_context: StaticAgentContext
    trace_bundles: tuple[NormalizedTraceBundle, ...]

    requires_enriched_traces: tuple[Dimension, ...] = (
        Dimension.TOOL_CALL_RELIABILITY,
        Dimension.PERFORMANCE_UNDER_LOAD,
        Dimension.FAULT_TOLERANCE,
    )

    def has_enriched_traces(self) -> bool:
        """True once the corpus carries tool I/O + timestamps *anywhere*.

        ANY-bundle semantics, matching ``event_signals.event_availability_profile``:
        the enriched dimensions become groundable as soon as at least one bundle
        reports tool results and at least one carries a runtime timestamp. A trace
        that never called a tool is not "unenriched" — it is simply *not applicable*
        to a tool measurement, and the per-measurement executor already counts it in
        ``not_applicable`` rather than gapping the whole dimension. Requiring EVERY
        bundle to have tool I/O (the old ``all`` semantics) meant any realistic mixed
        corpus — some traces call tools, some are pure conversations — never un-gapped
        TOOL_CALL_RELIABILITY / FAULT_TOLERANCE at all. Sub-agent span detection is
        adapter-specific and deferred to the executor.
        """
        if not self.trace_bundles:
            return False
        return any(
            bool(bundle.provenance.get("tool_results_available"))
            for bundle in self.trace_bundles
        ) and any(
            bundle.execution.runtime_seconds is not None for bundle in self.trace_bundles
        )


@dataclass(frozen=True, slots=True)
class MeasurementResult:
    """One measurement's computed value. ``n`` is the denominator — only traces the
    executor actually produced a value for.

    Two distinct, honestly-labeled exclusion counts sit alongside ``n`` (both default
    to 0 and are informational only — they are never folded into ``n`` or into a vague
    "unknown" bucket):

    - ``not_applicable``: traces outside this measurement's scoped population (e.g. a
      decision-correctness judge that only applies to decision sessions). These traces
      were never in scope, so they are not evidence of anything the measurement missed.
    - ``abstained``: in-scope traces the executor still could not produce a value for
      (a STATIC field absent on that trace, or a judge that genuinely could not decide).
      This is the only place a real "the executor couldn't tell" count lives.
    """

    measurement_id: str
    dimension: Dimension
    kind: MeasurementKind
    value_type: ValueType
    n: int
    distribution: dict[str, int] | None = None
    rate: float | None = None
    numeric_summary: dict[str, Any] | None = None
    evidence_ids: tuple[str, ...] = ()
    not_applicable: int = 0
    abstained: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "measurement_id": self.measurement_id,
            "dimension": self.dimension.value,
            "kind": self.kind.value,
            "value_type": self.value_type.value,
            "n": self.n,
            "distribution": self.distribution,
            "rate": self.rate,
            "numeric_summary": self.numeric_summary,
            "evidence_ids": list(self.evidence_ids),
            "not_applicable": self.not_applicable,
            "abstained": self.abstained,
        }
