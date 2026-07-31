"""Fatal refusal, privacy, logging, and atomic-output acceptance."""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Any

import pytest
from conftest import minimal_trace, parse_jsonl, write_jsonl


def assert_fatal_refusal(
    result: Any,
    output: Path,
    *,
    exit_code: int,
    reason_code: str,
) -> dict[str, Any]:
    assert result.returncode == exit_code
    assert result.stdout == b""
    assert not output.exists()
    log = result.stderr_json()
    assert log["event_name"] == "triana.traces.observe.rejected"
    assert log["outcome"] == "REJECTED"
    assert log["reason_code"] == reason_code
    assert log["severity"] == "ERROR"
    return log


def test_missing_input_is_refused_without_target(run_cli: Any, tmp_path: Path) -> None:
    output = tmp_path / "output"
    result = run_cli(
        "traces",
        "observe",
        tmp_path / "missing.jsonl",
        "--out",
        output,
    )

    assert_fatal_refusal(result, output, exit_code=2, reason_code="INPUT_READ_FAILED")


def test_unreadable_regular_input_is_refused(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "unreadable.jsonl"
    write_jsonl(corpus, [minimal_trace()])
    corpus.chmod(0)
    output = tmp_path / "output"
    try:
        result = run_cli("traces", "observe", corpus, "--out", output)
    finally:
        corpus.chmod(stat.S_IRUSR | stat.S_IWUSR)

    assert_fatal_refusal(result, output, exit_code=2, reason_code="INPUT_READ_FAILED")


def test_input_symlink_is_refused(run_cli: Any, tmp_path: Path) -> None:
    real_input = tmp_path / "real.jsonl"
    write_jsonl(real_input, [minimal_trace()])
    symlink = tmp_path / "linked.jsonl"
    symlink.symlink_to(real_input)
    output = tmp_path / "output"

    result = run_cli("traces", "observe", symlink, "--out", output)

    assert_fatal_refusal(
        result,
        output,
        exit_code=2,
        reason_code="INPUT_SYMLINK_FORBIDDEN",
    )


@pytest.mark.parametrize("input_name", ["directory", "device"])
def test_non_regular_input_is_refused(
    input_name: str,
    run_cli: Any,
    tmp_path: Path,
) -> None:
    input_path = tmp_path if input_name == "directory" else Path("/dev/null")
    output = tmp_path / f"{input_name}-output"

    result = run_cli("traces", "observe", input_path, "--out", output)

    assert_fatal_refusal(
        result,
        output,
        exit_code=2,
        reason_code="INPUT_NOT_REGULAR_FILE",
    )


def test_input_larger_than_16_mib_is_refused(run_cli: Any, tmp_path: Path) -> None:
    corpus = tmp_path / "too-large.jsonl"
    with corpus.open("wb") as stream:
        stream.truncate(16 * 1024 * 1024 + 1)
    output = tmp_path / "output"

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert_fatal_refusal(result, output, exit_code=3, reason_code="INPUT_TOO_LARGE")


def test_more_than_1000_lines_is_refused(run_cli: Any, tmp_path: Path) -> None:
    corpus = tmp_path / "too-many-lines.jsonl"
    corpus.write_bytes(b"\n" * 1001)
    output = tmp_path / "output"

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert_fatal_refusal(result, output, exit_code=3, reason_code="TOO_MANY_LINES")


def test_missing_output_parent_is_refused(run_cli: Any, tmp_path: Path) -> None:
    corpus = tmp_path / "valid.jsonl"
    write_jsonl(corpus, [minimal_trace()])
    output = tmp_path / "missing-parent" / "output"

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert_fatal_refusal(
        result,
        output,
        exit_code=2,
        reason_code="OUTPUT_PARENT_MISSING",
    )


def test_existing_output_is_never_overwritten_or_merged(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "valid.jsonl"
    write_jsonl(corpus, [minimal_trace()])
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("preserve")

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 2
    assert sentinel.read_text() == "preserve"
    assert {path.name for path in output.iterdir()} == {"keep.txt"}
    assert result.stderr_json()["reason_code"] == "OUTPUT_ALREADY_EXISTS"


def test_unwritable_output_parent_fails_without_partial_artifacts(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "valid.jsonl"
    write_jsonl(corpus, [minimal_trace()])
    parent = tmp_path / "unwritable"
    parent.mkdir()
    parent.chmod(stat.S_IRUSR | stat.S_IXUSR)
    output = parent / "output"
    try:
        result = run_cli("traces", "observe", corpus, "--out", output)
    finally:
        parent.chmod(stat.S_IRWXU)

    assert_fatal_refusal(
        result,
        output,
        exit_code=7,
        reason_code="OUTPUT_WRITE_FAILED",
    )
    assert list(parent.iterdir()) == []


def test_observe_makes_no_network_connection(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "valid.jsonl"
    write_jsonl(corpus, [minimal_trace()])
    output = tmp_path / "output"
    guard_dir = tmp_path / "network-guard"
    guard_dir.mkdir()
    marker = tmp_path / "network-attempted"
    (guard_dir / "sitecustomize.py").write_text(
        "import socket\n"
        "from pathlib import Path\n"
        f"_marker = Path({str(marker)!r})\n"
        "_original_connect = socket.socket.connect\n"
        "def _blocked_connect(self, address):\n"
        "    _marker.write_text(repr(address))\n"
        "    raise AssertionError('network forbidden')\n"
        "socket.socket.connect = _blocked_connect\n"
    )

    result = run_cli(
        "traces",
        "observe",
        corpus,
        "--out",
        output,
        env={"PYTHONPATH": str(guard_dir)},
    )

    assert result.returncode == 0
    assert not marker.exists()


def test_unexpected_read_exception_fails_safely_without_raw_exception(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "valid.jsonl"
    write_jsonl(corpus, [minimal_trace()])
    output = tmp_path / "output"
    guard_dir = tmp_path / "read-fault"
    guard_dir.mkdir()
    secret_exception = "TOP_SECRET_INJECTED_EXCEPTION"
    (guard_dir / "sitecustomize.py").write_text(
        "import os\n"
        "import sys\n"
        f"_target = {str(corpus)!r}\n"
        "def _fault(event, arguments):\n"
        "    if event == 'open' and os.fspath(arguments[0]) == _target:\n"
        f"        raise RuntimeError({secret_exception!r})\n"
        "sys.addaudithook(_fault)\n"
    )

    result = run_cli(
        "traces",
        "observe",
        corpus,
        "--out",
        output,
        env={"PYTHONPATH": str(guard_dir)},
    )

    log = assert_fatal_refusal(
        result,
        output,
        exit_code=70,
        reason_code="INTERNAL_INVARIANT_FAILED",
    )
    assert secret_exception.encode() not in result.stderr
    assert str(corpus) not in json_safe_values(log)


def test_atomic_rename_fault_removes_only_private_temporary_sibling(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "valid.jsonl"
    write_jsonl(corpus, [minimal_trace()])
    parent = tmp_path / "output-parent"
    parent.mkdir()
    output = parent / "output"
    guard_dir = tmp_path / "rename-fault"
    guard_dir.mkdir()
    (guard_dir / "sitecustomize.py").write_text(
        "import os\n"
        "import sys\n"
        f"_target = {str(output)!r}\n"
        "def _fault(event, arguments):\n"
        "    if event == 'os.rename' and os.fspath(arguments[1]) == _target:\n"
        "        raise PermissionError('injected atomic rename failure')\n"
        "sys.addaudithook(_fault)\n"
    )

    result = run_cli(
        "traces",
        "observe",
        corpus,
        "--out",
        output,
        env={"PYTHONPATH": str(guard_dir)},
    )

    assert_fatal_refusal(
        result,
        output,
        exit_code=7,
        reason_code="OUTPUT_WRITE_FAILED",
    )
    assert list(parent.iterdir()) == []


def json_safe_values(value: dict[str, Any]) -> str:
    """Flatten safe terminal-log values for leak assertions."""

    return " ".join(str(item) for item in value.values())


def test_sensitive_values_never_enter_rejections_logs_or_receipt(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    secrets = [
        "TOP_SECRET_CONTENT",
        "trace-secret-987",
        "source-secret-654",
        "private_tool_name",
    ]
    invalid = minimal_trace(
        trace_id=secrets[1],
        source_trace_id=secrets[2],
        events=[
            {
                "sequence": 0,
                "event_kind": "TOOL_RESULT",
                "call_id": "missing",
                "result_state": "SUCCEEDED",
                "result": {"payload": secrets[0], "tool": secrets[3]},
            }
        ],
    )
    corpus = tmp_path / "sensitive-invalid.jsonl"
    write_jsonl(corpus, [invalid])
    output = tmp_path / "output"

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 10
    public_bytes = (
        result.stdout + result.stderr + (output / "rejected_traces.jsonl").read_bytes()
    )
    for secret in secrets:
        assert secret.encode() not in public_bytes
    rejection = parse_jsonl(output / "rejected_traces.jsonl")[0]
    assert set(rejection) == {"line_number", "code", "json_pointer", "safe_message"}
    assert str(corpus).encode() not in public_bytes
    assert str(output).encode() not in result.stderr


def test_local_sensitive_line_is_rejected_and_never_normalized(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    trace = minimal_trace()
    trace["privacy_class"] = "LOCAL_SENSITIVE"
    corpus = tmp_path / "local-sensitive.jsonl"
    write_jsonl(corpus, [trace])
    output = tmp_path / "output"

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 10
    assert (output / "normalized_traces.jsonl").read_bytes() == b""
    assert (
        parse_jsonl(output / "rejected_traces.jsonl")[0]["code"]
        == "UNSUPPORTED_PRIVACY_CLASS"
    )


def test_ambient_locale_timezone_and_environment_do_not_change_artifacts(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "valid.jsonl"
    write_jsonl(corpus, [minimal_trace()])
    environments = [
        {"LANG": "C", "LC_ALL": "C", "TZ": "UTC", "TRIANA_SECRET": "first"},
        {
            "LANG": "en_US.UTF-8",
            "LC_ALL": "en_US.UTF-8",
            "TZ": "Asia/Kolkata",
            "TRIANA_SECRET": "second",
        },
    ]
    outputs = [tmp_path / "environment-one", tmp_path / "environment-two"]

    for environment, output in zip(environments, outputs, strict=True):
        result = run_cli(
            "traces",
            "observe",
            corpus,
            "--out",
            output,
            env=environment,
        )
        assert result.returncode == 0

    assert {path.name: path.read_bytes() for path in outputs[0].iterdir()} == {
        path.name: path.read_bytes() for path in outputs[1].iterdir()
    }


def test_usage_error_is_exit_two_and_creates_nothing(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    result = run_cli("traces", "observe", tmp_path / "anything.jsonl")

    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr_json()["reason_code"] == "CLI_USAGE_ERROR"
    assert list(tmp_path.iterdir()) == []
