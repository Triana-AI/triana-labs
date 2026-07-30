"""Typed public failures for deterministic contract operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

EXIT_CODES = {
    "CLI_USAGE_ERROR": 2,
    "INPUT_READ_FAILED": 2,
    "INPUT_TOO_LARGE": 3,
    "NESTING_TOO_DEEP": 3,
    "STRING_TOO_LARGE": 3,
    "COLLECTION_TOO_LARGE": 3,
    "INVALID_UTF8": 3,
    "BOM_FORBIDDEN": 3,
    "MALFORMED_JSON": 3,
    "DUPLICATE_JSON_KEY": 3,
    "UNKNOWN_CONTRACT_KIND": 4,
    "UNSUPPORTED_SCHEMA_VERSION": 4,
    "SCHEMA_VALIDATION_FAILED": 4,
    "VALIDATION_ERROR_LIMIT_REACHED": 4,
    "IMPOSSIBLE_STATE": 5,
    "IDENTITY_MISMATCH": 5,
    "HASH_FORMAT_INVALID": 6,
    "HASH_MISMATCH": 6,
    "OUTPUT_WRITE_FAILED": 7,
    "LOG_REDACTION_FAILED": 70,
    "INTERNAL_INVARIANT_FAILED": 70,
}


@dataclass(slots=True)
class TrianaError(Exception):
    """One safe, typed rejection."""

    code: str
    safe_message: str
    json_pointer: str | None = None
    contract_kind: str | None = None
    received_schema_version: int | None = None
    errors: list[dict[str, str]] = field(default_factory=list)
    context_correlation_id: str | None = None

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.code]

    def public_fields(self) -> dict[str, Any]:
        fields: dict[str, Any] = {
            "code": self.code,
            "safe_message": self.safe_message,
        }
        if self.json_pointer is not None:
            fields["json_pointer"] = self.json_pointer
        if self.contract_kind is not None:
            fields["contract_kind"] = self.contract_kind
        if self.received_schema_version is not None:
            fields["received_schema_version"] = self.received_schema_version
        if self.errors:
            fields["errors"] = self.errors
        return fields
