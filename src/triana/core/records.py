"""Release Evidence Record sealing and receipt verification."""

from __future__ import annotations

import copy
from typing import Any

from triana.core.canonical import domain_hash, without_field
from triana.core.errors import TrianaError


def require_record(value: dict[str, Any]) -> None:
    if value["contract_kind"] != "release_evidence_record":
        raise TrianaError(
            "SCHEMA_VALIDATION_FAILED",
            "This operation requires a Release Evidence Record.",
            "/contract_kind",
            value["contract_kind"],
            value["schema_version"],
        )


def seal_record(value: dict[str, Any]) -> dict[str, Any]:
    require_record(value)
    if value["seal_state"] != "UNSIGNED":
        raise TrianaError(
            "IMPOSSIBLE_STATE",
            "A sealed record cannot be sealed again.",
            "/seal_state",
            "release_evidence_record",
            value["schema_version"],
        )
    sealed = copy.deepcopy(value)
    sealed["seal_state"] = "SEALED"
    sealed["current_record_hash"] = domain_hash(
        "release_evidence_record", without_field(sealed, "current_record_hash")
    )
    return sealed


def verification_receipt(value: dict[str, Any]) -> dict[str, Any]:
    require_record(value)
    if value["seal_state"] != "SEALED":
        raise TrianaError(
            "IMPOSSIBLE_STATE",
            "An unsigned record cannot be verified.",
            "/seal_state",
            "release_evidence_record",
            value["schema_version"],
        )
    return {"record_hash": value["current_record_hash"], "verified": True}
