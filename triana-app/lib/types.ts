/** Shapes emitted by scripts/build-snapshot.mjs into data/snapshot.json. */

export type Direction =
  | "improved"
  | "regressed"
  | "flat"
  | "neutral"
  | "low-sample";

export type Verdict = "SHIP" | "SHIP WITH RISK" | "BLOCK";

export interface Mechanical {
  traces: number;
  completed: number;
  errors: number;
  costUsd: number;
  latencyP50: number;
  latencyP95: number;
  tokensIn: number;
  tokensOut: number;
  turnsMean: number;
  toolCalls: number;
  repeatedCallRate: number;
  date: string | null;
}

export interface Behaviour {
  taskCompletion: number | null;
  userFrustrationHigh: number | null;
  fabrication: number | null;
  repeatedCallRate: number;
}

export interface Release {
  key: string;
  version: string;
  hash: string;
  run: string;
  change: string;
  promptVersion: string;
  agentVersion: string;
  traces: string;
  mechanical: Mechanical;
  behaviour: Behaviour;
}

export interface MeasurementSide {
  n: number;
  distribution: Record<string, number> | null;
  rate: number | null;
  notApplicable: number | null;
}

export interface Measurement {
  id: string;
  title: string;
  dimension: string;
  kind: string;
  valueType: string;
  question: string | null;
  focusLabel: string | null;
  higherIsBetter: boolean | null;
  baseline: MeasurementSide;
  candidate: MeasurementSide;
  deltaPts: number | null;
  direction: Direction;
  sampleCollapse: boolean;
  definition: string | null;
  rubric: string | null;
  labelSet: string[] | null;
  judgeModel: string | null;
  judgePrompt: string | null;
  replacesJudgeMetric?: {
    id: string;
    baseline: number | null;
    candidate: number | null;
  } | null;
}

export interface PairSide {
  toolCalls: number;
  turns: number;
  usd: number;
  finalDecision: string;
  writes: number;
  repeat: { streak: number; tool: string | null };
}

/** Only the fields the evidence panel renders. */
export interface Pair {
  caseId: string;
  baseline: PairSide;
  candidate: PairSide;
  costMultiple: number | null;
  decisionChanged: boolean;
  newWrites: boolean;
}

export type Severity = "decision" | "writes" | "loop" | "drift";

/** A transcript, stored once and referenced by every measurement citing it. */
export interface EvidenceCase {
  caseId: string;
  metrics: Pair;
  userMessage: string | null;
  baselineQuote: string | null;
  candidateQuote: string | null;
  baselineTools: string | null;
  candidateTools: string | null;
}

export interface EvidenceRef {
  caseId: string;
  headline: string;
  severity: Severity;
  note: string | null;
  curated: boolean;
}

export type EvidenceItem = EvidenceRef & EvidenceCase;

export interface ReleaseDiff {
  id: string;
  baseline: Release & { traceCount: number };
  candidate: Release & { traceCount: number };
  score: number;
  verdict: Verdict;
  counts: {
    changed: number;
    total: number;
    improved: number;
    regressed: number;
    lowSample: number;
  };
  measurements: Measurement[];
  tail: Tail;
  coverage: {
    populated: Record<string, string[]>;
    gaps: { dimension: string; needs: string; reason: string }[];
  };
  bundleHash: string;
}

export interface HandlingSegment {
  key: string;
  count: number;
  share: number;
}

export interface Population {
  id: string;
  label: string;
  definition: string;
  kind: string;
  support: number;
  share: number;
  handling: HandlingSegment[];
  demands: string[];
}

export interface Populations {
  corpus: number;
  traceCount: number;
  items: Population[];
}

export interface Snapshot {
  generatedFrom: Record<string, string | null>;
  disclosures: string[];
  agent: { name: string; purpose: string | null };
  releases: Release[];
  populations: Populations;
  diff: ReleaseDiff;
  fixDiff?: ReleaseDiff;
  cases: Record<string, EvidenceCase>;
  evidence: Record<string, EvidenceRef[]>;
  tail: Tail;
}

export interface Tail {
  topCost: { caseId: string; costMultiple: number }[];
  newLoopers: number;
  pairCount: number;
  decisionChanges: number;
}
