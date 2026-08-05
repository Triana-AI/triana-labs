import { test } from "node:test";
import assert from "node:assert/strict";
import {
  existsSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const REPORT_PATH = join(ROOT, "data", "labs-report.json");
const VALIDATOR_PATH = join(ROOT, "scripts", "build-snapshot.mjs");

const run = (command, args, options = {}) =>
  spawnSync(command, args, {
    cwd: ROOT,
    encoding: "utf8",
    env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1" },
    timeout: 180_000,
    ...options,
  });

const commandOutput = (result) =>
  [result.stdout, result.stderr].filter(Boolean).join("\n").trim();

const assertSucceeded = (result, label) => {
  assert.equal(
    result.status,
    0,
    `${label} failed with status ${result.status}:\n${commandOutput(result)}`,
  );
};

const validate = (path) => run(process.execPath, [VALIDATOR_PATH, "--validate", path]);

const deepClone = (value) => JSON.parse(JSON.stringify(value));

const routeFile = (route) => {
  const relative = route.replace(/^\//, "");
  const candidates = relative
    ? [join(ROOT, "out", `${relative}.html`), join(ROOT, "out", relative, "index.html")]
    : [join(ROOT, "out", "index.html")];
  const found = candidates.find(existsSync);
  assert.ok(found, `static export is missing route /${relative}`);
  return found;
};

const decodeHtml = (value) =>
  value
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&quot;/g, '"')
    .replace(/&#x27;|&#39;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/\s+/g, " ")
    .trim();

const routeHtml = (route) => readFileSync(routeFile(route), "utf8");
const routeText = (route) => decodeHtml(routeHtml(route));

const assertIncludes = (text, value, context) => {
  assert.ok(
    text.includes(String(value)),
    `${context} does not render report-owned value ${JSON.stringify(value)}`,
  );
};

const rulingLabel = (value) =>
  ({
    YES: "Yes",
    NO: "No",
    CANNOT_JUDGE: "Cannot judge",
    UNANSWERED: "Unanswered",
  })[value];

test("canonical LABS report accepts only the frozen closed contract", async (t) => {
  assert.ok(existsSync(REPORT_PATH), "data/labs-report.json must be the one canonical UI input");
  assert.ok(existsSync(VALIDATOR_PATH), "the repository-owned report validator must exist");

  const report = JSON.parse(readFileSync(REPORT_PATH, "utf8"));
  assertSucceeded(validate(REPORT_PATH), "canonical report validation");

  const temporaryRoot = mkdtempSync(join(tmpdir(), "triana-labs-contract-"));
  t.after(() => rmSync(temporaryRoot, { recursive: true, force: true }));

  const mutations = [
    ["unknown field", (copy) => { copy.unexpected = true; }],
    ["unsupported schema", (copy) => { copy.schema_version = 2; }],
    ["duplicate identity", (copy) => {
      assert.ok(copy.behavior.groups.length, "fixture needs a behavior group");
      copy.behavior.groups.push(deepClone(copy.behavior.groups[0]));
    }],
    ["broken reference", (copy) => {
      assert.ok(copy.conversations.length, "fixture needs a conversation");
      copy.conversations[0].case_id = "missing-case";
    }],
    ["invalid denominator", (copy) => {
      copy.setup.understanding.accepted_record_count += 1;
    }],
    ["forbidden Release Review field", (copy) => { copy.verdict = "PASS"; }],
  ];

  for (const [name, mutate] of mutations) {
    await t.test(`rejects ${name}`, () => {
      const copy = deepClone(report);
      mutate(copy);
      const path = join(temporaryRoot, `${name.replaceAll(" ", "-")}.json`);
      writeFileSync(path, `${JSON.stringify(copy)}\n`);
      const result = validate(path);
      assert.notEqual(
        result.status,
        0,
        `${name} was accepted by the validator:\n${commandOutput(result)}`,
      );
    });
  }
});

test("seven Labs routes are a read-only projection of one report", () => {
  const report = JSON.parse(readFileSync(REPORT_PATH, "utf8"));
  assert.equal(report.artifact_kind, "labs_report");
  assert.equal(report.schema_version, 1);

  const jsonFiles = readdirSync(join(ROOT, "data"), { recursive: true })
    .filter((name) => name.endsWith(".json"))
    .sort();
  assert.deepEqual(jsonFiles, ["labs-report.json"], "Labs must build from one JSON report");

  assertSucceeded(run("npm", ["run", "build"]), "first static build");

  const conversationRoutes = report.conversations.map(
    ({ conversation_id }) => `/conversations/${conversation_id}`,
  );
  const persistentRoutes = ["/setup", "/behavior", "/cases", "/run", "/results", "/review"];
  const routes = [...persistentRoutes, ...conversationRoutes];
  const firstProjection = new Map(routes.map((route) => [route, routeText(route)]));

  const rootHtml = routeHtml("/");
  assert.match(rootHtml, /\/setup/, "root route must redirect to /setup");

  const navLabels = ["Overview", "User behavior", "Cases", "Runs", "Review"];
  for (const route of persistentRoutes) {
    const text = firstProjection.get(route);
    for (const label of navLabels) assertIncludes(text, label, `${route} Labs navigation`);
  }

  const setup = firstProjection.get("/setup");
  assertIncludes(setup, report.setup.source.display_name, "/setup");
  assertIncludes(setup, report.setup.adapter.mapping_status, "/setup");
  for (const key of [
    "physical_record_count",
    "accepted_record_count",
    "rejected_record_count",
    "usable_conversation_count",
  ]) assertIncludes(setup, report.setup.understanding[key], "/setup");
  for (const reason of report.setup.understanding.rejection_reasons) {
    assertIncludes(setup, reason.label, "/setup rejection reason");
    assertIncludes(setup, reason.count, "/setup rejection reason");
  }

  const behavior = firstProjection.get("/behavior");
  for (const group of report.behavior.groups) {
    assertIncludes(behavior, group.label, "/behavior");
    assertIncludes(behavior, group.support_count, "/behavior");
    assertIncludes(behavior, group.fidelity_label, "/behavior");
  }
  assertIncludes(behavior, report.behavior.population_claim, "/behavior");

  const cases = firstProjection.get("/cases");
  for (const item of report.cases) {
    assertIncludes(cases, item.title, "/cases");
    assertIncludes(cases, item.origin, "/cases");
    assertIncludes(cases, item.world_availability.status, "/cases");
    assertIncludes(cases, item.selection, "/cases");
  }

  const runPage = firstProjection.get("/run");
  assertIncludes(runPage, report.run.run_id, "/run");
  assertIncludes(runPage, report.run.recorded_state, "/run");
  assertIncludes(runPage, report.run.limits.selected_case_count, "/run");
  for (const conversation of report.conversations) {
    assertIncludes(runPage, conversation.conversation_id, "/run");
    assertIncludes(runPage, conversation.status, "/run");
  }

  const results = firstProjection.get("/results");
  for (const section of ["learned", "created", "happened", "judgment"]) {
    assertIncludes(results, report.results[section].headline, "/results");
    assertIncludes(results, report.results[section].detail, "/results");
  }
  for (const value of Object.values(report.results.accounting)) {
    assertIncludes(results, value === null ? "Unavailable" : value, "/results accounting");
  }

  const observedStates = new Set(report.conversations.map(({ status }) => status));
  for (const state of ["PARTIAL", "UNAVAILABLE", "NOT_STARTED"]) {
    assert.ok(observedStates.has(state), `fixture must exercise ${state}`);
    assertIncludes(runPage, state, "/run distinct state");
  }
  assert.ok(
    report.conversations.some(({ goal_state }) => goal_state === "UNKNOWN"),
    "fixture must exercise UNKNOWN goal evidence",
  );
  assert.ok(
    report.reviews.some(({ review_state }) => review_state === "UNREVIEWED"),
    "fixture must exercise UNREVIEWED human judgment",
  );

  const allVisible = [...firstProjection.values()].join(" ");
  assert.doesNotMatch(
    allVisible,
    /\bPASS\b|\bBLOCK\b|\bbaseline\b|\bcandidate\b|\bregression\b|release memory|release recommendation|accepted behavior/i,
    "Release Review vocabulary must not survive in Labs output",
  );
  assert.doesNotMatch(
    allVisible,
    /upload traces|choose file|run now|rerun|save ruling|approve|sign in|log in|create account/i,
    "read-only output must not advertise mutation, upload, execution, or auth actions",
  );

  for (const route of routes) {
    const html = routeHtml(route);
    assert.doesNotMatch(html, /<form\b/i, `${route} must not expose a write form`);
    for (const match of html.matchAll(/<(?:input|textarea|select)\b[^>]*>/gi)) {
      assert.match(
        match[0],
        /\bdisabled\b|aria-disabled=["']true["']|\breadonly\b/i,
        `${route} contains a mutable form control: ${match[0]}`,
      );
    }
  }

  for (const oldRoute of [
    "connect", "issues", "overview", "populations", "pr", "release-control",
    "release-memory", "release", "releases", "rolling-eval-set",
  ]) {
    assert.ok(
      !existsSync(join(ROOT, "out", `${oldRoute}.html`)) &&
        !existsSync(join(ROOT, "out", oldRoute, "index.html")),
      `old Release Review route /${oldRoute} must not be exported`,
    );
  }

  assertSucceeded(run("npm", ["run", "build"]), "second static build");
  const secondProjection = new Map(routes.map((route) => [route, routeText(route)]));
  assert.deepEqual(
    secondProjection,
    firstProjection,
    "identical report inputs must produce byte-identical visible route projections",
  );
});

test("conversation evidence and four human rulings retain their report ordering", () => {
  const report = JSON.parse(readFileSync(REPORT_PATH, "utf8"));

  for (const conversation of report.conversations) {
    const text = routeText(`/conversations/${conversation.conversation_id}`);
    let previousTurn = -1;
    for (const turn of conversation.turns) {
      const position = text.indexOf(turn.content);
      assert.ok(position > previousTurn, `${conversation.conversation_id} changed exact turn order`);
      previousTurn = position;

      const next = conversation.turns.find(({ ordinal }) => ordinal === turn.ordinal + 1);
      const boundary = next ? text.indexOf(next.content) : text.length;
      for (const refId of turn.evidence_ref_ids) {
        const ref = conversation.evidence_refs.find(({ evidence_ref_id }) => evidence_ref_id === refId);
        assert.ok(ref, `${conversation.conversation_id} has unresolved evidence ${refId}`);
        const refPosition = text.indexOf(ref.label, position);
        assert.ok(
          refPosition > position && refPosition < boundary,
          `${conversation.conversation_id} moved evidence ${refId} away from turn ${turn.ordinal}`,
        );
      }
      for (const gap of conversation.gaps.filter(({ turn_ordinal }) => turn_ordinal === turn.ordinal)) {
        const gapPosition = text.indexOf(gap.detail, position);
        assert.ok(
          gapPosition > position && gapPosition < boundary,
          `${conversation.conversation_id} moved gap ${gap.gap_id} away from turn ${turn.ordinal}`,
        );
      }
    }

    if (conversation.accounting.actual_cost_usd === null) {
      assert.match(text, /Unavailable/i, "missing conversation cost must not render as zero");
    }
  }

  const reviewText = routeText("/review");
  const questions = [
    ["Was the simulated user realistic", "realism"],
    ["Did each follow-up react", "adaptation"],
    ["Did the agent accomplish", "goal_completion"],
    ["Did the agent respect", "scope_privacy_boundaries"],
  ];
  const recorded = report.reviews.find(({ review_state }) => review_state === "RECORDED");
  assert.ok(recorded, "fixture needs a recorded review");
  assert.equal("verdict" in recorded, false, "reviews must not aggregate the four rulings");
  for (let index = 0; index < questions.length; index += 1) {
    const [question, field] = questions[index];
    const start = reviewText.indexOf(question);
    const end = index + 1 < questions.length
      ? reviewText.indexOf(questions[index + 1][0])
      : reviewText.length;
    assert.ok(start >= 0, `/review is missing question ${index + 1}`);
    assertIncludes(reviewText.slice(start, end), rulingLabel(recorded[field]), `/review question ${index + 1}`);
  }
  assert.doesNotMatch(reviewText, /overall|aggregate verdict|combined ruling/i);
});
