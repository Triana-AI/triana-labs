"""Expose the local Trace Observer as a safe process boundary.

The CLI owns argument handling, presentation receipts, terminal logs, and exit codes.
The Observer owns corpus behavior, while ``contracts.traces`` owns individual trace
validation. External adapters produce JSONL and do not call this module.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Never

from triana_labs import __version__
from triana_labs.observer import ObserveFailure, observe

_SERVICE = "triana-labs-cli"


class _SafeArgumentParser(argparse.ArgumentParser):
    """Replace value-echoing argparse failures with one safe terminal event."""

    def error(self, message: str) -> Never:
        """Emit the closed usage refusal without reproducing user arguments."""

        # argparse's default error echoes user arguments and usage text. Discarding the
        # message preserves the one-event log contract and prevents paths or values
        # from leaking before command execution begins.
        del message
        _write_json(
            sys.stderr,
            _terminal_log(
                event_name="triana.traces.observe.rejected",
                severity="ERROR",
                outcome="REJECTED",
                reason_code="CLI_USAGE_ERROR",
                duration_ms=0,
            ),
        )
        raise SystemExit(2)


def _build_parser() -> _SafeArgumentParser:
    """Build the small command tree without executing corpus behavior."""

    parser = _SafeArgumentParser(
        prog="triana",
        description="Inspect conversational-agent behavior with local evidence.",
    )
    commands = parser.add_subparsers(dest="command")

    traces = commands.add_parser("traces", help="Work with trace corpora.")
    trace_commands = traces.add_subparsers(dest="trace_command")
    observe = trace_commands.add_parser(
        "observe",
        help="Validate and profile a local trace corpus.",
    )
    observe.add_argument("input", help="Path to a local JSONL trace corpus.")
    observe.add_argument(
        "--out",
        required=True,
        help="New directory for generated corpus artifacts.",
    )
    return parser


def _write_json(stream: Any, value: dict[str, Any]) -> None:
    """Write one compact presentation JSON value and terminal LF."""

    # Receipts and logs are presentation channels, not portable artifact identities.
    # They still use a deterministic compact shape so automation has one clear form.
    stream.write(
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    )


def _terminal_log(
    *,
    event_name: str,
    severity: str,
    outcome: str,
    reason_code: str | None,
    duration_ms: int,
    input_count: int | None = None,
    accepted_count: int | None = None,
    rejected_count: int | None = None,
    eligible_count: int | None = None,
) -> dict[str, Any]:
    """Construct a log event through the closed safe-field seam."""

    # This constructor is the logging allowlist. Success includes corpus counts;
    # refusal omits them when no complete accounting exists. Paths, trace values,
    # tool names, exceptions, and artifact hashes have no parameter through this seam.
    event: dict[str, Any] = {
        "command": "traces.observe",
        "duration_ms": duration_ms,
        "event_name": event_name,
        "outcome": outcome,
        "reason_code": reason_code,
        "service": _SERVICE,
        "service_version": __version__,
        "severity": severity,
    }
    if input_count is not None:
        event.update(
            {
                "input_count": input_count,
                "accepted_count": accepted_count,
                "rejected_count": rejected_count,
                "case_generation_eligible_count": eligible_count,
            }
        )
    return event


def main(argv: Sequence[str] | None = None) -> int:
    """Invoke the Observer once and translate its typed result to CLI channels."""

    parser = _build_parser()
    arguments = parser.parse_args(argv)

    if arguments.command == "traces" and arguments.trace_command == "observe":
        start = time.monotonic_ns()
        try:
            result = observe(Path(arguments.input), Path(arguments.out))
        except ObserveFailure as failure:
            # Typed Observer refusals preserve their contract-owned reason and exit.
            _write_json(
                sys.stderr,
                _terminal_log(
                    event_name="triana.traces.observe.rejected",
                    severity="ERROR",
                    outcome="REJECTED",
                    reason_code=failure.reason_code,
                    duration_ms=_duration_ms(start),
                ),
            )
            return failure.exit_code
        except Exception:  # noqa: BLE001 - the CLI must redact unexpected failures.
            # The outermost boundary deliberately catches unexpected implementation
            # faults, emits no exception text, and refuses to mislabel them as evidence.
            _write_json(
                sys.stderr,
                _terminal_log(
                    event_name="triana.traces.observe.rejected",
                    severity="ERROR",
                    outcome="REJECTED",
                    reason_code="INTERNAL_INVARIANT_FAILED",
                    duration_ms=_duration_ms(start),
                ),
            )
            return 70

        _write_json(
            sys.stdout,
            {
                "accepted_count": result.accepted_count,
                "case_generation_eligible_count": (
                    result.case_generation_eligible_count
                ),
                "manifest_path": f"{arguments.out}/manifest.json",
                "outcome": result.outcome,
                "rejected_count": result.rejected_count,
            },
        )
        event_name = (
            "triana.traces.observe.succeeded"
            if result.outcome == "COMPLETED"
            else "triana.traces.observe.completed_with_rejections"
        )
        _write_json(
            sys.stderr,
            _terminal_log(
                event_name=event_name,
                severity="INFO",
                outcome=result.outcome,
                reason_code=None,
                duration_ms=_duration_ms(start),
                input_count=result.input_count,
                accepted_count=result.accepted_count,
                rejected_count=result.rejected_count,
                eligible_count=result.case_generation_eligible_count,
            ),
        )
        return 0 if result.outcome == "COMPLETED" else 10

    parser.print_help()
    return 0


def _duration_ms(start_ns: int) -> int:
    """Return nonnegative operational duration excluded from portable artifacts."""

    # Duration is operational log metadata only. Monotonic time cannot affect any
    # portable artifact, count, rejection, or future Corpus Intelligence input.
    return max(0, (time.monotonic_ns() - start_ns) // 1_000_000)
