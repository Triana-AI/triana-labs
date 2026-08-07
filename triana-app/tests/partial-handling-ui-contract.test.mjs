import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const COMPONENT = join(ROOT, "components", "analysis", "PartialHandlingEvidence.tsx");
const LOCAL_ANALYSIS = join(ROOT, "app", "analysis", "page.tsx");
const SELF_SERVE_REPORT = join(
  ROOT,
  "components",
  "analysis",
  "SelfServeReportClient.tsx",
);
const SELF_SERVE_TYPES = join(ROOT, "lib", "self-serve", "types.ts");

const read = (path) => readFileSync(path, "utf8");
const componentSource = () => {
  assert.ok(
    existsSync(COMPONENT),
    "partial handling must be one reusable analysis component",
  );
  return read(COMPONENT);
};

test("local and authenticated reports reuse one partial-handling evidence component", () => {
  const component = componentSource();
  const local = read(LOCAL_ANALYSIS);
  const selfServe = read(SELF_SERVE_REPORT);

  assert.match(
    component,
    /export\s+(?:default\s+)?(?:function|const)\s+PartialHandlingEvidence/,
  );
  for (const [name, source, callback] of [
    ["local /analysis", local, "openConversation"],
    ["authenticated report", selfServe, "openEvidence"],
  ]) {
    assert.match(
      source,
      /import\s*\{[^}]*PartialHandlingEvidence[^}]*\}\s*from\s*["']@\/components\/analysis\/PartialHandlingEvidence["']/s,
      `${name} must import the shared component`,
    );
    assert.match(
      source,
      /<PartialHandlingEvidence\b/,
      `${name} must render the shared component`,
    );
    assert.match(
      source,
      /evidence=\{report\.partial_handling_evidence\}/,
      `${name} must project the canonical partial evidence`,
    );
    assert.match(
      source,
      new RegExp(`onOpenTrace=\\{${callback}\\}`),
      `${name} must use its existing conversation callback`,
    );
  }
});

test("partial handling stays visibly proposal-only and keeps completed runs separate", () => {
  const source = componentSource();

  for (const label of ["PARTIAL", "PROPOSAL_ONLY"]) {
    assert.match(source, new RegExp(`["']${label}["']`));
  }
  assert.match(source, /completed_run_count/);
  assert.match(source, /\.runs\.map\s*\(/, "completed semantic runs must render separately");
  assert.match(source, /run\.run_index/, "each rendered run must retain its run index");
  assert.match(source, /run\.items/, "each rendered run must retain its own trace inventory");
  assert.match(source, /onOpenTrace\s*\(\s*traceId\s*\)/);
  assert.match(source, /Conversation|trace evidence|evidence trace/i);
});

test("authoritative outcome arithmetic is optional and trace-cited", () => {
  const source = componentSource();

  assert.match(
    source,
    /outcome_by_handling_mode\s*\?/,
    "outcome rendering must be conditional on authoritative joined evidence",
  );
  for (const field of [
    "denominator",
    "success_count",
    "failure_count",
    "mean_reward",
    "trace_ids",
  ]) {
    assert.match(source, new RegExp(`\\.${field}\\b`), `${field} must be visible`);
  }
  assert.match(source, /\.trace_ids\.map\s*\(/);
  assert.match(source, /onOpenTrace\s*\(\s*traceId\s*\)/);
});

test("report types preserve optional absence and the component makes no stronger claim", () => {
  const component = componentSource();
  const local = read(LOCAL_ANALYSIS);
  const selfServe = read(SELF_SERVE_REPORT);
  const selfServeTypes = read(SELF_SERVE_TYPES);

  assert.match(component, /export\s+(?:interface|type)\s+PartialHandlingEvidence\b/);
  assert.match(
    component,
    /evidence\??:\s*PartialHandlingEvidence/,
    "the shared component must accept absent partial evidence",
  );
  assert.match(
    component,
    /if\s*\(\s*!evidence\s*\)\s*return\s+null/,
    "absent evidence must retain the existing UI without a synthetic replacement",
  );
  for (const [name, source] of [
    ["local report type", local],
    ["self-serve report type", selfServeTypes],
  ]) {
    assert.match(
      source,
      /partial_handling_evidence\?\s*:\s*PartialHandlingEvidence/,
      `${name} must preserve field absence`,
    );
  }
  assert.match(selfServe, /tab\s*===\s*["']behavior["'][\s\S]*PartialHandlingEvidence/);
  assert.doesNotMatch(
    component,
    /\bstable\b|intent population|\bevals?\b|\bevaluations?\b|\bfinding\b|\bpass\b|causal failure/i,
    "partial handling must not be upgraded to stability, population, eval, finding, pass, or causality",
  );
});
