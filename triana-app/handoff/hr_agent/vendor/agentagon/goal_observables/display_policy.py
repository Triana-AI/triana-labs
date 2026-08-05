# DEPRECATED — slated for deletion, replaced by behavioral-evals pipeline (see internal/DELETION_MANIFEST_behavioral_evals.md).
"""Deterministic display policy for goal-observable measurement cards.

Judge results routinely leave a large share of traces ``unknown`` (ABSTAIN,
dropped batch entries, missing evidence). Displaying a point rate computed
only over the answered minority — while burying the unknown count in a
footnote — lets a card claim "never" or "always" on numbers that flip the
moment the unknowns get filled in. Every function here is pure (no I/O, no
model calls) and exists to make that unknown mass impossible to ignore.
"""

from __future__ import annotations

import math
from typing import Any


EXISTENCE_EVALUABLE_THRESHOLD = 10
TRACKABLE_EVALUABLE_THRESHOLD = 30


def unknown_inclusive_bounds(
    distribution: dict[str, int], evaluable: int, unknown: int
) -> dict[str, dict[str, Any]]:
    """Per-label share bounds if every unknown were resolved for or against it.

    ``min_share`` assumes none of the unknowns land on this label; ``max_share``
    assumes all of them do. ``point_rate`` is the share among evaluable traces
    only (``None`` when there is nothing evaluable to divide by).
    """
    total = evaluable + unknown
    bounds: dict[str, dict[str, Any]] = {}
    for label, count in distribution.items():
        bounds[label] = {
            "count": count,
            "point_rate": (count / evaluable) if evaluable else None,
            "min_share": (count / total) if total else 0.0,
            "max_share": ((count + unknown) / total) if total else 0.0,
        }
    return bounds


def _leading_label(distribution: dict[str, int]) -> tuple[str | None, int]:
    if not distribution:
        return None, 0
    label, count = sorted(distribution.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return label, count


def display_mode(
    distribution: dict[str, int],
    evaluable: int,
    unknown: int,
    *,
    existence_threshold: int = EXISTENCE_EVALUABLE_THRESHOLD,
) -> str:
    """Decide how a card is allowed to present its numbers.

    - ``EXISTENCE``: too few evaluable traces (< existence_threshold) for a
      share to mean anything; show raw observation counts only.
    - ``RANGE``: the leading label could lose its lead if every unknown were
      resolved against it (in favor of its strongest competitor); show the
      unknown-inclusive range instead of a point rate.
    - ``RATE``: the leading label stays leading under that worst case; a bare
      percentage may be shown (still alongside its unknown count).
    """
    if not distribution or evaluable < existence_threshold:
        return "EXISTENCE"
    leading_label, leading_count = _leading_label(distribution)
    for label, count in distribution.items():
        if label == leading_label:
            continue
        worst_case_competitor = count + unknown
        if worst_case_competitor >= leading_count:
            return "RANGE"
    return "RATE"


def tracking_role(evaluable: int, *, threshold: int = TRACKABLE_EVALUABLE_THRESHOLD) -> str:
    """TRACKABLE cards have enough evaluable traces to track release-to-release;
    everything below the threshold is a one-off FINDING, independent of qualification."""
    return "TRACKABLE" if evaluable >= threshold else "FINDING"


def min_detectable_change(distribution: dict[str, int], evaluable: int) -> int | None:
    """Smallest rate movement (whole percentage points) worth believing on a
    TRACKABLE card, using the normal approximation to a binomial proportion's
    margin of error at ~95% confidence for the leading label:

        MDC ~= 1.96 * sqrt(2 * p * (1 - p) / n)

    This is a rough approximation, not a rigorous power calculation (no stated
    alternate hypothesis, no multiple-comparison correction) — it is meant as
    a directional floor so small wiggles in a rate aren't read as a trend.
    Floored at 1/n (one trace's worth of movement) and rounded up to a whole
    percentage point, minimum 1.
    """
    if evaluable <= 0:
        return None
    leading_label, leading_count = _leading_label(distribution)
    if leading_label is None:
        return None
    p = leading_count / evaluable
    raw = 1.96 * math.sqrt(2 * p * (1 - p) / evaluable)
    floor = 1 / evaluable
    return max(1, math.ceil(max(raw, floor) * 100))


def card_copy_rules(
    distribution: dict[str, int],
    evaluable: int,
    unknown: int,
    mode: str,
    bounds: dict[str, dict[str, Any]],
) -> dict[str, str]:
    """Deterministic per-label phrasing for the given display mode.

    Hard rule: a zero-count label with unknown > 0 is never phrased as
    "never" / "0%" (it hasn't been ruled out — it just hasn't been observed
    among the evaluable traces yet). A full-count label with unknown > 0 is
    never phrased as "always" / "100%" for the same reason.
    """
    total = evaluable + unknown
    phrases: dict[str, str] = {}
    for label, count in distribution.items():
        if mode == "EXISTENCE":
            times = "time" if count == 1 else "times"
            traces = "trace" if evaluable == 1 else "traces"
            phrases[label] = (
                f"{label}: observed {count} {times} in {evaluable} evaluable {traces} ({unknown} unknown)"
            )
        elif mode == "RANGE":
            entry = bounds.get(label, {"min_share": 0.0, "max_share": 0.0})
            lo = round(100 * entry["min_share"])
            hi = round(100 * entry["max_share"])
            phrases[label] = (
                f"{label}: somewhere between {lo}% and {hi}% "
                f"— {unknown} of {total} traces unknown"
            )
        else:  # RATE
            if count == 0 and unknown > 0:
                phrases[label] = f"{label}: not observed in {evaluable} evaluable traces ({unknown} unknown)"
            elif evaluable and count == evaluable and unknown > 0:
                phrases[label] = (
                    f"{label}: observed in all {evaluable} evaluable traces ({unknown} unknown)"
                )
            else:
                pct = round(100 * count / evaluable) if evaluable else 0
                suffix = f" ({unknown} unknown)" if unknown else ""
                phrases[label] = f"{label}: {pct}% ({count} of {evaluable} evaluable){suffix}"
    return phrases


def tracking_chip(role: str, mdc: int | None) -> str:
    """The FINDING / TRACKABLE chip text, with the smallest-believable-move
    annotation appended for TRACKABLE cards that have one."""
    if role == "TRACKABLE":
        return f"TRACKABLE · smallest believable move: ±{mdc} points" if mdc else "TRACKABLE"
    return "FINDING"


def compute_card_display(
    distribution: dict[str, int], evaluable: int, unknown: int
) -> dict[str, Any]:
    """Assemble the full ``display`` block attached to a card during candidate
    assembly: mode, bounds, tracking role, MDC (TRACKABLE only), and the
    per-label phrases the report renders."""
    bounds = unknown_inclusive_bounds(distribution, evaluable, unknown)
    mode = display_mode(distribution, evaluable, unknown)
    role = tracking_role(evaluable)
    mdc = min_detectable_change(distribution, evaluable) if role == "TRACKABLE" else None
    leading_label, _ = _leading_label(distribution)
    return {
        "mode": mode,
        "bounds": bounds,
        "tracking_role": role,
        "min_detectable_change": mdc,
        "leading_label": leading_label,
        "phrases": card_copy_rules(distribution, evaluable, unknown, mode, bounds),
        "chip": tracking_chip(role, mdc),
    }
