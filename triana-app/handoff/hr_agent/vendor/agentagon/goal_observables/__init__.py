# DEPRECATED — slated for deletion, replaced by behavioral-evals pipeline (see internal/DELETION_MANIFEST_behavioral_evals.md).
"""Goal-linked observable measurement discovery."""

from .pipeline import build_goal_observable_slate
from .report import render_goal_observable_html, render_goal_observable_markdown

__all__ = [
    "build_goal_observable_slate",
    "render_goal_observable_html",
    "render_goal_observable_markdown",
]
