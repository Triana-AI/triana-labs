# LABS-04 proof-first Case Factory packet

Date frozen: 2026-08-04

Status: **FROZEN AND VERIFIED**

Slice ID: `LABS04-STRICT-STRUCTURED-NORMALIZATION-PROOF-V2`

## Outcome

Prove that the Case Factory can normalize the four already-selected private
HRAI traces against the captured current-world inventory through a
provider-neutral strict JSON-Schema response, producing and immediately
persisting one valid grounded or expanded case per exchange.

## Accepted behavior

For an authoritative LABS046 workflow-closure request only:

- the run configuration and world inventory are complete; model questions are
  unavailable;
- the selected trace catalog is already the evidence packet, so the model gets
  no search, trace-fetch, budget-inspection, or submission tools;
- the provider must support strict `response_format: json_schema`; unsupported,
  malformed, refused, length-truncated, or schema-invalid output is a typed
  failure and never enters a parser/repair fallback;
- each authoritative exchange requests and may persist exactly one case bundle;
- case slots 1-6 are grounded observed normalizations and slots 7-12 are
  grounded expansions;
- all world identifiers must resolve in the supplied inventory;
- the working context ceiling is `min(100,000 tokens, configured model context
  limit)` with 20% instruction/schema, 55% evidence, and 25% output/safety;
- context refusal occurs before egress and provider timeout remains typed;
- every accepted bundle is atomically retained before the next planned slot;
- no retry, repair, fallback, provider switch, prose extraction, or invented identifier is
  allowed.

Non-authoritative and legacy Case Factory behavior is deliberately untouched.

## Change budget

Production ownership is limited to:

- `triana-labs/src/triana_labs/case_factory/restricted_runtime.py`
- one additive strict wire-schema file under
  `triana-labs/src/triana_labs/case_factory/schemas/` only if required

Documentation ownership is limited to:

- `internal/SLICE_PACKET.md`
- `internal/DOGFOOD_FAILURE_MEMORY.md`
- `internal/DECISION_LOG.md`
- `.decision-memory/2026-08-04-codex-labs-06-regular-user-fidelity.md`

Test ownership is limited to one new black-box module:

- `triana-labs/tests/case_factory_acceptance/test_authoritative_structured_normalization.py`
- `triana-labs/tests/case_factory_acceptance/test_grounded_workflow_closure.py`
  may receive only the mechanical fixture update from one five-case scripted
  response to twelve one-case scripted responses. This bounded expansion was
  added after the focused suite showed three fixture-exhaustion failures while
  the remaining 205 Case Factory acceptance tests passed; assertions may not
  be weakened.
- `triana-labs/scripts/verify.sh` may receive only the two mechanically
  recomputed Case Factory acceptance freeze hashes after the orchestrator has
  reviewed the final test content and independently reproduced RED and GREEN.

No dependency, schema, connector, simulator, target, fixture, unrelated
formatting, or external-repository change is allowed. Maximum production
change: 520 physical lines across the bounded production paths. The final
increase covers the compact Azure-subset wire, recursive wire validation, and
deterministic translation into the unchanged internal submission contract. No dependency,
connector, simulator, target, or unrelated production file is allowed.

The acceptance freeze covers only the authoritative closure behavior already
proven live: strict schema output without tools, one independently retained
case per exchange, exact observed/expanded slot derivation, deterministic
projection of evidence handles and world bindings, partial retention on a
later typed provider failure, context refusal before egress, and preservation
of accounting/privacy/no-retry behavior. It must not copy private traces or
provider bodies into fixtures.

## Freeze verification

Independent RED command against canonical base `1460266`:

```text
uv run --project triana-labs --locked pytest -q triana-labs/tests/case_factory_acceptance/test_authoritative_structured_normalization.py
```

Focused GREEN command in the integration worktree:

```text
uv run --project triana-labs --locked pytest -q triana-labs/tests/case_factory_acceptance/test_authoritative_structured_normalization.py triana-labs/tests/case_factory_acceptance/test_grounded_workflow_closure.py
```

Complete repository verifier:

```text
./triana-labs/scripts/verify.sh
```

Freeze evidence:

- canonical-base RED at `1460266`: 4/4 acceptance cases failed on the absent
  authoritative path;
- focused integration GREEN: 12/12 tests passed;
- full Case Factory acceptance: 212/212 passed;
- final acceptance module SHA-256:
  `c25d183bae367722dc87e21d4cfc6857a9bd3361ef7fc852dbae5fa702c6c0cb`;
- complete repository verifier: 617 tests plus sdist, wheel, and clean-wheel
  installation passed; evidence retained at
  `/private/tmp/triana-labs-verify.m8oIxX`.

## Proof execution

The user explicitly authorized one fresh proof run using the same four
selected HRAI traces, private world inventory, Microsoft Foundry deployment
`FW-GLM-5.2`, and `/private/tmp` custody. The existing LABS-04 USD 25 maximum
and USD 2 reservation per logical Case Factory call remain in force. This
authorization does not permit an HRAI target run, another provider, a retry,
repair, or fallback.

The proof-first round intentionally added and ran no test files and did not
run the repository verifier. The live proof visibly reported tool-call
names, prompt/context accounting, generated tier counts, inventory binding,
provider exchanges, cost accounting, and typed gaps. Tests and the complete
repository verifier are now authorized because the proof succeeded and the
owner requested the freeze.

## Stop conditions

Stop on ambiguity, context preflight refusal, private custody failure,
unapproved egress, any model/tool call, provider failure, length truncation,
schema/semantic rejection, budget exhaustion, or any edit outside the change
budget. Do not retry or repair during the live proof.
