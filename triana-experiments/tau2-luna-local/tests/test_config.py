from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("tau2_luna_local") is None,
    reason="production package absent; test_package_contract owns the RED signal",
)


def test_explicit_azure_configuration_has_secret_safe_projection(azure_environ: dict[str, str]) -> None:
    from tau2_luna_local.config import load_config

    config = load_config(azure_environ)
    projection = config.safe_projection()

    assert config.model == "azure/luna-test-deployment"
    assert config.endpoint_host == "unit.openai.azure.com"
    assert projection["environment_presence"]["AZURE_API_KEY"] is True
    assert "test-azure-key-never-persist" not in repr(projection)
    assert projection["task_count"] == projection["trial_count"] == projection["concurrency"] == 1
    assert projection["seed"] == 1729


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("AZURE_API_KEY", ""),
        ("AZURE_API_BASE", ""),
        ("AZURE_API_VERSION", ""),
        ("TAU2_LUNA_DEPLOYMENT", ""),
    ],
)
def test_missing_or_empty_required_configuration_refuses(name: str, value: str, azure_environ: dict[str, str]) -> None:
    from tau2_luna_local.config import ConfigurationError, load_config

    azure_environ[name] = value
    with pytest.raises(ConfigurationError, match=name):
        load_config(azure_environ)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://unit.openai.azure.com",
        "https://example.com/openai",
        "not-a-url",
    ],
)
def test_non_https_or_non_azure_endpoint_refuses(endpoint: str, azure_environ: dict[str, str]) -> None:
    from tau2_luna_local.config import ConfigurationError, load_config

    azure_environ["AZURE_API_BASE"] = endpoint
    with pytest.raises(ConfigurationError, match="AZURE_API_BASE"):
        load_config(azure_environ)


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"task_count": 0}, "task_count"),
        ({"trial_count": 0}, "trial_count"),
        ({"concurrency": 2}, "concurrency"),
        ({"max_steps": 0}, "max_steps"),
        ({"max_errors": -1}, "max_errors"),
    ],
)
def test_unbounded_poc_options_refuse(overrides: dict[str, int], field: str, azure_environ: dict[str, str]) -> None:
    from tau2_luna_local.config import ConfigurationError, load_config

    with pytest.raises(ConfigurationError, match=field):
        load_config(azure_environ, **overrides)


def test_existing_run_directory_refuses_before_benchmark(azure_environ: dict[str, str], tmp_path: Path) -> None:
    from tau2_luna_local.runner import RunRefused, prepare_run_directory

    run_dir = tmp_path / "existing"
    run_dir.mkdir()
    with pytest.raises(RunRefused, match="exist"):
        prepare_run_directory(run_dir)
