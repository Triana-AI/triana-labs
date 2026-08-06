from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from triana_labs.trace_to_eval import (
    TraceToEvalError,
    append_human_ruling,
    read_human_rulings,
    run_trace_to_eval,
)
from triana_labs.trace_to_eval.adapters import prepare_evidence_manifest
from triana_labs.trace_to_eval.semantic import FoundryStructuredSemanticModel


def _line(value: Any) -> bytes:
    return (json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n").encode()


def _message(role: str, content: str) -> dict[str, Any]:
    return {"type": role, "content": content}


def test_grouped_langsmith_combines_session_without_nested_echoes(
    tmp_path: Path,
) -> None:
    rows = [
        {
            "trace_id": "group-1",
            "session_key": "session-1",
            "start_time": "1",
            "runs": [
                {
                    "id": "run-1",
                    "dotted_order": "1",
                    "run_type": "chain",
                    "status": "success",
                    "inputs": {"messages": [_message("human", "Hello")]},
                    "outputs": {"messages": [_message("ai", "Hi")]},
                },
                {
                    "id": "run-2",
                    "dotted_order": "2",
                    "run_type": "llm",
                    "status": "success",
                    "inputs": {"messages": [[_message("human", "Hello")]]},
                    "outputs": {"generations": [[{"text": "Hi"}]]},
                },
            ],
        },
        {
            "trace_id": "group-2",
            "session_key": "session-1",
            "start_time": "2",
            "runs": [
                {
                    "id": "run-3",
                    "dotted_order": "3",
                    "run_type": "chain",
                    "status": "success",
                    "inputs": {
                        "messages": [
                            _message("human", "Hello"),
                            _message("ai", "Hi"),
                            _message("human", "Track it"),
                        ]
                    },
                    "outputs": {"messages": [_message("ai", "On the way")]},
                }
            ],
        },
    ]
    source = tmp_path / "grouped.jsonl"
    source.write_bytes(b"".join(_line(row) for row in rows))
    manifest_path = prepare_evidence_manifest(
        source,
        tmp_path / "prepared",
        source_kind="langsmith-grouped-jsonl",
        semantic_model_id="FW-GLM-5.2",
    )
    manifest = json.loads(manifest_path.read_bytes())
    traces = [
        json.loads(line)
        for line in Path(manifest["source"]["path"]).read_bytes().splitlines()
    ]
    assert len(traces) == 1
    messages = [
        (event["event_kind"], event.get("content"))
        for event in traces[0]["events"]
        if event["event_kind"].endswith("MESSAGE")
    ]
    assert messages == [
        ("USER_MESSAGE", "Hello"),
        ("ASSISTANT_MESSAGE", "Hi"),
        ("USER_MESSAGE", "Track it"),
        ("ASSISTANT_MESSAGE", "On the way"),
    ]
    assert manifest["grouping"]["assignments"] == [
        {
            "group_id": "session-1",
            "trace_ids": ["langsmith-session-84097828fc31a8c8d29210df48901a85"],
        }
    ]
    assert manifest["privacy"]["provider_egress"] == {
        "authorized": False,
        "model_id": None,
    }


def test_hrai_float_arguments_are_preserved_as_canonical_text(tmp_path: Path) -> None:
    row = {
        "schema_version": "normalized-trace-v2",
        "case_id": "case-1",
        "session_id": "session-1",
        "status": "COMPLETED",
        "system_prompt": {"text": "Synthetic system"},
        "turns": [
            {"role": "user", "content": "Score"},
            {"role": "assistant", "content": "Done"},
        ],
        "events": [
            {"turn": 1, "role": "user", "tool_calls": []},
            {
                "turn": 1,
                "role": "assistant",
                "tool_calls": [
                    {
                        "name": "score",
                        "arguments": {"value": 0.5},
                        "result_summary": {"score": 0.5},
                        "status": "ok",
                    }
                ],
            },
        ],
    }
    source = tmp_path / "hrai.jsonl"
    source.write_bytes(_line(row))
    manifest = prepare_evidence_manifest(
        source, tmp_path / "prepared", source_kind="hrai-normalized-jsonl"
    )
    trace = json.loads(
        Path(json.loads(manifest.read_bytes())["source"]["path"]).read_bytes()
    )
    call = next(
        event for event in trace["events"] if event["event_kind"] == "TOOL_CALL"
    )
    result = next(
        event for event in trace["events"] if event["event_kind"] == "TOOL_RESULT"
    )
    assert call["arguments"] == '{"value":0.5}'
    assert result["result"] == '{"score":0.5}'


def test_hrai_noncompleted_rows_are_content_free_accounted_rejections(
    tmp_path: Path,
) -> None:
    completed = {
        "schema_version": "normalized-trace-v2",
        "case_id": "case-1",
        "session_id": "session-1",
        "status": "COMPLETED",
        "system_prompt": {"text": "Synthetic system"},
        "turns": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ],
        "events": [
            {"turn": 1, "role": "user", "tool_calls": []},
            {"turn": 1, "role": "assistant", "tool_calls": []},
        ],
    }
    rejected = {
        "schema_version": "normalized-trace-v2",
        "case_id": "case-secret",
        "session_id": "session-secret",
        "status": "HARNESS_ERROR",
        "turns": [],
        "events": [{"raw": "DO_NOT_LEAK"}],
    }
    source = tmp_path / "hrai.jsonl"
    source.write_bytes(_line(completed) + _line(rejected))
    manifest = prepare_evidence_manifest(
        source, tmp_path / "prepared", source_kind="hrai-normalized-jsonl"
    )
    report = run_trace_to_eval(manifest, tmp_path / "out")
    assert report["accounting"] == {
        "physical_record_count": 2,
        "accepted_conversation_count": 1,
        "rejected_record_count": 1,
    }
    assert report["rejections"] == [
        {
            "line_number": 2,
            "code": "SOURCE_EXECUTION_INCOMPLETE",
            "json_pointer": "/status",
        }
    ]
    assert "DO_NOT_LEAK" not in json.dumps(report)


def test_foundry_openai_v1_endpoint_is_exact_and_no_models_suffix() -> None:
    model = FoundryStructuredSemanticModel.from_environment(
        {
            "TRIANA_TRACE_TO_EVAL_SEMANTIC_PROVIDER": "MICROSOFT_FOUNDRY_FIREWORKS",
            "TRIANA_TRACE_TO_EVAL_MODEL_ID": "FW-GLM-5.2",
            "AZURE_OPENAI_BASE_URL": "https://kairos-openai-1.openai.azure.com/openai/v1",
            "TRIANA_FOUNDRY_API_KEY": "not-a-real-secret",
        }
    )
    assert model is not None and model.endpoint.endswith("/openai/v1")
    assert not model.endpoint.endswith("/models")
    with pytest.raises(ValueError, match="TRACE_TO_EVAL_FOUNDRY_CONFIG_INVALID"):
        FoundryStructuredSemanticModel.from_environment(
            {
                "TRIANA_TRACE_TO_EVAL_SEMANTIC_PROVIDER": "MICROSOFT_FOUNDRY_FIREWORKS",
                "TRIANA_TRACE_TO_EVAL_MODEL_ID": "FW-GLM-5.2",
                "AZURE_OPENAI_BASE_URL": "https://kairos-openai-1.openai.azure.com/models",
                "TRIANA_FOUNDRY_API_KEY": "x",
            }
        )


class _RequestModel:
    model_id = "fake"

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(self, request: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(request)
        ids = [row["trace_id"] for row in request["traces"]]
        return {
            "populations": [
                {
                    "label": "Observed",
                    "description": "Development only",
                    "evidence_trace_ids": ids,
                }
            ],
            "eval_candidates": [
                {
                    "name": "Observed behavior",
                    "criterion": "Review development evidence.",
                    "evidence_trace_ids": ids,
                }
            ],
        }


def test_semantic_scope_seals_non_development_and_ruling_tamper_fails(
    tmp_path: Path,
) -> None:
    traces = [
        {
            "contract_kind": "preview_trace",
            "schema_version": 1,
            "privacy_class": "SYNTHETIC",
            "trace_id": f"trace-{i}",
            "source_trace_id": f"source-{i}",
            "events": [
                {"sequence": 0, "event_kind": "USER_MESSAGE", "content": f"u{i}"},
                {
                    "sequence": 1,
                    "event_kind": "ASSISTANT_MESSAGE",
                    "content": f"a{i}",
                    "is_final": True,
                },
            ],
        }
        for i in range(5)
    ]
    payload = b"".join(_line(trace) for trace in traces)
    source = tmp_path / "traces.jsonl"
    source.write_bytes(payload)
    manifest = {
        "artifact_kind": "evidence_bundle_manifest_v0",
        "schema_version": 0,
        "source": {
            "adapter_id": "test",
            "adapter_version": "1",
            "path": str(source),
            "sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
            "physical_record_count": 5,
        },
        "agent": {"workspace_id": "test", "agent_id": "test"},
        "privacy": {
            "authorization": "SYNTHETIC_FIXTURE",
            "execution_location": "LOCAL_PRIVATE",
            "provider_egress": {"authorized": True, "model_id": "fake"},
        },
        "grouping": {
            "highest_dependency_key": "trace",
            "assignments": [
                {"group_id": f"g-{i}", "trace_ids": [f"trace-{i}"]} for i in range(5)
            ],
        },
        "capabilities": {
            "paired_arms": False,
            "outcomes": False,
            "existing_evals": False,
            "embeddings": False,
        },
        "outcomes": None,
        "existing_evals": None,
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(_line(manifest))
    output = tmp_path / "out"
    model = _RequestModel()
    report = run_trace_to_eval(manifest_path, output, semantic_model=model)
    dev = {
        row["trace_id"]
        for row in report["conversation_inventory"]
        if row["split"] == "DEVELOPMENT"
    }
    assert all(
        {trace["trace_id"] for trace in call["traces"]} == dev for call in model.calls
    )
    assert report["method"]["sealed_calibration_conversation_count"] == 1
    assert report["method"]["sealed_holdout_conversation_count"] == 1
    visible = json.loads((output / "conversations.json").read_bytes())
    assert visible["visible_scope"] == "DEVELOPMENT_ONLY"
    assert {row["trace_id"] for row in visible["conversations"]} == dev
    queue = json.loads((output / "review_queue.json").read_bytes())
    item = next(row for row in queue["items"] if row["item_kind"] == "EVAL_PROPOSAL")
    ruling = append_human_ruling(
        output,
        {
            "report_id": report["report_id"],
            "item_id": item["item_id"],
            "item_hash": item["item_hash"],
            "decision": "TRACK",
            "edited_text": None,
            "reviewer_id": "tester",
            "ruled_at": "2026-08-07T00:00:00Z",
            "supersedes_ruling_id": None,
        },
    )
    assert read_human_rulings(output, report["report_id"]) == [ruling]
    changed = {**ruling, "decision": "DEFER"}
    (output / "human_rulings.jsonl").write_bytes(_line(changed))
    with pytest.raises(TraceToEvalError, match="RULING_LEDGER_TAMPERED"):
        read_human_rulings(output, report["report_id"])


def test_optional_semantic_failure_keeps_deterministic_report(tmp_path: Path) -> None:
    trace = {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": "SYNTHETIC",
        "trace_id": "trace-1",
        "source_trace_id": "source-1",
        "events": [
            {"sequence": 0, "event_kind": "USER_MESSAGE", "content": "Hello"},
            {
                "sequence": 1,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": "Hi",
                "is_final": True,
            },
        ],
    }
    payload = _line(trace)
    source = tmp_path / "traces.jsonl"
    source.write_bytes(payload)
    manifest = {
        "artifact_kind": "evidence_bundle_manifest_v0",
        "schema_version": 0,
        "source": {
            "adapter_id": "test",
            "adapter_version": "1",
            "path": str(source),
            "sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
            "physical_record_count": 1,
        },
        "agent": {"workspace_id": "test", "agent_id": "test"},
        "privacy": {
            "authorization": "SYNTHETIC_FIXTURE",
            "execution_location": "LOCAL_PRIVATE",
            "provider_egress": {"authorized": True, "model_id": "fake"},
        },
        "grouping": {
            "highest_dependency_key": "trace",
            "assignments": [{"group_id": "g-1", "trace_ids": ["trace-1"]}],
        },
        "capabilities": {
            "paired_arms": False,
            "outcomes": False,
            "existing_evals": False,
            "embeddings": False,
        },
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(_line(manifest))

    class FailingModel:
        model_id = "fake"

        def __init__(self) -> None:
            self.calls = 0

        def __call__(self, request: dict[str, Any]) -> dict[str, Any]:
            del request
            self.calls += 1
            raise ValueError("SEMANTIC_BUDGET_EXCEEDED")

    model = FailingModel()
    report = run_trace_to_eval(manifest_path, tmp_path / "out", semantic_model=model)
    assert model.calls == 1
    assert report["accounting"]["accepted_conversation_count"] == 1
    assert report["populations"] == [] and report["eval_proposals"] == []
    assert "SEMANTIC_BUDGET_EXCEEDED" in {gap["code"] for gap in report["gaps"]}
    assert (
        report["method"]["semantic_run_policy"]
        == "PROVIDER_FAILED_NO_RETRY_OR_FALLBACK"
    )
