"""Black-box acceptance for Trace-to-Eval Review V0."""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

GROUPS = {
    "pair-a": ["trace-01", "trace-02"],
    "pair-b": ["trace-03", "trace-04"],
    "pair-c": ["trace-05", "trace-06"],
    "pair-d": ["trace-07", "trace-08"],
    "pair-e": ["trace-09", "trace-10"],
    "pair-f": ["trace-11", "trace-12"],
}


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


def _trace(trace_id: str, prompt: str, answer: str) -> dict[str, Any]:
    return {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": "SYNTHETIC",
        "trace_id": trace_id,
        "source_trace_id": "source-" + trace_id.removeprefix("trace-"),
        "events": [
            {"sequence": 0, "event_kind": "USER_MESSAGE", "content": prompt},
            {
                "sequence": 1,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": answer,
                "is_final": True,
            },
        ],
    }


def _write_manifest(tmp_path: Path, *, trace_only: bool = False) -> Path:
    topics = (
        ("Cancel synthetic order A.", "Synthetic order A was cancelled."),
        ("Cancel synthetic order A after clarification.", "Cancellation confirmed."),
        ("Change delivery address B.", "Synthetic address B was changed."),
        ("Confirm changed address B.", "Synthetic address B was confirmed."),
        ("Find refund status C.", "Synthetic refund C is pending."),
        ("Check refund status C with receipt.", "Synthetic refund C remains pending."),
        ("Exchange synthetic item D.", "Synthetic item D is exchangeable."),
        ("Exchange item D for another size.", "Synthetic size exchange is available."),
        ("Report synthetic item E damaged.", "Synthetic damage report E was opened."),
        ("Report item E damaged with a photo.", "Synthetic photo evidence was recorded."),
        ("Ask about synthetic warranty F.", "Synthetic warranty F lasts one year."),
        ("Does warranty F cover wear?", "Synthetic warranty F excludes wear."),
    )
    source = tmp_path / "traces.jsonl"
    payload = b"".join(
        _canonical(_trace(f"trace-{index:02d}", prompt, answer), lf=True)
        for index, (prompt, answer) in enumerate(topics, start=1)
    )
    payload += (
        b'{"contract_kind":"preview_trace","trace_id":"bad trace id",'
        b'"raw":"TOP_SECRET_REJECTED_CONTENT"}\n'
    )
    source.write_bytes(payload)
    manifest = {
        "artifact_kind": "evidence_bundle_manifest_v0",
        "schema_version": 0,
        "source": {
            "adapter_id": "preview-trace-jsonl",
            "adapter_version": "1",
            "path": str(source),
            "sha256": _sha256(payload),
            "physical_record_count": 13,
        },
        "agent": {"workspace_id": "synthetic", "agent_id": "synthetic-agent"},
        "privacy": {
            "authorization": "SYNTHETIC_FIXTURE",
            "execution_location": "LOCAL_PRIVATE",
            "provider_egress": {
                "authorized": not trace_only,
                "model_id": None if trace_only else "fake-semantic-model-v0",
            },
        },
        "grouping": {
            "highest_dependency_key": "paired_case_id",
            "assignments": [
                {"group_id": group_id, "trace_ids": trace_ids}
                for group_id, trace_ids in GROUPS.items()
            ],
        },
        "capabilities": {
            "paired_arms": not trace_only,
            "outcomes": not trace_only,
            "existing_evals": False,
            "embeddings": False,
        },
        "outcomes": None
        if trace_only
        else [
            {
                "group_id": group_id,
                "trace_id": trace_id,
                "outcome": "SUCCESS",
            }
            for group_id, trace_ids in GROUPS.items()
            for trace_id in trace_ids
        ],
        "existing_evals": None,
    }
    path = tmp_path / ("trace-only-manifest.json" if trace_only else "manifest.json")
    path.write_bytes(_canonical(manifest, lf=True))
    return path


def _response(variant: int = 0) -> dict[str, Any]:
    populations = [
        {
            "label": "Cancellation follow-through",
            "description": "Users seek completion of cancellation.",
            "evidence_trace_ids": ["trace-01", "trace-02"],
        },
        {
            "label": "Delivery detail correction",
            "description": "Users seek an address correction.",
            "evidence_trace_ids": ["trace-03", "trace-04"],
        },
        {
            "label": "Refund status seeking",
            "description": "Users ask for refund progress.",
            "evidence_trace_ids": ["trace-05", "trace-06"],
        },
        {
            "label": "Post-purchase remedy",
            "description": "Users seek exchange, damage, or warranty help.",
            "evidence_trace_ids": [
                "trace-07",
                "trace-08",
                "trace-09",
                "trace-10",
                "trace-11",
                "trace-12",
            ],
        },
    ]
    if variant == 1:
        populations[-1] = {
            "label": "Exchange and damage remedy",
            "description": "Users seek exchange or damage resolution.",
            "evidence_trace_ids": ["trace-07", "trace-08", "trace-09", "trace-10"],
        }
    elif variant == 2:
        populations[2]["label"] = "Refund progress checking"
    return {
        "populations": populations,
        "eval_candidates": [
            {
                "name": "Cancellation completion",
                "criterion": "Complete or safely explain cancellation.",
                "evidence_trace_ids": ["trace-01", "trace-02"],
            },
            {
                "name": "Address-change confirmation",
                "criterion": "Confirm the changed delivery address.",
                "evidence_trace_ids": ["trace-03", "trace-04"],
            },
            {
                "name": "Refund-state evidence",
                "criterion": "State the evidenced refund status.",
                "evidence_trace_ids": ["trace-05", "trace-06"],
            },
            {
                "name": "Warranty explanation",
                "criterion": "Explain the evidenced warranty boundary.",
                "evidence_trace_ids": ["trace-11", "trace-12"],
            },
        ],
    }


class _SemanticModel:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.calls: list[Any] = []

    def _next(self, request: Any) -> dict[str, Any]:
        self.calls.append(request)
        return deepcopy(self.responses[min(len(self.calls) - 1, len(self.responses) - 1)])

    __call__ = _next
    analyze = _next
    invoke = _next


def _api() -> Any:
    spec = importlib.util.find_spec("triana_labs.trace_to_eval")
    assert spec is not None, "Trace-to-Eval public engine package is absent"
    module = importlib.import_module("triana_labs.trace_to_eval")
    assert hasattr(module, "run_trace_to_eval")
    assert hasattr(module, "append_human_ruling")
    return module


def _artifact(output: Path, kind: str) -> tuple[dict[str, Any], bytes]:
    matches = []
    for path in output.glob("*.json"):
        payload = path.read_bytes()
        value = json.loads(payload)
        if isinstance(value, dict) and value.get("artifact_kind") == kind:
            matches.append((value, payload))
    assert len(matches) == 1, (kind, [path.name for path in output.iterdir()])
    return matches[0]


def _ledger(output: Path) -> tuple[Path, list[dict[str, Any]], bytes]:
    matches = []
    for path in output.glob("*.jsonl"):
        payload = path.read_bytes()
        records = [json.loads(line) for line in payload.splitlines()]
        if records and all(item.get("artifact_kind") == "human_ruling_v0" for item in records):
            matches.append((path, records, payload))
    assert len(matches) == 1
    return matches[0]


def _run(manifest: Path, output: Path, responses: list[dict[str, Any]]) -> tuple[Any, Any, Any]:
    model = _SemanticModel(responses)
    returned = _api().run_trace_to_eval(manifest, output, semantic_model=model)
    report, report_bytes = _artifact(output, "trace_to_eval_report_v0")
    queue, queue_bytes = _artifact(output, "review_queue_v0")
    assert returned == report
    assert report_bytes == _canonical(report, lf=True)
    assert queue_bytes == _canonical(queue, lf=True)
    return model, report, queue


def test_trace_path_yields_grounded_report_and_group_safe_splits(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path)
    model, report, queue = _run(manifest_path, tmp_path / "out", [_response()] * 3)
    assert len(model.calls) == 3
    assert report["accounting"] == {
        "physical_record_count": 13,
        "accepted_conversation_count": 12,
        "rejected_record_count": 1,
    }
    assert b"TOP_SECRET_REJECTED_CONTENT" not in _canonical([report, queue])
    assert report["rejections"] == [{
        "line_number": 13,
        "code": "SCHEMA_VALIDATION_FAILED",
        "json_pointer": "/trace_id",
    }]
    corpus_hash = json.loads(manifest_path.read_bytes())["source"]["sha256"]
    ranked = sorted(GROUPS, key=lambda group_id: hashlib.sha256(
        b"triana-split-v0" + corpus_hash.encode() + group_id.encode()
    ).digest())
    expected = {group_id: "DEVELOPMENT" if index < 4 else "CALIBRATION" if index == 4 else "HOLDOUT" for index, group_id in enumerate(ranked)}
    actual = {item["group_id"]: item["split"] for item in report["group_splits"]}
    assert actual == expected
    inventory = {item["trace_id"]: item["split"] for item in report["conversation_inventory"]}
    for group_id, trace_ids in GROUPS.items():
        assert {inventory[trace_id] for trace_id in trace_ids} == {actual[group_id]}
    accepted = set(inventory)
    assert report["populations"] and len(report["eval_proposals"]) <= 3
    assert report["qualified_eval_inventory"]
    for item in [*report["populations"], *report["qualified_eval_inventory"]]:
        assert item["proposal_state"] == "PROPOSED"
        assert set(item["evidence_trace_ids"]) <= accepted


def test_optional_absence_is_typed_not_a_false_claim(tmp_path: Path) -> None:
    output = tmp_path / "out"
    report = _api().run_trace_to_eval(
        _write_manifest(tmp_path, trace_only=True), output, semantic_model=None
    )
    assert report == _artifact(output, "trace_to_eval_report_v0")[0]
    assert report["populations"] == [] and report["eval_proposals"] == []
    assert "SEMANTIC_ANALYSIS_UNAVAILABLE" in {gap["code"] for gap in report["gaps"]}
    assert any(gap.get("capability") == "OUTCOMES" and gap.get("state") == "UNAVAILABLE" for gap in report["gaps"])
    assert "first-broken-link" not in _canonical(report).decode().casefold()
    assert '"verdict":"pass"' not in _canonical(report).decode().casefold()


def test_ungrounded_semantics_are_rejected_without_losing_accounting(tmp_path: Path) -> None:
    response = _response()
    response["populations"][0]["evidence_trace_ids"] = ["trace-not-in-corpus"]
    response["eval_candidates"][0]["evidence_trace_ids"] = []
    _, report, _ = _run(_write_manifest(tmp_path), tmp_path / "out", [response] * 3)
    assert "trace-not-in-corpus" not in _canonical(report).decode()
    assert any(gap["code"] == "UNGROUNDED_SEMANTIC_OUTPUT" for gap in report["gaps"])
    assert report["accounting"]["accepted_conversation_count"] == 12


def test_replays_are_identical_and_fresh_disagreement_is_visible(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)
    payloads = []
    queues = []
    for index in range(10):
        _, report, queue = _run(manifest, tmp_path / f"cached-{index}", [_response()] * 3)
        payloads.append(_canonical(report, lf=True))
        queues.append(_canonical(queue, lf=True))
    assert len(set(payloads)) == len(set(queues)) == 1
    _, varied, _ = _run(manifest, tmp_path / "varied", [_response(0), _response(1), _response(2)])
    assert varied["stability"]["semantic_run_count"] == 3
    assert varied["stability"]["state"] == "DISAGREEMENT_OBSERVED"
    assert varied["stability"]["disagreements"]
    assert varied["stability"]["rerun_selection"] == "NONE"


def test_review_queue_is_deterministic_and_rulings_append_across_refresh(tmp_path: Path) -> None:
    module = _api()
    manifest = _write_manifest(tmp_path)
    output = tmp_path / "out"
    _, report, queue = _run(manifest, output, [_response()] * 3)
    items = queue["items"]
    assert sum(item["item_kind"] == "POPULATION_PAIR" for item in items) <= 4
    assert sum(item["item_kind"] == "EVAL_PROPOSAL" for item in items) <= 3
    assert all("method" not in item and "hidden_truth" not in item for item in items)
    assert [item["item_id"] for item in items] == sorted(
        (item["item_id"] for item in items),
        key=lambda item_id: hashlib.sha256(b"triana-review-v0" + report["report_id"].encode() + item_id.encode()).digest(),
    )
    proposal = next(item for item in items if item["item_kind"] == "EVAL_PROPOSAL")
    ruling = {
        "artifact_kind": "human_ruling_v0", "schema_version": 0,
        "report_id": report["report_id"], "item_id": proposal["item_id"],
        "item_hash": proposal["item_hash"], "decision": "TRACK", "edited_text": None,
        "reviewer_id": "reviewer-synthetic", "ruled_at": "2026-08-07T01:00:00Z",
        "supersedes_ruling_id": None,
    }
    first = module.append_human_ruling(output, ruling)
    path, records, before = _ledger(output)
    assert records == [first]
    second = module.append_human_ruling(output, {
        **ruling, "decision": "EDIT", "edited_text": "Track with safe refusal evidence.",
        "ruled_at": "2026-08-07T01:05:00Z", "supersedes_ruling_id": first["ruling_id"],
    })
    same_path, records, after = _ledger(output)
    assert same_path == path and after.startswith(before) and records == [first, second]
    refreshed = module.run_trace_to_eval(manifest, output, semantic_model=_SemanticModel([_response()] * 3))
    assert refreshed["report_id"] == report["report_id"]
    assert _artifact(output, "review_queue_v0")[0]["items"] == items
    assert _ledger(output)[1] == [first, second]
