from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

SECRET = "test-azure-key-never-persist"
EVENT_DOMAIN = b"tau2-luna-local:event:v1\0"
CAPTURED_TELEMETRY = (
    "attempt.call_id",
    "attempt.role_lane",
    "attempt.start_time",
    "attempt.end_time",
    "attempt.duration",
    "attempt.number",
    "attempt.outcome",
    "request.model",
    "request.endpoint_host",
    "request.api_version",
    "request.kwargs",
    "request.messages",
    "request.tools",
    "request.tool_choice",
    "request.retry_setting",
    "response.mapping",
    "response.choices",
    "response.content",
    "response.tool_calls",
    "response.finish_reason",
    "response.identifiers",
    "response.created",
    "response.usage",
    "response.usage.prompt_tokens",
    "response.usage.completion_tokens",
    "response.usage.total_tokens",
    "response.usage.cached_tokens",
    "response.usage.reasoning_tokens",
    "response.cost",
    "response.headers",
    "response.hidden_metadata",
    "response.raw_class",
    "response.reasoning",
    "tau2.messages",
    "tau2.tool_calls",
    "tau2.tool_results",
    "tau2.costs",
    "tau2.usage",
    "tau2.raw_message_data",
    "tau2.termination_reason",
    "tau2.reward",
    "tau2.reward_breakdown",
    "tau2.evaluator_checks",
    "tau2.task_trial_seed",
    "tau2.run_config",
    "bundle.hashes",
    "verification.hashes",
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def event(sequence: int, name: str, payload: dict[str, Any], previous: str | None) -> dict[str, Any]:
    value = {
        "schema_version": "tau2-luna-event/v1",
        "sequence": sequence,
        "event_name": name,
        "timestamp_ns": 1_750_000_000_000_000_000 + sequence,
        "previous_event_hash": previous,
        "payload": payload,
    }
    value["event_hash"] = hashlib.sha256(EVENT_DOMAIN + canonical_bytes(value)).hexdigest()
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical_bytes(value) + b"\n")


def write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.write_bytes(b"".join(canonical_bytes(value) + b"\n" for value in values))


def refresh_manifest(run_dir: Path) -> None:
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["artifacts"] = {
        name: {
            "size": (run_dir / name).stat().st_size,
            "sha256": hashlib.sha256((run_dir / name).read_bytes()).hexdigest(),
        }
        for name in ("events.jsonl", "spans.jsonl", "tau2-results.json")
    }
    write_json(manifest_path, manifest)


@pytest.fixture
def azure_environ(tmp_path: Path) -> dict[str, str]:
    return {
        "AZURE_API_KEY": SECRET,
        "AZURE_API_BASE": "https://unit.openai.azure.com/openai/deployments/luna",
        "AZURE_API_VERSION": "2026-01-01-preview",
        "TAU2_LUNA_DEPLOYMENT": "luna-test-deployment",
        "TAU2_TRACE_ROOT": str(tmp_path / "runs"),
    }


@pytest.fixture
def valid_bundle(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run-fixed"
    run_dir.mkdir()
    request = event(
        1,
        "model.request",
        {
            "call_id": "call-fixed",
            "span_id": "span-model-fixed",
            "role_lane": "agent",
            "attempt": 1,
            "model": "azure/luna-test-deployment",
            "messages": [{"role": "user", "content": "Need order status"}],
            "tools": [{"type": "function", "function": {"name": "lookup_order"}}],
        },
        None,
    )
    response = event(
        2,
        "model.response",
        {
            "call_id": "call-fixed",
            "span_id": "span-model-fixed",
            "duration_ns": 25,
            "response": {
                "id": "resp-fixed",
                "choices": [{"finish_reason": "tool_calls"}],
                "usage": {
                    "prompt_tokens": 9,
                    "completion_tokens": 7,
                    "total_tokens": 16,
                    "completion_tokens_details": {"reasoning_tokens": 3},
                    "prompt_tokens_details": {"cached_tokens": 2},
                },
                "reasoning_content": "returned summary",
            },
            "cost": 0.0025,
            "response_headers": {"x-request-id": "provider-request-fixed"},
            "raw_response_class": "FakeModelResponse",
        },
        request["event_hash"],
    )
    write_jsonl(run_dir / "events.jsonl", [request, response])
    write_jsonl(
        run_dir / "spans.jsonl",
        [
            {
                "name": "model.call",
                "trace_id": "trace-fixed",
                "span_id": "span-model-fixed",
                "parent_span_id": "span-run-fixed",
                "status": "OK",
                "attributes": {"call_id": "call-fixed"},
            }
        ],
    )
    write_json(
        run_dir / "tau2-results.json",
        {
            "task_id": "retail-0",
            "trial": 0,
            "seed": 1729,
            "messages": [
                {"role": "assistant", "tool_calls": [{"id": "tool-1", "name": "lookup_order", "arguments": {"order_id": "O-1"}}]},
                {"role": "tool", "tool_call_id": "tool-1", "name": "lookup_order", "content": {"status": "shipped"}},
            ],
            "termination_reason": "agent_stop",
            "reward": 1.0,
            "reward_breakdown": {"task": 1.0},
            "evaluator_checks": [{"name": "order_status", "passed": True}],
        },
    )
    write_json(
        run_dir / "completeness.json",
        {
            "schema_version": "tau2-luna-completeness/v1",
            "valid": True,
            "telemetry": {
                **{
                    field: {"state": "CAPTURED", "source": "synthetic acceptance fixture"}
                    for field in CAPTURED_TELEMETRY
                },
                "provider_private_chain_of_thought": {"state": "NOT_RETURNED", "source": "azure", "reason": "provider-private"},
            },
        },
    )
    write_json(
        run_dir / "manifest.json",
        {
            "schema_version": "tau2-luna-manifest/v1",
            "run_id": "run-fixed",
            "upstream": {
                "repository": "https://github.com/sierra-research/tau2-bench",
                "commit": "f8de30c298689cbe0117d76a378e7315a17e5bd8",
                "release": "v0.2.0",
            },
            "config": {
                "model": "azure/luna-test-deployment",
                "endpoint_host": "unit.openai.azure.com",
                "api_version": "2026-01-01-preview",
                "seed": 1729,
            },
            "environment_presence": {"AZURE_API_KEY": True},
            "artifacts": {},
        },
    )
    refresh_manifest(run_dir)
    return run_dir
