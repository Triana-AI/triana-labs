"""Black-box acceptance for explicit validated semantic checkpoints."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, ClassVar

import pytest

from triana_labs.trace_to_eval import run_trace_to_eval
from triana_labs.trace_to_eval.semantic import FoundryStructuredSemanticModel

RAW_PROVIDER_MARKER = "RAW_PROVIDER_RESPONSE_MUST_NOT_PERSIST"


def _canonical(value: Any, *, lf: bool = False) -> bytes:
    encoded = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return encoded + (b"\n" if lf else b"")


def _manifest(tmp_path: Path) -> Path:
    traces = []
    assignments = []
    for pair in range(6):
        trace_ids = []
        for arm in range(2):
            trace_id = f"trace-{pair}-{arm}"
            trace_ids.append(trace_id)
            traces.append(
                {
                    "contract_kind": "preview_trace",
                    "schema_version": 1,
                    "privacy_class": "SYNTHETIC",
                    "trace_id": trace_id,
                    "source_trace_id": f"source-{pair}-{arm}",
                    "events": [
                        {
                            "sequence": 0,
                            "event_kind": "USER_MESSAGE",
                            "content": f"Handle synthetic request {pair} {arm}.",
                        },
                        {
                            "sequence": 1,
                            "event_kind": "ASSISTANT_MESSAGE",
                            "content": "The synthetic request was handled.",
                            "is_final": True,
                        },
                    ],
                }
            )
        assignments.append({"group_id": f"pair-{pair}", "trace_ids": trace_ids})
    source = tmp_path / "traces.jsonl"
    source_bytes = b"".join(_canonical(trace, lf=True) for trace in traces)
    source.write_bytes(source_bytes)
    manifest = {
        "artifact_kind": "evidence_bundle_manifest_v0",
        "schema_version": 0,
        "source": {
            "adapter_id": "preview-trace-jsonl",
            "adapter_version": "1",
            "path": str(source),
            "sha256": "sha256:" + hashlib.sha256(source_bytes).hexdigest(),
            "physical_record_count": len(traces),
        },
        "agent": {"workspace_id": "synthetic", "agent_id": "synthetic-agent"},
        "privacy": {
            "authorization": "SYNTHETIC_FIXTURE",
            "execution_location": "LOCAL_PRIVATE",
            "provider_egress": {
                "authorized": True,
                "model_id": "FW-GLM-5.2",
            },
        },
        "grouping": {
            "highest_dependency_key": "paired_case_id",
            "assignments": assignments,
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
    path = tmp_path / "manifest.json"
    path.write_bytes(_canonical(manifest, lf=True))
    return path


class _Message:
    def __init__(self, *, content: str) -> None:
        self.content = content


class _RawResponse:
    def __init__(self, content: str) -> None:
        self.content = content
        self.usage_metadata = {"input_tokens": 11, "output_tokens": 5}
        self.provider_debug_payload = RAW_PROVIDER_MARKER


class _FakeChatOpenAI:
    invocation_count: ClassVar[int] = 0
    fail_on_invocation: ClassVar[int | None] = None
    forbid_invocation: ClassVar[bool] = False

    def __init__(self, **_kwargs: Any) -> None:
        pass

    def bind(self, **_kwargs: Any) -> _FakeChatOpenAI:
        return self

    def invoke(self, messages: list[_Message]) -> _RawResponse:
        type(self).invocation_count += 1
        if self.forbid_invocation:
            raise AssertionError("provider must not be called for a checkpoint refusal")
        if self.fail_on_invocation == self.invocation_count:
            raise RuntimeError("synthetic transport failure")
        request = json.loads(messages[1].content)
        stage = request.pop("stage")
        if stage.endswith("facets-0"):
            result = {
                "facets": [
                    {
                        "trace_id": trace["trace_id"],
                        "demand_summary": "Handle a synthetic request.",
                        "goal_label": "synthetic request handling",
                        "handling_mode": "INFORMATION_RETURNED",
                        "claimed_action": "FALSE",
                        "terminal_summary": "A response was returned.",
                        "evidence_quotes": ["USER_MESSAGE:"],
                    }
                    for trace in request["traces"]
                ]
            }
        else:
            assert stage.endswith("population-consolidation-final")
            result = {
                "populations": [
                    {
                        "label": "Synthetic request handling",
                        "description": "Users ask the agent to handle a synthetic request.",
                        "kind": "PROPOSED_GOAL",
                        "member_labels": [row["label"] for row in request["labels"]],
                    }
                ]
            }
        return _RawResponse(json.dumps(result))


@pytest.fixture
def provider(monkeypatch: pytest.MonkeyPatch) -> type[_FakeChatOpenAI]:
    messages = ModuleType("langchain_core.messages")
    messages.HumanMessage = _Message  # type: ignore[attr-defined]
    messages.SystemMessage = _Message  # type: ignore[attr-defined]
    openai = ModuleType("langchain_openai")
    openai.ChatOpenAI = _FakeChatOpenAI  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "langchain_core.messages", messages)
    monkeypatch.setitem(sys.modules, "langchain_openai", openai)
    _FakeChatOpenAI.invocation_count = 0
    _FakeChatOpenAI.fail_on_invocation = None
    _FakeChatOpenAI.forbid_invocation = False
    return _FakeChatOpenAI


def _model() -> FoundryStructuredSemanticModel:
    return FoundryStructuredSemanticModel(
        model_id="FW-GLM-5.2",
        endpoint="https://kairos-openai-1.openai.azure.com/openai/v1",
        api_key="synthetic-test-key",
    )


def _lineage(report: dict[str, Any]) -> dict[str, Any]:
    lineage = report["method"]["semantic_lineage"]
    assert isinstance(lineage, dict)
    return lineage


def _checkpoints(output: Path) -> list[Path]:
    matches = []
    for path in output.rglob("*.json"):
        value = json.loads(path.read_bytes())
        if (
            isinstance(value, dict)
            and value.get("artifact_kind") == "semantic_checkpoint_v0"
        ):
            matches.append(path)
    return sorted(matches)


def test_valid_stages_checkpoint_exact_identity_without_raw_provider_response(
    tmp_path: Path, provider: type[_FakeChatOpenAI]
) -> None:
    output = tmp_path / "output"
    report = run_trace_to_eval(_manifest(tmp_path), output, semantic_model=_model())

    lineage = _lineage(report)
    assert lineage["attempted_call_count"] == provider.invocation_count == 6
    assert lineage["successful_call_count"] == 6
    assert lineage["validated_checkpoint_hit_count"] == 0
    assert lineage["resume_policy"] == "EXPLICIT_VALIDATED_CHECKPOINTS_ONLY"
    checkpoints = _checkpoints(output)
    assert len(checkpoints) == 6
    for path in checkpoints:
        checkpoint = json.loads(path.read_bytes())
        assert checkpoint["schema_version"] == 0
        assert set(checkpoint["identity"]) == {
            "model_id",
            "stage",
            "system_sha256",
            "canonical_payload_sha256",
            "requested_schema_sha256",
        }
        assert checkpoint["identity"]["model_id"] == "FW-GLM-5.2"
        assert all(
            checkpoint["identity"][field].startswith("sha256:")
            for field in (
                "system_sha256",
                "canonical_payload_sha256",
                "requested_schema_sha256",
            )
        )
    assert RAW_PROVIDER_MARKER.encode() not in b"".join(
        path.read_bytes() for path in output.rglob("*") if path.is_file()
    )


def test_explicit_same_run_reuses_only_valid_checkpoints_with_zero_provider_cost(
    tmp_path: Path, provider: type[_FakeChatOpenAI]
) -> None:
    output = tmp_path / "output"
    manifest = _manifest(tmp_path)
    first = run_trace_to_eval(manifest, output, semantic_model=_model())
    before = {
        path.relative_to(output): path.read_bytes() for path in _checkpoints(output)
    }
    provider.invocation_count = 0
    provider.forbid_invocation = True

    resumed = run_trace_to_eval(manifest, output, semantic_model=_model())

    assert resumed["populations"] == first["populations"]
    lineage = _lineage(resumed)
    assert lineage["attempted_call_count"] == 0
    assert lineage["successful_call_count"] == 0
    assert lineage["input_tokens"] == lineage["output_tokens"] == 0
    assert lineage["budget"]["reserved_usd"] == 0
    assert lineage["validated_checkpoint_hit_count"] == 6
    assert lineage["resume_policy"] == "EXPLICIT_VALIDATED_CHECKPOINTS_ONLY"
    assert {
        path.relative_to(output): path.read_bytes() for path in _checkpoints(output)
    } == before

    _checkpoints(output)[0].unlink()
    provider.invocation_count = 0
    provider.forbid_invocation = False
    partial = run_trace_to_eval(manifest, output, semantic_model=_model())
    partial_lineage = _lineage(partial)
    assert provider.invocation_count == partial_lineage["attempted_call_count"] == 1
    assert partial_lineage["successful_call_count"] == 1
    assert partial_lineage["validated_checkpoint_hit_count"] == 5
    assert len(_checkpoints(output)) == 6


def test_failed_response_is_not_cached_and_is_called_on_explicit_resume(
    tmp_path: Path, provider: type[_FakeChatOpenAI]
) -> None:
    output = tmp_path / "output"
    manifest = _manifest(tmp_path)
    provider.fail_on_invocation = 2
    failed = run_trace_to_eval(manifest, output, semantic_model=_model())
    assert _lineage(failed)["attempted_call_count"] == 2
    assert _lineage(failed)["successful_call_count"] == 1
    assert len(_checkpoints(output)) == 1
    provider.invocation_count = 0
    provider.fail_on_invocation = None

    resumed = run_trace_to_eval(manifest, output, semantic_model=_model())

    lineage = _lineage(resumed)
    assert lineage["attempted_call_count"] == 5
    assert lineage["successful_call_count"] == 5
    assert lineage["validated_checkpoint_hit_count"] == 1
    assert len(_checkpoints(output)) == 6


@pytest.mark.parametrize("tamper", ["corrupt", "mismatched", "schema-invalid"])
def test_invalid_checkpoint_fails_closed_without_provider_fallback(
    tmp_path: Path, provider: type[_FakeChatOpenAI], tamper: str
) -> None:
    output = tmp_path / "output"
    manifest = _manifest(tmp_path)
    run_trace_to_eval(manifest, output, semantic_model=_model())
    checkpoints = _checkpoints(output)
    target = checkpoints[0]
    if tamper == "corrupt":
        target.write_bytes(b"{")
    elif tamper == "mismatched":
        target.write_bytes(checkpoints[-1].read_bytes())
    else:
        value = json.loads(target.read_bytes())
        value["result"] = {}
        target.write_bytes(_canonical(value, lf=True))
    provider.invocation_count = 0
    provider.forbid_invocation = True

    report = run_trace_to_eval(manifest, output, semantic_model=_model())

    assert provider.invocation_count == 0
    assert "SEMANTIC_CHECKPOINT_INVALID" in {gap["code"] for gap in report["gaps"]}
    lineage = _lineage(report)
    assert lineage["attempted_call_count"] == 0
    assert lineage["last_failure_code"] == "SEMANTIC_CHECKPOINT_INVALID"
    assert lineage["fallback_policy"] == "NONE"
