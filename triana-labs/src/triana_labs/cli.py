"""Triana Labs command-line interface."""

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
    def error(self, message: str) -> Never:
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
    """Run the CLI and return its process exit status."""

    parser = _build_parser()
    arguments = parser.parse_args(argv)

    if arguments.command == "traces" and arguments.trace_command == "observe":
        start = time.monotonic_ns()
        try:
            result = observe(Path(arguments.input), Path(arguments.out))
        except ObserveFailure as failure:
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
    return max(0, (time.monotonic_ns() - start_ns) // 1_000_000)
