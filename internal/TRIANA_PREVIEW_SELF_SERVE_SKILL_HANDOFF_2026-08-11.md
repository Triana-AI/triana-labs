# Triana Preview self-serve skill handoff — 2026-08-11

## Objective

Finish the `onboard` skill before another live customer run. A fresh Codex or
Claude Code session must start from one authorized trace path, one short agent
description, and one ordinary OpenAI-compatible provider file. The customer
must not construct a release manifest, container digest, Triana's internal
sixteen-field provider binding, or a behavior taxonomy.

Do not run a provider or the full corpus until this closure is verified offline
and the plugin has been refreshed in the test session.

## Accepted customer contract

Required customer inputs:

1. authorized local trace path;
2. one-to-three-line agent description;
3. explicit trace-analysis and provider-egress authorization;
4. a private provider file containing:

   ```text
   OPENAI_BASE_URL=<OpenAI-compatible base URL>
   OPENAI_API_KEY=<secret>
   OPENAI_MODEL=<optional model name>
   ```

`OPENAI_MODEL` may be omitted only when the bundled release profile declares a
valid default for its own provider boundary. The current preference is Luna as
primary. Separate author/auditor endpoints, keys, or models are advanced
overrides, never default onboarding requirements. There is one provider
configuration for the complete run, not one per stage, population, behavior,
or taxonomy dimension.

Triana owns and hides:

- the immutable private-image digest and release manifest;
- provider adapter and primary/auditor role expansion;
- deployment metadata, SKU, capacity, pacing, credential-boundary labels, and
  run-wide budget ceiling;
- generation of any internal `TRIANA_BEHAVIOR_MAP_*` environment in a private
  temporary file;
- Behavior Map episode, demand-family, requested-action, modifier, population,
  behavior-pattern, emerging/unknown, evidence, and uncertainty machinery;
- final report verification.

The behavior taxonomy is generated from authorized trace evidence by the
Behavior Map engine. It is never supplied through `.env`, the skill prompt, or
a customer label file. The agent description is context, not a taxonomy.

## Current repository state

- Repository: `/Users/akarshgajbhiye/triana`
- Branch: `codex/triana-preview-local`
- Current committed HEAD/upstream tip before this handoff: `ab50795`
- The skill and latest engine/Preview repairs are uncommitted and not upstream.
- Preserve the complete dirty worktree. Do not reset, overwrite, or broadly
  stage it.

The private 200-conversation ABCD execution proved the engine path: 200
accepted conversations, 45 supported populations, 40 supported patterns, 288
primary attempts, and 116 auditor attempts. Its report is proposed and partial,
with typed gaps. This proves engine value, not self-serve packaging.

## Current skill state and exact defects

Current skill root:
`triana-skills/plugins/triana/skills/onboard/`

Already implemented locally:

- complete/execute/verify instructions for Codex and Claude Code;
- private provider-env path binding without printing values;
- fresh private output checks;
- `verify-report --require-semantic`;
- real partial-report acceptance using `attempted_call_count`, nonzero
  populations, and supported patterns.

Still wrong for self-serve:

1. `docker-command` requires a separately supplied published release manifest.
2. The plugin ships only an intentionally `UNPUBLISHED` example manifest.
3. Provider validation requires exactly sixteen internal
   `TRIANA_BEHAVIOR_MAP_*` variables.
4. A normal application `.env`, including the authorized HRAI Azure file, is
   rejected rather than normalized.
5. Customer instructions expose internal image/provider plumbing.
6. Latest skill changes are not committed, pushed, or installed through a
   refreshed marketplace/plugin snapshot.

The sixteen variables are runtime/provider lineage fields, not taxonomy. API
keys must never be bundled. Non-secret defaults and mapping belong in the
release profile and skill.

## Required implementation

1. Add one bundled, versioned release profile used automatically by
   `docker-command`. It binds the immutable private image internally and carries
   non-secret provider/model/auditor/budget/pacing defaults. The customer must
   not pass its path or see its digest in the normal journey.
   For the current no-registry local pilot, the profile may bind and verify the
   already-loaded immutable local image ID; it must not pretend that this is a
   published registry digest. A later registry release replaces only the
   profile's image locator.
2. Accept the minimal three-field provider file. Validate it as a private
   regular file, never print values, and normalize it once into the engine's
   internal binding. Use the same endpoint/key for both roles unless an
   explicit advanced override is supplied.
3. Keep model optional only when the bundled profile owns a valid default. Do
   not silently fall back after a provider/model failure.
4. Remove manifest and sixteen-variable requirements from default skill
   instructions. Retain an expert override only if typed and explicit.
5. Keep digest verification internal. Human output says the installed release
   was verified; it does not ask the customer to reason about a hash.
6. Retain authorization, local custody, read-only input, private output,
   redaction, no retry/fallback, typed gaps, and content-free verification.
7. Refresh Codex and Claude Code plugin installation only after source is
   committed or intentionally loaded from the local marketplace.
8. Then run one fresh customer-agent journey from original traces, not a
   prevalidated Triana artifact.

## Frozen exclusions

- No Behavior Map prompt/schema/threshold/audit change.
- No customer-specific ABCD adapter in the public skill.
- No credential or raw trace in repository, profile, prompt, logs, or report.
- No retry, fallback, hosted upload, telemetry, deployment, or public image
  publication without separate authorization.
- No accepted-baseline replacement or ABCD semantic promotion.

## Completion gate

The skill is ready only when a fresh agent completes the journey without
asking for a manifest, digest, sixteen internal variables, taxonomy, labels,
deployment version, SKU, capacity, credential-boundary ID, pacing, or lane
budgets.

Customer prompt after the fix:

```text
Use the Triana onboard skill to analyze my authorized local conversational
traces end to end.

Trace path: <ABSOLUTE_TRACE_PATH>
Agent: <ONE-TO-THREE-LINE_AGENT_DESCRIPTION>
Provider environment: <ABSOLUTE_PRIVATE_ENV_PATH>

I authorize local trace analysis and semantic provider egress. Prepare or adapt
the traces, run the installed private Triana Preview release into a fresh local
output directory, and verify the final report. Do not stop at scaffolding or a
no-network preview.
```

## Structured uncertainty handoff

- Changed here: continuation documentation only; existing dirty implementation
  is preserved.
- Unverified: bundled profile, minimal-provider normalization, refreshed plugin,
  and fresh customer run.
- Assumptions: distribution can pair the plugin with an immutable private image;
  Luna defaults only where the profile truthfully binds it.
- Unexpected finding: the secure scaffold was described as self-serve while it
  intentionally withheld both runnable release and usable normalization.
- Dependencies: one honest private image/profile and one supported
  OpenAI-compatible provider boundary.
- Risk: one model used for author and auditor is not independent-model audit and
  must be labeled honestly.
- Human action after implementation: supply the minimal inputs and approve one
  fresh run; no deterministic implementation choices should return to human.
