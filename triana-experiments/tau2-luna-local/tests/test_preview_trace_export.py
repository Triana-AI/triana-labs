"""Black-box acceptance for the verified 57-task TAU² archive export."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "triana-experiments" / "tau2-luna-local"
SCRIPT = PROJECT / "scripts" / "export_preview_trace.py"
ARCHIVE_SHA256 = "2788f37e3fa215548319be116dd1f5b47e70e04b188919e460441ed993a98169"
DEFAULT_ARCHIVE = (
    PROJECT
    / "runs"
    / "downloads"
    / "tau2-retail-discovery-v1"
    / f"{ARCHIVE_SHA256}.tar.gz"
)


def _run_export(archive: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            os.fspath(SCRIPT),
            "--archive",
            os.fspath(archive),
            "--output",
            os.fspath(output),
            "--expected-sha256",
            ARCHIVE_SHA256,
            "--expected-task-count",
            "57",
        ],
        cwd=PROJECT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def _source_attempts(archive: Path) -> dict[str, tuple[str, dict[str, Any]]]:
    attempts: dict[str, tuple[str, dict[str, Any]]] = {}
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            parts = Path(member.name).parts
            if (
                member.isfile()
                and len(parts) == 5
                and parts[0] == "tasks"
                and parts[2] == "attempts"
                and parts[4] == "tau2-results.json"
            ):
                payload = bundle.extractfile(member)
                assert payload is not None
                assert parts[1] not in attempts, "fixture itself must contain one attempt per task"
                attempts[parts[1]] = (parts[3], json.load(payload))
    return attempts


def test_verified_tau57_archive_exports_valid_ordered_preview_traces_reproducibly(
    tmp_path: Path,
) -> None:
    archive = Path(os.environ.get("TRIANA_TAU57_ARCHIVE", DEFAULT_ARCHIVE))
    assert archive.is_file(), f"TAU57_ACCEPTANCE_PRECONDITION: missing {archive}"
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == ARCHIVE_SHA256

    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    for output in (first, second):
        completed = _run_export(archive, output)
        assert completed.returncode == 0, completed.stdout + completed.stderr
    assert first.read_bytes() == second.read_bytes()

    traces = [json.loads(line) for line in first.read_bytes().splitlines()]
    assert len(traces) == 57
    assert len({trace["trace_id"] for trace in traces}) == 57
    assert len({trace["source_trace_id"] for trace in traces}) == 57
    assert [trace["trace_id"] for trace in traces] == sorted(
        trace["trace_id"] for trace in traces
    )

    labs_src = ROOT / "triana-labs" / "src"
    sys.path.insert(0, os.fspath(labs_src))
    try:
        from triana_labs.contracts.traces import parse_and_validate_line

        for line in first.read_bytes().splitlines():
            validated = parse_and_validate_line(line, first_line=False)
            assert validated.value["privacy_class"] == "SYNTHETIC"
    finally:
        sys.path.remove(os.fspath(labs_src))

    sources = _source_attempts(archive)
    assert len(sources) == 57
    for trace in traces:
        lineage = trace["source_trace_id"]
        matching = [task_id for task_id in sources if f"task/{task_id}/" in lineage]
        assert len(matching) == 1
        task_id = matching[0]
        attempt_id, result = sources[task_id]
        simulation = result["simulations"][0]
        assert ARCHIVE_SHA256 in lineage
        assert "tau2-retail-discovery-v1" in lineage
        assert attempt_id in lineage
        assert f"reward={simulation['reward_info']['reward']}" in lineage

        pending_calls: list[str] = []
        observed_structure: list[tuple[str, str | None]] = []
        for event in trace["events"]:
            kind = event["event_kind"]
            if kind == "TOOL_CALL":
                pending_calls.append(event["call_id"])
                observed_structure.append((kind, event["tool_name"]))
            elif kind == "TOOL_RESULT":
                assert pending_calls and event["call_id"] == pending_calls.pop(0)
                observed_structure.append((kind, None))
            elif kind != "TERMINAL":
                observed_structure.append((kind, None))

        expected_structure: list[tuple[str, str | None]] = []
        for message in simulation["messages"]:
            if message["role"] == "user":
                expected_structure.append(("USER_MESSAGE", None))
            elif message["role"] == "assistant":
                if isinstance(message.get("content"), str):
                    expected_structure.append(("ASSISTANT_MESSAGE", None))
                expected_structure.extend(
                    ("TOOL_CALL", call["name"])
                    for call in message.get("tool_calls") or []
                )
            elif message["role"] == "tool":
                expected_structure.append(("TOOL_RESULT", None))
        assert observed_structure == expected_structure
