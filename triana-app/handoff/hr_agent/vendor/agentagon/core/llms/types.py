"""LLM model metadata types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LLMModelInfo:
    model: str
    provider: str | None = None
    context_window_tokens: int | None = None
    max_output_tokens: int | None = None
    input_price_per_million_tokens: float | None = None
    output_price_per_million_tokens: float | None = None
    input_price_per_million_tokens_long_context: float | None = None
    output_price_per_million_tokens_long_context: float | None = None
    long_context_threshold_tokens: int | None = None
    currency: str = "USD"
    pricing_notes: str | None = None


__all__ = ["LLMModelInfo"]
