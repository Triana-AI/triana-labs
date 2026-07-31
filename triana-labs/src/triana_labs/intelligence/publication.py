"""Atomically publish a deterministic structural intelligence bundle."""

from __future__ import annotations

import os
import shutil
import stat
import tempfile
from pathlib import Path


class PublicationFailure(Exception):
    """Carry a content-free publication refusal reason."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


def publish(output_path: Path, artifacts: dict[str, bytes]) -> None:
    """Publish a complete nested bundle by one sibling-directory rename."""

    if os.path.lexists(output_path):
        raise PublicationFailure("OUTPUT_ALREADY_EXISTS")
    parent = output_path.parent
    try:
        metadata = parent.lstat()
    except OSError as error:
        raise PublicationFailure("OUTPUT_PARENT_MISSING") from error
    if parent.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
        raise PublicationFailure("OUTPUT_PARENT_MISSING")
    if metadata.st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) == 0:
        raise PublicationFailure("OUTPUT_WRITE_FAILED")
    temporary: Path | None = None
    try:
        temporary = Path(
            tempfile.mkdtemp(prefix=f".{output_path.name}.tmp-", dir=parent)
        )
        for name, payload in artifacts.items():
            destination = temporary / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
        if os.path.lexists(output_path):
            raise OSError
        temporary.rename(output_path)
    except Exception as error:
        if temporary is not None and temporary.exists():
            try:
                shutil.rmtree(temporary)
            except OSError as cleanup_error:
                raise PublicationFailure("INTERNAL_INVARIANT_FAILED") from cleanup_error
        raise PublicationFailure("OUTPUT_WRITE_FAILED") from error
