"""Validate one adapter-emitted PreviewTrace JSONL line.

External integrations emit JSONL; they do not call this module. The Observer passes
one already size-bounded physical line to :func:`parse_and_validate_line`, which owns
the byte and strict-JSON boundary. :func:`validate_trace` then owns the closed schema,
cross-event invariants, and mechanical eligibility returned to the Observer.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, cast

JsonObject = dict[str, Any]

MAX_SAFE_INTEGER = 9_007_199_254_740_991
EVENT_KINDS = (
    "ASSISTANT_MESSAGE",
    "SYSTEM_VISIBLE_MESSAGE",
    "TERMINAL",
    "TOOL_CALL",
    "TOOL_RESULT",
    "USER_MESSAGE",
)
TERMINAL_STATES = ("ABORTED", "ERROR", "SUCCESS")
PRIVACY_CLASSES = ("SYNTHETIC", "OWNER_AUTHORIZED_REAL_DATA_CANARY")

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$")
_SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")

_SAFE_MESSAGES = {
    "BLANK_LINE": "Input line is blank.",
    "INVALID_UTF8": "Input line is not valid UTF-8.",
    "BOM_FORBIDDEN": "A UTF-8 byte-order mark is not permitted.",
    "LINE_TOO_LARGE": "Input line exceeds the size limit.",
    "MALFORMED_JSON": "Input line is not valid JSON.",
    "DUPLICATE_JSON_KEY": "Input line contains a duplicate JSON object key.",
    "NESTING_TOO_DEEP": "Input line exceeds the JSON nesting limit.",
    "SCHEMA_VALIDATION_FAILED": "Input line does not match the trace schema.",
    "UNSUPPORTED_SCHEMA_VERSION": "Trace schema version is not supported.",
    "UNSUPPORTED_PRIVACY_CLASS": "Trace privacy class is not supported.",
    "DUPLICATE_TRACE_ID": "Trace identifier was already accepted.",
    "DUPLICATE_SOURCE_TRACE_ID": "Source trace identifier was already accepted.",
    "IMPOSSIBLE_TRACE_STATE": "Trace events describe an impossible state.",
}


class _DuplicateKeyError(ValueError):
    """Signal that strict JSON parsing observed an ambiguous object."""

    # Private parser signal translated into the stable DUPLICATE_JSON_KEY rejection.
    pass  # noqa: PIE790 - retained by the frozen docstring-stripped AST gate.


class _NonFiniteError(ValueError):
    """Signal that strict JSON parsing observed a non-standard numeric token."""

    # Private parser signal: bare NaN/Infinity are malformed JSON, not schema values.
    pass  # noqa: PIE790 - retained by the frozen docstring-stripped AST gate.


@dataclass(frozen=True)
class LineRejection(Exception):
    """Carry one closed, content-free reason for rejecting a physical line."""

    code: str
    json_pointer: str = ""

    def as_record(self, line_number: int) -> JsonObject:
        """Return the safe rejection artifact record for a one-based line."""

        # Only closed codes, pointers, and fixed prose cross the privacy boundary.
        # Raw values and parser exceptions must never enter rejected_traces.jsonl.
        return {
            "line_number": line_number,
            "code": self.code,
            "json_pointer": self.json_pointer,
            "safe_message": _SAFE_MESSAGES[self.code],
        }


@dataclass(frozen=True)
class ValidatedTrace:
    """Represent a normalized trace plus mechanical downstream readiness."""

    value: JsonObject
    # This flag is mechanical readiness for a future component. It is neither a
    # generated case nor a semantic judgment about the conversation.
    case_generation_eligible: bool


def parse_and_validate_line(raw_line: bytes, *, first_line: bool) -> ValidatedTrace:
    """Turn one bounded raw line into a validated trace or typed rejection.

    ``first_line`` enables the first-line-only BOM rule. Contract and validation
    failures become :class:`LineRejection`; unexpected faults remain internal. Raw
    bytes and parser exceptions never become rejection output.
    """

    # The Observer has already enforced the raw line-size limit. This stage owns the
    # remaining byte and strict-JSON boundary in a deliberate order: first-line BOM,
    # UTF-8, blankness, JSON grammar/duplicate keys, then structural depth. Keeping
    # these checks before validate_trace makes malformed transport distinguishable
    # from a well-formed JSON value that violates the PreviewTrace contract.

    if first_line and raw_line.startswith(b"\xef\xbb\xbf"):
        raise LineRejection("BOM_FORBIDDEN")
    try:
        text = raw_line.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise LineRejection("INVALID_UTF8") from error
    if not text.strip():
        raise LineRejection("BLANK_LINE")

    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_float=Decimal,
            parse_constant=_reject_nonfinite,
        )
    except _DuplicateKeyError as error:
        raise LineRejection("DUPLICATE_JSON_KEY") from error
    except (_NonFiniteError, json.JSONDecodeError) as error:
        raise LineRejection("MALFORMED_JSON") from error
    except RecursionError as error:
        raise LineRejection("NESTING_TOO_DEEP") from error

    if _json_depth(parsed) > 32:
        raise LineRejection("NESTING_TOO_DEEP")
    return validate_trace(parsed)


def validate_trace(value: Any) -> ValidatedTrace:
    """Validate parsed JSON against the closed trace and event contract.

    The function returns the input object only after local event shapes and ordered
    cross-event relationships pass. It does not own cross-line identity or artifacts.
    """

    # validate_trace starts at an already parsed JSON value. It owns the closed
    # top-level/event vocabulary and relationships across events; it owns no file or
    # corpus behavior. Unsupported integer versions and named privacy classes take
    # precedence over generic schema failure so callers receive the actionable typed
    # refusal even though the complete closed schema will also reject those values.

    if not isinstance(value, dict):
        raise LineRejection("SCHEMA_VALIDATION_FAILED")
    trace = cast(JsonObject, value)

    version = trace.get("schema_version")
    if type(version) is int and version != 1:
        raise LineRejection("UNSUPPORTED_SCHEMA_VERSION", "/schema_version")
    privacy_class = trace.get("privacy_class")
    if isinstance(privacy_class, str) and privacy_class not in PRIVACY_CLASSES:
        raise LineRejection("UNSUPPORTED_PRIVACY_CLASS", "/privacy_class")

    if set(trace) != {
        "contract_kind",
        "schema_version",
        "privacy_class",
        "trace_id",
        "source_trace_id",
        "events",
    }:
        raise LineRejection("SCHEMA_VALIDATION_FAILED")
    if trace["contract_kind"] != "preview_trace":
        raise LineRejection("SCHEMA_VALIDATION_FAILED", "/contract_kind")
    if type(trace["schema_version"]) is not int or trace["schema_version"] != 1:
        raise LineRejection("SCHEMA_VALIDATION_FAILED", "/schema_version")
    if trace["privacy_class"] not in PRIVACY_CLASSES:
        raise LineRejection("SCHEMA_VALIDATION_FAILED", "/privacy_class")
    if not _is_safe_id(trace["trace_id"]):
        raise LineRejection("SCHEMA_VALIDATION_FAILED", "/trace_id")
    if not _is_external_id(trace["source_trace_id"]):
        raise LineRejection("SCHEMA_VALIDATION_FAILED", "/source_trace_id")

    events = trace["events"]
    if not isinstance(events, list) or not 1 <= len(events) <= 1_000:
        raise LineRejection("SCHEMA_VALIDATION_FAILED", "/events")
    for index, event in enumerate(events):
        _validate_event(event, index)
    # Per-event shape must be known before relationship code reads discriminator and
    # companion fields. This separation prevents cross-event checks from inventing
    # defaults for malformed events or turning schema gaps into impossible states.
    _validate_event_relationships(cast(list[JsonObject], events))

    return ValidatedTrace(
        value=trace,
        case_generation_eligible=_is_case_generation_eligible(
            cast(list[JsonObject], events)
        ),
    )


def _unique_object(pairs: list[tuple[str, Any]]) -> JsonObject:
    """Build a JSON object while refusing a second occurrence of any key."""

    # json.loads normally keeps the last duplicate key. Rejecting while the ordered
    # pair stream is still visible prevents ambiguous input from being normalized.
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError
        result[key] = value
    return result


def _reject_nonfinite(_: str) -> None:
    """Reject the non-standard constants routed here by ``json.loads``."""

    # This callback is used only for non-standard bare constants. Finite JSON floats
    # parse as Decimal and are rejected later as syntactically valid but out-of-domain.
    raise _NonFiniteError


def _json_depth(value: Any) -> int:
    """Return maximum container depth, counting the root container as one."""

    # Containers contribute one level and scalars zero; the root container is depth
    # one. Object member order cannot affect the maximum, preserving determinism.
    if isinstance(value, dict):
        return 1 + max((_json_depth(item) for item in value.values()), default=0)
    if isinstance(value, list):
        return 1 + max((_json_depth(item) for item in value), default=0)
    return 0


def _is_safe_id(value: Any) -> bool:
    """Return whether a value satisfies the closed ASCII SafeId domain."""

    # SafeId's ASCII grammar makes the regex character bound identical to its byte
    # bound and keeps identifiers safe in deterministic artifacts.
    return isinstance(value, str) and _SAFE_ID.fullmatch(value) is not None


def _is_safe_code(value: Any) -> bool:
    """Return whether a value satisfies the closed uppercase SafeCode domain."""

    return isinstance(value, str) and _SAFE_CODE.fullmatch(value) is not None


def _contains_control(value: str, *, allow_lf: bool) -> bool:
    """Detect forbidden C0/C1 controls under the selected LF policy."""

    # Message and opaque JSON strings may carry LF; identifiers may not. All other
    # C0/C1 controls remain forbidden even when JSON escaped them successfully.
    return any(
        (code < 32 and not (allow_lf and code == 10)) or 127 <= code <= 159
        for code in map(ord, value)
    )


def _is_bounded_text(
    value: Any,
    *,
    minimum_bytes: int,
    maximum_bytes: int,
    allow_lf: bool,
) -> bool:
    """Check text type, control policy, and inclusive UTF-8 byte bounds."""

    # Limits are UTF-8 bytes, not Python code points. Encoding also rejects lone
    # surrogates before canonical artifact serialization can fail unexpectedly.
    if not isinstance(value, str) or _contains_control(value, allow_lf=allow_lf):
        return False
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError:
        return False
    return minimum_bytes <= size <= maximum_bytes


def _is_external_id(value: Any) -> bool:
    """Return whether a value is a bounded, control-free ExternalId."""

    return _is_bounded_text(
        value,
        minimum_bytes=1,
        maximum_bytes=512,
        allow_lf=False,
    )


def _is_json_scalar_domain(value: Any) -> bool:
    """Recursively check the portable LABS-01 opaque-JSON value domain."""

    # Tool arguments/results are opaque to Triana but not unbounded: their entire
    # tree must use portable strings, safe integers, and JSON containers. Decimal is
    # the parser's marker for every finite fractional/exponent-form number.
    if value is None or isinstance(value, (bool, str)):
        return not isinstance(value, str) or _is_bounded_text(
            value,
            minimum_bytes=0,
            maximum_bytes=65_536,
            allow_lf=True,
        )
    if type(value) is int:
        return -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER
    if isinstance(value, Decimal):
        return False
    if isinstance(value, list):
        return all(_is_json_scalar_domain(item) for item in value)
    if isinstance(value, dict):
        return all(
            _is_bounded_text(
                key,
                minimum_bytes=0,
                maximum_bytes=65_536,
                allow_lf=True,
            )
            and _is_json_scalar_domain(item)
            for key, item in value.items()
        )
    return False


def _validate_event(value: Any, index: int) -> None:
    """Validate one closed event variant without interpreting other events."""

    # This function validates one closed variant in isolation and reports the event
    # location. Ordering, call/result linkage, and terminal placement are intentionally
    # deferred until every event has a trustworthy shape.
    pointer = f"/events/{index}"
    if not isinstance(value, dict):
        raise LineRejection("SCHEMA_VALIDATION_FAILED", pointer)
    event = cast(JsonObject, value)
    sequence = event.get("sequence")
    if type(sequence) is not int or sequence < 0 or sequence > MAX_SAFE_INTEGER:
        raise LineRejection("SCHEMA_VALIDATION_FAILED", f"{pointer}/sequence")

    kind = event.get("event_kind")
    if not isinstance(kind, str) or kind not in EVENT_KINDS:
        raise LineRejection("SCHEMA_VALIDATION_FAILED", f"{pointer}/event_kind")

    if kind in {"USER_MESSAGE", "SYSTEM_VISIBLE_MESSAGE"}:
        if set(event) != {"sequence", "event_kind", "content"} or not _is_bounded_text(
            event.get("content"),
            minimum_bytes=1,
            maximum_bytes=65_536,
            allow_lf=True,
        ):
            raise LineRejection("SCHEMA_VALIDATION_FAILED", pointer)
    elif kind == "ASSISTANT_MESSAGE":
        if (
            set(event) != {"sequence", "event_kind", "content", "is_final"}
            or not _is_bounded_text(
                event.get("content"),
                minimum_bytes=0,
                maximum_bytes=65_536,
                allow_lf=True,
            )
            or type(event.get("is_final")) is not bool
        ):
            raise LineRejection("SCHEMA_VALIDATION_FAILED", pointer)
    elif kind == "TOOL_CALL":
        if (
            set(event)
            != {"sequence", "event_kind", "call_id", "tool_name", "arguments"}
            or not _is_safe_id(event.get("call_id"))
            or not _is_safe_id(event.get("tool_name"))
            or not _is_json_scalar_domain(event.get("arguments"))
        ):
            raise LineRejection("SCHEMA_VALIDATION_FAILED", pointer)
    elif kind == "TOOL_RESULT":
        _validate_tool_result(event, pointer)
    else:
        _validate_terminal(event, pointer)


def _validate_tool_result(event: JsonObject, pointer: str) -> None:
    """Validate result-state companion fields and opaque result content."""

    # Result-state companion fields are mutually exclusive. Presence is checked via
    # exact key sets so null cannot stand in for a required result or error code.
    state = event.get("result_state")
    if state == "SUCCEEDED":
        valid = set(event) == {
            "sequence",
            "event_kind",
            "call_id",
            "result_state",
            "result",
        } and _is_json_scalar_domain(event.get("result"))
    elif state == "ERROR":
        valid = set(event) == {
            "sequence",
            "event_kind",
            "call_id",
            "result_state",
            "error_code",
        } and _is_safe_code(event.get("error_code"))
    else:
        valid = False
    if not valid or not _is_safe_id(event.get("call_id")):
        raise LineRejection("SCHEMA_VALIDATION_FAILED", pointer)


def _validate_terminal(event: JsonObject, pointer: str) -> None:
    """Validate terminal-state companion fields without judging the outcome."""

    # SUCCESS carries no reason; ERROR and ABORTED require a safe reason code. This is
    # structural evidence only and does not interpret whether the outcome was good.
    state = event.get("terminal_state")
    if state == "SUCCESS":
        valid = set(event) == {"sequence", "event_kind", "terminal_state"}
    elif state in {"ERROR", "ABORTED"}:
        valid = set(event) == {
            "sequence",
            "event_kind",
            "terminal_state",
            "reason_code",
        } and _is_safe_code(event.get("reason_code"))
    else:
        valid = False
    if not valid:
        raise LineRejection("SCHEMA_VALIDATION_FAILED", pointer)


def _validate_event_relationships(events: list[JsonObject]) -> None:
    """Reject impossible sequence, call/result, final, and terminal ordering."""

    # Input order is semantic. Calls become available only after their TOOL_CALL,
    # results consume that earlier call once, and terminal/final multiplicity is
    # checked without reordering or repairing the supplied history.
    calls: set[str] = set()
    results: set[str] = set()
    final_count = 0
    terminal_indices: list[int] = []

    for index, event in enumerate(events):
        if event["sequence"] != index:
            raise LineRejection("IMPOSSIBLE_TRACE_STATE", f"/events/{index}/sequence")
        kind = event["event_kind"]
        if kind == "TOOL_CALL":
            call_id = cast(str, event["call_id"])
            if call_id in calls:
                raise LineRejection("IMPOSSIBLE_TRACE_STATE", f"/events/{index}")
            calls.add(call_id)
        elif kind == "TOOL_RESULT":
            call_id = cast(str, event["call_id"])
            if call_id not in calls or call_id in results:
                raise LineRejection("IMPOSSIBLE_TRACE_STATE", f"/events/{index}")
            results.add(call_id)
        elif kind == "ASSISTANT_MESSAGE" and event["is_final"] is True:
            final_count += 1
        elif kind == "TERMINAL":
            terminal_indices.append(index)

    if final_count > 1 or len(terminal_indices) > 1:
        raise LineRejection("IMPOSSIBLE_TRACE_STATE", "/events")
    if terminal_indices and terminal_indices[0] != len(events) - 1:
        raise LineRejection("IMPOSSIBLE_TRACE_STATE", f"/events/{terminal_indices[0]}")


def _is_case_generation_eligible(events: list[JsonObject]) -> bool:
    """Return whether a user turn has later assistant or tool-call behavior."""

    # Eligibility means only that an observed user turn has later agent behavior to
    # condition on. Future Corpus Intelligence consumes eligible normalized traces;
    # LABS-01 neither generates a case nor infers persona, intent, or quality here.
    user_seen = False
    for event in events:
        if event["event_kind"] == "USER_MESSAGE":
            user_seen = True
        elif user_seen and event["event_kind"] in {"ASSISTANT_MESSAGE", "TOOL_CALL"}:
            return True
    return False
