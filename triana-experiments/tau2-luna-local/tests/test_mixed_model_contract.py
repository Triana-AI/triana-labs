from __future__ import annotations

import json
import sys
from contextlib import nullcontext
from decimal import Decimal
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

TERRA_MODEL = "azure/gpt-5-6-terra-sentinel"
LUNA_MODEL = "azure/tau2-luna-smoke-20260805"
LUNA_BASE = "https://kairos-memory.openai.azure.com/"
API_VERSION = "2026-01-01-preview"


class NullCostResponse(dict[str, Any]):
    def __init__(self) -> None:
        super().__init__(
            id="mixed-model-response",
            choices=[{"finish_reason": "stop", "message": {"content": "unchanged"}}],
            usage={"prompt_tokens": 1_000, "completion_tokens": 1_000},
        )
        self._hidden_params = {"response_cost": None}
        self._response_headers = {"x-request-id": "mixed-model-request"}


def test_requested_model_selects_exact_cost_fallback_without_raw_mutation() -> None:
    from tau2_luna_local.capture import CompletionCapture
    from tau2_luna_local.terra_smoke import (
        luna_response_cost_fallback,
        terra_response_cost_fallback,
    )

    events: list[tuple[str, dict[str, Any]]] = []
    responses: list[NullCostResponse] = []

    def provider(**_: Any) -> NullCostResponse:
        response = NullCostResponse()
        responses.append(response)
        return response

    target = SimpleNamespace(completion=provider)
    with CompletionCapture(
        target=target,
        event_sink=lambda name, payload: events.append((name, payload)),
        span_sink=lambda _: None,
        response_cost_fallbacks={
            TERRA_MODEL: terra_response_cost_fallback,
            LUNA_MODEL: luna_response_cost_fallback,
        },
    ):
        target.completion(model=TERRA_MODEL, messages=[])
        target.completion(model=LUNA_MODEL, messages=[])

    terminals = [payload for name, payload in events if name == "model.response"]
    assert [Decimal(str(item["cost"])) for item in terminals] == [
        Decimal("0.017500"),
        Decimal("0.007000"),
    ]
    assert terminals[0]["cost_source"] == {
        "kind": "CALCULATED_FROM_RETURNED_USAGE",
        "input_price_per_million_usd": "2.50",
        "output_price_per_million_usd": "15.00",
    }
    assert terminals[1]["cost_source"] == {
        "kind": "CALCULATED_FROM_RETURNED_USAGE",
        "input_price_per_million_usd": "1.00",
        "output_price_per_million_usd": "6.00",
    }
    assert all(response == NullCostResponse() for response in responses)


def test_task_allocations_and_panel_limiters_are_separate_and_sum_to_9_60() -> None:
    from tau2_luna_local.terra_smoke import (
        LUNA_TASK_CAP_USD,
        TERRA_TASK_CAP_USD,
        LunaModelCallBudget,
        LunaPanelRateLimiter,
        TerraModelCallBudget,
        TerraPanelRateLimiter,
    )

    assert Decimal("0.90") == TERRA_TASK_CAP_USD
    assert Decimal("0.06") == LUNA_TASK_CAP_USD
    assert Decimal("9.60") == (TERRA_TASK_CAP_USD + LUNA_TASK_CAP_USD) * 10

    terra = TerraModelCallBudget(task_id=83, rate_limiter=TerraPanelRateLimiter())
    luna = LunaModelCallBudget(task_id=83, rate_limiter=LunaPanelRateLimiter())
    assert terra.task_cap_usd == Decimal("0.90")
    assert luna.task_cap_usd == Decimal("0.06")


def test_luna_missing_usage_and_429_charge_reservation_once_without_retry() -> None:
    from tau2_luna_local.terra_smoke import LunaModelCallBudget, LunaPanelRateLimiter

    calls = 0
    budget = LunaModelCallBudget(task_id=83, rate_limiter=LunaPanelRateLimiter())

    def missing_usage(**_: Any) -> dict[str, str]:
        return {"id": "no-usage"}

    budget.call(
        missing_usage,
        input_token_reservation=1_000,
        max_completion_tokens=2_048,
    )
    assert budget.ledger[-1]["outcome"] == "CONSERVATIVE_MISSING_USAGE"

    class Synthetic429(RuntimeError):
        pass

    def provider_429(**_: Any) -> None:
        nonlocal calls
        calls += 1
        raise Synthetic429("synthetic 429")

    with pytest.raises(Synthetic429, match="429"):
        budget.call(
            provider_429,
            input_token_reservation=1_000,
            max_completion_tokens=2_048,
        )
    assert calls == 1
    assert budget.ledger[-1]["outcome"] == "CONSERVATIVE_FAILED_CALL"


def test_luna_10k_tpm_limiter_is_shared_across_task_boundaries() -> None:
    from tau2_luna_local.terra_smoke import (
        LUNA_TOKENS_PER_MINUTE,
        TERRA_TOKENS_PER_MINUTE,
        LunaModelCallBudget,
        LunaPanelRateLimiter,
    )

    assert TERRA_TOKENS_PER_MINUTE == 100_000
    assert LUNA_TOKENS_PER_MINUTE == 10_000
    now = 100.0
    sleeps: list[float] = []
    egress: list[tuple[int, float]] = []

    def monotonic() -> float:
        return now

    def sleeper(seconds: float) -> None:
        nonlocal now
        sleeps.append(seconds)
        now += seconds

    limiter = LunaPanelRateLimiter(monotonic=monotonic, sleeper=sleeper)
    first = LunaModelCallBudget(task_id=83, rate_limiter=limiter)
    second = LunaModelCallBudget(task_id=113, rate_limiter=limiter)

    def provider(task_id: int, **_: Any) -> dict[str, Any]:
        egress.append((task_id, now))
        return {"usage": {"prompt_tokens": 0, "completion_tokens": 1}}

    first.call(
        provider,
        83,
        input_token_reservation=0,
        max_completion_tokens=1_000,
    )
    second.call(
        provider,
        113,
        input_token_reservation=0,
        max_completion_tokens=1_000,
    )

    assert sleeps == [6.0]
    assert egress == [(83, 100.0), (113, 106.0)]


@pytest.mark.parametrize("benchmark_fails", [False, True])
def test_runner_scopes_luna_to_nl_assertions_and_restores_upstream_globals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    benchmark_fails: bool,
) -> None:
    from tau2_luna_local import runner
    from tau2_luna_local.config import Config

    provider_calls: list[dict[str, Any]] = []

    class ProviderResponse(dict[str, Any]):
        def __init__(self) -> None:
            super().__init__(
                id="provider-response",
                choices=[{"finish_reason": "stop", "message": {"content": "ok"}}],
                usage={"prompt_tokens": 10, "completion_tokens": 5},
            )
            self._hidden_params = {"response_cost": 0.001}
            self._response_headers = {"x-request-id": "provider-request"}

    llm_utils = SimpleNamespace(
        completion=lambda **kwargs: provider_calls.append(dict(kwargs)) or ProviderResponse()
    )

    def agent_step(model: str, args: dict[str, Any]) -> None:
        llm_utils.completion(model=model, messages=[], **args)

    def user_step(model: str, args: dict[str, Any]) -> None:
        llm_utils.completion(model=model, messages=[], **args)

    evaluator_boundary = SimpleNamespace(
        __name__="fake_tau2.evaluator_nl_assertions",
        DEFAULT_LLM_NL_ASSERTIONS="gpt-4o-mini",
        DEFAULT_LLM_NL_ASSERTIONS_ARGS={"temperature": 0.7},
    )

    def evaluator_step() -> None:
        llm_utils.completion(
            model=evaluator_boundary.DEFAULT_LLM_NL_ASSERTIONS,
            messages=[],
            **evaluator_boundary.DEFAULT_LLM_NL_ASSERTIONS_ARGS,
        )

    evaluator_boundary.step = evaluator_step
    agent_boundary = SimpleNamespace(__name__="fake_tau2.agent", step=agent_step)
    user_boundary = SimpleNamespace(__name__="fake_tau2.user", step=user_step)

    class FakeResults:
        def model_dump(self, *, mode: str) -> dict[str, Any]:
            assert mode == "json"
            return {"tasks": [], "reward": None}

    def run_tasks(**kwargs: Any) -> FakeResults:
        assert kwargs["llm_agent"] == TERRA_MODEL
        assert kwargs["llm_user"] == TERRA_MODEL
        agent_boundary.step(kwargs["llm_agent"], kwargs["llm_args_agent"])
        user_boundary.step(kwargs["llm_user"], kwargs["llm_args_user"])
        assert evaluator_boundary.DEFAULT_LLM_NL_ASSERTIONS == LUNA_MODEL
        assert evaluator_boundary.DEFAULT_LLM_NL_ASSERTIONS_ARGS == {
            "api_base": LUNA_BASE,
            "api_version": API_VERSION,
            "api_key": "luna-secret",
            "caching": False,
            "num_retries": 0,
        }
        evaluator_boundary.step()
        if benchmark_fails:
            raise RuntimeError("synthetic benchmark failure")
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
        lambda: {
            "agent": agent_boundary,
            "user": user_boundary,
            "evaluator": evaluator_boundary,
        },
    )
    monkeypatch.setattr(
        runner,
        "verify_tau2_distribution",
        lambda: {"distribution_version": "fake", "commit": "frozen", "url": "frozen"},
    )
    monkeypatch.setattr(runner, "verify_bundle", lambda *_args, **_kwargs: {"valid": True})

    config = Config(
        api_key="terra-secret",
        api_base="https://terra.openai.azure.com/",
        api_version=API_VERSION,
        deployment="gpt-5-6-terra-sentinel",
        trace_root=tmp_path,
        task_id="83",
    )
    luna_config = {
        "model": LUNA_MODEL,
        "api_base": LUNA_BASE,
        "api_version": API_VERSION,
        "api_key": "luna-secret",
    }

    if benchmark_fails:
        with pytest.raises(runner.RunRefused, match="benchmark failed"):
            runner.run_experiment(
                config,
                run_id="mixed-failure",
                nl_assertions_config=luna_config,
            )
        run_dir = tmp_path / "mixed-failure"
    else:
        run_dir = runner.run_experiment(
            config,
            run_id="mixed-success",
            nl_assertions_config=luna_config,
        )

    assert evaluator_boundary.DEFAULT_LLM_NL_ASSERTIONS == "gpt-4o-mini"
    assert evaluator_boundary.DEFAULT_LLM_NL_ASSERTIONS_ARGS == {"temperature": 0.7}
    assert [call["model"] for call in provider_calls] == [TERRA_MODEL, TERRA_MODEL, LUNA_MODEL]
    assert all(call.get("num_retries") == 0 and call.get("caching") is False for call in provider_calls)
    assert "gpt-4o-mini" not in json.dumps(provider_calls)
    events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text().splitlines()]
    requests = [event["payload"] for event in events if event["event_name"] == "model.request"]
    assert [request["role_lane"] for request in requests] == ["agent", "user", "evaluator"]
    assert [request["model"] for request in requests] == [TERRA_MODEL, TERRA_MODEL, LUNA_MODEL]
    assert "luna-secret" not in "".join(
        path.read_text(errors="replace") for path in run_dir.iterdir() if path.is_file()
    )
