"""Local custody facade over the single Triana Labs Behavior Map engine."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from triana_labs.behavior_map import RedactionFailure, redact_preview_traces

JsonObject = dict[str, Any]

_PROVIDER = "TRIANA_BEHAVIOR_MAP_PROVIDER"
_PROVIDER_FIELDS = (
    "TRIANA_BEHAVIOR_MAP_PRIMARY_ENDPOINT",
    "TRIANA_BEHAVIOR_MAP_AUDIT_ENDPOINT",
    "TRIANA_BEHAVIOR_MAP_PRIMARY_MODEL_ID",
    "TRIANA_BEHAVIOR_MAP_AUDIT_MODEL_ID",
    "TRIANA_BEHAVIOR_MAP_PRIMARY_API_KEY",
    "TRIANA_BEHAVIOR_MAP_AUDIT_API_KEY",
    "TRIANA_BEHAVIOR_MAP_PRIMARY_DEPLOYMENT_VERSION",
    "TRIANA_BEHAVIOR_MAP_AUDIT_DEPLOYMENT_VERSION",
    "TRIANA_BEHAVIOR_MAP_PRIMARY_SKU",
    "TRIANA_BEHAVIOR_MAP_AUDIT_SKU",
    "TRIANA_BEHAVIOR_MAP_PRIMARY_CAPACITY",
    "TRIANA_BEHAVIOR_MAP_AUDIT_CAPACITY",
    "TRIANA_BEHAVIOR_MAP_PRIMARY_CREDENTIAL_BOUNDARY_ID",
    "TRIANA_BEHAVIOR_MAP_AUDIT_CREDENTIAL_BOUNDARY_ID",
)


class PreviewRefusal(Exception):
    """A content-free refusal at the local custody boundary."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


def _canonical(value: JsonObject) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _write_json(path: Path, value: JsonObject) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_canonical(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        path.chmod(0o600)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _receipt(*, outcome: str, reason_code: str | None = None, **facts: Any) -> None:
    value: JsonObject = {"command": "triana-preview.analyze", "outcome": outcome}
    if reason_code is not None:
        value["reason_code"] = reason_code
    value.update(facts)
    sys.stdout.buffer.write(_canonical(value))
    sys.stdout.flush()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="triana-preview")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser(
        "analyze", help="Analyze an authorized local PreviewTrace JSONL source."
    )
    analyze.add_argument("--traces", required=True)
    analyze.add_argument("--agent", required=True)
    analyze.add_argument("--output", required=True)
    analyze.add_argument("--confirm-authorized-traces", action="store_true")
    return parser


def _provider_binding() -> JsonObject:
    provider = os.environ.get(_PROVIDER)
    present_fields = {
        key: os.environ.get(key) for key in _PROVIDER_FIELDS if os.environ.get(key)
    }
    if provider is None and not present_fields:
        return {
            "authorized": False,
            "model_id": None,
            "audit_model_id": None,
        }
    if provider is None or len(present_fields) != len(_PROVIDER_FIELDS):
        raise PreviewRefusal("PROVIDER_CONFIG_INCOMPLETE")
    if provider != "MICROSOFT_FOUNDRY_OPENAI_V1":
        raise PreviewRefusal("PROVIDER_CONFIG_INCOMPLETE")
    configured = {key: os.environ[key] for key in _PROVIDER_FIELDS}

    primary_endpoint = configured["TRIANA_BEHAVIOR_MAP_PRIMARY_ENDPOINT"].rstrip("/")
    audit_endpoint = configured["TRIANA_BEHAVIOR_MAP_AUDIT_ENDPOINT"].rstrip("/")
    primary_url = urlsplit(primary_endpoint)
    audit_url = urlsplit(audit_endpoint)
    if (
        primary_url.scheme != "https"
        or not primary_url.hostname
        or primary_url.username is not None
        or primary_url.password is not None
        or primary_url.query
        or primary_url.fragment
        or audit_url.scheme != "https"
        or not audit_url.hostname
        or audit_url.username is not None
        or audit_url.password is not None
        or audit_url.query
        or audit_url.fragment
        or primary_endpoint == audit_endpoint
        or configured["TRIANA_BEHAVIOR_MAP_PRIMARY_MODEL_ID"]
        == configured["TRIANA_BEHAVIOR_MAP_AUDIT_MODEL_ID"]
        or not configured["TRIANA_BEHAVIOR_MAP_PRIMARY_CAPACITY"].isdigit()
        or not configured["TRIANA_BEHAVIOR_MAP_AUDIT_CAPACITY"].isdigit()
    ):
        raise PreviewRefusal("PROVIDER_CONFIG_INCOMPLETE")
    return {
        "authorized": True,
        "model_id": configured["TRIANA_BEHAVIOR_MAP_PRIMARY_MODEL_ID"],
        "audit_model_id": configured["TRIANA_BEHAVIOR_MAP_AUDIT_MODEL_ID"],
        "provider": provider,
        "audit_provider": provider,
        "endpoint_origin": primary_endpoint,
        "audit_endpoint_origin": audit_endpoint,
        "deployment_version": configured[
            "TRIANA_BEHAVIOR_MAP_PRIMARY_DEPLOYMENT_VERSION"
        ],
        "audit_deployment_version": configured[
            "TRIANA_BEHAVIOR_MAP_AUDIT_DEPLOYMENT_VERSION"
        ],
        "sku": configured["TRIANA_BEHAVIOR_MAP_PRIMARY_SKU"],
        "audit_sku": configured["TRIANA_BEHAVIOR_MAP_AUDIT_SKU"],
        "capacity": int(configured["TRIANA_BEHAVIOR_MAP_PRIMARY_CAPACITY"]),
        "audit_capacity": int(configured["TRIANA_BEHAVIOR_MAP_AUDIT_CAPACITY"]),
        "credential_boundary_id": configured[
            "TRIANA_BEHAVIOR_MAP_PRIMARY_CREDENTIAL_BOUNDARY_ID"
        ],
        "audit_credential_boundary_id": configured[
            "TRIANA_BEHAVIOR_MAP_AUDIT_CREDENTIAL_BOUNDARY_ID"
        ],
    }


def _prepare_output(path: Path) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise PreviewRefusal("OUTPUT_NOT_EMPTY")
        try:
            if any(path.iterdir()):
                raise PreviewRefusal("OUTPUT_NOT_EMPTY")
        except OSError as error:
            raise PreviewRefusal("OUTPUT_NOT_EMPTY") from error
    else:
        try:
            path.mkdir(parents=True, mode=0o700)
        except OSError as error:
            raise PreviewRefusal("OUTPUT_UNAVAILABLE") from error
    path.chmod(0o700)


def _open_regular_source(path: Path) -> tuple[int, os.stat_result, str]:
    try:
        before = path.lstat()
    except OSError as error:
        raise PreviewRefusal("PREVIEW_TRACE_INPUT_INVALID") from error
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise PreviewRefusal("PREVIEW_TRACE_INPUT_UNSAFE")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise OSError("source is not regular")
        with os.fdopen(os.dup(descriptor), "rb") as stream:
            digest = _sha256(stream.read())
    except OSError as error:
        if "descriptor" in locals():
            os.close(descriptor)
        raise PreviewRefusal("PREVIEW_TRACE_INPUT_UNSAFE") from error
    if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
        os.close(descriptor)
        raise PreviewRefusal("INPUT_CHANGED_DURING_RUN")
    return descriptor, opened, digest


def _source_unchanged(
    path: Path, descriptor: int, opened: os.stat_result, digest: str
) -> bool:
    try:
        current = path.lstat()
        if stat.S_ISLNK(current.st_mode) or not stat.S_ISREG(current.st_mode):
            return False
        if (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino):
            return False
        if (current.st_mtime_ns, current.st_ctime_ns) != (
            opened.st_mtime_ns,
            opened.st_ctime_ns,
        ):
            return False
        with path.open("rb") as stream:
            current_digest = _sha256(stream.read())
        descriptor_now = os.fstat(descriptor)
        return current_digest == digest and (
            descriptor_now.st_size,
            descriptor_now.st_mtime_ns,
            descriptor_now.st_ctime_ns,
        ) == (
            opened.st_size,
            opened.st_mtime_ns,
            opened.st_ctime_ns,
        )
    except OSError:
        return False


def _redacted_trace_ids(payload: bytes) -> list[str]:
    trace_ids: list[str] = []
    try:
        for line in payload.splitlines():
            value = json.loads(line)
            trace_id = value["trace_id"]
            if not isinstance(trace_id, str) or not trace_id or trace_id in trace_ids:
                raise ValueError
            trace_ids.append(trace_id)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise PreviewRefusal("PREVIEW_TRACE_INPUT_INVALID") from error
    if not trace_ids:
        raise PreviewRefusal("PREVIEW_TRACE_INPUT_INVALID")
    return trace_ids


def _provider_calls(report: JsonObject) -> int:
    lineage = report.get("provider_lineage")
    if not isinstance(lineage, dict):
        return 0
    total = 0
    for role in ("primary", "auditor"):
        item = lineage.get(role)
        if not isinstance(item, dict):
            continue
        value = item.get("attempted_call_count", item.get("provider_calls", 0))
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            total += value
    return total


def _chmod_custody(output: Path) -> None:
    output.chmod(0o700)
    for path in output.rglob("*"):
        if path.is_dir():
            path.chmod(0o700)
        elif path.is_file():
            path.chmod(0o600)


def _analyze(arguments: argparse.Namespace) -> int:
    if not arguments.confirm_authorized_traces:
        raise PreviewRefusal("TRACE_AUTHORIZATION_REQUIRED")
    agent = arguments.agent
    if not isinstance(agent, str) or not agent or len(agent.encode("utf-8")) > 2_000:
        raise PreviewRefusal("AGENT_DESCRIPTION_INVALID")
    provider_egress = _provider_binding()
    source = Path(arguments.traces)
    output = Path(arguments.output)
    descriptor, opened, source_digest = _open_regular_source(source)
    try:
        _prepare_output(output)
        redacted_path = output / "input.redacted.jsonl"
        audit_path = output / "redaction-audit.json"
        try:
            redact_preview_traces(source, redacted_path, audit_path)
        except RedactionFailure as error:
            reason = {
                "REDACTION_INPUT_INVALID": "PREVIEW_TRACE_INPUT_INVALID",
                "REDACTION_RESIDUAL_IDENTIFIER": (
                    "PREVIEW_TRACE_REDACTION_RESIDUAL_IDENTIFIER"
                ),
            }.get(error.reason_code, "PREVIEW_TRACE_REDACTION_REFUSED")
            raise PreviewRefusal(reason) from error
        if not _source_unchanged(source, descriptor, opened, source_digest):
            redacted_path.unlink(missing_ok=True)
            audit_path.unlink(missing_ok=True)
            raise PreviewRefusal("INPUT_CHANGED_DURING_RUN")
    finally:
        os.close(descriptor)

    redacted = redacted_path.read_bytes()
    trace_ids = _redacted_trace_ids(redacted)
    redacted_hash = _sha256(redacted)
    agent_id = _sha256(agent.encode("utf-8"))
    manifest: JsonObject = {
        "artifact_kind": "evidence_bundle_manifest_v0",
        "schema_version": 0,
        "source": {
            "adapter_id": "preview-trace-jsonl",
            "adapter_version": "1",
            "path": redacted_path.name,
            "sha256": redacted_hash,
            "physical_record_count": len(trace_ids),
        },
        "agent": {"workspace_id": "local-preview", "agent_id": agent_id},
        "privacy": {
            "authorization": "CUSTOMER_AUTHORIZED_TRACE_DATA",
            "execution_location": "LOCAL_PRIVATE",
            "redaction": {
                "state": "APPLIED",
                "audit_sha256": _sha256(audit_path.read_bytes()),
            },
            "provider_egress": provider_egress,
        },
        "accounting": {"accepted_conversation_count": len(trace_ids)},
        "grouping": {
            "highest_dependency_key": "conversation",
            "assignments": [
                {"group_id": f"conversation-{trace_id}", "trace_ids": [trace_id]}
                for trace_id in trace_ids
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
    manifest_path = output / "manifest.json"
    _write_json(manifest_path, manifest)

    command = [
        sys.executable,
        "-m",
        "triana_labs",
        "behavior-map",
        "run",
        "--manifest",
        os.fspath(manifest_path),
        "--output-dir",
        os.fspath(output),
        "--agent-context",
        agent,
    ]
    child = subprocess.run(command, check=False, capture_output=True, text=True)
    report_path = output / "behavior-map.json"
    if child.returncode not in {0, 10} or not report_path.is_file():
        raise PreviewRefusal("PREVIEW_ENGINE_REJECTED")
    try:
        report = json.loads(report_path.read_bytes())
        report_id = report["report_id"]
        if not isinstance(report_id, str):
            raise TypeError
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise PreviewRefusal("PREVIEW_ENGINE_ARTIFACT_INVALID") from error
    calls = _provider_calls(report)
    run_manifest: JsonObject = {
        "artifact_kind": "triana_preview_run_manifest_v0",
        "schema_version": 0,
        "execution_location": "LOCAL_CUSTOMER_DEVICE",
        "privacy": "LOCAL_PRIVATE",
        "redacted_source_sha256": redacted_hash,
        "redacted_trace_count": len(trace_ids),
        "redaction_audit_sha256": _sha256(audit_path.read_bytes()),
        "evidence_manifest_sha256": _sha256(manifest_path.read_bytes()),
        "report_id": report_id,
        "provider_calls": calls,
    }
    _write_json(output / "run-manifest.json", run_manifest)
    _chmod_custody(output)
    outcome = "COMPLETED_WITH_GAPS" if report.get("gaps") else "COMPLETED"
    _receipt(outcome=outcome, report_id=report_id, provider_calls=calls)
    return child.returncode


def main(arguments: list[str] | None = None) -> int:
    """Run the private local Preview command."""

    parsed = _parser().parse_args(arguments)
    try:
        if parsed.command == "analyze":
            return _analyze(parsed)
    except PreviewRefusal as error:
        _receipt(outcome="REJECTED", reason_code=error.reason_code)
        return 2
    _receipt(outcome="REJECTED", reason_code="COMMAND_INVALID")
    return 2


__all__ = ["main"]
