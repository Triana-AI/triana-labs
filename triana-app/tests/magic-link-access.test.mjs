import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));

const filesBelow = (directory) => {
  if (!existsSync(directory)) return [];
  return readdirSync(directory).flatMap((name) => {
    const path = join(directory, name);
    return statSync(path).isDirectory() ? filesBelow(path) : [path];
  });
};

const text = (paths) => paths.map((path) => readFileSync(path, "utf8")).join("\n");

test("magic-link owner keeps core access and can request locked features", () => {
  const loginSource = text(filesBelow(join(ROOT, "app", "login")).concat(
    filesBelow(join(ROOT, "components", "self-serve")),
  ));
  assert.match(loginSource, /type=["']email["']/, "login must accept an email address");
  assert.match(loginSource, /signInWithOtp/, "login must send a Supabase magic link");
  assert.match(loginSource, /shouldCreateUser\s*:\s*true/, "magic-link signup must remain open");
  assert.match(loginSource, /check your email|check your inbox|email sent/i,
    "login must return neutral check-your-email feedback");
  assert.doesNotMatch(loginSource, /account (?:exists|not found)|unknown account|registered user/i,
    "login feedback must not disclose whether the email already exists");

  const appSource = text(filesBelow(join(ROOT, "app")).concat(
    filesBelow(join(ROOT, "components")), filesBelow(join(ROOT, "lib")),
  ).filter((path) => /\.(?:ts|tsx)$/.test(path)));
  assert.doesNotMatch(appSource, /owner bearer token|paste a development jwt|sessionStorage|getSessionToken|setSessionToken|TOKEN_KEY/i,
    "the pasted bearer-token scaffold must be removed");

  const confirmationFiles = filesBelow(join(ROOT, "app", "auth"))
    .filter((path) => /route\.(?:ts|js)$/.test(path));
  assert.ok(confirmationFiles.length > 0, "a magic-link confirmation route must exist");
  const confirmationSource = text(confirmationFiles);
  assert.match(confirmationSource, /exchangeCodeForSession|verifyOtp/,
    "confirmation must establish the managed Supabase session");
  assert.match(confirmationSource, /["']\/agents["']/, "confirmation must continue to core agents");
  assert.match(confirmationSource, /no-store|force-dynamic|revalidate\s*=\s*0/i,
    "auth confirmation responses must not be cached");

  const apiSource = text(filesBelow(join(ROOT, "lib", "self-serve")).concat(
    filesBelow(join(ROOT, "lib", "supabase")),
  ));
  assert.match(apiSource, /getSession/, "API authentication must read the managed session");
  assert.match(apiSource, /access_token/, "API authentication must use the Supabase access token");
  assert.match(apiSource, /Authorization[\s\S]*Bearer/, "API requests must send the managed bearer token");
  assert.match(appSource, /signOut/, "the authenticated shell must expose managed logout");

  for (const state of ["AVAILABLE", "LOCKED", "REQUESTED"]) {
    assert.match(loginSource, new RegExp(`["']${state}["']`), `feature UI must render ${state}`);
  }
  assert.match(apiSource, /\/api\/v1\/me\/features/, "feature state must come from the backend");
  assert.match(apiSource, /\/api\/v1\/me\/access-requests/, "access requests must use the backend boundary");
  assert.match(loginSource, /request access/i, "locked features must expose a request-access action");

  assert.ok(existsSync(join(ROOT, "app", "agents", "page.tsx")), "core agents must remain reachable");
  assert.match(apiSource, /uploadImport[\s\S]*\/api\/v1\/agents\//,
    "core trace upload must remain reachable after feature gating");
  assert.ok(filesBelow(join(ROOT, "app", "agents")).some((path) =>
    /imports[\\/][^\\/]+[\\/]conversations[\\/][^\\/]+[\\/]page\.tsx$/.test(path),
  ), "core conversation viewer route must remain reachable");
});
