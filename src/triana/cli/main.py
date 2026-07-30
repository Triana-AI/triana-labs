"""Public Slice 0A command boundary."""

from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path
from typing import Any, cast

from triana.cli.logging import emit_prepared, emit_terminal, prepare_terminal
from triana.contracts.types import SafeId
from triana.core.canonical import canonical_bytes
from triana.core.errors import EXIT_CODES, TrianaError
from triana.core.parser import MAX_INPUT_BYTES, parse_json
from triana.core.records import require_record, seal_record, verification_receipt
from triana.core.validation import validate_document

COMMANDS = {
    ("contracts", "validate"): "contracts.validate",
    ("records", "seal"): "records.seal",
    ("records", "verify"): "records.verify",
}


def _help() -> None:
    print(
        "usage: triana [-h] {contracts,records} ...\n\n"
        "commands:\n"
        "  triana contracts validate <file-or-->\n"
        "  triana records seal <file-or-->\n"
        "  triana records verify <file-or-->"
    )


def _new_correlation_id() -> str:
    return str(uuid.uuid4())


def _parse_cli(argv: list[str]) -> tuple[str, str, str]:
    correlation_id = _new_correlation_id()
    command_key = cast(tuple[str, str], tuple(argv[:2]))
    if len(argv) >= 2 and command_key in COMMANDS:
        command = COMMANDS[command_key]
    else:
        raise TrianaError("CLI_USAGE_ERROR", "Unknown or missing command.")
    remainder = argv[2:]
    if "--correlation-id" in remainder:
        if remainder.count("--correlation-id") != 1:
            raise TrianaError("CLI_USAGE_ERROR", "Invalid command options.")
        position = remainder.index("--correlation-id")
        if position + 1 >= len(remainder):
            raise TrianaError("CLI_USAGE_ERROR", "Missing correlation identifier.")
        candidate = remainder[position + 1]
        remainder = remainder[:position] + remainder[position + 2 :]
        try:
            from pydantic import TypeAdapter

            correlation_id = TypeAdapter(SafeId).validate_python(candidate, strict=True)
        except Exception as error:
            raise TrianaError(
                "CLI_USAGE_ERROR",
                "Invalid correlation identifier.",
                context_correlation_id=_new_correlation_id(),
            ) from error
    if len(remainder) != 1 or remainder[0].startswith("--"):
        raise TrianaError(
            "CLI_USAGE_ERROR",
            "Exactly one input is required.",
            context_correlation_id=correlation_id,
        )
    return command, remainder[0], correlation_id


def _read_input(source: str) -> bytes:
    if source == "-":
        return sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        with Path(source).open("rb") as stream:
            return stream.read(MAX_INPUT_BYTES + 1)
    except OSError as error:
        raise TrianaError("INPUT_READ_FAILED", "Input could not be read.") from error


def _event_name(command: str, success: bool) -> str:
    return f"triana.{command}.{'succeeded' if success else 'rejected'}"


def _write_artifact(value: Any) -> None:
    try:
        sys.stdout.buffer.write(canonical_bytes(value) + b"\n")
        sys.stdout.buffer.flush()
    except (BrokenPipeError, OSError) as error:
        raise TrianaError(
            "OUTPUT_WRITE_FAILED", "Output could not be written."
        ) from error


def main(argv: list[str] | None = None) -> int:
    """Validate, seal, or verify one local JSON document."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--help"] or arguments == ["-h"]:
        _help()
        return 0

    start = time.monotonic_ns()
    correlation_id = _new_correlation_id()
    command = "cli"
    try:
        command, source, correlation_id = _parse_cli(arguments)
        document = validate_document(parse_json(_read_input(source)))
        record_hash: str | None = None
        if command == "contracts.validate":
            artifact = document
        elif command == "records.seal":
            require_record(document)
            artifact = seal_record(document)
            record_hash = artifact["current_record_hash"]
        else:
            require_record(document)
            artifact = verification_receipt(document)
            record_hash = artifact["record_hash"]
        duration_ms = (time.monotonic_ns() - start) // 1_000_000
        prepared = prepare_terminal(
            event_name=_event_name(command, True),
            command=command,
            outcome="SUCCEEDED",
            correlation_id=correlation_id,
            duration_ms=duration_ms,
            record_hash=record_hash,
        )
        if not prepared.serialization_succeeded:
            emit_prepared(prepared)
            return EXIT_CODES["LOG_REDACTION_FAILED"]
        _write_artifact(artifact)
        logged = emit_prepared(prepared)
        return 0 if logged else EXIT_CODES["LOG_REDACTION_FAILED"]
    except TrianaError as error:
        correlation_id = error.context_correlation_id or correlation_id
        event_name = (
            "triana.cli.rejected"
            if command == "cli" or error.code == "CLI_USAGE_ERROR"
            else _event_name(command, False)
        )
        duration_ms = (time.monotonic_ns() - start) // 1_000_000
        logged = emit_terminal(
            event_name=event_name,
            command="cli" if event_name == "triana.cli.rejected" else command,
            outcome="REJECTED",
            correlation_id=correlation_id,
            duration_ms=duration_ms,
            error=error,
        )
        return error.exit_code if logged else EXIT_CODES["LOG_REDACTION_FAILED"]
    except Exception:  # noqa: BLE001 - public boundary must never leak an exception
        internal_error = TrianaError(
            "INTERNAL_INVARIANT_FAILED",
            "An internal invariant failed safely.",
        )
        duration_ms = (time.monotonic_ns() - start) // 1_000_000
        logged = emit_terminal(
            event_name=_event_name(command, False),
            command=command,
            outcome="REJECTED",
            correlation_id=correlation_id,
            duration_ms=duration_ms,
            error=internal_error,
        )
        return (
            internal_error.exit_code if logged else EXIT_CODES["LOG_REDACTION_FAILED"]
        )
