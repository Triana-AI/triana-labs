# Tau-squared Azure trace experiments

This isolated package supports a one-task local trace proof, the historical
ten-task mixed-model smoke, and the completed 57-task Retail Discovery
baseline. All executions pin tau-squared `v0.2.0` at commit
`f8de30c298689cbe0117d76a378e7315a17e5bd8`. There is no configured Langfuse,
LangSmith, collector, remote exporter, cache, retry, or provider fallback.

The recorder captures Azure/LiteLLM requests and responses, tool schemas and
calls, returned reasoning summaries, token details, costs and headers when
exposed, tau-squared messages/results/rewards, and linked OpenTelemetry spans.
Azure-private chain-of-thought is not available through the API and is recorded
as `NOT_RETURNED`; this project never reconstructs or claims to capture it.

## Completed 57-task Retail Discovery baseline

The terminal experiment report is
[`EXPERIMENT_REPORT_2026-08-06.md`](EXPERIMENT_REPORT_2026-08-06.md). Its
artifact-derived headline result is 39 exact rewards of 1.0 from 57 completed
tasks, or 68.42%, on the frozen Discovery half of the Retail task set. This is
an unchanged-harness baseline for failure analysis, not a leaderboard result,
full-dataset score, model comparison, or harness-improvement claim.

The final run used Azure GPT-5.6 Terra for the benchmark agent and simulated
user. GPT-5.6 Luna was configured exclusively for natural-language assertion
judging, but none of the 57 selected tasks contained NL assertions, so no Luna
model call occurred. The terminal ledger closed at USD 9.559619 under the
owner-approved USD 25 aggregate ceiling.

Execution was detached on a private Azure VM. Raw events and spans were
appended synchronously to Blob, completed tasks received remotely verified
checkpoints, and terminal execution published a content-addressed archive. The
worker exited successfully; the VM and VM-local raw directory were retained by
owner request. The archive itself stays gitignored and is not part of this
repository.

## Install

Python 3.11 through 3.13 and `uv` are required. The lock pins tau-squared by Git
commit and pins the local OpenTelemetry SDK.

```bash
uv sync --project triana-experiments/tau2-luna-local --extra dev
```

## Configure and run

Set the values explicitly in the shell that will own the paid run. Do not put
the API key in a file or command history.

```bash
export AZURE_API_KEY='<operator secret>'
export AZURE_API_BASE='https://<resource>.openai.azure.com'
export AZURE_API_VERSION='<explicit supported API version>'
export TAU2_LUNA_DEPLOYMENT='<Azure deployment name>'
export TAU2_TRACE_ROOT='./triana-experiments/tau2-luna-local/runs'

uv run --project triana-experiments/tau2-luna-local tau2-luna-local run \
  --domain retail --task-id '<exact tau2 task id>' --seed 1729
```

The command refuses before model egress unless all provider values are explicit,
the endpoint is HTTPS and Azure-owned, the installed tau-squared PEP 610 record
proves the frozen commit, the destination is new, concurrency is one, and retry
count remains zero. No automated acceptance test calls Azure.

## Evidence bundle

Every successful run directory contains exactly:

- `events.jsonl`: canonical, sequence-linked, domain-separated event hashes;
- `spans.jsonl`: locally exported OpenTelemetry `ReadableSpan` projections;
- `tau2-results.json`: the tau-squared `Results` payload;
- `manifest.json`: safe config/upstream identity and artifact sizes/hashes;
- `completeness.json`: every registry field classified as `CAPTURED`,
  `NOT_RETURNED`, `UNAVAILABLE`, or `INVALID`.

Provider or benchmark failure retains partial evidence and exits non-zero.
Missing usage, cost, headers, a model terminal, a benchmark result, a hash match,
or a telemetry classification cannot become a valid bundle.

```bash
uv run --project triana-experiments/tau2-luna-local \
  tau2-luna-local verify ./triana-experiments/tau2-luna-local/runs/<run-id>
```

The verifier checks the configured key for exact reflection when it remains in
`AZURE_API_KEY`. Keep that environment available for the first verification.
Recursive redaction also removes secret-bearing fields before persistence.

## No-network smoke and development gates

```bash
uv run --directory triana-experiments/tau2-luna-local python scripts/synthetic_smoke.py
uv run --directory triana-experiments/tau2-luna-local pytest -q
uv run --directory triana-experiments/tau2-luna-local ruff check .
uv run --directory triana-experiments/tau2-luna-local mypy src
```

The synthetic smoke uses a fake LiteLLM-compatible completion and a temporary
directory. It exercises real local OTel export, event custody, manifest hashing,
secret redaction, and deterministic verification without credentials or network.

## Authorized Azure resumable smoke

The `infra/main.bicep` envelope creates a private Blob container, Key Vault,
managed-identity VM with no public IP or inbound rule, and scoped operator/VM
Key Vault access policies. A short-lived Standard NAT Gateway provides outbound-only package,
Azure API, and benchmark access; it does not expose the VM for inbound traffic.
Blob anonymous access remains disabled and the container is private. Shared Key
is enabled only on the disposable experiment Storage account; its dedicated key
and the distinct Terra and Luna Azure OpenAI keys are placed in Key Vault
through private files. The VM
and local relay retrieve the Storage key without placing either key in Run
Command parameters, deployment outputs, or evidence artifacts.

The operator workflow is `scripts/azure_deploy.sh`, `scripts/azure_run.sh`, then
`scripts/azure_relay.sh`. Required nonsecret environment names are declared at
the top of each script. Deploy pins `gpt-5.6-luna` version `2026-07-09` on
`GlobalStandard`, uploads a hashed source archive, and places the existing
`kairos-memory` key into Key Vault without printing it. `TAU2_DEPLOY_OUTPUT`
must name a new private local JSON file for nonsecret deployment outputs.
`TAU2_VM_SIZE` must be set to the one exact Azure VM size selected by the
operator; deployment performs no size discovery or fallback and records that
value in its nonsecret outputs. The pinned Azure Blob SDK seeds the two source
objects immutably from private local files and verifies their names and sizes by
listing the commit-scoped prefix; the Storage key remains file-backed throughout.
Run Command passes only
nonsecret parameters. The VM resolves credentials with managed identity,
checks out the exact tau-squared commit, verifies 114 retail tasks, reserves at
most six calls/$3, writes every event/span line synchronously to Blob, publishes
versioned resume checkpoints and a relay inventory, and is synchronously
deallocated after either exit path. Interrupted conversations restart as a new
immutable attempt; verified completed attempts are skipped.

The relay command creates a new private local directory, requires an exact
remote inventory and matching hashes, scans for the configured key when it is
available locally, and reruns deterministic bundle verification. These scripts
must not be run until the endpoint, task ID, deployment name, resource names,
and USD 5 ceiling have been confirmed by the operator.

## Authorized mixed Terra/Luna ten-task trace smoke

The Terra entrypoint reuses the private Azure envelope but requires
`TAU2_LUNA_DEPLOYMENT=gpt-5-6-terra-sentinel` (the environment name is retained
for compatibility). It refuses any other deployment and the operator check
requires exact `gpt-5.6-terra` version `2026-07-09` on `GlobalStandard`. The
deployment and preflight both preserve capacity 100 (100K TPM). The ordered
panel is fixed to `83, 113, 5, 52, 64, 58, 21, 85, 7, 23`, one trial and seed
1729; there is no task-ID control-plane input. NL assertions use only
`azure/tau2-luna-smoke-20260805` on `kairos-memory`, exact version `2026-07-09`,
`GlobalStandard` capacity 10, and a separately custodied key. The runner
temporarily overrides and always restores the pinned evaluator globals so the
upstream GPT-4-family default cannot egress.

`TAU2_AUTO_SHUTDOWN_UTC_HHMM` is mandatory. The launcher validates that UTC
HHMM value before any Azure call, configures auto-shutdown before starting the
VM, submits exactly one Run Command for the whole panel, and deallocates after
both completed and typed-partial outcomes. The experiment therefore does not
depend on the operator laptop remaining online after submission.

Each task has non-borrowable USD 0.90 Terra and USD 0.06 Luna budgets. Calls
reserve worst-case input and output cost before egress, debit returned usage at
USD 2.50/M input and USD 15/M output for Terra or USD 1/M input and USD 6/M
output for Luna, and conservatively debit the applicable reservation on missing
usage or failure. Separate panel clocks pace Terra at 100K TPM and Luna at 10K
TPM; output ceilings are 8,192 and 2,048 tokens respectively. A refusal stops
the ordered panel with partial evidence; there is no replacement, retry,
fallback, or favorable rerun. Corrected source custody uses immutable prefix
`source/f8de30c298689cbe0117d76a378e7315a17e5bd8/terra-10-v2/` and new v2
archive/digest names without overwriting the prior v1 partial source.

The panel relay accepts only the run ID, a new private destination, and Blob
custody. It discovers exactly one content-addressed final panel report, then
verifies all ten ordered task checkpoints, task relays, exact inventories, and
bundles before preserving that report locally. It refuses missing or invalid
evidence and has no VM-control or attempt-selection input.

The final panel evidence keeps `TRIANA_CORE_IMPORT` and
`TRIANA_LABS_ANALYSIS` separate. Core import remains an unauthorized adapter
with explicit required-field gaps. Labs use is labeled third-party synthetic
benchmark evidence only; it is not a production trace, accepted behavior,
product passage, regression result, or score-improvement claim, and semantic
usefulness requires human judgment.
