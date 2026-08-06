# TAU-squared Retail Discovery baseline

- Date completed: 2026-08-06
- Status: **COMPLETED — 57/57 tasks archived**
- Study ID: `tau2-retail-discovery-v1`
Final run ID: `retail-discovery-20260805-003`

## Executive result

The frozen 57-task Retail Discovery panel completed with 39 rewards of 1.0 and
18 rewards of 0.0: an observed baseline score of **39/57 = 68.42%**. Every task
terminated normally with `user_stop`; there were no partial or missing task
results in the final run.

This establishes a reusable trace-rich baseline for diagnosing failures and
designing a later harness intervention. It does **not** establish a leaderboard
score, full-dataset performance, model superiority, a production-trace result,
accepted behavior, regression evidence, or improvement. The other frozen 57
Retail tasks remain holdout evidence and were not executed.

## Research question and study shape

The immediate question was whether Triana could collect enough observable
evidence from a realistic TAU-squared baseline to identify failure patterns and
support a later prompt, tool, or harness intervention without changing the
model during the comparison.

The executed arm was deliberately discovery-only:

| Field | Frozen value |
|---|---|
| Arm | `BASELINE_DISCOVERY` |
| Domain | `retail` |
| Trial | `0` |
| Seed | `1729` |
| Split | `sha256-balanced-retail-v1` |
| Panel | `tau2-retail-discovery-v1-seed-1729` |
| Upstream | tau-squared `v0.2.0`, commit `f8de30c298689cbe0117d76a378e7315a17e5bd8` |
| Concurrency | `1` |
| Provider retries | `0` |
| Cache / fallback | disabled / disabled |

Discovery task IDs:

```text
1,2,5,6,7,10,11,15,16,19,21,22,23,24,25,26,27,30,32,34,
37,38,39,40,46,52,53,54,56,58,61,64,65,68,71,75,80,81,
83,85,86,88,90,91,94,95,96,97,99,101,103,104,107,108,
109,112,113
```

The complementary 57-task holdout is frozen in `discovery.py` and was refused
by the Discovery runner. It should remain untouched until an intervention is
specified before looking at its outcomes.

## Model and evaluator identity

| Lane | Azure deployment identity | Observed use |
|---|---|---|
| Agent and simulated user | `gpt-5.6-terra`, version `2026-07-09`, `GlobalStandard`, deployment `gpt-5-6-terra-sentinel`, capacity 100 | 853 requests and 853 responses in the final run |
| NL assertion judge | `gpt-5.6-luna`, version `2026-07-09`, `GlobalStandard`, deployment `tau2-luna-smoke-20260805`, capacity 10 | Configured but not called; selected tasks contained zero NL assertions |

The absence of Luna calls is an observed property of this panel, not a missing
trace. All rewards were based on the task's DB and communication evidence.

## Benchmark outcome

| Metric | Observed value |
|---|---:|
| Requested / completed / partial | 57 / 57 / 0 |
| Reward 1.0 | 39 |
| Reward 0.0 | 18 |
| Mean reward | 0.6842105263 |
| Exact success rate | 68.42% |
| Total conversation messages | 1,309 |
| Messages per task | min 8, median 22, max 45 |
| Evaluated action checks | 276 |
| Termination | 57 `user_stop` |

Reward-zero task IDs:

```text
19,22,27,32,34,37,38,54,56,68,81,85,88,91,103,104,107,112
```

Failure-lane decomposition from `reward_breakdown`:

| DB | Communication | Tasks |
|---:|---:|---:|
| 0 | 1 | 13 |
| 1 | 0 | 3 |
| 0 | 0 | 2 |

This decomposition is a starting point for trace analysis, not an explanation
of root cause. A later analysis must inspect each transcript, tool sequence,
task policy, expected state transition, and evaluator evidence before proposing
an intervention.

## Trace coverage and verification

Each task retained the canonical five-file bundle:

- `events.jsonl`
- `spans.jsonl`
- `tau2-results.json`
- `manifest.json`
- `completeness.json`

Across the final archive:

| Evidence | Observed value |
|---|---:|
| Valid completeness declarations | 57/57 |
| Captured telemetry classifications | 2,622 |
| Typed `NOT_RETURNED` classifications | 114 |
| Model requests / responses | 853 / 853 |
| OpenTelemetry span rows | 967 |
| Request fingerprints | 853 |

The two `NOT_RETURNED` classes per task are returned reasoning content when the
provider supplied none and provider-private chain-of-thought, which Azure does
not expose. The recorder does not invent either value.

The manifest-owned five-file bundle passes deterministic verification. Two
supplemental files, `request-fingerprints.json` and `task-budget.json`, are
retained beside those artifacts. A verifier pointed at the entire seven-file
directory reports them as `UNEXPECTED_ARTIFACT`; consumers must select the
manifest-owned subset until the packaging adapter separates supplemental study
evidence. This is a packaging gap, not telemetry loss.

### Triana reuse judgment

- **Triana Labs analysis:** suitable as labeled third-party synthetic benchmark
  evidence for transcript, tool-use, failure-mode, and intervention discovery.
- **Triana Core import:** the required evidence is present, including messages,
  tool schemas/calls/results, task identity, and trace/span identity, but a
  normalization adapter is not yet authorized or implemented.
- **Persistent truth:** no task outcome is an accepted behavior or human ruling.
  The TAU evaluator result and any future Triana analysis remain separate
  evidence lanes.

## Cost and budget lineage

The final aggregate ledger is the deterministic cost authority:

| Metric | Value |
|---|---:|
| Final hard ceiling | USD 25.00 |
| Accrued | USD 9.559619 |
| Outstanding | USD 0.000000 |
| Ledger entries | 930 |
| Terra actual-usage debit | USD 9.151054 |
| Conservatively recovered prior outstanding debit | USD 0.408565 |
| Terra prompt tokens represented in actual-usage entries | 3,260,280 |
| Terra completion tokens represented in actual-usage entries | 66,689 |

Budget/source history is preserved rather than rewritten:

1. Run `...-001` used source v3 and was paused when its mistakenly frozen USD
   15 guard was corrected to the then-understood USD 10 owner authority.
2. Run `...-002` used source v4 and was paused when Akarsh explicitly clarified
   a USD 25 ceiling.
3. Run `...-003` used immutable source v5, conservatively carried all accrued
   and outstanding debit from both prior prefixes, and completed all 57 tasks.

The prior task results were not silently imported into the final coherent
panel. Only their monetary debit was carried forward.

## Azure execution and custody

| Resource | Identity |
|---|---|
| Region | `swedencentral` |
| Resource group | `triana-tau2-discovery-se5-20260805` |
| Private VM | `tau2disc805-vm` |
| Service | `tau2-retail-discovery.service` |
| Storage account | `tau2disc805xrinzdyhp4efk` |
| Container | `tau2-smoke` |
| Key Vault | `tau2disc805-xrinzdyhp4ef` |
| Final source SHA-256 | `cb8608be986f1d4c90010f208dafb5bd5b15cea0784f2fade19eb1ba858be04f` |
| Study manifest SHA-256 | `17af554deea93b9260d9abb3d769a410c476377a5dfe3923fed85d3cb1cc622c` |

The VM had no public IP. Managed identity resolved Key Vault and Blob custody.
Raw events and spans were appended to Blob during each task, completed attempts
were checkpointed before advancing, and bounded systemd restart recovery did
not fire. The worker exited with `Result=success` and zero restarts. Per owner
direction, the VM and its local raw run directory remain retained after worker
completion; infrastructure cost is separate from the model ledger.

## Terminal archive

```text
studies/tau2-retail-discovery-v1/archives/2788f37e3fa215548319be116dd1f5b47e70e04b188919e460441ed993a98169.tar.gz
```

| Property | Verified value |
|---|---:|
| SHA-256 | `2788f37e3fa215548319be116dd1f5b47e70e04b188919e460441ed993a98169` |
| Size | 5,757,732 bytes |
| Archive inventory | 516 items |
| Final run-prefix Blob objects | 630 |
| Terminal state | `COMPLETED` |

The archive was downloaded locally, its SHA-256 recomputed successfully, and a
verified copy was placed in `~/Downloads`. Raw archives, downloaded status, and
manifests live under the gitignored `runs/` tree and are deliberately not
committed.

## Reproduction and verification

From this experiment directory:

```bash
uv run --frozen python -c '
import json, tarfile
from pathlib import Path

archive = next(Path("runs/downloads/tau2-retail-discovery-v1").glob("*.tar.gz"))
with tarfile.open(archive, "r:gz") as source:
    results = [
        json.load(source.extractfile(name))["simulations"][0]["reward_info"]["reward"]
        for name in source.getnames()
        if name.endswith("tau2-results.json")
    ]
print({"tasks": len(results), "reward_sum": sum(results), "mean": sum(results) / len(results)})
'
UV_CACHE_DIR=/private/tmp/triana-tau2-uv-cache uv run --frozen \
  pytest -q tests/test_discovery_cloud_contract.py
UV_CACHE_DIR=/private/tmp/triana-tau2-uv-cache uv run --frozen ruff check src scripts
UV_CACHE_DIR=/private/tmp/triana-tau2-uv-cache uv run --frozen mypy src
bash -n scripts/azure_deploy.sh scripts/azure_run.sh \
  scripts/vm_discovery_bootstrap.sh
```

The frozen Discovery acceptance test has SHA-256
`c3a67211649e0ade4dcd99a2cdcb3f7ccc7803bdb91fb4b0a5f192caec46f47a`
and passes 9/9 against the committed implementation.

## Next valid experiment

Analyze only the 57 Discovery traces and pre-register one bounded intervention
before touching the holdout outcomes. Keep model identity, task split, trial,
seed, upstream commit, provider retry, cache, fallback, and evidence capture
constant. Then execute the holdout or a separately frozen paired panel exactly
once and report paired denominators, uncertainty, failures, and trace evidence.

The current baseline is useful precisely because its 18 failures are retained;
they must not be rerun to green or filtered out when selecting the intervention.
