"""Corpus shapes, selection boundaries, ordering, and upstream integrity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from conftest import (
    ENVIRON,
    CapturePublisher,
    ScriptedTransport,
    api,
    build_upstream,
    canonical,
    critique_callback,
    invoke,
    proposal_callback,
    request_user_value,
    trace,
    write_config,
)


def selected_ids(transport: ScriptedTransport) -> list[str]:
    evidence = request_user_value(transport.requests[0])["evidence"]
    return [item["trace_id"] for item in evidence["selected_traces"]]


@pytest.mark.parametrize(
    ("traces", "rejected"),
    [
        ([trace("trace-one", "Tiny", "Reply")], 0),
        (
            [
                trace("trace-one", "Same content", "Same reply"),
                trace("trace-two", "Same content", "Same reply"),
            ],
            0,
        ),
        (
            [
                trace("trace-one", "Same content", "Same reply"),
                trace("trace-two", "Same content", "Same reply"),
            ],
            2,
        ),
    ],
)
def test_tiny_homogeneous_duplicate_content_and_source_rejections_are_accounted(
    tmp_path: Path, traces: list[dict[str, Any]], rejected: int
) -> None:
    publisher = CapturePublisher()
    result, transport, _, _ = invoke(
        tmp_path,
        [proposal_callback(), critique_callback, proposal_callback()],
        traces=traces,
        rejected=rejected,
        publisher=publisher,
    )
    assert result.valid_case_count == 5
    evidence = json.loads(publisher.artifacts["evidence_index.json"])
    assert evidence["selected_trace_count"] == len(traces)
    assert set(selected_ids(transport)) == {item["trace_id"] for item in traces}


def test_input_reorder_preserves_selection_order(tmp_path: Path) -> None:
    traces = [
        trace("trace-zeta", "Zeta request", "Reply"),
        trace("trace-alpha", "Alpha request", "Reply"),
        trace("trace-middle", "Middle request", "Reply"),
    ]
    transports = []
    for name, values in (("first", traces), ("second", list(reversed(traces)))):
        publisher = CapturePublisher()
        _, transport, _, _ = invoke(
            tmp_path / name,
            [proposal_callback(), critique_callback, proposal_callback()],
            traces=values,
            publisher=publisher,
        )
        transports.append(transport)
    assert selected_ids(transports[0]) == selected_ids(transports[1])


def test_oversized_user_event_leaves_no_usable_evidence(tmp_path: Path) -> None:
    observer, intelligence = build_upstream(
        tmp_path, [trace("trace-large", "x" * 16385, "Reply")]
    )
    config = write_config(tmp_path)
    generate_module, _ = api()
    transport = ScriptedTransport([])
    with pytest.raises(Exception) as caught:
        generate_module.generate(
            observer,
            intelligence,
            config,
            tmp_path / "output",
            transport=transport,
            environ=ENVIRON,
        )
    assert caught.value.reason_code == "NO_USABLE_SEMANTIC_EVIDENCE"
    assert caught.value.exit_code == 5
    assert transport.requests == []


def test_twenty_five_trace_limit_is_explicit(tmp_path: Path) -> None:
    traces = [
        trace(f"trace-{index:02d}", f"Request {index}", "Reply") for index in range(27)
    ]
    publisher = CapturePublisher()
    _, transport, _, _ = invoke(
        tmp_path,
        [proposal_callback(), critique_callback, proposal_callback()],
        traces=traces,
        publisher=publisher,
    )
    evidence = request_user_value(transport.requests[0])["evidence"]
    assert len(evidence["selected_traces"]) == 25
    assert {gap["reason_code"] for gap in evidence["gaps"]} == {
        "EVIDENCE_TRACE_LIMIT_REACHED"
    }
    index = json.loads(publisher.artifacts["evidence_index.json"])
    assert (index["selected_trace_count"], index["excluded_trace_count"]) == (25, 2)


def test_manifest_symlink_and_privacy_tamper_refuse(tmp_path: Path) -> None:
    observer, intelligence = build_upstream(tmp_path)
    config = write_config(tmp_path)
    generate_module, _ = api()
    transport = ScriptedTransport([])
    link = tmp_path / "observer-link.json"
    link.symlink_to(observer)
    with pytest.raises(Exception) as caught:
        generate_module.generate(
            link,
            intelligence,
            config,
            tmp_path / "one",
            transport=transport,
            environ=ENVIRON,
        )
    assert caught.value.reason_code == "INPUT_READ_FAILED"
    value = json.loads(observer.read_bytes())
    value["privacy_class"] = "LOCAL_SENSITIVE"
    observer.write_bytes(canonical(value, lf=True))
    with pytest.raises(Exception) as caught:
        generate_module.generate(
            observer,
            intelligence,
            config,
            tmp_path / "two",
            transport=transport,
            environ=ENVIRON,
        )
    assert caught.value.reason_code == "UNSUPPORTED_PRIVACY_CLASS"


def test_cluster_round_robin_selection_matches_upstream_clusters_exactly(
    tmp_path: Path,
) -> None:
    traces = []
    for trace_id, tool_name in (
        ("trace-zeta", "lookup_b"),
        ("trace-alpha", "lookup_a"),
        ("trace-middle", "lookup_a"),
        ("trace-omega", "lookup_b"),
        ("trace-single", "lookup_c"),
    ):
        item = trace(trace_id, f"Request {trace_id}", "Reply")
        item["events"][2]["tool_name"] = tool_name
        traces.append(item)
    observer, intelligence = build_upstream(tmp_path, traces)
    clusters = json.loads((intelligence.parent / "clusters.json").read_bytes())[
        "clusters"
    ]
    ordered_clusters = sorted(clusters, key=lambda item: item["cluster_id"])
    expected = []
    for member_index in range(
        max(len(item["member_trace_ids"]) for item in ordered_clusters)
    ):
        for cluster in ordered_clusters:
            members = sorted(cluster["member_trace_ids"])
            if member_index < len(members):
                expected.append(members[member_index])

    generate_module, _ = api()
    transport = ScriptedTransport(
        [proposal_callback(), critique_callback, proposal_callback()]
    )
    publisher = CapturePublisher()
    generate_module.generate(
        observer,
        intelligence,
        write_config(tmp_path),
        tmp_path / "round-robin",
        transport=transport,
        publisher=publisher,
        environ=ENVIRON,
    )
    evidence = request_user_value(transport.requests[0])["evidence"]
    assert [item["trace_id"] for item in evidence["selected_traces"]] == expected
    expected_cluster_by_trace = {
        trace_id: cluster["cluster_id"]
        for cluster in clusters
        for trace_id in cluster["member_trace_ids"]
    }
    assert {
        item["trace_id"]: item["structural_cluster_id"]
        for item in evidence["selected_traces"]
    } == expected_cluster_by_trace


def test_event_oversize_gap_keeps_trace_when_user_evidence_remains(
    tmp_path: Path,
) -> None:
    traces = [
        trace("trace-large-assistant", "Usable request", "x" * 16385),
        trace("trace-normal", "Another request", "Normal answer"),
    ]
    publisher = CapturePublisher()
    _, transport, _, _ = invoke(
        tmp_path,
        [proposal_callback(), critique_callback, proposal_callback()],
        traces=traces,
        publisher=publisher,
    )
    projected = request_user_value(transport.requests[0])["evidence"]
    large = next(
        item
        for item in projected["selected_traces"]
        if item["trace_id"] == "trace-large-assistant"
    )
    assert [event["sequence"] for event in large["events"]] == [1, 2, 3, 5]
    assert projected["gaps"] == [
        {
            "reason_code": "EVIDENCE_EVENT_TOO_LARGE",
            "trace_id": "trace-large-assistant",
            "event_sequence": 4,
        }
    ]
    evidence = json.loads(publisher.artifacts["evidence_index.json"])
    assert evidence["selected_trace_count"] == 2
    assert evidence["excluded_trace_count"] == 0
    assert evidence["gaps"] == projected["gaps"]
    assert evidence["projected_byte_count"] == len(canonical(projected))


def test_byte_limit_gap_counts_every_skipped_candidate_and_exact_bytes(
    tmp_path: Path,
) -> None:
    traces = [
        trace(f"trace-wide-{index:02d}", f"{index}:" + "x" * 16000, "short")
        for index in range(10)
    ]
    publisher = CapturePublisher()
    _, transport, _, _ = invoke(
        tmp_path,
        [proposal_callback(), critique_callback, proposal_callback()],
        traces=traces,
        publisher=publisher,
    )
    projected = request_user_value(transport.requests[0])["evidence"]
    byte_gaps = [
        gap
        for gap in projected["gaps"]
        if gap["reason_code"] == "EVIDENCE_BYTE_LIMIT_REACHED"
    ]
    index = json.loads(publisher.artifacts["evidence_index.json"])
    assert byte_gaps
    assert all(set(gap) == {"reason_code", "trace_id"} for gap in byte_gaps)
    assert index["excluded_trace_count"] == len(byte_gaps)
    assert index["selected_trace_count"] + index["excluded_trace_count"] == len(traces)
    assert index["projected_byte_count"] == len(canonical(projected)) <= 90000


def test_default_publisher_writes_only_the_exact_closed_bundle(
    tmp_path: Path, success_callbacks: list[Any]
) -> None:
    result, _, _, output = invoke(tmp_path, success_callbacks)
    assert result.manifest_path == output / "manifest.json"
    assert output.is_dir()
    assert {item.name for item in output.iterdir()} == {
        "manifest.json",
        "generation_attempts.jsonl",
        "evidence_index.json",
        "control_personas.jsonl",
        "control_intents.jsonl",
        "control_turn_policies.jsonl",
        "control_case_candidates.jsonl",
        "personas.jsonl",
        "intents.jsonl",
        "turn_policies.jsonl",
        "case_candidates.jsonl",
        "case_factory_eval.json",
        "human_review_template.json",
    }
    assert all(item.is_file() and not item.is_symlink() for item in output.iterdir())
    manifest = json.loads((output / "manifest.json").read_bytes())
    for name, digest in manifest["artifacts"].items():
        import hashlib

        assert (
            digest
            == f"sha256:{hashlib.sha256((output / name).read_bytes()).hexdigest()}"
        )


@pytest.mark.parametrize("mode", ["existing", "missing-parent", "symlink"])
def test_default_publisher_preconditions_leave_existing_paths_untouched(
    tmp_path: Path, mode: str
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    config = write_config(tmp_path)
    generate_module, _ = api()
    transport = ScriptedTransport([])
    parent = tmp_path / "publication-parent"
    parent.mkdir()
    output = parent / "output"
    marker: Path | None = None
    if mode == "existing":
        output.mkdir()
        marker = output / "PRIVATE_MARKER"
        marker.write_text("preserve")
        expected_reason = "OUTPUT_ALREADY_EXISTS"
    elif mode == "missing-parent":
        output = tmp_path / "absent" / "output"
        expected_reason = "OUTPUT_PARENT_MISSING"
    else:
        target = parent / "existing-target"
        target.mkdir()
        marker = target / "PRIVATE_MARKER"
        marker.write_text("preserve")
        output.symlink_to(target, target_is_directory=True)
        expected_reason = "OUTPUT_ALREADY_EXISTS"
    before = {item.name for item in parent.iterdir()}
    with pytest.raises(Exception) as caught:
        generate_module.generate(
            observer,
            intelligence,
            config,
            output,
            transport=transport,
            environ=ENVIRON,
        )
    assert caught.value.reason_code == expected_reason
    assert caught.value.exit_code == 2
    assert transport.requests == []
    if marker is not None:
        assert marker.read_text() == "preserve"
    assert {item.name for item in parent.iterdir()} == before
