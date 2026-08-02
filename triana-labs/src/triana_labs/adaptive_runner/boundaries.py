from __future__ import annotations

import hashlib
import json
import os
import ssl
import stat
import subprocess
import urllib.error
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .contracts import (
    AdaptiveRunFailure,
    SimulatorResponse,
    TargetSourceIdentity,
    VerifiedCaseFactoryInput,
    VerifiedCaseProjection,
)
from .runner import (
    CASE_HASH,
    CASE_IDS,
    MANIFEST_HASH,
    _canonical,
    _hash,
    _integer,
    _pairs,
)


def _regular(path: Path) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise OSError
        return stream.read()


def _json(payload: bytes) -> Any:
    return json.loads(payload, object_pairs_hook=_pairs)


class CaseFactoryLoader:
    def load(self, manifest_path: Path) -> VerifiedCaseFactoryInput:
        manifest_bytes = _regular(manifest_path)
        if _hash(manifest_bytes) != MANIFEST_HASH:
            raise AdaptiveRunFailure("CASE_INTEGRITY_FAILED", 4)
        manifest = _json(manifest_bytes)
        if (
            not isinstance(manifest, dict)
            or manifest.get("artifact_kind") != "case_factory_manifest"
        ):
            raise AdaptiveRunFailure("MANIFEST_INVALID", 4)
        root = manifest_path.parent
        if (
            root.is_symlink()
            or not root.is_dir()
            or not isinstance(manifest.get("artifacts"), dict)
        ):
            raise AdaptiveRunFailure("MANIFEST_INVALID", 4)
        loaded: dict[str, bytes] = {}
        for name, digest in manifest["artifacts"].items():
            if (
                not isinstance(name, str)
                or Path(name).name != name
                or not isinstance(digest, str)
            ):
                raise AdaptiveRunFailure("MANIFEST_INVALID", 4)
            payload = _regular(root / name)
            if _hash(payload) != digest:
                raise AdaptiveRunFailure("CASE_INTEGRITY_FAILED", 4)
            loaded[name] = payload
        if _hash(loaded.get("case_candidates.jsonl", b"")) != CASE_HASH:
            raise AdaptiveRunFailure("CASE_INTEGRITY_FAILED", 4)

        def records(name: str, id_key: str) -> dict[str, dict[str, Any]]:
            result: dict[str, dict[str, Any]] = {}
            for line in loaded[name].splitlines():
                item = _json(line)
                if (
                    not isinstance(item, dict)
                    or not isinstance(item.get(id_key), str)
                    or item[id_key] in result
                ):
                    raise AdaptiveRunFailure("CASE_INTEGRITY_FAILED", 4)
                result[item[id_key]] = item
            return result

        personas = records("personas.jsonl", "persona_id")
        intents = records("intents.jsonl", "intent_id")
        policies = records("turn_policies.jsonl", "turn_policy_id")
        cases = records("case_candidates.jsonl", "case_id")
        try:
            projections = tuple(
                VerifiedCaseProjection(
                    cases[case_id],
                    personas[cases[case_id]["persona_id"]],
                    intents[cases[case_id]["intent_id"]],
                    policies[cases[case_id]["turn_policy_id"]],
                )
                for case_id in CASE_IDS
            )
        except KeyError as error:
            raise AdaptiveRunFailure("CASE_INTEGRITY_FAILED", 4) from error
        return VerifiedCaseFactoryInput(
            MANIFEST_HASH,
            CASE_HASH,
            manifest["input_manifest_hash"],
            manifest["intelligence_manifest_hash"],
            projections,
        )


class GitTargetSourceVerifier:
    def verify(self, target_config: Mapping[str, Any]) -> TargetSourceIdentity:
        try:
            cwd = Path(target_config["cwd"])
            argv = [Path(item) for item in target_config["argv"]]
            if (
                cwd.is_symlink()
                or not cwd.is_dir()
                or any(not item.is_absolute() for item in argv[:2])
            ):
                raise OSError
            executable, adapter = argv[0], argv[1]
            executable_info, adapter_info = executable.lstat(), adapter.lstat()
            if (
                executable.is_symlink()
                or adapter.is_symlink()
                or not stat.S_ISREG(executable_info.st_mode)
                or not stat.S_ISREG(adapter_info.st_mode)
            ):
                raise OSError
            if not os.access(executable, os.X_OK) or not os.access(adapter, os.R_OK):
                raise OSError
            command = ["git", "-C", os.fspath(cwd)]
            head = subprocess.run(
                [*command, "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
            tree = subprocess.run(
                [*command, "rev-parse", f"{head}^{{tree}}"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
            dirty = subprocess.run(
                [*command, "status", "--porcelain", "--untracked-files=no"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout
            if head != target_config["source_commit"] or dirty:
                raise OSError
            adapter_hash = _hash(_regular(adapter))
        except (OSError, KeyError, subprocess.SubprocessError) as error:
            raise AdaptiveRunFailure("TARGET_SOURCE_MISMATCH", 4) from error
        identity = TargetSourceIdentity(
            head, "sha256:" + hashlib.sha256(tree.encode()).hexdigest(), adapter_hash
        )
        from .process import _register_source_snapshot

        cwd_info = cwd.lstat()
        _register_source_snapshot(
            (
                identity.source_commit,
                identity.source_tree_hash,
                identity.adapter_file_hash,
            ),
            os.fspath(cwd),
            os.fspath(executable),
            os.fspath(adapter),
            (cwd_info.st_dev, cwd_info.st_ino),
            _hash(_regular(executable)),
            adapter_hash,
        )
        return identity


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: object, fp: object, code: int, msg: str, headers: object, newurl: str
    ) -> None:
        return None


class FoundrySimulatorTransport:
    """One-attempt, no-redirect OpenAI-compatible simulator transport."""

    def __init__(self, config: dict[str, Any], api_key: str) -> None:
        self._config = config
        self._api_key = api_key

    def complete(self, request: Mapping[str, Any]) -> SimulatorResponse:
        schema = _json(
            b'{"additionalProperties":false,"properties":{"consumed_observation_hash":{"type":"string"},"next_user_content":{"type":"string"},"proposed_stop":{"type":"boolean"},"stop_reason":{"type":["string","null"]}},"required":["next_user_content","consumed_observation_hash","proposed_stop","stop_reason"],"type":"object"}'
        )
        body_value = _json(
            b'{"messages":[{"content":"LABS05_ADAPTIVE_USER_V1: react only to the latest bounded evidence.","role":"system"},{"content":"","role":"user"}],"model":"","n":1,"response_format":{"json_schema":{"name":"next_user_turn","schema":{},"strict":true},"type":"json_schema"},"seed":0,"temperature":0}'
        )
        body_value["model"] = self._config["deployment"]
        body_value["seed"] = self._config["seed"]
        body_value["messages"][1]["content"] = _canonical(request).decode()
        body_value["response_format"]["json_schema"]["schema"] = schema
        body = _canonical(body_value)
        call = urllib.request.Request(
            self._config["endpoint"] + "/chat/completions",
            data=body,
            headers={"Content-Type": "application/json", "api-key": self._api_key},
            method="POST",
        )
        opener = urllib.request.build_opener(
            _NoRedirect,
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        )
        try:
            with opener.open(call, timeout=self._config["timeout_seconds"]) as response:
                response_bytes = response.read(1_000_001)
        except (urllib.error.URLError, TimeoutError, OSError):
            return SimulatorResponse(
                "FAILED",
                body,
                None,
                None,
                None,
                None,
                None,
                0,
                0,
                1,
                None,
                "SIMULATOR_PROVIDER_ERROR",
            )
        try:
            envelope = _json(response_bytes)
            content = envelope["choices"][0]["message"]["content"]
            value = _json(content.encode())
            usage = envelope.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            if (
                not isinstance(value, dict)
                or not _integer(input_tokens)
                or not _integer(output_tokens)
                or set(value)
                != {
                    "next_user_content",
                    "consumed_observation_hash",
                    "proposed_stop",
                    "stop_reason",
                }
            ):
                raise ValueError
            return SimulatorResponse(
                "SUCCEEDED",
                body,
                response_bytes,
                value["next_user_content"],
                value["consumed_observation_hash"],
                value["proposed_stop"],
                value["stop_reason"],
                input_tokens,
                output_tokens,
                1,
                None,
                None,
            )
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
            return SimulatorResponse(
                "INVALID",
                body,
                response_bytes,
                None,
                None,
                None,
                None,
                0,
                0,
                1,
                None,
                "SIMULATOR_INVALID_RESPONSE",
            )
