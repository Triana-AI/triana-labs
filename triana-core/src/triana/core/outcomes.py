"""Stable bootstrap outcomes shared by Triana's public interfaces."""

from typing import Final, TypedDict

NOT_IMPLEMENTED_EXIT_CODE: Final = 70


class NotImplementedOutcome(TypedDict):
    """Safe machine-readable result for an available but unfinished command."""

    code: str
    command: str
    contract_kind: None
    correlation_id: str
    event: str
    json_pointer: str
    message: str
    outcome: str
    reason: str
    schema_version: None
    service: str
    severity: str
    version: str


def not_implemented(command: str, correlation_id: str) -> NotImplementedOutcome:
    """Return the one stable result used before domain behavior exists."""
    return {
        "code": "NOT_IMPLEMENTED",
        "command": command,
        "contract_kind": None,
        "correlation_id": correlation_id,
        "event": "command.finished",
        "json_pointer": "",
        "message": "Command boundary is available, but behavior is not implemented.",
        "outcome": "NOT_IMPLEMENTED",
        "reason": "NOT_IMPLEMENTED",
        "schema_version": None,
        "service": "triana-cli",
        "severity": "ERROR",
        "version": "0.0.0",
    }
