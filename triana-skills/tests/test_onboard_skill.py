"""Black-box contract for the shared Triana onboarding agent skill."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPOSITORY_ROOT / "triana-skills"
PLUGIN_ROOT = PACKAGE_ROOT / "plugins" / "triana"
SKILL_ROOT = PLUGIN_ROOT / "skills" / "onboard"
TOOL = SKILL_ROOT / "scripts" / "onboard.py"
FIXTURES = Path(__file__).parent / "fixtures"


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _safe_environment(**additions: str) -> dict[str, str]:
    environment = os.environ.copy()
    for key in tuple(environment):
        upper = key.upper()
        if any(token in upper for token in ("API_KEY", "TOKEN", "AZURE", "OPENAI")):
            environment.pop(key)
    environment.update(additions)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _run_tool(
    *arguments: str,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, os.fspath(TOOL), *arguments],
        cwd=PACKAGE_ROOT,
        env=environment or _safe_environment(),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _machine_json(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    stream = completed.stdout if completed.stdout.strip() else completed.stderr
    lines = [line for line in stream.splitlines() if line.strip()]
    if not lines:
        raise AssertionError(f"command emitted no JSON: {completed!r}")
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError as error:
        raise AssertionError(
            f"command did not emit terminal machine JSON: {completed!r}"
        ) from error


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"required JSON artifact is missing: {path}")
    try:
        value = json.loads(path.read_bytes())
    except json.JSONDecodeError as error:
        raise AssertionError(f"required JSON artifact is invalid: {path}") from error
    assert isinstance(value, dict), f"required JSON artifact is not an object: {path}"
    return value


def _authorized(*arguments: str) -> tuple[str, ...]:
    return (*arguments, "--confirm-authorized-traces")


class SkillPackageContractTests(unittest.TestCase):
    def test_one_canonical_skill_serves_codex_and_claude(self) -> None:
        skill = SKILL_ROOT / "SKILL.md"
        self.assertTrue(skill.is_file())
        skills = list(PACKAGE_ROOT.rglob("SKILL.md"))
        self.assertEqual(skills, [skill])
        body = skill.read_text(encoding="utf-8")
        self.assertTrue(body.startswith("---\nname: onboard\n"))
        self.assertIn("description:", body.split("---", 2)[1])
        self.assertIn("scripts/onboard.py", body)

        openai_metadata = SKILL_ROOT / "agents" / "openai.yaml"
        self.assertTrue(openai_metadata.is_file())
        metadata = openai_metadata.read_text(encoding="utf-8")
        for field in ("display_name:", "short_description:", "default_prompt:"):
            self.assertIn(field, metadata)

    def test_claude_marketplace_resolves_the_same_skill_plugin(self) -> None:
        marketplace = _read_json(PACKAGE_ROOT / ".claude-plugin" / "marketplace.json")
        plugin = _read_json(PLUGIN_ROOT / ".claude-plugin" / "plugin.json")
        self.assertEqual(marketplace["name"], "triana-skills")
        self.assertIn(
            {"name": "triana", "source": "./plugins/triana"},
            marketplace["plugins"],
        )
        self.assertEqual(plugin["name"], "triana")
        self.assertTrue((PLUGIN_ROOT / "skills" / "onboard" / "SKILL.md").is_file())


class AuthorizationAndInspectionTests(unittest.TestCase):
    def test_authorization_refuses_before_source_access(self) -> None:
        missing = FIXTURES / "does-not-exist.jsonl"
        completed = _run_tool("inspect", "--source", os.fspath(missing))
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(
            _machine_json(completed)["reason_code"],
            "TRACE_AUTHORIZATION_REQUIRED",
        )

    def test_inspection_is_value_free_but_structurally_useful(self) -> None:
        source = FIXTURES / "raw_unknown.jsonl"
        completed = _run_tool(*_authorized("inspect", "--source", os.fspath(source)))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = _machine_json(completed)
        serialized = json.dumps(result, sort_keys=True)
        self.assertEqual(result["physical_line_count"], 2)
        self.assertEqual(result["root_types"], {"object": 2})
        for structural_name in (
            "session_id",
            "messages",
            "role",
            "content",
            "metadata",
        ):
            self.assertIn(structural_name, serialized)
        for source_value in (
            "synthetic-session-alpha",
            "private-customer@example.invalid",
            "ORD-SYNTH01",
            "synthetic-private-tenant",
            "user",
            "assistant",
        ):
            self.assertNotIn(source_value, serialized)
        self.assertNotIn(os.fspath(source), serialized)

    def test_symlink_and_empty_sources_refuse(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            symlink = Path(temporary) / "linked.jsonl"
            symlink.symlink_to(FIXTURES / "raw_unknown.jsonl")
            for source, reason in (
                (symlink, "TRACE_SOURCE_UNSAFE"),
                (FIXTURES / "empty.jsonl", "TRACE_SOURCE_INVALID"),
            ):
                completed = _run_tool(
                    *_authorized("inspect", "--source", os.fspath(source))
                )
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(_machine_json(completed)["reason_code"], reason)


class PreviewTraceValidationTests(unittest.TestCase):
    def test_valid_previewtrace_passes_byte_stably(self) -> None:
        source = FIXTURES / "valid_preview.jsonl"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "validated.jsonl"
            completed = _run_tool(
                *_authorized(
                    "validate",
                    "--source",
                    os.fspath(source),
                    "--output",
                    os.fspath(output),
                )
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = _machine_json(completed)
            self.assertEqual(output.read_bytes(), source.read_bytes())
            self.assertEqual(result["trace_count"], 4)
            self.assertEqual(result["source_sha256"], _sha256(source.read_bytes()))

    def test_invalid_previewtrace_surfaces_refuse_line_by_line(self) -> None:
        cases = (
            ("invalid_role_preview.jsonl", "PREVIEWTRACE_INVALID"),
            ("invalid_tool_link_preview.jsonl", "PREVIEWTRACE_INVALID"),
            ("duplicate_ids_preview.jsonl", "PREVIEWTRACE_INVALID"),
            ("malformed_preview.jsonl", "PREVIEWTRACE_INVALID"),
            ("empty.jsonl", "ADAPTER_OUTPUT_INVALID"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            for index, (fixture, reason) in enumerate(cases):
                output = Path(temporary) / f"validated-{index}.jsonl"
                completed = _run_tool(
                    *_authorized(
                        "validate",
                        "--source",
                        os.fspath(FIXTURES / fixture),
                        "--output",
                        os.fspath(output),
                    )
                )
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(_machine_json(completed)["reason_code"], reason)
                self.assertFalse(output.exists())

    def test_validator_refuses_unsafe_or_existing_output(self) -> None:
        source = FIXTURES / "valid_preview.jsonl"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            existing = root / "existing.jsonl"
            existing.write_bytes(b"owner-data")
            linked = root / "linked.jsonl"
            linked.symlink_to(existing)
            for output in (existing, linked):
                completed = _run_tool(
                    *_authorized(
                        "validate",
                        "--source",
                        os.fspath(source),
                        "--output",
                        os.fspath(output),
                    )
                )
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(
                    _machine_json(completed)["reason_code"],
                    "ADAPTER_OUTPUT_INVALID",
                )
            self.assertEqual(existing.read_bytes(), b"owner-data")


class ScaffoldAndPreviewTests(unittest.TestCase):
    def test_unknown_schema_scaffold_is_bounded_and_never_overwrites(self) -> None:
        source = FIXTURES / "raw_unknown.jsonl"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "adapter"
            completed = _run_tool(
                *_authorized(
                    "scaffold",
                    "--source",
                    os.fspath(source),
                    "--output-dir",
                    os.fspath(output),
                )
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                {path.name for path in output.iterdir()},
                {"adapter.py", "adapter-contract.json"},
            )
            contract = json.loads((output / "adapter-contract.json").read_bytes())
            self.assertEqual(contract["status"], "IMPLEMENTATION_REQUIRED")
            self.assertEqual(contract["source_sha256"], _sha256(source.read_bytes()))
            combined = b"\n".join(path.read_bytes() for path in output.iterdir())
            self.assertLess(len(combined), 20_000)
            for private_value in (
                b"private-customer@example.invalid",
                b"ORD-SYNTH01",
                b"synthetic-private-tenant",
            ):
                self.assertNotIn(private_value, combined)
            before = {path.name: path.read_bytes() for path in output.iterdir()}

            repeated = _run_tool(
                *_authorized(
                    "scaffold",
                    "--source",
                    os.fspath(source),
                    "--output-dir",
                    os.fspath(output),
                )
            )
            self.assertEqual(repeated.returncode, 2)
            self.assertEqual(
                _machine_json(repeated)["reason_code"],
                "ADAPTER_OUTPUT_INVALID",
            )
            self.assertEqual(
                {path.name: path.read_bytes() for path in output.iterdir()}, before
            )

    def test_validation_preview_is_bounded_and_redacted(self) -> None:
        source = FIXTURES / "valid_preview.jsonl"
        completed = _run_tool(*_authorized("preview", "--source", os.fspath(source)))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = _machine_json(completed)
        self.assertEqual(result["trace_count"], 4)
        self.assertEqual(len(result["previews"]), 3)
        serialized = json.dumps(result["previews"], sort_keys=True)
        for private_value in (
            "private-customer@example.invalid",
            "second-customer@example.invalid",
            "ORD-SYNTH01",
            "ORD-SYNTH02",
            "10 Synthetic Lane",
        ):
            self.assertNotIn(private_value, serialized)
        self.assertIn("USER_MESSAGE", serialized)

    def test_codex_and_claude_share_validator_and_adapter_contracts(self) -> None:
        source = FIXTURES / "valid_preview.jsonl"
        raw = FIXTURES / "raw_unknown.jsonl"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            results: dict[str, dict[str, Any]] = {}
            scaffold_bytes: dict[str, dict[str, bytes]] = {}
            for surface in ("CODEX", "CLAUDE_CODE"):
                environment = _safe_environment(TRIANA_AGENT_SURFACE=surface)
                validated = root / surface / "validated.jsonl"
                validated.parent.mkdir()
                result = _run_tool(
                    *_authorized(
                        "validate",
                        "--source",
                        os.fspath(source),
                        "--output",
                        os.fspath(validated),
                    ),
                    environment=environment,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                results[surface] = _machine_json(result)
                scaffold = root / surface / "scaffold"
                result = _run_tool(
                    *_authorized(
                        "scaffold",
                        "--source",
                        os.fspath(raw),
                        "--output-dir",
                        os.fspath(scaffold),
                    ),
                    environment=environment,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                scaffold_bytes[surface] = {
                    path.name: path.read_bytes() for path in scaffold.iterdir()
                }
            self.assertEqual(results["CODEX"], results["CLAUDE_CODE"])
            self.assertEqual(scaffold_bytes["CODEX"], scaffold_bytes["CLAUDE_CODE"])


class ReleaseAndCommandTests(unittest.TestCase):
    def test_agent_description_accepts_one_to_three_nonempty_lines(self) -> None:
        source = FIXTURES / "valid_preview.jsonl"
        manifest = FIXTURES / "release_pinned.json"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report"
            output.mkdir(mode=0o700)
            for line_count in (1, 2, 3):
                agent = "\n".join(
                    f"Synthetic agent description line {index}."
                    for index in range(1, line_count + 1)
                )
                completed = _run_tool(
                    *_authorized(
                        "docker-command",
                        "--source",
                        os.fspath(source),
                        "--output-dir",
                        os.fspath(output),
                        "--agent",
                        agent,
                        "--release-manifest",
                        os.fspath(manifest),
                    )
                )
                with self.subTest(line_count=line_count):
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertIn(agent, _machine_json(completed)["docker_argv"])

    def test_four_line_agent_description_refuses_with_typed_reason(self) -> None:
        source = FIXTURES / "valid_preview.jsonl"
        manifest = FIXTURES / "release_pinned.json"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report"
            output.mkdir(mode=0o700)
            agent = "\n".join(f"Synthetic line {index}." for index in range(1, 5))
            completed = _run_tool(
                *_authorized(
                    "docker-command",
                    "--source",
                    os.fspath(source),
                    "--output-dir",
                    os.fspath(output),
                    "--agent",
                    agent,
                    "--release-manifest",
                    os.fspath(manifest),
                )
            )
            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(
                _machine_json(completed)["reason_code"],
                "AGENT_DESCRIPTION_INVALID",
            )

    def test_unpublished_or_mutable_release_refuses(self) -> None:
        source = FIXTURES / "valid_preview.jsonl"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report"
            output.mkdir(mode=0o700)
            for manifest, reason in (
                ("release_unpublished.json", "RELEASE_UNPUBLISHED"),
                ("release_mutable.json", "RELEASE_IMAGE_NOT_DIGEST_PINNED"),
            ):
                completed = _run_tool(
                    *_authorized(
                        "docker-command",
                        "--source",
                        os.fspath(source),
                        "--output-dir",
                        os.fspath(output),
                        "--agent",
                        "Synthetic order-support agent.",
                        "--release-manifest",
                        os.fspath(FIXTURES / manifest),
                    )
                )
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(_machine_json(completed)["reason_code"], reason)

    def test_pinned_release_constructs_exact_safe_docker_argv_without_running(
        self,
    ) -> None:
        source = FIXTURES / "valid_preview.jsonl"
        manifest = FIXTURES / "release_pinned.json"
        image = json.loads(manifest.read_bytes())["image"]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "private report"
            output.mkdir(mode=0o700)
            environment = _safe_environment(
                PATH="",
                TRIANA_TEST_TOKEN="must-not-appear",
            )
            completed = _run_tool(
                *_authorized(
                    "docker-command",
                    "--source",
                    os.fspath(source),
                    "--output-dir",
                    os.fspath(output),
                    "--agent",
                    "Synthetic order-support agent.",
                    "--release-manifest",
                    os.fspath(manifest),
                ),
                environment=environment,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = _machine_json(completed)
            expected = [
                "docker",
                "run",
                "--rm",
                "--mount",
                (
                    f"type=bind,src={source.resolve()},"
                    "dst=/triana/input/traces.jsonl,readonly"
                ),
                "--mount",
                f"type=bind,src={output.resolve()},dst=/triana/output",
                image,
                "analyze",
                "--traces",
                "/triana/input/traces.jsonl",
                "--agent",
                "Synthetic order-support agent.",
                "--output",
                "/triana/output",
                "--confirm-authorized-traces",
            ]
            self.assertEqual(result["docker_argv"], expected)
            serialized = json.dumps(result, sort_keys=True)
            self.assertNotIn("must-not-appear", serialized)
            self.assertNotIn("--env", serialized)
            self.assertEqual(result["image"], image)
            self.assertEqual(
                result["release_manifest_sha256"], _sha256(manifest.read_bytes())
            )


if __name__ == "__main__":
    unittest.main()
