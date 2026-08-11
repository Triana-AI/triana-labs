# Triana self-serve Python onboarding slice

Date: 2026-08-11
Status: **RELEASE GREEN**
Owner: Akarsh Gajbhiye
Orchestrator: Codex

## Outcome

Ship the next immutable public alpha as `triana-preview==0.1.0a2` and the
canonical Codex/Claude plugin as `0.1.2`. A first-time user supplies an exact
authorized trace path and a plain agent description; the skill guides a local
Python-only `uvx` workflow through doctor, optional declarative adaptation,
validation, redacted preview, analysis, and semantic report verification.

The skill contains instructions only. Preview owns every deterministic command.
The public onboarding surface contains no Docker, image, release-profile,
release-manifest, or customer-authored runtime-manifest concept.

## Input and output contract

`doctor` accepts the exact trace path, a fresh/empty private output directory,
the canonical plugin root, explicit trace authorization, and either an
explicitly authorized private provider file or `--no-provider`. It performs no
network call. Its one content-free receipt proves:

- CPython 3.13 and installed `triana-preview==0.1.0a2`;
- Codex/Claude plugin files resolve one canonical skill, both plugin versions
  equal `0.1.2`, and every documented command pins Preview `0.1.0a2`;
- the provider file is a stable, private `0600` regular file containing only
  the authorized OpenAI-compatible HTTPS base URL, API key, and model fields;
- the output directory is private and empty; and
- the trace is structurally readable without retaining or emitting values.

Doctor never instantiates the provider client and never requires provider
egress approval or a request cap. Analysis still requires both explicitly.

`scaffold` writes a private declarative mapping file and contract, not Python.
`adapter-execute` accepts the exact source, completed mapping, and a new output
path; maps bounded JSON/JSONL conversation records and ordered events into
PreviewTrace v1; refuses ambiguity or missing required facts; and never executes
customer code. Validation remains a separate required command.

Long-running analysis writes content-free canonical progress receipts to
stderr while preserving one final canonical stdout receipt. Required phases
are `INPUT_VALIDATION`, `REDACTION`, `EXTRACTION_PREFLIGHT`, `EXTRACTION`,
`POPULATION_ANALYSIS`, `PATTERN_ANALYSIS`, `REPORT_FINALIZATION`, and
`SEMANTIC_VERIFICATION`; each phase emits `STARTED` and either `COMPLETED` or
`FAILED`. Receipts contain no paths, trace values, endpoint/model names,
prompts, responses, or secrets.

On a retained safe semantic diagnostic, the final receipt immediately exposes
`stage`, `failure_code`, optional `failure_class`, and optional `http_status`.
Closed failure classes are `AUTHENTICATION`, `MODEL_UNAVAILABLE`, `RATE_LIMIT`,
`RESPONSE_SCHEMA_INVALID`, `NETWORK`, and `UNKNOWN`. No provider prose or
payload crosses. Attempt accounting counts the shared provider ledger once;
using one model for both roles must not double-count a failed preflight.

## Authority, privacy, and refusal

Deterministic code owns structure, mapping execution, redaction, identities,
call accounting, progress receipts, report lineage, and verification. The model
proposes semantic labels and explanations. The human owns exact-path access,
provider-file access, provider egress, the positive request ceiling, and any
acceptance ruling.

Preserve stable exact-path reads, private `0700` directories and `0600` files,
temporary derived credentials removed after every outcome, no ambient secret
discovery, no telemetry or Triana upload, no automatic retry, and no fallback.
Missing or failed semantics remain typed partial evidence and cannot become a
successful Behavior Map.

## Change budget and roles

Staging roots are `/private/tmp/triana-self-serve-preview` and
`/private/tmp/triana-self-serve-skills`, copied from the clean public release
heads before RED. They are disjoint from the dirty private monorepo.

The independent test author may change only `tests/**` in both staging roots.
It must establish collection and a valid RED state covering doctor/no-egress,
version/source parity, private permissions, declarative adapter execution,
progress/failure receipts, shared-ledger accounting, exact uvx pins, canonical
Codex/Claude parity, and forbidden onboarding vocabulary. It returns exact test
hashes; tests then freeze.

After the freeze, the independent implementation author may change only:

- Preview: `pyproject.toml`, `uv.lock`, `README.md`, `PRIVACY.md`,
  `src/triana_preview/**`;
- Skills: `README.md`, both marketplace JSON files, both plugin JSON files,
  `plugins/triana/skills/onboard/SKILL.md`, and
  `plugins/triana/skills/onboard/agents/openai.yaml`.

No test edit, dependency addition, provider/customer execution, unrelated
refactor, or private monorepo production edit is allowed. The orchestrator owns
canonical docs, decision records, staging/public-repository reconciliation,
fresh `uvx`, plugin cache refresh, commit/push, and PyPI publication after GREEN.

## Acceptance

1. Frozen suites pass; Ruff, format, strict mypy, package build, Skill Creator
   validation, and official Claude/Codex plugin validation pass.
2. Doctor proves all checks and zero provider calls; unsafe provider/output,
   mismatched plugin/pin, wrong Python/package, and invalid traces fail closed.
3. A synthetic unfamiliar schema completes scaffold → mapping edit →
   adapter-execute → validate without executing Python.
4. A synthetic semantic failure emits safe immediate phase/final diagnostics
   and exactly one shared attempted call when one configured model fills both
   roles. No retry or fallback occurs.
5. Public user-facing onboarding contains none of the superseded vocabulary.
6. Built artifacts contain only the accepted public inventory and exact
   version metadata. A fresh PyPI-only `uvx` journey and refreshed Codex/Claude
   marketplace/cache copies match canonical bytes.
7. Publication stops on any provenance, secret, security, or verification gap.

No customer traces or paid provider calls are part of acceptance.
