from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest


def test_model_call_budget_paces_after_first_call_and_counts_failures_without_retry() -> None:
    from tau2_luna_local.cloud_smoke import ModelCallBudget

    now = 100.0
    sleeps: list[float] = []
    provider_invocations: list[tuple[str, float, int, Decimal]] = []

    def monotonic() -> float:
        return now

    def sleeper(seconds: float) -> None:
        nonlocal now
        assert seconds > 0
        sleeps.append(seconds)
        now += seconds

    class Provider429(RuntimeError):
        pass

    budget = ModelCallBudget(
        monotonic=monotonic,
        sleeper=sleeper,
        minimum_interval_seconds=30.0,
    )

    def provider(label: str, **_: Any) -> str:
        provider_invocations.append(
            (label, monotonic(), budget.admitted_calls, budget.reserved_usd)
        )
        if label == "failure":
            raise Provider429("synthetic Azure capacity response")
        return label

    assert budget.call(provider, "first") == "first"
    assert sleeps == []
    assert budget.call(provider, "second") == "second"
    with pytest.raises(Provider429, match="capacity"):
        budget.call(provider, "failure")
    assert budget.call(provider, "fourth-explicit-call") == "fourth-explicit-call"

    assert sleeps == [30.0, 30.0, 30.0]
    assert provider_invocations == [
        ("first", 100.0, 1, Decimal("0.50")),
        ("second", 130.0, 2, Decimal("1.00")),
        ("failure", 160.0, 3, Decimal("1.50")),
        ("fourth-explicit-call", 190.0, 4, Decimal("2.00")),
    ]
    assert budget.admitted_calls == 4
    assert budget.reserved_usd == Decimal("2.00")
