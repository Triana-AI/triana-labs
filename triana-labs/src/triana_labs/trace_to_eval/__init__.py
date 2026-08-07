"""Local, evidence-grounded Trace-to-Eval Review V0 engine.

The module adapts the bounded semantic-proposal shape of Agentagon Exploration V1
to Triana's PreviewTrace contract.  Models may propose labels and criteria; this
module owns validation, membership, accounting, splits, identities, persistence,
and the append-only human-review ledger.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, cast

from triana_labs.contracts.traces import LineRejection, parse_and_validate_line
from triana_labs.trace_to_eval.semantic import (
    ValidatedCheckpointSemanticModel,
    run_staged_analysis,
)

JsonObject = dict[str, Any]

_REPORT_KIND = "trace_to_eval_report_v0"
_QUEUE_KIND = "review_queue_v0"
_RULING_KIND = "human_ruling_v0"
_SPLITS = ("DEVELOPMENT", "CALIBRATION", "HOLDOUT")
_SAFE_TRACE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$")
_TYPED_SEMANTIC_FAILURES = {
    "SEMANTIC_BUDGET_EXCEEDED",
    "SEMANTIC_CHECKPOINT_INVALID",
    "SEMANTIC_PROVIDER_CALL_FAILED",
    "SEMANTIC_REQUEST_TOO_LARGE",
    "SEMANTIC_RESPONSE_CONTENT_MISSING",
    "SEMANTIC_RESPONSE_JSON_INVALID",
    "SEMANTIC_SCHEMA_INVALID",
}


class TraceToEvalError(ValueError):
    """Refuse an invalid or tampered Trace-to-Eval operation."""


def _canonical(value: Any, *, lf: bool = False) -> bytes:
    try:
        payload = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise TraceToEvalError("ARTIFACT_CANONICALIZATION_FAILED") from error
    return payload + (b"\n" if lf else b"")


def _digest(domain: str, value: Any) -> str:
    return (
        "sha256:"
        + hashlib.sha256(domain.encode("ascii") + b"\0" + _canonical(value)).hexdigest()
    )


def _read_object(path: Path, code: str) -> JsonObject:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise TraceToEvalError(code) from error
    if not isinstance(value, dict):
        raise TraceToEvalError(code)
    return cast(JsonObject, value)


def _require_manifest(value: JsonObject) -> None:
    if value.get("artifact_kind") != "evidence_bundle_manifest_v0":
        raise TraceToEvalError("MANIFEST_INVALID")
    if value.get("schema_version") != 0:
        raise TraceToEvalError("MANIFEST_VERSION_UNSUPPORTED")
    for field in ("source", "agent", "privacy", "grouping", "capabilities"):
        if not isinstance(value.get(field), dict):
            raise TraceToEvalError("MANIFEST_INVALID")


def _source_path(manifest_path: Path, source: Mapping[str, Any]) -> Path:
    raw = source.get("path")
    if not isinstance(raw, str) or not raw:
        raise TraceToEvalError("MANIFEST_INVALID")
    path = Path(raw)
    return path if path.is_absolute() else manifest_path.parent / path


def _verified_source(manifest_path: Path, manifest: JsonObject) -> tuple[Path, bytes]:
    source = cast(Mapping[str, Any], manifest["source"])
    path = _source_path(manifest_path, source)
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise TraceToEvalError("SOURCE_UNAVAILABLE") from error
    expected = source.get("sha256")
    observed = "sha256:" + hashlib.sha256(payload).hexdigest()
    if expected != observed:
        raise TraceToEvalError("SOURCE_HASH_MISMATCH")
    return path, payload


def _ingest(payload: bytes) -> tuple[list[JsonObject], list[JsonObject]]:
    accepted: list[JsonObject] = []
    rejections: list[JsonObject] = []
    trace_ids: set[str] = set()
    source_trace_ids: set[str] = set()
    for line_number, raw_line in enumerate(payload.splitlines(), start=1):
        try:
            validated = parse_and_validate_line(raw_line, first_line=line_number == 1)
            trace = validated.value
            trace_id = cast(str, trace["trace_id"])
            source_trace_id = cast(str, trace["source_trace_id"])
            if trace_id in trace_ids:
                raise LineRejection("DUPLICATE_TRACE_ID", "/trace_id")
            if source_trace_id in source_trace_ids:
                raise LineRejection("DUPLICATE_SOURCE_TRACE_ID", "/source_trace_id")
            trace_ids.add(trace_id)
            source_trace_ids.add(source_trace_id)
            accepted.append(trace)
        except LineRejection as rejection:
            pointer = rejection.json_pointer
            if rejection.code == "SCHEMA_VALIDATION_FAILED" and not pointer:
                # The shared closed-schema validator sees unknown top-level keys before
                # field grammar. Trace-to-Eval's line accounting gives the invalid
                # identity field precedence when it can do so without retaining or
                # emitting any source content.
                try:
                    rejected_value = json.loads(raw_line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    rejected_value = None
                rejected_trace_id = (
                    rejected_value.get("trace_id")
                    if isinstance(rejected_value, dict)
                    else None
                )
                if not isinstance(
                    rejected_trace_id, str
                ) or not _SAFE_TRACE_ID.fullmatch(rejected_trace_id):
                    pointer = "/trace_id"
            rejections.append(
                {
                    "line_number": line_number,
                    "code": rejection.code,
                    "json_pointer": pointer,
                }
            )
    return accepted, rejections


def _validate_grouping(
    manifest: JsonObject, accepted_ids: set[str]
) -> tuple[dict[str, list[str]], dict[str, str]]:
    grouping = cast(Mapping[str, Any], manifest["grouping"])
    assignments = grouping.get("assignments")
    if not isinstance(assignments, list):
        raise TraceToEvalError("GROUPING_INVALID")
    groups: dict[str, list[str]] = {}
    trace_to_group: dict[str, str] = {}
    for assignment in assignments:
        if not isinstance(assignment, dict):
            raise TraceToEvalError("GROUPING_INVALID")
        group_id = assignment.get("group_id")
        trace_ids = assignment.get("trace_ids")
        if (
            not isinstance(group_id, str)
            or not group_id
            or group_id in groups
            or not isinstance(trace_ids, list)
            or not trace_ids
            or any(not isinstance(item, str) for item in trace_ids)
        ):
            raise TraceToEvalError("GROUPING_INVALID")
        members = cast(list[str], trace_ids)
        for trace_id in members:
            if trace_id not in accepted_ids or trace_id in trace_to_group:
                raise TraceToEvalError("GROUPING_INVALID")
            trace_to_group[trace_id] = group_id
        groups[group_id] = sorted(members)
    if set(trace_to_group) != accepted_ids:
        raise TraceToEvalError("GROUPING_INCOMPLETE")
    return groups, trace_to_group


def _split_counts(size: int) -> tuple[int, int, int]:
    if size <= 0:
        return (0, 0, 0)
    numerators = (60, 20, 20)
    floors = [size * numerator // 100 for numerator in numerators]
    remaining = size - sum(floors)
    remainders = [size * numerator % 100 for numerator in numerators]
    order = sorted(range(3), key=lambda index: (-remainders[index], index))
    for index in order[:remaining]:
        floors[index] += 1
    return cast(tuple[int, int, int], tuple(floors))


def _assign_splits(
    corpus_hash: str, groups: Mapping[str, list[str]]
) -> tuple[list[JsonObject], dict[str, str]]:
    ranked = sorted(
        groups,
        key=lambda group_id: hashlib.sha256(
            b"triana-split-v0" + corpus_hash.encode("utf-8") + group_id.encode("utf-8")
        ).digest(),
    )
    counts = _split_counts(len(ranked))
    boundaries = (counts[0], counts[0] + counts[1])
    split_by_group: dict[str, str] = {}
    for index, group_id in enumerate(ranked):
        split = (
            _SPLITS[0]
            if index < boundaries[0]
            else _SPLITS[1]
            if index < boundaries[1]
            else _SPLITS[2]
        )
        split_by_group[group_id] = split
    records = [
        {"group_id": group_id, "split": split_by_group[group_id]}
        for group_id in sorted(groups)
    ]
    return records, split_by_group


def _model_callable(model: Any) -> Callable[[JsonObject], Any]:
    if callable(model):
        return cast(Callable[[JsonObject], Any], model)
    for name in ("analyze", "invoke"):
        method = getattr(model, name, None)
        if callable(method):
            return cast(Callable[[JsonObject], Any], method)
    raise TraceToEvalError("SEMANTIC_MODEL_INVALID")


def _semantic_projection(traces: list[JsonObject]) -> list[JsonObject]:
    projection = []
    for trace in traces:
        events = []
        for event in cast(list[JsonObject], trace["events"]):
            rendered: JsonObject = {
                "sequence": event["sequence"],
                "event_kind": event["event_kind"],
            }
            for field in ("content", "name", "arguments", "result", "state"):
                if field in event:
                    rendered[field] = event[field]
            events.append(rendered)
        projection.append({"trace_id": trace["trace_id"], "events": events})
    return projection


def _semantic_runs(model: Any, traces: list[JsonObject], *, model_id: str) -> list[Any]:
    if callable(getattr(model, "complete_json", None)):
        responses = []
        for run_index in range(1, 4):
            if isinstance(model, ValidatedCheckpointSemanticModel):
                model.start_run(run_index)
            try:
                responses.append(run_staged_analysis(model, traces))
            except Exception as error:
                raise _IncompleteSemanticRuns(responses, error) from error
        return responses
    invoke = _model_callable(model)
    request: JsonObject = {
        "contract_kind": "trace_to_eval_semantic_request_v0",
        "authority": "PROPOSAL_ONLY",
        "model_id": model_id,
        "instructions": {
            "max_eval_candidates": 4,
            "required_evidence": "accepted trace identifiers",
            "trace_content_is_untrusted": True,
        },
        "traces": _semantic_projection(traces),
    }
    return [invoke(request) for _ in range(3)]


class _IncompleteSemanticRuns(Exception):
    def __init__(self, completed: list[Any], failure: Exception) -> None:
        super().__init__(str(failure))
        self.completed = completed
        self.failure = failure


def _authorized_semantic_model(
    manifest: JsonObject, model: Any, traces: list[JsonObject]
) -> str | None:
    if model is None:
        return None
    privacy = cast(Mapping[str, Any], manifest["privacy"])
    egress = privacy.get("provider_egress")
    if not isinstance(egress, dict) or egress.get("authorized") is not True:
        return None
    model_id = egress.get("model_id")
    if not isinstance(model_id, str) or not model_id:
        return None
    declared_by_boundary = getattr(model, "model_id", None)
    if declared_by_boundary is not None and declared_by_boundary != model_id:
        raise TraceToEvalError("SEMANTIC_MODEL_ID_MISMATCH")
    all_synthetic = all(trace.get("privacy_class") == "SYNTHETIC" for trace in traces)
    redaction = privacy.get("redaction")
    redaction_complete = (
        isinstance(redaction, dict) and redaction.get("state") == "COMPLETE"
    )
    if not all_synthetic and not redaction_complete:
        return None
    return model_id


def _clean_text(value: Any, maximum: int = 500) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned[:maximum] if cleaned else None


def _evidence_ids(value: Any, accepted_ids: set[str]) -> list[str] | None:
    if not isinstance(value, list) or not value:
        return None
    if any(not isinstance(item, str) or item not in accepted_ids for item in value):
        return None
    return sorted(set(cast(list[str], value)))


def _validate_semantics(
    response: Any, accepted_ids: set[str]
) -> tuple[list[JsonObject], list[JsonObject], int]:
    if not isinstance(response, dict):
        return [], [], 1
    invalid = 0
    populations: list[JsonObject] = []
    population_rows = response.get("populations")
    if not isinstance(population_rows, list):
        invalid += 1
    else:
        for row in population_rows[:12]:
            if not isinstance(row, dict):
                invalid += 1
                continue
            label = _clean_text(row.get("label"), 120)
            description = _clean_text(row.get("description"))
            evidence = _evidence_ids(row.get("evidence_trace_ids"), accepted_ids)
            if label is None or description is None or evidence is None:
                invalid += 1
                continue
            population_id = _digest(
                "triana-population-v0",
                {
                    "description": description,
                    "evidence_trace_ids": evidence,
                    "label": label,
                },
            )
            populations.append(
                {
                    "population_id": population_id,
                    "label": label,
                    "description": description,
                    "support": len(evidence),
                    "evidence_trace_ids": evidence,
                    "proposal_state": "PROPOSED",
                }
            )
    candidates: list[JsonObject] = []
    candidate_rows = response.get("eval_candidates")
    if not isinstance(candidate_rows, list):
        invalid += 1
    else:
        for row in candidate_rows:
            if not isinstance(row, dict):
                invalid += 1
                continue
            name = _clean_text(row.get("name"), 120)
            criterion = _clean_text(row.get("criterion"))
            evidence = _evidence_ids(row.get("evidence_trace_ids"), accepted_ids)
            if name is None or criterion is None or evidence is None:
                invalid += 1
                continue
            proposal_id = _digest(
                "triana-eval-proposal-v0",
                {"criterion": criterion, "evidence_trace_ids": evidence, "name": name},
            )
            candidates.append(
                {
                    "proposal_id": proposal_id,
                    "name": name,
                    "criterion": criterion,
                    "support": len(evidence),
                    "evidence_trace_ids": evidence,
                    "proposal_state": "PROPOSED",
                }
            )
    return populations, candidates, invalid


def _stability(
    validated: list[tuple[list[JsonObject], list[JsonObject], int]],
) -> JsonObject:
    fingerprints = [
        _digest("triana-semantic-run-v0", {"populations": run[0], "candidates": run[1]})
        for run in validated
    ]
    disagreements: list[JsonObject] = []
    reference = fingerprints[0]
    for index, fingerprint in enumerate(fingerprints[1:], start=2):
        if fingerprint != reference:
            disagreements.append(
                {
                    "reference_run": 1,
                    "compared_run": index,
                    "reference_fingerprint": reference,
                    "compared_fingerprint": fingerprint,
                }
            )
    return {
        "semantic_run_count": len(validated),
        "state": "DISAGREEMENT_OBSERVED" if disagreements else "STABLE",
        "disagreements": disagreements,
        "rerun_selection": "NONE",
    }


def _gaps(
    manifest: JsonObject,
    *,
    semantic_available: bool,
    invalid_semantic_rows: int,
    semantic_failure_code: str | None = None,
) -> list[JsonObject]:
    capabilities = cast(Mapping[str, Any], manifest["capabilities"])
    gaps: list[JsonObject] = []
    if not semantic_available and semantic_failure_code is None:
        gaps.append(
            {
                "code": "SEMANTIC_ANALYSIS_UNAVAILABLE",
                "capability": "SEMANTIC_ANALYSIS",
                "state": "UNAVAILABLE",
            }
        )
    if invalid_semantic_rows:
        gaps.append(
            {
                "code": "UNGROUNDED_SEMANTIC_OUTPUT",
                "capability": "SEMANTIC_ANALYSIS",
                "state": "PARTIAL",
                "rejected_item_count": invalid_semantic_rows,
            }
        )
    if semantic_failure_code is not None:
        gaps.append(
            {
                "code": semantic_failure_code,
                "capability": "SEMANTIC_ANALYSIS",
                "state": "UNAVAILABLE",
            }
        )
    for manifest_key, capability in (
        ("outcomes", "OUTCOMES"),
        ("existing_evals", "EXISTING_EVALS"),
        ("embeddings", "EMBEDDINGS"),
    ):
        if capabilities.get(manifest_key) is not True:
            gaps.append(
                {
                    "code": f"{capability}_UNAVAILABLE",
                    "capability": capability,
                    "state": "UNAVAILABLE",
                }
            )
    gaps.append(
        {
            "code": "REMOTE_PERSISTENCE_UNAVAILABLE",
            "capability": "REMOTE_PERSISTENCE",
            "state": "UNAVAILABLE",
        }
    )
    return sorted(gaps, key=lambda gap: cast(str, gap["code"]))


def _behavior_analytics(traces: list[JsonObject]) -> JsonObject:
    tool_traces = 0
    turn_counts: list[int] = []
    event_kinds: dict[str, int] = {}
    for trace in traces:
        events = cast(list[JsonObject], trace["events"])
        turn_counts.append(
            sum(
                event["event_kind"] in {"USER_MESSAGE", "ASSISTANT_MESSAGE"}
                for event in events
            )
        )
        if any(event["event_kind"] == "TOOL_CALL" for event in events):
            tool_traces += 1
        for event in events:
            kind = cast(str, event["event_kind"])
            event_kinds[kind] = event_kinds.get(kind, 0) + 1
    return {
        "authority": "DETERMINISTIC",
        "conversation_count": len(traces),
        "event_kind_counts": dict(sorted(event_kinds.items())),
        "tool_observed_conversation_count": tool_traces,
        "turn_count": {
            "minimum": min(turn_counts) if turn_counts else 0,
            "maximum": max(turn_counts) if turn_counts else 0,
            "total": sum(turn_counts),
        },
    }


def _authoritative_outcomes(
    manifest: JsonObject, accepted_ids: set[str]
) -> dict[str, tuple[float, str]] | None:
    capabilities = cast(Mapping[str, Any], manifest["capabilities"])
    source = cast(Mapping[str, Any], manifest["source"])
    if (
        capabilities.get("outcomes") is not True
        or source.get("adapter_id") != "tau-archive"
    ):
        return None
    rows = manifest.get("outcomes")
    if not isinstance(rows, list) or not rows:
        raise TraceToEvalError("OUTCOMES_INVALID")
    outcomes: dict[str, tuple[float, str]] = {}
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "trace_id",
            "group_id",
            "source",
            "reward",
            "outcome",
        }:
            raise TraceToEvalError("OUTCOMES_INVALID")
        trace_id = row.get("trace_id")
        reward = row.get("reward")
        outcome = row.get("outcome")
        if (
            not isinstance(trace_id, str)
            or trace_id not in accepted_ids
            or trace_id in seen
            or row.get("source") != "TAU2_REWARD_INFO"
            or not isinstance(reward, (int, float))
            or isinstance(reward, bool)
            or not math.isfinite(float(reward))
            or outcome not in {"SUCCESS", "FAILURE"}
            or (outcome == "SUCCESS") != (float(reward) == 1.0)
        ):
            raise TraceToEvalError("OUTCOMES_INVALID")
        seen.add(trace_id)
        outcomes[trace_id] = (float(reward), cast(str, outcome))
    if seen != accepted_ids:
        raise TraceToEvalError("OUTCOMES_INVALID")
    return outcomes


def _outcome_analytics(
    outcomes: Mapping[str, tuple[float, str]] | None,
) -> JsonObject | None:
    if outcomes is None:
        return None
    rewards = [row[0] for row in outcomes.values()]
    success_count = sum(row[1] == "SUCCESS" for row in outcomes.values())
    return {
        "authority": "DETERMINISTIC",
        "source": "TAU2_REWARD_INFO",
        "denominator": len(rewards),
        "success_count": success_count,
        "failure_count": len(rewards) - success_count,
        "mean_reward": sum(rewards) / len(rewards),
    }


def _partial_handling_evidence(
    responses: list[Any],
    *,
    discovery_ids: set[str],
    outcomes: Mapping[str, tuple[float, str]] | None,
) -> JsonObject | None:
    runs: list[JsonObject] = []
    for run_index, response in enumerate(responses, start=1):
        raw_items = response.get("handling_items") if isinstance(response, dict) else None
        items = [
            cast(JsonObject, item)
            for item in raw_items
            if isinstance(item, dict) and item.get("trace_id") in discovery_ids
        ] if isinstance(raw_items, list) else []
        items.sort(key=lambda item: cast(str, item["trace_id"]))
        runs.append({"run_index": run_index, "items": items})
    if not runs:
        return None
    partial: JsonObject = {
        "state": "PARTIAL",
        "authority": "PROPOSAL_ONLY",
        "completed_run_count": len(runs),
        "runs": runs,
    }
    if outcomes is not None:
        grouped: dict[str, list[tuple[str, float, str]]] = {}
        for item in cast(list[JsonObject], runs[0]["items"]):
            trace_id = cast(str, item["trace_id"])
            outcome = outcomes.get(trace_id)
            if outcome is None:
                continue
            mode = cast(str, item["handling_mode"])
            grouped.setdefault(mode, []).append((trace_id, *outcome))
        partial["outcome_by_handling_mode"] = [
            {
                "handling_mode": mode,
                "denominator": len(rows),
                "trace_ids": [row[0] for row in rows],
                "success_count": sum(row[2] == "SUCCESS" for row in rows),
                "failure_count": sum(row[2] == "FAILURE" for row in rows),
                "mean_reward": sum(row[1] for row in rows) / len(rows),
            }
            for mode, rows in sorted(grouped.items())
        ]
    return partial


def _review_queue(
    report_id: str, populations: list[JsonObject], proposals: list[JsonObject]
) -> JsonObject:
    items: list[JsonObject] = []
    for population in populations[:4]:
        evidence = cast(list[str], population["evidence_trace_ids"])
        if len(evidence) < 2:
            continue
        body: JsonObject = {
            "item_kind": "POPULATION_PAIR",
            "trace_ids": evidence[:2],
            "allowed_decisions": [
                "SAME",
                "DIFFERENT",
                "AMBIGUOUS",
                "INSUFFICIENT_EVIDENCE",
            ],
        }
        body["item_id"] = _digest("triana-review-item-id-v0", body)
        body["item_hash"] = _digest("triana-review-item-v0", body)
        items.append(body)
    for proposal in proposals[:3]:
        body = {
            "item_kind": "EVAL_PROPOSAL",
            "proposal_id": proposal["proposal_id"],
            "name": proposal["name"],
            "criterion": proposal["criterion"],
            "evidence_trace_ids": proposal["evidence_trace_ids"],
            "allowed_decisions": ["TRACK", "EDIT", "DEFER"],
        }
        body["item_id"] = _digest("triana-review-item-id-v0", body)
        body["item_hash"] = _digest("triana-review-item-v0", body)
        items.append(body)
    items.sort(
        key=lambda item: hashlib.sha256(
            b"triana-review-v0"
            + report_id.encode("utf-8")
            + cast(str, item["item_id"]).encode("utf-8")
        ).digest()
    )
    return {
        "artifact_kind": _QUEUE_KIND,
        "schema_version": 0,
        "report_id": report_id,
        "items": items,
    }


def _write_artifact(path: Path, value: Any) -> None:
    path.write_bytes(_canonical(value, lf=True))


def _ledger_path(output_dir: Path) -> Path:
    return output_dir / "human_rulings.jsonl"


def _read_rulings(
    output_dir: Path,
    *,
    report_id: str | None = None,
    queue: JsonObject | None = None,
) -> list[JsonObject]:
    path = _ledger_path(output_dir)
    if not path.exists():
        return []
    records: list[JsonObject] = []
    try:
        previous_id: str | None = None
        prior_by_id: dict[str, JsonObject] = {}
        queue_items = queue.get("items") if isinstance(queue, dict) else None
        for line in path.read_bytes().splitlines():
            value = json.loads(line)
            if (
                not isinstance(value, dict)
                or set(value)
                != {
                    "artifact_kind",
                    "schema_version",
                    "report_id",
                    "item_id",
                    "item_hash",
                    "decision",
                    "edited_text",
                    "reviewer_id",
                    "ruled_at",
                    "supersedes_ruling_id",
                    "previous_ruling_id",
                    "ruling_id",
                }
                or value.get("artifact_kind") != _RULING_KIND
                or value.get("schema_version") != 0
                or value.get("previous_ruling_id") != previous_id
            ):
                raise TraceToEvalError("RULING_LEDGER_TAMPERED")
            record = cast(JsonObject, value)
            ruling_id = record.get("ruling_id")
            unsigned = {key: item for key, item in record.items() if key != "ruling_id"}
            if not isinstance(ruling_id, str) or ruling_id != _digest(
                "triana-human-ruling-v0", unsigned
            ):
                raise TraceToEvalError("RULING_LEDGER_TAMPERED")
            if report_id is not None and record.get("report_id") != report_id:
                raise TraceToEvalError("RULING_LEDGER_TAMPERED")
            supersedes = record.get("supersedes_ruling_id")
            if supersedes is not None:
                prior = prior_by_id.get(cast(str, supersedes))
                if prior is None or prior.get("item_id") != record.get("item_id"):
                    raise TraceToEvalError("RULING_LEDGER_TAMPERED")
            if isinstance(queue_items, list):
                item = next(
                    (
                        row
                        for row in queue_items
                        if isinstance(row, dict)
                        and row.get("item_id") == record.get("item_id")
                    ),
                    None,
                )
                if (
                    item is None
                    or item.get("item_hash") != record.get("item_hash")
                    or record.get("decision") not in item.get("allowed_decisions", [])
                ):
                    raise TraceToEvalError("RULING_LEDGER_TAMPERED")
            records.append(record)
            prior_by_id[ruling_id] = record
            previous_id = ruling_id
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise TraceToEvalError("RULING_LEDGER_TAMPERED") from error
    return records


def run_trace_to_eval(
    manifest_path: str | Path,
    output_dir: str | Path,
    *,
    semantic_model: Any = None,
) -> JsonObject:
    """Analyze one manifest-declared PreviewTrace corpus and persist local artifacts."""

    manifest_file = Path(manifest_path)
    manifest = _read_object(manifest_file, "MANIFEST_INVALID")
    _require_manifest(manifest)
    _, source_bytes = _verified_source(manifest_file, manifest)
    source = cast(Mapping[str, Any], manifest["source"])
    physical_count = source.get("physical_record_count")
    upstream_physical_count = source.get("upstream_physical_record_count")
    if upstream_physical_count is not None and (
        type(upstream_physical_count) is not int
        or type(physical_count) is not int
        or upstream_physical_count < physical_count
    ):
        raise TraceToEvalError("MANIFEST_INVALID")
    actual_normalized_count = len(source_bytes.splitlines())
    normalized_count = source.get("normalized_record_count", physical_count)
    if normalized_count != actual_normalized_count:
        raise TraceToEvalError("PHYSICAL_RECORD_COUNT_MISMATCH")
    traces, rejections = _ingest(source_bytes)
    adapter_rejections = manifest.get("adapter_rejections", [])
    if not isinstance(adapter_rejections, list) or any(
        not isinstance(row, dict)
        or set(row) != {"line_number", "code", "json_pointer"}
        or type(row["line_number"]) is not int
        or row["line_number"] < 1
        or not isinstance(row["code"], str)
        or not isinstance(row["json_pointer"], str)
        for row in adapter_rejections
    ):
        raise TraceToEvalError("MANIFEST_INVALID")
    rejections = [*cast(list[JsonObject], adapter_rejections), *rejections]
    if type(physical_count) is not int or physical_count != len(traces) + len(
        rejections
    ):
        raise TraceToEvalError("PHYSICAL_RECORD_COUNT_MISMATCH")
    if not traces:
        raise TraceToEvalError("NO_ACCEPTED_CONVERSATIONS")
    accepted_ids = {cast(str, trace["trace_id"]) for trace in traces}
    groups, trace_to_group = _validate_grouping(manifest, accepted_ids)
    corpus_hash = cast(str, source["sha256"])
    group_splits, split_by_group = _assign_splits(corpus_hash, groups)
    inventory = [
        {
            "trace_id": trace_id,
            "group_id": trace_to_group[trace_id],
            "split": split_by_group[trace_to_group[trace_id]],
            "evidence_handle": f"conversation:{trace_id}",
        }
        for trace_id in sorted(accepted_ids)
    ]

    discovery_traces = [
        trace
        for trace in traces
        if split_by_group[trace_to_group[cast(str, trace["trace_id"])]] == "DEVELOPMENT"
    ]
    discovery_ids = {cast(str, trace["trace_id"]) for trace in discovery_traces}
    semantic_model_id = _authorized_semantic_model(
        manifest, semantic_model, discovery_traces
    )
    semantic_authorized = semantic_model_id is not None and bool(discovery_traces)
    destination = Path(output_dir)
    if semantic_authorized and callable(
        getattr(semantic_model, "complete_json", None)
    ):
        destination.mkdir(parents=True, exist_ok=True)
        semantic_model = ValidatedCheckpointSemanticModel(
            semantic_model, destination / "semantic_checkpoints"
        )
    semantic_available = False
    semantic_failure_code: str | None = None
    invalid_semantic_rows = 0
    behavior_candidate_inventory: list[JsonObject] = []
    partial_handling_evidence: JsonObject | None = None
    authoritative_outcomes = _authoritative_outcomes(manifest, accepted_ids)
    if semantic_authorized:
        try:
            responses = _semantic_runs(
                semantic_model,
                discovery_traces,
                model_id=cast(str, semantic_model_id),
            )
            validated = [
                _validate_semantics(response, discovery_ids) for response in responses
            ]
            populations, qualified_inventory, _ = validated[0]
            behavior_candidate_inventory = (
                cast(
                    list[JsonObject],
                    responses[0].get("behavior_candidate_inventory", []),
                )
                if isinstance(responses[0], dict)
                else []
            )
            invalid_semantic_rows = sum(run[2] for run in validated) + sum(
                int(response.get("semantic_gap_count", 0))
                for response in responses
                if isinstance(response, dict)
                and isinstance(response.get("semantic_gap_count", 0), int)
            )
            stability = _stability(validated)
            semantic_available = True
        except Exception as error:  # noqa: BLE001 - optional provider boundary.
            completed_responses = (
                error.completed if isinstance(error, _IncompleteSemanticRuns) else []
            )
            original_error = (
                error.failure if isinstance(error, _IncompleteSemanticRuns) else error
            )
            semantic_failure_code = (
                str(original_error)
                if str(original_error) in _TYPED_SEMANTIC_FAILURES
                else "SEMANTIC_ANALYSIS_FAILED"
            )
            record_failure = getattr(semantic_model, "record_failure", None)
            if callable(record_failure):
                record_failure(semantic_failure_code)
            populations = []
            qualified_inventory = []
            behavior_candidate_inventory = []
            partial_handling_evidence = _partial_handling_evidence(
                completed_responses,
                discovery_ids=discovery_ids,
                outcomes=authoritative_outcomes,
            )
            completed_run_count = (
                cast(int, partial_handling_evidence["completed_run_count"])
                if partial_handling_evidence is not None
                else 0
            )
            stability = {
                "semantic_run_count": completed_run_count,
                "state": "PARTIAL" if completed_run_count else "UNAVAILABLE",
                "disagreements": [],
                "rerun_selection": "NONE",
            }
    else:
        populations = []
        qualified_inventory = []
        stability = {
            "semantic_run_count": 0,
            "state": "UNAVAILABLE",
            "disagreements": [],
            "rerun_selection": "NONE",
        }
    eval_proposals = qualified_inventory[:3]
    outcome_analytics = _outcome_analytics(authoritative_outcomes)
    report_without_id: JsonObject = {
        "artifact_kind": _REPORT_KIND,
        "schema_version": 0,
        "accounting": {
            "physical_record_count": physical_count,
            "accepted_conversation_count": len(traces),
            "rejected_record_count": len(rejections),
            **(
                {
                    "upstream_physical_record_count": source[
                        "upstream_physical_record_count"
                    ],
                    "canonical_normalized_record_count": physical_count,
                }
                if type(source.get("upstream_physical_record_count")) is int
                else {}
            ),
        },
        "rejections": rejections,
        "capabilities": dict(cast(Mapping[str, Any], manifest["capabilities"])),
        "gaps": _gaps(
            manifest,
            semantic_available=semantic_available,
            invalid_semantic_rows=invalid_semantic_rows,
            semantic_failure_code=semantic_failure_code,
        ),
        "group_splits": group_splits,
        "conversation_inventory": inventory,
        "populations": populations,
        "behavior_analytics": _behavior_analytics(traces),
        **({"outcome_analytics": outcome_analytics} if outcome_analytics else {}),
        **(
            {"partial_handling_evidence": partial_handling_evidence}
            if partial_handling_evidence is not None
            else {}
        ),
        "behavior_candidate_inventory": behavior_candidate_inventory,
        "qualified_eval_inventory": qualified_inventory,
        "eval_proposals": eval_proposals,
        "stability": stability,
        "method": {
            "authority": {
                "deterministic": "identity, accounting, splits, evidence, arithmetic, hashes, persistence",
                "semantic_model": "proposed labels, descriptions, and criteria only",
                "human": "pair meaning and Track/Edit/Defer rulings",
            },
            "semantic_run_policy": (
                "THREE_FIXED_RUNS_NO_SELECTION"
                if semantic_available
                else "PROVIDER_FAILED_NO_RETRY_OR_FALLBACK"
                if semantic_failure_code is not None
                else "NO_PROVIDER"
            ),
            "source_hash": corpus_hash,
            "semantic_lineage": semantic_model.lineage()
            if semantic_authorized
            and callable(getattr(semantic_model, "lineage", None))
            else None,
            "semantic_discovery_split": "DEVELOPMENT",
            "semantic_discovery_conversation_count": len(discovery_traces),
            "sealed_calibration_conversation_count": sum(
                item["split"] == "CALIBRATION" for item in inventory
            ),
            "sealed_holdout_conversation_count": sum(
                item["split"] == "HOLDOUT" for item in inventory
            ),
            "persisted_conversation_split": "DEVELOPMENT",
            "persisted_conversation_count": len(discovery_traces),
        },
        "review_state": {
            "state": "PENDING" if eval_proposals else "NOT_AVAILABLE",
            "ruling_count": 0,
        },
    }
    report_id = _digest("triana-trace-to-eval-report-v0", report_without_id)
    report = {**report_without_id, "report_id": report_id}
    queue = _review_queue(report_id, populations, eval_proposals)

    destination.mkdir(parents=True, exist_ok=True)
    # Validate an existing ledger before replacing projections, but keep the report
    # immutable. Current human state is the append-only ledger, not mutable report
    # content under an unchanged report identity.
    _read_rulings(destination, report_id=report_id, queue=queue)
    _write_artifact(destination / "trace_to_eval_report.json", report)
    _write_artifact(destination / "review_queue.json", queue)
    _write_artifact(
        destination / "conversations.json",
        {
            "artifact_kind": "trace_to_eval_conversations_v0",
            "schema_version": 0,
            "report_id": report_id,
            "visible_scope": "DEVELOPMENT_ONLY",
            "conversations": discovery_traces,
        },
    )
    return report


def append_human_ruling(
    output_dir: str | Path, ruling: Mapping[str, Any]
) -> JsonObject:
    """Validate and append one immutable ruling without rewriting prior records."""

    destination = Path(output_dir)
    report = _read_object(
        destination / "trace_to_eval_report.json", "REPORT_UNAVAILABLE"
    )
    queue = _read_object(destination / "review_queue.json", "REVIEW_QUEUE_UNAVAILABLE")
    if (
        report.get("artifact_kind") != _REPORT_KIND
        or queue.get("artifact_kind") != _QUEUE_KIND
    ):
        raise TraceToEvalError("REVIEW_ARTIFACT_INVALID")
    report_id = report.get("report_id")
    if ruling.get("report_id") != report_id or queue.get("report_id") != report_id:
        raise TraceToEvalError("RULING_REPORT_MISMATCH")
    items = queue.get("items")
    if not isinstance(items, list):
        raise TraceToEvalError("REVIEW_QUEUE_INVALID")
    item = next(
        (
            candidate
            for candidate in items
            if isinstance(candidate, dict)
            and candidate.get("item_id") == ruling.get("item_id")
        ),
        None,
    )
    if item is None or ruling.get("item_hash") != item.get("item_hash"):
        raise TraceToEvalError("RULING_ITEM_MISMATCH")
    decision = ruling.get("decision")
    allowed = item.get("allowed_decisions")
    if (
        not isinstance(decision, str)
        or not isinstance(allowed, list)
        or decision not in allowed
    ):
        raise TraceToEvalError("RULING_DECISION_INVALID")
    edited_text = ruling.get("edited_text")
    if decision == "EDIT":
        if _clean_text(edited_text, 2_000) is None:
            raise TraceToEvalError("RULING_EDIT_INVALID")
    elif edited_text is not None:
        raise TraceToEvalError("RULING_EDIT_INVALID")
    reviewer_id = _clean_text(ruling.get("reviewer_id"), 128)
    ruled_at = _clean_text(ruling.get("ruled_at"), 64)
    if reviewer_id is None or ruled_at is None:
        raise TraceToEvalError("RULING_IDENTITY_INVALID")

    previous = _read_rulings(destination, report_id=cast(str, report_id), queue=queue)
    prior_ids = {record.get("ruling_id") for record in previous}
    supersedes = ruling.get("supersedes_ruling_id")
    if supersedes is not None:
        if supersedes not in prior_ids:
            raise TraceToEvalError("RULING_SUPERSESSION_INVALID")
        prior = next(
            record for record in previous if record.get("ruling_id") == supersedes
        )
        if prior.get("item_id") != ruling.get("item_id"):
            raise TraceToEvalError("RULING_SUPERSESSION_INVALID")
    elif any(record.get("item_id") == ruling.get("item_id") for record in previous):
        raise TraceToEvalError("RULING_SUPERSESSION_REQUIRED")

    accepted: JsonObject = {
        "artifact_kind": _RULING_KIND,
        "schema_version": 0,
        "report_id": report_id,
        "item_id": ruling["item_id"],
        "item_hash": ruling["item_hash"],
        "decision": decision,
        "edited_text": edited_text,
        "reviewer_id": reviewer_id,
        "ruled_at": ruled_at,
        "supersedes_ruling_id": supersedes,
        "previous_ruling_id": previous[-1]["ruling_id"] if previous else None,
    }
    accepted["ruling_id"] = _digest("triana-human-ruling-v0", accepted)
    if accepted["ruling_id"] in prior_ids:
        raise TraceToEvalError("DUPLICATE_RULING")
    with _ledger_path(destination).open("ab") as stream:
        stream.write(_canonical(accepted, lf=True))
    return accepted


def read_human_rulings(output_dir: str | Path, report_id: str) -> list[JsonObject]:
    """Read and fully validate the append-only human-ruling projection."""

    destination = Path(output_dir)
    queue = _read_object(destination / "review_queue.json", "REVIEW_QUEUE_UNAVAILABLE")
    return _read_rulings(destination, report_id=report_id, queue=queue)


__all__ = [
    "TraceToEvalError",
    "append_human_ruling",
    "read_human_rulings",
    "run_trace_to_eval",
]
