# Active implementation slice — LABS-03 structural Corpus Intelligence

Status: **INDEPENDENT ACCEPTANCE FROZEN — IMPLEMENTATION AUTHOR AUTHORIZED**

Date: 2026-07-31
Branch: `codex/labs-03-corpus-intelligence`
Canonical base: `c993be3`
Slice ID: `LABS-03-structural-corpus-intelligence`

## 1. Product outcome

Prove that the unchanged synthetic Trace Observer bundle is a usable input to
the next canonical component. The new command derives deterministic,
inspectable structural clusters with support, ambiguity, fidelity, lineage,
and explicit gaps. It does not invent semantic personas, intents, distress,
language, or turn-generation policy.

This is the first bounded checkpoint inside plan milestone M1B. It is not full
Corpus Intelligence and does not start Case Generator.

```text
PreviewTrace JSONL
  -> triana traces observe
  -> Observer manifest + normalized_traces.jsonl
  -> triana corpus derive <manifest> --out <new-directory>
  -> structural clusters + typed semantic gaps
```

## 2. Invocation and location

```bash
triana corpus derive <observer-output>/manifest.json \
  --out <new-intelligence-directory>
```

Execution is local and deterministic. The command performs no network access,
provider call, model inference, redaction, hidden credential discovery, or
environment-based configuration. Only Observer bundles labeled `SYNTHETIC`
are accepted.

## 3. Input contract

The input is a regular, non-symlink Observer `manifest.json`, at most 1 MiB,
inside a regular local directory. It must be strict UTF-8 JSON with no BOM,
duplicate key, non-finite number, or container depth above 32.

The manifest has exactly the LABS-01 keys `accepted_count`, `artifact_kind`,
`artifacts`, `case_generation_eligible_count`, `input_count`, `privacy_class`,
`rejected_count`, and `schema_version`. Kind is `corpus_manifest`, schema
version is 1, privacy is `SYNTHETIC`, and nonnegative safe-integer counts obey
`input_count = accepted_count + rejected_count`. `artifacts` has exactly
`corpus_profile.json`, `corpus_profile.md`, `normalized_traces.jsonl`, and
`rejected_traces.jsonl`, with lowercase `sha256:<64 hex>` values.

LABS-03 hashes all four regular non-symlink sibling artifacts. Limits are 16
MiB for each JSONL file, 1 MiB for each profile file, 1,000 normalized physical
lines, and 1 MiB per normalized line. It parses every normalized line through
the unchanged PreviewTrace validator, verifies accepted count and unique
trace/source identities, and verifies `corpus_profile.json`.

The profile has exactly `accepted_count`, `artifact_kind`,
`case_generation_eligible_count`, `distress_analysis`, `event_kind_counts`,
`input_count`, `language_analysis`, `rejected_count`,
`rejection_code_counts`, `schema_version`, `terminal_state_counts`, and
`tool_call_counts`. Its kind is `corpus_profile`, schema version is 1, its four
corpus counts match the manifest, and both analyses are `NOT_EVALUATED`. Any
sibling absence/symlink/nonregular file, hash/count/schema
contradiction, invalid normalized trace, or duplicate identity is fatal
`CORPUS_INTEGRITY_FAILED`. An accepted count of zero is fatal `EMPTY_CORPUS`.
Source rejections are permitted when at least one accepted trace exists and
become a typed derivation gap.

The Observer remains the input-validation owner. LABS-03 does not accept raw
PreviewTrace JSONL or an external source export directly.

## 4. Exact deterministic clustering

Each accepted trace receives one structural fingerprint derived only from its
validated ordered event shapes:

```json
{
  "assistant_message_count": 0,
  "case_generation_eligible": false,
  "terminal_state": "MISSING",
  "tool_call_count": 0,
  "tool_error_count": 0,
  "tool_name_sequence": [],
  "tool_result_count": 0,
  "unmatched_tool_call_count": 0,
  "user_message_count": 0
}
```

`unmatched_tool_call_count` counts calls with no later result for the same
call ID. `tool_error_count` counts error-state tool results. The terminal state
is the one validated terminal value or `MISSING`.

Traces with byte-identical canonical fingerprints share one cluster.
`cluster_id` is `cluster-` plus the first 16 lowercase hex characters of the
SHA-256 of the compact sorted-key fingerprint JSON bytes. Cluster members are
sorted by trace ID and clusters by cluster ID, independent of input line order.

Each cluster contains exactly:

- `cluster_id`;
- the complete fingerprint;
- `member_trace_ids`;
- `support_count`;
- `support_state: SINGLETON | SUPPORTED`;
- `ambiguity_state: SEMANTICS_NOT_EVALUATED`;
- `fidelity: SYNTHETIC_OBSERVED_STRUCTURE`.

No system/user/assistant text, opaque argument/result value, error/reason text,
or source trace ID enters cluster artifacts. Safe tool names and trace IDs are
the only source-derived strings retained.

## 5. Exact output bundle

`--out` must not exist and its immediate parent must be a real directory. A
successful partial derivation is published atomically as:

```text
manifest.json
clusters.json
derivation_report.json
personas/index.json
intents/index.json
turn_policies/index.json
```

All JSON is compact, sorted-key UTF-8 with one LF. The fingerprint hash preimage
uses that encoding without LF. The five non-manifest files carry schema version
1, `fidelity: SYNTHETIC_OBSERVED_STRUCTURE`, and the SHA-256 of the exact input
manifest bytes including LF as `input_manifest_hash`. Timestamps and random
values are absent.

The output `manifest.json` has exactly:

```json
{
  "artifact_kind": "intelligence_manifest",
  "artifacts": {
    "clusters.json": "sha256:<digest>",
    "derivation_report.json": "sha256:<digest>",
    "intents/index.json": "sha256:<digest>",
    "personas/index.json": "sha256:<digest>",
    "turn_policies/index.json": "sha256:<digest>"
  },
  "cluster_count": 0,
  "fidelity": "SYNTHETIC_OBSERVED_STRUCTURE",
  "gap_count": 0,
  "input_manifest_hash": "sha256:<digest>",
  "outcome": "COMPLETED_WITH_GAPS",
  "privacy_class": "SYNTHETIC",
  "producing_component": "corpus_intelligence",
  "producing_component_version": "<triana_labs version>",
  "schema_version": 1,
  "trace_count": 0
}
```

The five artifact digest values hash their exact bytes. `clusters.json` has
exactly `artifact_kind: corpus_clusters`, `clusters`, `cluster_count`,
`fidelity`, `input_manifest_hash`, `schema_version`, and `trace_count`.

Each asset index has exactly `artifact_kind`, `asset_kind`, `assets`,
`derivation_state`, `fidelity`, `input_manifest_hash`, `reason_code`,
`schema_version`, and `support_count`. It uses
`artifact_kind: derived_asset_index`, one `asset_kind`
from `PERSONA | INTENT | TURN_POLICY`, `derivation_state: NOT_DERIVED`, empty
`assets`, support count zero, and reason
`SEMANTIC_EVIDENCE_NOT_DERIVED`. These are explicit gaps, not placeholder
assets.

`derivation_report.json` has exactly `artifact_kind`, `cluster_count`,
`fidelity`, `gap_codes`, `gap_count`, `input_count`, `input_manifest_hash`,
`outcome`, `schema_version`, `singleton_cluster_count`,
`source_rejection_count`, `supported_cluster_count`, and `trace_count`. Its kind
is `corpus_derivation_report`, outcome is `COMPLETED_WITH_GAPS`, and it carries
these sorted gap codes:

```text
DISTRESS_NOT_EVALUATED
LANGUAGE_NOT_EVALUATED
SEMANTIC_ASSETS_NOT_DERIVED
SOURCE_REJECTIONS_PRESENT  # only when rejected_count > 0
```

## 6. CLI, refusal, and partial behavior

- Completed structural derivation: exit 10, output exists, stdout has exactly
  `cluster_count`, `gap_count`, `manifest_path`, `outcome`, and `trace_count`.
  Stderr has exactly `cluster_count`, `command: corpus.derive`, nonnegative
  `duration_ms`, `event_name: triana.corpus.derive.completed_with_gaps`,
  `gap_count`, `outcome: COMPLETED_WITH_GAPS`, `reason_code: null`,
  `service: triana-labs-cli`, current `service_version`, `severity: INFO`, and
  `trace_count`. It has no path, trace ID, tool name, content, hash, or
  exception.
- `--help`: exit 0, human help on stdout, no terminal event.
- Fatal refusal has empty stdout, no output, and exactly one stderr event with
  `command: corpus.derive`, nonnegative `duration_ms`, `event_name:
  triana.corpus.derive.rejected`, `outcome: REJECTED`, the closed `reason_code`,
  service/version, and `severity: ERROR`. It has no counts or unsafe values.
- Output write failure: exit 7. Unexpected failure: exit 70. Neither emits raw
  values or a partial target.
- Existing output is exit 2 and never overwritten or merged.

Closed fatal reasons:

```text
CLI_USAGE_ERROR
INPUT_READ_FAILED
INPUT_TOO_LARGE
MANIFEST_INVALID
UNSUPPORTED_PRIVACY_CLASS
CORPUS_INTEGRITY_FAILED
EMPTY_CORPUS
OUTPUT_ALREADY_EXISTS
OUTPUT_PARENT_MISSING
OUTPUT_WRITE_FAILED
INTERNAL_INVARIANT_FAILED
```

Exact exit mapping:

```text
2  CLI_USAGE_ERROR, INPUT_READ_FAILED, OUTPUT_ALREADY_EXISTS,
   OUTPUT_PARENT_MISSING
3  INPUT_TOO_LARGE
4  MANIFEST_INVALID, UNSUPPORTED_PRIVACY_CLASS
5  CORPUS_INTEGRITY_FAILED, EMPTY_CORPUS
7  OUTPUT_WRITE_FAILED
70 INTERNAL_INVARIANT_FAILED
```

`MANIFEST_INVALID` covers manifest byte/JSON/depth/closed-schema failures.
Oversized manifest or sibling artifacts use `INPUT_TOO_LARGE`. Once a valid
manifest names a sibling, its missing/nonregular/symlink state is corpus
integrity failure. Atomic write cleanup is tested on POSIX with an OS-level
`RLIMIT_FSIZE` child limit and ignored `SIGXFSZ`; no production injection seam
is added.

## 7. Authority and non-goals

Deterministic code owns parsing, integrity, membership, fingerprints, IDs,
support counts, ambiguity state, fidelity, lineage, serialization, hashes, and
exit state. No LLM or human semantic ruling is used. A human has not accepted
any cluster as a persona, intent, policy, failure, or product truth.

Explicitly absent: real/local-sensitive input; redaction; provider egress;
semantic labels; language/distress mining; Blitz/public corpus mining; persona,
intent, or turn-policy generation; Case Generator; Panel Builder; runner; F1;
report UI; SDK; OTel; hosted ingestion; changes to `triana-core` or LABS-01/02
artifact bytes.

## 8. Change budget and serial roles

Orchestrator only:

```text
internal/SLICE_PACKET.md
internal/DECISION_LOG.md
internal/WORKING_MEMORY.md
docs/ARCHITECTURE.md
README.md
triana-labs/scripts/verify.sh
triana-labs/tests/intelligence_adversarial/**
```

Independent test author only:

```text
triana-labs/tests/intelligence_acceptance/**
triana-labs/tests/intelligence_fixtures/**
```

Implementation author only after RED freeze:

```text
triana-labs/src/triana_labs/cli.py
triana-labs/src/triana_labs/intelligence/**
```

No dependency, package metadata, lockfile, existing test/fixture, Observer,
adapter example, `triana-core`, or suspended V1 change is allowed. Maximum
scope expansion without orchestrator return is none.

## 9. Independent acceptance

The test author independently creates synthetic Observer bundles and exact
expected bytes without importing production derivation code. Minimum matrix:

- exact structural fingerprints, clusters, IDs, ordering, counts, fidelity,
  lineage, manifest hashes, and typed semantic gaps;
- repeated-process byte determinism and line-order-independent memberships;
- singleton and supported clusters, tool errors, unmatched calls, missing and
  present terminal states, and case-generation eligibility;
- no semantic/raw content leakage into any output or safe terminal event;
- source-rejection gap and empty-corpus fatal refusal;
- manifest/profile/normalized hash, count, schema, duplicate-ID, and trace
  integrity failures;
- manifest/artifact symlinks, missing/nonregular/oversize input, invalid JSON,
  no-overwrite, atomic failure cleanup, and safe CLI errors;
- unchanged Observer/adapter behavior, prior 151 tests, frozen acceptance
  aggregates, and five canonical Observer hashes;
- source and clean-wheel command parity.

Valid RED means new tests fail only because `triana corpus derive` and the
`intelligence` package do not exist. The orchestrator freezes test commit and
aggregate before implementation begins.

### 9.1 Frozen acceptance evidence

Independent acceptance is frozen at commit `f731afe`. Its six test-owned files
contain 33 black-box cases. The independent author and Codex each reproduced
valid RED: all 33 fail solely because the command and packaged intelligence
module are absent, while the previous 151 tests pass.

The aggregate SHA-256 over sorted repository-relative `shasum -a 256` lines is:

```text
2f929a849362f471bf504b741ff2413016c1d3d6132f1a9c0e7073c4c81a77ae
```

Commit `f731afe` and this aggregate are the only acceptance freeze authorized
to judge implementation. Evidence root:
`/private/tmp/labs03-test-author.Avnprb`.

## 10. Reproducible exit gate

LABS-03 exits only when independent RED is frozen; implementation changes only
owned files; all new and prior tests pass; deterministic outputs match exact
independent bytes; adversarial safety and no-network checks pass; source and
clean-wheel commands match; the five Observer hashes and LABS-02 aggregates
remain unchanged; the diff and dependency budget reconcile; canonical docs
and decision log are current; and all non-goals remain absent.

Every role reports: what changed; why each file was necessary; budget
reconciliation; exact verification and artifacts; unverified work;
assumptions; unexpected findings; dependencies; deliberately excluded
problems; known risks; and human action required, using `none` explicitly.
