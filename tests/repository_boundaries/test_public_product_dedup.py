"""Black-box repository-boundary contract for public-product deduplication."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).with_name("canonical_public_products.json")
MANIFEST = ROOT / "internal" / "PUBLIC_PRODUCT_DEDUP_MANIFEST_2026-08-12.json"
SHA256_PREFIX = "sha256:"
DISPOSITION_CODES = {
    "EXACT_PUBLIC_COPY",
    "ALLOWLISTED_EXTRACTION",
    "BEHAVIORALLY_PRESERVED",
    "RETIRED_GIT_HISTORY",
    "SUPERSEDED_STAGING",
}
MONOREPO_HISTORY_REPOSITORY = "triana-monorepo"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(path: Path) -> str:
    return SHA256_PREFIX + hashlib.sha256(path.read_bytes()).hexdigest()


def _inventory_digest(files: dict[str, str]) -> str:
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return SHA256_PREFIX + hashlib.sha256(encoded).hexdigest()


def _is_relative_file_path(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and value == path.as_posix()


class PublicProductDedupContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = _load(FIXTURE)

    def test_frozen_public_commits_and_complete_inventories_are_canonical(self) -> None:
        self.assertEqual(
            set(self.fixture),
            {
                "schema_version",
                "canonical_repositories",
                "deleted_production_candidates",
                "retired_git_history",
                "retained_private_files",
            },
        )
        self.assertEqual(self.fixture["schema_version"], 1)
        repositories = self.fixture["canonical_repositories"]
        self.assertEqual(set(repositories), {"triana-preview", "triana-skills"})
        self.assertEqual(
            repositories["triana-preview"]["commit"],
            "a738e3fdf4364f2d46913b40ed59297b290cb96f",
        )
        self.assertEqual(
            repositories["triana-skills"]["commit"],
            "0ce39bcdbcb90ff964cfc180eda34adc56b0362c",
        )
        self.assertEqual(len(repositories["triana-preview"]["files"]), 31)
        self.assertEqual(len(repositories["triana-skills"]["files"]), 15)
        for repository in repositories.values():
            self.assertEqual(set(repository), {"commit", "files"})
            self.assertRegex(repository["commit"], r"^[0-9a-f]{40}$")
            for path, digest in repository["files"].items():
                self.assertTrue(_is_relative_file_path(path), path)
                self.assertRegex(digest, r"^sha256:[0-9a-f]{64}$")

    def test_retired_private_utilities_are_recoverable_byte_for_byte_from_git(self) -> None:
        history = self.fixture["retired_git_history"]
        self.assertEqual(set(history), {"commit", "files"})
        self.assertEqual(history["commit"], "ab5079548a42ed2ca1f37dded5deeaa77e32d251")
        self.assertEqual(
            set(history["files"]),
            {
                "triana-labs/src/triana_labs/behavior_map/benchmark.py",
                "triana-labs/src/triana_labs/behavior_map/checkpoint_migration.py",
                "triana-labs/src/triana_labs/behavior_map/comparison.py",
                "triana-labs/src/triana_labs/behavior_map/historical_projection.py",
            },
        )
        for relative, expected in history["files"].items():
            self.assertEqual(expected, self.fixture["deleted_production_candidates"][relative])
            committed = subprocess.run(
                ["git", "show", f"{history['commit']}:{relative}"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            ).stdout
            actual = SHA256_PREFIX + hashlib.sha256(committed).hexdigest()
            self.assertEqual(actual, expected, f"Git history bytes differ for {relative}")

    def test_monorepo_staging_and_removed_behavior_map_package_are_absent(self) -> None:
        forbidden = (
            ROOT / "triana-preview",
            ROOT / "triana-skills",
            ROOT / "triana-labs" / "src" / "triana_labs" / "behavior_map",
        )
        present = [path.relative_to(ROOT).as_posix() for path in forbidden if path.exists()]
        self.assertEqual(present, [], f"duplicate product trees remain: {present}")

    def test_no_production_python_module_imports_removed_behavior_map(self) -> None:
        offenders: list[str] = []
        for path in ROOT.rglob("*.py"):
            relative = path.relative_to(ROOT)
            if any(part in {".git", ".venv", "__pycache__", "tests"} for part in relative.parts):
                continue
            if "src" not in relative.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(relative))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                    is_relative = False
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                    is_relative = bool(node.level)
                    if node.level and node.module in {None, ""}:
                        names.extend(alias.name for alias in node.names)
                else:
                    continue
                if any(
                    name == "triana_labs.behavior_map"
                    or name.startswith("triana_labs.behavior_map.")
                    or (is_relative and (name == "behavior_map" or name.startswith("behavior_map.")))
                    for name in names
                ):
                    offenders.append(f"{relative}:{node.lineno}")
        self.assertEqual(offenders, [], f"production importers remain: {offenders}")

    def test_distinct_trace_simulation_and_backend_code_is_retained_unchanged(self) -> None:
        mismatches = {}
        for relative, expected in self.fixture["retained_private_files"].items():
            path = ROOT / relative
            actual = _digest(path) if path.is_file() else "missing"
            if actual != expected:
                mismatches[relative] = {"expected": expected, "actual": actual}
        self.assertEqual(mismatches, {}, f"private product code changed or disappeared: {mismatches}")

    def test_every_deleted_production_file_has_closed_machine_readable_disposition(self) -> None:
        self.assertTrue(MANIFEST.is_file(), f"missing disposition manifest: {MANIFEST.relative_to(ROOT)}")
        manifest = _load(MANIFEST)
        self.assertEqual(
            set(manifest),
            {"artifact_kind", "schema_version", "canonical_repositories", "dispositions"},
        )
        self.assertEqual(manifest["artifact_kind"], "public_product_dedup_manifest_v1")
        self.assertEqual(manifest["schema_version"], 1)

        canonical = self.fixture["canonical_repositories"]
        manifest_repositories = manifest["canonical_repositories"]
        self.assertEqual(set(manifest_repositories), set(canonical))
        for name, receipt in manifest_repositories.items():
            self.assertEqual(set(receipt), {"commit", "inventory_sha256"})
            self.assertEqual(receipt["commit"], canonical[name]["commit"])
            self.assertEqual(receipt["inventory_sha256"], _inventory_digest(canonical[name]["files"]))

        expected_paths = set(self.fixture["deleted_production_candidates"])
        dispositions = manifest["dispositions"]
        self.assertIsInstance(dispositions, list)
        self.assertEqual(len(dispositions), len(expected_paths))
        by_path = {entry.get("path"): entry for entry in dispositions}
        self.assertEqual(set(by_path), expected_paths)

        for relative, source_digest in self.fixture["deleted_production_candidates"].items():
            entry = by_path[relative]
            self.assertEqual(
                set(entry),
                {"path", "source_sha256", "disposition", "preservation_target"},
            )
            self.assertTrue(_is_relative_file_path(entry["path"]), entry["path"])
            self.assertEqual(entry["source_sha256"], source_digest)
            self.assertIn(entry["disposition"], DISPOSITION_CODES)
            if relative in self.fixture["retired_git_history"]["files"]:
                self.assertEqual(entry["disposition"], "RETIRED_GIT_HISTORY")
            else:
                self.assertNotEqual(entry["disposition"], "RETIRED_GIT_HISTORY")
            self.assertFalse((ROOT / relative).exists(), f"recorded file was not deleted: {relative}")

            target = entry["preservation_target"]
            self.assertEqual(set(target), {"repository", "commit", "path", "sha256"})
            self.assertTrue(_is_relative_file_path(target["path"]), target["path"])
            if entry["disposition"] == "RETIRED_GIT_HISTORY":
                history = self.fixture["retired_git_history"]
                self.assertEqual(target["repository"], MONOREPO_HISTORY_REPOSITORY)
                self.assertEqual(target["commit"], history["commit"])
                self.assertEqual(target["path"], relative)
                self.assertEqual(target["sha256"], history["files"].get(relative))
                self.assertEqual(target["sha256"], source_digest)
            else:
                repository = target["repository"]
                self.assertIn(repository, canonical)
                self.assertEqual(target["commit"], canonical[repository]["commit"])
                self.assertEqual(target["sha256"], canonical[repository]["files"].get(target["path"]))
                if entry["disposition"] == "EXACT_PUBLIC_COPY":
                    self.assertEqual(target["sha256"], source_digest)


if __name__ == "__main__":
    unittest.main()
