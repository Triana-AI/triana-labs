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
