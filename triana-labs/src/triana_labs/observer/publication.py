"""Render, hash, and atomically publish the five LABS-01 corpus artifacts.

This module receives fully accounted values from the Observer and a completed profile
from ``observer.profile``. It owns exact artifact bytes, manifest construction, and
filesystem publication; it performs no trace validation or corpus aggregation.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from triana_labs.observer.renderer import compact_json, render_markdown

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class PublicationFailure(Exception):
    """Carry a safe publication refusal for translation by the Observer."""

    reason_code: str
    exit_code: int


def publish_bundle(
    output_path: Path,
    accepted: list[JsonObject],
    rejected: list[JsonObject],
    profile: JsonObject,
) -> None:
    """Render authoritative bytes, construct their manifest, and publish once."""

    # Machine artifacts are authoritative. Markdown is rendered from the completed
    # profile, and the manifest hashes the exact four non-manifest byte streams. The
    # renderer performs no independent counting and the manifest has no circular hash.
    normalized_bytes = b"".join(compact_json(trace) for trace in accepted)
    rejected_bytes = b"".join(compact_json(record) for record in rejected)
    profile_bytes = compact_json(profile)
    markdown_bytes = render_markdown(profile)
    artifacts = {
        "normalized_traces.jsonl": normalized_bytes,
        "rejected_traces.jsonl": rejected_bytes,
        "corpus_profile.json": profile_bytes,
        "corpus_profile.md": markdown_bytes,
    }
    manifest = {
        "artifact_kind": "corpus_manifest",
        "schema_version": 1,
        "privacy_class": "SYNTHETIC",
        "input_count": profile["input_count"],
        "accepted_count": profile["accepted_count"],
        "rejected_count": profile["rejected_count"],
        "case_generation_eligible_count": profile["case_generation_eligible_count"],
        "artifacts": {
            name: f"sha256:{hashlib.sha256(payload).hexdigest()}"
            for name, payload in artifacts.items()
        },
    }
    artifacts["manifest.json"] = compact_json(manifest)
    _write_atomically(output_path, artifacts)


def _write_atomically(output_path: Path, artifacts: dict[str, bytes]) -> None:
    """Expose a complete bundle with one sibling-directory rename or clean up."""

    # The random private sibling name is operational only: it never enters artifacts,
    # logs, or identity. All files close before one rename exposes the bundle. Failure
    # removes only this invocation's sibling; cleanup failure is an internal invariant
    # failure because claiming ordinary write failure would hide uncertain residue.
    parent = output_path.parent
    try:
        parent_mode = parent.stat().st_mode
    except OSError as error:
        raise PublicationFailure("OUTPUT_WRITE_FAILED", 7) from error
    if parent_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) == 0:
        raise PublicationFailure("OUTPUT_WRITE_FAILED", 7)
    temporary: Path | None = None
    try:
        temporary = Path(
            tempfile.mkdtemp(prefix=f".{output_path.name}.tmp-", dir=parent)
        )
        for name, payload in artifacts.items():
            (temporary / name).write_bytes(payload)
        if os.path.lexists(output_path):
            raise OSError
        temporary.rename(output_path)
    except Exception as error:
        if temporary is not None and temporary.exists():
            try:
                shutil.rmtree(temporary)
            except OSError as cleanup_error:
                raise PublicationFailure(
                    "INTERNAL_INVARIANT_FAILED", 70
                ) from cleanup_error
        raise PublicationFailure("OUTPUT_WRITE_FAILED", 7) from error
