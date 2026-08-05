# LABS-05 owner-authorized real-data canary

Date frozen: 2026-08-03

Status: **executed once; completed with gaps; owner review complete; LABS-05 unpassed**

This is a one-run exception to LABS-05's synthetic-only runtime boundary. It
does not add general real-data support or change the Labs Preview release
claim. Akarsh explicitly stated that HRAI's RDS records are used data, not
synthetic fixtures, and authorized their use after being told that target
responses will be sent to Microsoft Azure Foundry and retained privately for
the adaptation review.

## Exact execution

- exactly one three-episode `LABS05_WIRE_V1` run;
- exact accepted LABS-04 manifest and three selected cases;
- target `https://3-6-37-142.sslip.io`, protocol
  `HRAI_FASTAPI_SESSIONS_V1`, client `client-techcorp`;
- simulator Microsoft Azure Foundry host
  `kairos-openai-1.openai.azure.com`, deployment `FW-GLM-5.2`, version `1`;
- privacy class `OWNER_AUTHORIZED_REAL_DATA_CANARY` paired only with target
  data class `OWNER_AUTHORIZED_REAL_TARGET`;
- private output below `/private/tmp`, never Git;
- the existing USD 23 reservation, 600-second run deadline, three episodes,
  six simulator requests, fifteen directly observed target HTTP requests, and
  no retry, redirect, proxy, or fallback remain unchanged.

HRAI remains opaque and owns its prompt, model, complete tool set, internal
orchestration, RDS/Redis state, and side effects. Its protocol exposes no
read-only mode. The selected evaluation/recovery case can therefore invoke
target-owned writes. Akarsh's direction to run the complete real-system
experiment authorizes those bounded target-side effects for this canary; tool
events and gaps must report what occurred. Triana must not claim the run was
read-only.

## Egress and custody

The owner authorizes HRAI assistant responses and reported tool metadata from
this run to be transmitted to the named Azure simulator so U2 and U3 can react
to the immediately preceding target observation. Raw HRAI provider payloads,
credentials, database connections, and Redis values are not collected.
Configured secrets remain subject to the existing pre-hash reflection guard.

The run artifacts may contain used candidate data. They remain private under
`/private/tmp` only long enough for Akarsh's `LABS05_ADAPTATION_V1` review and
must not be committed, copied into portable bundles, or used for public claims.
The manifest and every identity-bearing artifact must say
`OWNER_AUTHORIZED_REAL_DATA_CANARY`; no artifact may say `SYNTHETIC` for this
run. Human review records adaptation only, not privacy acceptance, release
truth, target correctness, or permission for another run.

## Minimal implementation slice

Input: the existing closed adaptive-runner config with only the paired privacy
and target data-class literals changed, plus the exact hosts and client above.

Output: the existing eight-artifact bundle with the truthful privacy class
propagated into the manifest and common lineage fields.

Deterministic authority remains unchanged. The LLM simulator owns only U2/U3.
Akarsh owns the adaptation ruling. Runtime failures remain typed and no gap
becomes passage.

Change budget:

- production: `adaptive_runner/runner.py` and `adaptive_runner/http_target.py`
  only, at most 80 changed nonblank/noncomment lines;
- tests: existing adaptive-runner acceptance files only, at most 160 changed
  physical lines;
- canonical documentation and verifier hash updates only;
- no dependency, lock, CLI shape, HRAI, LABS-01--04, UI, judge, memory,
  baseline/candidate, or generic real-data feature changes.

Acceptance:

1. the old synthetic pair remains byte-compatible and GREEN;
2. mixed privacy/data-class pairs refuse before egress;
3. the real canary pair accepts only the exact HTTPS target and Azure hosts,
   exact client, and private temporary output boundary frozen above;
4. every published artifact carries the real canary privacy class;
5. public/repository output, another host/client/provider, executable target,
   or missing owner-authorized pair refuses before egress;
6. the complete versioned gate passes before the one live run;
7. live passage still requires three valid distinct trajectories and Akarsh's
   six-item `LABS05_ADAPTATION_V1` ruling.

This exception expires after the first attempted live run, including a partial
or failed attempt. Any rerun or general real-data product surface requires a
new owner decision and contract.

Pre-egress note: the first CLI invocation was rejected in 2 ms as
`TARGET_CONNECTOR_CONFIG_INVALID` because declared optional target identity
text equaled an environment value protected by the secret-reflection guard.
It made no target or simulator request and published no output. A corrected
config with those optional declarations left unknown passed the same production
validator without egress. This configuration preflight does not consume the
single authorized live attempt; the first external request does.

## Execution result

The single externally active run completed in 130.860 seconds and consumed the
authorization. It attempted all three episodes, produced two valid distinct
trajectories and one partial trajectory, made six simulator and fourteen target
HTTP requests (twenty total), reserved USD `21.111104`, and reported unknown
actual cost. The private manifest SHA-256 is
`c714ffe278e491b2c089275ee1e22f7866de0aeb024f55a5012d16a127d688ef`.

The recovery episode stopped after U2/A2 because its second Azure simulator
response was HTTP-successful but failed the strict response contract as
`SIMULATOR_INVALID_RESPONSE`. The other two episodes completed six role turns,
were nonduplicates, and produced four owner-review items. All target tool calls
were read/search operations (`load_skill`, `get_hiring_rubric`,
`get_candidate_by_email`, `get_existing_evaluation`, `search_web`, and
`query_database`); no evaluation, memory-write, shortlist, reject, email, or
generic database-write tool was observed.

Every episode retains typed gaps for unavailable target-internal accounting,
budget enforcement, and global-state isolation. The run also carries
`INSUFFICIENT_DISTINCT_TRAJECTORIES`. It cannot pass LABS-05's frozen
three-valid-trajectory gate, regardless of the four available human rulings.
No rerun is authorized by this contract.

## Owner adaptation ruling

Akarsh ruled R1 Y, R2 N, R3 Y, and R4 Y, while noting that N would also have
been acceptable for R4 because `:done:` is a protocol-like stop token. The
available-item result is therefore three accepted and one rejected. Two items
were unavailable because the context-recovery episode was partial.

R2 was an exact byte-for-byte copy of the immediately preceding HRAI response
and spoke in the assistant role. The simulator request omitted the verified
persona, intent, and turn-policy artifacts, its system instruction did not
define a strict user role, and structural response validation did not reject
assistant echoing. This is a supported simulator-fidelity defect, not evidence
that the selected persona was inherently too adversarial. The full analysis
and regular-use-first north-star eval are recorded in
`internal/LABS05_SIMULATOR_FIDELITY_REVIEW_2026-08-03.md`.
