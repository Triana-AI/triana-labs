# Blitz Behavior Map conservation repair — deterministic before/after

Status: **private mechanical comparison; semantic benchmark remains human-blocked**

The accepted full Blitz DEVELOPMENT report remains the best accepted baseline:
`sha256:9c98854dba09a188600b5de7a6f20e71a86ea01791d61556e31f40f16fd1f021`.
Its JSON, Markdown, and HTML hashes remain unchanged. This repair does not
promote or replace it.

## Artifact lineage

| Role | Artifact | Identity |
|---|---|---|
| Accepted baseline | `/private/tmp/triana-blitz-full-development-corrected-final-20260808/report` | `sha256:9c98854dba09a188600b5de7a6f20e71a86ea01791d61556e31f40f16fd1f021` |
| Before projection | `/private/tmp/triana-blitz-coverage-repair-historical-projection-final-v5-20260808` | `sha256:4a31e882651e533254a71fb43bf2aafe87b026297dea056c0c377aa4c1729f6e` |
| Repaired projection | `/private/tmp/triana-blitz-pattern-conservation-repair-20260809-projection-v1` | `sha256:9ee02d4d5160b55d47e96e141dbb90f2b735007b98162ca28f94e8da8b0ade33` |
| Repeated replay | `/private/tmp/triana-blitz-pattern-conservation-repair-20260809-projection-v2` | byte-identical |

Both repaired replay JSON files hash to
`5918a71382294c466ea8b096f3b8071b0240d688336dc3967a5201d521cb7b63`.
Projection provider attempts are zero.

## Same-frontier mechanical movement

| Measure | Before | After | Interpretation |
|---|---:|---:|---|
| Corrected episodes | 405 | 405 | unchanged |
| Supported populations | 74 | 73 | one active disputed membership invalidated its population identity |
| Active assigned episodes | 210 | 208 | disputed member excluded; one co-member requires re-audit after identity change |
| Unpublished candidate populations | 3 | 4 | changed parent retained as candidate, not silently deleted |
| Re-audit-required candidate memberships | 8 | 9 | original eight preserved plus one changed-parent co-member |
| Preserved `AUDIT_DISPUTED` dispositions | 0 | 25 | predecessor dispute authority is no longer erased |
| Explicitly excluded active disputed edges | 0 | 1 | the reproduced 221/220 inconsistency is removed |
| Grounding replacements | 2 | 2 | unchanged |
| Grounding rejections | 1 | 1 | unchanged |
| Unexplained population-edge loss | 0 | 0 | hard gate passes |
| Historical supported patterns | 24 | 24 | unchanged by provider-disabled projection |
| Historical pattern support | 75 | 75 | unchanged by provider-disabled projection |

The after artifact accounts for the predecessor's 221 population edges as 208
exact active edges, 9 explicitly superseded candidate edges, 2 grounding
replacement exclusions, 1 grounding rejection, 1 audit-disputed exclusion,
and 0 unexplained edges. The apparent 210→208 movement is required by the
identity-and-audit contract; it is not evidence of semantic regression.

## Confirmed-defect matrix

| Defect | Evidence | Disposition |
|---|---|---|
| B1 successful-batch omissions | 77 supplied occurrences absent from successful responses | fixed: exact terminal omission custody |
| B2 foreign occurrence IDs | two observed plus synthetic hierarchy reintroduction | fixed: exact first-level and hierarchy-input rejection/counting |
| B3 unassigned reporting nested under generic labels | direct branch reproduction | fixed: ordinary unassigned projection is independent |
| B4 audit-missing pattern deletion | 67 candidate patterns lacked audits | fixed: retained missing/unpublished, zero active support |
| B5 conflated pattern metrics | candidate/audit/support counts previously shared | fixed: separate accounting including explicit uncertain audits |
| B6 non-lineaged 61→24 movement | preserved=0, superseded=0 | fixed: raw counts remain, semantic attrition language refused |
| B7 active membership/disposition mismatch | 221 active members versus 220 assigned | fixed: exact edge/cardinality publication gate |
| B8 disputed episode in support | one active population member was audit-disputed | fixed: removed before identity/support finalization |
| B9 historical dispute restoration | predecessor dispute became assigned | fixed: predecessor dispute persists absent current ruling |
| B10 incomplete pattern disposition contract | omissions, failures, candidates and disputes shared no exhaustive ledger | fixed: one terminal row per eligible occurrence plus duplicate refusal |

## Suspected issues deliberately not promoted

- S1: arbitrary batching can expose cross-batch semantic opportunity loss, but
  no human label proves the correct grouping. Mechanical disappearance is
  fixed; semantic regrouping is not forced.
- S2: population-first scheduling can starve pattern audits. Missing candidates
  now survive; scheduling policy is unchanged.
- S3: the existing hierarchy-abort preservation control is green; no silent
  loss was reproduced on that path.
- S4–S6: taxonomy regression, 80→77 population-quality loss, and lower quality
  among recovered conversations remain `HUMAN_LABELS_MISSING`.

## Claim boundary

No provider call or fresh semantic Blitz run occurred. Pattern-stage repairs
are proven by provider-disabled synthetic/checkpoint regressions, while the
real before/after artifact proves historical population/disposition repair.
Therefore this comparison establishes stronger deterministic integrity—not
better semantic taxonomy, higher quality, benchmark passage, or baseline
promotion.
