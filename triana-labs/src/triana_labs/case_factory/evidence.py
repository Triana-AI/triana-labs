"""Verify upstream lineage and construct the allowlisted provider evidence."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from triana_labs.case_factory.primitives import (
    Invalid,
    Json,
    artifact_hash,
    canonical,
    compact_id,
    domain_hash,
    read_object_file,
    strict_json,
)
from triana_labs.intelligence.input import InputFailure, read_bundle

_INTELLIGENCE_LIMITS = {
    "clusters.json": 16 * 1024 * 1024,
    "derivation_report.json": 1024 * 1024,
    "personas/index.json": 1024 * 1024,
    "intents/index.json": 1024 * 1024,
    "turn_policies/index.json": 1024 * 1024,
}
_PROJECTED_FIELDS = {
    "USER_MESSAGE": "content",
    "ASSISTANT_MESSAGE": "content",
    "TOOL_CALL": "tool_name",
    "TOOL_RESULT": "result_state",
    "TERMINAL": "terminal_state",
}


def _gap_key(item: Json) -> tuple[str, str, int]:
    return item["reason_code"], item.get("trace_id", ""), item.get("event_sequence", -1)


def build(
    observer_path: Path, intelligence_path: Path
) -> tuple[Json, list[Json], Json, int]:
    try:
        observer_bytes, _, traces = read_bundle(observer_path)
    except InputFailure as error:
        raise Invalid(error.reason_code) from error
    intelligence_bytes = read_object_file(
        intelligence_path, 1024 * 1024, "MANIFEST_INVALID"
    )
    try:
        intelligence = strict_json(intelligence_bytes)
    except Invalid as error:
        raise Invalid("MANIFEST_INVALID") from error
    if not isinstance(intelligence, dict):
        raise Invalid("MANIFEST_INVALID")
    if intelligence.get("input_manifest_hash") != artifact_hash(observer_bytes):
        raise Invalid("INTELLIGENCE_MISMATCH")
    artifacts = intelligence.get("artifacts")
    if not isinstance(artifacts, dict) or "clusters.json" not in artifacts:
        raise Invalid("INTELLIGENCE_MISMATCH")
    payloads = {
        name: read_object_file(
            intelligence_path.parent / name, limit, "INTELLIGENCE_MISMATCH"
        )
        for name, limit in _INTELLIGENCE_LIMITS.items()
    }
    if set(artifacts) != set(_INTELLIGENCE_LIMITS) or any(
        artifact_hash(payload) != artifacts[name] for name, payload in payloads.items()
    ):
        raise Invalid("INTELLIGENCE_MISMATCH")
    try:
        parsed_payloads = {
            name: strict_json(payload) for name, payload in payloads.items()
        }
    except Invalid as error:
        raise Invalid("INTELLIGENCE_MISMATCH") from error
    if any(
        canonical(parsed_payloads[name], lf=True) != payload
        for name, payload in payloads.items()
    ):
        raise Invalid("INTELLIGENCE_MISMATCH")
    clusters_bytes = payloads["clusters.json"]
    try:
        cluster_root = strict_json(clusters_bytes)
        clusters = cluster_root["clusters"]
    except (Invalid, KeyError, TypeError) as error:
        raise Invalid("INTELLIGENCE_MISMATCH") from error
    cluster_by_trace: dict[str, str] = {}
    ordered_clusters: list[list[str]] = []
    for cluster in sorted(clusters, key=lambda item: item["cluster_id"]):
        members = sorted(cluster["member_trace_ids"])
        ordered_clusters.append(members)
        for trace_id in members:
            if trace_id in cluster_by_trace:
                raise Invalid("INTELLIGENCE_MISMATCH")
            cluster_by_trace[trace_id] = cluster["cluster_id"]
    trace_by_id = {cast(str, trace["trace_id"]): trace for trace in traces}
    if set(cluster_by_trace) != set(trace_by_id):
        raise Invalid("INTELLIGENCE_MISMATCH")
    candidates = _round_robin(ordered_clusters)
    selected: list[Json] = []
    gaps: list[Json] = []
    eligible = [trace_id for trace_id in candidates if _eligible(trace_by_id[trace_id])]
    for trace_id in eligible:
        if len(selected) == 25:
            gaps.append({"reason_code": "EVIDENCE_TRACE_LIMIT_REACHED"})
            break
        projected, event_gaps = _project(
            trace_by_id[trace_id], cluster_by_trace[trace_id]
        )
        gaps.extend(event_gaps)
        if not any(
            event["event_kind"] == "USER_MESSAGE" for event in projected["events"]
        ):
            gaps.append(
                {"reason_code": "NO_USABLE_USER_EVIDENCE", "trace_id": trace_id}
            )
            continue
        trial = _root(observer_bytes, intelligence_bytes, [*selected, projected], gaps)
        if len(canonical(trial)) > 90_000:
            gaps.append(
                {"reason_code": "EVIDENCE_BYTE_LIMIT_REACHED", "trace_id": trace_id}
            )
            continue
        selected.append(projected)
    gaps.sort(key=_gap_key)
    root = _root(observer_bytes, intelligence_bytes, selected, gaps)
    if not selected:
        raise Invalid("NO_USABLE_SEMANTIC_EVIDENCE")
    citations = _citations(selected)
    excluded = len(eligible) - len(selected)
    return root, citations, intelligence, excluded


def _root(
    observer: bytes, intelligence: bytes, selected: list[Json], gaps: list[Json]
) -> Json:
    return {
        "artifact_kind": "case_factory_provider_evidence",
        "schema_version": 1,
        "input_manifest_hash": artifact_hash(observer),
        "intelligence_manifest_hash": artifact_hash(intelligence),
        "selection_algorithm": "LABS04_CLUSTER_ROUND_ROBIN_V1",
        "selected_traces": selected,
        "gaps": sorted(gaps, key=_gap_key),
    }


def _round_robin(clusters: list[list[str]]) -> list[str]:
    result: list[str] = []
    for index in range(max((len(item) for item in clusters), default=0)):
        result.extend(item[index] for item in clusters if index < len(item))
    return result


def _eligible(trace: Json) -> bool:
    user = False
    for event in cast(list[Json], trace["events"]):
        if event["event_kind"] == "USER_MESSAGE":
            user = True
        elif user and event["event_kind"] in {"ASSISTANT_MESSAGE", "TOOL_CALL"}:
            return True
    return False


def _project(trace: Json, cluster_id: str) -> tuple[Json, list[Json]]:
    events: list[Json] = []
    gaps: list[Json] = []
    for event in cast(list[Json], trace["events"]):
        kind = event["event_kind"]
        field = _PROJECTED_FIELDS.get(kind)
        if field is None:
            continue
        if field == "content" and len(cast(str, event["content"]).encode()) > 16_384:
            gaps.append(
                {
                    "reason_code": "EVIDENCE_EVENT_TOO_LARGE",
                    "trace_id": trace["trace_id"],
                    "event_sequence": event["sequence"],
                }
            )
            continue
        events.append(
            {
                "sequence": event["sequence"],
                "event_kind": kind,
                field: event[field],
            }
        )
    return {
        "trace_id": trace["trace_id"],
        "structural_cluster_id": cluster_id,
        "events": events,
    }, gaps


def _citations(traces: list[Json]) -> list[Json]:
    result: list[Json] = []
    for trace in traces:
        for event in trace["events"]:
            preimage = {
                "trace_id": trace["trace_id"],
                "event_sequences": [event["sequence"]],
                "evidence_hash": domain_hash(
                    "citation-evidence",
                    {
                        "trace_id": trace["trace_id"],
                        "structural_cluster_id": trace["structural_cluster_id"],
                        "events": [event],
                    },
                ),
                "structural_cluster_id": trace["structural_cluster_id"],
            }
            result.append({"citation_id": compact_id("citation", preimage), **preimage})
    return sorted(result, key=lambda item: item["citation_id"])
