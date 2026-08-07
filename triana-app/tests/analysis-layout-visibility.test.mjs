import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path) => readFileSync(path, "utf8");
const analysis = read(join(ROOT, "app", "analysis", "page.tsx"));
const viewer = read(
  join(ROOT, "components", "conversation", "ConversationViewer.tsx"),
);
const css = read(join(ROOT, "app", "globals.css"));

test("trace input and report lookup use bounded non-overlapping control grids", () => {
  assert.match(
    analysis,
    /<form[^>]*className="analysis-controls"[^>]*data-layout="trace"/s,
    "trace inputs need their own structural grid",
  );
  assert.match(
    analysis,
    /<(?:div|section)[^>]*className="analysis-controls"[^>]*data-layout="report"/s,
    "report lookup needs its own structural grid",
  );
  assert.ok(
    (analysis.match(/className="analysis-field"/g) ?? []).length >= 3,
    "every labeled trace/report field needs a bounded grid cell",
  );
  assert.ok(
    (analysis.match(/className="analysis-control"/g) ?? []).length >= 3,
    "select and text controls need one width-safe class",
  );
  assert.match(css, /\.analysis-controls\s*\{[^}]*display\s*:\s*grid[^}]*align-items\s*:\s*end[^}]*\}/s);
  assert.match(
    css,
    /\.analysis-controls\[data-layout="trace"\]\s*\{[^}]*grid-template-columns\s*:\s*minmax\([^;]*minmax\(0,[^;]*auto[^}]*\}/s,
  );
  assert.match(
    css,
    /\.analysis-controls\[data-layout="report"\]\s*\{[^}]*grid-template-columns\s*:\s*minmax\(0,[^;]*auto[^}]*\}/s,
  );
  assert.match(css, /\.analysis-field\s*\{[^}]*min-width\s*:\s*0[^}]*\}/s);
  assert.match(
    css,
    /\.analysis-control\s*\{[^}]*width\s*:\s*100%[^}]*min-width\s*:\s*0[^}]*\}/s,
  );
  assert.match(
    css,
    /@media[^}]*max-width[^}]*\{[\s\S]*\.analysis-controls[^}]*grid-template-columns\s*:\s*1fr/s,
    "narrow screens must collapse both control grids before they overlap",
  );
});

test("conversation evidence and message copy declare visible foreground/background pairs", () => {
  assert.match(
    viewer,
    /<aside\s+className="conversation-context conversation-evidence-pane"/,
    "the optional report evidence pane needs an explicit visibility class",
  );
  assert.match(
    viewer,
    /<p\s+className="conversation-message-text">\{event\.content\}<\/p>/,
    "message copy needs an explicit visibility class",
  );
  assert.match(
    css,
    /\.conversation-evidence-pane\s*\{[^}]*background(?:-color)?\s*:\s*var\(--surface-subtle\)[^}]*color\s*:\s*var\(--ink\)[^}]*\}/s,
    "evidence context must not inherit an unreadable foreground",
  );
  assert.match(
    css,
    /\.conversation-message-text\s*\{[^}]*background(?:-color)?\s*:\s*var\(--surface\)[^}]*color\s*:\s*var\(--ink\)[^}]*\}/s,
    "message text must carry an explicit readable color pair",
  );
});
