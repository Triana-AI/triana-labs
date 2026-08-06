from __future__ import annotations

import ast
import json
import sys
from contextlib import nullcontext
from decimal import Decimal
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLOUD_WORKER = PROJECT_ROOT / "scripts" / "cloud_worker.py"
EXACT_TASK_PANEL = (83, 113, 5, 52, 64, 58, 21, 85, 7, 23)


def _calls(function: ast.AST, name: str) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name
    ]


def test_cloud_worker_drives_fixed_terra_panel_with_fresh_task_local_budgets() -> None:
    tree = ast.parse(CLOUD_WORKER.read_text(), filename=str(CLOUD_WORKER))
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")

    terra_imports = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "tau2_luna_local.terra_smoke"
        for alias in node.names
    }
    assert {
        "TERRA_TASK_PANEL",
        "TerraModelCallBudget",
        "TerraPanelRateLimiter",
        "run_terra_panel",
    } <= terra_imports

    panel_calls = _calls(main, "run_terra_panel")
    assert len(panel_calls) == 1
    task_ids = next(keyword.value for keyword in panel_calls[0].keywords if keyword.arg == "task_ids")
    assert isinstance(task_ids, ast.Name) and task_ids.id == "TERRA_TASK_PANEL"

    execute = next(keyword.value for keyword in panel_calls[0].keywords if keyword.arg == "execute")
    assert isinstance(execute, ast.Name)
    task_executor = next(
        node
        for node in ast.walk(main)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == execute.id
    )
    limiter_assignments = [
        statement
        for statement in main.body
        if isinstance(statement, ast.Assign)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Name)
        and statement.value.func.id == "TerraPanelRateLimiter"
    ]
    assert len(limiter_assignments) == 1
    limiter_target = limiter_assignments[0].targets[0]
    assert isinstance(limiter_target, ast.Name)
    assert _calls(task_executor, "TerraPanelRateLimiter") == []

    budget_calls = _calls(task_executor, "TerraModelCallBudget")
    assert len(budget_calls) == 1
    task_id = next(keyword.value for keyword in budget_calls[0].keywords if keyword.arg == "task_id")
    assert isinstance(task_id, ast.Name) and task_id.id == "task_id"
    rate_limiter = next(
        keyword.value for keyword in budget_calls[0].keywords if keyword.arg == "rate_limiter"
    )
    assert isinstance(rate_limiter, ast.Name) and rate_limiter.id == limiter_target.id
    assert len(_calls(task_executor, "run_experiment")) == 1

    completion_ceilings = [
        node
        for node in ast.walk(task_executor)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "kwargs"
        and node.func.attr == "setdefault"
        and len(node.args) == 2
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "max_completion_tokens"
    ]
    assert len(completion_ceilings) == 1
    ceiling = completion_ceilings[0].args[1]
    assert isinstance(ceiling, ast.Constant) and ceiling.value == 8_192

    assert "ModelCallBudget" not in {
        alias.name for node in tree.body if isinstance(node, ast.ImportFrom) for alias in node.names
    }
    assert EXACT_TASK_PANEL == (83, 113, 5, 52, 64, 58, 21, 85, 7, 23)


def test_runner_integrates_boundary_context_into_captured_agent_user_and_unknown_lanes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tau2_luna_local import runner
    from tau2_luna_local.config import Config

    llm_utils = SimpleNamespace(
        completion=lambda **_: {
            "id": "fake-response",
            "usage": {"prompt_tokens": 1_000, "completion_tokens": 1_000},
        }
    )
    agent_boundary = SimpleNamespace(generate=lambda: llm_utils.completion(messages=[]))
    user_boundary = SimpleNamespace(generate=lambda: llm_utils.completion(messages=[]))

    class FakeResults:
        def model_dump(self, *, mode: str) -> dict[str, Any]:
            assert mode == "json"
            return {"tasks": [], "reward": None}

    def run_tasks(**_: Any) -> FakeResults:
        agent_boundary.generate()
        user_boundary.generate()
        llm_utils.completion(messages=[])
        return FakeResults()

    tau_run = SimpleNamespace(
        get_tasks=lambda *_args, **_kwargs: [SimpleNamespace(id="retail-83")],
        run_tasks=run_tasks,
    )

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
        "_tau2_role_modules",
        lambda: {"agent": agent_boundary, "user": user_boundary},
        raising=False,
    )
    monkeypatch.setattr(
        runner,
        "verify_tau2_distribution",
        lambda: {"distribution_version": "fake", "commit": "frozen", "url": "frozen"},
    )
    monkeypatch.setattr(runner, "verify_bundle", lambda *_args, **_kwargs: {"valid": True})

    run_dir = runner.run_experiment(
        Config(
            api_key="synthetic-secret",
            api_base="https://unit.openai.azure.com",
            api_version="2026-01-01-preview",
            deployment="gpt-5-6-terra-sentinel",
            trace_root=tmp_path,
            task_id="83",
        ),
        run_id="role-integration",
    )

    events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text().splitlines()]
    requests = [event["payload"] for event in events if event["event_name"] == "model.request"]
    responses = [event["payload"] for event in events if event["event_name"] == "model.response"]
    assert [request["role_lane"] for request in requests] == ["agent", "user", "unknown"]
    assert "role_lane_gap" not in requests[0]
    assert "role_lane_gap" not in requests[1]
    assert requests[2]["role_lane_gap"] == "BOUNDARY_NOT_OBSERVABLE"
    assert all(response["cost"] is not None for response in responses)
    assert all(Decimal(str(response["cost"])) == Decimal("0.017500") for response in responses)
    assert all(response["cost_source"]["kind"] == "CALCULATED_FROM_RETURNED_USAGE" for response in responses)
