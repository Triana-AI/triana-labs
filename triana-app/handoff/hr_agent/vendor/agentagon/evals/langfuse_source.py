"""Langfuse span-tree trace source.

The HR AI adapter (``experiments/hr_ai_seed/adapter_v1.py``) reconstructs
bundles from a hand-rolled LangGraph stream export that only recorded
AIMessages — tool status/error, tool arguments, tool results, per-turn
tokens, and stop reason were never captured, so
``agentagon.behavioral_evals.event_signals.event_availability_profile`` and
``BehavioralEvalsInput.has_enriched_traces()`` correctly report those fields
as absent and TOOL_CALL_RELIABILITY / FAULT_TOLERANCE / PERFORMANCE_UNDER_LOAD
come back as coverage gaps.

Langfuse already captures all of this on the span tree it stores for any
traced run (standard OTEL GenAI conventions): each observation carries
``type`` (GENERATION | TOOL | SPAN | EVENT), ``level``/``statusMessage`` for
tool errors, ``input``/``output`` for arguments and results, ``usage`` for
per-call token counts, and timing for latency and ordering. This module maps
that span tree onto ``NormalizedTraceBundle`` so those fields survive.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from agentagon.core.types.json import JsonObject
from agentagon.evals.models import ResetPolicy
from agentagon.evals.trace_bundle import NormalizedTraceBundle, parse_trace_bundle

ADAPTER_VERSION = "langfuse-span-tree-v1"

# Observation.type -> NormalizedEvent kind. SPAN/CHAIN cover LangGraph
# node/workflow spans (LangChain instrumentation emits both names depending on
# the wrapped construct); EVENT covers point-in-time markers with no duration.
_OBSERVATION_KIND = {
    "GENERATION": "AGENT",
    "TOOL": "TOOL",
    "SPAN": "WORKFLOW",
    "CHAIN": "WORKFLOW",
    "EVENT": "SYSTEM",
}

# Candidate keys for the model's stop/finish reason, checked in order. Langfuse
# does not standardize this into a top-level field; providers surface it inside
# metadata or modelParameters under different names.
_STOP_REASON_KEYS = ("finishReason", "finish_reason", "stopReason", "stop_reason")

# Finish-reason values that mean the model's response was cut off rather than
# ending naturally.
_TRUNCATION_REASONS = {"length", "max_tokens", "max_output_tokens"}


class LangfuseSourceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class LangfuseCredentials:
    base_url: str
    public_key: str
    secret_key: str


def load_env_credentials(dotenv_path: Path) -> LangfuseCredentials:
    """Read LANGFUSE_BASE_URL / LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY from
    ``dotenv_path`` at call time. Never hardcode or log these values."""
    values: dict[str, str] = {}
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        if key.startswith("LANGFUSE_"):
            values[key] = value.strip().strip('"').strip("'")
    missing = [
        key
        for key in ("LANGFUSE_BASE_URL", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")
        if not values.get(key)
    ]
    if missing:
        raise LangfuseSourceError(f"{dotenv_path}: missing {', '.join(missing)}")
    return LangfuseCredentials(
        base_url=values["LANGFUSE_BASE_URL"],
        public_key=values["LANGFUSE_PUBLIC_KEY"],
        secret_key=values["LANGFUSE_SECRET_KEY"],
    )


def fetch_trace(trace_id: str, creds: LangfuseCredentials) -> JsonObject:
    """Fetch one full trace (with its ``observations``) from the live API."""
    with httpx.Client(
        base_url=creds.base_url,
        auth=(creds.public_key, creds.secret_key),
        timeout=30.0,
    ) as client:
        response = client.get(f"/api/public/traces/{trace_id}")
        response.raise_for_status()
        return response.json()


def _observation_start(observation: JsonObject) -> str:
    start = observation.get("startTime")
    return start if isinstance(start, str) else ""


def _extract_stop_reason(observation: JsonObject) -> str | None:
    metadata = observation.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    model_params = observation.get("modelParameters")
    model_params = model_params if isinstance(model_params, dict) else {}
    for source in (observation, metadata, model_params):
        for key in _STOP_REASON_KEYS:
            value = source.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def _business_error(output: Any) -> str | None:
    """The Langfuse ``level`` field only flags harness-level exceptions. Real
    tool failures in this corpus (a rejected write, a 404 profile lookup) come
    back as a normal DEFAULT-level observation whose JSON output body carries
    ``success: false`` or an ``error`` key — inspect the body too."""
    if not isinstance(output, dict):
        return None
    if output.get("success") is False:
        return str(output.get("error") or "tool reported success=false")
    error = output.get("error")
    if isinstance(error, str) and error:
        return error
    return None


def _tool_event(observation: JsonObject) -> JsonObject:
    output = observation.get("output")
    business_error = _business_error(output)
    is_error = str(observation.get("level") or "").upper() == "ERROR" or business_error is not None
    return {
        "arguments": observation.get("input"),
        "result": output,
        "result_available": output is not None,
        "status": "error" if is_error else "ok",
        "error": (observation.get("statusMessage") or business_error) if is_error else None,
    }


def _generation_event(observation: JsonObject) -> JsonObject:
    usage = observation.get("usage")
    tokens = usage if isinstance(usage, dict) else {}
    stop_reason = _extract_stop_reason(observation)
    return {
        "tokens": tokens,
        "model": observation.get("model"),
        "stop_reason": stop_reason,
        "truncated": stop_reason in _TRUNCATION_REASONS,
    }


def _observation_to_event(observation: JsonObject, sequence: int) -> JsonObject:
    obs_type = str(observation.get("type") or "").upper()
    kind = _OBSERVATION_KIND.get(obs_type, "SYSTEM")
    data: JsonObject = {
        "observation_id": observation.get("id"),
        "parent_observation_id": observation.get("parentObservationId"),
        "level": observation.get("level"),
    }
    if kind == "TOOL":
        data.update(_tool_event(observation))
    elif kind == "AGENT":
        data.update(_generation_event(observation))
    return {
        "sequence": sequence,
        "kind": kind,
        "name": str(observation.get("name") or obs_type.lower() or "observation"),
        "content": observation.get("output"),
        "data": data,
        "started_at": observation.get("startTime"),
        "ended_at": observation.get("endTime"),
    }


def _runtime_seconds(trace: JsonObject, observations: list[JsonObject]) -> float | None:
    latency = trace.get("latency")
    if isinstance(latency, (int, float)) and not isinstance(latency, bool):
        return float(latency)
    starts = [o.get("startTime") for o in observations if isinstance(o.get("startTime"), str)]
    ends = [o.get("endTime") for o in observations if isinstance(o.get("endTime"), str)]
    if not starts or not ends:
        return None
    from datetime import datetime

    try:
        return max(
            0.0,
            (datetime.fromisoformat(max(ends)) - datetime.fromisoformat(min(starts))).total_seconds(),
        )
    except ValueError:
        return None


def observations_to_bundle(trace: JsonObject) -> NormalizedTraceBundle:
    """Pure, offline mapping from one raw Langfuse trace dict (as returned by
    ``GET /api/public/traces/{id}``) to a ``NormalizedTraceBundle`` that carries
    tool status/error/args/results, per-turn tokens, and stop reason — the
    fields the AIMessage-only reconstruction throws away."""
    trace_id = trace.get("id")
    if not isinstance(trace_id, str) or not trace_id:
        raise LangfuseSourceError("trace is missing a non-empty id")
    observations = trace.get("observations")
    if not isinstance(observations, list) or not observations:
        raise LangfuseSourceError(f"trace {trace_id}: no observations")
    ordered = sorted(observations, key=_observation_start)
    events = [_observation_to_event(obs, index) for index, obs in enumerate(ordered)]

    any_tool_result = any(
        event["kind"] == "TOOL" and event["data"].get("result_available")
        for event in events
    )
    runtime_seconds = _runtime_seconds(trace, ordered)

    return parse_trace_bundle(
        {
            "case_id": str(trace.get("name") or trace_id),
            "case_revision": str(trace.get("release") or "langfuse-observed"),
            "release_id": str(trace.get("release") or "langfuse-unreleased"),
            "trial_id": trace_id,
            "session_id": str(trace.get("sessionId") or trace_id),
            "scenario": {
                "source_kind": "langfuse_trace",
                "user_id": trace.get("userId"),
                "metadata": trace.get("metadata"),
            },
            "events": events,
            "artifact_refs": [],
            "state_before_ref": {"kind": "LANGFUSE_TRACE_INPUT", "value": trace.get("input")},
            "state_after_ref": {"kind": "LANGFUSE_TRACE_OUTPUT", "value": trace.get("output")},
            "environment_draw_id": trace_id,
            "reset_policy": "ISOLATED_NAMESPACE",
            "execution": {
                "status": "COMPLETED",
                "started_at": trace.get("timestamp"),
                "ended_at": ordered[-1].get("endTime"),
                "runtime_seconds": runtime_seconds,
                "estimated_cost": trace.get("totalCost"),
            },
            "provenance": {
                "adapter_version": ADAPTER_VERSION,
                "corpus_kind": "LANGFUSE",
                "tool_results_available": any_tool_result,
                "full_world_state_available": False,
                "reset_proof_available": False,
                "diff_qualified": False,
            },
        },
        default_reset_policy=ResetPolicy.ISOLATED_NAMESPACE,
    )


def load_langfuse_traces(
    trace_ids: tuple[str, ...], creds: LangfuseCredentials
) -> tuple[NormalizedTraceBundle, ...]:
    """Fetch and normalize each trace id in one call. Convenience wrapper over
    ``fetch_trace`` + ``observations_to_bundle`` for callers that don't need the
    intermediate raw JSON."""
    return tuple(observations_to_bundle(fetch_trace(trace_id, creds)) for trace_id in trace_ids)


__all__ = [
    "ADAPTER_VERSION",
    "LangfuseCredentials",
    "LangfuseSourceError",
    "fetch_trace",
    "load_env_credentials",
    "load_langfuse_traces",
    "observations_to_bundle",
]
