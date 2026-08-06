from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from decimal import Decimal
from typing import Any, TypeVar

T = TypeVar("T")

TERRA_MODEL_IDENTITY = {
    "model_name": "gpt-5.6-terra",
    "model_version": "2026-07-09",
    "sku": "GlobalStandard",
}
TERRA_DEPLOYMENT = "gpt-5-6-terra-sentinel"
TERRA_TASK_PANEL = (83, 113, 5, 52, 64, 58, 21, 85, 7, 23)
TERRA_INPUT_PRICE_PER_MILLION_USD = Decimal("2.50")
TERRA_OUTPUT_PRICE_PER_MILLION_USD = Decimal("15.00")
LUNA_INPUT_PRICE_PER_MILLION_USD = Decimal("1.00")
LUNA_OUTPUT_PRICE_PER_MILLION_USD = Decimal("6.00")
TERRA_TASK_CAP_USD = Decimal("0.90")
LUNA_TASK_CAP_USD = Decimal("0.06")
TERRA_TOKENS_PER_MINUTE = 100_000
LUNA_TOKENS_PER_MINUTE = 10_000
_MILLION = Decimal(1_000_000)
_USD_QUANTUM = Decimal("0.000001")


class ModelIdentityError(RuntimeError):
    pass


class BudgetExhausted(RuntimeError):
    pass


class PanelInfrastructureFailure(RuntimeError):
    pass


def validate_terra_model_identity(identity: Mapping[str, Any]) -> None:
    if dict(identity) != TERRA_MODEL_IDENTITY:
        raise ModelIdentityError("Azure deployment is not exact gpt-5.6-terra 2026-07-09 GlobalStandard")


def _cost_at_rates(
    prompt_tokens: int,
    completion_tokens: int,
    input_price: Decimal,
    output_price: Decimal,
) -> Decimal:
    value = (
        Decimal(prompt_tokens) * input_price
        + Decimal(completion_tokens) * output_price
    ) / _MILLION
    return value.quantize(_USD_QUANTUM)


def _cost(prompt_tokens: int, completion_tokens: int) -> Decimal:
    return _cost_at_rates(
        prompt_tokens,
        completion_tokens,
        TERRA_INPUT_PRICE_PER_MILLION_USD,
        TERRA_OUTPUT_PRICE_PER_MILLION_USD,
    )


def _usage(response: Any) -> tuple[int, int] | None:
    if isinstance(response, Mapping):
        projected: Any = response
    elif callable(getattr(response, "model_dump", None)):
        projected = response.model_dump()
    elif callable(getattr(response, "to_dict", None)):
        projected = response.to_dict()
    else:
        return None
    usage = projected.get("usage") if isinstance(projected, Mapping) else None
    if not isinstance(usage, Mapping):
        return None
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    valid_prompt = isinstance(prompt, int) and not isinstance(prompt, bool) and prompt >= 0
    valid_completion = isinstance(completion, int) and not isinstance(completion, bool) and completion >= 0
    if not valid_prompt or not valid_completion:
        return None
    assert isinstance(prompt, int) and isinstance(completion, int)
    return prompt, completion


def terra_response_cost_fallback(response: Any) -> tuple[str | None, dict[str, str]]:
    usage = _usage(response)
    if usage is None:
        return None, {"kind": "UNAVAILABLE_MALFORMED_OR_MISSING_USAGE"}
    return str(_cost(*usage)), {
        "kind": "CALCULATED_FROM_RETURNED_USAGE",
        "input_price_per_million_usd": str(TERRA_INPUT_PRICE_PER_MILLION_USD),
        "output_price_per_million_usd": str(TERRA_OUTPUT_PRICE_PER_MILLION_USD),
    }


def luna_response_cost_fallback(response: Any) -> tuple[str | None, dict[str, str]]:
    usage = _usage(response)
    if usage is None:
        return None, {"kind": "UNAVAILABLE_MALFORMED_OR_MISSING_USAGE"}
    cost = _cost_at_rates(
        *usage,
        LUNA_INPUT_PRICE_PER_MILLION_USD,
        LUNA_OUTPUT_PRICE_PER_MILLION_USD,
    )
    return str(cost), {
        "kind": "CALCULATED_FROM_RETURNED_USAGE",
        "input_price_per_million_usd": str(LUNA_INPUT_PRICE_PER_MILLION_USD),
        "output_price_per_million_usd": str(LUNA_OUTPUT_PRICE_PER_MILLION_USD),
    }


class _PanelRateLimiter:
    def __init__(
        self,
        *,
        tokens_per_minute: int,
        monotonic: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.tokens_per_minute = tokens_per_minute
        self.monotonic = monotonic
        self.sleeper = sleeper
        self._next_egress_at: float | None = None
        self._lock = threading.Lock()

    def admit(self, worst_case_tokens: int) -> None:
        with self._lock:
            now = self.monotonic()
            if self._next_egress_at is not None:
                remaining = self._next_egress_at - now
                while remaining > 0:
                    self.sleeper(remaining)
                    now = self.monotonic()
                    remaining = self._next_egress_at - now
            self._next_egress_at = now + worst_case_tokens * 60.0 / self.tokens_per_minute


class TerraPanelRateLimiter(_PanelRateLimiter):
    """One continuous 100K TPM clock shared by every Terra panel task."""

    def __init__(
        self,
        *,
        monotonic: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        super().__init__(
            tokens_per_minute=TERRA_TOKENS_PER_MINUTE,
            monotonic=monotonic,
            sleeper=sleeper,
        )


class LunaPanelRateLimiter(_PanelRateLimiter):
    """One continuous 10K TPM clock shared by every Luna panel task."""

    def __init__(
        self,
        *,
        monotonic: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        super().__init__(
            tokens_per_minute=LUNA_TOKENS_PER_MINUTE,
            monotonic=monotonic,
            sleeper=sleeper,
        )


class _ModelCallBudget:
    task_cap_limit: Decimal
    input_price: Decimal
    output_price: Decimal
    model_name: str
    limiter_type: Callable[..., _PanelRateLimiter]

    def __init__(
        self,
        *,
        task_id: int,
        task_cap_usd: Decimal | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
        rate_limiter: _PanelRateLimiter | None = None,
        study_budget: Any | None = None,
        allowed_task_ids: Sequence[int] = TERRA_TASK_PANEL,
    ) -> None:
        if task_id not in allowed_task_ids:
            raise ValueError("task_id must belong to the fixed panel")
        cap = self.task_cap_limit if task_cap_usd is None else task_cap_usd
        if cap <= 0 or cap > self.task_cap_limit:
            raise ValueError(
                f"{self.model_name} per-task cap cannot exceed fixed USD {self.task_cap_limit}"
            )
        self.task_id = task_id
        self.task_cap_usd = cap
        self.study_budget = study_budget
        self.rate_limiter = rate_limiter or self.limiter_type(
            monotonic=monotonic, sleeper=sleeper
        )
        self.charged_usd = Decimal("0.000000")
        self.ledger: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def call(
        self, provider: Callable[..., T], /, *args: Any, input_token_reservation: int,
        max_completion_tokens: int, **kwargs: Any,
    ) -> T:
        if (
            not isinstance(input_token_reservation, int)
            or isinstance(input_token_reservation, bool)
            or input_token_reservation < 0
            or not isinstance(max_completion_tokens, int)
            or isinstance(max_completion_tokens, bool)
            or max_completion_tokens <= 0
        ):
            raise BudgetExhausted("token reservation is malformed before egress")
        reserved = _cost_at_rates(
            input_token_reservation,
            max_completion_tokens,
            self.input_price,
            self.output_price,
        )
        with self._lock:
            if self.study_budget is None and self.charged_usd + reserved > self.task_cap_usd:
                raise BudgetExhausted("next worst-case reservation exceeds per-task cap before egress")

            def egress() -> T:
                self.rate_limiter.admit(input_token_reservation + max_completion_tokens)
                return provider(*args, max_completion_tokens=max_completion_tokens, **kwargs)

            try:
                if self.study_budget is None:
                    response = egress()
                else:
                    response = self.study_budget.call(
                        model=self.model_name.lower(), reserved_usd=reserved, provider=egress
                    )
            except Exception as exc:
                from .discovery import AggregateBudgetExhausted

                if isinstance(exc, AggregateBudgetExhausted):
                    raise
                self.charged_usd += reserved
                self.ledger.append({
                    "outcome": "CONSERVATIVE_FAILED_CALL",
                    "reserved_usd": reserved, "charged_usd": reserved,
                })
                raise
            except BaseException:
                self.charged_usd += reserved
                self.ledger.append({
                    "outcome": "CONSERVATIVE_FAILED_CALL",
                    "reserved_usd": reserved, "charged_usd": reserved,
                })
                raise
            usage = _usage(response)
            if usage is None:
                charged = reserved
                entry = {"outcome": "CONSERVATIVE_MISSING_USAGE", "reserved_usd": reserved,
                         "charged_usd": reserved}
            else:
                prompt_tokens, completion_tokens = usage
                charged = _cost_at_rates(
                    prompt_tokens,
                    completion_tokens,
                    self.input_price,
                    self.output_price,
                )
                entry = {
                    "outcome": "USAGE_DEBIT",
                    "reserved_usd": reserved,
                    "charged_usd": charged,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                }
            self.charged_usd += charged
            self.ledger.append(entry)
            return response


class TerraModelCallBudget(_ModelCallBudget):
    """Task-local Terra spend reservation, dynamic debit, and 100K TPM pacing."""

    task_cap_limit = TERRA_TASK_CAP_USD
    input_price = TERRA_INPUT_PRICE_PER_MILLION_USD
    output_price = TERRA_OUTPUT_PRICE_PER_MILLION_USD
    model_name = "Terra"
    limiter_type = TerraPanelRateLimiter


class LunaModelCallBudget(_ModelCallBudget):
    """Task-local Luna spend reservation, dynamic debit, and 10K TPM pacing."""

    task_cap_limit = LUNA_TASK_CAP_USD
    input_price = LUNA_INPUT_PRICE_PER_MILLION_USD
    output_price = LUNA_OUTPUT_PRICE_PER_MILLION_USD
    model_name = "Luna"
    limiter_type = LunaPanelRateLimiter


def _denominators(records: Iterable[Mapping[str, Any]], *, requested: int) -> dict[str, int]:
    counts = {"requested": requested, "completed": 0, "partial": 0, "invalid": 0, "skipped": 0}
    for record in records:
        state = str(record.get("state", "")).lower()
        if state in counts and state != "requested":
            counts[state] += 1
    return counts


def run_terra_panel(
    *,
    resume: Callable[[int, int], Mapping[str, str]],
    execute: Callable[..., str | Mapping[str, Any]],
    task_ids: Sequence[int] = TERRA_TASK_PANEL,
) -> dict[str, Any]:
    if tuple(task_ids) != TERRA_TASK_PANEL:
        raise ValueError("Terra panel order must match the frozen task panel")
    records: list[dict[str, Any]] = []
    report: dict[str, Any] = {"records": records}
    for task_id in task_ids:
        decision = resume(task_id, 0)
        attempt_id = decision.get("attempt_id")
        if not isinstance(attempt_id, str) or not attempt_id:
            raise PanelInfrastructureFailure("resume returned no attempt identity")
        if decision.get("action") == "SKIP_VERIFIED_COMPLETED":
            records.append({"task_id": task_id, "state": "SKIPPED", "attempt_id": attempt_id})
            continue
        if decision.get("action") != "START_NEW_ATTEMPT":
            raise PanelInfrastructureFailure("resume returned an invalid action")
        invocation = {"task_id": task_id, "trial": 0, "seed": 1729, "attempt_id": attempt_id}
        try:
            outcome = execute(**invocation)
        except (BudgetExhausted, PanelInfrastructureFailure) as exc:
            records.append({**invocation, "state": "PARTIAL"})
            reason = "BUDGET" if isinstance(exc, BudgetExhausted) else "INFRASTRUCTURE"
            report["stop"] = {"reason": reason, "task_id": task_id, "attempt_id": attempt_id}
            break
        if isinstance(outcome, Mapping):
            record = {**invocation, **outcome}
        else:
            record = {**invocation, "state": outcome}
        if record.get("state") not in {"COMPLETED", "PARTIAL", "INVALID"}:
            raise PanelInfrastructureFailure("task execution returned an invalid state")
        records.append(record)
    report["denominators"] = _denominators(records, requested=len(task_ids))
    return report


def audit_trace_suitability(
    *,
    records: Sequence[Mapping[str, Any]],
    normalized_trace_required_fields: Sequence[str],
    normalized_trace_observed_fields: Sequence[str],
) -> dict[str, Any]:
    observed = set(normalized_trace_observed_fields)
    missing = [field for field in normalized_trace_required_fields if field not in observed]
    return {
        "denominators": _denominators(records, requested=len(records)),
        "TRIANA_CORE_IMPORT": {
            "classification": "GAP" if missing else "FIELDS_OBSERVED_ADAPTER_NOT_AUTHORIZED",
            "adapter_authorized": False,
            "missing_required_fields": missing,
        },
        "TRIANA_LABS_ANALYSIS": {
            "classification": "LABELED_THIRD_PARTY_SYNTHETIC_BENCHMARK_EVIDENCE",
            "verifier_valid_completed_bundles": sum(
                record.get("state") == "COMPLETED" and record.get("bundle_valid") is True
                for record in records
            ),
            "prohibited_claims": ["PRODUCTION_TRACE", "ACCEPTED_BEHAVIOR", "PRODUCT_PASSAGE",
                                  "REGRESSION_EVIDENCE", "SCORE_IMPROVEMENT"],
            "human_semantic_judgment_required": True,
        },
    }
