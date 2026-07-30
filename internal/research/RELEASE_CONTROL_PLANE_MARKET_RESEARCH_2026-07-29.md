# Can a vendor-neutral release control plane for AI agents be a standalone company?

Research date: 2026-07-29. Method: 13 parallel research agents over primary sources
(vendor docs, GitHub repos, changelogs, pricing pages, press). Marketing claims
separated from documented behavior throughout. Full per-platform reports with all
citations live in the session task outputs; this document is the synthesis.

## 0. End-to-end release lifecycle, and where the empty layer sits

```mermaid
flowchart LR
  subgraph commodity_below["Commodity below (every eval vendor)"]
    T[Prod traces] --> D[Prod-to-dataset conversion] --> M[LLM-judge and code metrics]
  end
  subgraph empty["EMPTY MIDDLE LAYER (verified: nobody ships this)"]
    RI[Composite release identity<br/>code+prompt+model+tools+harness] --> RS[Versioned Release Replay Set]
    RS --> OX[Orchestrate CUSTOMER harness + any evaluator<br/>in customer infra]
    OX --> CMP[Baseline vs candidate<br/>distribution over N runs]
    CMP --> POL[Versioned Release Policy] --> V{PASS / REVIEW / BLOCK}
    V --> EV[Immutable evidence record<br/>dataset v + evaluator v + policy v + approvals]
    EV --> ATT[Compliance attestation<br/>EU AI Act 43-4 + 72, SR 11-7]
  end
  subgraph commodity_above["Commodity above (delivery incumbents)"]
    GH[GitHub required check /<br/>deployment protection rule]
    AR[Argo analysis / rollback]
    LD[LaunchDarkly flags / guarded rollout]
  end
  M --> RS
  V --> GH & AR & LD
  T -. Art. 72 continuous monitoring .-> POL
```

---

## 1. Competitor matrix (documented behavior, not marketing)

Legend: ✅ Yes · 🟡 Partial · ❌ No. "Partial" noted inline where the nuance matters.

| Capability | GitHub | Harness | LaunchDarkly | Argo Rollouts | AWS (SageMaker+AgentCore) | Google (GEAP/Vertex) | Datadog | Braintrust | LangSmith | DeepEval/Confident | Langfuse |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. Prod trace ingestion (LLM/agent) | ❌ | 🟡 AgentTrace, launch-week | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2. Prod→dataset conversion | ❌ | 🟡 unverified | 🟡 script/manual | ❌ | 🟡 manual curation | ✅ | ✅ one-click | ✅ manual trigger | ✅ manual + rules | ✅ rule-based | 🟡 manual only |
| 3. Automatic dataset maintenance | ❌ | ❌ | ❌ | ❌ | ❌ | 🟡 scores only, no dataset | 🟡 Automations (20k cap, read-only) | 🟡 scores traces, doesn't append | ✅ polling rules | 🟡 auto after rule setup | ❌ |
| 4. Custom evaluator import | 🟡 prompt-judge only | 🟡 "scoring functions" | ❌ LLM-judge UI only | ✅ any container, exit-code only | ✅ Lambda py/js | ✅ CustomMetric py | ✅ scores API | ✅ SDK-shaped | 🟡 sandboxed UI / SDK in CI | ✅ Python BaseMetric | 🟡 hosted sandbox / insecure-local |
| 5. External evaluator orchestration | 🟡 generic CI compute | ✅ claims DeepEval integration | ❌ | 🟡 Web/Job provider, thin | 🟡 3rd-party DIY | ❌ | ❌ ingestion-only | 🟡 remote evals (own contract) | ❌ (no-internet sandbox) | ❌ own SDK only | ❌ Scores API ingestion-only |
| 6. Baseline/candidate comparison | 🟡 side-by-side UI | ✅ | ✅ guarded rollouts (online) | 🟡 Kayenta, numeric | ✅ batch + A/B (Jun 2026) | 🟡 models yes, agents no | 🟡 disconnected products | ✅ experiment diff | ✅ | ✅ A/B regression | ✅ via CI action |
| 7. Candidate executes in customer infra | ✅ self-hosted runners | ✅ Delegate | ✅ (SDK by design) | ✅ (by construction) | ❌ AWS-managed compute | 🟡 ADK portable; runtime Google-managed | ❌ observer only | ✅ remote evals | 🟡 pytest path / hybrid Enterprise | ✅ (SDK by nature) | ✅ webhook trigger |
| 8. Release policies (codified gate decision) | ✅ generic checks | ✅ OPA/Rego + AI Evals gates | 🟡 advisory only | ✅ metrics-shaped | 🟡 model layer yes; agent DIY | ❌ DIY assertions | 🟡 pass/fail, no eval rule type | 🟡 no threshold input in action | ❌ DIY glue | 🟡 new Governance, thin | 🟡 DIY RegressionError |
| 9. Approvals / change management | ✅ required reviewers | ✅ Jira/ServiceNow | ✅ flag approvals | ✅ pause/promote | 🟡 model layer only | 🟡 action-level HITL | 🟡 | ❌ | ❌ | 🟡 prompt PRs only | ❌ RBAC ≠ approval |
| 10. GitHub/deploy gates on eval results | ✅ (rails, not eval-aware) | 🟡 | ❌ annotations only | 🟡 deploy gate, no PR gate | 🟡 sample code only | 🟡 pattern, not product | 🟡 no LLM rule type | 🟡 DIY Reporter | 🟡 pattern repo | ✅ assert_test exit code | ✅ experiment-action |
| 11. Shadow / canary for agents | ❌ | ✅ to Bedrock/Google runtimes | ✅ online guarded rollouts | ✅ generic traffic | ✅ shadow (models) + A/B (agents) | ✅ runtime traffic split | 🟡 generic flags | ❌ | ❌ | ❌ | ❌ explicitly disclaimed |
| 12. Automatic rollback | ❌ | 🟡 fragmented (artifact vs prompt) | ✅ guarded rollout | ✅ | ✅ models / 🟡 agents | ❌ alert-only | ✅ flag circuit breakers | ❌ | 🟡 manual revision rollback | ❌ | 🟡 prompt label repoint |
| 13. Release evidence history (composite record) | ✅ generic deploy audit | ✅ claimed single audit trail | ✅ audit log | 🟡 K8s objects | 🟡 lineage (models) | 🟡 pieces, unstitched | 🟡 | ❌ | 🟡 pieces, no release object | 🟡 pieces, no ledger | ❌ |
| 14. BYOC / self-hosted / regulated | ✅ GHES + runners | 🟡 platform yes; Agent DLC unverified | 🟡 cloud-only control plane | ✅ maximal | ❌ agent layer | 🟡 GCP-contained, not BYOC | ❌ (CloudPrem logs-only) | ✅ Enterprise | ✅ Enterprise | ✅ Enterprise | ✅ MIT OSS |

### The universal gaps (rows nobody fully owns)

Across all 11 platforms, four capabilities are absent everywhere as shipped product:

1. **Composite release identity.** No platform versions the agent as one addressable
   unit (code + prompt + model + tools + retrieval + policies + harness). AWS has
   four separate versioning systems (Agents/Flows/Prompts/Guardrails), LangSmith
   versions prompts and deployments independently, Braintrust versions prompts,
   datasets and experiments in silos. Nobody hashes the composite.
2. **Immutable release evidence record.** No object anywhere binds
   {dataset version + evaluator version + policy version + approvals} → decision.
   Verified gap in LangSmith, Langfuse, Braintrust, Confident AI, AWS, Google,
   Datadog docs explicitly.
3. **Release approval state machine at the agent layer.** SageMaker has
   `ModelApprovalStatus` for model artifacts; nothing equivalent exists for agents
   anywhere. Braintrust docs: "delegates promotion decisions entirely to users."
4. **Vendor-neutral external-evaluator orchestration.** Every vendor is either
   "push scores into us" (Langfuse, Datadog) or "write code inside our SDK shape"
   (DeepEval, Braintrust, LangSmith). Nobody invokes another vendor's evaluator or
   a customer's arbitrary harness as a first-class orchestrated citizen. Harness
   *claims* DeepEval integration (launch week, unverified depth).

### The marketing-vs-reality findings worth remembering

- **Braintrust**: `/articles/*` claims eval-action "blocks merges when scores fall
  below thresholds." The actual GitHub Action has **no threshold input** — it exits
  non-zero only on exceptions. Score gating = customer writes a custom Reporter.
- **LaunchDarkly**: "Release policies" are advisory — non-compliant configs show a
  "recommended" label and members "can continue without adopting."
- **GitHub**: `gh-models` README self-describes as "not designed for production
  use cases."
- **Harness Agent DLC** (launched 2026-07-21): zero customer proof of the
  end-to-end loop; primary docs pages returned empty at research time; IDC analyst
  on record that individual features are "not especially differentiated."
- **Zero enforced-gate case studies anywhere.** Not one named customer was found,
  across all 11 platforms, publicly gating agent deploys on eval results. All
  customer quotes are dashboards/experiments. The category is pre-adoption.

---

## 2. Per-platform absorption risk summary

| Platform | Risk | Time-to-absorb the missing layer | Structural stop |
|---|---|---|---|
| Harness | **HIGH** — shipped the concept 2026-07-21 | 0 (concept), 2–4 quarters (substance) | Eval/dataset depth; framework credibility with AI teams; rollback fragmentation |
| LaunchDarkly | HIGH (online gate) / LOW-MED (offline CI gate) | Already shipped online side | No dataset/replay DNA; no custom-code evaluators; cloud-only control plane |
| LangSmith | HIGH | 1–2 quarters (composition of existing primitives) | Neutrality (LangGraph-shaped runtime); sandbox can't call external vendors |
| Braintrust | HIGH | 1–2 quarters (policy) / 2–4+ (traffic) | Chose not to be gatekeeper; single-vendor evals; $80M B war chest says intent |
| Confident AI | MED-HIGH | 2–4 quarters | Python SDK lock-in is the business model; no traffic layer; 8 people |
| Langfuse (ClickHouse) | MED-HIGH | 6–9 months if prioritized | GTM is observability-led; explicitly won't split traffic |
| AWS AgentCore | MED-HIGH (policy layer) | 12–24 months | No BYOC execution (hard architectural conflict); 4 siloed version systems |
| Google GEAP | MED | 12–24 months | GCP-locked; orchestrating rivals' evaluators conflicts with incentives |
| Datadog | MED | eval rule type = cheap; execution = never | Deliberately avoids executing customer code (Bits Release is human-in-loop by design); no BYOC for traces |
| GitHub | MED | shallow gate cheap; substance far | No trace/dataset/eval DNA; is the rail, not the brain |
| Argo Rollouts | LOW-MED | n/a (OSS plumbing) | No SaaS, no data layer; integration target, not competitor |

Reading: the gate *mechanics* (thresholds → block, approvals, rollback) are cheap
everywhere and already commoditizing. The gate *substance* — trustworthy replay
datasets from production, orchestration of the customer's real harness, composite
identity, evidence — is nowhere, and it is the only part that is hard.

---

## 3. Base rates: which release-lifecycle stages ever became companies

| Stage | Category-definer | Standalone outcome | Why |
|---|---|---|---|
| Source / change identity | GitHub, GitLab | **Company** (GitHub → MSFT $7.5B) | Daily habit + irreplaceable history + network effect |
| Build + artifact registry | JFrog, Docker Hub | **Partial** (JFrog public, $531.8M rev; Docker enterprise sold) | Binary data gravity, but clouds bundle free registries |
| CI test execution | CircleCI, Travis | **Collapsed into platform** (GitHub Actions won) | Trigger is a git event; source host owns the run |
| Security scanning | Snyk | **Company** ($326M ARR, Feb 2026) | Distinct buyer (security budget) + proprietary vuln DB |
| Staging / previews | Vercel, Netlify | **Feature** | Zero data gravity; sells hosting |
| Approvals / change mgmt | ServiceNow | **Company, but not a release tool** | Control point = enterprise system of record, sold to IT/GRC |
| Feature flags | LaunchDarkly / Split | **Split outcome** (LD ~$200M ARR, $3B val; Split → Harness 2024) | Only stage that stays live AFTER deploy: runtime control point + event data gravity |
| Progressive delivery | Spinnaker, Argo Rollouts | **Collapsed hardest** (Armory assets → Harness, ~$7M) | Commodity mechanism, no data, no distinct buyer |
| **Continuous verification** | Kayenta (Netflix/Google) | **Never a company — not once in ~8 years** | ← direct analog of "release gate" |
| Promotion & rollback | — | Feature of the CD tool | No separable surface |
| Audit / compliance evidence | Vanta, Drata | **Company** | Distinct buyer + auditor forcing function + evidence corpus |

**Rule extracted:** a release-stage tool sustains a company only with at least one of
(1) a runtime control point that stays live after deploy, (2) a distinct buyer with
an external forcing function, (3) accumulated data the customer can't recreate.
"A step that runs once at deploy time" collapsed into platforms without exception.

**The uncomfortable one:** continuous verification — fetch metrics, run statistical
tests, score, promote-or-block — is conceptually this product, and it produced zero
standalone companies. Any thesis must name which of the three survival properties it
claims instead.

**Demand-side signal (pro-thesis):** DORA 2025 renamed itself the "State of
AI-assisted Software Development" and reports AI adoption correlates with higher
throughput AND higher instability (more change failures, more rework). The
industry's measurement standard formally acknowledges AI ships faster and breaks more.

## 4. MLOps lesson: model release gating never became a company

- **Zero examples** of a standalone "ML release gating" company. The reference
  implementation — MLflow Model Stages (None→Staging→Production→Archived) — was
  **deprecated by its own maintainers** (MLflow 2.9+) as too rigid for real
  workflows, replaced by free-form aliases/tags.
- Exits went to whoever owned **compute or the model**, not to tooling: W&B →
  CoreWeave ($1.4B, 2025); Neptune → OpenAI (product sunset Mar 2026); Aporia →
  Coralogix; WhyLabs discontinued operations. The wave's ceiling was experiment
  tracking (daily habit + run history), not gating.
- Survivors survived by **pivoting to the agent era** (Arize's $70M Series C is an
  LLM/agent-observability round, not an ML-monitoring round).
- Google's ML Test Score (2017) — 28 production-readiness tests, a quantified
  rubric — became widely cited and produced zero dollars of product.

## 5. What is genuinely different about agent releases (evidence-ranked)

**Strong evidence:**

- **Stochastic multi-step behavior.** τ-bench pass^k: SOTA agents <50% pass^1,
  <25% pass^8 (retail). "Beyond pass@1" (arXiv 2603.29231, Mar 2026; 23,392
  episodes): degradation score falls 0.90→0.44 with task length; meltdown rates up
  to 19%; capability and reliability rankings diverge. Implication: the unit of
  release evidence is a **distribution over N runs vs a baseline distribution**
  (Kayenta-style statistics), not a pass/fail unit test. Ordinary CI cannot express
  this. Cost of N×k×judge runs per release is a real constraint.
- **Harness belongs in version identity.** Harness-Bench (arXiv 2605.27922):
  23.8-point spread between best and worst harness at identical model and task.
  Capability must be reported as model–harness configurations. Nobody versions this
  composite; nearest standards (CycloneDX ML-BOM, SPDX AI profile, Agent-BOM
  GitHub issue) are procurement inventories, not gate-diffable hashes.
- **Human authority is becoming law.** EU AI Act high-risk obligations apply from
  **2026-08-02** (this week). Art. 14: humans must be able to detect anomalies and
  degradation. Art. 43(4): substantial modification triggers a new conformity
  assessment — **except changes pre-declared and documented at initial assessment**.
  That carve-out is a direct legal incentive for a declared change envelope plus an
  attestation record proving each release stayed inside it. Art. 26(6): ≥6-month
  log retention. Art. 72: mandatory active post-market monitoring plan — a legal
  mandate for the production-feedback loop.
- **Replay is hard for a specific reason.** The tractable split: record LLM
  *decisions* (cassettes: vcr-langchain, Docker cagent), re-run *executions*.
  Benchmarks (Terminal-Bench 2.0/Harbor, τ²-bench) achieve reproducibility by
  owning the entire environment — which is exactly what does not transfer to a
  customer's production agent talking to their CRM/payments/DB. Every vendor's
  replay story stops at the LLM boundary. Whoever solves customer-side bounded
  replay owns something real.

**Weak evidence (honesty required):**

- **"Custom evals dominate / generic metrics fail"** — vendor marketing only; no
  strong peer-reviewed source found. And a counter-paper: "Lost in Simulation"
  (arXiv 2601.17087) shows LLM-simulated users are unreliable proxies — a validity
  ceiling on simulation-based gating itself.
- **Privacy/execution-location requirement** — plausible, but no survey quantifies
  it; supported only indirectly (self-hosted tiers exist; EU log-retention rules).
  Treat as an assumption to test, not a finding.
- **Prod-failure→test-case conversion is already commoditized** (LangSmith rules,
  Langfuse one-click, Confident auto-ingest). Defensibility must sit above the
  conversion: the authority to block, the accumulated corpus, or the attestation
  record.

---

## 6. Emerging startups and buyer economics

### 6.1 The agent-release startup landscape (mid-2026)

| Company | Funding | What they ship | Distance from release control plane |
|---|---|---|---|
| Coval | $28M A (Jun 2026, Norwest) | Voice-agent Simulate→Observe→Review loop, CI integration, 60+ orgs, enterprise from $4,500/mo | Closest shipping loop; voice-shaped, no policy object, no evidence artifact |
| Patronus AI | $50M B (Jun 2026) | **Pivoted to RL training environments for labs** | Vacated the enterprise release-gate position entirely |
| Okareo | unverified | Best-documented "escaped failure → next PR" loop; CI gating in nav (depth unverified) | Closest loop semantics; voice-heavy, no policy/evidence object |
| Distributional | $19M A (Oct 2024; no round since) | Statistical testing, VPC/single-tenant deployment | Solved the procurement wedge, no loop; 21-month funding gap |
| Hamming | $4.5M seed | Voice testing tied to release workflow | Right shape, narrow, under-capitalized |
| Humanloop | **DEAD** — Anthropic acqui-hire Aug 2025, platform shut down Sep 2025 | — | Live proof eval-platform buyers get burned by vendor disappearance → argument for customer-infra execution + neutrality |
| Arize AX | $70M C | Agent feedback loop: detect→investigate→test→improve; dataset curation agents | Most direct threat to the trace→dataset half; weak on blocking gates |

**Nobody — startup or incumbent — ships the full chain.** Three specific gaps
recur across every player: (a) a versioned release **policy as a first-class
object** you can diff, review, roll back; (b) **BYO-executor orchestration** where
the customer's harness runs and the vendor only orchestrates and records; (c) a
**PASS/REVIEW/BLOCK decision with an evidence bundle** as the product output
rather than a dashboard.

Signal to hold with both hands: the most-funded simulation company (Patronus)
walked away from this position — either it is whitespace, or a revealed preference
that the gate is the worse business.

### 6.2 Buyer economics

- **Economic buyer:** VP/Head of AI Platform Engineering (reports CTO), with a
  cross-functional governance council (eng, legal, compliance). Compliance
  co-signs; it is not the buyer.
- **Daily user:** application/agent engineers — not a QA org (ZenML, 1,200+
  deployments: engineering teams own eval work). Coval's unlimited-seats pricing
  corroborates: value is not in seats.
- **Budget displaced:** manual QA review (59.8% of teams evaluate by human review)
  and internal-build cost (~6–10 eng-weeks + 10–15% of an engineer ongoing).
  **There is no existing "agent release" budget line item.** That is both the risk
  (nothing to displace) and the opportunity (category creation).
- **Build-vs-buy evidence is strong and double-edged.** Ramp built exactly this
  loop internally: user failures → regression datasets → golden sets → shadow mode
  on real transactions before enabling live actions. GitHub, DoorDash, Cox built
  their own. Validates the primitive; also shows sophisticated teams choose build.
- **Implementation burden objection #1:** framework-coupled re-instrumentation.
  Vendors now compete on "no re-instrumentation" (Arize), which reveals the
  objection. Supports trace-adapter-first, SDK-last design.
- **Procurement:** "runs in your VPC" is **table stakes in 2026**, not a
  differentiator — Braintrust ships a certified split-plane (data plane in
  customer VPC), HoneyHive BYOVPC on 5 k8s flavors, Distributional single-tenant.
  The bar that still discriminates: certification covering the self-hosted
  deployment itself, and SR 11-7-style model-risk audit trails in banks.
- **Pricing:** four observed units — sim-minutes (Coval), scores (Braintrust),
  seats+traces (LangSmith), spans (Galileo). **Nobody prices per release
  decision.** No comparable, no anchor; enterprise floor in this category is
  ~$54K ACV (Coval).
- **Timing:** LangChain State of Agent Engineering (n=1,340, Dec 2025): 57.3% have
  agents in production (67% at 10k+ employee firms); quality is the #1 barrier
  (32–33%); **89% have observability but only 52.4% run offline evals; 22.8% of
  production teams don't evaluate at all**; 75%+ run multiple models (supports
  neutrality). The survey contains no release-gating questions at all — the
  practice is too immature to be surveyed. Lyft rebuilt evals from production
  verbatims after synthetic users failed (validates prod-replay); **Chime moved
  compliance from a release gate to continuous co-authoring** — a direct challenge
  to gate-shaped products that Section 8 addresses.
- **Failure-incident evidence is weak. Do not pitch on it.** The circulating "74%
  of agents rolled back" stat traces to an unnamed survey on a Medium post —
  unusable. One solid public postmortem exists (Replit DB deletion, Jul 2025,
  gate-shaped remediation). Lead with the adoption/eval gap and Ramp/Lyft build
  evidence instead.

---

## 7. Three company theses, tested

### Thesis A — Production Replay Dataset company
- **Control point:** the continuously maintained, reviewable replay dataset.
- **Verdict: NOT a standalone company.** The conversion primitive is already
  commoditized: LangSmith automation rules (unattended), Confident AI auto-ingest
  (Apr 2026), Datadog Automations, Okareo's loop, Langfuse one-click. Datasets
  alone have no blocking authority, no distinct buyer, no forcing function.
- **Kill criterion (already met):** ≥3 funded vendors ship rule-based
  prod→dataset. Keep the capability as the *fuel*, not the company.

### Thesis B — Vendor-neutral release evidence + policy system of record
- **Control point:** the versioned Release Policy + the immutable evidence record
  (dataset version + evaluator versions + policy version + approvals → decision)
  + orchestration of the customer's own executor and any evaluator, executed in
  customer infrastructure. The verdict surfaces as a GitHub required check /
  deployment protection rule / Argo analysis endpoint — riding existing rails.
- **Survival properties claimed (per Section 3 rule):**
  - (2) distinct forcing function: EU AI Act Art. 43(4) pre-declared change
    envelope + Art. 72 post-market monitoring (live 2026-08-02); SR 11-7 in banks.
  - (3) data gravity: the accumulated release-evidence corpus and baseline
    distributions become the customer's audit history — Vanta-shaped, not
    Kayenta-shaped. The product is a **system of record that happens to gate**,
    not a pipeline step.
- **Incumbent substitution risk:** highest of any risk. LangSmith/Braintrust can
  compose a policy layer in 1–2 quarters; Langfuse in 6–9 months; Harness already
  shipped the branding. **What they structurally cannot do:** be neutral
  (orchestrating a rival's evaluators is a business-model conflict for every eval
  vendor; 75% of buyers are multi-model/multi-stack), and orchestrate harnesses
  outside their SDK shape (their stickiness *is* the SDK).
- **Defensibility:** neutrality + evidence corpus + regulatory mapping. Weak until
  a customer lets the verdict block; strong after two quarters of accumulated
  release history that an auditor has accepted.
- **Expansion path:** evidence record → policy library per vertical → compliance
  packets → promotion/rollback triggers via existing delivery rails → Thesis C.
- **Gross-margin risks:** N-run × k-case × judge-call replay compute per release
  (mitigated: customer-infra execution puts compute on the customer's bill —
  Triana's $0/deterministic default is the right instinct); per-partner harness
  adapters drifting into services.
- **Services burden:** the real danger. Each custom harness is an integration.
  Mitigation is a hard adapter contract + measured time-to-first-verdict.
- **Minimum product:** trace adapters (OTel GenAI first) → Replay Set versioning →
  run-your-harness orchestration → baseline/candidate distribution comparison →
  versioned policy → PASS/REVIEW/BLOCK verdict as a GitHub check → immutable
  evidence page. No dashboards beyond the evidence page.
- **Strongest kill criterion:** no design partner will let the verdict block a
  release (even after an advisory trust period) → it is Kayenta, a feature.

### Thesis C — Full agent progressive-delivery and rollback platform
- **Control point:** the live traffic path.
- **Verdict: NOT now.** LaunchDarkly AgentControl (May 2026) and Harness Agent DLC
  (Jul 2026) already occupy the online side with mature stats engines and
  auto-rollback; Datadog flags ship circuit breakers; AWS shipped agent A/B
  testing. Entering the serving path is a different architecture, a different
  buyer conversation, and a war against funded incumbents on their home turf.
- **Correct move:** *integrate* — emit promotion/rollback decisions that
  LaunchDarkly flags, Argo analysis, and Harness pipelines execute. Own the
  decision and its evidence, never the traffic.
- **Kill criterion if attempted:** time-to-parity with LaunchDarkly's sequential
  testing engine measured in years, not quarters.

**The feature-versus-company boundary, stated plainly:**
below Triana sits the commodity (trace capture, prod→dataset conversion, LLM-judge
metrics — every vendor has these); above Triana sits the other commodity (traffic
splitting, flags, rollback mechanics — Argo/LaunchDarkly/Harness own these). The
only defensible standalone layer is the middle: **neutral orchestration of
customer-owned execution + versioned policy + the immutable evidence record**.
A company exists there only if the verdict acquires blocking authority and the
evidence corpus acquires audit acceptance. Otherwise it is a feature of whichever
neighbor gets there first.

---

## 8. Verdict (one page)

**Question:** standalone venture-scale company, or feature of eval/observability/
CI-CD platforms?

**Answer: conditionally standalone — as Thesis B only, and the window is 2–4
quarters.** The unconditional version of the thesis is refuted by three
independent lines of evidence: the closest historical analog (continuous
verification) produced zero companies in eight years; the MLOps reference
implementation of release gating was deprecated by its own maintainers; and every
adjacent vendor has shipped, or can cheaply ship, the gate *mechanics*. Harness
literally shipped the branding eight days before this research.

What keeps the standalone case alive — and it is a real case, not a consolation:

1. **The middle layer is empty and hard.** Across 11 platforms and 5 startups,
   nobody ships composite release identity, an immutable evidence record, a
   release approval state machine, or neutral orchestration of external
   evaluators/harnesses. These are the four verified universal gaps, and they are
   the four things Triana's wedge is made of.
2. **The two absorbers have structural conflicts, not just backlogs.** Eval
   vendors cannot orchestrate rivals' evaluators or non-SDK harnesses without
   dissolving their own lock-in. Delivery platforms (Harness) have the gate but
   not the eval substance, and analyst consensus says their parts are undifferentiated.
3. **A forcing function arrives this week.** EU AI Act Art. 43(4) + 72 (applicable
   2026-08-02) legally rewards exactly a pre-declared change envelope plus
   attestation that each release stayed inside it — the Vanta-shaped buyer
   dynamic, which is one of only three patterns that ever made release-stage
   tools into companies.
4. **The demand gap is quantified.** 89% observability vs 52% offline evals, 22.8%
   of production teams not evaluating at all, quality the #1 barrier, and teams
   like Ramp/Lyft/GitHub building the loop internally because nothing sells it.

**On the user's framings:** "GitLab for agent release" — no; GitLab won by
bundling everything, and Triana cannot out-bundle Harness. "Composio for agent
release" — yes; adapters over everyone's existing traces, harnesses, evaluators,
and delivery rails, owning only the decision and its evidence, is precisely the
shape the evidence supports. The Chime pattern (compliance co-authoring
continuously, not reviewing at a gate) is not a threat to this shape — it is the
roadmap: the policy object must be evaluated continuously against production
(Art. 72) with the release verdict as one checkpoint in a standing record, not a
terminal toll booth.

**What Triana must own that Braintrust, LangSmith, and Harness do not:**
1. **Composite release identity** — a diffable hash of code + prompt + model +
   tools + retrieval + policy + harness (Harness-Bench: 23.8 points of behavior
   live in the harness alone; nobody versions it).
2. **The immutable evidence record** binding dataset version + evaluator versions
   + policy version + approvals to each PASS/REVIEW/BLOCK decision.
3. **Orchestration of the customer's own executor** in the customer's
   environment, with a thin contract — not an SDK the agent must be rewritten
   into. (Braintrust remote evals is the nearest rival primitive; it still
   requires Braintrust's contract and evaluator model.)
4. **Neutral multi-evaluator orchestration** — running DeepEval, Braintrust
   scorers, and the customer's bespoke judges in one gated run. Structurally
   unavailable to every eval vendor.
5. **The regulatory attestation mapping** (EU AI Act change envelope, SR 11-7
   evidence) compiled from #1–#4.

**What would falsify this within 90 days** (any one is close to fatal):
- 10+ non-leading interviews with production agent teams and no one describes
  pain between "evals ran" and "we shipped" — or DIY CI glue is universally
  "good enough."
- No design partner grants blocking authority even after a 30-day advisory
  (shadow-verdict) period.
- Onboarding a real custom harness takes weeks per team despite the adapter
  contract — the services trap, meaning it is consulting, not product.
- Braintrust or LangSmith ships a versioned policy object + evidence record with
  a named customer gating deploys on it.
- Zero budget motion from EU AI Act Art. 43(4)/72 among regulated prospects by
  Q4 2026 — the forcing-function leg fails, leaving only Kayenta economics.

---

## 9. Wedges, experiments, questions, roadmap

### 9.1 Three wedges, ranked

| Rank | Wedge | Defensibility | Speed | Note |
|---|---|---|---|---|
| 1 | **Custom-harness orchestration + evidence record**: "keep your executor and your evals; we run them against a versioned Replay Set in your infra and emit a policy verdict as a GitHub check, with an immutable evidence page" | High — business-model conflict for eval vendors; matches the verified insight that real teams keep custom harnesses and vendors capture only SDK users | Medium — adapter contract is the hard part | This is Triana's current wedge. Correct. |
| 2 | **Release evidence + compliance attestation** for regulated teams (EU AI Act envelope, SR 11-7) | High once an auditor accepts a packet; distinct co-signer budget | Slow — compliance sales cycles | Sequence as expansion of wedge 1, lead with it only for regulated design partners |
| 3 | **Production Replay Dataset** as the entry product | Low — conversion is commoditized | Fastest demo | Keep as the fuel/first-run magic inside wedge 1, never the positioning |

### 9.2 Five design-partner experiments
1. **Shadow verdict** — non-blocking GitHub check on a partner's real releases for
   30 days; measure verdict-vs-outcome agreement and count decisions the team
   changed because of it. Success: they ask to make it blocking.
2. **Time-to-first-verdict** — onboard 3 teams with existing custom harnesses,
   zero changes to their eval code, measure wall-clock to first PASS/REVIEW/BLOCK.
   Success: <2 days each; failure: weeks (services trap).
3. **Evidence willingness-to-pay** — hand a regulated partner a compiled evidence
   packet mapped to Art. 43(4)/72 or SR 11-7; test whether compliance will co-sign
   budget. Success: a named compliance stakeholder joins the eval call.
4. **Distribution vs single-run gating** — run N-replica verdicts (pass^k /
   baseline-distribution deltas) beside single-run verdicts on the same releases;
   count decisions that flip. Success: material flip rate proves the statistical
   layer is the product, not garnish.
5. **Coexistence probe** — partner already paying Braintrust or LangSmith: does
   the Triana verdict drive actions their stack didn't? Success: identified
   decisions unique to Triana; failure: full duplication (feature confirmed).

### 9.3 Ten non-leading interview questions
1. Walk me through the last change you shipped to your production agent — what
   happened between the PR merging and the change reaching all users?
2. What did you look at before deciding that change was safe? Who made the call?
3. Tell me about a time an agent change caused a problem in production. How did
   you find out, and what happened next?
4. What do you run agent changes against before shipping? Where did those test
   cases come from, and when were they last updated?
5. What have you built in-house for testing or gating agent changes? Who
   maintains it, and what does it cost you?
6. Which eval or observability tools have you adopted, and what do you actually
   use them for day to day?
7. Who besides engineers sees evaluation results before something ships? What do
   they see, and in what form?
8. If a customer, auditor, or regulator asked you to prove a specific agent
   change was safe to release, what would you show them today?
9. When your agent misbehaves in production, what happens to that example
   afterward?
10. What would have to be true before you'd let an automated system block one of
    your releases?

### 9.4 24-month roadmap
- **Q3–Q4 2026 (wedge):** trace adapters (OTel GenAI, Langfuse, LangSmith,
  Braintrust export) → versioned Release Replay Sets → harness-orchestration
  contract (webhook/CLI, customer infra, deterministic-first) → baseline/candidate
  distribution comparison → versioned Release Policy → verdict as GitHub required
  check + evidence page. 3–5 design partners; experiments 1–2, 5.
- **Q1–Q2 2027 (record):** approval state machine; composite release identity
  hashing; multi-evaluator orchestration (DeepEval + custom judges in one run);
  automatic Replay Set maintenance with drift/coverage maps; Argo analysis
  endpoint + deployment-protection-rule app; first compliance packet (experiment
  3); pricing per gated release + platform fee.
- **Q3–Q4 2027 (authority):** blocking authority as default motion; policy
  library per vertical (fintech SR 11-7, EU high-risk); evidence corpus becomes
  the renewal moat; continuous policy evaluation against production (Art. 72
  posture — answers the Chime pattern).
- **Q1–Q2 2028 (expansion toward C):** promotion/rollback *triggers* into
  LaunchDarkly/Argo/Harness (own the decision, never the traffic); shadow-replay
  of candidate agents on mirrored traces in customer infra; if and only if pull
  exists, evaluate owning canary orchestration for agents.

---

## 10. Evidence gaps and confidence

| Claim | Confidence | Gap |
|---|---|---|
| Universal absence of policy/evidence/approval layer across 11 platforms | High | Primary docs verified per platform; Harness Agent DLC docs unreadable at research time |
| Eval vendors can compose gate mechanics in 1–4 quarters | High | Directly evidenced by shipped primitives + cadence |
| Custom-harness insight (teams keep own executors; vendors capture SDK users) | Medium-High | Ramp/GitHub/DoorDash/Cox build evidence + ZenML corpus; missing practitioner-forum voice (HN/Reddit not retrieved) |
| EU AI Act creates purchasable attestation demand | Medium | Regulation text solid; zero evidence yet of budget motion — test in 90 days |
| "Custom evals dominate; generic metrics fail" | Low | Vendor marketing only; one counter-paper (Lost in Simulation) |
| Privacy forces in-VPC evaluation | Low-Medium | Inferred from vendor behavior (everyone ships BYOC); no survey |
| Agent release failures are frequent/public | Low | One real postmortem (Replit); the viral 74% stat is unusable |
| Funding/ARR figures (LangChain $16M ARR, etc.) | Low-Medium | Third-party aggregators, flagged inline in agent reports |

Per-platform citation-complete reports: session task outputs (13 agents), plus
`scratchpad/synthesis-notes.md` for the condensed trail.

