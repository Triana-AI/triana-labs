"""Standalone PreviewTrace v1 conformance panel for the public skill validator."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPOSITORY_ROOT / "triana-skills"
TOOL = (
    PACKAGE_ROOT
    / "plugins"
    / "triana"
    / "skills"
    / "onboard"
    / "scripts"
    / "onboard.py"
)
REFERENCE = (
    PACKAGE_ROOT
    / "plugins"
    / "triana"
    / "skills"
    / "onboard"
    / "references"
    / "previewtrace-v1.md"
)
FIXTURES = Path(__file__).parent / "fixtures"
JsonObject = dict[str, Any]


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _event(sequence: int | bool, event_kind: str, **values: Any) -> JsonObject:
    return {"sequence": sequence, "event_kind": event_kind, **values}


def _trace(events: list[JsonObject] | None = None) -> JsonObject:
    return {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": "CUSTOMER_AUTHORIZED_TRACE_DATA",
        "trace_id": "synthetic-conformance",
        "source_trace_id": "fixture/synthetic-conformance",
        "events": events
        or [
            _event(0, "USER_MESSAGE", content="Synthetic request"),
            _event(
                1,
                "ASSISTANT_MESSAGE",
                content="Synthetic response",
                is_final=True,
            ),
            _event(2, "TERMINAL", terminal_state="SUCCESS"),
        ],
    }


def _safe_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in tuple(environment):
        upper = key.upper()
        if any(token in upper for token in ("API_KEY", "TOKEN", "AZURE", "OPENAI")):
            environment.pop(key)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, os.fspath(TOOL), *arguments],
        cwd=PACKAGE_ROOT,
        env=_safe_environment(),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _terminal_json(completed: subprocess.CompletedProcess[str]) -> JsonObject:
    stream = completed.stdout if completed.stdout.strip() else completed.stderr
    lines = [line for line in stream.splitlines() if line.strip()]
    if not lines:
        raise AssertionError(f"validator emitted no terminal JSON: {completed!r}")
    try:
        value = json.loads(lines[-1])
    except json.JSONDecodeError as error:
        raise AssertionError(
            f"validator emitted invalid terminal JSON: {completed!r}"
        ) from error
    assert isinstance(value, dict)
    return value


def _validate_payload(
    payload: bytes,
) -> tuple[subprocess.CompletedProcess[str], bytes | None]:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = root / "source.jsonl"
        output = root / "validated.jsonl"
        source.write_bytes(payload)
        completed = _run(
            "validate",
            "--source",
            os.fspath(source),
            "--output",
            os.fspath(output),
            "--confirm-authorized-traces",
        )
        return completed, output.read_bytes() if output.is_file() else None


def _replace_event(trace: JsonObject, event: JsonObject) -> JsonObject:
    changed = copy.deepcopy(trace)
    changed["events"] = [event]
    return changed


class PreviewTraceClosedSchemaTests(unittest.TestCase):
    def assert_rejected(
        self,
        value: JsonObject | bytes,
        *,
        reason_code: str = "PREVIEWTRACE_INVALID",
    ) -> None:
        payload = value if isinstance(value, bytes) else _canonical(value)
        completed, output = _validate_payload(payload)
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(_terminal_json(completed)["reason_code"], reason_code)
        self.assertIsNone(output)

    def assert_accepted(self, value: JsonObject) -> None:
        payload = _canonical(value)
        completed, output = _validate_payload(payload)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(output, payload)

    def test_closed_top_and_event_schemas_ids_and_scalar_domains(self) -> None:
        base = _trace()
        mutations: list[tuple[str, Callable[[JsonObject], None]]] = [
            ("extra top field", lambda row: row.__setitem__("extra", True)),
            ("unsafe trace id", lambda row: row.__setitem__("trace_id", "bad id")),
            (
                "overlong trace id",
                lambda row: row.__setitem__("trace_id", "a" * 129),
            ),
            (
                "controlled external id",
                lambda row: row.__setitem__("source_trace_id", "bad\nid"),
            ),
            (
                "overlong external id",
                lambda row: row.__setitem__("source_trace_id", "é" * 257),
            ),
            (
                "extra message field",
                lambda row: row["events"][0].__setitem__("role", "user"),
            ),
            (
                "boolean sequence",
                lambda row: row["events"][0].__setitem__("sequence", False),
            ),
            (
                "empty user content",
                lambda row: row["events"][0].__setitem__("content", ""),
            ),
            (
                "controlled user content",
                lambda row: row["events"][0].__setitem__("content", "bad\tcontent"),
            ),
            (
                "overlong user content",
                lambda row: row["events"][0].__setitem__("content", "x" * 65_537),
            ),
        ]
        for label, mutate in mutations:
            with self.subTest(label=label):
                value = copy.deepcopy(base)
                mutate(value)
                self.assert_rejected(value)

        for privacy_class in (
            "SYNTHETIC",
            "OWNER_AUTHORIZED_REAL_DATA_CANARY",
            "CUSTOMER_AUTHORIZED_TRACE_DATA",
        ):
            with self.subTest(privacy_class=privacy_class):
                value = copy.deepcopy(base)
                value["privacy_class"] = privacy_class
                self.assert_accepted(value)

    def test_strict_json_depth_size_and_portable_number_boundaries(self) -> None:
        canonical = _canonical(_trace())
        duplicate_key = canonical.replace(
            b'"source_trace_id":"fixture/synthetic-conformance",',
            b'"source_trace_id":"fixture/synthetic-conformance",'
            b'"source_trace_id":"second",',
            1,
        )
        self.assertNotEqual(duplicate_key, canonical)
        self.assert_rejected(duplicate_key)
        self.assert_rejected(
            _canonical(_trace()).replace(b'"schema_version":1', b'"schema_version":NaN')
        )

        nested: Any = None
        for _ in range(31):
            nested = [nested]
        deep = _trace(
            [
                _event(0, "USER_MESSAGE", content="Synthetic request"),
                _event(
                    1,
                    "TOOL_CALL",
                    call_id="call-1",
                    tool_name="synthetic_tool",
                    arguments={"nested": nested},
                ),
                _event(2, "TERMINAL", terminal_state="SUCCESS"),
            ]
        )
        self.assert_rejected(deep)

        for opaque_value in (
            0.5,
            9_007_199_254_740_992,
            "bad\tvalue",
            "x" * 65_537,
        ):
            with self.subTest(opaque_value=type(opaque_value).__name__):
                trace = _trace(
                    [
                        _event(0, "USER_MESSAGE", content="Synthetic request"),
                        _event(
                            1,
                            "TOOL_CALL",
                            call_id="call-1",
                            tool_name="synthetic_tool",
                            arguments={"value": opaque_value},
                        ),
                        _event(2, "TERMINAL", terminal_state="SUCCESS"),
                    ]
                )
                self.assert_rejected(trace)

        too_many_events = _trace(
            [
                *[_event(index, "USER_MESSAGE", content="x") for index in range(1_000)],
                _event(1_000, "TERMINAL", terminal_state="SUCCESS"),
            ]
        )
        self.assert_rejected(too_many_events)
        line_too_large = _canonical(
            _trace(
                [
                    _event(0, "USER_MESSAGE", content="x"),
                    *[
                        _event(
                            index,
                            "SYSTEM_VISIBLE_MESSAGE",
                            content="x" * 1_100,
                        )
                        for index in range(1, 999)
                    ],
                    _event(999, "TERMINAL", terminal_state="SUCCESS"),
                ]
            )
        )
        self.assertGreater(len(line_too_large), 1_048_576)
        self.assert_rejected(line_too_large)

    def test_tool_result_and_terminal_companion_fields_are_exact(self) -> None:
        user = _event(0, "USER_MESSAGE", content="Synthetic request")
        call = _event(
            1,
            "TOOL_CALL",
            call_id="call-1",
            tool_name="synthetic_tool",
            arguments={},
        )
        terminal = _event(3, "TERMINAL", terminal_state="SUCCESS")
        accepted = (
            [
                user,
                call,
                _event(
                    2,
                    "TOOL_RESULT",
                    call_id="call-1",
                    result_state="SUCCEEDED",
                    result=None,
                ),
                terminal,
            ],
            [
                user,
                call,
                _event(
                    2,
                    "TOOL_RESULT",
                    call_id="call-1",
                    result_state="ERROR",
                    error_code="NOT_FOUND",
                ),
                terminal,
            ],
            [_event(0, "TERMINAL", terminal_state="SUCCESS")],
            [_event(0, "TERMINAL", terminal_state="ERROR", reason_code="FAILED")],
            [_event(0, "TERMINAL", terminal_state="ABORTED", reason_code="STOPPED")],
        )
        for events in accepted:
            with self.subTest(events=events):
                self.assert_accepted(_trace(copy.deepcopy(events)))

        rejected = (
            [
                user,
                call,
                _event(2, "TOOL_RESULT", call_id="call-1", result_state="SUCCEEDED"),
                terminal,
            ],
            [
                user,
                call,
                _event(
                    2,
                    "TOOL_RESULT",
                    call_id="call-1",
                    result_state="SUCCEEDED",
                    result={},
                    error_code="BAD",
                ),
                terminal,
            ],
            [
                user,
                call,
                _event(
                    2, "TOOL_RESULT", call_id="call-1", result_state="ERROR", result={}
                ),
                terminal,
            ],
            [
                user,
                call,
                _event(
                    2,
                    "TOOL_RESULT",
                    call_id="call-1",
                    result_state="ERROR",
                    error_code="lowercase",
                ),
                terminal,
            ],
            [_event(0, "TERMINAL", terminal_state="SUCCESS", reason_code="EXTRA")],
            [_event(0, "TERMINAL", terminal_state="ERROR")],
            [_event(0, "TERMINAL", terminal_state="UNKNOWN")],
            [_event(0, "TERMINAL", terminal_state=[])],
            [_event(0, "TERMINAL", terminal_state={})],
        )
        for events in rejected:
            with self.subTest(events=events):
                self.assert_rejected(_trace(copy.deepcopy(events)))

    def test_jsonl_line_privacy_and_discriminator_boundaries_refuse_safely(
        self,
    ) -> None:
        first = _trace()
        second = copy.deepcopy(first)
        second["trace_id"] = "synthetic-second"
        second["source_trace_id"] = "fixture/synthetic-second"

        cr_only = (
            _canonical(first).rstrip(b"\n")
            + b"\r"
            + _canonical(second).rstrip(b"\n")
            + b"\r"
        )
        second["privacy_class"] = "SYNTHETIC"
        invalid_privacy = copy.deepcopy(first)
        invalid_privacy["privacy_class"] = []
        invalid_kind = copy.deepcopy(first)
        invalid_kind["events"][0]["event_kind"] = []
        cases: tuple[tuple[str, JsonObject | bytes, str], ...] = (
            ("CR-only record separators", cr_only, "PREVIEWTRACE_INVALID"),
            (
                "mixed corpus privacy classes",
                _canonical(first) + _canonical(second),
                "PRIVACY_CLASS_MISMATCH",
            ),
            (
                "unhashable privacy discriminator",
                invalid_privacy,
                "PREVIEWTRACE_INVALID",
            ),
            ("unhashable event discriminator", invalid_kind, "PREVIEWTRACE_INVALID"),
        )
        for label, payload, reason_code in cases:
            with self.subTest(label=label):
                self.assert_rejected(payload, reason_code=reason_code)

    def test_relationships_final_and_terminal_multiplicity_are_exact(self) -> None:
        invalid_events = (
            [
                _event(1, "USER_MESSAGE", content="wrong sequence"),
                _event(1, "TERMINAL", terminal_state="SUCCESS"),
            ],
            [
                _event(0, "USER_MESSAGE", content="Synthetic request"),
                _event(
                    1,
                    "TOOL_RESULT",
                    call_id="missing",
                    result_state="SUCCEEDED",
                    result={},
                ),
                _event(2, "TERMINAL", terminal_state="SUCCESS"),
            ],
            [
                _event(0, "USER_MESSAGE", content="Synthetic request"),
                _event(1, "TOOL_CALL", call_id="same", tool_name="tool", arguments={}),
                _event(2, "TOOL_CALL", call_id="same", tool_name="tool", arguments={}),
                _event(3, "TERMINAL", terminal_state="SUCCESS"),
            ],
            [
                _event(0, "USER_MESSAGE", content="Synthetic request"),
                _event(1, "TOOL_CALL", call_id="same", tool_name="tool", arguments={}),
                _event(
                    2,
                    "TOOL_RESULT",
                    call_id="same",
                    result_state="SUCCEEDED",
                    result={},
                ),
                _event(
                    3,
                    "TOOL_RESULT",
                    call_id="same",
                    result_state="SUCCEEDED",
                    result={},
                ),
                _event(4, "TERMINAL", terminal_state="SUCCESS"),
            ],
            [
                _event(0, "USER_MESSAGE", content="Synthetic request"),
                _event(1, "ASSISTANT_MESSAGE", content="one", is_final=True),
                _event(2, "ASSISTANT_MESSAGE", content="two", is_final=True),
                _event(3, "TERMINAL", terminal_state="SUCCESS"),
            ],
            [
                _event(0, "USER_MESSAGE", content="Synthetic request"),
                _event(1, "TERMINAL", terminal_state="SUCCESS"),
                _event(2, "TERMINAL", terminal_state="SUCCESS"),
            ],
            [
                _event(0, "USER_MESSAGE", content="Synthetic request"),
                _event(1, "TERMINAL", terminal_state="SUCCESS"),
                _event(2, "ASSISTANT_MESSAGE", content="after", is_final=False),
            ],
        )
        for events in invalid_events:
            with self.subTest(events=events):
                self.assert_rejected(_trace(copy.deepcopy(events)))

        self.assert_accepted(
            _trace([_event(0, "ASSISTANT_MESSAGE", content="", is_final=False)])
        )
        self.assert_accepted(
            _trace(
                [
                    _event(0, "USER_MESSAGE", content="Synthetic request"),
                    _event(1, "ASSISTANT_MESSAGE", content="Response", is_final=True),
                ]
            )
        )
        self.assert_accepted(
            _trace(
                [
                    _event(0, "SYSTEM_VISIBLE_MESSAGE", content="System context"),
                    _event(1, "TERMINAL", terminal_state="SUCCESS"),
                ]
            )
        )


class StructuralKeyPrivacyTests(unittest.TestCase):
    def test_dynamic_object_keys_are_redacted_without_hiding_known_structure(
        self,
    ) -> None:
        source = FIXTURES / "raw_dynamic_key.jsonl"
        completed = _run(
            "inspect",
            "--source",
            os.fspath(source),
            "--confirm-authorized-traces",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = _terminal_json(completed)
        serialized = json.dumps(result, sort_keys=True)
        for known_name in ("messages", "role", "content", "metadata", "tenant"):
            self.assertIn(known_name, serialized)
        self.assertNotIn("private-customer@example.invalid", serialized)
        self.assertNotIn("ORD-SYNTH-DYNAMIC", serialized)
        self.assertNotIn("synthetic-value", serialized)
        self.assertGreaterEqual(result.get("redacted_key_count", 0), 2)


class PublicContractReferenceTests(unittest.TestCase):
    def test_reference_exposes_the_complete_closed_mapping(self) -> None:
        text = REFERENCE.read_text(encoding="utf-8")
        normalized = " ".join(text.lower().split())
        searchable = normalized.replace("`", "")
        requirements = (
            ("^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$", text),
            ("contract_kind", searchable),
            ("schema_version", searchable),
            ("privacy_class", searchable),
            ("trace_id", searchable),
            ("source_trace_id", searchable),
            ("events", searchable),
            ("512 utf-8 bytes", searchable),
            ("1,000 events", searchable),
            ("65,536 utf-8 bytes", searchable),
            ("result must follow its matching call", searchable),
            ("at most one result per call", searchable),
            ("at most one assistant message may set is_final: true", searchable),
        )
        for token, haystack in requirements:
            with self.subTest(token=token):
                self.assertIn(token, haystack)
        self.assertTrue(
            "user and terminal events are optional" in searchable
            or "neither a user event nor a terminal event is mandatory" in searchable
        )
        self.assertTrue(
            "terminal may appear at most once and must be last" in searchable
            or "at most one terminal may appear, and if present it is last"
            in searchable
        )

        expected_rows = {
            "SYSTEM_VISIBLE_MESSAGE": {"sequence", "event_kind", "content"},
            "USER_MESSAGE": {"sequence", "event_kind", "content"},
            "ASSISTANT_MESSAGE": {
                "sequence",
                "event_kind",
                "content",
                "is_final",
            },
            "TOOL_CALL": {
                "sequence",
                "event_kind",
                "call_id",
                "tool_name",
                "arguments",
            },
            "TOOL_RESULT SUCCEEDED": {
                "sequence",
                "event_kind",
                "call_id",
                "result_state",
                "result",
            },
            "TOOL_RESULT ERROR": {
                "sequence",
                "event_kind",
                "call_id",
                "result_state",
                "error_code",
            },
            "TERMINAL SUCCESS": {"sequence", "event_kind", "terminal_state"},
            "TERMINAL ERROR/ABORTED": {
                "sequence",
                "event_kind",
                "terminal_state",
                "reason_code",
            },
        }
        table_rows: dict[str, set[str]] = {}
        for line in text.splitlines():
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 2:
                continue
            label = cells[0].replace("`", "")
            fields = {
                field.strip().strip("`")
                for field in cells[1].split(",")
                if field.strip()
            }
            table_rows[label] = fields
        self.assertEqual(
            {label: table_rows.get(label) for label in expected_rows},
            expected_rows,
        )


if __name__ == "__main__":
    unittest.main()
