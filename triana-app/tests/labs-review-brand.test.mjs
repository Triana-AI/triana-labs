import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const BRAND_ASSET = join(ROOT, "public", "brand", "triana-lazo-favicon-master.svg");
const APP_NAV = join(ROOT, "components", "AppNav.tsx");
const RESULTS_ROUTE = join(ROOT, "app", "results", "page.tsx");
const REVIEW_ROUTE = join(ROOT, "app", "review", "page.tsx");
const REPORT = join(ROOT, "data", "labs-report.json");

const source = (path) => readFileSync(path, "utf8");
const normalized = (value) => value.replace(/\s+/g, " ").trim();

const collectTsx = (root) => {
  if (!existsSync(root)) return "";
  return readdirSync(root, { recursive: true })
    .filter((entry) => extname(entry) === ".tsx")
    .map((entry) => source(join(root, entry)))
    .join("\n");
};

const assertNear = (text, label, patterns) => {
  const start = text.toLowerCase().indexOf(label.toLowerCase());
  assert.ok(start >= 0, `Review must define ${label}`);
  const definition = text.slice(start, start + 520);
  for (const pattern of patterns) {
    assert.match(definition, pattern, `${label} needs a plain-language definition matching ${pattern}`);
  }
  return start;
};

test("AppNav uses the official Lazo asset as an accessible Triana Labs brand", () => {
  assert.ok(existsSync(BRAND_ASSET), "official Lazo SVG is missing from public/brand");
  const svg = source(BRAND_ASSET);
  assert.match(svg, /^\s*<svg\b[\s\S]*<\/svg>\s*$/i, "brand asset must be a complete SVG");

  const nav = source(APP_NAV);
  assert.match(nav, /\/brand\/triana-lazo-favicon-master\.svg/, "AppNav must render the official Lazo asset");
  assert.match(nav, /(?:aria-label|alt)=["'{]*Triana Labs\b/i, "the rendered brand needs an accessible Triana Labs label");
  assert.match(nav, />\s*Triana Labs\s*</, "the expanded brand lockup must read Triana Labs");
});

test("Overview truthfully discloses the bundled report without limiting Triana to synthetic data", () => {
  const overview = normalized(`${source(RESULTS_ROUTE)}\n${collectTsx(join(ROOT, "components", "labs"))}`);

  assert.match(overview, /Bundled demo report/i);
  assert.match(
    overview,
    /public build.{0,180}ships.{0,100}one.{0,80}synthetic artifact/i,
    "Overview must explain what artifact this public build ships",
  );
  assert.match(
    overview,
    /(?:UI|interface|renderer).{0,80}report[- ]driven|report[- ]driven.{0,80}(?:UI|interface|renderer)/i,
    "Overview must identify the UI as report-driven",
  );
  assert.doesNotMatch(
    overview,
    /Triana.{0,60}(?:only|solely|exclusively).{0,60}synthetic|(?:only|solely|exclusively).{0,60}synthetic data/i,
    "the bundled demo disclosure must not claim Triana only supports synthetic data",
  );
});

test("Review explains four independent dimensions before report-backed rulings", () => {
  const review = normalized(`${source(REVIEW_ROUTE)}\n${collectTsx(join(ROOT, "components", "labs"))}`);
  const queueStart = review.toLowerCase().indexOf("recorded rulings");
  assert.ok(queueStart >= 0, "Review needs a recorded-rulings queue");

  assert.match(
    review.slice(0, queueStart),
    /human.{0,100}(?:decid|judg|review).{0,180}(?:conversation|simulation|agent)/i,
    "Review must first explain what the human is deciding and why",
  );

  const definitions = [
    assertNear(review, "Realism", [/simulated user/i, /(?:believ|realistic|situation)/i]),
    assertNear(review, "Adaptation", [/follow-up/i, /agent.{0,80}(?:said|response)|(?:said|response).{0,80}agent/i]),
    assertNear(review, "Goal completion", [/(?:stated|case) goal/i, /(?:accomplish|complete|achiev)/i]),
    assertNear(review, "Scope, privacy, and boundaries", [/scope/i, /privacy/i, /boundar/i]),
  ];
  for (const position of definitions) {
    assert.ok(position < queueStart, "dimension definitions must appear before recorded rulings");
  }

  assert.match(
    review.slice(0, queueStart),
    /(?:do not|does not|never|aren't|are not).{0,70}(?:combine|roll up|aggregate).{0,70}score/i,
    "Review must say the dimensions do not combine into a score",
  );
  assert.match(
    review.slice(0, queueStart),
    /Cannot judge.{0,140}(?:missing|insufficient|unavailable).{0,80}evidence/i,
    "Cannot judge must mean evidence is missing or insufficient",
  );
  assert.match(
    review.slice(0, queueStart),
    /Cannot judge.{0,220}(?:does not|doesn't|is not|isn't).{0,60}(?:failure|failed|run failed)/i,
    "Cannot judge must not be framed as a failed run",
  );
});

test("Review queues every report conversation and keeps answers read-only", () => {
  const report = JSON.parse(source(REPORT));
  assert.ok(report.conversations.length > 0, "canonical report needs conversations");

  const review = normalized(`${source(REVIEW_ROUTE)}\n${collectTsx(join(ROOT, "components", "labs"))}`);
  assert.match(
    review,
    /labsReport\.conversations\.map|conversations\.map/,
    "the queue must be driven by every report conversation, not only recorded reviews",
  );
  assert.match(review, /review_state/, "each queued conversation must expose its review status");
  assert.match(review, /displayRuling\s*\(\s*review\s*\[\s*field\s*\]\s*\)/, "answers must come from report rulings");
  assert.match(review, /\/conversations\/\$\{[^}]*conversation_id[^}]*\}/, "each queue item must link to its conversation");
  assert.doesNotMatch(review, /<form\b|<input\b|<textarea\b|<select\b|onChange\s*=|onSubmit\s*=/i, "recorded answers must remain read-only");
  assert.doesNotMatch(review, /aggregate verdict|combined ruling|overall score/i);
});
