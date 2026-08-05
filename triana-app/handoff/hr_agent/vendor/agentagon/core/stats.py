"""Small shared statistics helpers."""

from __future__ import annotations

from math import ceil


def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def nearest_rank_percentile(sorted_values: list[float], percentile: int) -> float:
    index = max(0, ceil((percentile / 100) * len(sorted_values)) - 1)
    return sorted_values[index]


__all__ = [
    "nearest_rank_percentile",
    "safe_ratio",
]
