# Trace-to-Eval Review V0 local runbook

This runbook starts the local-only Trace-to-Eval product loop. It does not
deploy, provision infrastructure, open ingress, configure authentication, or
silently substitute a provider. Customer evidence remains on the operator's
machine except when the manifest explicitly authorizes the one pinned semantic
provider. Calibration and holdout conversation bodies are not persisted in the
viewer artifact.

## Start the product

Terminal 1:

```bash
cd /path/to/triana/triana-backend
TRIANA_TRACE_TO_EVAL_LOCAL=1 \
TRIANA_TRACE_TO_EVAL_ROOT=/private/tmp/triana-trace-to-eval-local \
UV_CACHE_DIR=/private/tmp/triana-uv-cache \
uv run python -m triana_backend.main
```

The local entrypoint binds only to `127.0.0.1:8000`. Without an authorized
semantic-provider environment it still completes deterministic ingestion and
publishes `SEMANTIC_ANALYSIS_UNAVAILABLE`. Remote persistence is deliberately
reported as `REMOTE_PERSISTENCE_UNAVAILABLE` in this tranche.

Terminal 2:

```bash
cd /path/to/triana/triana-app
TRIANA_BACKEND_API_ORIGIN=http://127.0.0.1:8000 npm run dev
```

Open <http://127.0.0.1:3000/analysis>. Select the exact source kind, enter an
authorized local path, and run analysis. The page shows the canonical report,
bounded review queue, and DEVELOPMENT evidence through the existing
`ConversationViewer`. Track/Edit/Defer rulings append to the report ledger and
survive reload.

## Run the same engine from the CLI

```bash
cd /path/to/triana/triana-labs
UV_CACHE_DIR=/private/tmp/triana-uv-cache \
uv run --locked triana analysis run /authorized/path/to/traces.jsonl \
  --source-kind langsmith-grouped-jsonl \
  --out /private/tmp/my-trace-analysis

UV_CACHE_DIR=/private/tmp/triana-uv-cache \
uv run --locked triana analysis report /private/tmp/my-trace-analysis
```

Other accepted source kinds are printed by `triana analysis run --help` and
include canonical manifests, PreviewTrace JSONL, normalized HRAI traces, TAU
PreviewTrace JSONL, and a TAU archive. A ruling is an explicit JSON object whose
`report_id`, `item_id`, and `item_hash` come from the persisted review queue:

```bash
UV_CACHE_DIR=/private/tmp/triana-uv-cache \
uv run --locked triana analysis review /private/tmp/my-trace-analysis \
  --ruling /authorized/path/to/ruling.json
```

## Expected artifacts

Every completed local run contains:

- `trace_to_eval_report.json` — canonical accounting, capabilities, behavior,
  semantic proposals when available, stability, gaps, and ruling state;
- `review_queue.json` — deterministic bounded blind review items;
- `human_rulings.jsonl` — append-only, identity-checked rulings after review;
- `conversations.json` — DEVELOPMENT-only evidence for the conversation viewer;
- `prepared/evidence_bundle_manifest.json` and `prepared/preview_traces.jsonl`
  when a direct source adapter was used.

Semantic populations and at most three eval candidates appear only when the
pinned provider returns schema-valid, cited, DEVELOPMENT-grounded output in
three fixed runs. Failure never falls back: the deterministic report remains
available and records a typed semantic gap.

## Morning smoke checklist

1. Confirm both processes listen only on `127.0.0.1` and open `/analysis`.
2. Run a small authorized source path; reconcile physical, accepted, and
   rejected counts with the source.
3. Confirm DEVELOPMENT, CALIBRATION, and HOLDOUT groups do not split and only
   DEVELOPMENT bodies open in `ConversationViewer`.
4. If semantics are enabled, inspect every population/eval citation, the three
   run stability state, provider identity, attempted/successful calls, and
   reserved cost before accepting any proposal.
5. Track, edit, or defer one review item; refresh and confirm the ruling remains.
6. Download/reload the report and confirm the same `report_id` is shown by CLI,
   backend, and UI.
7. Treat every `UNAVAILABLE` or `PARTIAL` gap as a gap—not as zero, pass, or
   evidence that the capability ran.

