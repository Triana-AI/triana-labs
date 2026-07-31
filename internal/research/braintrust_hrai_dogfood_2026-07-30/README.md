# Reproduce the offline HRAI Braintrust dogfood

This directory evaluates immutable, synthetic HRAI model-change artifacts with
Braintrust's Python SDK in local-only mode. It does not upload traces, execute
HRAI, call an LLM, deploy anything, or change HRAI behavior.

Source repository and run:

- `/Users/akarshgajbhiye/Documents/hr_ai`
- HRAI source branch observed: `feat/agent-looping-dedup`
- Baseline run: Qwen3-235B, prompt
  `candidate-screening-v2-reliability`, `out/run_200`
- Candidate run: Qwen3-32B, the same agent/prompt/scenarios,
  `out/run_200_qwen32b_v1schema`
- Corpus: `scenarios_200.jsonl`

Create a disposable environment:

```sh
UV_CACHE_DIR=/private/tmp/triana-uv-cache \
  uv venv --python 3.13 /private/tmp/triana-bt-uv-venv
UV_CACHE_DIR=/private/tmp/triana-uv-cache \
  uv pip install --python /private/tmp/triana-bt-uv-venv/bin/python \
  'braintrust==0.31.0' 'autoevals==0.3.0'
```

Run the baseline and candidate:

```sh
HRAI=/Users/akarshgajbhiye/Documents/hr_ai
DOGFOOD=internal/research/braintrust_hrai_dogfood_2026-07-30
PY=/private/tmp/triana-bt-uv-venv/bin/python

"$PY" "$DOGFOOD/run_offline_braintrust_eval.py" \
  --scenarios "$HRAI/experiments/historical_traffic_v0/scenarios_200.jsonl" \
  --traces "$HRAI/experiments/historical_traffic_v0/out/run_200/normalized_traces.jsonl" \
  --manifest "$HRAI/experiments/historical_traffic_v0/out/run_200/RUN_MANIFEST.json" \
  --label baseline --trial-count 3 \
  --output "$DOGFOOD/artifacts/baseline.json"

"$PY" "$DOGFOOD/run_offline_braintrust_eval.py" \
  --scenarios "$HRAI/experiments/historical_traffic_v0/scenarios_200.jsonl" \
  --traces "$HRAI/experiments/historical_traffic_v0/out/run_200_qwen32b_v1schema/normalized_traces.jsonl" \
  --manifest "$HRAI/experiments/historical_traffic_v0/out/run_200_qwen32b_v1schema/RUN_MANIFEST.json" \
  --label candidate --trial-count 3 \
  --output "$DOGFOOD/artifacts/candidate.json"

"$PY" "$DOGFOOD/ci_gate.py" \
  --baseline "$DOGFOOD/artifacts/baseline.json" \
  --candidate "$DOGFOOD/artifacts/candidate.json" \
  --output "$DOGFOOD/artifacts/ci_gate.json"
```

The CI command is expected to exit `1` when the candidate crosses a required
regression threshold. The artifact is written before exit.

The bounded optional model-graded lane uses four synthetic security cases and
one judge pass per case:

```sh
set -a
source "$HRAI/.env"
set +a

"$PY" "$DOGFOOD/run_model_graded_scorer.py" \
  --scenarios "$HRAI/experiments/historical_traffic_v0/scenarios_200.jsonl" \
  --traces "$HRAI/experiments/historical_traffic_v0/out/run_200/normalized_traces.jsonl" \
  --label baseline \
  --output "$DOGFOOD/artifacts/baseline_model_judge.json"
```

Run the same command with the candidate trace path and label. The scorer uses
the OpenAI-compatible endpoint already configured by HRAI; it sends only
synthetic scenario text and assistant outputs. It is intentionally advisory:
one uncalibrated judge pass cannot create ground truth or authorize release.

Important limitation: `trial_count=3` verifies Braintrust's repeated-trial
execution and aggregation over a frozen replay. It produces zero within-run
variance and must not be cited as a live-model variance estimate. HRAI's two
independent Qwen3-235B runs measured the real A/A noise floor separately:
17 versus 23 committed decisions, approximately six decisions or seven
percentage points of eval-to-stop movement.
