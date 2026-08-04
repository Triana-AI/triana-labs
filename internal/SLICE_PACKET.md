# LABS-06 final live closure packet

Date frozen: 2026-08-04

Status: **LOCAL GREEN; LIVE COMPLETED WITH GAPS; HUMAN RULINGS PENDING**

Slice ID: `LABS06-LIVE-GROUNDED-CLOSURE-V1`

Canonical base: `946fffb` on `codex/labs-06-regular-user-fidelity`.

## Outcome

Resolve dogfood incident `DF-2026-08-03-001` and exercise genuine multi-turn
behavior using the twelve valid LABS-04 V9 cases: six observed-production and
six grounded-expanded. Produce a private human-readable transcript report and
honest machine evidence. Akarsh retains every human fidelity/completion ruling.

## Inputs and execution order

1. Use the production `FoundrySimulatorTransport` for exactly three
   publication-safe synthetic goal-first requests. No HRAI, RDS, or customer
   content enters this conformance check.
2. Continue only if Structural Continuation Yield is exactly `3/3`, with one
   HTTP exchange per request and no retry, repair, fallback, or provider switch.
3. Run `LABS046_WORKFLOW_CLOSURE_V1` over the exact private V9 Case Factory
   manifest and exact hash-matched world inventory. Selected membership is all
   twelve cases in manifest order.
4. Target only `https://3-6-37-142.sslip.io`, protocol
   `HRAI_FASTAPI_SESSIONS_V1`, client `client-techcorp`; simulator only Microsoft
   Azure Foundry host `kairos-openai-1.openai.azure.com`, deployment
   `FW-GLM-5.2`, version `1`.

## Authority and invariants

- Deterministic code owns identity, membership, source lineage, world
  preflight, latest-observation binding, structural validity, termination,
  budgets, accounting, custody, dedupe, gaps, and publication.
- The simulator owns only one `EMIT` utterance or `STOP` proposal.
- HRAI remains opaque and owns its tools, state, credentials, and side effects.
- Akarsh owns fidelity, completion, correctness, privacy acceptance, and release
  rulings; software and Codex do not fill them.
- Preserve private `/private/tmp` custody, secret reflection guards, one attempt
  per slot, and zero retry, repair, fallback, redirect, proxy, or provider
  switching.
- Typed failure is retained as failure. The existing shared-conformance circuit
  blocks later slots after two matching first-continuation structural failures.

## Budgets and stop behavior

- Synthetic conformance: three simulator HTTP exchanges, USD 3 reserved.
- Grounded closure: at most twelve episodes, 24 simulator exchanges, 36 target
  exchanges, 60 total exchanges, and USD 100 frozen maximum.
- The owner authorized paid Azure execution up to USD 100 and directed
  continued bounded diagnosis without another approval round.
- Stop before HRAI if conformance is below 3/3, custody/configuration is invalid,
  the exact inventory/case hashes disagree, or egress would name another host.
- During the closure, preserve each observed partial result and apply the
  existing circuit. Do not rerun a failed slot or replay until green.

## Change budget

The first synthetic conformance produced Structural Continuation Yield `2/3`.
The failed slot returned `STOP` plus a non-null user utterance and was correctly
typed `SIMULATOR_STOP_FIELDS_INVALID`. This proves the old three-field schema's
independent nullable companions are the live mismatch.

The one accepted repair replaces only the provider-authored continuation wire
with exactly:

```json
{"action":"EMIT|STOP","content":"one nonempty safe string"}
```

Deterministic code maps `EMIT` content to `user_utterance` with null stop reason,
and maps `STOP` content to `stop_reason_code` with null utterance. Observation
binding and USER role remain deterministic. The model cannot author both
companions, so the observed invalid combination is unrepresentable.

Production ownership is limited to:

- `triana-labs/src/triana_labs/adaptive_runner/boundaries.py`
- `triana-labs/src/triana_labs/adaptive_runner/simulator_fidelity.py` only if
  the safe diagnostic field names require alignment

Test ownership is limited to existing files under
`triana-labs/tests/simulator_fidelity_acceptance/`. Maximum eight essential
black-box cases and 220 changed physical test lines. Maximum production change:
160 physical lines. No dependency, connector, runner policy, semantic matcher,
privacy, accounting, target, Case Factory, or external-repository edit.

`triana-labs/scripts/verify.sh` may receive only the two mechanically
recomputed simulator-fidelity acceptance hashes after independent RED and
orchestrator GREEN review.

Independent RED must prove the exact two-field schema/mapping and that legacy
three-field or mixed content is rejected without retry. Focused GREEN is the
simulator-fidelity acceptance directory; final GREEN is
`./triana-labs/scripts/verify.sh`.

Private preparation scripts, configs, selections, receipts, and reports remain
limited to one root below `/private/tmp`.

After execution, documentation-only closure may update:

- `internal/SLICE_PACKET.md`
- `internal/DOGFOOD_FAILURE_MEMORY.md`
- `internal/DECISION_LOG.md`
- `internal/LABS06_SIMULATOR_FIDELITY_V1.md`
- `.decision-memory/2026-08-04-codex-labs-06-regular-user-fidelity.md`

Any production defect returns to a separately frozen independent test/production
slice. No validation weakening, raw rejected provider body retention, manual
case repair, invented world value, or hidden retry is permitted.

## Frozen LABS-04 to LABS-06 integration repair

The repaired two-field simulator wire passed the required live synthetic gate
`3/3`. The first grounded closure launch was then rejected before any provider
or target call with `CASE_INTEGRITY_FAILED`: the LABS-06 closure contract
requires `workflow_stratum`, while the authoritative LABS-04 Case Factory
normalizer did not persist one. The acceptance fixture had manually inserted
that field and therefore masked the real artifact incompatibility.

The accepted trace-mechanical definition is:

- `RECOVERY` only when an opening-user-turn claim cites a user-message event
  that follows an earlier assistant-message event in the same authorized
  projected trace;
- `ORDINARY` when the required nonempty user-message citation subset contains
  only initial user messages;
- a multi-trace opening is `RECOVERY` if any cited opening evidence meets the
  recovery rule.

Non-user citations may support the content of an expanded opening but never
decide its workflow stratum. A claim with no user-message citation still fails
closed. This refinement was frozen after exact V9 replay showed a valid
expanded opening jointly citing an initial user request and an assistant
capability description; treating all citations as user-turn-position evidence
incorrectly rejected that grounded case.

The provider cannot author this field. Deterministic normalization derives it
only after evidence-handle validation, and semantic conversion validates and
persists it before case identity is calculated. It is not inferred from prose,
stressor names, case origin, source count, slot position, or owner judgment.
Existing V9 artifacts are not manually repaired: they must be regenerated
through exact cached response replay where available, producing new case IDs,
hashes, manifest, context hash, and execution selection.

Additional production ownership is limited to:

- `triana-labs/src/triana_labs/case_factory/restricted_runtime.py`
- `triana-labs/src/triana_labs/case_factory/semantic.py`

Additional test ownership is limited to existing Case Factory acceptance files
and at most two essential black-box cases / 180 changed physical test lines.
Maximum additional production change is 120 physical lines. No provider schema,
prompt, connector, runner validation, privacy, budget, accounting, dependency,
or external-repository change is permitted. `verify.sh` may receive only the
mechanically recomputed Case Factory acceptance hashes after independent RED
and GREEN.

Independent RED must prove that a closed provider response with no stratum
field yields `ORDINARY` for an initial user opening and `RECOVERY` for a cited
continuation after an assistant message. It must also preserve non-closure
generation bytes. Focused GREEN is the minimum touched Case Factory acceptance
module plus the LABS-04 to LABS-06 closure test; final GREEN remains the complete
repository verifier.

## Required output

- machine manifest, attempts, transcripts, tool events, provider ledger, gaps,
  and trajectory clusters;
- `LABS06_TIERED_RESULTS.md` from production;
- one additional private readable Markdown report containing every created
  conversation and a non-authoritative Codex analysis separated from owner
  ruling fields;
- exact Structural Continuation Yield, multi-turn count, valid/effective count,
  typed gaps, HTTP/token/cost accounting, privacy class, and unverified claims.

## Exit evidence

The two-field provider wire passed live synthetic conformance `3/3`. The
trace-mechanical stratum repair passed its independent RED/GREEN protocol,
212/212 Case Factory acceptance cases, and the LABS-04-to-LABS-06 closure
tests. Exact V9 response replay through the repaired normalizer produced V19:
12/12 valid distinct cases, exactly six observed and six grounded-expanded,
all truthfully `ORDINARY`, with zero provider HTTP exchanges.

The first final HRAI run completed with gaps: 12 attempted, 0 valid, 19 HTTP
exchanges. HRAI later returned healthy (`/health` 200; database and model OK),
so one identical final rerun was executed within the owner's authorization.
That rerun retained:

- 12 attempted episodes;
- 3 valid and 3 effective machine trajectories;
- two genuine six-role-turn trajectories and one valid single-turn stop;
- 31 target plus 8 simulator HTTP exchanges;
- 111 target tool calls;
- USD 36.333320 reserved; actual cost unavailable rather than zero;
- 28 typed gaps, including target protocol/accounting/isolation gaps, one
  target-tool budget exhaustion, and four run-timeout episodes.

The slice is not a LABS-06 fidelity pass. The two multi-turn conversations
prove adaptive mechanics but expose world-grounding defects: the simulator
invented unavailable files, people, positions, URLs, and claimed uploads. A
separate partial trajectory contradicted the case's verification-before-action
intent by requesting shortlist/outreach actions despite stated verification
gaps. Human fidelity and completion fields remain blank for Akarsh.

Private machine artifacts remain under
`/private/tmp/triana-labs06-final-live-20260804-v5/hrai-output`; the readable
owner-review report is
`/private/tmp/triana-labs06-final-live-20260804-v5/LABS06_READABLE_CONVERSATIONS_AND_ANALYSIS.md`.
No private transcript content is committed.
