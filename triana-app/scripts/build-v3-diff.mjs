#!/usr/bin/env node
/**
 * Builds the v2-to-v3 release diff (all 13 frozen behavioral-evals measurement
 * ids, scored on the demo_corpus baseline/candidate pair) and writes it into
 * data/snapshot.json's top-level `diff` key, replacing the historical v1-to-v2
 * diff that was there. Everything else in snapshot.json (fixDiff, cases,
 * evidence, releases, tail) is left untouched.
 *
 * Source of truth for the 13 rows:
 *   - experiments/hr_ai_seed/out/v3_demo_diff.json (agentagon, produced by
 *     run_v3_demo_diff.py): static measurements computed directly from the
 *     demo_corpus state_after, judge-scored measurements from the pinned
 *     Bedrock model against a deterministic 40/40 sample.
 *   - experiments/behavioral_evals_smoke/FROZEN_SET.json: definition/rubric/
 *     labelSet/judgeModel/judgePrompt text, verbatim.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const AGENTAGON = "/Users/akarshgajbhiye/agentagon";
const DEMO_CORPUS = "/Users/akarshgajbhiye/Documents/hr_ai/experiments/demo_corpus";

const readJson = (p) => JSON.parse(readFileSync(p, "utf8"));
const readJsonl = (p) =>
  readFileSync(p, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));

const v3 = readJson(`${AGENTAGON}/experiments/hr_ai_seed/out/v3_demo_diff.json`);
const frozen = readJson(`${AGENTAGON}/experiments/behavioral_evals_smoke/FROZEN_SET.json`);
const frozenById = new Map(frozen.measurements.map((m) => [m.id, m]));

const baselineTraces = readJsonl(`${DEMO_CORPUS}/baseline/normalized_traces.jsonl`);
const candidateTraces = readJsonl(`${DEMO_CORPUS}/candidate/normalized_traces.jsonl`);

/* ------------------------------------------------------- measurement rows --- */

const FOCUS = {
  goal_correctness_evaluation: { label: "correct", higherIsBetter: true },
  goal_correctness_decision: { label: "correct", higherIsBetter: true },
  goal_correctness_outreach: { label: "correct", higherIsBetter: true },
  goal_correctness_ranking: { label: "correct", higherIsBetter: true },
  goal_correctness_recall: { label: "correct", higherIsBetter: true },
  task_evasion_rate: { label: "completed", higherIsBetter: true },
  untrusted_content_handling: { label: "grounded", higherIsBetter: true },
  user_frustration_level: { label: "high", higherIsBetter: false },
  evaluation_commit_rate: { label: null, higherIsBetter: true },
  decision_distribution: { label: "shortlist", higherIsBetter: null },
  email_status_distribution: { label: "queued", higherIsBetter: null },
  evaluation_recommendation_distribution: { label: "strong_hire", higherIsBetter: null },
  repeated_call_rate: { label: null, higherIsBetter: false },
};

const TITLES = { task_evasion_rate: "Task Completion" };

function sideRate(side, focus) {
  if (side.rate !== undefined && side.rate !== null) return side.rate;
  const dist = side.distribution ?? {};
  const n = side.n ?? Object.values(dist).reduce((a, b) => a + b, 0);
  if (!n || !focus?.label) return null;
  return (dist[focus.label] ?? 0) / n;
}

/** Below this sample size on either side, a category rate is too thin to call
 *  IMPROVED/REGRESSED — same spirit as build-snapshot.mjs's baseN>=8 collapse
 *  rule, extended to also catch small-population EVAL rows where the ratio
 *  rule (baseN>=8) never engages because baseN itself starts under 8. */
const MIN_STABLE_N = 5;

function buildEvalRow(id) {
  const frozenDef = frozenById.get(id);
  const gate = v3.eval[id]; // may be null (0 population in the 40-sample on both sides)
  const sampleN = v3.sample_n[id] ?? { baseline: 0, candidate: 0 };
  const focus = FOCUS[id];

  const baseline = gate
    ? { n: gate.baseline.evaluable, distribution: gate.baseline.distribution, notApplicable: gate.baseline.not_applicable ?? null }
    : { n: sampleN.baseline, distribution: {}, notApplicable: sampleN.baseline };
  const candidate = gate
    ? { n: gate.candidate.evaluable, distribution: gate.candidate.distribution, notApplicable: gate.candidate.not_applicable ?? null }
    : { n: sampleN.candidate, distribution: {}, notApplicable: sampleN.candidate };

  const baseRate = sideRate(baseline, focus);
  const candRate = sideRate(candidate, focus);
  const deltaPts = baseRate !== null && candRate !== null ? (candRate - baseRate) * 100 : null;
  const sampleCollapse =
    (baseline.n >= 8 && candidate.n < baseline.n * 0.5) ||
    baseline.n < MIN_STABLE_N ||
    candidate.n < MIN_STABLE_N;

  let direction = "neutral";
  if (sampleCollapse) {
    direction = "low-sample";
  } else if (deltaPts !== null && focus.higherIsBetter !== null) {
    const improved = focus.higherIsBetter ? deltaPts > 0 : deltaPts < 0;
    if (Math.abs(deltaPts) < 0.5) direction = "flat";
    else direction = improved ? "improved" : "regressed";
  }

  return {
    id,
    title: TITLES[id] ?? frozenDef.title,
    dimension: frozenDef.dimension,
    kind: frozenDef.kind,
    valueType: frozenDef.value_type,
    question: frozenDef.developer_question,
    focusLabel: focus.label,
    higherIsBetter: focus.higherIsBetter,
    baseline: { n: baseline.n, distribution: baseline.distribution, rate: baseRate, notApplicable: baseline.notApplicable },
    candidate: { n: candidate.n, distribution: candidate.distribution, rate: candRate, notApplicable: candidate.notApplicable },
    deltaPts,
    direction,
    sampleCollapse,
    definition: frozenDef.definition,
    rubric: frozenDef.executor.rubric,
    labelSet: frozenDef.executor.label_set,
    judgeModel: frozenDef.executor.model_id,
    judgePrompt: frozenDef.executor.prompt_version,
  };
}

function buildStaticRow(id) {
  const frozenDef = frozenById.get(id);
  const side = v3.static[id];
  const focus = FOCUS[id];

  const baseRate = sideRate(side.baseline, focus);
  const candRate = sideRate(side.candidate, focus);
  const deltaPts = baseRate !== null && candRate !== null ? (candRate - baseRate) * 100 : null;
  const sampleCollapse = side.baseline.n >= 8 && side.candidate.n < side.baseline.n * 0.5;

  let direction = "neutral";
  if (sampleCollapse) {
    direction = "low-sample";
  } else if (deltaPts !== null && focus.higherIsBetter !== null) {
    const improved = focus.higherIsBetter ? deltaPts > 0 : deltaPts < 0;
    if (Math.abs(deltaPts) < 0.5) direction = "flat";
    else direction = improved ? "improved" : "regressed";
  }

  const isRepeatedCallRate = id === "repeated_call_rate";
  return {
    id,
    title: isRepeatedCallRate ? "Repeated-call Rate" : frozenDef.title,
    dimension: isRepeatedCallRate ? "PERFORMANCE_UNDER_LOAD" : frozenDef.dimension,
    kind: "STATIC",
    valueType: isRepeatedCallRate ? "PERCENT" : frozenDef.value_type,
    question: isRepeatedCallRate
      ? "Did the agent fire the same tool three or more times back to back?"
      : frozenDef.developer_question,
    focusLabel: focus.label,
    higherIsBetter: focus.higherIsBetter,
    baseline: { n: side.baseline.n, distribution: side.baseline.distribution, rate: baseRate, notApplicable: side.baseline.notApplicable },
    candidate: { n: side.candidate.n, distribution: side.candidate.distribution, rate: candRate, notApplicable: side.candidate.notApplicable },
    deltaPts,
    direction,
    sampleCollapse,
    definition: isRepeatedCallRate
      ? "Share of completed traces containing a run of three or more identical consecutive tool calls, computed directly from the trace tool sequence."
      : frozenDef.definition,
    rubric: null,
    labelSet: isRepeatedCallRate ? null : frozenDef.executor.label_set,
    judgeModel: null,
    judgePrompt: isRepeatedCallRate ? "deterministic — no judge model" : null,
  };
}

const EVAL_IDS = [
  "goal_correctness_evaluation",
  "goal_correctness_decision",
  "goal_correctness_outreach",
  "goal_correctness_ranking",
  "goal_correctness_recall",
  "task_evasion_rate",
  "untrusted_content_handling",
  "user_frustration_level",
];
const STATIC_IDS = [
  "evaluation_commit_rate",
  "decision_distribution",
  "email_status_distribution",
  "evaluation_recommendation_distribution",
  "repeated_call_rate",
];

const rows = [...STATIC_IDS.map(buildStaticRow), ...EVAL_IDS.map(buildEvalRow)];

/* ------------------------------------------------------------ tail/pairs --- */

const toolSequence = (t) => (t.events ?? []).filter((e) => e.kind === "tool").map((e) => e.name ?? "unknown");
const summarizeToolNames = (seq) => {
  if (!seq.length) return null;
  const counts = new Map();
  for (const n of seq) counts.set(n, (counts.get(n) ?? 0) + 1);
  return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3)
    .map(([n, c]) => (c > 1 ? `${n} ×${c}` : n)).join(", ");
};
const isLoopingOtel = (t) => {
  const dup = t.repeated_tool_calls?.duplicate_count ?? 0;
  const excessive = toolSequence(t).length > 20;
  const crash = typeof t.error === "string" && t.error.includes("Recursion limit");
  return dup > 0 || excessive || crash;
};
const decisionsOf = (t) =>
  (t.state_after?.committed_decisions ?? []).map((d) => `${d.candidate_id}:${d.decision}`).sort().join("|");

function pairCases(baseline, candidate) {
  const byCase = new Map();
  for (const t of baseline) byCase.set(t.case_id, { baseline: t });
  for (const t of candidate) {
    const e = byCase.get(t.case_id) ?? {};
    e.candidate = t;
    byCase.set(t.case_id, e);
  }
  const pairs = [];
  for (const [caseId, { baseline: b, candidate: c }] of byCase) {
    if (!b || !c) continue;
    const bTools = toolSequence(b);
    const cTools = toolSequence(c);
    pairs.push({
      caseId,
      baseline: { toolCalls: bTools.length, usd: b.usd ?? 0, looping: isLoopingOtel(b), decisions: decisionsOf(b) },
      candidate: { toolCalls: cTools.length, usd: c.usd ?? 0, looping: isLoopingOtel(c), decisions: decisionsOf(c) },
    });
  }
  const MIN_COMPARABLE_USD = 0.005;
  for (const p of pairs) {
    p.comparable = p.baseline.usd >= MIN_COMPARABLE_USD && p.candidate.usd >= MIN_COMPARABLE_USD;
    p.costMultiple = p.comparable ? p.candidate.usd / p.baseline.usd : null;
    p.newLooper = !p.baseline.looping && p.candidate.looping;
    p.decisionChanged = p.baseline.decisions !== p.candidate.decisions;
  }
  return pairs;
}

const pairs = pairCases(baselineTraces, candidateTraces);
const tail = {
  topCost: [...pairs]
    .filter((p) => p.costMultiple !== null)
    .sort((a, b) => (b.costMultiple ?? 0) - (a.costMultiple ?? 0))
    .slice(0, 2)
    .map((p) => ({ caseId: p.caseId, costMultiple: Number((p.costMultiple ?? 0).toFixed(1)) })),
  newLoopers: pairs.filter((p) => p.newLooper).length,
  pairCount: pairs.length,
  decisionChanges: pairs.filter((p) => p.decisionChanged).length,
};

/* ---------------------------------------------------------------- score --- */

function scoreRelease({ regressions, sampleCollapses, costGrowthPct }) {
  const raw = 100 - 12 * regressions - 5 * sampleCollapses - 0.3 * Math.max(costGrowthPct, 0);
  return Math.max(0, Math.min(100, Math.round(raw)));
}
function verdictFor({ regressions, safetyRegressions, worstDeltaPts }) {
  if (safetyRegressions > 0 || Math.abs(worstDeltaPts ?? 0) >= 10) return "BLOCK";
  if (regressions > 0) return "SHIP WITH RISK";
  return "SHIP";
}

const regressed = rows.filter((m) => m.direction === "regressed");
const improved = rows.filter((m) => m.direction === "improved");
const collapsed = rows.filter((m) => m.direction === "low-sample");
const costGrowthPct = ((v3.mechanical.candidate.costUsd - v3.mechanical.baseline.costUsd) / v3.mechanical.baseline.costUsd) * 100;
const worstDelta = regressed.reduce(
  (worst, m) => (Math.abs(m.deltaPts ?? 0) > Math.abs(worst ?? 0) ? m.deltaPts : worst),
  null,
);
const score = scoreRelease({ regressions: regressed.length, sampleCollapses: collapsed.length, costGrowthPct });
const verdict = verdictFor({
  regressions: regressed.length,
  safetyRegressions: regressed.filter((m) => m.dimension === "SAFETY").length,
  worstDeltaPts: worstDelta,
});

/* --------------------------------------------------------------- release --- */

function behaviourFor(side) {
  const pick = (id, label) => {
    const row = rows.find((r) => r.id === id);
    if (!row) return null;
    const s = row[side];
    if (s.rate !== null && row.focusLabel === label) return s.rate;
    const dist = s.distribution ?? {};
    const n = s.n ?? Object.values(dist).reduce((a, b) => a + b, 0);
    return n ? (dist[label] ?? 0) / n : null;
  };
  return {
    taskCompletion: pick("task_evasion_rate", "completed"),
    userFrustrationHigh: pick("user_frustration_level", "high"),
    fabrication: pick("untrusted_content_handling", "fabricated"),
    repeatedCallRate: v3.mechanical[side].repeatedCallRate,
  };
}

const snapshotPath = join(ROOT, "data", "snapshot.json");
const snapshot = readJson(snapshotPath);

const FIX_BASELINE_META = {
  version: "v3-pre-fix",
  hash: "demo-corpus-baseline",
  run: "demo_corpus_baseline",
  change: "baseline (pre-fix, frozen demo corpus)",
  promptVersion: "candidate-screening-v3-decision-followthrough",
  agentVersion: "agent v1",
  traces: `${DEMO_CORPUS}/baseline/normalized_traces.jsonl`,
};
const FIX_CANDIDATE_META = {
  version: "v3",
  hash: "108bce9",
  run: "demo_corpus_candidate",
  change: "agent_looping dedup fix",
  promptVersion: "candidate-screening-v3-decision-followthrough",
  agentVersion: "agent v1 + dedup fix",
  traces: `${DEMO_CORPUS}/candidate/normalized_traces.jsonl`,
};

const newDiff = {
  id: "v2-to-v3",
  baseline: {
    ...FIX_BASELINE_META,
    key: "fixBaseline",
    traceCount: v3.baseline_trace_count,
    mechanical: v3.mechanical.baseline,
    behaviour: behaviourFor("baseline"),
  },
  candidate: {
    ...FIX_CANDIDATE_META,
    key: "fix",
    traceCount: v3.candidate_trace_count,
    mechanical: v3.mechanical.candidate,
    behaviour: behaviourFor("candidate"),
  },
  score,
  verdict,
  counts: {
    changed: rows.length,
    total: rows.length,
    improved: improved.length,
    regressed: regressed.length,
    lowSample: collapsed.length,
  },
  measurements: rows,
  tail,
  coverage: {
    populated: {
      GOAL_CORRECTNESS: [
        "goal_correctness_evaluation",
        "goal_correctness_decision",
        "goal_correctness_outreach",
        "goal_correctness_ranking",
        "goal_correctness_recall",
        "task_evasion_rate",
      ],
      PERFORMANCE_UNDER_LOAD: ["repeated_call_rate"],
      SAFETY: ["untrusted_content_handling", "user_frustration_level"],
      TRACE_OBSERVABILITY: [
        "evaluation_commit_rate",
        "decision_distribution",
        "email_status_distribution",
        "evaluation_recommendation_distribution",
      ],
    },
    gaps: [
      {
        dimension: "TOOL_CALL_RELIABILITY",
        needs: "needs tool call arguments and results",
        reason: "Tool call reliability cannot be assessed without observing both tool call arguments and results.",
      },
      {
        dimension: "FAULT_TOLERANCE",
        needs: "needs tool call status/result data",
        reason: "Fault tolerance cannot be assessed without tool call status/result data.",
      },
    ],
  },
  bundleHash: frozen.frozen_from_git_commit ?? null,
};

snapshot.diff = newDiff;

writeFileSync(snapshotPath, `${JSON.stringify(snapshot, null, 2)}\n`);
console.log(`snapshot.json diff replaced with v2-to-v3: score ${score} verdict ${verdict}`);
console.log(`  improved ${improved.length} regressed ${regressed.length} lowSample ${collapsed.length} total ${rows.length}`);
for (const r of rows) {
  console.log(`  - ${r.id}: n=${r.baseline.n}/${r.candidate.n} direction=${r.direction} deltaPts=${r.deltaPts}`);
}
