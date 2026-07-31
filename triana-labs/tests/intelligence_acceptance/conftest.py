"""Independent black-box harness for structural Corpus Intelligence."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = REPOSITORY_ROOT / "triana-labs"
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "intelligence_fixtures"
OUTPUT_NAMES = {
    "manifest.json",
    "clusters.json",
    "derivation_report.json",
    "personas/index.json",
    "intents/index.json",
    "turn_policies/index.json",
}
FIDELITY = "SYNTHETIC_OBSERVED_STRUCTURE"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: bytes
    stderr: bytes

    def stdout_json(self) -> dict[str, Any]:
        value = json.loads(self.stdout)
        assert isinstance(value, dict)
        return value

    def stderr_json(self) -> dict[str, Any]:
        lines = self.stderr.splitlines()
        assert len(lines) == 1
        value = json.loads(lines[0])
        assert isinstance(value, dict)
        return value


def compact_json(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def digest(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def read_fixture_traces() -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (FIXTURE_ROOT / "structural_traces.jsonl").read_bytes().splitlines()
    ]


def _profile(traces: list[dict[str, Any]], rejected_count: int) -> dict[str, Any]:
    event_kinds: Counter[str] = Counter()
    terminals: Counter[str] = Counter()
    tools: Counter[str] = Counter()
    eligible = 0
    for trace in traces:
        user_seen = False
        trace_eligible = False
        for event in trace["events"]:
            kind = event["event_kind"]
            event_kinds[kind] += 1
            if kind == "USER_MESSAGE":
                user_seen = True
            elif user_seen and kind in {"ASSISTANT_MESSAGE", "TOOL_CALL"}:
                trace_eligible = True
            if kind == "TERMINAL":
                terminals[event["terminal_state"]] += 1
            if kind == "TOOL_CALL":
                tools[event["tool_name"]] += 1
        eligible += int(trace_eligible)
    return {
        "accepted_count": len(traces),
        "artifact_kind": "corpus_profile",
        "case_generation_eligible_count": eligible,
        "distress_analysis": "NOT_EVALUATED",
        "event_kind_counts": dict(sorted(event_kinds.items())),
        "input_count": len(traces) + rejected_count,
        "language_analysis": "NOT_EVALUATED",
        "rejected_count": rejected_count,
        "rejection_code_counts": (
            {"MALFORMED_JSON": rejected_count} if rejected_count else {}
        ),
        "schema_version": 1,
        "terminal_state_counts": {
            state: terminals[state] for state in ("ABORTED", "ERROR", "SUCCESS")
        },
        "tool_call_counts": dict(sorted(tools.items())),
    }


def build_observer_bundle(
    root: Path,
    traces: list[dict[str, Any]] | None = None,
    *,
    rejected_count: int = 0,
) -> Path:
    root.mkdir()
    if traces is None:
        traces = read_fixture_traces()
    normalized = b"".join(compact_json(trace) for trace in traces)
    rejected = b"".join(
        compact_json(
            {
                "code": "MALFORMED_JSON",
                "json_pointer": "",
                "line_number": len(traces) + index + 1,
                "safe_message": "Input line is not valid JSON.",
            }
        )
        for index in range(rejected_count)
    )
    profile = compact_json(_profile(traces, rejected_count))
    markdown = b"# Synthetic Observer profile\n"
    payloads = {
        "normalized_traces.jsonl": normalized,
        "rejected_traces.jsonl": rejected,
        "corpus_profile.json": profile,
        "corpus_profile.md": markdown,
    }
    for name, payload in payloads.items():
        (root / name).write_bytes(payload)
    profile_value = json.loads(profile)
    manifest = {
        "accepted_count": len(traces),
        "artifact_kind": "corpus_manifest",
        "artifacts": {name: digest(payload) for name, payload in payloads.items()},
        "case_generation_eligible_count": profile_value[
            "case_generation_eligible_count"
        ],
        "input_count": len(traces) + rejected_count,
        "privacy_class": "SYNTHETIC",
        "rejected_count": rejected_count,
        "schema_version": 1,
    }
    (root / "manifest.json").write_bytes(compact_json(manifest))
    return root / "manifest.json"


@pytest.fixture
def run_cli() -> Callable[..., CommandResult]:
    def run(
        *arguments: str | os.PathLike[str],
        env: Mapping[str, str] | None = None,
        preexec_fn: Callable[[], None] | None = None,
    ) -> CommandResult:
        child_env = os.environ.copy()
        if env:
            child_env.update(env)
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "triana_labs",
                *(os.fspath(arg) for arg in arguments),
            ],
            cwd=PROJECT_ROOT,
            env=child_env,
            preexec_fn=preexec_fn,
            check=False,
            capture_output=True,
            timeout=30,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)

    return run


def assert_refusal(result: CommandResult, reason: str, exit_code: int) -> None:
    assert result.returncode == exit_code
    assert result.stdout == b""
    assert result.stderr_json() == {
        "command": "corpus.derive",
        "duration_ms": result.stderr_json()["duration_ms"],
        "event_name": "triana.corpus.derive.rejected",
        "outcome": "REJECTED",
        "reason_code": reason,
        "service": "triana-labs-cli",
        "service_version": "0.0.0",
        "severity": "ERROR",
    }
    assert type(result.stderr_json()["duration_ms"]) is int
    assert result.stderr_json()["duration_ms"] >= 0
