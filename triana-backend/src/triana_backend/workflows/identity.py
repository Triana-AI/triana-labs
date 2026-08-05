"""Deterministic workflow identity derivation."""

from __future__ import annotations

import hashlib
import json

from .contracts import ImportRunRequest


def workflow_id_for(request: ImportRunRequest) -> str:
    payload = request.as_history_payload()
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return f"labs08-run-{digest}"
