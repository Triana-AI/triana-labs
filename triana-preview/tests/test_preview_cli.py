"""Independent black-box acceptance contract for Triana Preview local alpha."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import threading
from pathlib import Path

import pytest
from conftest import (
    PREVIEW_ROOT,
    REPOSITORY_ROOT,
    analyze_arguments,
    machine_json,
    provider_disabled_environment,
    run_preview,
)

from triana_preview import cli as preview_cli


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _all_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())


def _assert_private(path: Path, expected: int) -> None:
    assert stat.S_IMODE(path.stat().st_mode) == expected


def test_missing_authorization_refuses_before_output_or_source_access(
    tmp_path: Path,
) -> None:
    source = tmp_path / "does-not-exist.jsonl"
    output = tmp_path / "result"

    completed = run_preview(*analyze_arguments(source, output, authorized=False))

    assert completed.returncode == 2
    assert machine_json(completed)["reason_code"] == "TRACE_AUTHORIZATION_REQUIRED"
    assert not output.exists()


@pytest.mark.parametrize(
    ("mutation", "reason_code"),
    [
        ("invalid", "PREVIEW_TRACE_INPUT_INVALID"),
        ("symlink", "PREVIEW_TRACE_INPUT_UNSAFE"),
    ],
)
def test_invalid_or_symlinked_input_refuses_without_empty_report(
    tmp_path: Path,
    synthetic_trace: Path,
    mutation: str,
    reason_code: str,
) -> None:
    source = tmp_path / "input.jsonl"
    if mutation == "invalid":
        source.write_text("{not-json}\n", encoding="utf-8")
    else:
        source.symlink_to(synthetic_trace)
    output = tmp_path / "result"

    completed = run_preview(*analyze_arguments(source, output))

    assert completed.returncode == 2
    assert machine_json(completed)["reason_code"] == reason_code
    assert not (output / "behavior-map.json").exists()


def test_nonempty_output_refuses_without_overwriting_evidence(
    tmp_path: Path, synthetic_trace: Path
) -> None:
    output = tmp_path / "result"
    output.mkdir()
    existing = output / "owner-evidence.txt"
    existing.write_bytes(b"preserve-me")

    completed = run_preview(*analyze_arguments(synthetic_trace, output))

    assert completed.returncode == 2
    assert machine_json(completed)["reason_code"] == "OUTPUT_NOT_EMPTY"
    assert existing.read_bytes() == b"preserve-me"
    assert _all_files(output) == [existing]


def test_partial_provider_configuration_refuses_before_child_engine(
    tmp_path: Path, synthetic_trace: Path
) -> None:
    output = tmp_path / "result"
    environment = provider_disabled_environment(
        {"TRIANA_BEHAVIOR_MAP_PROVIDER": "MICROSOFT_FOUNDRY_OPENAI_V1"}
    )

    completed = run_preview(
        *analyze_arguments(synthetic_trace, output), environment=environment
    )

    assert completed.returncode == 2
    assert machine_json(completed)["reason_code"] == "PROVIDER_CONFIG_INCOMPLETE"
    assert not output.exists()


def test_valid_no_provider_run_uses_labs_and_preserves_local_custody(
    tmp_path: Path, synthetic_trace: Path
) -> None:
    source_before = synthetic_trace.read_bytes()
    output = tmp_path / "result"
    environment = provider_disabled_environment(
        {"TRIANA_PREVIEW_SECRET_CANARY": "must-never-enter-artifacts"}
    )

    completed = run_preview(
        *analyze_arguments(synthetic_trace, output), environment=environment
    )

    assert completed.returncode == 10, completed.stderr
    receipt = machine_json(completed)
    assert receipt["outcome"] == "COMPLETED_WITH_GAPS"
    assert receipt["provider_calls"] == 0
    assert synthetic_trace.read_bytes() == source_before
    assert output.is_dir()
    _assert_private(output, 0o700)
    expected = {
        "input.redacted.jsonl",
        "redaction-audit.json",
        "manifest.json",
        "behavior-map.json",
        "behavior-map.md",
        "behavior-map.html",
        "run-manifest.json",
    }
    assert expected <= {path.name for path in _all_files(output)}
    assert not (output / synthetic_trace.name).exists()
    for name in ("input.redacted.jsonl", "redaction-audit.json", "manifest.json"):
        _assert_private(output / name, 0o600)

    combined = b"\n".join(path.read_bytes() for path in _all_files(output))
    assert source_before not in combined
    assert b"preview-customer@example.invalid" not in combined
    assert b"ORD-TEST01" not in combined
    assert b"must-never-enter-artifacts" not in combined
    assert b"TRIANA_BEHAVIOR_MAP_PRIMARY_API_KEY" not in combined


def test_run_manifest_binds_redacted_input_and_report_accounting(
    tmp_path: Path, synthetic_trace: Path
) -> None:
    output = tmp_path / "result"
    completed = run_preview(*analyze_arguments(synthetic_trace, output))
    assert completed.returncode == 10, completed.stderr

    redacted = (output / "input.redacted.jsonl").read_bytes()
    evidence_manifest = json.loads((output / "manifest.json").read_bytes())
    run_manifest = json.loads((output / "run-manifest.json").read_bytes())
    report = json.loads((output / "behavior-map.json").read_bytes())

    assert run_manifest["redacted_source_sha256"] == _sha256(redacted)
    assert run_manifest["redacted_trace_count"] == 1
    assert run_manifest["report_id"] == report["report_id"]
    assert run_manifest["provider_calls"] == 0
    assert evidence_manifest["source"]["sha256"] == _sha256(redacted)
    assert evidence_manifest["accounting"]["accepted_conversation_count"] == 1
    assignments = evidence_manifest["grouping"]["assignments"]
    trace_ids = [trace_id for row in assignments for trace_id in row["trace_ids"]]
    assert trace_ids == ["synthetic-preview-1"]
    assert len(trace_ids) == len(set(trace_ids))
    assert report["accounting"]["accepted_conversation_count"] == 1
    assert report["gaps"]


def test_input_changed_during_custody_is_an_integrity_refusal(
    tmp_path: Path, synthetic_trace: Path
) -> None:
    output = tmp_path / "result"
    original = synthetic_trace.read_bytes()
    alternate = original.replace(
        b"fixture/synthetic-preview-1", b"fixture/synthetic-preview-2"
    )
    assert len(alternate) == len(original)
    stop = threading.Event()

    def swap_regular_files() -> None:
        index = 0
        while not stop.is_set():
            replacement = synthetic_trace.with_suffix(f".swap-{index}.jsonl")
            replacement.write_bytes(alternate if index % 2 else original)
            replacement.replace(synthetic_trace)
            index += 1

    mutator = threading.Thread(target=swap_regular_files, daemon=True)
    mutator.start()
    try:
        completed = run_preview(*analyze_arguments(synthetic_trace, output))
    finally:
        stop.set()
        mutator.join(timeout=5)

    assert completed.returncode == 2
    assert machine_json(completed)["reason_code"] == "INPUT_CHANGED_DURING_RUN"
    assert not (output / "behavior-map.json").exists()


def test_transient_same_length_mutation_restored_during_redaction_refuses(
    tmp_path: Path,
    synthetic_trace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """Restoring bytes cannot erase evidence that the path changed in custody."""

    original = synthetic_trace.read_bytes()
    alternate = original.replace(
        b"fixture/synthetic-preview-1", b"fixture/synthetic-preview-2"
    )
    assert alternate != original
    assert len(alternate) == len(original)
    before = synthetic_trace.stat()
    real_redact = preview_cli.redact_preview_traces
    mutation_facts: dict[str, os.stat_result] = {}

    def mutate_then_restore(source: Path, output: Path, audit: Path) -> object:
        source.write_bytes(alternate)
        try:
            return real_redact(source, output, audit)
        finally:
            source.write_bytes(original)
            mutation_facts["after"] = source.stat()

    monkeypatch.setattr(preview_cli, "redact_preview_traces", mutate_then_restore)
    for key in tuple(os.environ):
        if key.startswith("TRIANA_BEHAVIOR_MAP_"):
            monkeypatch.delenv(key)
    output = tmp_path / "result"

    exit_code = preview_cli.main(analyze_arguments(synthetic_trace, output))

    receipt = json.loads(capfd.readouterr().out.splitlines()[-1])
    after = mutation_facts["after"]
    assert synthetic_trace.read_bytes() == original
    assert (after.st_dev, after.st_ino, after.st_size) == (
        before.st_dev,
        before.st_ino,
        before.st_size,
    )
    assert (after.st_mtime_ns, after.st_ctime_ns) != (
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    assert exit_code == 2
    assert receipt["reason_code"] == "INPUT_CHANGED_DURING_RUN"
    assert not (output / "behavior-map.json").exists()


def test_agent_description_boundary_is_explicit(
    tmp_path: Path, synthetic_trace: Path
) -> None:
    for agent in ("", "x" * 2_001):
        output = tmp_path / f"result-{len(agent)}"
        completed = run_preview(
            *analyze_arguments(synthetic_trace, output, agent=agent)
        )
        assert completed.returncode == 2
        assert machine_json(completed)["reason_code"] == "AGENT_DESCRIPTION_INVALID"
        assert not output.exists()


def test_module_and_installed_command_have_the_same_refusal_contract(
    tmp_path: Path,
) -> None:
    arguments = analyze_arguments(
        tmp_path / "missing.jsonl", tmp_path / "result", authorized=False
    )
    module = run_preview(*arguments)
    installed = run_preview(*arguments, module=False)

    assert installed.returncode == module.returncode == 2
    assert machine_json(installed) == machine_json(module)


def test_preview_is_a_facade_over_the_single_labs_engine() -> None:
    source_root = PREVIEW_ROOT / "src"
    assert source_root.is_dir()
    assert not (source_root / "triana_preview" / "behavior_map").exists()
    python_sources = list(source_root.rglob("*.py"))
    assert python_sources
    combined = "\n".join(path.read_text(encoding="utf-8") for path in python_sources)
    assert "triana_labs.behavior_map" in combined
    assert "def run_behavior_map(" not in combined
    forbidden_copies = (
        "behavior-map-population-v0",
        "behavior-map-pattern-v0",
        "population_dispositions",
        "pattern_occurrence_dispositions",
    )
    assert not any(marker in combined for marker in forbidden_copies)


def test_container_contract_is_private_nonroot_and_data_free() -> None:
    dockerfile = (PREVIEW_ROOT / "Dockerfile").read_text(encoding="utf-8")
    readme = (PREVIEW_ROOT / "README.md").read_text(encoding="utf-8")
    dockerignore = (PREVIEW_ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert "USER root" not in dockerfile
    assert any(line.startswith("USER ") for line in dockerfile.splitlines())
    assert "COPY triana-labs" in dockerfile
    assert "COPY triana-preview" in dockerfile
    assert not any(
        token in dockerfile.upper()
        for token in (
            "API_KEY=",
            "AZURE_OPENAI_API_KEY=",
            "CUSTOMER_AUTHORIZED_TRACE_DATA",
        )
    )
    assert ":ro" in readme
    assert "--confirm-authorized-traces" in readme
    assert ".env" in dockerignore
    assert "*.jsonl" in dockerignore
    assert "tests" not in dockerfile


def test_preview_dockerfile_has_an_isolated_explicit_source_allowlist() -> None:
    dockerignore = PREVIEW_ROOT / "Dockerfile.dockerignore"
    assert dockerignore.is_file()
    rules = [
        line.strip()
        for line in dockerignore.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    # Docker gives this file precedence only for `triana-preview/Dockerfile`.
    # Exclude its root context first, then reopen its exact copied package inputs.
    assert rules[0] == "**"
    assert set(rules[1:]) == {
        "!triana-labs/",
        "!triana-labs/pyproject.toml",
        "!triana-labs/uv.lock",
        "!triana-labs/src/",
        "!triana-labs/src/**",
        "!triana-preview/",
        "!triana-preview/Dockerfile",
        "!triana-preview/pyproject.toml",
        "!triana-preview/uv.lock",
        "!triana-preview/src/",
        "!triana-preview/src/**",
    }
    assert not any(
        rule in rules
        for rule in (
            "!.git/**",
            "!.env",
            "!**/*.jsonl",
            "!**/tests/**",
            "!docs/**",
            "!internal/**",
            "!triana-labs/**",
            "!triana-preview/**",
        )
    )

    root_ignore = REPOSITORY_ROOT / ".dockerignore"
    if root_ignore.is_file():
        root_rules = [
            line.strip()
            for line in root_ignore.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        assert "**" not in root_rules
        assert not any(rule.startswith("!triana-preview/") for rule in root_rules)


def test_output_contains_no_network_telemetry_or_hosted_upload_contract(
    tmp_path: Path, synthetic_trace: Path
) -> None:
    output = tmp_path / "result"
    completed = run_preview(*analyze_arguments(synthetic_trace, output))
    assert completed.returncode == 10, completed.stderr

    run_manifest = json.loads((output / "run-manifest.json").read_bytes())
    assert run_manifest["execution_location"] == "LOCAL_CUSTOMER_DEVICE"
    assert run_manifest["privacy"] == "LOCAL_PRIVATE"
    serialized = json.dumps(run_manifest, sort_keys=True).lower()
    assert "telemetry" not in serialized
    assert "upload_url" not in serialized
    assert "authorization" not in serialized
    assert "api_key" not in serialized
