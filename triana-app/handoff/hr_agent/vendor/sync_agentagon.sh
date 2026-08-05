#!/usr/bin/env bash
# Copies the agentagon packages `run_gate.py` needs into `vendor/agentagon/`, from a
# local agentagon checkout. Run this ONCE, on your machine, before you push this
# `hr_agent` branch -- the copied tree is what makes the Action self-contained (no
# private repo, no deploy token, no network fetch at CI time).
#
# We deliberately do NOT commit a real vendored tree in this handoff -- copying
# hundreds of files (including transitive deps like agentagon.exploration_v1.llm,
# agentagon.evals.trace_bundle, ...) here would bloat a demo repo with agentagon's own
# source. This script + this comment is the actual deliverable: it documents exactly
# what to copy and lets you regenerate vendor/agentagon/ any time agentagon changes.
#
# Usage:
#   AGENTAGON_SRC=/path/to/agentagon vendor/sync_agentagon.sh
# Defaults to ../../agentagon relative to this script if AGENTAGON_SRC is unset --
# adjust to wherever your agentagon checkout actually lives.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${AGENTAGON_SRC:-$SCRIPT_DIR/../../../agentagon}"
DEST="$SCRIPT_DIR/agentagon"

if [ ! -d "$SRC/agentagon" ]; then
  echo "error: no agentagon package found at $SRC/agentagon" >&2
  echo "       set AGENTAGON_SRC to your local agentagon checkout" >&2
  exit 1
fi

# Packages run_gate.py imports, directly or transitively (import chain: gate.py ->
# measurement_promotion.* -> evals.* ; behavioral_evals/__init__.py -> pipeline.py ->
# exploration_v1.llm for CachedLiteLLMModel, imported even though this Action only ever
# exercises the FrozenLabelModel path).
PACKAGES=(
  behavioral_evals
  measurement_promotion
  evals
  exploration_v1
  goal_observables
  core
)

rm -rf "$DEST"
mkdir -p "$DEST"
# agentagon/agentagon has no top-level __init__.py (implicit namespace package) --
# vendor/agentagon works the same way, so nothing to copy at this level.

for pkg in "${PACKAGES[@]}"; do
  echo "vendoring agentagon/$pkg"
  rsync -a --exclude '__pycache__' --exclude '*.pyc' "$SRC/agentagon/$pkg/" "$DEST/$pkg/"
done

echo
echo "vendored into $DEST"
echo "next: pip install -r ../requirements.txt, then verify with:"
echo "  python3 -c 'import sys; sys.path.insert(0, \"$SCRIPT_DIR\"); from agentagon.behavioral_evals.gate import run_release_gate'"
