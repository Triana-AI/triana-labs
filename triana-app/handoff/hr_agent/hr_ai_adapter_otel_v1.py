"""HR-AI normalized-trace-otel-v1 -> Agentagon normalized trace bundle adapter.

Schema ``normalized-trace-otel-v1`` is a newer HR-AI export shape sourced from
OpenTelemetry spans rather than the historical_traffic_v0 simulator runner v1/v2
parse. Unlike v1/v2 (turns + a parallel per-turn runtime-events list, with tool
calls nested under each assistant turn), otel-v1 rows carry a single flat
``events`` list directly on the row, mixing ``kind`` values ``"tool"``,
``"model"``, and ``"generate-sql"`` in emission order -- there is no
turns/events pairing to merge. Only ``kind == "tool"`` events become TOOL
NormalizedEvents (name + arguments + result), which is all
``event_signals.agent_looping_label`` and ``_tool_call_signature`` need;
``"model"`` events become AGENT events (a model call producing the next
assistant turn) and ``"generate-sql"`` events become WORKFLOW events (an
internal SQL-generation step), both kept for provenance/inspection even though
no current signal reads them.

Row-level ``status`` is always ``"COMPLETED"`` in this corpus even when
``error`` is set (e.g. a LangGraph "Recursion limit of 50 reached" crash) --
the row still carries a full, usable event trace up to the crash. So unlike
v1/v2, a non-empty ``error`` does NOT become an ExecutionGap here; the row is
still parsed into a bundle, and the raw error text is carried into
``provenance["error"]`` so downstream recursion-crash detection (which the
generic ``agent_looping_label`` formula does not perform) can read it without
a second corpus pass.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from agentagon.evals.adapters import TraceAdapterResult
from agentagon.evals.models import ExecutionGap, ExecutionGapKind, ResetPolicy
from agentagon.evals.trace_bundle import NormalizedTraceBundle, parse_trace_bundle

SUPPORTED_SCHEMA_VERSION = "normalized-trace-otel-v1"

# Row.error substrings that mean "the agent crashed out of its own control loop"
# rather than an ordinary tool/backend failure. Recognized here (not just in
# run_gate.py) so any consumer of this adapter's bundles can read the same
# flag off provenance instead of re-parsing the raw error string.
RECURSION_CRASH_MARKER = "Recursion limit"


class HrAiNormalizedTraceOtelV1Adapter:
    """Normalize a ``normalized-trace-otel-v1`` export (OTel-sourced HR-AI runs).

    Like v1/v2, the export records ordered tool calls but not a full
    world-state snapshot or reset-state proof; those limits stay explicit in
    provenance. Tool results ARE available here (``result`` on each tool
    event), unlike v1.
    """

    adapter_version = "hr-ai-normalized-trace-otel-v1"

    def load(
        self,
        path: Path,
        *,
        default_reset_policy: ResetPolicy = ResetPolicy.ISOLATED_NAMESPACE,
    ) -> TraceAdapterResult:
        del default_reset_policy
        bundles: list[NormalizedTraceBundle] = []
        gaps: list[ExecutionGap] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            case_id: str | None = None
            session_id: str | None = None
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("row is not an object")
                schema_version = row.get("schema_version")
                if schema_version != SUPPORTED_SCHEMA_VERSION:
                    raise ValueError(f"unsupported schema_version: {schema_version!r}")
                case_id = _required_text(row, "case_id")
                session_id = _required_text(row, "session_id")
                if str(row.get("status", "")).upper() != "COMPLETED":
                    gaps.append(
                        ExecutionGap(
                            kind=ExecutionGapKind.HARNESS_FAILURE,
                            reason=f"{path}:{line_number}: {row.get('error') or 'harness run did not complete'}",
                            case_id=case_id,
                            trial_id=session_id,
                        )
                    )
                    continue

                raw_events = row.get("events")
                if not isinstance(raw_events, list):
                    raise ValueError("events must be a list")

                events = _normalize_events(raw_events)
                client_id = str(row.get("client_id") or "unknown-client")
                state_after = row.get("state_after")
                if not isinstance(state_after, dict):
                    state_after = {}
                error = row.get("error")
                repeated_tool_calls = row.get("repeated_tool_calls")
                if not isinstance(repeated_tool_calls, dict):
                    repeated_tool_calls = {}
                bundles.append(
                    parse_trace_bundle(
                        {
                            "case_id": case_id,
                            "case_revision": "normalized-trace-otel-v1",
                            "release_id": "hr-ai-normalized-trace-otel-v1",
                            "trial_id": session_id,
                            "session_id": session_id,
                            "scenario": {
                                "client_id": client_id,
                                "source_kind": "otel_span_export",
                            },
                            "events": events,
                            "artifact_refs": [],
                            "state_before_ref": {
                                "kind": "SIMULATED_CASE_CONTEXT_ONLY",
                                "case_id": case_id,
                                "client_id": client_id,
                            },
                            "state_after_ref": {
                                "kind": "STATE_AFTER_SNAPSHOT",
                                "value": state_after,
                            },
                            "environment_draw_id": session_id,
                            "reset_policy": "ISOLATED_NAMESPACE",
                            "execution": {
                                "status": "COMPLETED",
                                "started_at": row.get("started_at"),
                                "ended_at": row.get("finished_at"),
                                "runtime_seconds": _runtime_seconds(
                                    row.get("started_at"), row.get("finished_at")
                                ),
                                "estimated_cost": row.get("usd"),
                            },
                            "provenance": {
                                "adapter_version": self.adapter_version,
                                "source_line": line_number,
                                "corpus_kind": "PRODUCTION_LIKE",
                                "tool_order_boundary": "",
                                "tool_results_available": True,
                                "full_world_state_available": False,
                                "reset_proof_available": False,
                                "diff_qualified": False,
                                "error": error,
                                "recursion_crash": bool(error) and RECURSION_CRASH_MARKER in str(error),
                                "repeated_tool_calls": repeated_tool_calls,
                            },
                        },
                        source_path=str(path),
                        source_line=line_number,
                    )
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                gaps.append(
                    ExecutionGap(
                        kind=ExecutionGapKind.MALFORMED_TRACE,
                        reason=f"{path}:{line_number}: {error}",
                        case_id=case_id,
                        trial_id=session_id,
                    )
                )
        if not bundles:
            raise ValueError(f"{path}: no completed HR-AI otel-v1 conversations")
        return TraceAdapterResult(
            adapter_version=self.adapter_version,
            bundles=tuple(bundles),
            gaps=tuple(gaps),
            source_path=str(path),
        )


def _normalize_events(raw_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for sequence, event in enumerate(raw_events):
        if not isinstance(event, dict):
            raise ValueError("event must be an object")
        kind = event.get("kind")
        if kind == "tool":
            output.append(
                {
                    "sequence": sequence,
                    "kind": "TOOL",
                    "name": str(event.get("name") or "unknown_tool"),
                    "content": None,
                    "data": {
                        "arguments": event.get("arguments", {}),
                        "result": event.get("result"),
                        "result_available": "result" in event,
                        "status": event.get("status"),
                    },
                    "started_at": event.get("ts"),
                }
            )
        elif kind == "model":
            output.append(
                {
                    "sequence": sequence,
                    "kind": "AGENT",
                    "name": str(event.get("name") or "model_call"),
                    "content": None,
                    "data": {
                        "model": event.get("model"),
                        "tokens": event.get("tokens", {}),
                        "status": event.get("status"),
                    },
                    "started_at": event.get("ts"),
                }
            )
        elif kind == "generate-sql":
            output.append(
                {
                    "sequence": sequence,
                    "kind": "WORKFLOW",
                    "name": str(event.get("name") or "generate-sql"),
                    "content": event.get("sql"),
                    "data": {
                        "arguments": event.get("arguments", {}),
                        "status": event.get("status"),
                    },
                    "started_at": event.get("ts"),
                }
            )
        else:
            raise ValueError(f"unknown otel-v1 event kind: {kind!r}")
    return output


def _required_text(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be non-empty text")
    return value.strip()


def _runtime_seconds(started_at: Any, finished_at: Any) -> float | None:
    if not isinstance(started_at, str) or not isinstance(finished_at, str):
        return None
    try:
        return max(
            0.0,
            (datetime.fromisoformat(finished_at) - datetime.fromisoformat(started_at)).total_seconds(),
        )
    except ValueError:
        return None


__all__ = ["HrAiNormalizedTraceOtelV1Adapter", "RECURSION_CRASH_MARKER"]
