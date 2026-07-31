import argparse
import json
import os
import re
import shutil
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, NoReturn

Object = dict[str, Any]
MAX_SAFE = 9_007_199_254_740_991
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$")
SCHEMA = "SOURCE_SCHEMA_VALIDATION_FAILED"
MISMATCH = "SOURCE_TURN_EVENT_MISMATCH"
TOP_FIELDS = "schema_version case_id session_id status system_prompt turns events"
TRACE_KEYS = "contract_kind events privacy_class schema_version source_trace_id "
TRACE_KEYS += "trace_id"
ENCODER = json.JSONEncoder(ensure_ascii=False, separators=(",", ":"), sort_keys=True)


class Reject(Exception):
    def __init__(self, code: str, pointer: str = "") -> None:
        self.code, self.pointer = code, pointer


class Parser(argparse.ArgumentParser):
    def error(self, _: str) -> NoReturn:
        raise SystemExit(fatal("CLI_USAGE_ERROR", 2))


def record(names: str, *values: Any) -> Object:
    return dict(zip(names.split(), values, strict=True))


def require(valid: bool, pointer: str = "", code: str = SCHEMA) -> None:
    if not valid:
        raise Reject(code, pointer)


def has_fields(value: Any, names: str) -> bool:
    return isinstance(value, dict) and all(name in value for name in names.split())


def unique(pairs: list[tuple[str, Any]]) -> Object:
    if len({key for key, _ in pairs}) != len(pairs):
        raise KeyError
    return dict(pairs)


DECODER = json.JSONDecoder(
    object_pairs_hook=unique, parse_float=Decimal, parse_constant=int
)


def text(value: Any, minimum: int = 0) -> bool:
    if not isinstance(value, str):
        return False
    control = ((n < 32 and n != 10) or 127 <= n <= 159 for n in map(ord, value))
    try:
        return not any(control) and minimum <= len(value.encode()) <= 65_536
    except UnicodeEncodeError:
        return False


def opaque(value: Any) -> bool:
    if value is None or isinstance(value, (bool, str)):
        return not isinstance(value, str) or text(value)
    if type(value) is int:
        return -MAX_SAFE <= value <= MAX_SAFE
    if isinstance(value, list):
        return all(map(opaque, value))
    return isinstance(value, dict) and all(
        text(key) and opaque(item) for key, item in value.items()
    )


def event(kind: str, names: str = "", *values: Any) -> Object:
    return {"event_kind": kind, **record(names, *values)}


def map_call(call: Any, turn: int, index: int, pointer: str) -> list[Object]:
    require(has_fields(call, "name arguments result_summary status"), pointer)
    name, arguments = call["name"], call["arguments"]
    summary, status = call["result_summary"], call["status"]
    valid = isinstance(name, str) and SAFE_ID.fullmatch(name) is not None
    require(valid and opaque(arguments) and opaque(summary), pointer)
    require(status in {"ok", "error"}, pointer)
    call_id = f"hrai-t{turn}-c{index}"
    fields = "call_id tool_name arguments"
    mapped = [event("TOOL_CALL", fields, call_id, name, arguments)]
    if status == "error":
        fields = "call_id result_state error_code"
        mapped.append(event("TOOL_RESULT", fields, call_id, "ERROR", "HRAI_TOOL_ERROR"))
    elif summary is not None:
        fields = "call_id result_state result"
        mapped.append(event("TOOL_RESULT", fields, call_id, "SUCCEEDED", summary))
    return mapped


def map_source(value: Any, seen: set[str]) -> Object:
    require(has_fields(value, TOP_FIELDS))
    version = value["schema_version"]
    if isinstance(version, str) and version != "normalized-trace-v2":
        raise Reject("UNSUPPORTED_SOURCE_SCHEMA_VERSION", "/schema_version")
    require(version == "normalized-trace-v2")
    require(value["status"] == "COMPLETED", "/status", "SOURCE_EXECUTION_INCOMPLETE")
    session = value["session_id"]
    ids = (value["case_id"], session)
    require(all(isinstance(item, str) and SAFE_ID.fullmatch(item) for item in ids))
    require(session not in seen, "/session_id", "DUPLICATE_TRACE_ID")
    prompt, turns, events = value["system_prompt"], value["turns"], value["events"]
    require(has_fields(prompt, "text") and text(prompt["text"], 1))
    require(isinstance(turns, list) and bool(turns) and not len(turns) % 2)
    require(isinstance(events, list) and len(turns) == len(events), "/events", MISMATCH)
    mapped = [event("SYSTEM_VISIBLE_MESSAGE", "content", prompt["text"])]
    for index, (turn, source_event) in enumerate(zip(turns, events, strict=True)):
        role, turn_number = ("user", "assistant")[index % 2], index // 2 + 1
        require(has_fields(turn, "role content"))
        require(turn["role"] == role and text(turn["content"], int(role == "user")))
        require(has_fields(source_event, "turn role tool_calls"))
        aligned = source_event["turn"] == turn_number and source_event["role"] == role
        tool_calls = source_event["tool_calls"]
        require(aligned and isinstance(tool_calls, list), "/events", MISMATCH)
        if role == "user":
            require(not tool_calls, "/events", MISMATCH)
            mapped.append(event("USER_MESSAGE", "content", turn["content"]))
            continue
        pointer = f"/events/{index}/tool_calls"
        for call_index, call in enumerate(tool_calls, 1):
            mapped.extend(map_call(call, turn_number, call_index, pointer))
        final = index == len(turns) - 1
        fields = "content is_final"
        mapped.append(event("ASSISTANT_MESSAGE", fields, turn["content"], final))
    require(len(mapped) <= 1_000, "/events", "MAPPED_TRACE_INVALID")
    for sequence, item in enumerate(mapped):
        item["sequence"] = sequence
    values = ("preview_trace", mapped, "SYNTHETIC", 1, session, session)
    return record(TRACE_KEYS, *values)


def compact(value: Any) -> bytes:
    return f"{ENCODER.encode(value)}\n".encode()


def parse_line(raw: bytes, first: bool) -> Any:
    require(not (first and raw.startswith(b"\xef\xbb\xbf")), code="BOM_FORBIDDEN")
    try:
        decoded = raw.decode()
    except UnicodeDecodeError as error:
        raise Reject("INVALID_UTF8") from error
    require(bool(decoded.strip()), code="BLANK_LINE")
    try:
        return DECODER.decode(decoded)
    except KeyError as error:
        raise Reject("DUPLICATE_JSON_KEY") from error
    except (ValueError, RecursionError) as error:
        raise Reject("MALFORMED_JSON") from error


def fatal(code: str, exit_code: int) -> int:
    print(ENCODER.encode({"outcome": "REJECTED", "reason_code": code}), file=sys.stderr)
    return exit_code


def read_input(source: Path) -> bytes:
    require(not source.is_symlink() and source.is_file(), code="INPUT_READ_FAILED")
    try:
        with source.open("rb") as handle:
            payload = handle.read(16 * 1024 * 1024 + 1)
    except OSError as error:
        raise Reject("INPUT_READ_FAILED") from error
    require(len(payload) <= 16 * 1024 * 1024, code="INPUT_TOO_LARGE")
    return payload


def main() -> int:
    parser = Parser()
    parser.add_argument("input", nargs="?")
    parser.add_argument("--out")
    parser.add_argument("--data-class")
    args = parser.parse_args()
    if args.data_class != "SYNTHETIC":
        return fatal("UNSUPPORTED_DATA_CLASS", 2)
    if args.input is None or args.out is None:
        return fatal("CLI_USAGE_ERROR", 2)
    source, target = Path(args.input), Path(args.out)
    if os.path.lexists(target) or not target.parent.is_dir():
        return fatal("OUTPUT_PATH_INVALID", 2)
    try:
        payload = read_input(source)
    except Reject as error:
        return fatal(error.code, 3 if error.code == "INPUT_TOO_LARGE" else 2)
    lines, final_lf = payload.split(b"\n"), payload.endswith(b"\n")
    if final_lf:
        lines.pop()
    if len(lines) > 1_000:
        return fatal("TOO_MANY_LINES", 3)
    accepted, rejected, seen = [], [], set[str]()
    for index, raw in enumerate(lines):
        try:
            size = len(raw) + int(index < len(lines) - 1 or final_lf)
            require(size <= 1024 * 1024, code="LINE_TOO_LARGE")
            bounded = raw[:-1] if raw.endswith(b"\r") else raw
            trace = map_source(parse_line(bounded, index == 0), seen)
        except Reject as error:
            message = error.code.replace("_", " ").capitalize() + "."
            if error.code == MISMATCH:
                message = "Source turns and events do not align."
            names = "code json_pointer line_number safe_message"
            values = (error.code, error.pointer, index + 1, message)
            rejected.append(record(names, *values))
        else:
            accepted.append(trace)
            seen.add(trace["trace_id"])
    accepted_bytes = b"".join(map(compact, accepted))
    rejected_bytes = b"".join(map(compact, rejected))
    created = False
    try:
        target.mkdir()
        created = True
        (target / "preview_traces.jsonl").write_bytes(accepted_bytes)
        (target / "rejected_source_traces.jsonl").write_bytes(rejected_bytes)
    except OSError:
        if created:
            shutil.rmtree(target, ignore_errors=True)
        return fatal("PUBLICATION_FAILED", 7)
    outcome = "EMPTY_CORPUS"
    if lines:
        outcome = "COMPLETED_WITH_REJECTIONS" if rejected else "COMPLETED"
    names = "input_count accepted_count rejected_count outcome"
    receipt = record(names, len(lines), len(accepted), len(rejected), outcome)
    print(ENCODER.encode(receipt))
    return 0 if outcome == "COMPLETED" else 10


raise SystemExit(main())
