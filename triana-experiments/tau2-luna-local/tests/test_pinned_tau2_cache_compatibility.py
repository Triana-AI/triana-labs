from __future__ import annotations

import sys
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest


def test_runner_supports_pinned_llm_utils_without_disable_cache_and_disables_per_call_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tau2_luna_local import runner
    from tau2_luna_local.config import Config

    observed_run_args: list[dict[str, Any]] = []

    class FakeResults:
        def model_dump(self, *, mode: str) -> dict[str, Any]:
            assert mode == "json"
            return {"tasks": [], "reward": None}

    def run_tasks(**kwargs: Any) -> FakeResults:
        observed_run_args.append(kwargs)
        assert kwargs["llm_args_agent"]["caching"] is False
        assert kwargs["llm_args_user"]["caching"] is False
        return FakeResults()

    tau_run = SimpleNamespace(
        get_tasks=lambda *_args, **_kwargs: [SimpleNamespace(id="retail-18")],
        run_tasks=run_tasks,
    )
    llm_utils = SimpleNamespace(completion=lambda **_: None)
    assert not hasattr(llm_utils, "disable_cache")

    class FakeTelemetry:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def __enter__(self) -> FakeTelemetry:
            return self

        def __exit__(self, *_args: Any) -> None:
            pass

        def boundary(self, *_args: Any, **_kwargs: Any) -> Any:
            return nullcontext()

        def record_model_span(self, _payload: dict[str, Any]) -> None:
            pass

    fake_otel = ModuleType("tau2_luna_local.otel")
    fake_otel.LocalTelemetry = FakeTelemetry  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "tau2_luna_local.otel", fake_otel)
    monkeypatch.setattr(runner, "_tau2_modules", lambda: (tau_run, llm_utils))
    monkeypatch.setattr(
        runner,
        "verify_tau2_distribution",
        lambda: {"distribution_version": "0.2.1.dev0", "commit": "frozen", "url": "frozen"},
    )
    monkeypatch.setattr(runner, "verify_bundle", lambda *_args, **_kwargs: {"valid": True})

    run_dir = runner.run_experiment(
        Config(
            api_key="synthetic-secret",
            api_base="https://unit.openai.azure.com",
            api_version="2026-01-01-preview",
            deployment="gpt-5-6-luna-smoke",
            trace_root=tmp_path,
            task_id="18",
        ),
        run_id="cache-compatibility",
    )

    assert run_dir == tmp_path / "cache-compatibility"
    assert len(observed_run_args) == 1
