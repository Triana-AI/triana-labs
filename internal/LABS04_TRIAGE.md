# LABS-04 Grounded Case Factory triage ledger

Date opened: 2026-08-01
Status: active until the HRAI smoke produces reviewable cases or the checkpoint
is explicitly closed as failed

This is an evidence ledger, not product authority or an acceptance backlog.
Accepted durable decisions remain append-only in `internal/DECISION_LOG.md`;
the live contract remains `internal/SLICE_PACKET.md` and
`internal/LABS04_WIRE_CONTRACT.md`.

## Reading the ledger

- **Type** distinguishes a production bug from a contract/specification hole,
  test defect, orchestration error, provider observation, or environmental
  failure.
- **Classification evidence** says why the observed behavior belongs in that
  category instead of relying on inference from a generic failure code.
- **Fix authority** records who made or approved the correction.
- **Status** is one of `CLOSED`, `FIX IN PROGRESS`, `OPEN`, or `OBSERVATION`.
- Provider failures are preserved. A changed-version run is never represented
  as if the earlier attempt did not happen.

## Current checkpoint state

| Surface | State | Evidence |
|---|---|---|
| Local repository gate | GREEN | 352 tests, Ruff, strict mypy, build, clean CPython 3.13 wheel, frozen hashes |
| HRAI source accounting | GREEN | 50 lines = 25 adapter accepts + 25 explicit source rejections |
| Observer/intelligence | GREEN with typed gaps | 25/25 Observer accepts; 22 structural clusters; three semantic gaps |
| Corrected request preflight | GREEN, zero egress | 25 traces, 424 citations, zero exclusions, 193,868 bytes |
| First Azure attempt | PRESERVED FAILURE | HTTP 200; 28,295 input; exactly 4,096 output; no artifacts |
| Corrected Azure attempt | PRESERVED FAILURE | HTTP 200; 58,855 input; 4,877 output; no artifacts |
| Final repair-validation attempt | PRESERVED FAILURE | HTTP 200; 58,855 input; 4,444 output; one call; no artifacts |
| Current repair | CLOSED | Independent RED `8da6fca`; production fix `18748af`; full gate green |
| Product usefulness | UNPROVEN | No generated case bundle exists yet; owner rubric cannot be scored |

## Triage items

### TRIAGE-01 — originally named HRAI smoke file was incompatible

- **Type:** contract/specification input error.
- **Observed:** the frozen legacy `run_50b` source produced 0 accepted records
  out of 50 through the shipped LABS-02 adapter.
- **Classification evidence:** the adapter was conforming to its frozen HRAI
  v2 contract; the named file used a different legacy schema. A tracked v2
  corpus at pinned HRAI commit
  `728f6c5058efe40a16e2aecc9b528b3353f4df4f` existed and exercised the
  intended mapping.
- **Fix:** before production, freeze the first 50 physical lines of v2
  `run_200`, SHA-256
  `4bb5839771bffe13b33b30cb42cf8cfc4ab1513e9012c10da0923bf58e1e991c`.
  Preserve its honest 25 accepted/25 rejected denominator; no fallback corpus.
- **Fix authority:** Codex identified and corrected the bad freeze; Akarsh
  reaffirmed fail-fast/no fallback.
- **Regression/evidence:** pinned source identity and adapter/Observer smoke
  assertions in the slice packet.
- **Status:** CLOSED.

### TRIAGE-02 — first smoke config omitted `api_key_env`

- **Type:** Codex orchestration error, not production behavior.
- **Observed:** local preflight returned `CONFIG_INVALID(2)` with zero Azure
  calls.
- **Classification evidence:** the private config omitted a required exact
  field already present in the frozen wire; adding that field made `_config`
  and `_egress` preflight pass without changing code.
- **Fix:** correct the private config; preserve the original refusal receipt.
- **Fix authority:** Codex owned and corrected its command/config error.
- **Regression/evidence:** existing strict-config tests; private
  `preflight-case-terminal.jsonl` retained.
- **Status:** CLOSED.

### TRIAGE-03 — evidence-root limit did not bound the actual provider request

- **Type:** wire-contract sizing defect.
- **Observed:** the HRAI evidence root was 73,650 bytes, but 424 required
  singleton citations expanded the exact PROPOSE request to 193,867 bytes;
  pre-egress returned `EVIDENCE_TOO_LARGE(3)`.
- **Classification evidence:** the original 100,000-byte complete-request
  ceiling assumed only a small envelope reserve. Exact serialization falsified
  that assumption. A proposed total-citation cap contradicted the frozen rule
  requiring a citation for every projected event and was rejected by the
  independent tester.
- **Fix:** first implement deterministic whole-trace tail fitting; after live
  telemetry and budget reconciliation, permit a 240,000-byte request so all 25
  traces and 424 citations fit. No citation truncation or hidden replacement.
- **Fix authority:** Codex proposed the correction under the approved smoke
  budget; independent tester rejected the conflicting citation-cap idea and
  froze the corrected behavior before production.
- **Regression/evidence:** exact 240,000 acceptance, 240,001 tail fit, and
  sole-oversized-trace pre-egress refusal tests.
- **Status:** CLOSED.

### TRIAGE-04 — combined-suite test helper import collision

- **Type:** test-harness bug.
- **Observed:** isolated LABS-04 tests passed, but the combined suite produced
  three import failures because runtime `from conftest` resolved to an already
  cached LABS-03 module.
- **Classification evidence:** production behavior and all 142 assertions were
  unchanged; moving the same imports to explicit module-level bindings made
  isolated and combined runs agree.
- **Fix:** independent tester corrected only test import binding.
- **Fix authority:** Codex reproduced the order dependency; independent test
  author made the test-only correction.
- **Regression/evidence:** full combined verifier, not isolated suites alone.
- **Status:** CLOSED.

### TRIAGE-05 — first Azure response reached the old output ceiling

- **Type:** provider observation with a budget/wire correction; exact parser
  failure cause remains unobservable because raw responses are intentionally
  not retained.
- **Observed:** one HTTP 200 call, 28,295 input tokens, exactly the configured
  4,096 output tokens, followed by `PROVIDER_FAILED(8)` and no output bundle.
- **Classification evidence:** read-only Azure telemetry ruled out auth,
  transport, non-200 HTTP, and zero generation. Exact ceiling contact strongly
  supported truncation, but it did not prove the raw `finish_reason`.
- **Fix:** preserve the failed attempt; reshape the remaining run to three
  calls, no retries, 12,000 output tokens, 240,000 input bytes, and USD 8.70,
  keeping the then-calculated cumulative conservative ceiling below USD 10.
- **Fix authority:** Codex made and logged this material technical correction
  under Akarsh's prior Azure/USD 10/fail-fast authorization.
- **Regression/evidence:** exact request token setting, reservation arithmetic,
  call cap, no-retry, and fatal/partial lineage tests.
- **Status:** CLOSED as a preserved failed version; not evidence of usefulness.

### TRIAGE-06 — oversized fixture asserted a vanity byte count

- **Type:** test defect.
- **Observed:** production and the independent request oracle serialized the
  same sole-trace request to 240,776 bytes while one test asserted 240,055
  before generation ran.
- **Classification evidence:** that fixture's contract duty was only
  `request > 240,000` followed by pre-egress refusal. Separate independent
  tests already own exact 240,000 and 240,001 boundary behavior.
- **Fix:** replace `== 240_055` with `> 240_000`; do not tune fixture events to
  recover a magic size.
- **Fix authority:** Akarsh challenged vanity-limit testing; independent tester
  audited and made the test-only correction.
- **Regression/evidence:** `01b87dc`; 163/163 LABS-04 and 188/188 historical.
- **Status:** CLOSED.

### TRIAGE-07 — versioned verifier retained stale test hashes

- **Type:** Codex orchestration/bookkeeping bug.
- **Observed:** full runs passed all 351 tests, then the verifier stopped on
  stale corrected-budget acceptance/adversarial hash constants.
- **Classification evidence:** measured tracked bytes matched the independent
  test freeze; no test changed during reconciliation. Codex's first update also
  missed two already-changed adversarial files, requiring a second correction.
- **Fix:** update every acceptance aggregate and all three adversarial file
  hashes in the orchestrator-owned gate; append exact canonical evidence.
- **Fix authority:** Codex owned both the stale constants and incomplete first
  reconciliation.
- **Regression/evidence:** versioned gate later passed all hashes.
- **Status:** CLOSED.

### TRIAGE-08 — clean-wheel install could not reach PyPI in sandbox

- **Type:** execution-environment failure, not a product bug.
- **Observed:** 351 tests, hashes, and build passed; clean installation failed
  only on DNS resolution for `pydantic`.
- **Classification evidence:** rerunning the identical versioned gate with
  network permission installed the same locked dependencies and passed clean
  CPython 3.13 wheel verification.
- **Fix:** rerun the unchanged gate with network permission. No code or test
  change.
- **Fix authority:** Codex, under the repository's clean-install gate.
- **Regression/evidence:** final `triana-labs verification passed` evidence at
  `/private/tmp/triana-labs-verify.mAQ40m`.
- **Status:** CLOSED.

### TRIAGE-09 — production rejects valid Azure usage metadata

- **Type:** production compatibility bug against the frozen wire.
- **Observed:** corrected smoke made exactly one HTTP 200 request with 58,855
  input tokens and 4,877 output tokens, below the 12,000 ceiling, but Triana
  returned `PROVIDER_FAILED(8)` and published no cases.
- **Classification evidence:** `generate._response` accepts `usage` only when
  its key set is exactly the three core token counts or those counts plus
  `cost`. Frozen wire section 8 says extra Azure response fields are ignored
  after projecting validated fields. Azure's v1 response contract documents
  optional `prompt_tokens_details` and `completion_tokens_details`. Therefore
  a valid provider envelope can be rejected before structured content is used.
- **Fix:** accept benign extra response/usage metadata while continuing to
  validate required core counts, arithmetic, optional cost, strict JSON,
  single choice, finish reason, content schema, response size, and secrets.
  Portable attempts retain only core token counts and optional cost; the raw
  response hash remains sensitive to every extra byte.
- **Fix authority:** no new product decision. Independent test author froze the
  existing wire at `8da6fca`; implementation author made the smallest
  production-only correction at `18748af`.
- **Regression/evidence:** new fake-transport test is the sole intended RED:
  164 LABS-04 collected, 163 pass/one RED; 188 historical pass. No Azure call.
- **Status:** CLOSED: 164/164 LABS-04 and 188/188 historical tests plus the
  352-test versioned build/clean-wheel/hash gate pass.

### TRIAGE-10 — local preflight imported the public function as a module

- **Type:** Codex diagnostic-command error.
- **Observed:** the first corrected zero-egress Python preflight raised
  `AttributeError` because `generate` resolved to the public function.
- **Classification evidence:** no transport was constructed or called; an
  explicit `importlib.import_module` invocation immediately completed the same
  read-only calculation.
- **Fix:** use explicit module import for internal diagnostic calculation.
- **Fix authority:** Codex.
- **Regression/evidence:** corrected zero-egress result: 25 selected traces,
  424 citations, zero exclusions/gaps, 193,868 bytes, no secret in request.
- **Status:** CLOSED.

### TRIAGE-11 — provider-schema success does not imply semantic acceptance

- **Type:** open product/wire design failure exposed by live smoke.
- **Observed:** the one-time post-`18748af` repair-validation run again returned
  `PROVIDER_FAILED(8)` after exactly one Azure HTTP 200 request with 58,855
  processed prompt tokens and 4,444 generated tokens. It made no second-stage
  call and published no artifacts.
- **Classification evidence:** the response was below the 12,000 output limit,
  the Azure envelope parser now passes its independently frozen official-extra
  regression, and the full package gate is green. Raw provider bodies are
  intentionally not retained, so the exact failing field remains unknown and
  cannot honestly be claimed. Code inspection nevertheless proves the
  published proposal JSON Schema omits many deterministic postconditions that
  `convert_lane` enforces after parsing: 1–10 semantic assets, exactly five
  cases, local-key formats and uniqueness, sorted/unique citations and gaps,
  support-state trace cardinality, cross-asset references, nonempty reaction
  rules, complete claim use, and observed anchors. Azure structured output can
  satisfy the schema while still being discarded before CRITIQUE.
- **Fix:** the bounded recovery at `dae4bf1` preserves exact secret-safe stage
  evidence, diagnoses three frozen semantic defects, carries an invalid parsed
  proposal through CRITIQUE and REVISE, and adds exact local response replay;
  strict final semantic validity is unchanged.
- **Fix authority:** Akarsh approved the minimal recovery and one final live run
  under USD 15; the independent RED is `1f65901` and reconciled suite is
  `3e716bb`.
- **Regression/evidence:** private terminal SHA-256
  `f129baff229940cf4faf18a4fcad6bebd417a23bcdfd72c6e2365ce3205b3e7b`;
  Azure minute metrics at 07:43Z; no output directory.
- **Status:** RECOVERY LOCALLY GREEN: 167/167 LABS-04 tests, Ruff, and strict
  mypy pass. Grounded Case Factory usefulness remains unproven until the full
  gate and one authorized live smoke complete.

## Remaining decisions requiring owner visibility

1. **Usefulness verdict:** unavailable because no case bundle has yet been
   published by a live provider run.
   The rubric remains unchanged for a future valid bundle.
