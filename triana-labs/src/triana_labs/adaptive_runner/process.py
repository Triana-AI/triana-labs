from __future__ import annotations

import hashlib
import json
import os
import select
import stat
import subprocess
import time
from typing import Any

from .contracts import JsonObject, TargetLaunch, TargetProtocolFailure

_MAX_LINE = 1_048_576
_SOURCE_SNAPSHOTS: dict[
    tuple[str, str, str], tuple[str, str, str, tuple[int, int], str, str]
] = {}


def _register_source_snapshot(
    identity: tuple[str, str, str],
    cwd: str,
    executable: str,
    adapter: str,
    cwd_stat: tuple[int, int],
    executable_hash: str,
    adapter_hash: str,
) -> None:
    _SOURCE_SNAPSHOTS[identity] = (
        cwd,
        executable,
        adapter,
        cwd_stat,
        executable_hash,
        adapter_hash,
    )


def _file_hash(path: str) -> str:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise OSError
        return "sha256:" + hashlib.sha256(stream.read()).hexdigest()


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError
        value[key] = item
    return value


def _read_line(process: subprocess.Popen[bytes], timeout: float) -> bytes:
    assert process.stdout is not None and process.stderr is not None
    deadline, line = time.monotonic() + timeout, bytearray()
    while not line.endswith(b"\n"):
        ready, _, _ = select.select(
            [process.stdout, process.stderr],
            [],
            [],
            max(0.0, deadline - time.monotonic()),
        )
        if not ready:
            raise TargetProtocolFailure("TARGET_TIMEOUT")
        if process.stderr in ready and os.read(process.stderr.fileno(), _MAX_LINE):
            raise TargetProtocolFailure("TARGET_STDERR")
        if process.stdout in ready:
            chunk = os.read(process.stdout.fileno(), _MAX_LINE + 1 - len(line))
            if not chunk:
                raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
            line.extend(chunk)
        if len(line) > _MAX_LINE:
            raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
    return bytes(line)


class _Session:
    def __init__(self, process: subprocess.Popen[bytes], timeout: int) -> None:
        self._process = process
        self._timeout = timeout
        self._terminated = False

    def exchange(self, request: JsonObject) -> JsonObject:
        process = self._process
        try:
            assert process.stdin is not None and process.stdout is not None
            assert process.stderr is not None
            if process.poll() is not None:
                raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
            payload = (
                json.dumps(
                    dict(request),
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("utf-8")
                + b"\n"
            )
            process.stdin.write(payload)
            process.stdin.flush()
            line = _read_line(process, self._timeout)
            if line == b"\n":
                raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
            try:
                decoded = line.decode("utf-8")
                value = json.loads(decoded, object_pairs_hook=_object_pairs)
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
                raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR") from error
            if not isinstance(value, dict):
                raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
            # A second already-buffered response violates one-request/one-response.
            more, _, _ = select.select([process.stdout, process.stderr], [], [], 0.01)
            if process.stderr in more and os.read(process.stderr.fileno(), _MAX_LINE):
                raise TargetProtocolFailure("TARGET_STDERR")
            if process.stdout in more:
                raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
            return value
        except TargetProtocolFailure:
            raise
        except (BrokenPipeError, OSError, ValueError) as error:
            raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR") from error

    def terminate(self) -> None:
        if self._terminated:
            return
        self._terminated = True
        process = self._process
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)


class JsonlTargetProcessFactory:
    """Start only the target argv/cwd/environment carried by a verified launch."""

    def start(self, launch: TargetLaunch) -> _Session:
        target = launch.target_config
        argv = target["argv"]
        cwd = target["cwd"]
        timeout = target["timeout_seconds"]
        environment = {"LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"}
        environment.update(launch.environment)
        try:
            identity = (
                launch.source_identity.source_commit,
                launch.source_identity.source_tree_hash,
                launch.source_identity.adapter_file_hash,
            )
            snapshot = _SOURCE_SNAPSHOTS.get(identity)
            if snapshot is not None:
                (
                    pinned_cwd,
                    pinned_executable,
                    pinned_adapter,
                    pinned_cwd_stat,
                    executable_hash,
                    adapter_hash,
                ) = snapshot
                current = os.lstat(cwd)
                head = subprocess.run(
                    ["git", "-C", cwd, "rev-parse", "HEAD"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                ).stdout.strip()
                dirty = subprocess.run(
                    ["git", "-C", cwd, "status", "--porcelain", "--untracked-files=no"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                ).stdout
                if (
                    cwd != pinned_cwd
                    or argv[0] != pinned_executable
                    or argv[1] != pinned_adapter
                    or (current.st_dev, current.st_ino) != pinned_cwd_stat
                    or head != launch.source_identity.source_commit
                    or dirty
                    or _file_hash(argv[0]) != executable_hash
                    or _file_hash(argv[1]) != adapter_hash
                ):
                    raise OSError
            process = subprocess.Popen(
                argv,
                cwd=cwd,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR") from error
        return _Session(process, timeout)
