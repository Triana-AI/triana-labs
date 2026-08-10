"""Compile retained HRAI records into deterministic Labs-owned report facts.

This boundary intentionally owns only source accounting that can be established
from the retained normalized records.  It does not derive behavior labels, cases,
conversation outcomes, costs, or human rulings.  Downstream report projections may
copy these facts, but they may not upgrade them into semantic evidence.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from triana_labs.contracts.traces import LineRejection, parse_and_validate_line

JsonValue = None | bool | int | str | list["JsonValue"] | dict[str, "JsonValue"]

_EVIDENCE_CLASS = "SYNTHETIC_EXISTING_TRACE_CORPUS"
_SCHEMA_VERSION = "normalized-trace-v2"
_COMPILER_VERSION = "labs08-hrai-accounting-v1"
_PREVIEW_COMPILER_VERSION = "preview-trace-structural-v1"
_ALLOWED_STATUSES = frozenset({"COMPLETED", "HARNESS_ERROR"})


class ReportCompilationError(ValueError):
    """Refuse an invalid or unsupported retained source with a stable code."""

    def __init__(self, reason_code: str, *, line_number: int | None = None) -> None:
        self.reason_code = reason_code
        self.line_number = line_number
        super().__init__(reason_code)


@dataclass(frozen=True, slots=True)
class AnalysisFact:
    """One deterministic fact suitable for persistence by the backend."""

    fact_id: str
    fact_kind: str
    value: JsonValue
    authority: str = "DETERMINISTIC"
    schema_version: int = 1

    def to_mapping(self) -> dict[str, JsonValue]:
        return {
            "authority": self.authority,
            "fact_id": self.fact_id,
            "fact_kind": self.fact_kind,
            "schema_version": self.schema_version,
            "value": self.value,
        }


@dataclass(frozen=True, slots=True)
class RejectedEvidence:
    """Retain one unusable source record as typed evidence, never as a pass."""

    line_number: int
    record_id: str
    reason_code: str
    source_status: str

    def to_mapping(self) -> dict[str, JsonValue]:
        return {
            "line_number": self.line_number,
            "reason_code": self.reason_code,
            "record_id": self.record_id,
            "source_status": self.source_status,
        }


@dataclass(frozen=True, slots=True)
class CompiledAnalysis:
    """Immutable Labs-owned fact set with exact source and result lineage."""

    source_sha256: str
    evidence_class: str
    facts: tuple[AnalysisFact, ...]
    rejected_evidence: tuple[RejectedEvidence, ...]
    result_hash: str
    artifact_kind: str = "labs_analysis_facts"
    schema_version: int = 1
    compiler_version: str = _COMPILER_VERSION

    def to_mapping(self) -> dict[str, JsonValue]:
        return {
            "artifact_kind": self.artifact_kind,
            "compiler_version": self.compiler_version,
            "evidence_class": self.evidence_class,
            "facts": [fact.to_mapping() for fact in self.facts],
            "rejected_evidence": [item.to_mapping() for item in self.rejected_evidence],
            "result_hash": self.result_hash,
            "schema_version": self.schema_version,
            "source_sha256": self.source_sha256,
        }


def compile_hrai_normalized_trace_v2(
    source_bytes: bytes,
    *,
    evidence_class: str,
    expected_sha256: str | None = None,
) -> CompiledAnalysis:
    """Compile only deterministic accounting from an HRAI normalized JSONL corpus.

    Malformed or unsupported records refuse the compilation because an incomplete
    denominator cannot truthfully become a report.  A well-formed ``HARNESS_ERROR``
    remains retained as typed rejected evidence and contributes to the physical and
    status denominators while never contributing to usable conversations.
    """

    if evidence_class != _EVIDENCE_CLASS:
        raise ReportCompilationError("UNSUPPORTED_EVIDENCE_CLASS")
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if expected_sha256 is not None and source_sha256 != expected_sha256:
        raise ReportCompilationError("SOURCE_HASH_MISMATCH")

    lines = source_bytes.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    if not lines:
        raise ReportCompilationError("EMPTY_CORPUS")

    status_counts: dict[str, int] = {}
    usable_count = 0
    seen_record_ids: set[str] = set()
    rejected: list[RejectedEvidence] = []
    for line_number, raw_line in enumerate(lines, start=1):
        record = _parse_record(raw_line, line_number=line_number)
        record_id = record.get("case_id")
        if not isinstance(record_id, str) or not record_id:
            raise ReportCompilationError(
                "SOURCE_RECORD_ID_INVALID", line_number=line_number
            )
        if record_id in seen_record_ids:
            raise ReportCompilationError(
                "SOURCE_RECORD_ID_DUPLICATE", line_number=line_number
            )
        seen_record_ids.add(record_id)

        if record.get("schema_version") != _SCHEMA_VERSION:
            raise ReportCompilationError(
                "SOURCE_SCHEMA_VERSION_UNSUPPORTED", line_number=line_number
            )
        status = record.get("status")
        if not isinstance(status, str) or status not in _ALLOWED_STATUSES:
            raise ReportCompilationError(
                "SOURCE_STATUS_UNSUPPORTED", line_number=line_number
            )
        status_counts[status] = status_counts.get(status, 0) + 1
        if status == "COMPLETED":
            turns = record.get("turns")
            if not isinstance(turns, list) or not turns:
                raise ReportCompilationError(
                    "COMPLETED_CONVERSATION_MISSING", line_number=line_number
                )
            usable_count += 1
        else:
            rejected.append(
                RejectedEvidence(
                    line_number=line_number,
                    record_id=record_id,
                    reason_code="SOURCE_EXECUTION_INCOMPLETE",
                    source_status=status,
                )
            )

    ordered_counts: dict[str, JsonValue] = {
        key: status_counts[key] for key in sorted(status_counts)
    }
    values: tuple[tuple[str, JsonValue], ...] = (
        ("physical_record_count", len(lines)),
        ("source_status_counts", ordered_counts),
        ("usable_conversation_count", usable_count),
    )
    facts = tuple(
        AnalysisFact(
            fact_id=_fact_id(source_sha256, kind, value),
            fact_kind=kind,
            value=value,
        )
        for kind, value in values
    )
    preimage: dict[str, JsonValue] = {
        "artifact_kind": "labs_analysis_facts",
        "compiler_version": _COMPILER_VERSION,
        "evidence_class": evidence_class,
        "facts": [fact.to_mapping() for fact in facts],
        "rejected_evidence": [item.to_mapping() for item in rejected],
        "schema_version": 1,
        "source_sha256": source_sha256,
    }
    return CompiledAnalysis(
        source_sha256=source_sha256,
        evidence_class=evidence_class,
        facts=facts,
        rejected_evidence=tuple(rejected),
        result_hash=hashlib.sha256(_canonical(preimage)).hexdigest(),
    )


def compile_preview_trace_v1(
    source_bytes: bytes,
    *,
    evidence_class: str,
    expected_sha256: str | None = None,
) -> CompiledAnalysis:
    """Compile PreviewTrace records into content-free structural groups."""

    if evidence_class != _EVIDENCE_CLASS:
        raise ReportCompilationError("UNSUPPORTED_EVIDENCE_CLASS")
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if expected_sha256 is not None and source_sha256 != expected_sha256:
        raise ReportCompilationError("SOURCE_HASH_MISMATCH")
    lines = source_bytes.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    if not lines:
        raise ReportCompilationError("EMPTY_CORPUS")

    seen_trace_ids: set[str] = set()
    seen_source_ids: set[str] = set()
    members: dict[str, list[str]] = {}
    for line_number, raw_line in enumerate(lines, start=1):
        try:
            validated = parse_and_validate_line(raw_line, first_line=line_number == 1)
        except LineRejection as error:
            raise ReportCompilationError(error.code, line_number=line_number) from error
        trace = validated.value
        if trace["privacy_class"] != "SYNTHETIC":
            raise ReportCompilationError(
                "UNSUPPORTED_PRIVACY_CLASS", line_number=line_number
            )
        trace_id = str(trace["trace_id"])
        source_trace_id = str(trace["source_trace_id"])
        if trace_id in seen_trace_ids:
            raise ReportCompilationError(
                "SOURCE_RECORD_ID_DUPLICATE", line_number=line_number
            )
        if source_trace_id in seen_source_ids:
            raise ReportCompilationError(
                "SOURCE_TRACE_ID_DUPLICATE", line_number=line_number
            )
        seen_trace_ids.add(trace_id)
        seen_source_ids.add(source_trace_id)
        pattern = " > ".join(
            (
                f"TOOL_CALL:{event['tool_name']}"
                if event["event_kind"] == "TOOL_CALL"
                else str(event["event_kind"])
            )
            for event in trace["events"]
        )
        members.setdefault(pattern, []).append(trace_id)

    group_rows: list[dict[str, JsonValue]] = []
    ordered_patterns = sorted(
        members,
        key=lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest(),
    )
    shares = _basis_point_shares(
        [len(members[pattern]) for pattern in ordered_patterns], len(lines)
    )
    for index, (pattern, share) in enumerate(
        zip(ordered_patterns, shares, strict=True), start=1
    ):
        group_id = f"group_{hashlib.sha256(pattern.encode('utf-8')).hexdigest()[:24]}"
        evidence_ids = sorted(members[pattern])
        group: dict[str, JsonValue] = {
            "group_id": group_id,
            "label": f"Observed structure {index}",
            "summary": f"Observed ordered event structure: {pattern}.",
            "support_count": len(evidence_ids),
            "share_basis_points": share,
            "structural_pattern": pattern,
            "source_evidence_ids": list(evidence_ids),
        }
        group_rows.append(group)
    group_rows.sort(key=lambda row: str(row["group_id"]))

    values: tuple[tuple[str, JsonValue], ...] = (
        ("physical_record_count", len(lines)),
        ("accepted_record_count", len(lines)),
        ("rejected_record_count", 0),
        ("usable_conversation_count", len(lines)),
        ("source_status_counts", {"ACCEPTED": len(lines)}),
        ("rejection_summary", {}),
        ("behavior_groups", list(group_rows)),
    )
    facts = tuple(
        AnalysisFact(
            fact_id=_fact_id(source_sha256, kind, value),
            fact_kind=kind,
            value=value,
        )
        for kind, value in values
    )
    preimage: dict[str, JsonValue] = {
        "artifact_kind": "labs_analysis_facts",
        "compiler_version": _PREVIEW_COMPILER_VERSION,
        "evidence_class": evidence_class,
        "facts": [fact.to_mapping() for fact in facts],
        "rejected_evidence": [],
        "schema_version": 1,
        "source_sha256": source_sha256,
    }
    return CompiledAnalysis(
        source_sha256=source_sha256,
        evidence_class=evidence_class,
        facts=facts,
        rejected_evidence=(),
        result_hash=hashlib.sha256(_canonical(preimage)).hexdigest(),
        compiler_version=_PREVIEW_COMPILER_VERSION,
    )


def _basis_point_shares(support: list[int], denominator: int) -> list[int]:
    floors = [count * 10_000 // denominator for count in support]
    remaining = 10_000 - sum(floors)
    priority = sorted(
        range(len(support)),
        key=lambda index: (-(support[index] * 10_000 % denominator), index),
    )
    for index in priority[:remaining]:
        floors[index] += 1
    return floors


def _parse_record(raw_line: bytes, *, line_number: int) -> dict[str, Any]:
    if not raw_line.strip():
        raise ReportCompilationError("SOURCE_BLANK_LINE", line_number=line_number)
    try:
        value: Any = json.loads(raw_line)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReportCompilationError(
            "SOURCE_RECORD_INVALID", line_number=line_number
        ) from error
    if not isinstance(value, dict):
        raise ReportCompilationError("SOURCE_RECORD_INVALID", line_number=line_number)
    return value


def _fact_id(source_sha256: str, fact_kind: str, value: JsonValue) -> str:
    identity: dict[str, JsonValue] = {
        "fact_kind": fact_kind,
        "source_sha256": source_sha256,
        "value": value,
    }
    return f"fact_{hashlib.sha256(_canonical(identity)).hexdigest()[:32]}"


def _canonical(value: JsonValue) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
