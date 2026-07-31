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
from triana_labs.intelligence import DeriveFailure, derive
from triana_labs.observer import ObserveFailure, observe

_SERVICE = "triana-labs-cli"
_usage_command = "traces.observe"


class _SafeArgumentParser(argparse.ArgumentParser):
    """Replace value-echoing argparse failures with one safe terminal event."""

    def error(self, message: str) -> Never:
        """Emit the closed usage refusal without reproducing user arguments."""

        # argparse's default error echoes user arguments and usage text. Discarding the
        # message preserves the one-event log contract and prevents paths or values
        # from leaking before command execution begins.
        del message
        if _usage_command == "corpus.derive":
            event = _corpus_terminal_log(
                event_name="triana.corpus.derive.rejected",
                severity="ERROR",
                outcome="REJECTED",
                reason_code="CLI_USAGE_ERROR",
                duration_ms=0,
            )
        else:
            event = _terminal_log(
                event_name="triana.traces.observe.rejected",
                severity="ERROR",
                outcome="REJECTED",
                reason_code="CLI_USAGE_ERROR",
                duration_ms=0,
            )
        _write_json(sys.stderr, event)
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
    corpus = commands.add_parser("corpus", help="Derive intelligence from a corpus.")
    corpus_commands = corpus.add_subparsers(dest="corpus_command")
    derive_parser = corpus_commands.add_parser(
        "derive", help="Derive structural intelligence from an Observer bundle."
    )
    derive_parser.add_argument("manifest", help="Observer manifest.json path.")
    derive_parser.add_argument(
        "--out", required=True, help="New directory for intelligence artifacts."
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

    global _usage_command
    raw_arguments = list(sys.argv[1:] if argv is None else argv)
    _usage_command = (
        "corpus.derive"
        if raw_arguments[:2] == ["corpus", "derive"]
        else "traces.observe"
    )
    parser = _build_parser()
    arguments = parser.parse_args(raw_arguments)

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

    if arguments.command == "corpus" and arguments.corpus_command == "derive":
        start = time.monotonic_ns()
        try:
            derive_result = derive(Path(arguments.manifest), Path(arguments.out))
        except DeriveFailure as failure:
            _write_json(
                sys.stderr,
                _corpus_terminal_log(
                    event_name="triana.corpus.derive.rejected",
                    severity="ERROR",
                    outcome="REJECTED",
                    reason_code=failure.reason_code,
                    duration_ms=_duration_ms(start),
                ),
            )
            return failure.exit_code
        except Exception:  # noqa: BLE001 - redact unexpected failures at the CLI.
            _write_json(
                sys.stderr,
                _corpus_terminal_log(
                    event_name="triana.corpus.derive.rejected",
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
                "cluster_count": derive_result.cluster_count,
                "gap_count": derive_result.gap_count,
                "manifest_path": f"{arguments.out}/manifest.json",
                "outcome": derive_result.outcome,
                "trace_count": derive_result.trace_count,
            },
        )
        _write_json(
            sys.stderr,
            _corpus_terminal_log(
                event_name="triana.corpus.derive.completed_with_gaps",
                severity="INFO",
                outcome=derive_result.outcome,
                reason_code=None,
                duration_ms=_duration_ms(start),
                cluster_count=derive_result.cluster_count,
                gap_count=derive_result.gap_count,
                trace_count=derive_result.trace_count,
            ),
        )
        return 10

    parser.print_help()
    return 0


def _duration_ms(start_ns: int) -> int:
    """Return nonnegative operational duration excluded from portable artifacts."""

    # Duration is operational log metadata only. Monotonic time cannot affect any
    # portable artifact, count, rejection, or future Corpus Intelligence input.
    return max(0, (time.monotonic_ns() - start_ns) // 1_000_000)


def _corpus_terminal_log(
    *,
    event_name: str,
    severity: str,
    outcome: str,
    reason_code: str | None,
    duration_ms: int,
    cluster_count: int | None = None,
    gap_count: int | None = None,
    trace_count: int | None = None,
) -> dict[str, Any]:
    """Construct the closed, content-free Corpus Intelligence log shape."""

    event: dict[str, Any] = {
        "command": "corpus.derive",
        "duration_ms": duration_ms,
        "event_name": event_name,
        "outcome": outcome,
        "reason_code": reason_code,
        "service": _SERVICE,
        "service_version": __version__,
        "severity": severity,
    }
    if cluster_count is not None:
        event.update(
            {
                "cluster_count": cluster_count,
                "gap_count": gap_count,
                "trace_count": trace_count,
            }
        )
    return event
