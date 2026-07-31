"""Derive deterministic structural clusters from a validated Observer bundle."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from triana_labs import __version__
from triana_labs.intelligence.input import InputFailure, JsonObject, read_bundle
from triana_labs.intelligence.publication import PublicationFailure, publish

_FIDELITY = "SYNTHETIC_OBSERVED_STRUCTURE"


@dataclass(frozen=True)
class DeriveFailure(Exception):
    """Carry one safe derivation refusal and stable exit code."""

    reason_code: str
    exit_code: int


@dataclass(frozen=True)
class DeriveResult:
    """Expose completed-with-gaps counts to the CLI."""

    cluster_count: int
    gap_count: int
    trace_count: int
    outcome: str = "COMPLETED_WITH_GAPS"


def derive(manifest_path: Path, output_path: Path) -> DeriveResult:
    """Validate, derive, and atomically publish one structural bundle."""

    try:
        manifest_bytes, manifest, traces = read_bundle(manifest_path)
        artifacts, result = _derive_artifacts(manifest_bytes, manifest, traces)
        publish(output_path, artifacts)
    except InputFailure as failure:
        raise DeriveFailure(
            failure.reason_code, _exit_code(failure.reason_code)
        ) from failure
    except PublicationFailure as failure:
        raise DeriveFailure(
            failure.reason_code, _exit_code(failure.reason_code)
        ) from failure
    return result


def _derive_artifacts(
    manifest_bytes: bytes, manifest: JsonObject, traces: list[JsonObject]
) -> tuple[dict[str, bytes], DeriveResult]:
    input_hash = _digest(manifest_bytes)
    grouped: dict[bytes, tuple[JsonObject, list[str]]] = {}
    for trace in traces:
        fingerprint = _fingerprint(trace)
        preimage = _compact(fingerprint, lf=False)
        _, members = grouped.setdefault(preimage, (fingerprint, []))
        members.append(cast(str, trace["trace_id"]))
    clusters: list[JsonObject] = []
    for preimage, (fingerprint, members) in grouped.items():
        members.sort()
        support = len(members)
        clusters.append(
            {
                "ambiguity_state": "SEMANTICS_NOT_EVALUATED",
                "cluster_id": f"cluster-{hashlib.sha256(preimage).hexdigest()[:16]}",
                "fidelity": _FIDELITY,
                "fingerprint": fingerprint,
                "member_trace_ids": members,
                "support_count": support,
                "support_state": "SUPPORTED" if support > 1 else "SINGLETON",
            }
        )
    clusters.sort(key=lambda value: cast(str, value["cluster_id"]))
    gap_codes = [
        "DISTRESS_NOT_EVALUATED",
        "LANGUAGE_NOT_EVALUATED",
        "SEMANTIC_ASSETS_NOT_DERIVED",
    ]
    rejected_count = cast(int, manifest["rejected_count"])
    if rejected_count:
        gap_codes.append("SOURCE_REJECTIONS_PRESENT")
    gap_codes.sort()
    cluster_count = len(clusters)
    trace_count = len(traces)
    common = {
        "fidelity": _FIDELITY,
        "input_manifest_hash": input_hash,
        "schema_version": 1,
    }
    values: dict[str, JsonObject] = {
        "clusters.json": {
            **common,
            "artifact_kind": "corpus_clusters",
            "cluster_count": cluster_count,
            "clusters": clusters,
            "trace_count": trace_count,
        },
        "derivation_report.json": {
            **common,
            "artifact_kind": "corpus_derivation_report",
            "cluster_count": cluster_count,
            "gap_codes": gap_codes,
            "gap_count": len(gap_codes),
            "input_count": cast(int, manifest["input_count"]),
            "outcome": "COMPLETED_WITH_GAPS",
            "singleton_cluster_count": sum(
                len(item[1]) == 1 for item in grouped.values()
            ),
            "source_rejection_count": rejected_count,
            "supported_cluster_count": sum(
                len(item[1]) > 1 for item in grouped.values()
            ),
            "trace_count": trace_count,
        },
    }
    for path, kind in (
        ("personas/index.json", "PERSONA"),
        ("intents/index.json", "INTENT"),
        ("turn_policies/index.json", "TURN_POLICY"),
    ):
        values[path] = {
            **common,
            "artifact_kind": "derived_asset_index",
            "asset_kind": kind,
            "assets": [],
            "derivation_state": "NOT_DERIVED",
            "reason_code": "SEMANTIC_EVIDENCE_NOT_DERIVED",
            "support_count": 0,
        }
    artifacts = {name: _compact(value) for name, value in values.items()}
    artifacts["manifest.json"] = _compact(
        {
            "artifact_kind": "intelligence_manifest",
            "artifacts": {
                name: _digest(payload) for name, payload in artifacts.items()
            },
            "cluster_count": cluster_count,
            "fidelity": _FIDELITY,
            "gap_count": len(gap_codes),
            "input_manifest_hash": input_hash,
            "outcome": "COMPLETED_WITH_GAPS",
            "privacy_class": "SYNTHETIC",
            "producing_component": "corpus_intelligence",
            "producing_component_version": __version__,
            "schema_version": 1,
            "trace_count": trace_count,
        }
    )
    return artifacts, DeriveResult(cluster_count, len(gap_codes), trace_count)


def _fingerprint(trace: JsonObject) -> JsonObject:
    counts = {
        "assistant_message_count": 0,
        "tool_call_count": 0,
        "tool_error_count": 0,
        "tool_result_count": 0,
        "unmatched_tool_call_count": 0,
        "user_message_count": 0,
    }
    calls: set[str] = set()
    results: set[str] = set()
    names: list[str] = []
    terminal = "MISSING"
    user_seen = False
    eligible = False
    for event in cast(list[JsonObject], trace["events"]):
        kind = cast(str, event["event_kind"])
        if kind == "USER_MESSAGE":
            counts["user_message_count"] += 1
            user_seen = True
        elif kind == "ASSISTANT_MESSAGE":
            counts["assistant_message_count"] += 1
            eligible = eligible or user_seen
        elif kind == "TOOL_CALL":
            counts["tool_call_count"] += 1
            calls.add(cast(str, event["call_id"]))
            names.append(cast(str, event["tool_name"]))
            eligible = eligible or user_seen
        elif kind == "TOOL_RESULT":
            counts["tool_result_count"] += 1
            results.add(cast(str, event["call_id"]))
            counts["tool_error_count"] += int(event["result_state"] == "ERROR")
        elif kind == "TERMINAL":
            terminal = cast(str, event["terminal_state"])
    counts["unmatched_tool_call_count"] = len(calls - results)
    return {
        **counts,
        "case_generation_eligible": eligible,
        "terminal_state": terminal,
        "tool_name_sequence": names,
    }


def _compact(value: Any, *, lf: bool = True) -> bytes:
    payload = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return payload + (b"\n" if lf else b"")


def _digest(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _exit_code(reason: str) -> int:
    if reason in {
        "INPUT_READ_FAILED",
        "OUTPUT_ALREADY_EXISTS",
        "OUTPUT_PARENT_MISSING",
    }:
        return 2
    if reason == "INPUT_TOO_LARGE":
        return 3
    if reason in {"MANIFEST_INVALID", "UNSUPPORTED_PRIVACY_CLASS"}:
        return 4
    if reason in {"CORPUS_INTEGRITY_FAILED", "EMPTY_CORPUS"}:
        return 5
    if reason == "OUTPUT_WRITE_FAILED":
        return 7
    return 70
