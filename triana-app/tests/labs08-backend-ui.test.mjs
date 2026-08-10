import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const LOADER = join(ROOT, "lib", "labs-report.ts");
const CANONICAL_REPORT = resolve(
  ROOT,
  "..",
  "triana-backend",
  "tests",
  "acceptance",
  "labs08_canonical_accounting_report.json",
);

const read = (path) => readFileSync(path, "utf8");

test("Labs UI loads the exact backend report and never falls back to a fixture", async () => {
  const productionSources = [
    LOADER,
    join(ROOT, "app", "setup", "page.tsx"),
    join(ROOT, "components", "AppNav.tsx"),
  ].map(read).join("\n");

  assert.doesNotMatch(
    productionSources,
    /(?:from|require\s*\()\s*["'][^"']*data\/labs-report\.json/,
    "production UI code must not import the Exit A report fixture",
  );
  assert.match(productionSources, /TRIANA_BACKEND_API_ORIGIN/);
  assert.match(productionSources, /TRIANA_LABS_REPORT_ID/);
  assert.match(productionSources, /BACKEND_(?:REPORT_)?UNAVAILABLE/);

  const report = JSON.parse(read(CANONICAL_REPORT));

  const { loadLabsReport } = await import(`${pathToFileURL(LOADER).href}?labs08`);
  const calls = [];
  const loaded = await loadLabsReport({
    apiOrigin: "http://127.0.0.1:8000",
    reportId: report.report_id,
    fetchImpl: async (url) => {
      calls.push(url);
      return new Response(JSON.stringify(report), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    },
  });
  assert.deepEqual(calls, [
    `http://127.0.0.1:8000/api/v1/reports/${report.report_id}`,
  ]);
  assert.equal(loaded.availability, "AVAILABLE");
  assert.deepEqual(loaded.report, report);
  assert.equal(loaded.report.setup.understanding.physical_record_count, 200);
  assert.equal(loaded.report.setup.understanding.usable_conversation_count, 186);
  assert.deepEqual(loaded.report.setup.understanding.source_status_counts, {
    COMPLETED: 186,
    HARNESS_ERROR: 14,
  });
  assert.equal(loaded.report.evidence_class, "SYNTHETIC_EXISTING_TRACE_CORPUS");

  const unavailable = await loadLabsReport({
    apiOrigin: "http://127.0.0.1:8000",
    reportId: report.report_id,
    fetchImpl: async () => { throw new TypeError("connection refused"); },
  });
  assert.deepEqual(unavailable, {
    availability: "UNAVAILABLE",
    code: "BACKEND_REPORT_UNAVAILABLE",
    report: null,
  });
  assert.notDeepEqual(unavailable.report, report);
});

test("Labs UI explicitly accepts both report modes and rejects invented modes", async () => {
  const retained = JSON.parse(read(CANONICAL_REPORT));
  const generated = structuredClone(retained);
  generated.report_id = "rpt_generated_mode_control";
  generated.mode = "GENERATED_MULTI_TURN_SIMULATION";
  const { loadLabsReport } = await import(`${pathToFileURL(LOADER).href}?labs08-modes`);

  for (const report of [retained, generated]) {
    const loaded = await loadLabsReport({
      apiOrigin: "http://127.0.0.1:8000",
      reportId: report.report_id,
      fetchImpl: async () => new Response(JSON.stringify(report), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    });
    assert.equal(loaded.availability, "AVAILABLE", `mode ${report.mode} must be supported`);
    assert.equal(loaded.report.mode, report.mode);
  }

  const invented = structuredClone(retained);
  invented.mode = "OWNER_AUTHORIZED_REAL_DATA_CANARY";
  const refused = await loadLabsReport({
    apiOrigin: "http://127.0.0.1:8000",
    reportId: invented.report_id,
    fetchImpl: async () => new Response(JSON.stringify(invented), {
      status: 200,
      headers: { "content-type": "application/json" },
    }),
  });
  assert.deepEqual(refused, {
    availability: "UNAVAILABLE",
    code: "BACKEND_REPORT_UNAVAILABLE",
    report: null,
  });
});

test("behavior UI renders deterministic structural descriptions without model authority", async () => {
  const behaviorSource = read(join(ROOT, "app", "behavior", "page.tsx"));
  const loaderSource = read(LOADER);
  assert.match(loaderSource, /semantic_summary_authority:[^;]*"DETERMINISTIC"/s);
  assert.match(loaderSource, /STRUCTURALLY_OBSERVED_DETERMINISTIC_DESCRIPTION/);
  assert.match(behaviorSource, /Deterministic description/);
  assert.doesNotMatch(behaviorSource, /Summary model-written|model-proposed summaries/i);

  const report = JSON.parse(read(CANONICAL_REPORT));
  report.report_id = "rpt_tau57_structural";
  report.setup.understanding = {
    physical_record_count: 57,
    accepted_record_count: 57,
    rejected_record_count: 0,
    usable_conversation_count: 57,
    source_status_counts: { ACCEPTED: 57 },
    rejection_reasons: [],
    unassessed_semantics: ["No population or accepted-behavior claim was established."],
  };
  report.behavior = {
    derivation_kind: "STRUCTURAL_GROUPING",
    membership_authority: "DETERMINISTIC",
    semantic_summary_authority: "DETERMINISTIC",
    population_claim: "NOT_ESTABLISHED",
    groups: [{
      group_id: "group_tau57",
      label: "Observed structure 1",
      summary: "User message followed by an agent response.",
      support_count: 57,
      share_basis_points: 10000,
      structural_pattern: "USER_MESSAGE > ASSISTANT_MESSAGE",
      fidelity_label: "STRUCTURALLY_OBSERVED_DETERMINISTIC_DESCRIPTION",
      source_evidence_ids: ["trace-01"],
    }],
  };

  const { loadLabsReport } = await import(`${pathToFileURL(LOADER).href}?tau57`);
  const loaded = await loadLabsReport({
    apiOrigin: "http://127.0.0.1:8000",
    reportId: report.report_id,
    fetchImpl: async () => new Response(JSON.stringify(report), {
      status: 200,
      headers: { "content-type": "application/json" },
    }),
  });
  assert.equal(loaded.availability, "AVAILABLE");
  assert.equal(loaded.report.behavior.groups.length, 1);
  assert.equal(loaded.report.behavior.semantic_summary_authority, "DETERMINISTIC");
  assert.equal(loaded.report.behavior.population_claim, "NOT_ESTABLISHED");
});
