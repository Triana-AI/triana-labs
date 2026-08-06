#!/usr/bin/env python3
"""Export the exact completed TAU² task bundles as PreviewTrace JSONL."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from collections import deque
from pathlib import Path, PurePosixPath
from typing import Any

STUDY_ID = "tau2-retail-discovery-v1"


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--expected-task-count", required=True, type=int)
    return parser.parse_args()


def _read_attempts(archive: Path) -> dict[str, tuple[str, dict[str, Any]]]:
    attempts: dict[str, tuple[str, dict[str, Any]]] = {}
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            parts = PurePosixPath(member.name).parts
            if not (
                member.isfile()
                and len(parts) == 5
                and parts[0] == "tasks"
                and parts[2] == "attempts"
                and parts[4] == "tau2-results.json"
            ):
                continue
            task_id, attempt_id = parts[1], parts[3]
            if task_id in attempts:
                raise ValueError(f"duplicate completed task bundle: {task_id}")
            stream = bundle.extractfile(member)
            if stream is None:
                raise ValueError(f"unreadable task bundle: {task_id}")
            try:
                payload = json.load(stream)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ValueError(f"invalid task bundle: {task_id}") from error
            if not isinstance(payload, dict):
                raise ValueError(f"invalid task bundle: {task_id}")
            attempts[task_id] = (attempt_id, payload)
    return attempts


def _event_stream(messages: Any) -> list[dict[str, Any]]:
    if not isinstance(messages, list) or not messages:
        raise ValueError("simulation messages are missing")
    events: list[dict[str, Any]] = []
    unresolved: deque[str] = deque()
    textual_assistant_indices: list[int] = []
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("simulation message is invalid")
        role = message.get("role")
        content = message.get("content")
        if role == "user":
            if not isinstance(content, str) or not content:
                raise ValueError("user message is invalid")
            events.append({"event_kind": "USER_MESSAGE", "content": content})
        elif role == "assistant":
            if isinstance(content, str):
                textual_assistant_indices.append(len(events))
                events.append(
                    {
                        "event_kind": "ASSISTANT_MESSAGE",
                        "content": content,
                        "is_final": False,
                    }
                )
            calls = message.get("tool_calls") or []
            if not isinstance(calls, list):
                raise ValueError("assistant tool calls are invalid")
            for call in calls:
                if not isinstance(call, dict):
                    raise ValueError("assistant tool call is invalid")
                call_id, tool_name, arguments = (
                    call.get("id"),
                    call.get("name"),
                    call.get("arguments"),
                )
                if not isinstance(call_id, str) or not isinstance(tool_name, str):
                    raise ValueError("assistant tool call identity is invalid")
                unresolved.append(call_id)
                events.append(
                    {
                        "event_kind": "TOOL_CALL",
                        "call_id": call_id,
                        "tool_name": tool_name,
                        "arguments": arguments,
                    }
                )
        elif role == "tool":
            if not unresolved:
                raise ValueError("tool result has no unresolved call")
            if not isinstance(content, str):
                raise ValueError("tool result is invalid")
            events.append(
                {
                    "event_kind": "TOOL_RESULT",
                    "call_id": unresolved.popleft(),
                    "result_state": "SUCCEEDED",
                    "result": content,
                }
            )
        else:
            raise ValueError(f"unsupported simulation role: {role!r}")
    if unresolved:
        raise ValueError("simulation has unresolved tool calls")
    if textual_assistant_indices:
        events[textual_assistant_indices[-1]]["is_final"] = True
    return [dict(event, sequence=index) for index, event in enumerate(events)]


def _trace(
    task_id: str,
    attempt_id: str,
    payload: dict[str, Any],
    archive_sha256: str,
) -> dict[str, Any]:
    simulations = payload.get("simulations")
    if not isinstance(simulations, list) or len(simulations) != 1:
        raise ValueError(f"task {task_id} must contain exactly one simulation")
    simulation = simulations[0]
    if not isinstance(simulation, dict):
        raise ValueError(f"task {task_id} simulation is invalid")
    reward_info = simulation.get("reward_info")
    if not isinstance(reward_info, dict) or "reward" not in reward_info:
        raise ValueError(f"task {task_id} reward lineage is missing")
    reward = reward_info["reward"]
    trace_id = f"tau2-retail-{task_id}"
    return {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": "SYNTHETIC",
        "trace_id": trace_id,
        "source_trace_id": (
            f"tau2://{STUDY_ID}/archive/{archive_sha256}/task/{task_id}/"
            f"attempt/{attempt_id}/reward={reward}"
        ),
        "events": _event_stream(simulation.get("messages")),
    }


def main() -> int:
    args = _arguments()
    archive_bytes = args.archive.read_bytes()
    actual_sha256 = hashlib.sha256(archive_bytes).hexdigest()
    if actual_sha256 != args.expected_sha256:
        raise ValueError("archive SHA-256 mismatch")
    attempts = _read_attempts(args.archive)
    if len(attempts) != args.expected_task_count:
        raise ValueError(
            f"expected {args.expected_task_count} task bundles, found {len(attempts)}"
        )
    traces = [
        _trace(task_id, attempt_id, payload, actual_sha256)
        for task_id, (attempt_id, payload) in attempts.items()
    ]
    traces.sort(key=lambda item: item["trace_id"])
    encoded = b"".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
        + b"\n"
        for item in traces
    )
    args.output.write_bytes(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
