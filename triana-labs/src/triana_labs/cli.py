"""Triana Labs command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from triana_labs import __version__

_NOT_IMPLEMENTED_EXIT = 70


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
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


def _write_not_implemented() -> None:
    event = {
        "command": "traces.observe",
        "event_name": "triana.traces.observe.rejected",
        "outcome": "NOT_IMPLEMENTED",
        "reason_code": "NOT_IMPLEMENTED",
        "service": "triana-labs-cli",
        "service_version": __version__,
        "severity": "ERROR",
    }
    sys.stderr.write(
        json.dumps(event, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return its process exit status."""

    parser = _build_parser()
    arguments = parser.parse_args(argv)

    if arguments.command == "traces" and arguments.trace_command == "observe":
        _write_not_implemented()
        return _NOT_IMPLEMENTED_EXIT

    parser.print_help()
    return 0
