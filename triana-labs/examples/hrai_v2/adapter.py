# fmt: off
import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import Any, NoReturn

MAX_SAFE = 9_007_199_254_740_991
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$")
TOP = {"schema_version", "case_id", "session_id", "status", "system_prompt", "turns", "events"}
TOP_IGNORED = {"client_id", "simulator_model", "user_turn_budget", "started_at", "error", "tokens", "usd", "tool_sequence", "decision_observable", "sub_agents", "finished_at"}
MESSAGES = {
    "BLANK_LINE": "Input line is blank.", "INVALID_UTF8": "Input line is not valid UTF-8.",
    "BOM_FORBIDDEN": "A UTF-8 byte-order mark is not permitted.", "LINE_TOO_LARGE": "Input line exceeds the size limit.",
    "MALFORMED_JSON": "Input line is not valid JSON.", "DUPLICATE_JSON_KEY": "Input line contains a duplicate JSON object key.",
    "NESTING_TOO_DEEP": "Input line exceeds the JSON nesting limit.",
    "UNSUPPORTED_SOURCE_SCHEMA_VERSION": "Source trace schema version is not supported.", "SOURCE_EXECUTION_INCOMPLETE": "Source execution is incomplete.",
    "SOURCE_TURN_EVENT_MISMATCH": "Source turns and events do not align.", "DUPLICATE_TRACE_ID": "Trace identifier was already accepted.",
    "MAPPED_TRACE_INVALID": "Mapped trace does not match the PreviewTrace contract.",
}


class Reject(Exception):
    def __init__(self, code: str, pointer: str = "") -> None:
        self.code, self.pointer = code, pointer


class Parser(argparse.ArgumentParser):
    def error(self, _: str) -> NoReturn:
        raise SystemExit(fail("CLI_USAGE_ERROR", 2))


def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise KeyError
        result[key] = value
    return result


def nonfinite(_: str) -> None:
    raise ValueError


def depth(value: Any) -> int:
    maximum, stack = 0, [(value, int(isinstance(value, (dict, list))))]
    while stack:
        item, level = stack.pop()
        maximum = max(maximum, level)
        children = item.values() if isinstance(item, dict) else item if isinstance(item, list) else ()
        stack.extend((child, level + int(isinstance(child, (dict, list)))) for child in children)
    return maximum


def text(value: Any, minimum: int = 0) -> bool:
    if not isinstance(value, str) or any((n < 32 and n != 10) or 127 <= n <= 159 for n in map(ord, value)):
        return False
    try:
        return minimum <= len(value.encode()) <= 65_536
    except UnicodeEncodeError:
        return False


def opaque(value: Any) -> bool:
    if value is None or isinstance(value, (bool, str)):
        return not isinstance(value, str) or text(value)
    if type(value) is int:
        return -MAX_SAFE <= value <= MAX_SAFE
    if isinstance(value, list):
        return all(map(opaque, value))
    return isinstance(value, dict) and all(text(key) and opaque(item) for key, item in value.items())


def require(valid: bool, pointer: str = "", code: str = "SOURCE_SCHEMA_VALIDATION_FAILED") -> None:
    if not valid:
        raise Reject(code, pointer)


def map_source(value: Any, seen: set[str]) -> dict[str, Any]:
    require(isinstance(value, dict))
    version = value.get("schema_version")
    require(not isinstance(version, str) or version == "normalized-trace-v2", "/schema_version", "UNSUPPORTED_SOURCE_SCHEMA_VERSION")
    require(not set(value) - TOP - TOP_IGNORED and TOP <= set(value) and version == "normalized-trace-v2")
    require(value["status"] == "COMPLETED", "/status", "SOURCE_EXECUTION_INCOMPLETE")
    session = value["session_id"]
    require(all(isinstance(item, str) and SAFE_ID.fullmatch(item) for item in (value["case_id"], session)))
    require(session not in seen, "/session_id", "DUPLICATE_TRACE_ID")
    prompt, turns, events = value["system_prompt"], value["turns"], value["events"]
    require(isinstance(prompt, dict) and set(prompt) == {"text"} and text(prompt.get("text"), 1), "/system_prompt")
    require(isinstance(turns, list) and bool(turns) and not len(turns) % 2 and isinstance(events, list), "/turns")
    require(len(turns) == len(events), "/events", "SOURCE_TURN_EVENT_MISMATCH")
    mapped = [{"event_kind": "SYSTEM_VISIBLE_MESSAGE", "content": prompt["text"]}]
    for index, (turn, event) in enumerate(zip(turns, events, strict=True)):
        role, number = ("user", "assistant")[index % 2], index // 2 + 1
        require(isinstance(turn, dict) and not set(turn) - {"role", "content", "tools_called", "metadata"} and {"role", "content"} <= set(turn), f"/turns/{index}")
        require(turn["role"] == role and text(turn["content"], int(role == "user")), f"/turns/{index}")
        require(isinstance(event, dict) and not set(event) - {"turn", "role", "tool_calls", "tokens", "ts", "error"} and {"turn", "role", "tool_calls"} <= set(event), f"/events/{index}")
        require(event["turn"] == number and event["role"] == role and isinstance(event["tool_calls"], list), "/events", "SOURCE_TURN_EVENT_MISMATCH")
        if role == "user":
            require(not event["tool_calls"], "/events", "SOURCE_TURN_EVENT_MISMATCH")
            mapped.append({"event_kind": "USER_MESSAGE", "content": turn["content"]})
            continue
        for call_index, call in enumerate(event["tool_calls"], 1):
            require(isinstance(call, dict) and set(call) == {"name", "arguments", "result_summary", "status", "error", "latency_ms", "cached"}, f"/events/{index}/tool_calls")
            latency = call["latency_ms"]
            valid = isinstance(call["name"], str) and SAFE_ID.fullmatch(call["name"]) is not None and opaque(call["arguments"]) and opaque(call["result_summary"])
            valid = valid and call["status"] in {"ok", "error"} and type(call["cached"]) is bool
            valid = valid and (latency is None or type(latency) is int and 0 <= latency <= MAX_SAFE)
            require(valid, f"/events/{index}/tool_calls")
            call_id = f"hrai-t{number}-c{call_index}"
            mapped.append({"event_kind": "TOOL_CALL", "call_id": call_id, "tool_name": call["name"], "arguments": call["arguments"]})
            if call["status"] == "error":
                mapped.append({"event_kind": "TOOL_RESULT", "call_id": call_id, "result_state": "ERROR", "error_code": "HRAI_TOOL_ERROR"})
            elif call["result_summary"] is not None:
                mapped.append({"event_kind": "TOOL_RESULT", "call_id": call_id, "result_state": "SUCCEEDED", "result": call["result_summary"]})
        mapped.append({"event_kind": "ASSISTANT_MESSAGE", "content": turn["content"], "is_final": index == len(turns) - 1})
    require(len(mapped) <= 1_000, "/events", "MAPPED_TRACE_INVALID")
    for sequence, event in enumerate(mapped):
        event["sequence"] = sequence
    return {"contract_kind": "preview_trace", "events": mapped, "privacy_class": "SYNTHETIC", "schema_version": 1, "source_trace_id": session, "trace_id": session}


def compact(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True) + "\n").encode()


def parse_line(raw: bytes, first: bool) -> Any:
    if first and raw.startswith(b"\xef\xbb\xbf"):
        raise Reject("BOM_FORBIDDEN")
    try:
        decoded = raw.decode()
    except UnicodeDecodeError as error:
        raise Reject("INVALID_UTF8") from error
    if not decoded.strip():
        raise Reject("BLANK_LINE")
    try:
        value = json.loads(decoded, object_pairs_hook=unique, parse_float=Decimal, parse_constant=nonfinite)
    except KeyError as error:
        raise Reject("DUPLICATE_JSON_KEY") from error
    except (ValueError, RecursionError) as error:
        raise Reject("NESTING_TOO_DEEP" if isinstance(error, RecursionError) else "MALFORMED_JSON") from error
    if depth(value) > 32:
        raise Reject("NESTING_TOO_DEEP")
    return value


def fail(code: str, exit_code: int) -> int:
    terminal = {"accepted_count": 0, "outcome": "REJECTED", "reason_code": code, "rejected_count": 0}
    print(json.dumps(terminal, separators=(",", ":"), sort_keys=True), file=sys.stderr)
    return exit_code


def main() -> int:
    parser = Parser()
    parser.add_argument("input", nargs="?")
    parser.add_argument("--out")
    parser.add_argument("--data-class")
    args = parser.parse_args()
    if args.data_class != "SYNTHETIC":
        return fail("UNSUPPORTED_DATA_CLASS", 2)
    if args.input is None or args.out is None:
        return fail("CLI_USAGE_ERROR", 2)
    source, target = Path(args.input), Path(args.out)
    if os.path.lexists(target) or not target.parent.is_dir() or target.parent.is_symlink():
        return fail("OUTPUT_PATH_INVALID", 2)
    try:
        info = source.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o444:
            raise OSError
        if info.st_size > 16 * 1024 * 1024:
            return fail("INPUT_TOO_LARGE", 3)
        payload = source.read_bytes()
    except OSError:
        return fail("INPUT_READ_FAILED", 2)
    if len(payload) > 16 * 1024 * 1024:
        return fail("INPUT_TOO_LARGE", 3)
    parts, final = payload.split(b"\n"), payload.endswith(b"\n")
    if final:
        parts.pop()
    if len(parts) > 1_000:
        return fail("TOO_MANY_LINES", 3)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(parts):
        line_number, size = index + 1, len(raw) + int(index < len(parts) - 1 or final)
        try:
            if size > 1024 * 1024:
                raise Reject("LINE_TOO_LARGE")
            trace = map_source(parse_line(raw[:-1] if raw.endswith(b"\r") else raw, index == 0), seen)
        except Reject as error:
            message = MESSAGES.get(error.code, "Source line does not match the trace schema.")
            rejected.append({"code": error.code, "json_pointer": error.pointer, "line_number": line_number, "safe_message": message})
        else:
            accepted.append(trace)
            seen.add(trace["trace_id"])
    preview, rejects = b"".join(map(compact, accepted)), b"".join(map(compact, rejected))
    manifest = {"accepted_count": len(accepted), "adapter_kind": "hrai_normalized_trace_v2_reference", "artifacts": {"preview_traces.jsonl": "sha256:" + hashlib.sha256(preview).hexdigest(), "rejected_source_traces.jsonl": "sha256:" + hashlib.sha256(rejects).hexdigest()}, "input_count": len(parts), "privacy_class": "SYNTHETIC", "rejected_count": len(rejected), "schema_version": 1, "source_schema_version": "normalized-trace-v2"}
    temporary: Path | None = None
    try:
        temporary = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=target.parent))
        for name, data in (("preview_traces.jsonl", preview), ("rejected_source_traces.jsonl", rejects), ("adapter_manifest.json", compact(manifest))):
            with (temporary / name).open("wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        if os.path.lexists(target):
            raise OSError
        os.rename(temporary, target)
    except OSError:
        if temporary is not None:
            shutil.rmtree(temporary, ignore_errors=True)
        return fail("PUBLICATION_FAILED", 7)
    outcome = "EMPTY_CORPUS" if not parts else "COMPLETED_WITH_REJECTIONS" if rejected else "COMPLETED"
    receipt = {"accepted_count": len(accepted), "manifest_path": f"{target}/adapter_manifest.json", "outcome": outcome, "rejected_count": len(rejected)}
    print(json.dumps(receipt, separators=(",", ":"), sort_keys=True))
    print(json.dumps({key: value for key, value in receipt.items() if key != "manifest_path"}, separators=(",", ":"), sort_keys=True), file=sys.stderr)
    return 0 if outcome == "COMPLETED" else 10


if __name__ == "__main__":
    raise SystemExit(main())
