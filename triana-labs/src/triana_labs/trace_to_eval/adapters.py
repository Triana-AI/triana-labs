"""Fail-closed local source adapters for Trace-to-Eval Review V0."""

# ruff: noqa: TRY004 - typed ValueError codes are the public adapter boundary.

from __future__ import annotations

import hashlib
import json
import math
import re
import tarfile
from collections import defaultdict, deque
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any, cast

from triana_labs.contracts.traces import LineRejection, validate_trace

JsonObject = dict[str, Any]
_MAX_SAFE_INTEGER = 9_007_199_254_740_991
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$")

_LANGCHAIN_ROLES = {
    "human": "HumanMessage",
    "ai": "AIMessage",
    "system": "SystemMessage",
    "tool": "ToolMessage",
    "chat": "ChatMessage",
}


def _canonical(value: Any, *, lf: bool = False) -> bytes:
    encoded = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return encoded + (b"\n" if lf else b"")


def _portable_opaque(value: Any) -> Any:
    """Preserve unsupported JSON scalars as visibly encoded canonical JSON text."""

    def supported(item: Any) -> bool:
        if item is None or isinstance(item, (bool, str)):
            return True
        if type(item) is int:
            return -_MAX_SAFE_INTEGER <= item <= _MAX_SAFE_INTEGER
        if isinstance(item, list):
            return all(supported(child) for child in item)
        if isinstance(item, dict):
            return all(
                isinstance(key, str) and supported(child) for key, child in item.items()
            )
        return False

    return value if supported(value) else _canonical(value).decode("utf-8")


def _object_lines(path: Path) -> list[JsonObject]:
    try:
        raw_lines = path.read_bytes().splitlines()
    except OSError as error:
        raise ValueError("SOURCE_UNAVAILABLE") from error
    rows: list[JsonObject] = []
    for line in raw_lines:
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("SOURCE_SCHEMA_INVALID") from error
        if not isinstance(row, dict):
            raise ValueError("SOURCE_SCHEMA_INVALID")
        rows.append(cast(JsonObject, row))
    if not rows:
        raise ValueError("SOURCE_EMPTY")
    return rows


def _event(kind: str, **fields: Any) -> JsonObject:
    return {"event_kind": kind, **fields}


def _safe_langsmith_id(value: str) -> str:
    if _SAFE_ID.fullmatch(value):
        return value
    return "ls-call-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
    except OSError as error:
        raise ValueError("SOURCE_UNAVAILABLE") from error
    return "sha256:" + digest.hexdigest()


def _is_langchain_message(value: Any) -> bool:
    return isinstance(value, dict) and (
        value.get("type") == "constructor"
        or ("content" in value and isinstance(value.get("type"), str))
    )


def _flatten_langchain_messages(value: Any) -> list[JsonObject]:
    if _is_langchain_message(value):
        return [cast(JsonObject, value)]
    if isinstance(value, list):
        return [row for item in value for row in _flatten_langchain_messages(item)]
    return []


def _message_class(message: JsonObject) -> str | None:
    if message.get("type") == "constructor":
        identity = message.get("id")
        return str(identity[-1]) if isinstance(identity, list) and identity else None
    role = message.get("type")
    return _LANGCHAIN_ROLES.get(role.lower(), role) if isinstance(role, str) else None


def _flatten_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "\n".join(parts)
    return ""


def _message_text(message: JsonObject) -> str:
    if message.get("type") == "constructor":
        kwargs = message.get("kwargs")
        return (
            _flatten_message_content(kwargs.get("content"))
            if isinstance(kwargs, dict)
            else ""
        )
    return _flatten_message_content(message.get("content"))


def _run_messages(run: JsonObject, side: str) -> list[JsonObject]:
    block = run.get(side)
    return (
        _flatten_langchain_messages(block.get("messages"))
        if isinstance(block, dict)
        else []
    )


def _run_ai_messages(run: JsonObject) -> list[JsonObject]:
    outputs = run.get("outputs")
    if not isinstance(outputs, dict):
        return []
    generations = outputs.get("generations")
    generated: list[JsonObject] = []
    if isinstance(generations, list):
        for outer in generations:
            for generation in outer if isinstance(outer, list) else []:
                if not isinstance(generation, dict):
                    continue
                message = generation.get("message")
                if _is_langchain_message(message):
                    generated.append(cast(JsonObject, message))
                elif isinstance(generation.get("text"), str):
                    generated.append({"type": "ai", "content": generation["text"]})
    return generated or [
        message
        for message in _run_messages(run, "outputs")
        if _message_class(message) == "AIMessage"
    ]


def _message_fact(message: JsonObject) -> tuple[str, str] | None:
    role = _message_class(message)
    text = _message_text(message)
    if not text or role not in {"HumanMessage", "AIMessage", "SystemMessage"}:
        return None
    return role, text


def _message_payload(message: JsonObject) -> JsonObject:
    kwargs = message.get("kwargs")
    return cast(JsonObject, kwargs) if isinstance(kwargs, dict) else message


def _embedded_tool_events(
    messages: list[JsonObject],
) -> list[tuple[tuple[str, str] | None, JsonObject]]:
    """Recover AI tool calls and ToolMessage results before the next visible turn."""

    recovered: list[tuple[tuple[str, str] | None, JsonObject]] = []
    for index, message in enumerate(messages):
        payload = _message_payload(message)
        next_fact = next(
            (
                fact
                for later in messages[index + 1 :]
                if (fact := _message_fact(later)) is not None
            ),
            None,
        )
        if _message_class(message) == "AIMessage":
            additional = payload.get("additional_kwargs")
            additional = additional if isinstance(additional, dict) else {}
            raw_calls = payload.get("tool_calls") or additional.get("tool_calls") or []
            if not isinstance(raw_calls, list):
                raise ValueError("LANGSMITH_TOOL_CALL_INVALID")
            for raw_call in raw_calls:
                if not isinstance(raw_call, dict):
                    raise ValueError("LANGSMITH_TOOL_CALL_INVALID")
                function = raw_call.get("function")
                function = function if isinstance(function, dict) else {}
                call_id = raw_call.get("id")
                name = raw_call.get("name") or function.get("name")
                arguments = raw_call.get("args", function.get("arguments"))
                if not isinstance(call_id, str) or not isinstance(name, str):
                    raise ValueError("LANGSMITH_TOOL_CALL_INVALID")
                call_id = _safe_langsmith_id(call_id)
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        pass
                recovered.append(
                    (
                        next_fact,
                        _event(
                            "TOOL_CALL",
                            call_id=call_id,
                            tool_name=name,
                            arguments=_portable_opaque(arguments),
                        ),
                    )
                )
        if _message_class(message) == "ToolMessage":
            call_id = payload.get("tool_call_id")
            if not isinstance(call_id, str):
                raise ValueError("LANGSMITH_TOOL_RESULT_INVALID")
            call_id = _safe_langsmith_id(call_id)
            status = payload.get("status")
            if status in {"error", "failed", "failure"}:
                event = _event(
                    "TOOL_RESULT",
                    call_id=call_id,
                    result_state="ERROR",
                    error_code="LANGSMITH_TOOL_ERROR",
                )
            else:
                event = _event(
                    "TOOL_RESULT",
                    call_id=call_id,
                    result_state="SUCCEEDED",
                    result=_portable_opaque(payload.get("content")),
                )
            recovered.append((next_fact, event))
    return recovered


def _append_tool_event(
    events: list[JsonObject],
    event: JsonObject,
    emitted: set[tuple[str, str]],
    calls: Mapping[str, JsonObject],
) -> None:
    kind, call_id = cast(str, event["event_kind"]), cast(str, event["call_id"])
    key = (kind, call_id)
    if key in emitted:
        return
    if kind == "TOOL_RESULT" and ("TOOL_CALL", call_id) not in emitted:
        call = calls.get(call_id)
        if call is None:
            return
        events.append(call)
        emitted.add(("TOOL_CALL", call_id))
    events.append(event)
    emitted.add(key)


def _merge_facts(
    existing: list[tuple[str, str]], candidate: list[tuple[str, str]]
) -> None:
    """Merge cumulative/nested LangSmith echoes without dropping novel messages."""
    if not candidate:
        return
    if len(candidate) <= len(existing):
        for offset in range(len(existing) - len(candidate) + 1):
            if existing[offset : offset + len(candidate)] == candidate:
                return
    if len(existing) <= len(candidate) and candidate[: len(existing)] == existing:
        existing.extend(candidate[len(existing) :])
        return
    overlap = min(len(existing), len(candidate))
    while overlap and existing[-overlap:] != candidate[:overlap]:
        overlap -= 1
    existing.extend(candidate[overlap:])


def _grouped_langsmith(
    path: Path,
) -> tuple[list[tuple[JsonObject, str]], int, int]:
    """Adapt grouped LangSmith rows into one dependency-safe session trace."""
    sessions: dict[str, list[JsonObject]] = defaultdict(list)
    seen_trace_ids: set[str] = set()
    source_line_count = 0
    try:
        with path.open("rb") as stream:
            for line_number, raw in enumerate(stream, 1):
                source_line_count = line_number
                if not raw.strip():
                    raise ValueError(f"LANGSMITH_SOURCE_INVALID_LINE_{line_number}")
                try:
                    row = json.loads(raw)
                except (json.JSONDecodeError, UnicodeDecodeError) as error:
                    raise ValueError(
                        f"LANGSMITH_SOURCE_INVALID_LINE_{line_number}"
                    ) from error
                if not isinstance(row, dict):
                    raise ValueError(f"LANGSMITH_SOURCE_INVALID_LINE_{line_number}")
                trace_id, session_key, runs = (
                    row.get("trace_id"),
                    row.get("session_key"),
                    row.get("runs"),
                )
                if (
                    not isinstance(trace_id, str)
                    or not trace_id
                    or trace_id in seen_trace_ids
                    or not isinstance(session_key, str)
                    or not session_key
                    or not isinstance(runs, list)
                    or not runs
                    or any(not isinstance(run, dict) for run in runs)
                ):
                    raise ValueError(f"LANGSMITH_SOURCE_INVALID_LINE_{line_number}")
                seen_trace_ids.add(trace_id)
                sessions[session_key].append(row)
    except OSError as error:
        raise ValueError("SOURCE_UNAVAILABLE") from error
    if not sessions:
        raise ValueError("SOURCE_EMPTY")

    converted: list[tuple[JsonObject, str]] = []
    suppressed_fact_count = 0
    for session_key, groups in sorted(sessions.items()):
        facts: list[tuple[str, str]] = []
        seen_facts: set[tuple[str, str]] = set()
        tool_events: list[JsonObject] = []
        tool_events_before: dict[tuple[str, str], list[JsonObject]] = defaultdict(list)
        embedded_tool_keys: set[tuple[str, str]] = set()
        embedded_calls: dict[str, JsonObject] = {}
        any_error = False
        ordered_groups = sorted(
            groups, key=lambda row: str(row.get("start_time") or row["trace_id"])
        )
        for group in ordered_groups:
            runs = sorted(
                cast(list[JsonObject], group["runs"]),
                key=lambda run: str(
                    run.get("dotted_order") or run.get("start_time") or run.get("id")
                ),
            )
            candidates = [
                (
                    len(_run_messages(run, "inputs")),
                    str(run.get("end_time") or ""),
                    str(run.get("id") or ""),
                    run,
                )
                for run in runs
                if _run_messages(run, "inputs")
            ]
            if not candidates:
                raise ValueError("LANGSMITH_MESSAGE_RUN_UNAVAILABLE")
            selected = max(candidates, key=lambda item: item[:3])[3]
            selected_messages = [
                *_run_messages(selected, "inputs"),
                *_run_ai_messages(selected),
            ]
            for message in selected_messages:
                fact = _message_fact(message)
                if fact is None:
                    continue
                if fact in seen_facts:
                    suppressed_fact_count += 1
                    continue
                seen_facts.add(fact)
                facts.append(fact)

            for run in runs:
                run_messages = [
                    *_run_messages(run, "inputs"),
                    *_run_ai_messages(run),
                ]
                for next_fact, event in _embedded_tool_events(run_messages):
                    key = (cast(str, event["event_kind"]), cast(str, event["call_id"]))
                    if key in embedded_tool_keys:
                        continue
                    embedded_tool_keys.add(key)
                    if event["event_kind"] == "TOOL_CALL":
                        embedded_calls[cast(str, event["call_id"])] = event
                    if next_fact is None:
                        tool_events.append(event)
                    else:
                        tool_events_before[next_fact].append(event)
                run_error = run.get("error")
                is_error = run.get("status") == "error" or bool(run_error)
                any_error = any_error or is_error
                if run.get("run_type") != "tool":
                    continue
                run_id, name = run.get("id"), run.get("name")
                if not isinstance(run_id, str) or not isinstance(name, str):
                    raise ValueError("LANGSMITH_TOOL_IDENTITY_INVALID")
                call_id = "ls-" + run_id
                tool_events.append(
                    _event(
                        "TOOL_CALL",
                        call_id=call_id,
                        tool_name=name,
                        arguments=run.get("inputs"),
                    )
                )
                if is_error:
                    tool_events.append(
                        _event(
                            "TOOL_RESULT",
                            call_id=call_id,
                            result_state="ERROR",
                            error_code="LANGSMITH_RUN_ERROR",
                        )
                    )
                else:
                    tool_events.append(
                        _event(
                            "TOOL_RESULT",
                            call_id=call_id,
                            result_state="SUCCEEDED",
                            result=run.get("outputs"),
                        )
                    )
        events: list[JsonObject] = []
        emitted_embedded_keys: set[tuple[str, str]] = set()
        for role, text in facts:
            for tool_event in tool_events_before.get((role, text), []):
                key = (
                    cast(str, tool_event["event_kind"]),
                    cast(str, tool_event["call_id"]),
                )
                _append_tool_event(
                    events,
                    tool_event,
                    emitted_embedded_keys,
                    embedded_calls,
                )
            events.append(
                _event(
                    {
                        "HumanMessage": "USER_MESSAGE",
                        "AIMessage": "ASSISTANT_MESSAGE",
                        "SystemMessage": "SYSTEM_VISIBLE_MESSAGE",
                    }[role],
                    content=text,
                    **({"is_final": False} if role == "AIMessage" else {}),
                )
            )
        assistant_indices = [
            index
            for index, event in enumerate(events)
            if event["event_kind"] == "ASSISTANT_MESSAGE"
        ]
        if assistant_indices:
            events[assistant_indices[-1]]["is_final"] = True
        for tool_event in tool_events:
            _append_tool_event(
                events,
                tool_event,
                emitted_embedded_keys,
                embedded_calls,
            )
        events.append(
            _event(
                "TERMINAL",
                terminal_state="ERROR" if any_error else "SUCCESS",
                **({"reason_code": "LANGSMITH_RUN_ERROR"} if any_error else {}),
            )
        )
        for sequence, event in enumerate(events):
            event["sequence"] = sequence
        safe_session_id = hashlib.sha256(session_key.encode("utf-8")).hexdigest()[:32]
        trace = {
            "contract_kind": "preview_trace",
            "schema_version": 1,
            "privacy_class": "CUSTOMER_AUTHORIZED_TRACE_DATA",
            "trace_id": "langsmith-session-" + safe_session_id,
            "source_trace_id": "langsmith://session/" + session_key,
            "events": events,
        }
        try:
            validated = validate_trace(trace).value
        except LineRejection as error:
            raise ValueError("LANGSMITH_MAPPED_TRACE_INVALID") from error
        converted.append((validated, session_key))
    return converted, source_line_count, suppressed_fact_count


def _hrai(row: JsonObject) -> tuple[JsonObject, str]:
    if (
        row.get("schema_version") != "normalized-trace-v2"
        or row.get("status") != "COMPLETED"
    ):
        raise ValueError("HRAI_SOURCE_INVALID")
    session, case = row.get("session_id"), row.get("case_id")
    prompt, turns, source_events = (
        row.get("system_prompt"),
        row.get("turns"),
        row.get("events"),
    )
    if not all(isinstance(item, str) and item for item in (session, case)):
        raise ValueError("HRAI_SOURCE_INVALID")
    if not isinstance(session, str) or not isinstance(case, str):
        raise ValueError("HRAI_SOURCE_INVALID")
    if not isinstance(prompt, dict) or not isinstance(prompt.get("text"), str):
        raise ValueError("HRAI_SOURCE_INVALID")
    if (
        not isinstance(turns, list)
        or not isinstance(source_events, list)
        or len(turns) != len(source_events)
    ):
        raise ValueError("HRAI_SOURCE_INVALID")
    events = [_event("SYSTEM_VISIBLE_MESSAGE", content=prompt["text"])]
    for index, (turn, source_event) in enumerate(
        zip(turns, source_events, strict=True)
    ):
        if not isinstance(turn, dict) or not isinstance(source_event, dict):
            raise ValueError("HRAI_SOURCE_INVALID")
        role, content = turn.get("role"), turn.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            raise ValueError("HRAI_SOURCE_INVALID")
        calls = source_event.get("tool_calls")
        if not isinstance(calls, list):
            raise ValueError("HRAI_SOURCE_INVALID")
        if role == "user":
            if calls:
                raise ValueError("HRAI_SOURCE_INVALID")
            events.append(_event("USER_MESSAGE", content=content))
            continue
        for call_index, call in enumerate(calls, 1):
            if not isinstance(call, dict) or not isinstance(call.get("name"), str):
                raise ValueError("HRAI_SOURCE_INVALID")
            call_id = f"hrai-t{index // 2 + 1}-c{call_index}"
            events.append(
                _event(
                    "TOOL_CALL",
                    call_id=call_id,
                    tool_name=call["name"],
                    arguments=_portable_opaque(call.get("arguments")),
                )
            )
            if call.get("status") == "error":
                events.append(
                    _event(
                        "TOOL_RESULT",
                        call_id=call_id,
                        result_state="ERROR",
                        error_code="HRAI_TOOL_ERROR",
                    )
                )
            elif call.get("result_summary") is not None:
                events.append(
                    _event(
                        "TOOL_RESULT",
                        call_id=call_id,
                        result_state="SUCCEEDED",
                        result=_portable_opaque(call["result_summary"]),
                    )
                )
        events.append(
            _event(
                "ASSISTANT_MESSAGE", content=content, is_final=index == len(turns) - 1
            )
        )
    for sequence, item in enumerate(events):
        item["sequence"] = sequence
    trace = {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": "SYNTHETIC",
        "trace_id": session,
        "source_trace_id": session,
        "events": events,
    }
    return validate_trace(trace).value, case


def _messages_trace(row: JsonObject, *, prefix: str) -> tuple[JsonObject, str]:
    trace_id = row.get("trace_id", row.get("conversation_id", row.get("id")))
    group_id = row.get("conversation_id", row.get("group_id", trace_id))
    messages = row.get("messages", row.get("conversation"))
    if (
        not isinstance(trace_id, str)
        or not isinstance(group_id, str)
        or not isinstance(messages, list)
    ):
        raise ValueError("NORMALIZED_SOURCE_INVALID")
    events: list[JsonObject] = []
    assistant_positions: list[int] = []
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("NORMALIZED_SOURCE_INVALID")
        role, content = message.get("role"), message.get("content")
        if role not in {"user", "assistant", "system"} or not isinstance(content, str):
            raise ValueError("NORMALIZED_SOURCE_INVALID")
        if role == "assistant":
            assistant_positions.append(len(events))
        events.append(
            _event(
                {
                    "user": "USER_MESSAGE",
                    "assistant": "ASSISTANT_MESSAGE",
                    "system": "SYSTEM_VISIBLE_MESSAGE",
                }[role],
                content=content,
                **({"is_final": False} if role == "assistant" else {}),
            )
        )
    if assistant_positions:
        events[assistant_positions[-1]]["is_final"] = True
    for sequence, item in enumerate(events):
        item["sequence"] = sequence
    trace = {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": row.get("privacy_class", "CUSTOMER_AUTHORIZED_TRACE_DATA"),
        "trace_id": trace_id,
        "source_trace_id": f"{prefix}:{trace_id}",
        "events": events,
    }
    return validate_trace(trace).value, group_id


def _tau_events(messages: Any) -> list[JsonObject]:
    if not isinstance(messages, list) or not messages:
        raise ValueError("TAU_SOURCE_INVALID")
    events: list[JsonObject] = []
    unresolved: deque[str] = deque()
    assistants: list[int] = []
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("TAU_SOURCE_INVALID")
        role, content = message.get("role"), message.get("content")
        if role == "user" and isinstance(content, str):
            events.append(_event("USER_MESSAGE", content=content))
        elif role == "assistant":
            if isinstance(content, str):
                assistants.append(len(events))
                events.append(
                    _event("ASSISTANT_MESSAGE", content=content, is_final=False)
                )
            calls = message.get("tool_calls") or []
            if not isinstance(calls, list):
                raise ValueError("TAU_SOURCE_INVALID")
            for call in calls:
                if (
                    not isinstance(call, dict)
                    or not isinstance(call.get("id"), str)
                    or not isinstance(call.get("name"), str)
                ):
                    raise ValueError("TAU_SOURCE_INVALID")
                unresolved.append(call["id"])
                events.append(
                    _event(
                        "TOOL_CALL",
                        call_id=call["id"],
                        tool_name=call["name"],
                        arguments=call.get("arguments"),
                    )
                )
        elif role == "tool" and isinstance(content, str) and unresolved:
            events.append(
                _event(
                    "TOOL_RESULT",
                    call_id=unresolved.popleft(),
                    result_state="SUCCEEDED",
                    result=content,
                )
            )
        else:
            raise ValueError("TAU_SOURCE_INVALID")
    if unresolved:
        raise ValueError("TAU_SOURCE_INVALID")
    if assistants:
        events[assistants[-1]]["is_final"] = True
    for sequence, item in enumerate(events):
        item["sequence"] = sequence
    return events


def _tau_archive(
    path: Path,
) -> tuple[list[tuple[JsonObject, str]], list[JsonObject] | None]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    output: list[tuple[JsonObject, str]] = []
    outcomes: list[JsonObject] = []
    outcomes_complete = True
    try:
        with tarfile.open(path, "r:gz") as bundle:
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
                stream = bundle.extractfile(member)
                if stream is None:
                    raise ValueError("TAU_SOURCE_INVALID")
                payload = json.load(stream)
                simulations = (
                    payload.get("simulations") if isinstance(payload, dict) else None
                )
                if (
                    not isinstance(simulations, list)
                    or len(simulations) != 1
                    or not isinstance(simulations[0], dict)
                ):
                    raise ValueError("TAU_SOURCE_INVALID")
                task_id, attempt_id = parts[1], parts[3]
                reward_info = simulations[0].get("reward_info")
                reward = (
                    reward_info.get("reward") if isinstance(reward_info, dict) else None
                )
                if (
                    not isinstance(reward, (int, float))
                    or isinstance(reward, bool)
                    or not math.isfinite(float(reward))
                ):
                    outcomes_complete = False
                trace = {
                    "contract_kind": "preview_trace",
                    "schema_version": 1,
                    "privacy_class": "SYNTHETIC",
                    "trace_id": f"tau2-{task_id}",
                    "source_trace_id": f"tau2://archive/{digest}/task/{task_id}/attempt/{attempt_id}",
                    "events": _tau_events(simulations[0].get("messages")),
                }
                output.append((validate_trace(trace).value, task_id))
                if outcomes_complete and reward is not None:
                    numeric_reward = float(reward)
                    outcomes.append(
                        {
                            "trace_id": f"tau2-{task_id}",
                            "group_id": task_id,
                            "source": "TAU2_REWARD_INFO",
                            "reward": numeric_reward,
                            "outcome": "SUCCESS"
                            if numeric_reward == 1.0
                            else "FAILURE",
                        }
                    )
    except (OSError, tarfile.TarError, json.JSONDecodeError) as error:
        raise ValueError("TAU_SOURCE_INVALID") from error
    if not output:
        raise ValueError("TAU_SOURCE_INVALID")
    if not outcomes_complete or len(outcomes) != len(output):
        return output, None
    outcomes.sort(key=lambda row: cast(str, row["trace_id"]))
    return output, outcomes


def prepare_evidence_manifest(
    source_path: str | Path,
    output_dir: str | Path,
    *,
    source_kind: str,
    workspace_id: str = "local",
    agent_id: str = "local-agent",
    semantic_model_id: str | None = None,
) -> Path:
    """Normalize one explicitly selected source and write a local evidence manifest."""
    source, destination = Path(source_path), Path(output_dir)
    upstream_sha256 = _file_sha256(source)
    adapter_rejections: list[JsonObject] = []
    source_record_count: int | None = None
    upstream_record_count: int | None = None
    reconstruction_suppressed_count: int | None = None
    tau_outcomes: list[JsonObject] | None = None
    if source_kind == "tau-archive":
        converted, tau_outcomes = _tau_archive(source)
        upstream_record_count = 1
    elif source_kind == "langsmith-grouped-jsonl":
        (
            converted,
            upstream_record_count,
            reconstruction_suppressed_count,
        ) = _grouped_langsmith(source)
    else:
        rows = _object_lines(source)
        upstream_record_count = len(rows)
        converted = []
        source_record_count = (
            len(rows) if source_kind == "hrai-normalized-jsonl" else None
        )
        for line_number, row in enumerate(rows, 1):
            if source_kind in {"preview-trace-jsonl", "tau-preview-jsonl"}:
                try:
                    trace = validate_trace(row).value
                except LineRejection as error:
                    raise ValueError("PREVIEW_TRACE_INVALID") from error
                converted.append((trace, cast(str, trace["trace_id"])))
            elif source_kind == "hrai-normalized-jsonl":
                if row.get("status") != "COMPLETED":
                    adapter_rejections.append(
                        {
                            "line_number": line_number,
                            "code": "SOURCE_EXECUTION_INCOMPLETE",
                            "json_pointer": "/status",
                        }
                    )
                    continue
                try:
                    converted.append(_hrai(row))
                except (ValueError, LineRejection):
                    adapter_rejections.append(
                        {
                            "line_number": line_number,
                            "code": "SOURCE_SCHEMA_VALIDATION_FAILED",
                            "json_pointer": "",
                        }
                    )
            elif source_kind in {
                "blitz-normalized-jsonl",
                "langsmith-normalized-jsonl",
            }:
                converted.append(_messages_trace(row, prefix="blitz"))
            else:
                raise ValueError("SOURCE_KIND_UNSUPPORTED")
    ids: set[str] = set()
    groups: dict[str, list[str]] = defaultdict(list)
    for trace, group in converted:
        trace_id = cast(str, trace["trace_id"])
        if trace_id in ids:
            raise ValueError("DUPLICATE_TRACE_ID")
        ids.add(trace_id)
        groups[group].append(trace_id)
    payload = b"".join(
        _canonical(trace, lf=True)
        for trace, _ in sorted(
            converted, key=lambda item: cast(str, item[0]["trace_id"])
        )
    )
    destination.mkdir(parents=True, exist_ok=True)
    traces_path = destination / "preview_traces.jsonl"
    traces_path.write_bytes(payload)
    all_synthetic = all(trace["privacy_class"] == "SYNTHETIC" for trace, _ in converted)
    synthetic_tau = (
        source_kind in {"tau-archive", "tau-preview-jsonl"} and all_synthetic
    )
    manifest = {
        "artifact_kind": "evidence_bundle_manifest_v0",
        "schema_version": 0,
        "source": {
            "adapter_id": source_kind,
            "adapter_version": "1",
            "path": str(traces_path.resolve()),
            "sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
            "physical_record_count": source_record_count or len(converted),
            "normalized_record_count": len(converted),
            "upstream_sha256": upstream_sha256,
            "upstream_source_kind": source_kind,
        },
        "agent": {"workspace_id": workspace_id, "agent_id": agent_id},
        "privacy": {
            "authorization": "LOCAL_OPERATOR_DECLARED",
            "execution_location": "LOCAL_PRIVATE",
            "provider_egress": {
                "authorized": semantic_model_id is not None and synthetic_tau,
                "model_id": semantic_model_id if synthetic_tau else None,
            },
            "redaction": {"state": "NOT_DECLARED"},
        },
        "grouping": {
            "highest_dependency_key": "source_group_id",
            "assignments": [
                {"group_id": group, "trace_ids": sorted(trace_ids)}
                for group, trace_ids in sorted(groups.items())
            ],
        },
        "capabilities": {
            "paired_arms": any(len(items) > 1 for items in groups.values()),
            "outcomes": tau_outcomes is not None,
            "existing_evals": False,
            "embeddings": False,
        },
        "outcomes": tau_outcomes,
        "existing_evals": None,
        "adapter_rejections": adapter_rejections,
    }
    if source_kind == "langsmith-grouped-jsonl":
        cast(JsonObject, manifest["source"])["upstream_physical_record_count"] = (
            upstream_record_count
        )
        cast(JsonObject, manifest["source"])["session_reconstruction"] = {
            "policy": "MOST_COMPLETE_MESSAGE_RUN_PER_GROUP_V0",
            "ordering": ["INPUT_MESSAGE_COUNT", "END_TIME", "RUN_ID"],
            "exact_duplicate_key": ["ROLE", "CONTENT"],
            "suppressed_fact_count": reconstruction_suppressed_count,
        }
    manifest_path = destination / "evidence_bundle_manifest.json"
    manifest_path.write_bytes(_canonical(manifest, lf=True))
    return manifest_path


__all__ = ["prepare_evidence_manifest"]
