"""Freeze the LABS-01B Observer module ownership and dependency direction."""

from __future__ import annotations

import ast
import shutil
import subprocess
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OBSERVER_ROOT = PROJECT_ROOT / "src" / "triana_labs" / "observer"


def _parse(path: Path) -> ast.Module:
    """Parse a required source module after producing an assertion, never an error."""

    assert path.is_file(), f"required Observer module is absent: {path.name}"
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _top_level_functions(tree: ast.Module) -> set[str]:
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _imported_modules(tree: ast.Module) -> set[str]:
    modules: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def _imported_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            names.update(
                alias.asname or alias.name.split(".")[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in node.names)
    return names


def test_source_package_uses_the_unambiguous_observer_module_names() -> None:
    module_names = {path.name for path in OBSERVER_ROOT.glob("*.py")}

    assert {"profile.py", "renderer.py", "publication.py"} <= module_names
    assert "render.py" not in module_names


def test_profile_module_owns_corpus_count_aggregation_only() -> None:
    tree = _parse(OBSERVER_ROOT / "profile.py")
    functions = _top_level_functions(tree)
    imports = _imported_modules(tree)

    assert "build_profile" in functions
    assert not functions & {"compact_json", "render_markdown", "publish_bundle"}
    assert not imports & {
        "argparse",
        "hashlib",
        "os",
        "shutil",
        "tempfile",
        "triana_labs.cli",
        "triana_labs.observer.renderer",
    }


def test_renderer_module_owns_serialization_and_projection_only() -> None:
    tree = _parse(OBSERVER_ROOT / "renderer.py")
    functions = _top_level_functions(tree)
    imports = _imported_modules(tree)

    assert {"compact_json", "render_markdown"} <= functions
    assert not functions & {"build_profile", "publish_bundle"}
    assert not imports & {
        "argparse",
        "collections",
        "hashlib",
        "os",
        "pathlib",
        "shutil",
        "stat",
        "tempfile",
        "triana_labs.cli",
    }


def test_publication_module_owns_hashing_and_atomic_publication() -> None:
    tree = _parse(OBSERVER_ROOT / "publication.py")
    functions = _top_level_functions(tree)
    imports = _imported_modules(tree)
    imported_names = _imported_names(tree)
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    private_function_nodes = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("_")
    ]

    assert "publish_bundle" in functions
    assert private_function_nodes
    assert any(
        {
            call.func.attr
            for call in ast.walk(function)
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
        }
        & {"rename", "replace"}
        for function in private_function_nodes
    )
    assert "hashlib" in imports or "sha256" in imported_names
    assert "triana_labs.observer.renderer" in imports
    assert "sha256" in called_attributes
    assert called_attributes & {"rename", "replace"}
    assert not functions & {"build_profile", "compact_json", "render_markdown"}


def test_observe_module_keeps_orchestration_and_delegates_other_ownership() -> None:
    tree = _parse(OBSERVER_ROOT / "observe.py")
    functions = _top_level_functions(tree)
    imports = _imported_modules(tree)
    imported_names = _imported_names(tree)

    assert {
        "observe",
        "_validate_output_boundary",
        "_read_input",
        "_physical_lines",
    } <= functions
    assert not functions & {
        "_build_profile",
        "build_profile",
        "compact_json",
        "render_markdown",
        "_publish_bundle",
        "publish_bundle",
        "_write_atomically",
    }
    assert {
        "triana_labs.contracts.traces",
        "triana_labs.observer.profile",
        "triana_labs.observer.publication",
    } <= imports
    assert not imports & {
        "hashlib",
        "shutil",
        "tempfile",
        "triana_labs.observer.render",
        "triana_labs.observer.renderer",
    }
    assert not imported_names & {"Counter", "compact_json", "render_markdown"}


def test_built_wheel_exposes_only_the_target_observer_modules(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    assert uv is not None
    output = tmp_path / "dist"
    completed = subprocess.run(
        [
            uv,
            "build",
            "--wheel",
            "--project",
            str(PROJECT_ROOT),
            "--out-dir",
            str(output),
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr.decode(errors="replace")

    wheel = next(output.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())

    required = {
        "triana_labs/observer/profile.py",
        "triana_labs/observer/renderer.py",
        "triana_labs/observer/publication.py",
    }
    assert required <= names
    assert "triana_labs/observer/render.py" not in names
