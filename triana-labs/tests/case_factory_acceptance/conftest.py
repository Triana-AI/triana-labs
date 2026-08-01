"""Independent contract oracles and fake-provider harness for LABS-04."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = REPOSITORY_ROOT / "triana-labs"
SCHEMA_ROOT = REPOSITORY_ROOT / "internal" / "labs04_provider_schemas"
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "case_factory_fixtures"
OUTPUT_NAMES = {
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
ENVIRON = {
    "AZURE_OPENAI_ENDPOINT": "https://operator.example.azure.com",
    "AZURE_OPENAI_API_KEY": "PRIVATE_TEST_KEY_123456789",
    "TRIANA_LABS04_SECRET_SENTINEL": "PRIVATE_SENTINEL_123456789",
}


def canonical(value: Any, *, lf: bool = False) -> bytes:
    payload = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return payload + (b"\n" if lf else b"")


def artifact_hash(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def domain_hash(kind: str, value: Any) -> str:
    prefix = f"triana.labs.case-factory.v1.{kind}".encode() + b"\0"
    return f"sha256:{hashlib.sha256(prefix + canonical(value)).hexdigest()}"


def byte_hash(kind: str, payload: bytes) -> str:
    prefix = f"triana.labs.case-factory.v1.{kind}".encode() + b"\0"
    return f"sha256:{hashlib.sha256(prefix + payload).hexdigest()}"


def compact_id(kind: str, value: Any) -> str:
    prefixes = {
        "citation": "citation-",
        "claim": "claim-",
        "persona": "persona-",
        "intent": "intent-",
        "turn-policy": "turn-policy-",
        "case": "case-",
        "attempt": "attempt-",
        "blind-item": "blind-",
        "duplicate-cluster": "duplicate-cluster-",
    }
    return prefixes[kind] + domain_hash(kind, value)[7:23]


def trace(trace_id: str, user: str, assistant: str) -> dict[str, Any]:
    return {
        "contract_kind": "preview_trace",
        "events": [
            {
                "sequence": 0,
                "event_kind": "SYSTEM_VISIBLE_MESSAGE",
                "content": "PRIVATE_SYSTEM",
            },
            {"sequence": 1, "event_kind": "USER_MESSAGE", "content": user},
            {
                "sequence": 2,
                "event_kind": "TOOL_CALL",
                "call_id": f"call-{trace_id}",
                "tool_name": "lookup_safe",
                "arguments": {"secret": "PRIVATE_ARGUMENT"},
            },
            {
                "sequence": 3,
                "event_kind": "TOOL_RESULT",
                "call_id": f"call-{trace_id}",
                "result_state": "SUCCEEDED",
                "result": {"secret": "PRIVATE_RESULT"},
            },
            {
                "sequence": 4,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": assistant,
                "is_final": True,
            },
            {
                "sequence": 5,
                "event_kind": "TERMINAL",
                "terminal_state": "ERROR",
                "reason_code": "PRIVATE_REASON",
            },
        ],
        "privacy_class": "SYNTHETIC",
        "schema_version": 1,
        "source_trace_id": f"source-{trace_id}-private",
        "trace_id": trace_id,
    }


def _profile(traces: list[dict[str, Any]], rejected: int) -> dict[str, Any]:
    kinds: Counter[str] = Counter(
        {
            name: 0
            for name in (
                "ASSISTANT_MESSAGE",
                "SYSTEM_VISIBLE_MESSAGE",
                "TERMINAL",
                "TOOL_CALL",
                "TOOL_RESULT",
                "USER_MESSAGE",
            )
        }
    )
    tools: Counter[str] = Counter()
    terminals: Counter[str] = Counter()
    for item in traces:
        for event in item["events"]:
            kinds[event["event_kind"]] += 1
            if event["event_kind"] == "TOOL_CALL":
                tools[event["tool_name"]] += 1
            if event["event_kind"] == "TERMINAL":
                terminals[event["terminal_state"]] += 1
    return {
        "accepted_count": len(traces),
        "artifact_kind": "corpus_profile",
        "case_generation_eligible_count": len(traces),
        "distress_analysis": "NOT_EVALUATED",
        "event_kind_counts": dict(sorted(kinds.items())),
        "input_count": len(traces) + rejected,
        "language_analysis": "NOT_EVALUATED",
        "rejected_count": rejected,
        "rejection_code_counts": {"MALFORMED_JSON": rejected} if rejected else {},
        "schema_version": 1,
        "terminal_state_counts": {
            name: terminals[name] for name in ("ABORTED", "ERROR", "SUCCESS")
        },
        "tool_call_counts": dict(sorted(tools.items())),
    }


def build_upstream(
    tmp_path: Path,
    traces: list[dict[str, Any]] | None = None,
    *,
    rejected: int = 0,
) -> tuple[Path, Path]:
    traces = traces or [
        trace("trace-alpha", "Need bilingual ayuda", "I can help"),
        trace("trace-beta", "Need code-switched सहायता", "I can assist"),
    ]
    observed = tmp_path / "observed"
    observed.mkdir(parents=True)
    normalized = b"".join(canonical(item, lf=True) for item in traces)
    rejected_bytes = b"".join(
        canonical(
            {
                "code": "MALFORMED_JSON",
                "json_pointer": "",
                "line_number": len(traces) + index + 1,
                "safe_message": "Input line is not valid JSON.",
            },
            lf=True,
        )
        for index in range(rejected)
    )
    payloads = {
        "normalized_traces.jsonl": normalized,
        "rejected_traces.jsonl": rejected_bytes,
        "corpus_profile.json": canonical(_profile(traces, rejected), lf=True),
        "corpus_profile.md": b"# Synthetic profile\n",
    }
    for name, payload in payloads.items():
        (observed / name).write_bytes(payload)
    observer_manifest = {
        "accepted_count": len(traces),
        "artifact_kind": "corpus_manifest",
        "artifacts": {
            name: artifact_hash(payload) for name, payload in payloads.items()
        },
        "case_generation_eligible_count": len(traces),
        "input_count": len(traces) + rejected,
        "privacy_class": "SYNTHETIC",
        "rejected_count": rejected,
        "schema_version": 1,
    }
    observer = observed / "manifest.json"
    observer.write_bytes(canonical(observer_manifest, lf=True))
    intelligence = tmp_path / "intelligence"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "triana_labs",
            "corpus",
            "derive",
            str(observer),
            "--out",
            str(intelligence),
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        timeout=30,
    )
    assert completed.returncode == 10, completed.stderr.decode(errors="replace")
    return observer, intelligence / "manifest.json"


def config_value() -> dict[str, Any]:
    return {
        "artifact_kind": "case_factory_config",
        "schema_version": 1,
        "provider": {
            "provider_kind": "AZURE_OPENAI",
            "endpoint_env": "AZURE_OPENAI_ENDPOINT",
            "api_key_env": "AZURE_OPENAI_API_KEY",
            "secret_sentinel_envs": ["TRIANA_LABS04_SECRET_SENTINEL"],
            "allowed_endpoint_host": "operator.example.azure.com",
            "api_surface": "/openai/v1/chat/completions",
            "deployment": "gpt-4.1-mini",
            "model_name": "gpt-4.1-mini",
            "model_version": "2025-04-14",
        },
        "authorization": {
            "allow_provider_egress": True,
            "privacy_classes": ["SYNTHETIC"],
            "allowed_projection": "LABS04_SYNTHETIC_SEMANTIC_EVIDENCE_V1",
        },
        "generation": {
            "candidate_count": 5,
            "evidence_trace_limit": 25,
            "seed": 2026080104,
        },
        "budget": {
            "max_calls": 3,
            "normal_calls": 3,
            "max_input_bytes_per_call": 240000,
            "max_output_tokens_per_call": 12000,
            "max_wall_clock_seconds": 600,
            "request_timeout_seconds": 60,
            "max_transport_retries_per_stage": 0,
            "max_usd": "8.700000",
            "conservative_input_usd_per_million_tokens": "10.000000",
            "conservative_output_usd_per_million_tokens": "40.000000",
            "pricing_source": "OPERATOR_CONSERVATIVE_BOUND",
        },
    }


def write_config(tmp_path: Path, value: dict[str, Any] | None = None) -> Path:
    path = tmp_path / "config.json"
    path.write_bytes(canonical(value or config_value(), lf=True))
    return path


def api() -> tuple[Any, Any]:
    generate_module = importlib.import_module("triana_labs.case_factory.generate")
    provider_module = importlib.import_module("triana_labs.case_factory.provider")
    return generate_module, provider_module


class ScriptedTransport:
    def __init__(self, callbacks: list[Any]) -> None:
        self.callbacks = callbacks
        self.requests: list[Any] = []

    def send(self, request: Any) -> Any:
        self.requests.append(request)
        action = self.callbacks[len(self.requests) - 1]
        if isinstance(action, BaseException):
            raise action
        response = action(request) if callable(action) else action
        return SimpleNamespace(status_code=response[0], body=response[1])


class CapturePublisher:
    def __init__(self, *, cleanup_failed: bool | None = None) -> None:
        self.artifacts: Mapping[str, bytes] | None = None
        self.cleanup_failed = cleanup_failed

    def publish(self, output_path: Path, artifacts: Mapping[str, bytes]) -> None:
        self.artifacts = dict(artifacts)
        if self.cleanup_failed is not None:
            _, provider = api()
            raise provider.PublicationFailure(cleanup_failed=self.cleanup_failed)


class ScriptedClock:
    def __init__(self, values: list[int]) -> None:
        self.values = iter(values)
        self.last = values[-1]

    def monotonic_ns(self) -> int:
        return next(self.values, self.last)


def request_user_value(request: Any) -> dict[str, Any]:
    envelope = json.loads(request.body)
    return json.loads(envelope["messages"][1]["content"])


def valid_proposal(
    citations: list[dict[str, Any]], *, duplicate: bool = False
) -> dict[str, Any]:
    citation_ids = [item["citation_id"] for item in citations]
    by_trace: dict[str, str] = {}
    for item in citations:
        by_trace.setdefault(item["trace_id"], item["citation_id"])
    support = sorted(by_trace.values())[:2]
    population_state = "SUPPORTED" if len(support) >= 2 else "SINGLE_OBSERVATION"
    observed = lambda text, key: {
        "text": text,
        "basis": "OBSERVED",
        "claim_keys": [key],
    }
    generated = lambda text: {
        "text": text,
        "basis": "GENERATED_VARIATION",
        "claim_keys": [],
    }
    claim = lambda key, text, ids, state: {
        "claim_key": key,
        "claim": text,
        "support_state": state,
        "citation_ids": sorted(ids),
    }
    persona = {
        "persona_key": "persona",
        "label": "Careful requester",
        "behavioral_traits": [
            observed("Checks details before proceeding", "persona_claim")
        ],
        "communication_tendencies": [],
        "constraints": [],
        "grounding_claims": [
            claim("persona_claim", "Checks details", support, population_state)
        ],
    }
    intent = {
        "intent_key": "intent",
        "goal": observed("Complete a supported request", "intent_claim"),
        "known_constraints": [],
        "observed_success_signals": [],
        "observed_failure_or_abandonment_signals": [],
        "grounding_claims": [
            claim("intent_claim", "Requests assistance", support, population_state)
        ],
    }
    policy = {
        "turn_policy_key": "policy",
        "information_reveal_policy": [],
        "reaction_rules": [
            observed("Clarify after an incomplete answer", "policy_claim")
        ],
        "clarification_behavior": [],
        "escalation_tendencies": [],
        "stop_conditions": [generated("Stop when the request is resolved")],
        "forbidden_inventions": [],
        "grounding_claims": [
            claim("policy_claim", "Continues after response", support, population_state)
        ],
    }
    cases = []
    single = citation_ids[0]
    for index in range(5):
        suffix = 0 if duplicate else index
        cases.append(
            {
                "case_key": f"case_{index}",
                "persona_key": "persona",
                "intent_key": "intent",
                "turn_policy_key": "policy",
                "scenario": {
                    "opening_user_turn": observed(
                        f"Opening request variant {suffix}", f"case_claim_{index}"
                    ),
                    "known_facts": [],
                    "private_user_facts": [],
                    "unknowns": [],
                    "allowed_user_actions": [generated("May clarify")],
                    "tool_world_constraints": [],
                    "termination_conditions": [generated("Resolved")],
                    "expected_tool_names": [f"tool_{suffix}"],
                    "stressor_codes": [f"STRESS_{suffix}"],
                },
                "grounding_claims": [
                    claim(
                        f"case_claim_{index}",
                        f"Observed anchor {index}",
                        [single],
                        "SINGLE_OBSERVATION",
                    )
                ],
                "proposed_evaluation": {
                    "criteria": [generated("Agent adapts to clarification")],
                    "abstain_conditions": [generated("Evidence is unavailable")],
                },
                "gaps": [],
            }
        )
    return {
        "personas": [persona],
        "intents": [intent],
        "turn_policies": [policy],
        "cases": cases,
    }


def proposal_callback(
    *, duplicate: bool = False, mutate: Callable[[dict[str, Any]], None] | None = None
) -> Any:
    def respond(request: Any) -> tuple[int, bytes]:
        user = request_user_value(request)
        proposal = valid_proposal(user["citations"], duplicate=duplicate)
        if mutate:
            mutate(proposal)
        return 200, azure_body(proposal)

    return respond


def critique_callback(request: Any) -> tuple[int, bytes]:
    user = request_user_value(request)
    assert "proposal" in user and "evidence" in user
    return 200, azure_body({"issues": []})


def azure_body(content: Any, *, finish: str = "stop", extra: bool = False) -> bytes:
    value: dict[str, Any] = {
        "choices": [
            {"message": {"content": json.dumps(content)}, "finish_reason": finish}
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }
    if extra:
        value["provider_request_id"] = "PRIVATE_REQUEST_ID"
    return canonical(value)


def invoke(
    tmp_path: Path,
    callbacks: list[Any],
    *,
    traces: list[dict[str, Any]] | None = None,
    rejected: int = 0,
    config: dict[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
    clock: Any = None,
    publisher: Any = None,
    cache_path: Path | None = None,
) -> tuple[Any, ScriptedTransport, Any, Path]:
    observer, intelligence = build_upstream(tmp_path, traces, rejected=rejected)
    config_path = write_config(tmp_path, config)
    generate_module, _ = api()
    transport = ScriptedTransport(callbacks)
    output = tmp_path / "case-factory"
    result = generate_module.generate(
        observer,
        intelligence,
        config_path,
        output,
        cache_path=cache_path or tmp_path / "provider-cache",
        transport=transport,
        clock=clock,
        environ=dict(environ or ENVIRON),
        publisher=publisher,
    )
    return result, transport, publisher, output


@pytest.fixture
def success_callbacks() -> list[Any]:
    return [proposal_callback(), critique_callback, proposal_callback()]


@dataclass(frozen=True)
class CliResult:
    returncode: int
    stdout: bytes
    stderr: bytes


def run_cli(*args: str | Path, env: Mapping[str, str] | None = None) -> CliResult:
    child_env = os.environ.copy()
    child_env.update(env or {})
    completed = subprocess.run(
        [sys.executable, "-m", "triana_labs", *(os.fspath(item) for item in args)],
        cwd=PROJECT_ROOT,
        env=child_env,
        check=False,
        capture_output=True,
        timeout=30,
    )
    return CliResult(completed.returncode, completed.stdout, completed.stderr)
