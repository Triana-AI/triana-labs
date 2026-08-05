"""Re-apply a frozen PINNED_SEMANTIC_JUDGE measurement to unseen traces.

This is the scrappy minimal core of the release gate: a measurement is
"repeatable" not because the judge is deterministic, but because its DEFINITION
(question, labels, pinned model, system prompt, population classifier) is frozen
and re-applied to whatever traces a new release produces. Determinism is not the
requirement; frozen definition + re-application + measured stability is.

`execute_bundled_labels` only re-aggregates labels handed to it. This module
adds the missing step: given a frozen bundle + new trace bundles + the pinned
model, actually run the judge on those traces and produce the labels.

Deliberately minimal (see internal/REPEATABLE_MEASUREMENT_PARKING_2026-07-20.md):
covers the PINNED_SEMANTIC_JUDGE route only; native denominator and identity
fixes are parked.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from typing import Any, Iterable

from agentagon.evals.trace_bundle import EventKind, NormalizedTraceBundle
from agentagon.exploration_v1.llm import StructuredModel
from agentagon.goal_observables.pipeline import _judge_with_retries
from agentagon.measurement_promotion.compiler import FrozenMeasurementDefinition, execute_frozen_results
from agentagon.measurement_promotion.population import PopulationClassifier

from .bundle import _definition_from_dict, bundle_hash, validate_measurement_bundle


def compact_trace_evidence(bundle: NormalizedTraceBundle) -> str:
    """Build the judge's compact evidence for one trace, tolerating absent facets.

    Mirrors goal_observables._compact_units but without the cold-start semantic
    facets (a fresh release has none precomputed). The judge still sees user
    turns, agent turns, tool events, and post-state.
    """
    user_lines: list[str] = []
    agent_lines: list[str] = []
    tools: list[str] = []
    for event in bundle.events:
        content = (
            event.content
            if isinstance(event.content, str)
            else json.dumps(event.content, sort_keys=True, default=str)
        )
        if event.kind is EventKind.USER:
            user_lines.append(content[:500])
        elif event.kind is EventKind.AGENT:
            agent_lines.append(content[:800])
        elif event.kind is EventKind.TOOL:
            tools.append(f"{event.name}: {content[:300]}")
    compact = "\n".join(
        [
            "USER: " + " | ".join(user_lines[:4]),
            "AGENT: " + " | ".join(agent_lines[-3:]),
            "TOOLS/ACTIONS: " + " | ".join(tools[:20]),
            "STATE AFTER: "
            + json.dumps(bundle.state_after_ref, sort_keys=True, default=str)[:1800],
            f"EXECUTION: {bundle.execution.status.value}",
            "TRACE BOUNDARY: complete normalized trace evidence for this imported run",
        ]
    )
    return compact[:6000]


def _classifier_text(bundle: NormalizedTraceBundle) -> str:
    """Text handed to the population classifier — user turns carry the demand."""
    parts: list[str] = []
    for event in bundle.events:
        if event.kind is EventKind.USER:
            content = (
                event.content
                if isinstance(event.content, str)
                else json.dumps(event.content, default=str)
            )
            parts.append(content)
    return " ".join(parts)[:4000]


def _judge_omit_contract(
    model: StructuredModel,
    evaluator: dict[str, Any],
    definition: FrozenMeasurementDefinition,
    proposal_id: str,
    units: list[dict[str, str]],
    *,
    semantic_workers: int,
    batch_size: int = 15,
) -> list[dict[str, Any]]:
    """Judge `units` under the omit-without-unknown contract a bundle's own evaluator
    packages (behavioral_evals.prompts.EXECUTOR_JUDGE_SYSTEM / parse_judge_results):
    the model omits a trace's evidence_id entirely rather than returning ABSTAIN, and
    no evidence-quote grounding is required (result_contract.quote_policy == "NONE").

    Deliberately separate from `_judge_with_retries` (goal_observables' quote-grounded,
    ABSTAIN-based contract) — running a bundle authored under one contract through the
    other's stricter validation is exactly the abstain-leak this branch exists to avoid
    (see bundle["evaluator"]["result_contract"]["quote_policy"] as the dispatch key in
    `execute_semantic_bundle`).

    `stage` is keyed on `proposal_id` (the stable, human-authored Measurement.id, e.g.
    "goal_correctness_decision"), not `definition.measurement_id` (a compiler-assigned
    hash) — frozen_labels.FrozenLabelModel/RecordingModel key their replay/recording on
    this same stage naming, and a hash would defeat freezing a label set by hand or
    across a re-compile.
    """
    from agentagon.behavioral_evals.prompts import parse_judge_results

    label_set = tuple(definition.labels)
    system_prompt = str(evaluator.get("system_prompt", ""))
    prompt_version = str(evaluator.get("evaluator_version", ""))
    batches = [units[index : index + batch_size] for index in range(0, len(units), max(1, batch_size))]

    def judge(batch: list[dict[str, str]]) -> dict[str, str]:
        payload = {
            "rubric": definition.observable_definition,
            "label_set": list(label_set),
            "traces": batch,
        }
        try:
            response = model.complete_json(
                stage=f"release-gate-eval-{proposal_id}",
                prompt_version=prompt_version,
                system=system_prompt,
                payload=payload,
            )
        except (json.JSONDecodeError, RuntimeError):
            # A malformed/failed model response excludes this batch's traces from the
            # denominator; it must never crash the whole executor or invent a value.
            return {}
        requested = {str(unit["evidence_id"]) for unit in batch}
        return parse_judge_results(response, label_set, requested)

    values: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max(1, semantic_workers)) as pool:
        for partial in pool.map(judge, batches):
            values.update(partial)

    per_trace = []
    for unit in units:
        evidence_id = unit["evidence_id"]
        if evidence_id in values:
            per_trace.append(
                {
                    "evidence_id": evidence_id,
                    "value": values[evidence_id],
                    "abstain_reason": None,
                    "evidence_quote": "",
                }
            )
        else:
            # Omitted by the model (genuinely unclear, or a malformed batch) -- honestly
            # counted as an abstain here, never silently dropped from the denominator.
            per_trace.append(
                {
                    "evidence_id": evidence_id,
                    "value": "ABSTAIN",
                    "abstain_reason": "NO_RESULT_RETURNED",
                    "evidence_quote": "",
                }
            )
    return per_trace


def execute_semantic_bundle(
    bundle: dict[str, Any],
    trace_bundles: Iterable[NormalizedTraceBundle],
    model: StructuredModel,
    *,
    semantic_workers: int = 4,
) -> dict[str, Any]:
    """Re-apply every PINNED_SEMANTIC_JUDGE definition to unseen trace bundles.

    For each measurement: classify each trace into IN/OUT/UNKNOWN with the frozen
    population classifier, run the pinned judge (frozen system prompt + model)
    on the IN traces via the completeness-retry batching, then aggregate with the
    same frozen contract used at discovery time. No rediscovery, no re-authoring.
    """
    validate_measurement_bundle(bundle)
    ordered = list(trace_bundles)
    evaluator = bundle["evaluator"]
    classifiers = {
        population_id: PopulationClassifier.from_dict(spec)
        for population_id, spec in bundle["population_classifiers"].items()
    }

    results = []
    for row in bundle["definitions"]:
        if row.get("executor") == "NATIVE_SIGNAL":
            continue
        definition = _definition_from_dict(row)
        population_ids = list(definition.population_ids)
        is_global = population_ids == ["GLOBAL"]

        # Frozen denominator: only traces the classifier places IN this population.
        in_traces = []
        for tb in ordered:
            if is_global:
                in_traces.append(tb)
                continue
            label = None
            for population_id in population_ids:
                classifier = classifiers.get(population_id)
                if classifier is not None and classifier.classify(_classifier_text(tb)) == "IN":
                    label = "IN"
                    break
            if label == "IN":
                in_traces.append(tb)

        units = [
            {"evidence_id": tb.trace_id, "compact_evidence": compact_trace_evidence(tb)}
            for tb in in_traces
        ]
        proposal_id = str(row["proposal_id"])
        # The bundle's own evaluator carries its judge contract's quote policy: "NONE"
        # means the bundle was authored under behavioral_evals' omit-without-unknown
        # contract (gate.py's EXECUTOR_JUDGE_SYSTEM), not goal_observables' deprecated
        # quote-grounded/ABSTAIN contract this module otherwise reuses. Legacy bundles
        # (measurement_promotion.build_measurement_bundle) never set quote_policy to
        # "NONE" -- they fall through to the original _judge_with_retries path unchanged.
        if evaluator.get("result_contract", {}).get("quote_policy") == "NONE":
            per_trace = _judge_omit_contract(
                model, evaluator, definition, proposal_id, units, semantic_workers=semantic_workers
            )
        else:
            requests = [
                {
                    "trace": unit,
                    "proposals": [
                        {
                            "proposal_id": proposal_id,
                            "title": definition.name,
                            "observable_definition": definition.observable_definition,
                            "categories": list(definition.labels),
                        }
                    ],
                }
                for unit in units
            ]
            judged = _judge_with_retries(
                model,
                requests,
                semantic_workers=semantic_workers,
                max_requests_per_batch=12,
                max_pairs_per_batch=12,
                max_retries=2,
            )
            per_trace = [
                {
                    "evidence_id": row_["evidence_id"],
                    "value": row_["value"],
                    "abstain_reason": row_.get("abstain_reason"),
                    "evidence_quote": row_.get("evidence_quote", ""),
                }
                for row_ in judged
            ]
        results.append(
            {"proposal_id": proposal_id, "population_evaluated": population_ids}
            | execute_frozen_results(definition, per_trace)
            | {"per_trace_results": per_trace}
        )

    return {
        "schema_version": "measurement-bundle-semantic-execution-v0.1",
        "bundle_hash": bundle_hash(bundle),
        "results": results,
    }
