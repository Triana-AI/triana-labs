"""Exact deterministic structural derivation acceptance."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from conftest import (
    FIDELITY,
    OUTPUT_NAMES,
    build_observer_bundle,
    compact_json,
    digest,
    read_fixture_traces,
)


def fingerprint(trace: dict[str, Any]) -> dict[str, Any]:
    calls: dict[str, int] = {}
    results: set[str] = set()
    terminal_state = "MISSING"
    user_seen = False
    eligible = False
    counts = {
        "assistant_message_count": 0,
        "tool_call_count": 0,
        "tool_error_count": 0,
        "tool_result_count": 0,
        "unmatched_tool_call_count": 0,
        "user_message_count": 0,
    }
    names: list[str] = []
    for index, event in enumerate(trace["events"]):
        kind = event["event_kind"]
        if kind == "USER_MESSAGE":
            counts["user_message_count"] += 1
            user_seen = True
        elif kind == "ASSISTANT_MESSAGE":
            counts["assistant_message_count"] += 1
            eligible = eligible or user_seen
        elif kind == "TOOL_CALL":
            counts["tool_call_count"] += 1
            calls[event["call_id"]] = index
            names.append(event["tool_name"])
            eligible = eligible or user_seen
        elif kind == "TOOL_RESULT":
            counts["tool_result_count"] += 1
            results.add(event["call_id"])
            counts["tool_error_count"] += int(event["result_state"] == "ERROR")
        elif kind == "TERMINAL":
            terminal_state = event["terminal_state"]
    counts["unmatched_tool_call_count"] = len(set(calls) - results)
    return {
        **counts,
        "case_generation_eligible": eligible,
        "terminal_state": terminal_state,
        "tool_name_sequence": names,
    }


def test_owner_authorized_canary_derivation_retains_private_class_and_fidelity(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    privacy = "OWNER_AUTHORIZED_REAL_DATA_CANARY"
    fidelity = "OWNER_AUTHORIZED_REAL_DATA_OBSERVED_STRUCTURE"
    traces = read_fixture_traces()
    for trace in traces:
        trace["privacy_class"] = privacy

    with tempfile.TemporaryDirectory(
        prefix="triana-intelligence-", dir="/private/tmp"
    ) as root:
        private_root = Path(root)
        source_manifest = build_observer_bundle(private_root / "observed", traces)
        manifest = json.loads(source_manifest.read_bytes())
        manifest["privacy_class"] = privacy
        source_manifest.write_bytes(compact_json(manifest))
        output = private_root / "intelligence"

        result = run_cli("corpus", "derive", source_manifest, "--out", output)

        assert result.returncode == 10
        values = {
            path.relative_to(output).as_posix(): json.loads(path.read_bytes())
            for path in output.rglob("*.json")
        }
        assert set(values) == OUTPUT_NAMES
        assert values["manifest.json"]["privacy_class"] == privacy
        assert values["manifest.json"]["fidelity"] == fidelity
        assert all(
            value.get("fidelity") == fidelity
            for name, value in values.items()
            if name != "manifest.json"
        )
        combined = b"".join(path.read_bytes() for path in output.rglob("*.*"))
        assert b"SYNTHETIC_OBSERVED_STRUCTURE" not in combined


def expected_outputs(
    manifest: Path, traces: list[dict[str, Any]], rejected: int
) -> dict[str, bytes]:
    input_hash = digest(manifest.read_bytes())
    members: dict[bytes, list[str]] = {}
    fingerprints: dict[bytes, dict[str, Any]] = {}
    for trace in traces:
        value = fingerprint(trace)
        preimage = compact_json(value)[:-1]
        fingerprints[preimage] = value
        members.setdefault(preimage, []).append(trace["trace_id"])
    clusters = []
    for preimage, trace_ids in members.items():
        support = len(trace_ids)
        clusters.append(
            {
                "ambiguity_state": "SEMANTICS_NOT_EVALUATED",
                "cluster_id": f"cluster-{hashlib.sha256(preimage).hexdigest()[:16]}",
                "fidelity": FIDELITY,
                "fingerprint": fingerprints[preimage],
                "member_trace_ids": sorted(trace_ids),
                "support_count": support,
                "support_state": "SUPPORTED" if support > 1 else "SINGLETON",
            }
        )
    clusters.sort(key=lambda item: item["cluster_id"])
    cluster_count = len(clusters)
    gap_codes = [
        "DISTRESS_NOT_EVALUATED",
        "LANGUAGE_NOT_EVALUATED",
        "SEMANTIC_ASSETS_NOT_DERIVED",
    ]
    if rejected:
        gap_codes.append("SOURCE_REJECTIONS_PRESENT")
    gap_codes.sort()
    common = {
        "fidelity": FIDELITY,
        "input_manifest_hash": input_hash,
        "schema_version": 1,
    }
    values: dict[str, Any] = {
        "clusters.json": {
            **common,
            "artifact_kind": "corpus_clusters",
            "cluster_count": cluster_count,
            "clusters": clusters,
            "trace_count": len(traces),
        },
        "derivation_report.json": {
            **common,
            "artifact_kind": "corpus_derivation_report",
            "cluster_count": cluster_count,
            "gap_codes": gap_codes,
            "gap_count": len(gap_codes),
            "input_count": len(traces) + rejected,
            "outcome": "COMPLETED_WITH_GAPS",
            "singleton_cluster_count": sum(len(ids) == 1 for ids in members.values()),
            "source_rejection_count": rejected,
            "supported_cluster_count": sum(len(ids) > 1 for ids in members.values()),
            "trace_count": len(traces),
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
    payloads = {path: compact_json(value) for path, value in values.items()}
    payloads["manifest.json"] = compact_json(
        {
            "artifact_kind": "intelligence_manifest",
            "artifacts": {path: digest(payload) for path, payload in payloads.items()},
            "cluster_count": cluster_count,
            "fidelity": FIDELITY,
            "gap_count": len(gap_codes),
            "input_manifest_hash": input_hash,
            "outcome": "COMPLETED_WITH_GAPS",
            "privacy_class": "SYNTHETIC",
            "producing_component": "corpus_intelligence",
            "producing_component_version": "0.0.0",
            "schema_version": 1,
            "trace_count": len(traces),
        }
    )
    return payloads


def test_exact_bundle_ids_hashes_lineage_and_gaps(run_cli: Any, tmp_path: Path) -> None:
    traces = read_fixture_traces()
    source_manifest = build_observer_bundle(
        tmp_path / "observed", traces, rejected_count=1
    )
    output = tmp_path / "intelligence"

    result = run_cli("corpus", "derive", source_manifest, "--out", output)

    expected = expected_outputs(source_manifest, traces, 1)
    assert result.returncode == 10
    assert {
        path.relative_to(output).as_posix() for path in output.rglob("*.json")
    } == OUTPUT_NAMES
    assert {name: (output / name).read_bytes() for name in OUTPUT_NAMES} == expected
    assert result.stdout_json() == {
        "cluster_count": 3,
        "gap_count": 4,
        "manifest_path": f"{output}/manifest.json",
        "outcome": "COMPLETED_WITH_GAPS",
        "trace_count": 4,
    }
    log = result.stderr_json()
    duration = log.pop("duration_ms")
    assert type(duration) is int and duration >= 0
    assert log == {
        "cluster_count": 3,
        "command": "corpus.derive",
        "event_name": "triana.corpus.derive.completed_with_gaps",
        "gap_count": 4,
        "outcome": "COMPLETED_WITH_GAPS",
        "reason_code": None,
        "service": "triana-labs-cli",
        "service_version": "0.0.0",
        "severity": "INFO",
        "trace_count": 4,
    }


def test_repeat_and_input_order_are_byte_deterministic(
    run_cli: Any, tmp_path: Path
) -> None:
    traces = read_fixture_traces()
    manifests = [
        build_observer_bundle(tmp_path / "first-observed", traces),
        build_observer_bundle(tmp_path / "second-observed", list(reversed(traces))),
    ]
    outputs = [tmp_path / "first", tmp_path / "second"]
    for manifest, output in zip(manifests, outputs, strict=True):
        assert run_cli("corpus", "derive", manifest, "--out", output).returncode == 10
    # Input manifest lineage differs with line order, but cluster membership and IDs do not.
    first = json.loads((outputs[0] / "clusters.json").read_bytes())
    second = json.loads((outputs[1] / "clusters.json").read_bytes())
    assert first["clusters"] == second["clusters"]
    repeat = tmp_path / "repeat"
    assert run_cli("corpus", "derive", manifests[0], "--out", repeat).returncode == 10
    assert {name: (outputs[0] / name).read_bytes() for name in OUTPUT_NAMES} == {
        name: (repeat / name).read_bytes() for name in OUTPUT_NAMES
    }


def test_no_source_content_or_semantic_assets_leak(
    run_cli: Any, tmp_path: Path
) -> None:
    manifest = build_observer_bundle(tmp_path / "observed")
    output = tmp_path / "derived"
    result = run_cli("corpus", "derive", manifest, "--out", output)
    assert result.returncode == 10
    combined = (
        b"".join(path.read_bytes() for path in output.rglob("*.json")) + result.stderr
    )
    for forbidden in (
        b"PRIVATE_",
        b"source-zeta-private",
        b"source-alpha-private",
        b"source-tool-private",
        b"source-system-private",
    ):
        assert forbidden not in combined
    for path in (
        "personas/index.json",
        "intents/index.json",
        "turn_policies/index.json",
    ):
        assert json.loads((output / path).read_bytes())["assets"] == []
