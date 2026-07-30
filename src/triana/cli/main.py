"""Public Slice 0A command boundary."""

import argparse
import json
import sys
from collections.abc import Sequence

from triana.core.outcomes import NOT_IMPLEMENTED_EXIT_CODE, not_implemented


def _add_operation_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("file", help="UTF-8 JSON input file")
    parser.add_argument(
        "--correlation-id",
        default="not-provided",
        help="caller-provided safe correlation identifier",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="triana")
    groups = parser.add_subparsers(dest="group", required=True)

    contracts = groups.add_parser("contracts")
    contract_commands = contracts.add_subparsers(dest="operation", required=True)
    _add_operation_arguments(contract_commands.add_parser("validate"))

    records = groups.add_parser("records")
    record_commands = records.add_subparsers(dest="operation", required=True)
    _add_operation_arguments(record_commands.add_parser("seal"))
    _add_operation_arguments(record_commands.add_parser("verify"))

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run an available command boundary without implementing domain behavior."""
    arguments = _parser().parse_args(argv)
    command = f"{arguments.group}.{arguments.operation}"
    outcome = not_implemented(command, arguments.correlation_id)
    print(
        json.dumps(outcome, ensure_ascii=True, separators=(",", ":"), sort_keys=True),
        file=sys.stderr,
    )
    return NOT_IMPLEMENTED_EXIT_CODE
