import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));

const filesBelow = (directory) => {
  if (!existsSync(directory)) return [];
  return readdirSync(directory).flatMap((name) => {
    const path = join(directory, name);
    return statSync(path).isDirectory() ? filesBelow(path) : [path];
  });
};

const sourceFiles = filesBelow(join(ROOT, "app"))
  .concat(filesBelow(join(ROOT, "components")), filesBelow(join(ROOT, "lib")))
  .filter((path) => /\.(?:ts|tsx)$/.test(path));

const source = (paths) => paths.map((path) => readFileSync(path, "utf8")).join("\n");
const normalizedRoute = (path) => relative(join(ROOT, "app"), path)
  .replaceAll("\\", "/")
  .replace(/(^|\/)\([^/]+\)(?=\/)/g, "")
  .replace(/\[[^\]]+\]/g, "[]")
  .replace(/\/page\.tsx$/, "")
  .replace(/^page\.tsx$/, "");

test("self-serve owner can reach trace import accounting and a reusable conversation timeline", () => {
  const pages = sourceFiles.filter((path) => path.endsWith("page.tsx"));
  const routes = new Set(pages.map(normalizedRoute));
  for (const route of [
    "login",
    "agents",
    "agents/[]",
    "agents/[]/imports/[]",
    "agents/[]/imports/[]/conversations/[]",
  ]) {
    assert.ok(routes.has(route), `missing self-serve route /${route}`);
  }

  const selfServeSource = source(sourceFiles.filter((path) =>
    /(?:app|components|lib)[\\/](?:\(self-serve\)[\\/])?(?:login|agents|self-serve|conversation)/.test(path),
  ));
  assert.match(selfServeSource, /log\s*in|sign\s*in/i, "login must expose an authentication action");
  assert.match(selfServeSource, /add\s+agent|create\s+agent/i, "agents must expose creation");
  assert.match(selfServeSource, /\.jsonl/i, "agent imports must prescribe JSONL upload");
  assert.match(selfServeSource, /accepted/i, "import detail must show accepted accounting");
  assert.match(selfServeSource, /rejected/i, "import detail must show rejected accounting");
  assert.match(selfServeSource, /failed|unavailable|error/i, "failed imports must remain visibly typed");

  const conversationSource = source(sourceFiles.filter((path) =>
    /components[\\/]conversation|lib[\\/](?:self-serve|conversation)/.test(path),
  ));
  assert.match(conversationSource, /export\s+(?:default\s+)?(?:function|const)\s+ConversationViewer|export\s*\{[^}]*ConversationViewer/s,
    "ConversationViewer must be an exported reusable element");
  for (const eventKind of ["message", "tool_call", "tool_result", "terminal", "gap"]) {
    assert.match(conversationSource, new RegExp(`[\"']${eventKind}[\"']`),
      `ConversationViewer contract must represent ${eventKind}`);
  }
  assert.match(conversationSource, /LegacyReportConversationAdapter/,
    "the existing report conversation must remain available through an explicit adapter");

  const legacyRoute = join(ROOT, "app", "conversations", "[conversation_id]", "page.tsx");
  assert.ok(existsSync(legacyRoute), "legacy report conversation route must remain reachable");
  assert.match(readFileSync(legacyRoute, "utf8"), /LegacyReportConversationAdapter/,
    "legacy report route must use the reusable viewer adapter");
});
