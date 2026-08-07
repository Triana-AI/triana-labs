"""Black-box contract for the local PreviewTrace redacted projection."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from triana_labs.behavior_map import redact_preview_traces
from triana_labs.behavior_map import redaction as redaction_module
from triana_labs.contracts.traces import validate_trace

DIRECT_VALUES = (
    "repeat@example.com",
    "https://private.example/path",
    "203.0.113.42",
    "+1 (415) 555-0123",
    "415-555-0123",
    "ORD-ABCDE",
    "@secret_handle",
    "560001",
    "987654321",
    "Alice Example",
    "10 Secret Lane",
)


def _canonical(value: Any, *, lf: bool = False) -> bytes:
    payload = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return payload + (b"\n" if lf else b"")


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _event(sequence: int, event_kind: str, **values: Any) -> dict[str, Any]:
    return {"sequence": sequence, "event_kind": event_kind, **values}


def _trace(
    trace_id: str,
    source_trace_id: str,
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": "CUSTOMER_AUTHORIZED_TRACE_DATA",
        "trace_id": trace_id,
        "source_trace_id": source_trace_id,
        "events": events,
    }


def _sensitive_trace(trace_id: str) -> dict[str, Any]:
    call_id = "call-repeat@example.com"
    return _trace(
        trace_id,
        f"source-{trace_id}",
        [
            _event(
                0,
                "SYSTEM_VISIBLE_MESSAGE",
                content="Support repeat@example.com at https://private.example/path.",
            ),
            _event(
                1,
                "USER_MESSAGE",
                content="Contact repeat@example.com, again repeat@example.com.",
            ),
            _event(
                2,
                "TOOL_CALL",
                call_id=call_id,
                tool_name="lookup-repeat@example.com",
                arguments={
                    "owner": "repeat@example.com",
                    "network": {"ip": "203.0.113.42"},
                    "contacts": ["+1 (415) 555-0123", "@secret_handle"],
                    "ordinary_phone": "415-555-0123",
                    "order": "order id ORD-ABCDE",
                    "postal_code": "560001",
                    "long_number": "987654321",
                    "person": "my name is Alice Example",
                    "address": "delivery address is 10 Secret Lane.",
                },
            ),
            _event(
                3,
                "TOOL_RESULT",
                call_id=call_id,
                result_state="SUCCEEDED",
                result={
                    "owner": "repeat@example.com",
                    "nested": [
                        {
                            "error_message": (
                                "Could not notify repeat@example.com at "
                                "https://private.example/path"
                            )
                        }
                    ],
                },
            ),
            _event(
                4,
                "ASSISTANT_MESSAGE",
                content="I could not notify repeat@example.com.",
                is_final=True,
            ),
            _event(5, "TERMINAL", terminal_state="SUCCESS"),
        ],
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> bytes:
    payload = b"".join(_canonical(row, lf=True) for row in rows)
    path.write_bytes(payload)
    return payload


def _run_redact(
    source: Path,
    output: Path,
    audit: Path,
) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    for key in tuple(environment):
        if any(token in key.upper() for token in ("API_KEY", "AZURE", "OPENAI")):
            environment.pop(key)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "triana_labs",
            "behavior-map",
            "redact",
            "--input",
            os.fspath(source),
            "--output",
            os.fspath(output),
            "--audit",
            os.fspath(audit),
        ],
        check=False,
        capture_output=True,
        env=environment,
        timeout=30,
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in _walk_strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in _walk_strings(child)]
    return []


def _machine_result(completed: subprocess.CompletedProcess[bytes]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for stream in (completed.stdout, completed.stderr):
        for line in stream.splitlines():
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                records.append(value)
    assert records, (completed.stdout, completed.stderr)
    return records[-1]


def test_redacts_every_event_string_surface_with_stable_placeholders(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.jsonl"
    source_bytes = _write_jsonl(
        source,
        [_sensitive_trace("conversation-one"), _sensitive_trace("conversation-two")],
    )
    runs = [
        (tmp_path / "first.jsonl", tmp_path / "first.audit.json"),
        (tmp_path / "second.jsonl", tmp_path / "second.audit.json"),
    ]

    for output, audit in runs:
        completed = _run_redact(source, output, audit)
        assert completed.returncode == 0, (completed.stdout, completed.stderr)
        assert output.is_file() and audit.is_file()
        assert source.read_bytes() == source_bytes
        result = _machine_result(completed)
        assert result.get("command") == "behavior-map.redact"
        assert result.get("outcome") == "COMPLETED"

    assert runs[0][0].read_bytes() == runs[1][0].read_bytes()
    assert runs[0][1].read_bytes() == runs[1][1].read_bytes()
    projected = _read_jsonl(runs[0][0])
    original = _read_jsonl(source)
    assert len(projected) == len(original) == 2

    for before, after in zip(original, projected, strict=True):
        assert after["trace_id"] == before["trace_id"]
        assert after["source_trace_id"] == before["source_trace_id"]
        assert after["contract_kind"] == before["contract_kind"]
        assert after["schema_version"] == before["schema_version"]
        assert after["privacy_class"] == before["privacy_class"]
        assert len(after["events"]) == len(before["events"])
        assert [row["sequence"] for row in after["events"]] == list(range(6))
        assert [row["event_kind"] for row in after["events"]] == [
            row["event_kind"] for row in before["events"]
        ]
        assert validate_trace(after).value == after

        call, result = after["events"][2:4]
        assert call["call_id"] == result["call_id"]
        assert call["call_id"] != before["events"][2]["call_id"]
        assert call["tool_name"] != before["events"][2]["tool_name"]
        message = after["events"][1]["content"]
        repeated = re.fullmatch(r"Contact (.+), again (.+)\.", message)
        assert repeated is not None and repeated.group(1) == repeated.group(2)
        assert call["arguments"]["owner"] == repeated.group(1)
        assert result["result"]["owner"] == repeated.group(1)

    projected_text = "\n".join(_walk_strings(projected))
    assert all(value not in projected_text for value in DIRECT_VALUES)

    audit = json.loads(runs[0][1].read_bytes())
    assert audit["artifact_kind"] == "behavior_map_redaction_audit_v0"
    assert audit["schema_version"] == 0
    assert audit["source_sha256"] == _sha256(source_bytes)
    assert audit["output_sha256"] == _sha256(runs[0][0].read_bytes())
    assert audit["input_trace_count"] == audit["output_trace_count"] == 2
    assert audit["input_event_count"] == audit["output_event_count"] == 12
    assert all(
        int(audit["category_counts"].get(category, 0)) > 0
        for category in (
            "ADDRESS",
            "EMAIL",
            "HANDLE",
            "IP",
            "LONG_NUMBER",
            "ORDER_ID",
            "PERSON",
            "PHONE",
            "POSTAL_CODE",
            "URL",
        )
    )
    assert not audit.get("residual_detector_counts")
    audit_text = runs[0][1].read_text()
    assert all(value not in audit_text for value in DIRECT_VALUES)
    assert "complete pii removal" not in audit_text.casefold()


@pytest.mark.parametrize(
    ("payload", "reason_code"),
    [
        (b'{"contract_kind":"preview_trace"\n', "REDACTION_INPUT_INVALID"),
        (
            _canonical(
                _trace(
                    "identity-residual",
                    "repeat@example.com",
                    [_event(0, "USER_MESSAGE", content="A harmless request.")],
                ),
                lf=True,
            ),
            "REDACTION_RESIDUAL_IDENTIFIER",
        ),
    ],
)
def test_invalid_or_identity_residual_refuses_before_atomic_publication(
    tmp_path: Path,
    payload: bytes,
    reason_code: str,
) -> None:
    source = tmp_path / "source.jsonl"
    source.write_bytes(payload)
    output = tmp_path / "redacted.jsonl"
    audit = tmp_path / "redaction.audit.json"

    completed = _run_redact(source, output, audit)

    assert completed.returncode != 0
    assert source.read_bytes() == payload
    assert not output.exists()
    assert not audit.exists()
    result = _machine_result(completed)
    assert result.get("command") == "behavior-map.redact"
    assert result.get("outcome") == "REJECTED"
    assert result.get("reason_code") == reason_code


def test_person_placeholder_does_not_self_match_residual_person_detector(
    tmp_path: Path,
) -> None:
    phrase = "My name is Alice and I Need Help Today"
    source = tmp_path / "source.jsonl"
    source_bytes = _write_jsonl(
        source,
        [
            _trace(
                "person-content",
                "source-person-content",
                [_event(0, "USER_MESSAGE", content=phrase)],
            )
        ],
    )
    output = tmp_path / "redacted.jsonl"
    audit_path = tmp_path / "redaction.audit.json"

    completed = _run_redact(source, output, audit_path)

    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert source.read_bytes() == source_bytes
    projected = _read_jsonl(output)[0]
    projected_content = projected["events"][0]["content"]
    assert "Alice" not in projected_content
    assert "REDACTED_PERSON" in projected_content
    audit = json.loads(audit_path.read_bytes())
    assert not audit.get("residual_detector_counts")

    identity_source = tmp_path / "identity-source.jsonl"
    identity_payload = _write_jsonl(
        identity_source,
        [
            _trace(
                "person-identity",
                phrase,
                [_event(0, "USER_MESSAGE", content="A harmless request.")],
            )
        ],
    )
    identity_output = tmp_path / "identity-redacted.jsonl"
    identity_audit = tmp_path / "identity-redaction.audit.json"

    refused = _run_redact(identity_source, identity_output, identity_audit)

    assert refused.returncode != 0
    assert identity_source.read_bytes() == identity_payload
    assert not identity_output.exists() and not identity_audit.exists()
    result = _machine_result(refused)
    assert result.get("command") == "behavior-map.redact"
    assert result.get("outcome") == "REJECTED"
    assert result.get("reason_code") == "REDACTION_RESIDUAL_IDENTIFIER"


def test_structured_langsmith_uuid_identity_is_preserved_not_scanned_as_free_text(
    tmp_path: Path,
) -> None:
    trace_id = "langsmith-session-1234567890abcdef1234567890abcdef"
    residual_trigger_trace_id = "langsmith-session-abcdef123456abcdef123456abcdef12"
    source_trace_id = "langsmith://session/12345678-1234-1234-1234-123456789012"
    placeholder_source_trace_id = (
        "langsmith://session/<phone_redacted>-1234-1234-123456789012"
    )
    source = tmp_path / "source.jsonl"
    source_bytes = _write_jsonl(
        source,
        [
            _trace(
                trace_id,
                source_trace_id,
                [_event(0, "USER_MESSAGE", content="A harmless request.")],
            ),
            _trace(
                residual_trigger_trace_id,
                "langsmith://session/abcdef12-1234-1234-1234-abcdef123456",
                [_event(0, "USER_MESSAGE", content="Another harmless request.")],
            ),
            _trace(
                "langsmith-session-abcdefabcdefabcdefabcdefabcdefab",
                placeholder_source_trace_id,
                [_event(0, "USER_MESSAGE", content="A third harmless request.")],
            ),
        ],
    )
    output = tmp_path / "redacted.jsonl"
    audit_path = tmp_path / "redaction.audit.json"

    completed = _run_redact(source, output, audit_path)

    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert source.read_bytes() == source_bytes
    projected = _read_jsonl(output)
    assert [row["trace_id"] for row in projected] == [
        trace_id,
        residual_trigger_trace_id,
        "langsmith-session-abcdefabcdefabcdefabcdefabcdefab",
    ]
    assert [row["source_trace_id"] for row in projected] == [
        source_trace_id,
        "langsmith://session/abcdef12-1234-1234-1234-abcdef123456",
        placeholder_source_trace_id,
    ]
    assert all(validate_trace(row).value == row for row in projected)
    audit = json.loads(audit_path.read_bytes())
    assert not audit.get("residual_detector_counts")


def test_blitz_identifiers_are_stably_redacted_across_recursive_event_strings(
    tmp_path: Path,
) -> None:
    identifiers = ("GS123456789", "NM234567890", "NN345678901")
    trace_id = "blitz-conversation-GS123456789"
    source_trace_id = "blitz://trace/NM234567890"
    existing_placeholder = "REDACTED_BLITZ_IDENTIFIER_77"
    ordinary_alphanumeric_id = "taskGS123456789suffix"
    source = tmp_path / "source.jsonl"
    _write_jsonl(
        source,
        [
            _trace(
                trace_id,
                source_trace_id,
                [
                    _event(
                        0,
                        "USER_MESSAGE",
                        content=(
                            f"Find {identifiers[0]}, then {identifiers[0]}; keep "
                            f"{existing_placeholder} and {ordinary_alphanumeric_id}."
                        ),
                    ),
                    _event(
                        1,
                        "TOOL_CALL",
                        call_id=identifiers[1],
                        tool_name="lookup_blitz_record",
                        arguments={
                            identifiers[2]: {
                                "record": identifiers[0],
                                "nested": [identifiers[1], {"value": identifiers[2]}],
                            }
                        },
                    ),
                    _event(
                        2,
                        "TOOL_RESULT",
                        call_id=identifiers[1],
                        result_state="SUCCEEDED",
                        result={"records": list(identifiers)},
                    ),
                    _event(3, "TERMINAL", terminal_state="SUCCESS"),
                ],
            )
        ],
    )
    output = tmp_path / "redacted.jsonl"
    audit_path = tmp_path / "redaction.audit.json"

    completed = _run_redact(source, output, audit_path)

    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    projected = _read_jsonl(output)[0]
    assert projected["trace_id"] == trace_id
    assert projected["source_trace_id"] == source_trace_id
    event_text = json.dumps(projected["events"], sort_keys=True)
    assert all(
        re.search(
            rf"(?<![A-Za-z0-9]){re.escape(identifier)}(?![A-Za-z0-9])",
            event_text,
        )
        is None
        for identifier in identifiers
    )
    assert existing_placeholder in event_text
    assert ordinary_alphanumeric_id in event_text
    tokens = re.findall(r"REDACTED_BLITZ_IDENTIFIER_\d+", event_text)
    assert len(set(tokens) - {existing_placeholder}) == len(identifiers)
    user_content = projected["events"][0]["content"]
    repeated = re.search(
        r"Find (REDACTED_BLITZ_IDENTIFIER_\d+), then (REDACTED_BLITZ_IDENTIFIER_\d+)",
        user_content,
    )
    assert repeated is not None and repeated.group(1) == repeated.group(2)
    call, result = projected["events"][1:3]
    assert call["call_id"] == result["call_id"]
    assert validate_trace(projected).value == projected
    audit = json.loads(audit_path.read_bytes())
    assert audit["category_counts"]["BLITZ_IDENTIFIER"] >= 9
    assert not audit.get("residual_detector_counts")


def test_blitz_identifier_residual_validation_is_independent_of_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identifier = "GS123456789"
    source = tmp_path / "source.jsonl"
    _write_jsonl(
        source,
        [
            _trace(
                "blitz-residual",
                "source-blitz-residual",
                [_event(0, "USER_MESSAGE", content=f"Inspect {identifier}.")],
            )
        ],
    )
    output = tmp_path / "redacted.jsonl"
    audit = tmp_path / "redaction.audit.json"
    redactor = redaction_module._Redactor
    monkeypatch.setattr(redactor, "text", lambda _self, value: value)

    with pytest.raises(redaction_module.RedactionFailure) as failure:
        redact_preview_traces(source, output, audit)

    assert failure.value.reason_code == "REDACTION_RESIDUAL_IDENTIFIER"
    assert not output.exists() and not audit.exists()


def test_street_addresses_without_address_keyword_are_stably_redacted_recursively(
    tmp_path: Path,
) -> None:
    addresses = (
        "House 14, Shanti Colony",
        "Flat 9B, Lake View Apartment",
        "Plot 22, Rose Nagar",
        "17 Secret Lane",
        "44 Market Road",
        "8 Park Street",
        "House 5, Sector 21",
        "Flat 3, Sunrise Building",
        "Plot 7, Lotus Society",
    )
    existing_placeholder = "REDACTED_ADDRESS_77"
    ordinary_prose = (
        "Please address the issue, plot the chart, keep pricing flat, build trust, "
        "improve society, review sector performance, and take the road ahead."
    )
    trace_id = "blitz-address-structural-id"
    source_trace_id = f"source-only::{addresses[0]}"
    source = tmp_path / "source.jsonl"
    _write_jsonl(
        source,
        [
            _trace(
                trace_id,
                source_trace_id,
                [
                    _event(
                        0,
                        "USER_MESSAGE",
                        content=(
                            f"Deliver to {addresses[0]}, again {addresses[0]}. "
                            f"Keep {existing_placeholder}. {ordinary_prose}"
                        ),
                    ),
                    _event(
                        1,
                        "TOOL_CALL",
                        call_id="address-lookup",
                        tool_name="lookup_delivery_location",
                        arguments={
                            addresses[1]: {
                                "primary": addresses[0],
                                "alternates": list(addresses[2:6]),
                                "nested": {
                                    "sector": addresses[6],
                                    "building": addresses[7],
                                    "society": addresses[8],
                                },
                            }
                        },
                    ),
                    _event(
                        2,
                        "TOOL_RESULT",
                        call_id="address-lookup",
                        result_state="SUCCEEDED",
                        result={"locations": list(addresses)},
                    ),
                    _event(3, "TERMINAL", terminal_state="SUCCESS"),
                ],
            )
        ],
    )
    output = tmp_path / "redacted.jsonl"
    audit_path = tmp_path / "redaction.audit.json"

    completed = _run_redact(source, output, audit_path)

    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    projected = _read_jsonl(output)[0]
    assert projected["trace_id"] == trace_id
    assert projected["source_trace_id"] == source_trace_id
    event_text = json.dumps(projected["events"], sort_keys=True)
    assert all(address not in event_text for address in addresses)
    assert existing_placeholder in event_text
    assert ordinary_prose in event_text
    tokens = set(re.findall(r"REDACTED_ADDRESS_\d+", event_text))
    assert len(tokens - {existing_placeholder}) == len(addresses)
    repeated = re.search(
        r"Deliver to (REDACTED_ADDRESS_\d+), again (REDACTED_ADDRESS_\d+)",
        projected["events"][0]["content"],
    )
    assert repeated is not None and repeated.group(1) == repeated.group(2)
    assert validate_trace(projected).value == projected
    audit = json.loads(audit_path.read_bytes())
    assert audit["category_counts"]["ADDRESS"] >= len(addresses) + 2
    assert not audit.get("residual_detector_counts")


def test_complete_address_span_precedes_narrower_numeric_and_person_redaction(
    tmp_path: Path,
) -> None:
    addresses = (
        "House no. 42, Green Colony 560001",
        "Flat number 9B Lake View Apartment 987654321",
        "Plot #17, Rose Nagar 110001",
        "House 21 Alice Street 400001",
    )
    ordinary_prose = (
        "House number 42 is the answer; plot number 17 on the chart and keep the "
        "pricing flat."
    )
    source = tmp_path / "source.jsonl"
    _write_jsonl(
        source,
        [
            _trace(
                "complete-address-span",
                "source-complete-address-span",
                [
                    _event(
                        0,
                        "USER_MESSAGE",
                        content=f"Ship to {addresses[0]}. {ordinary_prose}",
                    ),
                    _event(
                        1,
                        "TOOL_CALL",
                        call_id="complete-address-lookup",
                        tool_name="lookup_delivery_location",
                        arguments={
                            "addresses": list(addresses),
                            "ordinary_prose": ordinary_prose,
                        },
                    ),
                    _event(
                        2,
                        "TOOL_RESULT",
                        call_id="complete-address-lookup",
                        result_state="SUCCEEDED",
                        result={"addresses": list(addresses)},
                    ),
                    _event(3, "TERMINAL", terminal_state="SUCCESS"),
                ],
            )
        ],
    )
    output = tmp_path / "redacted.jsonl"
    audit_path = tmp_path / "redaction.audit.json"

    completed = _run_redact(source, output, audit_path)

    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    projected = _read_jsonl(output)[0]
    user_content = projected["events"][0]["content"]
    projected_arguments = projected["events"][1]["arguments"]
    projected_result = projected["events"][2]["result"]
    argument_tokens = projected_arguments["addresses"]
    result_tokens = projected_result["addresses"]
    assert argument_tokens == result_tokens
    assert len(set(argument_tokens)) == len(addresses)
    assert all(
        re.fullmatch(r"REDACTED_ADDRESS_\d+", token) for token in argument_tokens
    )
    assert user_content == f"Ship to {argument_tokens[0]}. {ordinary_prose}"
    assert projected_arguments["ordinary_prose"] == ordinary_prose
    assert all(address not in json.dumps(projected["events"]) for address in addresses)
    audit = json.loads(audit_path.read_bytes())
    assert audit["category_counts"]["ADDRESS"] >= len(addresses) * 2 + 1
    assert int(audit["category_counts"].get("POSTAL_CODE", 0)) == 0
    assert int(audit["category_counts"].get("LONG_NUMBER", 0)) == 0
    assert int(audit["category_counts"].get("PERSON", 0)) == 0
    assert not audit.get("residual_detector_counts")


def test_numbered_and_landmark_locations_are_stable_whole_span_redactions(
    tmp_path: Path,
) -> None:
    locations = (
        "27 Green Park Street",
        "18 Lotus Sector 4",
        "21 Sunrise Phase 2",
        "8 River View Lane",
        "Near City Hospital",
        "Opposite Central Mall",
        "Behind Sunrise School",
    )
    ordinary_prose = (
        "The work is near completion; opposite opinions remain; delivery is behind "
        "schedule; review the phase of the project and the sector metric."
    )
    trace_id = "numbered-landmark-location"
    source_trace_id = "source-numbered-landmark-location"
    source = tmp_path / "source.jsonl"
    _write_jsonl(
        source,
        [
            _trace(
                trace_id,
                source_trace_id,
                [
                    _event(
                        0,
                        "USER_MESSAGE",
                        content=(
                            f"Route to {locations[0]}, then {locations[4]}. "
                            f"{ordinary_prose}"
                        ),
                    ),
                    _event(
                        1,
                        "TOOL_CALL",
                        call_id="numbered-landmark-lookup",
                        tool_name="lookup_delivery_location",
                        arguments={
                            "locations": list(locations),
                            "ordinary_prose": ordinary_prose,
                        },
                    ),
                    _event(
                        2,
                        "TOOL_RESULT",
                        call_id="numbered-landmark-lookup",
                        result_state="SUCCEEDED",
                        result={"locations": list(locations)},
                    ),
                    _event(3, "TERMINAL", terminal_state="SUCCESS"),
                ],
            )
        ],
    )
    output = tmp_path / "redacted.jsonl"
    audit_path = tmp_path / "redaction.audit.json"

    completed = _run_redact(source, output, audit_path)

    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    projected = _read_jsonl(output)[0]
    assert projected["trace_id"] == trace_id
    assert projected["source_trace_id"] == source_trace_id
    arguments = projected["events"][1]["arguments"]
    result = projected["events"][2]["result"]
    location_tokens = arguments["locations"]
    assert location_tokens == result["locations"]
    assert len(set(location_tokens)) == len(locations)
    assert all(
        re.fullmatch(r"REDACTED_ADDRESS_\d+", token) for token in location_tokens
    )
    assert projected["events"][0]["content"] == (
        f"Route to {location_tokens[0]}, then {location_tokens[4]}. {ordinary_prose}"
    )
    assert arguments["ordinary_prose"] == ordinary_prose
    assert all(
        location not in json.dumps(projected["events"]) for location in locations
    )
    assert validate_trace(projected).value == projected
    audit = json.loads(audit_path.read_bytes())
    assert audit["category_counts"]["ADDRESS"] >= len(locations) * 2 + 2
    assert not audit.get("residual_detector_counts")


@pytest.mark.parametrize(
    "location",
    ["18 Lotus Sector 4", "Opposite Central Mall"],
    ids=("numbered-named-sector", "relative-named-landmark"),
)
def test_numbered_and_landmark_residuals_refuse_when_replacement_is_bypassed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    location: str,
) -> None:
    source = tmp_path / "source.jsonl"
    _write_jsonl(
        source,
        [
            _trace(
                "location-residual",
                "source-location-residual",
                [
                    _event(
                        0,
                        "TOOL_CALL",
                        call_id="location-residual-check",
                        tool_name="inspect_location",
                        arguments={"location": location},
                    ),
                    _event(
                        1,
                        "TOOL_RESULT",
                        call_id="location-residual-check",
                        result_state="SUCCEEDED",
                        result={"status": "checked"},
                    ),
                    _event(2, "TERMINAL", terminal_state="SUCCESS"),
                ],
            )
        ],
    )
    output = tmp_path / "redacted.jsonl"
    audit = tmp_path / "redaction.audit.json"
    monkeypatch.setattr(redaction_module._Redactor, "text", lambda _self, value: value)

    with pytest.raises(redaction_module.RedactionFailure) as failure:
        redact_preview_traces(source, output, audit)

    assert failure.value.reason_code == "REDACTION_RESIDUAL_IDENTIFIER"
    assert not output.exists() and not audit.exists()


def test_contextual_and_structured_order_identifiers_are_stably_redacted(
    tmp_path: Path,
) -> None:
    keyed_identifiers = {
        "order_id": "AB12CD3456",
        "tracking": "TRK8Q2W9E7",
        "awb": "AWB7M4N8Q2",
        "shipment_id": "SHP4T8R2K6",
        "reference": "REF7Y3U9I5",
        "ticket": "TKT5P8L2D4",
        "id": "IDC4V7B9N2",
    }
    contextual_identifiers = ("ORD9Q2W7E4", "DLV8R3T6Y2", "TRK4P7L2M9")
    unrelated = ("MODELX12345", "VERSION2BUILD7", "CUSTOMERSEGMENT9")
    existing_placeholder = "REDACTED_ORDER_ID_77"
    trace_id = "structural-order-AB12CD3456"
    source_trace_id = "source-structural-tracking-TRK8Q2W9E7"
    source = tmp_path / "source.jsonl"
    _write_jsonl(
        source,
        [
            _trace(
                trace_id,
                source_trace_id,
                [
                    _event(
                        0,
                        "USER_MESSAGE",
                        content=(
                            f"Check order {contextual_identifiers[0]}, delivery "
                            f"{contextual_identifiers[1]}, and tracking number "
                            f"{contextual_identifiers[2]}. Keep {existing_placeholder}; "
                            f"ordinary tokens are {', '.join(unrelated)}."
                        ),
                    ),
                    _event(
                        1,
                        "TOOL_CALL",
                        call_id="identifier-lookup",
                        tool_name="lookup_fulfilment_records",
                        arguments={
                            **keyed_identifiers,
                            "nested": {
                                "order": keyed_identifiers["order_id"],
                                "records": [
                                    {"tracking_id": keyed_identifiers["tracking"]},
                                    {"ticket_id": keyed_identifiers["ticket"]},
                                ],
                            },
                        },
                    ),
                    _event(
                        2,
                        "TOOL_RESULT",
                        call_id="identifier-lookup",
                        result_state="SUCCEEDED",
                        result={"records": keyed_identifiers},
                    ),
                    _event(3, "TERMINAL", terminal_state="SUCCESS"),
                ],
            )
        ],
    )
    output = tmp_path / "redacted.jsonl"
    audit_path = tmp_path / "redaction.audit.json"

    completed = _run_redact(source, output, audit_path)

    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    projected = _read_jsonl(output)[0]
    assert projected["trace_id"] == trace_id
    assert projected["source_trace_id"] == source_trace_id
    event_text = json.dumps(projected["events"], sort_keys=True)
    for identifier in (*keyed_identifiers.values(), *contextual_identifiers):
        assert identifier not in event_text
    assert existing_placeholder in event_text
    assert all(token in event_text for token in unrelated)
    arguments = projected["events"][1]["arguments"]
    assert arguments["order_id"] == arguments["nested"]["order"]
    assert arguments["tracking"] == arguments["nested"]["records"][0]["tracking_id"]
    assert arguments["ticket"] == arguments["nested"]["records"][1]["ticket_id"]
    assert all(
        re.fullmatch(r"REDACTED_ORDER_ID_\d+", arguments[key])
        for key in keyed_identifiers
    )
    assert validate_trace(projected).value == projected
    audit = json.loads(audit_path.read_bytes())
    assert audit["category_counts"]["ORDER_ID"] >= len(keyed_identifiers) + 3
    assert not audit.get("residual_detector_counts")


@pytest.mark.parametrize(
    "arguments",
    [
        {"note": "Leave the parcel at House 14, Shanti Colony"},
        {"order_id": "AB12CD3456"},
        {"note": "Check tracking number TRK8Q2W9E7"},
    ],
    ids=("street-address", "structured-order-id", "contextual-tracking-id"),
)
def test_address_and_order_identifier_residual_checks_survive_replacement_bypass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arguments: dict[str, str],
) -> None:
    source = tmp_path / "source.jsonl"
    _write_jsonl(
        source,
        [
            _trace(
                "privacy-residual",
                "source-privacy-residual",
                [
                    _event(
                        0,
                        "TOOL_CALL",
                        call_id="privacy-check",
                        tool_name="inspect_record",
                        arguments=arguments,
                    ),
                    _event(
                        1,
                        "TOOL_RESULT",
                        call_id="privacy-check",
                        result_state="SUCCEEDED",
                        result={"status": "checked"},
                    ),
                    _event(2, "TERMINAL", terminal_state="SUCCESS"),
                ],
            )
        ],
    )
    output = tmp_path / "redacted.jsonl"
    audit = tmp_path / "redaction.audit.json"
    monkeypatch.setattr(redaction_module._Redactor, "text", lambda _self, value: value)

    with pytest.raises(redaction_module.RedactionFailure) as failure:
        redact_preview_traces(source, output, audit)

    assert failure.value.reason_code == "REDACTION_RESIDUAL_IDENTIFIER"
    assert not output.exists() and not audit.exists()


@pytest.mark.parametrize("existing_target", ["output", "audit"])
def test_existing_publication_target_is_never_clobbered(
    tmp_path: Path,
    existing_target: str,
) -> None:
    source = tmp_path / "source.jsonl"
    _write_jsonl(
        source,
        [
            _trace(
                "existing-target",
                "source-existing-target",
                [_event(0, "USER_MESSAGE", content="A harmless request.")],
            )
        ],
    )
    output = tmp_path / "redacted.jsonl"
    audit = tmp_path / "redaction.audit.json"
    protected = output if existing_target == "output" else audit
    other = audit if existing_target == "output" else output
    sentinel = f"owned-{existing_target}\n".encode()
    protected.write_bytes(sentinel)

    completed = _run_redact(source, output, audit)

    assert completed.returncode != 0
    assert protected.read_bytes() == sentinel
    assert not other.exists()
    result = _machine_result(completed)
    assert result.get("command") == "behavior-map.redact"
    assert result.get("outcome") == "REJECTED"
    assert result.get("reason_code") == "REDACTION_PUBLICATION_REFUSED"


def test_handled_second_publication_failure_rolls_back_both_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.jsonl"
    _write_jsonl(
        source,
        [
            _trace(
                "paired-publication",
                "source-paired-publication",
                [_event(0, "USER_MESSAGE", content="A harmless request.")],
            )
        ],
    )
    output = tmp_path / "redacted.jsonl"
    audit = tmp_path / "redaction.audit.json"
    real_replace = redaction_module.os.replace
    replace_calls = 0

    def fail_second_replace(source_path: Path, destination_path: Path) -> None:
        nonlocal replace_calls
        replace_calls += 1
        if replace_calls == 2:
            raise OSError("synthetic-second-publication-failure")
        real_replace(source_path, destination_path)

    monkeypatch.setattr(redaction_module.os, "replace", fail_second_replace)

    with pytest.raises(redaction_module.RedactionFailure) as failure:
        redact_preview_traces(source, output, audit)

    assert failure.value.reason_code == "REDACTION_PUBLICATION_REFUSED"
    assert replace_calls == 2
    assert not output.exists() and not audit.exists()
    assert not list(tmp_path.glob(".*.jsonl.*"))
    assert not list(tmp_path.glob(".*.json.*"))
