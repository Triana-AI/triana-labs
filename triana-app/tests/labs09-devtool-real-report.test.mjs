import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import {
  existsSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { dirname, extname, join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const CANONICAL = join(ROOT, "data", "labs-report.json");
const VALIDATOR = join(ROOT, "scripts", "build-snapshot.mjs");
const REAL_PRIVACY = "OWNER_AUTHORIZED_REAL_DATA_CANARY";
const REAL_SAMPLE = "PRIVATE_OWNER_AUTHORIZED_CANARY";
const REAL_SOURCE_AUTH = "OWNER_AUTHORIZED_REAL_DATA";
const REAL_EGRESS_AUTH = "OWNER_AUTHORIZED_REAL_DATA_EGRESS";
const REPORT_ENV = "TRIANA_LABS_REPORT_PATH";

const read = (path) => readFileSync(path, "utf8");
const normalized = (value) => value.replace(/\s+/g, " ").trim();
const clone = (value) => JSON.parse(JSON.stringify(value));
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");

const commandOutput = (result) =>
  [result.stdout, result.stderr].filter(Boolean).join("\n").trim();

const validateDefault = () => spawnSync(process.execPath, [VALIDATOR, "--validate", CANONICAL], {
  cwd: ROOT,
  encoding: "utf8",
  env: { ...process.env, [REPORT_ENV]: "" },
});

const validateSelected = (path) => spawnSync("npm", ["run", "report:validate"], {
  cwd: ROOT,
  encoding: "utf8",
  env: { ...process.env, [REPORT_ENV]: path },
});

const sourceFiles = (roots) => {
  const files = [];
  const visit = (path) => {
    if (!existsSync(path)) return;
    if (statSync(path).isDirectory()) {
      for (const entry of readdirSync(path)) visit(join(path, entry));
    } else if ([".ts", ".tsx", ".js", ".mjs", ".css"].includes(extname(path))) {
      files.push(path);
    }
  };
  roots.forEach(visit);
  return files;
};

const inventory = (roots) => {
  const result = new Map();
  const visit = (path) => {
    if (!existsSync(path)) return;
    if (statSync(path).isDirectory()) {
      for (const entry of readdirSync(path)) visit(join(path, entry));
    } else {
      result.set(path.slice(ROOT.length + 1), sha256(readFileSync(path)));
    }
  };
  roots.forEach(visit);
  return result;
};

const writeReport = (directory, name, mutate) => {
  const report = clone(JSON.parse(read(CANONICAL)));
  mutate(report);
  const path = join(directory, name);
  writeFileSync(path, `${JSON.stringify(report)}\n`);
  return path;
};

const makeReal = (report) => {
  report.privacy_class = REAL_PRIVACY;
  report.sample_class = REAL_SAMPLE;
  report.setup.source.authorization = REAL_SOURCE_AUTH;
  report.run.privacy_egress.authorization = REAL_EGRESS_AUTH;
};

test("shared UI is a warm compact Triana instrument panel and retains the official Lazo", () => {
  const css = normalized(sourceFiles([
    join(ROOT, "tokens.css"),
    join(ROOT, "app", "globals.css"),
    join(ROOT, "styles"),
  ]).map(read).join("\n"));

  assert.match(css, /\bwarm\b|\bcream\b/i, "the solid canvas must retain Triana's warm cream tone");
  assert.match(css, /body\s*\{[^}]*background-color\s*:/i, "the page canvas must be a solid color");
  assert.match(css, /\.app-sidebar\s*\{[^}]*background\s*:\s*(?:white|#f{3,6}|var\(--[^)]*(?:white|paper|rail)[^)]*\))/i,
    "the compact navigation rail must use a white surface");
  assert.match(css, /\.app-nav-link\[aria-current=["']page["']\]\s*\{[^}]*background\s*:\s*(?:black|#0{3,6}|var\(--[^)]*(?:ink|black|active)[^)]*\))/i,
    "the active navigation cell must be black or ink-dark");
  assert.match(css, /\.mono-label\s*\{[^}]*font-family\s*:\s*var\(--font-mono\)/i,
    "compact operational metadata must retain the mono face");
  assert.match(css, /\bacid\b/i, "the shared accent must be described as Triana's sparse acid signal");
  const acidFills = css.match(/background(?:-color)?\s*:\s*var\(--(?:color-)?accent\)/gi) ?? [];
  assert.ok(acidFills.length <= 3, `acid accent is not sparse: ${acidFills.length} surface fills`);
  assert.doesNotMatch(css, /\bdotted\b|background-image\s*:|\burl\s*\(/i,
    "the canvas must not use dots, textures, or background images");
  assert.doesNotMatch(css, /(?:linear|radial|conic)-gradient\s*\(/i, "the UI must not use gradients");
  assert.doesNotMatch(css, /fake-(?:browser|terminal|window)|browser-chrome|terminal-chrome/i,
    "the UI must not draw fake application chrome");

  const asset = join(ROOT, "public", "brand", "triana-lazo-favicon-master.svg");
  assert.ok(existsSync(asset), "the official Lazo asset must remain installed");
  assert.match(read(asset), /^\s*<svg\b[\s\S]*<\/svg>\s*$/i);
  assert.match(read(join(ROOT, "components", "AppNav.tsx")), /\/brand\/triana-lazo-favicon-master\.svg/);
});

test("default validation and loader remain pinned to the public synthetic reference", () => {
  const result = validateDefault();
  assert.equal(result.status, 0, `default report failed validation:\n${commandOutput(result)}`);

  const report = JSON.parse(read(CANONICAL));
  assert.equal(report.privacy_class, "SYNTHETIC");
  assert.equal(report.sample_class, "PUBLIC_SYNTHETIC_REFERENCE");
  assert.equal(report.setup.source.authorization, "AUTHORIZED_SYNTHETIC");
  assert.equal(report.run.privacy_egress.authorization, "SYNTHETIC_APPROVED");

  const loader = read(join(ROOT, "lib", "labs-report.ts"));
  assert.match(loader, /data\/labs-report\.json|@\/data\/labs-report\.json/,
    "without an override the app must render the checked-in canonical report");
  const visibleSources = normalized(sourceFiles([
    join(ROOT, "app"), join(ROOT, "components"),
  ]).map(read).join("\n"));
  assert.match(visibleSources, /PUBLIC_SYNTHETIC_REFERENCE|privacy_class|sample_class/,
    "the default UI must expose report-owned sample/privacy metadata");
});

test("an absolute private local override validates without copying the report", (t) => {
  const privateRoot = mkdtempSync("/private/tmp/triana-labs09-report-");
  t.after(() => rmSync(privateRoot, { recursive: true, force: true }));
  const realPath = writeReport(privateRoot, "owner-canary.json", makeReal);

  const guardedRoots = [join(ROOT, "data"), join(ROOT, "public", "out")];
  const before = inventory(guardedRoots);
  const result = validateSelected(realPath);
  assert.equal(result.status, 0, `valid owner-authorized private report was refused:\n${commandOutput(result)}`);
  assert.match(commandOutput(result), new RegExp(REAL_PRIVACY),
    "validation output must identify the selected real-data privacy class");
  assert.deepEqual(inventory(guardedRoots), before, "selection must not copy or rewrite private report bytes");

  const runtime = normalized(sourceFiles([
    join(ROOT, "lib"), join(ROOT, "app"), join(ROOT, "components", "AppNav.tsx"), VALIDATOR,
  ]).map(read).join("\n"));
  assert.match(runtime, new RegExp(REPORT_ENV), "the app and validator must honor the explicit local-report path");
  assert.match(runtime, /OWNER_AUTHORIZED_REAL_DATA_CANARY/);
  assert.match(runtime, /real[- ]data/i, "the UI needs a truthful real-data disclosure");
  assert.match(runtime, /private.{0,100}(?:custody|local)|(?:custody|local).{0,100}private/i,
    "the UI needs a truthful private-custody disclosure");
  assert.match(runtime, /app-connections[\s\S]{0,1800}(?:privacy_class|sample_class|authorization)/,
    "rail metadata must derive from the selected report rather than fixed synthetic copy");
});

test("unsafe, missing, and mismatched local report selections refuse", async (t) => {
  const privateRoot = mkdtempSync("/private/tmp/triana-labs09-refusal-");
  const nonPrivateRoot = mkdtempSync(join(tmpdir(), "triana-labs09-refusal-"));
  t.after(() => {
    rmSync(privateRoot, { recursive: true, force: true });
    rmSync(nonPrivateRoot, { recursive: true, force: true });
  });

  const cases = [
    ["relative path", "owner-canary.json"],
    ["missing path", join(privateRoot, "missing.json")],
    ["repo-contained path", CANONICAL],
    ["non-private path", writeReport(nonPrivateRoot, "real.json", makeReal)],
    ["unknown privacy", writeReport(privateRoot, "unknown.json", (report) => {
      makeReal(report); report.privacy_class = "UNKNOWN_PRIVATE_DATA";
    })],
    ["mismatched sample", writeReport(privateRoot, "sample-mismatch.json", (report) => {
      makeReal(report); report.sample_class = "PUBLIC_SYNTHETIC_REFERENCE";
    })],
    ["mismatched authorization", writeReport(privateRoot, "auth-mismatch.json", (report) => {
      makeReal(report); report.setup.source.authorization = "AUTHORIZED_SYNTHETIC";
    })],
    ["mismatched egress authorization", writeReport(privateRoot, "egress-mismatch.json", (report) => {
      makeReal(report); report.run.privacy_egress.authorization = "SYNTHETIC_APPROVED";
    })],
  ];

  for (const [name, path] of cases) {
    await t.test(name, () => {
      const result = validateSelected(path);
      assert.notEqual(result.status, 0, `${name} reached the build:\n${commandOutput(result)}`);
    });
  }
});

test("local report selection has no provider call, model fallback, or hidden network path", () => {
  const runtimeFiles = sourceFiles([
    join(ROOT, "scripts"), join(ROOT, "lib"), join(ROOT, "app"), join(ROOT, "components"),
  ]);
  const runtime = runtimeFiles.map((path) => `${path}\n${read(path)}`).join("\n");
  assert.doesNotMatch(runtime, /\bfetch\s*\(|XMLHttpRequest|WebSocket\s*\(|https?\.request\s*\(/,
    "selecting or rendering a report must not make a network call");
  assert.doesNotMatch(runtime, /chat\.completions|responses\.create|generateContent|invokeModel|API_KEY/,
    "no model/provider fallback may fill or reinterpret report evidence");
});
