"""Paired, authority-aware comparison over completed normalized outcomes."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
import hashlib
import math
import random
from statistics import fmean, stdev
from typing import Any

from agentagon.evals.manifest import measurement_version_id
from agentagon.evals.models import (
    ComparisonStatus,
    DiffRow,
    EvidenceReference,
    ExecutionGap,
    ExecutionGapKind,
    MeasurementDefinition,
    MeasurementDirection,
    MeasurementMaturity,
    MeasurementResult,
    MeasurementResultStatus,
    MeasurementValueType,
    PairOutcome,
    ReleaseDiff,
    ReleaseRun,
    ReleaseSide,
    SideOutcome,
)


MIN_DIRECTIONAL_CASES = 30
BOOTSTRAP_DRAWS = 1_000


def compare_release_run(
    run: ReleaseRun,
    measurements: Sequence[MeasurementDefinition],
) -> ReleaseDiff:
    expected = tuple(measurement_version_id(item) for item in measurements)
    if expected != run.measurement_versions:
        raise ValueError("Comparator measurements do not match the pinned ReleaseRun")

    rows: list[DiffRow] = []
    gaps = list(run.execution_gaps)
    for definition in measurements:
        row, row_gaps = _compare_measurement(run.pairs, definition)
        rows.append(row)
        gaps.extend(row_gaps)
    digest = hashlib.sha256(f"{run.run_id}:{expected}".encode()).hexdigest()[:16]
    return ReleaseDiff(
        diff_id=f"diff-{digest}",
        release_run_id=run.run_id,
        rows=tuple(rows),
        execution_gaps=tuple(gaps),
    )


def _compare_measurement(
    pairs: tuple[PairOutcome, ...],
    definition: MeasurementDefinition,
) -> tuple[DiffRow, tuple[ExecutionGap, ...]]:
    records: list[tuple[str, Any, Any, tuple[EvidenceReference, ...]]] = []
    gaps: list[ExecutionGap] = []
    invalid_pairs = 0
    abstained_pairs = 0

    for pair in pairs:
        if not pair.is_valid:
            invalid_pairs += 1
            gaps.extend(_pair_validity_gaps(pair))
            continue
        baseline = _find_result(pair.baseline, definition)
        candidate = _find_result(pair.candidate, definition)
        if baseline is None or candidate is None:
            abstained_pairs += 1
            gaps.append(
                ExecutionGap(
                    kind=ExecutionGapKind.NOT_EVALUABLE,
                    reason=f"Missing paired result for {measurement_version_id(definition)}",
                    case_id=pair.key.case_id,
                    trial_id=pair.key.trial_id,
                )
            )
            continue
        if (
            baseline.status is not MeasurementResultStatus.OK
            or candidate.status is not MeasurementResultStatus.OK
        ):
            abstained_pairs += 1
            gaps.extend(_measurement_result_gaps(pair, baseline, candidate))
            continue
        if not _valid_value(definition.value_type, baseline.value) or not _valid_value(
            definition.value_type, candidate.value
        ):
            abstained_pairs += 1
            gaps.append(
                ExecutionGap(
                    kind=ExecutionGapKind.MALFORMED_RESULT,
                    reason=f"Result value does not match {definition.value_type}",
                    case_id=pair.key.case_id,
                    trial_id=pair.key.trial_id,
                )
            )
            continue
        records.append(
            (
                pair.key.case_id,
                baseline.value,
                candidate.value,
                (*baseline.evidence, *candidate.evidence),
            )
        )

    common = {
        "measurement_id": definition.measurement_id,
        "measurement_version": definition.version,
        "evaluable_pairs": len(records),
        "total_pairs": len(pairs),
        "abstained_pairs": abstained_pairs,
        "invalid_pairs": invalid_pairs,
        "expectation_id": definition.expectation_id,
    }
    if definition.value_type in {
        MeasurementValueType.BOOLEAN,
        MeasurementValueType.NUMBER,
    }:
        row = _compare_numeric(records, definition, common)
    elif definition.value_type is MeasurementValueType.CATEGORY:
        row = _compare_category(records, common)
    else:
        row = _compare_text(records, common)
    return row, tuple(gaps)


def _compare_numeric(
    records: list[tuple[str, Any, Any, tuple[EvidenceReference, ...]]],
    definition: MeasurementDefinition,
    common: dict[str, Any],
) -> DiffRow:
    by_case: dict[str, list[tuple[float, float]]] = defaultdict(list)
    transitions: Counter[str] = Counter()
    evidence: list[EvidenceReference] = []
    affected: set[str] = set()
    for case_id, baseline, candidate, refs in records:
        baseline_number = float(baseline)
        candidate_number = float(candidate)
        by_case[case_id].append((baseline_number, candidate_number))
        if baseline_number != candidate_number:
            affected.add(case_id)
            evidence.extend(refs)
        if definition.value_type is MeasurementValueType.BOOLEAN:
            transitions[f"{int(baseline_number)}_TO_{int(candidate_number)}"] += 1

    case_values = [
        (fmean(item[0] for item in values), fmean(item[1] for item in values))
        for _, values in sorted(by_case.items())
    ]
    baseline_value = fmean(item[0] for item in case_values) if case_values else None
    candidate_value = fmean(item[1] for item in case_values) if case_values else None
    case_deltas = [candidate - baseline for baseline, candidate in case_values]
    delta = fmean(case_deltas) if case_deltas else None
    interval = _bootstrap_interval(case_deltas, definition.measurement_id)
    status = _numeric_status(delta, interval, len(case_values), definition)
    return DiffRow(
        **common,
        status=status,
        baseline_value=baseline_value,
        candidate_value=candidate_value,
        delta=delta,
        independent_case_count=len(case_values),
        interval=interval,
        minimum_detectable_effect=_minimum_detectable_effect(case_deltas),
        paired_transitions=tuple(sorted(transitions.items())),
        affected_case_ids=tuple(sorted(affected)),
        evidence=tuple(evidence),
    )


def _compare_category(
    records: list[tuple[str, Any, Any, tuple[EvidenceReference, ...]]],
    common: dict[str, Any],
) -> DiffRow:
    by_case: dict[str, list[tuple[str, str]]] = defaultdict(list)
    transitions: Counter[str] = Counter()
    evidence: list[EvidenceReference] = []
    affected: set[str] = set()
    for case_id, baseline, candidate, refs in records:
        by_case[case_id].append((baseline, candidate))
        transitions[f"{baseline}_TO_{candidate}"] += 1
        if baseline != candidate:
            affected.add(case_id)
            evidence.extend(refs)

    collapsed: list[tuple[str, str]] = []
    for _, values in sorted(by_case.items()):
        baseline = _unique_mode(item[0] for item in values)
        candidate = _unique_mode(item[1] for item in values)
        if baseline is not None and candidate is not None:
            collapsed.append((baseline, candidate))
    baseline_distribution = _distribution(item[0] for item in collapsed)
    candidate_distribution = _distribution(item[1] for item in collapsed)
    if not collapsed:
        status = ComparisonStatus.NOT_EVALUABLE
    elif baseline_distribution == candidate_distribution:
        status = ComparisonStatus.UNCHANGED
    elif len(collapsed) < MIN_DIRECTIONAL_CASES:
        status = ComparisonStatus.INCONCLUSIVE
    else:
        status = ComparisonStatus.CHANGED
    return DiffRow(
        **common,
        status=status,
        baseline_value=baseline_distribution,
        candidate_value=candidate_distribution,
        delta=None,
        independent_case_count=len(collapsed),
        paired_transitions=tuple(sorted(transitions.items())),
        affected_case_ids=tuple(sorted(affected)),
        evidence=tuple(evidence),
    )


def _compare_text(
    records: list[tuple[str, Any, Any, tuple[EvidenceReference, ...]]],
    common: dict[str, Any],
) -> DiffRow:
    affected = {
        case_id for case_id, baseline, candidate, _ in records if baseline != candidate
    }
    evidence = tuple(
        ref
        for case_id, baseline, candidate, refs in records
        if baseline != candidate
        for ref in refs
    )
    text_common = {
        **common,
        "evaluable_pairs": 0,
        "abstained_pairs": common["abstained_pairs"] + len(records),
    }
    return DiffRow(
        **text_common,
        status=ComparisonStatus.NOT_EVALUABLE,
        baseline_value=None,
        candidate_value=None,
        delta=None,
        independent_case_count=0,
        affected_case_ids=tuple(sorted(affected)),
        evidence=evidence,
    )


def _numeric_status(
    delta: float | None,
    interval: tuple[float, float] | None,
    independent_cases: int,
    definition: MeasurementDefinition,
) -> ComparisonStatus:
    if delta is None:
        return ComparisonStatus.NOT_EVALUABLE
    if math.isclose(delta, 0.0, abs_tol=1e-12):
        return ComparisonStatus.UNCHANGED
    if (
        independent_cases < MIN_DIRECTIONAL_CASES
        or interval is None
        or interval[0] <= 0 <= interval[1]
    ):
        return ComparisonStatus.INCONCLUSIVE

    raw_status = ComparisonStatus.INCREASED if delta > 0 else ComparisonStatus.DECREASED
    authoritative = (
        definition.expectation_id is not None
        and definition.maturity is MeasurementMaturity.CONFIRMED
        and definition.direction is not MeasurementDirection.NEUTRAL
    )
    if not authoritative:
        return raw_status
    desirable = (
        delta > 0 and definition.direction is MeasurementDirection.HIGHER_BETTER
    ) or (delta < 0 and definition.direction is MeasurementDirection.LOWER_BETTER)
    return ComparisonStatus.IMPROVED if desirable else ComparisonStatus.REGRESSED


def _find_result(
    outcome: SideOutcome,
    definition: MeasurementDefinition,
) -> MeasurementResult | None:
    matches = [
        result
        for result in outcome.measurement_results
        if result.measurement_id == definition.measurement_id
        and result.measurement_version == definition.version
    ]
    if len(matches) > 1:
        raise ValueError(
            f"Duplicate result for {definition.measurement_id}@{definition.version}"
        )
    return matches[0] if matches else None


def _valid_value(value_type: MeasurementValueType, value: Any) -> bool:
    if value_type is MeasurementValueType.BOOLEAN:
        return isinstance(value, bool)
    if value_type is MeasurementValueType.NUMBER:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )
    if value_type in {MeasurementValueType.CATEGORY, MeasurementValueType.TEXT}:
        return isinstance(value, str)
    return False


def _bootstrap_interval(
    values: list[float], seed_text: str
) -> tuple[float, float] | None:
    if len(values) < 2:
        return None
    seed = int(hashlib.sha256(seed_text.encode()).hexdigest()[:16], 16)
    rng = random.Random(seed)
    means = sorted(
        fmean(rng.choice(values) for _ in values) for _ in range(BOOTSTRAP_DRAWS)
    )
    return (_percentile(means, 0.025), _percentile(means, 0.975))


def _percentile(values: list[float], probability: float) -> float:
    position = (len(values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    fraction = position - lower
    return values[lower] * (1 - fraction) + values[upper] * fraction


def _minimum_detectable_effect(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    return (1.96 + 0.84) * stdev(values) / math.sqrt(len(values))


def _unique_mode(values: Iterable[str]) -> str | None:
    counts = Counter(values)
    if not counts:
        return None
    top = max(counts.values())
    winners = [value for value, count in counts.items() if count == top]
    return winners[0] if len(winners) == 1 else None


def _distribution(values: Iterable[str]) -> dict[str, float]:
    counts = Counter(values)
    total = sum(counts.values())
    return (
        {value: count / total for value, count in sorted(counts.items())}
        if total
        else {}
    )


def _pair_validity_gaps(pair: PairOutcome) -> list[ExecutionGap]:
    gaps = [outcome.gap for outcome in (pair.baseline, pair.candidate) if outcome.gap]
    recorded = {gap.reason for gap in gaps}
    for reason in pair.validity_reasons:
        if reason in recorded or reason.endswith("EXECUTION_GAP"):
            continue
        gaps.append(
            ExecutionGap(
                kind=ExecutionGapKind.ENVIRONMENT_FAILURE,
                reason=reason,
                case_id=pair.key.case_id,
                trial_id=pair.key.trial_id,
            )
        )
    return gaps


def _measurement_result_gaps(
    pair: PairOutcome,
    baseline: MeasurementResult,
    candidate: MeasurementResult,
) -> list[ExecutionGap]:
    gaps = []
    for side, result in (
        (ReleaseSide.BASELINE, baseline),
        (ReleaseSide.CANDIDATE, candidate),
    ):
        if result.status is MeasurementResultStatus.OK:
            continue
        kind = {
            MeasurementResultStatus.UNSUPPORTED: ExecutionGapKind.UNSUPPORTED,
            MeasurementResultStatus.NOT_EVALUABLE: ExecutionGapKind.NOT_EVALUABLE,
            MeasurementResultStatus.ABSTAIN: ExecutionGapKind.NOT_EVALUABLE,
            MeasurementResultStatus.EXECUTION_ERROR: ExecutionGapKind.HARNESS_FAILURE,
        }[result.status]
        gaps.append(
            ExecutionGap(
                kind=kind,
                reason=result.reason or result.status,
                case_id=pair.key.case_id,
                trial_id=pair.key.trial_id,
                side=side,
            )
        )
    return gaps


__all__ = ["compare_release_run"]
