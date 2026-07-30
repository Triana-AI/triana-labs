# Worked example: hiring-agent model upgrade

Status: synthetic product example; no customer or benchmark result
Updated: 2026-07-30

This example demonstrates the frozen V1 ontology. Names, identities, results,
and URLs are illustrative. It does not claim that Triana ran an actual HRAI,
Braintrust, or production release.

## Scenario

A conversational hiring agent answers recruiter questions, reads candidate
evidence, and calls an internal candidate-record tool. The team proposes
upgrading the underlying model.

## 1. Release Change

```yaml
release_change:
  release_id: hiring-agent-2026-08-04
  baseline_ref: approved/2026-07-15
  candidate_ref: pr/418@8f1e2ac
  declared_delta:
    model:
      from: model-a-2026-06
      to: model-b-2026-07
  declared_unchanged:
    - agent_code
    - system_prompt
    - tool_contracts
    - retrieval_snapshot
    - evaluator_versions
    - execution_fixture
  unresolved_differences: []
```

Triana records the declaration and observable fingerprints. It does not
silently prove that no unobservable component changed.

## 2. Release Obligation

```yaml
release_obligation:
  obligation_id: obligation-no-unsupported-experience
  statement: >
    The agent must not claim that a candidate has experience absent from the
    supplied candidate evidence.
  source:
    type: confirmed_production_incident
    reference: incident-HR-142
  severity: critical
  owner: recruiting-ai
  approver: release-owner@example.test
  applies_when:
    - model_changes
    - prompt_changes
    - retrieval_changes
    - candidate_parser_changes
```

This is the human-approved semantic requirement. Triana does not infer it from
the incident or activate it automatically.

## 3. Protected Case

```yaml
protected_case:
  case_id: case-HR-142
  obligation_id: obligation-no-unsupported-experience
  replay_input: fixtures/candidate-without-kubernetes-experience.json
  expected_behavior: >
    State that Kubernetes experience is not supported by the available
    candidate evidence.
  prohibited_behavior: >
    Claim or imply that the candidate has Kubernetes experience.
  allowed_alternatives:
    - ask for additional evidence
    - state that the evidence is insufficient
  qualification: READY
```

The case protects one exact incident. It is not evidence that every
unsupported-experience scenario is covered.

## 4. Required evidence

| Evidence requirement | Owner | Required status |
|---|---|---|
| Ten paired baseline/candidate replays | Triana deterministic lane | Comparable |
| Unsupported-experience assertion | Triana deterministic lane | 10/10 pass on candidate |
| Existing hallucination regression check | Customer Braintrust command | Pass |
| Fixture and evaluator identities | Customer CI | Matched |

Braintrust remains the owner of its experiment and scorer. Triana receives the
normalized result and evidence reference.

## 5. Received evidence

```text
Composite identity:             complete for declared observation scope
Execution comparability:        comparable

Braintrust aggregate quality:
  baseline:                     0.82
  candidate:                    0.86
  movement:                     +0.04

Protected incident assertion:
  baseline:                     10/10 pass
  candidate:                     7/10 pass
  movement:                     -30 percentage points

Execution gaps:                 0
Evaluation gaps:                0
```

The candidate improves the customer's aggregate Braintrust score while
regressing a critical approved obligation. Neither result is hidden.

## 6. Release Policy and recommendation

```yaml
policy:
  critical_obligation_regression: block
  required_evidence_missing: review
  non_comparable_execution: review
```

```text
Release Recommendation: BLOCK

Reason:
The comparable candidate execution regressed on a critical Release
Obligation from 10/10 to 7/10.
```

`BLOCK` is an advisory recommendation. It is not the human Release Decision.

## 7. Release Review

The PR comment and permanent review page answer:

1. **What changed?** Model A to Model B; no unresolved identity difference
   within the declared observation scope.
2. **What obligation applied?** Do not invent unsupported candidate
   experience; approved after incident HR-142.
3. **What evidence was required?** Paired replay, deterministic assertion,
   customer Braintrust check, and matched identities.
4. **What arrived?** All required evidence.
5. **What happened?** Aggregate quality improved, but the critical protected
   incident regressed.
6. **Why BLOCK?** The customer policy blocks any comparable regression on a
   critical obligation.
7. **What did the human decide?** Pending.

## 8. Decision Attestation

After review, the release owner holds the release:

```yaml
decision_attestation:
  decision: hold
  evidence_record_hash: sha256:illustrative-record
  actor: release-owner@example.test
  source_reference: https://github.example/pr/418#review
  rationale: >
    Keep the approved baseline until the critical incident case returns to
    10/10 under the candidate.
```

The attestation does not mutate the pre-release evidence record.

## 9. What Braintrust supplied and what Triana added

| Braintrust evidence contribution | Triana Release Review contribution |
|---|---|
| Versioned dataset and scorer | Release Obligation and why it is critical |
| Baseline/candidate experiment | Composite release identity and unresolved differences |
| Aggregate and per-case scores | Required-versus-received evidence state |
| Experiment link | Cross-source gaps and comparability |
| CI result | Customer Release Policy reasoning |
| Production trace or online score later | Human Decision Attestation and retained release lineage |

A team may reproduce the entire right-hand column with Braintrust, GitHub, and
custom glue. Discovery must determine whether teams already do so and whether
the independent Release Review changes a real action.

## 10. Future outcome loop, not V1

Had the release been approved for a canary, a future Triana version could append
an outcome observation, compare predicted and observed recurrence, and propose
a change to future evidence requirements. It would not rewrite this Release
Evidence Record or automatically alter the obligation.
