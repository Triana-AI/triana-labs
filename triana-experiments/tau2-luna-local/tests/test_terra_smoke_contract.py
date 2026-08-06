from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

EXACT_TERRA_IDENTITY = {
    "model_name": "gpt-5.6-terra",
    "model_version": "2026-07-09",
    "sku": "GlobalStandard",
}
EXACT_TASK_PANEL = (83, 113, 5, 52, 64, 58, 21, 85, 7, 23)


def test_terra_identity_and_panel_are_exactly_frozen() -> None:
    from tau2_luna_local.terra_smoke import (
        TERRA_MODEL_IDENTITY,
        TERRA_TASK_PANEL,
        validate_terra_model_identity,
    )

    assert TERRA_MODEL_IDENTITY == EXACT_TERRA_IDENTITY
    assert TERRA_TASK_PANEL == EXACT_TASK_PANEL
    assert validate_terra_model_identity(dict(EXACT_TERRA_IDENTITY)) is None


@pytest.mark.parametrize(
    "identity",
    [
        {**EXACT_TERRA_IDENTITY, "model_name": "gpt-5.6-luna"},
        {**EXACT_TERRA_IDENTITY, "model_version": "2026-07-08"},
        {**EXACT_TERRA_IDENTITY, "sku": "Standard"},
        {**EXACT_TERRA_IDENTITY, "deployment": "gpt-5-6-terra-sentinel"},
        {"model_name": "gpt-5.6-terra", "model_version": "2026-07-09"},
    ],
)
def test_terra_identity_rejects_any_substitution_or_extra_field(
    identity: dict[str, str],
) -> None:
    from tau2_luna_local.terra_smoke import ModelIdentityError, validate_terra_model_identity

    with pytest.raises(ModelIdentityError, match=r"gpt-5\.6-terra|2026-07-09|GlobalStandard"):
        validate_terra_model_identity(identity)


def test_budget_debits_valid_returned_usage_at_terra_rates() -> None:
    from tau2_luna_local.terra_smoke import TerraModelCallBudget

    egress: list[dict[str, Any]] = []
    response = {
        "id": "response-1",
        "usage": {"prompt_tokens": 1_000, "completion_tokens": 2_000},
    }

    def provider(**kwargs: Any) -> dict[str, Any]:
        egress.append(kwargs)
        return response

    budget = TerraModelCallBudget(task_id=83)
    returned = budget.call(
        provider,
        input_token_reservation=20_000,
        max_completion_tokens=10_000,
        model="azure/gpt-5-6-terra-sentinel",
    )

    assert returned is response
    assert egress == [
        {
            "max_completion_tokens": 10_000,
            "model": "azure/gpt-5-6-terra-sentinel",
        }
    ]
    assert budget.charged_usd == Decimal("0.032500")
    assert budget.ledger == [
        {
            "outcome": "USAGE_DEBIT",
            "reserved_usd": Decimal("0.200000"),
            "charged_usd": Decimal("0.032500"),
            "prompt_tokens": 1_000,
            "completion_tokens": 2_000,
        }
    ]


@pytest.mark.parametrize(
    "response",
    [
        {"id": "missing-usage"},
        {"usage": None},
        {"usage": {"prompt_tokens": "1000", "completion_tokens": 2_000}},
        {"usage": {"prompt_tokens": -1, "completion_tokens": 2_000}},
        {"usage": {"prompt_tokens": 1_000}},
    ],
)
def test_missing_or_malformed_success_usage_charges_full_reservation(
    response: dict[str, Any],
) -> None:
    from tau2_luna_local.terra_smoke import TerraModelCallBudget

    budget = TerraModelCallBudget(task_id=83)

    assert (
        budget.call(
            lambda **_: response,
            input_token_reservation=20_000,
            max_completion_tokens=10_000,
        )
        is response
    )
    assert budget.charged_usd == Decimal("0.200000")
    assert budget.ledger[-1]["outcome"] == "CONSERVATIVE_MISSING_USAGE"


def test_failed_call_is_charged_conservatively_without_retry() -> None:
    from tau2_luna_local.terra_smoke import TerraModelCallBudget

    calls = 0

    class ProviderFailure(RuntimeError):
        pass

    def provider(**_: Any) -> None:
        nonlocal calls
        calls += 1
        raise ProviderFailure("synthetic provider failure")

    budget = TerraModelCallBudget(task_id=83)
    with pytest.raises(ProviderFailure, match="synthetic"):
        budget.call(
            provider,
            input_token_reservation=20_000,
            max_completion_tokens=10_000,
        )

    assert calls == 1
    assert budget.charged_usd == Decimal("0.200000")
    assert budget.ledger[-1]["outcome"] == "CONSERVATIVE_FAILED_CALL"


def test_next_worst_case_reservation_refuses_before_egress() -> None:
    from tau2_luna_local.terra_smoke import BudgetExhausted, TerraModelCallBudget

    egress = 0

    def provider(**_: Any) -> dict[str, Any]:
        nonlocal egress
        egress += 1
        return {"usage": {"prompt_tokens": 1_000, "completion_tokens": 2_000}}

    budget = TerraModelCallBudget(task_id=83, task_cap_usd=Decimal("0.25"))
    budget.call(
        provider,
        input_token_reservation=20_000,
        max_completion_tokens=10_000,
    )
    with pytest.raises(BudgetExhausted, match=r"before egress|reservation|cap"):
        budget.call(
            provider,
            input_token_reservation=28_000,
            max_completion_tokens=10_000,
        )

    assert egress == 1
    assert budget.charged_usd == Decimal("0.032500")


def test_exact_per_task_caps_preserve_aggregate_infrastructure_reservation() -> None:
    from tau2_luna_local.terra_smoke import LunaModelCallBudget, TerraModelCallBudget

    terra_budgets = [TerraModelCallBudget(task_id=task_id) for task_id in EXACT_TASK_PANEL]
    luna_budgets = [LunaModelCallBudget(task_id=task_id) for task_id in EXACT_TASK_PANEL]

    assert {budget.task_cap_usd for budget in terra_budgets} == {Decimal("0.90")}
    assert {budget.task_cap_usd for budget in luna_budgets} == {Decimal("0.06")}
    assert sum(
        (terra.task_cap_usd + luna.task_cap_usd)
        for terra, luna in zip(terra_budgets, luna_budgets, strict=True)
    ) == Decimal("9.60")
    with pytest.raises(ValueError, match=r"0\.90|per-task|cap"):
        TerraModelCallBudget(task_id=83, task_cap_usd=Decimal("0.91"))
    with pytest.raises(ValueError, match=r"0\.06|per-task|cap"):
        LunaModelCallBudget(task_id=83, task_cap_usd=Decimal("0.07"))
    with pytest.raises(ValueError, match=r"fixed|panel|task"):
        TerraModelCallBudget(task_id=999)


def test_calls_are_paced_from_worst_case_tokens_for_100k_tpm() -> None:
    from tau2_luna_local.terra_smoke import TerraModelCallBudget

    now = 100.0
    sleeps: list[float] = []
    egress_times: list[float] = []

    def monotonic() -> float:
        return now

    def sleeper(seconds: float) -> None:
        nonlocal now
        sleeps.append(seconds)
        now += seconds

    def provider(**_: Any) -> dict[str, Any]:
        egress_times.append(now)
        return {"usage": {"prompt_tokens": 1_000, "completion_tokens": 1_000}}

    budget = TerraModelCallBudget(task_id=83, monotonic=monotonic, sleeper=sleeper)
    for _ in range(2):
        budget.call(
            provider,
            input_token_reservation=15_000,
            max_completion_tokens=10_000,
        )

    assert sleeps == [15.0]
    assert egress_times == [100.0, 115.0]


def test_panel_pacing_survives_task_budget_boundary_and_429_has_no_retry() -> None:
    from tau2_luna_local.terra_smoke import TerraModelCallBudget, TerraPanelRateLimiter

    now = 100.0
    sleeps: list[float] = []
    invocations: list[tuple[int, float]] = []

    def monotonic() -> float:
        return now

    def sleeper(seconds: float) -> None:
        nonlocal now
        sleeps.append(seconds)
        now += seconds

    class Synthetic429(RuntimeError):
        pass

    limiter = TerraPanelRateLimiter(monotonic=monotonic, sleeper=sleeper)
    first_task = TerraModelCallBudget(task_id=83, rate_limiter=limiter)
    second_task = TerraModelCallBudget(task_id=113, rate_limiter=limiter)

    def first_provider(**_: Any) -> None:
        invocations.append((83, now))
        raise Synthetic429("synthetic 429")

    def second_provider(**_: Any) -> dict[str, Any]:
        invocations.append((113, now))
        return {"usage": {"prompt_tokens": 1_000, "completion_tokens": 1_000}}

    with pytest.raises(Synthetic429, match="429"):
        first_task.call(
            first_provider,
            input_token_reservation=15_000,
            max_completion_tokens=10_000,
        )
    second_task.call(
        second_provider,
        input_token_reservation=15_000,
        max_completion_tokens=10_000,
    )

    assert invocations == [(83, 100.0), (113, 115.0)]
    assert sleeps == [15.0]
    assert first_task.charged_usd == Decimal("0.187500")
    assert second_task.charged_usd == Decimal("0.017500")
    assert len(first_task.ledger) == len(second_task.ledger) == 1


def test_panel_runs_each_task_once_in_order_with_resumable_attempt_identity() -> None:
    from tau2_luna_local.terra_smoke import run_terra_panel

    invocations: list[dict[str, Any]] = []

    def resume(task_id: int, trial: int) -> dict[str, str]:
        assert trial == 0
        if task_id == 58:
            return {"action": "SKIP_VERIFIED_COMPLETED", "attempt_id": "58-old"}
        return {"action": "START_NEW_ATTEMPT", "attempt_id": f"{task_id}-attempt-1"}

    def execute(**invocation: Any) -> str:
        invocations.append(invocation)
        return "COMPLETED"

    report = run_terra_panel(resume=resume, execute=execute)

    assert [item["task_id"] for item in invocations] == [
        task_id for task_id in EXACT_TASK_PANEL if task_id != 58
    ]
    assert invocations[0] == {
        "task_id": 83,
        "trial": 0,
        "seed": 1729,
        "attempt_id": "83-attempt-1",
    }
    assert report["denominators"] == {
        "requested": 10,
        "completed": 9,
        "partial": 0,
        "invalid": 0,
        "skipped": 1,
    }
    assert report["records"][5] == {
        "task_id": 58,
        "state": "SKIPPED",
        "attempt_id": "58-old",
    }


@pytest.mark.parametrize("failure_name", ["budget", "infrastructure"])
def test_panel_stops_without_replacement_or_rerun_on_budget_or_infrastructure_failure(
    failure_name: str,
) -> None:
    from tau2_luna_local.terra_smoke import (
        BudgetExhausted,
        PanelInfrastructureFailure,
        run_terra_panel,
    )

    invocations: list[int] = []
    failure_type = BudgetExhausted if failure_name == "budget" else PanelInfrastructureFailure

    def execute(*, task_id: int, **_: Any) -> str:
        invocations.append(task_id)
        if task_id == 52:
            raise failure_type("synthetic stop")
        return "COMPLETED"

    report = run_terra_panel(
        resume=lambda task_id, trial: {
            "action": "START_NEW_ATTEMPT",
            "attempt_id": f"{task_id}-{trial}-only",
        },
        execute=execute,
    )

    assert invocations == [83, 113, 5, 52]
    assert report["stop"] == {
        "reason": failure_name.upper(),
        "task_id": 52,
        "attempt_id": "52-0-only",
    }
    assert report["denominators"] == {
        "requested": 10,
        "completed": 3,
        "partial": 1,
        "invalid": 0,
        "skipped": 0,
    }
