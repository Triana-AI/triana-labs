"""Restricted, handle-grounded LABS-04 Case Factory runtime."""

from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from itertools import chain
from pathlib import Path
from typing import Any, Protocol, cast

from triana_labs import __version__
from triana_labs.case_factory.evidence import build as build_evidence
from triana_labs.case_factory.primitives import (
    SAFE_CODE,
    Invalid,
    Json,
    artifact_hash,
    bounded_text,
    byte_hash,
    canonical,
    contains_secret,
    domain_hash,
    strict_json,
)
from triana_labs.case_factory.provider import (
    ArtifactPublisher,
    AtomicPublisher,
    Clock,
    PublicationFailure,
)
from triana_labs.case_factory.semantic import Lane, apply_diversity, convert_lane

MODEL = "FW-GLM-5.2"
MODEL_VERSION = "1"
PROVIDER = "MICROSOFT_FOUNDRY_FIREWORKS"
TOOLS = (
    "search_evidence",
    "get_trace_packet",
    "inspect_budget",
    "submit_case_batch",
)
PORTABLE = (
    "control_personas.jsonl",
    "control_intents.jsonl",
    "control_turn_policies.jsonl",
    "control_case_candidates.jsonl",
    "personas.jsonl",
    "intents.jsonl",
    "turn_policies.jsonl",
    "case_candidates.jsonl",
)


@dataclass(frozen=True)
class AgentBatchRequest:
    run_id: str
    batch_id: str
    phase: str
    case_slots: tuple[str, ...]
    evidence_catalog: Json
    answers: list[Json]
    prior_submission: Json | None
    deterministic_defects: list[Json]
    remaining_budget_usd: str
    interaction_state: str
    answers_authoritative: bool


class RestrictedAgentTransport(Protocol):
    def run(self, request: AgentBatchRequest, tools: RestrictedTools) -> Any: ...


@dataclass(frozen=True)
class RestrictedResult:
    outcome: str
    reason_code: str | None
    manifest_path: Path
    attempted_case_count: int
    valid_case_count: int
    distinct_case_count: int
    provider_call_count: int
    conservative_cost_usd: str


@dataclass
class RestrictedTools:
    """The only model-callable surface; all methods are bounded and read-only."""

    catalog: Json
    budget: str
    submission: Json | None = None
    log_path: Path | None = None
    attempt_id: str | None = None
    sequence: int = 0
    search_cache: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = field(
        default_factory=dict, init=False, repr=False
    )

    def search_evidence(self, query: str) -> Json:
        def execute() -> Json:
            if not bounded_text(query, 512):
                raise Invalid
            query_key = " ".join(query.casefold().split())
            cached = self.search_cache.get(query_key)
            if cached is not None:
                return {
                    "trace_handles": list(cached[0]),
                    "evidence_handles": list(cached[1]),
                    "duplicate_query": True,
                    "searches_used": len(self.search_cache),
                    "searches_remaining": 2 - len(self.search_cache),
                }
            if len(self.search_cache) >= 2:
                return {
                    "trace_handles": [],
                    "evidence_handles": [],
                    "duplicate_query": False,
                    "searches_used": 2,
                    "searches_remaining": 0,
                }
            query_tokens = frozenset(re.findall(r"[a-z0-9]+", query.casefold()))
            ranked: list[tuple[int, str, tuple[tuple[int, int, str], ...]]] = []
            for trace in self.catalog["traces"]:
                event_matches = []
                for event in trace["events"]:
                    event_tokens = frozenset(
                        re.findall(r"[a-z0-9]+", canonical(event).decode().casefold())
                    )
                    score = len(query_tokens & event_tokens)
                    if score:
                        event_matches.append(
                            (-score, event["sequence"], event["evidence_handle"])
                        )
                if event_matches:
                    ranked.append(
                        (
                            -sum(-match[0] for match in event_matches),
                            trace["trace_handle"],
                            tuple(sorted(event_matches)),
                        )
                    )
            ranked.sort()
            trace_handles = (ranked[0][1],) if ranked else ()
            evidence_handles = (
                tuple(match[2] for match in ranked[0][2]) if ranked else ()
            )
            self.search_cache[query_key] = (trace_handles, evidence_handles)
            return {
                "trace_handles": list(trace_handles),
                "evidence_handles": list(evidence_handles),
                "duplicate_query": False,
                "searches_used": len(self.search_cache),
                "searches_remaining": 2 - len(self.search_cache),
            }

        return self._execute("search_evidence", {"query": query}, execute)

    def get_trace_packet(self, trace_handle: str) -> Json:
        def execute() -> Json:
            for trace in self.catalog["traces"]:
                if trace["trace_handle"] == trace_handle:
                    return cast(Json, trace)
            raise Invalid

        return self._execute(
            "get_trace_packet", {"trace_handle": trace_handle}, execute
        )

    def inspect_budget(self) -> Json:
        return self._execute(
            "inspect_budget",
            {},
            lambda: {"remaining_budget_usd": self.budget},
        )

    def submit_case_batch(self, submission: Json) -> Json:
        def execute() -> Json:
            if self.submission is not None:
                raise Invalid
            self.submission = submission
            return {"accepted_for_validation": True}

        return self._execute("submit_case_batch", {"submission": submission}, execute)

    def _execute(self, name: str, arguments: Json, execute: Any) -> Json:
        self.sequence += 1
        try:
            result = cast(Json, execute())
        except Exception as error:
            self._record(name, arguments, "FAILED", "TOOL_EXECUTION_FAILED", None)
            raise RestrictedToolFailure from error
        self._record(name, arguments, "SUCCEEDED", None, result)
        return result

    def _record(
        self,
        name: str,
        arguments: Json,
        status: str,
        reason: str | None,
        result: Json | None,
    ) -> None:
        if self.log_path is None or self.attempt_id is None:
            return
        _private_append(
            self.log_path,
            canonical(
                {
                    "artifact_kind": "case_factory_tool_call",
                    "schema_version": 1,
                    "attempt_id": self.attempt_id,
                    "sequence": self.sequence,
                    "tool_name": name,
                    "arguments": arguments,
                    "status": status,
                    "reason_code": reason,
                    "result": result,
                },
                lf=True,
            ),
        )


class RestrictedToolFailure(Exception):
    """Safe sentinel raised when an allowlisted tool fails closed."""


@dataclass
class _State:
    run_id: str
    evidence: Json
    citations: list[Json]
    catalog: Json
    handle_map: dict[str, Json]
    requested: int
    maximum: Decimal
    reservation: Decimal
    reserved: Decimal
    actual: Decimal
    actual_known: bool
    attempts: list[Json]
    lanes: list[Lane]
    calls: int
    cache: Path
    sentinels: list[bytes]
    config_hash: str
    clock: Clock


def generate_restricted(
    observer_manifest: Path,
    intelligence_manifest: Path,
    config_path: Path,
    output_path: Path,
    *,
    cache_path: Path,
    transport: RestrictedAgentTransport,
    clock: Clock,
    environ: Mapping[str, str],
    publisher: ArtifactPublisher | None = None,
    requested_case_count: int = 10,
) -> RestrictedResult:
    _output(output_path)
    _cache(cache_path, output_path)
    if not 1 <= requested_case_count <= 25:
        raise Invalid
    config_bytes = config_path.read_bytes()
    config = strict_json(config_bytes)
    maximum, reservation = _restricted_budget(config)
    evidence, citations, _, excluded = build_evidence(
        observer_manifest, intelligence_manifest
    )
    catalog, handle_map = _catalog(evidence, citations)
    run_id = domain_hash(
        "restricted-case-factory-run",
        {
            "input_manifest_hash": evidence["input_manifest_hash"],
            "intelligence_manifest_hash": evidence["intelligence_manifest_hash"],
            "config_hash": artifact_hash(config_bytes),
            "requested_case_count": requested_case_count,
        },
    )
    sentinels = _sentinels(config, environ)
    state = _State(
        run_id,
        evidence,
        citations,
        catalog,
        handle_map,
        requested_case_count,
        maximum,
        reservation,
        Decimal(0),
        Decimal(0),
        True,
        [],
        [],
        0,
        cache_path,
        sentinels,
        artifact_hash(config_bytes),
        clock,
    )
    slots = [f"case_{index}" for index in range(1, requested_case_count + 1)]
    for offset in range(0, len(slots), 5):
        batch_slots = tuple(slots[offset : offset + 5])
        result = _batch(
            state,
            transport,
            offset // 5 + 1,
            batch_slots,
            [],
        )
        if result[0] == "VALID":
            state.lanes.append(cast(Lane, result[1]))
            continue
        if result[0] == "NEEDS_INPUT":
            return _pause(
                state,
                cast(list[Json], result[1]),
                slots[:offset],
                slots[offset:],
                excluded,
                output_path,
                publisher,
            )
        return _terminal(
            state,
            cast(str, result[1]),
            excluded,
            output_path,
            publisher,
        )
    return _terminal(state, None, excluded, output_path, publisher)


def resume_restricted(
    pause_manifest: Path,
    answers: Mapping[str, str],
    output_path: Path,
    *,
    cache_path: Path,
    transport: RestrictedAgentTransport,
    clock: Clock,
    publisher: ArtifactPublisher | None = None,
) -> RestrictedResult:
    _output(output_path)
    manifest = strict_json(pause_manifest.read_bytes())
    resume = strict_json((pause_manifest.parent / "resume_state.json").read_bytes())
    questions = strict_json((pause_manifest.parent / "questions.json").read_bytes())
    expected = resume["question_ids"]
    if (
        set(answers) != set(expected)
        or any(not bounded_text(answers[item], 4096) for item in expected)
        or manifest.get("outcome") != "NEEDS_INPUT"
    ):
        raise Invalid("RESUME_INPUT_INVALID")
    run_id = resume["run_id"]
    private = _run_root(cache_path, run_id) / "resume-private.json"
    value = strict_json(private.read_bytes())
    state = _restore(value, cache_path, clock)
    ordered_answers = [
        {"question_id": item, "answer": answers[item]} for item in expected
    ]
    pending = resume["pending_case_slots"]
    batch_number = len(resume["completed_case_slots"]) // 5 + 1
    first = True
    while pending:
        batch_slots = tuple(pending[:5])
        result = _batch(
            state,
            transport,
            batch_number,
            batch_slots,
            ordered_answers if first else [],
            interaction_state="RESUMED" if first else "INITIAL",
            answers_authoritative=first,
        )
        first = False
        if result[0] != "VALID":
            reason = (
                "QUESTION_LIMIT_EXCEEDED"
                if result[0] == "NEEDS_INPUT"
                else cast(str, result[1])
            )
            return _terminal(
                state,
                reason,
                cast(int, value["excluded"]),
                output_path,
                publisher,
            )
        state.lanes.append(cast(Lane, result[1]))
        pending = pending[5:]
        batch_number += 1
    del questions
    return _terminal(
        state,
        None,
        cast(int, value["excluded"]),
        output_path,
        publisher,
    )


def _batch(
    state: _State,
    transport: RestrictedAgentTransport,
    number: int,
    slots: tuple[str, ...],
    answers: list[Json],
    *,
    interaction_state: str = "INITIAL",
    answers_authoritative: bool = False,
) -> tuple[str, Lane | list[Json] | str]:
    batch_id = f"batch-{number:03d}"
    prior: Json | None = None
    defects: list[Json] = []
    for phase in ("GENERATE", "REPAIR"):
        if state.reserved + state.reservation > state.maximum:
            state.attempts.append(
                _attempt(
                    state,
                    batch_id,
                    phase,
                    slots,
                    "BUDGET_REFUSED",
                    "BUDGET_REFUSED",
                    None,
                )
            )
            return "FAILED", "BUDGET_REFUSED"
        request = AgentBatchRequest(
            state.run_id,
            batch_id,
            phase,
            slots,
            state.catalog,
            answers,
            prior,
            defects,
            _money(state.maximum - state.reserved),
            interaction_state,
            answers_authoritative,
        )
        state.reserved += state.reservation
        state.calls += 1
        attempt_id = _attempt_identity(state, batch_id, phase)
        tools = RestrictedTools(
            state.catalog,
            request.remaining_budget_usd,
            log_path=_run_root(state.cache, state.run_id)
            / "agent"
            / "tool_calls.jsonl",
            attempt_id=attempt_id,
        )
        response = transport.run(request, tools)
        status = _field(response, "status")
        reason = _field(response, "failure_reason_code")
        request_bytes = cast(bytes, _field(response, "request_bytes"))
        response_bytes = cast(bytes, _field(response, "response_bytes"))
        stage_root = _preserve_boundary(
            state, batch_id, phase, attempt_id, request_bytes, response_bytes
        )
        actual_value = _field(response, "actual_cost_usd")
        if actual_value is None:
            state.actual_known = False
        else:
            state.actual += _decimal(actual_value)
        if status == "FAILED":
            attempt_status = (
                "TOOL_FAILED"
                if reason == "TOOL_EXECUTION_FAILED"
                else "PROVIDER_FAILED"
            )
            state.attempts.append(
                _attempt(
                    state,
                    batch_id,
                    phase,
                    slots,
                    attempt_status,
                    cast(str, reason),
                    response,
                )
            )
            return "FAILED", cast(str, reason)
        if status == "NEEDS_INPUT":
            questions = cast(list[Json], _field(response, "questions"))
            state.attempts.append(
                _attempt(
                    state,
                    batch_id,
                    phase,
                    slots,
                    "NEEDS_INPUT",
                    "MATERIAL_INPUT_REQUIRED",
                    response,
                )
            )
            return "NEEDS_INPUT", questions
        if status == "SUBMITTED" and tools.submission is None:
            state.attempts.append(
                _attempt(
                    state,
                    batch_id,
                    phase,
                    slots,
                    "PROVIDER_FAILED",
                    "PROVIDER_INVALID_RESPONSE",
                    response,
                )
            )
            return "FAILED", "PROVIDER_INVALID_RESPONSE"
        submission = cast(Json, _field(response, "submission"))
        normalized, current = _normalize(submission, slots, state.handle_map)
        lane: Lane | None = None
        if not current and normalized is not None:
            try:
                lane = convert_lane(
                    normalized,
                    state.citations,
                    _lineage(state, phase),
                    cast(str, state.evidence["input_manifest_hash"]),
                    cast(str, state.evidence["intelligence_manifest_hash"]),
                    strict_cases=True,
                    expected_case_count=len(slots),
                )
            except Invalid:
                current = [_defect("INTERNAL_INVARIANT_FAILED", "")]
        _preserve_submission(stage_root, phase, submission, normalized, current)
        if lane is not None:
            state.attempts.append(
                _attempt(
                    state,
                    batch_id,
                    phase,
                    slots,
                    "SUCCEEDED",
                    None,
                    response,
                )
            )
            return "VALID", lane
        state.attempts.append(
            _attempt(
                state,
                batch_id,
                phase,
                slots,
                "INVALID",
                "INVALID_CASE_BATCH",
                response,
            )
        )
        if phase == "REPAIR":
            return "FAILED", "INVALID_CASE_BATCH"
        prior, defects = submission, current
        if not answers_authoritative:
            answers = []
    return "FAILED", "INTERNAL_INVARIANT_FAILED"


def _catalog(evidence: Json, citations: list[Json]) -> tuple[Json, dict[str, Json]]:
    citation_map = {
        (item["trace_id"], item["event_sequences"][0]): item for item in citations
    }
    traces: list[Json] = []
    handles: dict[str, Json] = {}
    evidence_index = 1
    for trace_index, trace in enumerate(evidence["selected_traces"], start=1):
        events = []
        for event in trace["events"]:
            handle = f"E{evidence_index:06d}"
            evidence_index += 1
            projected = {"evidence_handle": handle, **event}
            events.append(projected)
            handles[handle] = citation_map[(trace["trace_id"], event["sequence"])]
        traces.append(
            {
                "trace_handle": f"T{trace_index:03d}",
                "structural_cluster_id": trace["structural_cluster_id"],
                "events": events,
            }
        )
    return (
        {
            "artifact_kind": "case_factory_evidence_catalog",
            "schema_version": 1,
            "traces": traces,
            "gaps": evidence["gaps"],
        },
        handles,
    )


def _normalize(
    submission: Json, slots: tuple[str, ...], handles: dict[str, Json]
) -> tuple[Json | None, list[Json]]:
    defects: list[Json] = []
    cases = submission.get("cases")
    if not isinstance(cases, list) or [item.get("case_key") for item in cases] != list(
        slots
    ):
        defects.append(_defect("DUPLICATE_LOCAL_SLOT", "/cases"))
    normalized = json.loads(canonical(submission))
    for group in ("personas", "intents", "turn_policies", "cases"):
        values = normalized.get(group)
        if not isinstance(values, list):
            defects.append(_defect("BROKEN_LOCAL_REFERENCE", f"/{group}"))
            continue
        for index, value in enumerate(values):
            defects.extend(_generated_claim_key_defects(value, f"/{group}/{index}"))
            if group == "cases":
                scenario = value.get("scenario")
                stressors = (
                    scenario.get("stressor_codes")
                    if isinstance(scenario, dict)
                    else None
                )
                if isinstance(stressors, list) and all(
                    isinstance(item, str) for item in stressors
                ):
                    valid_stressors = (
                        len(stressors) <= 20
                        and len(stressors) == len(set(stressors))
                        and stressors == sorted(stressors)
                        and all(SAFE_CODE.fullmatch(item) for item in stressors)
                    )
                    if not valid_stressors:
                        defects.append(
                            _defect(
                                "INVALID_CASE",
                                f"/cases/{index}/scenario/stressor_codes",
                                sorted(stressors),
                            )
                        )
            claims = value.get("grounding_claims")
            if not isinstance(claims, list):
                defects.append(
                    _defect(
                        "BROKEN_LOCAL_REFERENCE", f"/{group}/{index}/grounding_claims"
                    )
                )
                continue
            referenced_claims = _local_claim_keys(value)
            for claim_index, claim in enumerate(claims):
                claim_key = claim.get("claim_key")
                if isinstance(claim_key, str) and claim_key not in referenced_claims:
                    defects.append(
                        _defect(
                            "BROKEN_LOCAL_REFERENCE",
                            f"/{group}/{index}/grounding_claims/{claim_index}",
                            [claim_key],
                        )
                    )
                selected = claim.get("evidence_handles")
                path = (
                    f"/{group}/{index}/grounding_claims/{claim_index}/evidence_handles"
                )
                if not isinstance(selected, list) or not selected:
                    defects.append(_defect("UNKNOWN_EVIDENCE_HANDLE", path))
                    continue
                unknown = sorted({item for item in selected if item not in handles})
                if unknown:
                    defects.append(_defect("UNKNOWN_EVIDENCE_HANDLE", path, unknown))
                    continue
                citations = sorted({handles[item]["citation_id"] for item in selected})
                traces = {handles[item]["trace_id"] for item in selected}
                kind = claim.pop("support_kind", None)
                claim.pop("evidence_handles", None)
                claim["support_state"] = (
                    "SINGLE_OBSERVATION"
                    if len(traces) == 1
                    else "CONFLICTED"
                    if kind == "CONFLICTING"
                    else "SUPPORTED"
                )
                claim["citation_ids"] = citations
    return (None if defects else cast(Json, normalized)), sorted(
        defects, key=lambda item: (item["code"], item["path"], item["related_ids"])
    )


def _local_claim_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = value.get("claim_keys")
        result = (
            {item for item in keys if isinstance(item, str)}
            if isinstance(keys, list)
            else set()
        )
        for name, item in value.items():
            if name != "grounding_claims":
                result.update(_local_claim_keys(item))
        return result
    if isinstance(value, list):
        return set(chain.from_iterable(_local_claim_keys(item) for item in value))
    return set()


def _generated_claim_key_defects(value: Any, path: str) -> list[Json]:
    defects: list[Json] = []
    if isinstance(value, dict):
        keys = value.get("claim_keys")
        if (
            {"basis", "claim_keys", "text"} <= value.keys()
            and value.get("basis") == "GENERATED_VARIATION"
            and isinstance(keys, list)
            and keys
            and all(isinstance(item, str) for item in keys)
        ):
            defects.append(
                _defect(
                    "BROKEN_LOCAL_REFERENCE",
                    f"{path}/claim_keys",
                    sorted(keys),
                )
            )
        for name, item in value.items():
            token = str(name).replace("~", "~0").replace("/", "~1")
            defects.extend(_generated_claim_key_defects(item, f"{path}/{token}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            defects.extend(_generated_claim_key_defects(item, f"{path}/{index}"))
    return defects


def _defect(code: str, path: str, related: list[str] | None = None) -> Json:
    return {
        "code": code,
        "path": path,
        "message": code.replace("_", " "),
        "related_ids": related or [],
        "repairable": code != "INTERNAL_INVARIANT_FAILED",
    }


def _attempt(
    state: _State,
    batch_id: str,
    phase: str,
    slots: tuple[str, ...],
    status: str,
    reason: str | None,
    response: Any | None,
) -> Json:
    return {
        "artifact_kind": "case_factory_agent_attempt",
        "schema_version": 1,
        "attempt_id": _attempt_identity(state, batch_id, phase),
        "batch_id": batch_id,
        "phase": phase,
        "case_slots": [int(item.removeprefix("case_")) for item in slots],
        "status": status,
        "reason_code": reason,
        "request_hash": (
            byte_hash("restricted-provider-request", _field(response, "request_bytes"))
            if response is not None
            else None
        ),
        "response_hash": (
            byte_hash(
                "restricted-provider-response", _field(response, "response_bytes")
            )
            if response is not None
            else None
        ),
        "input_tokens": _field(response, "input_tokens")
        if response is not None
        else None,
        "output_tokens": _field(response, "output_tokens")
        if response is not None
        else None,
        "actual_cost_usd": (
            _field(response, "actual_cost_usd") if response is not None else None
        ),
        "reserved_cost_usd": _money(state.reservation),
        "latency_ms": _field(response, "latency_ms") if response is not None else None,
    }


def _attempt_identity(state: _State, batch_id: str, phase: str) -> str:
    return domain_hash(
        "restricted-agent-attempt",
        {
            "run_id": state.run_id,
            "batch_id": batch_id,
            "phase": phase,
            "attempt_index": len(state.attempts),
        },
    )


def _preserve_boundary(
    state: _State,
    batch_id: str,
    phase: str,
    attempt_id: str,
    request: bytes,
    response: bytes,
) -> Path:
    legacy = (
        _run_root(state.cache, state.run_id) / "provider" / batch_id / phase.casefold()
    )
    root = (
        legacy
        if not legacy.exists()
        else legacy.parent / f"{phase.casefold()}-{attempt_id.removeprefix('sha256:')}"
    )
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if contains_secret(request, state.sentinels) or contains_secret(
        response, state.sentinels
    ):
        raise Invalid
    _private_write(root / "request.json", request)
    _private_write(root / "response.json", response)
    return root


def _preserve_submission(
    root: Path,
    phase: str,
    submission: Json,
    normalized: Json | None,
    defects: list[Json],
) -> None:
    _private_write(root / "parsed.json", canonical(submission, lf=True))
    if normalized is not None:
        _private_write(root / "normalized.json", canonical(normalized, lf=True))
    _private_write(
        root / "defects.json",
        canonical(
            {
                "artifact_kind": "case_factory_stage_defects",
                "schema_version": 1,
                "stage": phase,
                "defects": defects,
            },
            lf=True,
        ),
    )


def _terminal(
    state: _State,
    reason: str | None,
    excluded: int,
    output: Path,
    publisher: ArtifactPublisher | None,
) -> RestrictedResult:
    lane = _merge(state.lanes)
    duplicates = apply_diversity(lane, state.citations) if lane.cases else []
    distinct = len(lane.cases) - sum(
        len(item["member_case_ids"]) - 1 for item in duplicates
    )
    if reason is None:
        outcome = "COMPLETED"
    else:
        outcome = "COMPLETED_WITH_GAPS" if lane.cases else "REJECTED"
    artifacts = _portable(state, lane, duplicates, distinct, excluded, outcome, reason)
    _publish(output, artifacts, publisher)
    return RestrictedResult(
        outcome,
        reason,
        output / "manifest.json",
        state.requested,
        len(lane.cases),
        distinct,
        state.calls,
        _money(state.reserved),
    )


def _portable(
    state: _State,
    lane: Lane,
    duplicates: list[Json],
    distinct: int,
    excluded: int,
    outcome: str,
    reason: str | None,
) -> dict[str, bytes]:
    records = {
        "control_personas.jsonl": [],
        "control_intents.jsonl": [],
        "control_turn_policies.jsonl": [],
        "control_case_candidates.jsonl": [],
        "personas.jsonl": lane.personas,
        "intents.jsonl": lane.intents,
        "turn_policies.jsonl": lane.policies,
        "case_candidates.jsonl": lane.cases,
    }
    artifacts = {
        name: b"".join(canonical(item, lf=True) for item in values)
        for name, values in records.items()
    }
    artifacts["generation_attempts.jsonl"] = b"".join(
        canonical(item, lf=True) for item in state.attempts
    )
    artifacts["evidence_index.json"] = canonical(
        {
            "artifact_kind": "case_factory_evidence_index",
            "schema_version": 1,
            "input_manifest_hash": state.evidence["input_manifest_hash"],
            "intelligence_manifest_hash": state.evidence["intelligence_manifest_hash"],
            "selection_algorithm": state.evidence["selection_algorithm"],
            "selected_trace_count": len(state.evidence["selected_traces"]),
            "excluded_trace_count": excluded,
            "projected_byte_count": len(canonical(state.evidence)),
            "citations": state.citations,
            "gaps": state.evidence["gaps"],
        },
        lf=True,
    )
    evaluation = {
        "artifact_kind": "case_factory_evaluation",
        "schema_version": 1,
        "comparison_available": False,
        "requested_case_count": state.requested,
        "valid_case_count": len(lane.cases),
        "distinct_case_count": distinct,
        "duplicate_clusters": duplicates,
        "attempt_count": len(state.attempts),
        "provider_call_count": state.calls,
        "reserved_cost_usd": _money(state.reserved),
        "actual_cost_usd": _money(state.actual) if state.actual_known else None,
        "gap_codes": [reason] if reason else [],
        "machine_status": "PASSED"
        if len(lane.cases) >= min(7, state.requested)
        else "FAILED",
    }
    artifacts["case_factory_eval.json"] = canonical(evaluation, lf=True)
    artifacts["human_review_template.json"] = canonical(
        {
            "artifact_kind": "case_factory_human_review",
            "schema_version": 1,
            "comparison_available": False,
            "review_items": [
                {"case_id": item["case_id"], "owner_ruling": None}
                for item in lane.cases
            ],
            "review_state": "PENDING",
        },
        lf=True,
    )
    manifest = {
        "artifact_kind": "case_factory_manifest",
        "schema_version": 1,
        "input_manifest_hash": state.evidence["input_manifest_hash"],
        "intelligence_manifest_hash": state.evidence["intelligence_manifest_hash"],
        "privacy_class": "SYNTHETIC",
        "producing_component": "triana-labs-case-factory",
        "producing_component_version": __version__,
        "provider_kind": PROVIDER,
        "deployment": MODEL,
        "model_name": MODEL,
        "model_version": MODEL_VERSION,
        "outcome": outcome,
        "reason_code": reason,
        "attempt_count": len(state.attempts),
        "requested_case_count": state.requested,
        "valid_case_count": len(lane.cases),
        "distinct_case_count": distinct,
        "reserved_cost_usd": _money(state.reserved),
        "actual_cost_usd": _money(state.actual) if state.actual_known else None,
        "human_review_state": "PENDING",
        "artifacts": {
            name: artifact_hash(payload) for name, payload in artifacts.items()
        },
    }
    artifacts["manifest.json"] = canonical(manifest, lf=True)
    return artifacts


def _pause(
    state: _State,
    questions: list[Json],
    completed: list[str],
    pending: list[str],
    excluded: int,
    output: Path,
    publisher: ArtifactPublisher | None,
) -> RestrictedResult:
    if not 1 <= len(questions) <= 3:
        return _terminal(state, "QUESTION_LIMIT_EXCEEDED", excluded, output, publisher)
    question_ids = [item["question_id"] for item in questions]
    resume = {
        "artifact_kind": "case_factory_resume_state",
        "schema_version": 1,
        "run_id": state.run_id,
        "input_manifest_hash": state.evidence["input_manifest_hash"],
        "intelligence_manifest_hash": state.evidence["intelligence_manifest_hash"],
        "config_hash": state.config_hash,
        "requested_case_count": state.requested,
        "completed_case_slots": completed,
        "pending_case_slots": pending,
        "attempt_ids": [item["attempt_id"] for item in state.attempts],
        "question_ids": question_ids,
        "reserved_cost_usd": _money(state.reserved),
        "actual_cost_usd": _money(state.actual) if state.actual_known else None,
    }
    private = _snapshot(state, excluded)
    _private_write(
        _run_root(state.cache, state.run_id) / "resume-private.json",
        canonical(private, lf=True),
    )
    artifacts = {
        "generation_attempts.jsonl": b"".join(
            canonical(item, lf=True) for item in state.attempts
        ),
        "evidence_index.json": canonical(
            {
                "artifact_kind": "case_factory_evidence_index",
                "schema_version": 1,
                "input_manifest_hash": state.evidence["input_manifest_hash"],
                "intelligence_manifest_hash": state.evidence[
                    "intelligence_manifest_hash"
                ],
            },
            lf=True,
        ),
        "questions.json": canonical(
            {
                "artifact_kind": "case_factory_questions",
                "schema_version": 1,
                "run_id": state.run_id,
                "questions": questions,
            },
            lf=True,
        ),
        "resume_state.json": canonical(resume, lf=True),
    }
    artifacts["manifest.json"] = canonical(
        {
            "artifact_kind": "case_factory_pause_manifest",
            "schema_version": 1,
            "run_id": state.run_id,
            "outcome": "NEEDS_INPUT",
            "reason_code": "MATERIAL_INPUT_REQUIRED",
            "artifacts": {
                name: artifact_hash(payload) for name, payload in artifacts.items()
            },
        },
        lf=True,
    )
    _publish(output, artifacts, publisher)
    return RestrictedResult(
        "NEEDS_INPUT",
        "MATERIAL_INPUT_REQUIRED",
        output / "manifest.json",
        state.requested,
        sum(len(item.cases) for item in state.lanes),
        0,
        state.calls,
        _money(state.reserved),
    )


def _snapshot(state: _State, excluded: int) -> Json:
    return {
        "run_id": state.run_id,
        "evidence": state.evidence,
        "citations": state.citations,
        "catalog": state.catalog,
        "handle_map": state.handle_map,
        "requested": state.requested,
        "maximum": _money(state.maximum),
        "reservation": _money(state.reservation),
        "reserved": _money(state.reserved),
        "actual": _money(state.actual),
        "actual_known": state.actual_known,
        "attempts": state.attempts,
        "lanes": [_lane_value(item) for item in state.lanes],
        "calls": state.calls,
        "config_hash": state.config_hash,
        "excluded": excluded,
    }


def _restore(value: Json, cache: Path, clock: Clock) -> _State:
    return _State(
        value["run_id"],
        value["evidence"],
        value["citations"],
        value["catalog"],
        value["handle_map"],
        value["requested"],
        Decimal(value["maximum"]),
        Decimal(value["reservation"]),
        Decimal(value["reserved"]),
        Decimal(value["actual"]),
        value["actual_known"],
        value["attempts"],
        [_lane_from_value(item) for item in value["lanes"]],
        value["calls"],
        cache,
        [],
        value["config_hash"],
        clock,
    )


def _lane_value(lane: Lane) -> Json:
    return {
        "personas": lane.personas,
        "intents": lane.intents,
        "policies": lane.policies,
        "cases": lane.cases,
        "positions": lane.positions,
        "invalid": lane.invalid,
        "valid_refs": lane.valid_refs,
        "invalid_refs": lane.invalid_refs,
    }


def _lane_from_value(value: Json) -> Lane:
    return Lane(
        value["personas"],
        value["intents"],
        value["policies"],
        value["cases"],
        value["positions"],
        value["invalid"],
        value["valid_refs"],
        value["invalid_refs"],
    )


def _merge(lanes: list[Lane]) -> Lane:
    positions: dict[str, int] = {}
    cases = list(chain.from_iterable(item.cases for item in lanes))
    for index, case in enumerate(cases):
        positions[case["case_id"]] = index
    return Lane(
        list(chain.from_iterable(item.personas for item in lanes)),
        list(chain.from_iterable(item.intents for item in lanes)),
        list(chain.from_iterable(item.policies for item in lanes)),
        cases,
        positions,
        sum(item.invalid for item in lanes),
        sum(item.valid_refs for item in lanes),
        sum(item.invalid_refs for item in lanes),
    )


def _restricted_budget(config: Any) -> tuple[Decimal, Decimal]:
    try:
        maximum = Decimal(config["budget"]["max_usd"])
        reservation = Decimal(config["budget"]["reservation_usd_per_agent_call"])
    except (KeyError, TypeError, InvalidOperation) as error:
        raise Invalid from error
    if maximum > Decimal(10) or maximum < 0 or reservation < 0:
        raise Invalid
    return maximum, reservation


def _sentinels(config: Json, environ: Mapping[str, str]) -> list[bytes]:
    names = config["provider"]["secret_sentinel_envs"]
    values = []
    for name in names:
        if name in environ:
            values.append(environ[name].encode())
    key_name = config["provider"]["api_key_env"]
    if key_name in environ:
        values.append(environ[key_name].encode())
    return values


def _lineage(state: _State, phase: str) -> Json:
    return {
        "provider_kind": PROVIDER,
        "deployment": MODEL,
        "model_name": MODEL,
        "model_version": MODEL_VERSION,
        "stage": phase,
        "run_id": state.run_id,
        "attempt_ids": [item["attempt_id"] for item in state.attempts],
    }


def _run_root(cache: Path, run_id: str) -> Path:
    root = cache / "runs" / run_id.removeprefix("sha256:")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    return root


def _private_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _private_append(path: Path, payload: bytes) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(descriptor, "ab") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _publish(
    output: Path, artifacts: dict[str, bytes], publisher: ArtifactPublisher | None
) -> None:
    try:
        (publisher or AtomicPublisher()).publish(output, artifacts)
    except PublicationFailure as error:
        raise Invalid from error


def _output(path: Path) -> None:
    if os.path.lexists(path) or path.parent.is_symlink() or not path.parent.is_dir():
        raise Invalid


def _cache(path: Path, output: Path) -> None:
    cache = path.resolve(strict=False)
    target = output.resolve(strict=False)
    if cache == target or cache in target.parents or target in cache.parents:
        raise Invalid
    if not path.exists():
        path.mkdir(mode=0o700)
    os.chmod(path, 0o700)


def _money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.000001")), "f")


def _decimal(value: Any) -> Decimal:
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError) as error:
        raise Invalid from error
    if result < 0:
        raise Invalid
    return result


def _field(value: Any, name: str) -> Any:
    return value[name] if isinstance(value, dict) else getattr(value, name)


class FoundryGLMRestrictedTransport:
    """Pinned Foundry model executed only through a restricted LangChain agent."""

    def __init__(
        self, endpoint: str, api_key: str, *, timeout_seconds: int = 180
    ) -> None:
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, int)
            or not 1 <= timeout_seconds <= 600
        ):
            raise Invalid("PROVIDER_TIMEOUT_INVALID")
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def run(self, request: AgentBatchRequest, tools: RestrictedTools) -> Any:
        import httpx
        import openai
        from langchain_core.exceptions import LangChainException
        from langgraph.errors import GraphRecursionError

        capture = _HTTPExchangeCapture()
        model, http_client = _foundry_model(
            self.endpoint, self.api_key, self.timeout_seconds, capture
        )
        agent_tools = _agent_tools(request, tools)
        if tuple(item.name for item in agent_tools) != TOOLS:
            raise Invalid
        resumed = request.interaction_state == "RESUMED"
        agent = _restricted_agent(model, agent_tools, resumed=resumed)
        prompt = canonical(request.__dict__).decode()
        started = time.monotonic_ns()
        try:
            state = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
        except RestrictedToolFailure:
            return _live_response(
                "FAILED",
                capture.requests_bytes(prompt),
                capture.responses_bytes(),
                _latency(started),
                "TOOL_EXECUTION_FAILED",
            )
        except (
            openai.APIError,
            httpx.HTTPError,
            LangChainException,
            GraphRecursionError,
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            return _provider_failure(error, capture, prompt, started)
        finally:
            http_client.close()
        latency = _latency(started)
        request_bytes = capture.requests_bytes(prompt)
        response_bytes = capture.responses_bytes()
        input_tokens, output_tokens = _usage(state)
        common = {
            "request_bytes": request_bytes,
            "response_bytes": response_bytes,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "actual_cost_usd": None,
            "latency_ms": latency,
        }
        if tools.submission is not None:
            return {
                "status": "SUBMITTED",
                "submission": tools.submission,
                "questions": [],
                "failure_reason_code": None,
                **common,
            }
        try:
            outcome = cast(Json, state["structured_response"])
            status = cast(str, outcome["status"])
            questions = cast(list[Json], outcome["questions"])
            reason = cast(str | None, outcome["failure_reason_code"])
        except (KeyError, TypeError, ValueError):
            return _live_response(
                "FAILED",
                request_bytes,
                response_bytes,
                latency,
                "PROVIDER_INVALID_RESPONSE",
            )
        if status == "NEEDS_INPUT":
            if (
                tools.submission is None
                and _valid_questions(questions)
                and reason in {None, "MATERIAL_INPUT_REQUIRED"}
            ):
                return {
                    "status": "NEEDS_INPUT",
                    "submission": None,
                    "questions": questions,
                    "failure_reason_code": None,
                    **common,
                }
        elif (
            status == "FAILED"
            and tools.submission is None
            and not questions
            and reason in _MODEL_FAILURE_REASONS
        ):
            return {
                "status": "FAILED",
                "submission": None,
                "questions": [],
                "failure_reason_code": reason,
                **common,
            }
        return _live_response(
            "FAILED",
            request_bytes,
            response_bytes,
            latency,
            "PROVIDER_INVALID_RESPONSE",
        )


_MODEL_FAILURE_REASONS = frozenset({"MATERIAL_INPUT_REQUIRED"})


class _HTTPExchangeCapture:
    def __init__(self) -> None:
        self.requests: list[bytes] = []
        self.responses: list[bytes] = []

    def on_request(self, request: Any) -> None:
        self.requests.append(bytes(request.content))

    def on_response(self, response: Any) -> None:
        response.read()
        self.responses.append(bytes(response.content))

    def requests_bytes(self, prompt: str) -> bytes:
        if self.requests:
            return b"\n".join(self.requests)
        return canonical({"messages": [{"role": "user", "content": prompt}]})

    def responses_bytes(self) -> bytes:
        return b"\n".join(self.responses)


def _foundry_model(
    endpoint: str,
    api_key: str,
    timeout_seconds: int,
    capture: _HTTPExchangeCapture,
) -> tuple[Any, Any]:
    import httpx
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr

    class AllowlistedFoundryModel(ChatOpenAI):
        def bind_tools(self, values: Any, **kwargs: Any) -> Any:  # type: ignore[override]
            names = tuple(_model_tool_name(value) for value in values)
            if names != TOOLS:
                raise Invalid("RESTRICTED_TOOL_SURFACE_INVALID")
            return super().bind_tools(values, **kwargs)

    client = httpx.Client(
        event_hooks={
            "request": [capture.on_request],
            "response": [capture.on_response],
        }
    )
    return (
        AllowlistedFoundryModel(
            model=MODEL,
            api_key=SecretStr(api_key),
            base_url=endpoint.rstrip("/") + "/models",
            default_headers={"api-key": api_key},
            default_query={"api-version": "2024-05-01-preview"},
            http_client=client,
            max_retries=0,
            temperature=0,
            timeout=timeout_seconds,
        ),
        client,
    )


def _model_tool_name(value: Any) -> str:
    if hasattr(value, "name"):
        return cast(str, value.name)
    return cast(str, value["function"]["name"])


def _restricted_agent(
    model: Any, agent_tools: list[Any], *, resumed: bool = False
) -> Any:
    from langchain.agents import create_agent
    from langchain.agents.middleware import wrap_model_call
    from langchain.agents.structured_output import ProviderStrategy
    from langchain_core.messages import AIMessage, ToolMessage
    from langgraph.errors import GraphRecursionError

    @wrap_model_call
    def require_tool(request: Any, handler: Any) -> Any:
        if sum(isinstance(message, AIMessage) for message in request.messages) >= 3:
            raise GraphRecursionError("Restricted agent exceeded three model calls")
        trace_read = any(
            isinstance(message, ToolMessage)
            and message.name == "get_trace_packet"
            and message.status == "success"
            for message in request.messages
        )
        successful_searches = sum(
            isinstance(message, ToolMessage)
            and message.name == "search_evidence"
            and message.status == "success"
            for message in request.messages
        )
        tool_choice = (
            "submit_case_batch"
            if trace_read
            else "get_trace_packet"
            if successful_searches >= 2
            else "required"
        )
        return handler(request.override(tool_choice=tool_choice))

    instruction = (
        "This interaction is RESUMED. The supplied answers are authoritative and "
        "resolve every prior question. NEEDS_INPUT is unavailable. You must call "
        "submit_case_batch exactly once; text or a SUBMITTED terminal response "
        "without that tool cannot publish a case."
        if resumed
        else "Ask NEEDS_INPUT only when material target or construction input is missing."
    )
    response_format: dict[str, Any] = {}
    if not resumed:
        response_format["response_format"] = ProviderStrategy(
            _terminal_schema(resumed=False), strict=True
        )
    return create_agent(
        model=model,
        tools=agent_tools,
        middleware=[require_tool] if resumed else [],
        system_prompt=(
            "Act as a grounding researcher, then a case architect. Use only the "
            "four supplied tools. Inspect evidence before drafting. Every declared "
            "grounding claim in each object must be referenced by at least one local "
            "claim_keys; omit unused claims. GENERATED_VARIATION must have empty "
            "claim_keys; OBSERVED text must use resolving local claim_keys. "
            "stressor_codes must match ^[A-Z][A-Z0-9_]{0,63}$, be unique, and be "
            "lexicographically sorted. Make at most two search calls; then read a "
            "returned trace. Submit exactly "
            "once through submit_case_batch, using only supplied evidence handles "
            f"and every supplied case slot. {instruction} After a successful "
            "submission, stop. "
            "Never invent IDs, retry, select another model, or claim acceptance."
        ),
        **response_format,
    )


def _agent_tools(request: AgentBatchRequest, tools: RestrictedTools) -> list[Any]:
    from langchain_core.tools import StructuredTool

    trace_handles = [
        cast(str, trace["trace_handle"]) for trace in request.evidence_catalog["traces"]
    ]
    return [
        StructuredTool.from_function(
            tools.search_evidence,
            name="search_evidence",
            description="Find bounded evidence handles matching a semantic query.",
            args_schema=_object_schema(
                {"query": {"type": "string", "minLength": 1, "maxLength": 512}}
            ),
        ),
        StructuredTool.from_function(
            tools.get_trace_packet,
            name="get_trace_packet",
            description="Read one allowlisted synthetic trace packet by handle.",
            args_schema=_object_schema(
                {"trace_handle": {"type": "string", "enum": trace_handles}}
            ),
        ),
        StructuredTool.from_function(
            tools.inspect_budget,
            name="inspect_budget",
            description="Read the remaining reserved run budget.",
            args_schema=_object_schema({}),
        ),
        StructuredTool.from_function(
            tools.submit_case_batch,
            name="submit_case_batch",
            description="Submit one complete case batch for deterministic validation.",
            args_schema=_submission_tool_schema(request),
            return_direct=True,
        ),
    ]


def _submission_tool_schema(request: AgentBatchRequest) -> Json:
    submission = _submission_schema(request)
    definitions = submission.pop("$defs")
    outer = _object_schema({"submission": submission})
    outer["$defs"] = definitions
    return outer


def _submission_schema(request: AgentBatchRequest) -> Json:
    schema_path = Path(__file__).parent / "schemas" / "proposal.schema.json"
    schema = cast(Json, json.loads(schema_path.read_bytes()))
    claims = schema["$defs"]["claimDraft"]
    handles = [
        event["evidence_handle"]
        for trace in request.evidence_catalog["traces"]
        for event in trace["events"]
    ]
    claims["properties"] = {
        "claim_key": {"type": "string", "pattern": "^claim_[1-9][0-9]*$"},
        "claim": {"type": "string", "minLength": 1},
        "support_kind": {
            "type": "string",
            "enum": ["CORROBORATING", "CONFLICTING"],
        },
        "evidence_handles": {
            "type": "array",
            "items": {"type": "string", "enum": handles},
            "minItems": 1,
            "uniqueItems": True,
        },
    }
    claims["required"] = [
        "claim_key",
        "claim",
        "support_kind",
        "evidence_handles",
    ]
    schema["$defs"]["caseDraft"]["properties"]["case_key"] = {
        "type": "string",
        "enum": list(request.case_slots),
    }
    stressors = schema["$defs"]["scenarioDraft"]["properties"]["stressor_codes"]
    stressors["items"] = {"type": "string", "pattern": SAFE_CODE.pattern}
    stressors["maxItems"] = 20
    stressors["uniqueItems"] = True
    count = len(request.case_slots)
    for group in ("personas", "intents", "turn_policies", "cases"):
        schema["properties"][group]["minItems"] = count
        schema["properties"][group]["maxItems"] = count
    return schema


def _terminal_schema(*, resumed: bool = False) -> Json:
    statuses = (
        ["SUBMITTED", "FAILED"] if resumed else ["SUBMITTED", "NEEDS_INPUT", "FAILED"]
    )
    return {
        "title": "case_factory_agent_outcome",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "status": {
                "type": "string",
                "enum": statuses,
            },
            "questions": {
                "type": "array",
                **({"minItems": 1} if not resumed else {}),
                "maxItems": 3,
                "items": _object_schema(
                    {
                        "question_id": {
                            "type": "string",
                            "enum": ["Q001", "Q002", "Q003"],
                        },
                        "question": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 4096,
                        },
                        "material_scope": {
                            "type": "string",
                            "enum": ["TARGET_RELEVANCE", "CASE_CONSTRUCTION"],
                        },
                    }
                ),
            },
            "failure_reason_code": {
                "anyOf": [
                    {"type": "string", "enum": sorted(_MODEL_FAILURE_REASONS)},
                    {"type": "null"},
                ]
            },
        },
        "required": ["status", "questions", "failure_reason_code"],
    }


def _object_schema(properties: Json) -> Json:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
    }


def _valid_questions(questions: list[Json]) -> bool:
    if not 1 <= len(questions) <= 3:
        return False
    expected = [f"Q{index:03d}" for index in range(1, len(questions) + 1)]
    return [item.get("question_id") for item in questions] == expected and all(
        bounded_text(item.get("question"), 4096)
        and item.get("material_scope") in {"TARGET_RELEVANCE", "CASE_CONSTRUCTION"}
        and set(item) == {"question_id", "question", "material_scope"}
        for item in questions
    )


def _usage(state: Any) -> tuple[int | None, int | None]:
    input_tokens = 0
    output_tokens = 0
    observed = False
    for message in state.get("messages", []):
        usage = getattr(message, "usage_metadata", None)
        if usage:
            input_tokens += int(usage.get("input_tokens", 0))
            output_tokens += int(usage.get("output_tokens", 0))
            observed = True
    return (input_tokens, output_tokens) if observed else (None, None)


def _latency(started: int) -> int:
    return (time.monotonic_ns() - started) // 1_000_000


def _provider_failure(
    error: Exception,
    capture: _HTTPExchangeCapture,
    prompt: str,
    started: int,
) -> Json:
    import httpx
    import openai

    if isinstance(error, (openai.APIConnectionError, httpx.TransportError)):
        reason = "PROVIDER_TRANSPORT_FAILED"
    elif isinstance(error, openai.APIStatusError):
        reason = "PROVIDER_REFUSED"
    else:
        reason = "PROVIDER_INVALID_RESPONSE"
    return _live_response(
        "FAILED",
        capture.requests_bytes(prompt),
        capture.responses_bytes(),
        _latency(started),
        reason,
    )


def _live_response(
    status: str, request: bytes, response: bytes, latency: int, reason: str
) -> Json:
    return {
        "status": status,
        "submission": None,
        "questions": [],
        "failure_reason_code": reason,
        "request_bytes": request,
        "response_bytes": response,
        "input_tokens": None,
        "output_tokens": None,
        "actual_cost_usd": None,
        "latency_ms": latency,
    }
