# Vendoring agentagon into hr_agent

`run_gate.py` imports from the `agentagon` package (`behavioral_evals.event_signals` for
the real `agent_looping_label` formula, plus the `evals`/`core` plumbing that formula and
the trace adapter depend on). Rather than depend on a private repo or a deploy token in
CI, we vendor the source directly into `vendor/agentagon/` so the Action is fully
self-contained.

`vendor/agentagon/` **is committed** in this handoff (~720KB) -- small enough that
committing it beats re-deriving it in CI, and it's what makes the Action runnable with
zero setup beyond `pip install -r requirements.txt`. `sync_agentagon.sh` is how to
regenerate it whenever agentagon's vendored packages change.

## Re-vendoring (only needed when agentagon changes)

```bash
cd handoff/hr_agent
AGENTAGON_SRC=/path/to/your/agentagon/checkout vendor/sync_agentagon.sh
git add vendor/agentagon
```

This copies `agentagon/{behavioral_evals,measurement_promotion,evals,exploration_v1,
goal_observables,core}` into `vendor/agentagon/`. Verified (2026-07-22) to produce an
importable tree with just `pip install -r requirements.txt` (litellm) in a bare venv --
no boto3, no fastapi, no opentelemetry, none of agentagon's other pyproject dependencies
are needed for the deterministic-only path this Action runs.

`measurement_promotion`, `exploration_v1`, and `goal_observables` are vendored even
though `run_gate.py` never calls into them directly -- they're pulled in transitively by
`agentagon/behavioral_evals/__init__.py` (a Python package import always runs its
`__init__.py`, and that module imports the judge-pipeline code alongside
`event_signals`). See `run_gate.py`'s module docstring for the exact import chain.

`run_gate.py` also imports `hr_ai_adapter_otel_v1.py`, a direct copy of agentagon's
`experiments/hr_ai_seed/adapter_otel_v1.py` (kept as a plain file in this directory, not
routed through `sync_agentagon.sh`, because it lives in agentagon's `experiments/` tree
rather than its installable package -- a re-run of the sync script won't pick it up).

## Re-running later

Safe to re-run any time; it wipes and recreates `vendor/agentagon/` from whatever
`AGENTAGON_SRC` points at. Commit the result before pushing so CI has it.

## Verifying it worked

```bash
python3 -c "import sys; sys.path.insert(0, 'vendor'); from agentagon.behavioral_evals.event_signals import agent_looping_label; print('ok')"
```
