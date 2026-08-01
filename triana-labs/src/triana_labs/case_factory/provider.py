"""Internal provider, clock, and atomic-publication seams."""

from __future__ import annotations

import ctypes
import errno
import os
import shutil
import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ProviderRequest:
    url: str
    api_key: str
    body: bytes
    timeout_seconds: int


@dataclass(frozen=True)
class ProviderResponse:
    status_code: int
    body: bytes


class ProviderTransport(Protocol):
    def send(self, request: ProviderRequest) -> ProviderResponse: ...


class Clock(Protocol):
    def monotonic_ns(self) -> int: ...


class ArtifactPublisher(Protocol):
    def publish(self, output_path: Path, artifacts: Mapping[str, bytes]) -> None: ...


@dataclass(frozen=True)
class PublicationFailure(Exception):
    cleanup_failed: bool


class SystemClock:
    def monotonic_ns(self) -> int:
        return time.monotonic_ns()


class AzureOpenAITransport:
    def send(self, request: ProviderRequest) -> ProviderResponse:
        call = urllib.request.Request(
            request.url,
            data=request.body,
            headers={"Content-Type": "application/json", "api-key": request.api_key},
            method="POST",
        )
        opener = urllib.request.build_opener(
            _NoRedirect,
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        )
        try:
            with opener.open(call, timeout=request.timeout_seconds) as response:
                return ProviderResponse(response.status, response.read(1_000_001))
        except urllib.error.HTTPError as error:
            return ProviderResponse(error.code, error.read(1_000_001))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: object, fp: object, code: int, msg: str, headers: object, newurl: str
    ) -> None:
        return None


def _rename_no_replace(source: Path, target: Path) -> None:
    library = ctypes.CDLL(None, use_errno=True)
    old, new = os.fsencode(source), os.fsencode(target)
    if sys.platform == "darwin":
        result = library.renamex_np(old, new, 4)
    elif sys.platform.startswith("linux"):
        try:
            rename = library.renameat2
        except AttributeError as error:
            raise OSError(
                errno.ENOTSUP, "atomic no-replace rename unavailable"
            ) from error
        result = rename(-100, old, -100, new, 1)
    else:
        raise OSError(errno.ENOTSUP, "atomic no-replace rename unavailable")
    if result != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), target)


class AtomicPublisher:
    def publish(self, output_path: Path, artifacts: Mapping[str, bytes]) -> None:
        temporary: Path | None = None
        try:
            temporary = Path(
                tempfile.mkdtemp(
                    prefix=f".{output_path.name}.tmp-", dir=output_path.parent
                )
            )
            names = [name for name in artifacts if name != "manifest.json"]
            if "manifest.json" in artifacts:
                names.append("manifest.json")
            for name in names:
                payload = artifacts[name]
                target = temporary / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("wb") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
            directory = os.open(temporary, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            ready = temporary.with_name(f"{temporary.name}.ready")
            temporary.rename(ready)
            temporary = ready
            if os.path.lexists(output_path):
                raise OSError
            _rename_no_replace(temporary, output_path)
            temporary = None
        except BaseException as error:
            if temporary is not None and temporary.exists():
                try:
                    shutil.rmtree(temporary)
                except OSError as cleanup:
                    raise PublicationFailure(True) from cleanup
            raise PublicationFailure(False) from error
