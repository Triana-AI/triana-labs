import { readFile, readdir, writeFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { compileFromFile } from "json-schema-to-typescript";

const here = dirname(fileURLToPath(import.meta.url));
const consumerRoot = resolve(here, "..");
const repositoryRoot = resolve(consumerRoot, "..", "..");
const schemaRoot = resolve(repositoryRoot, "schemas");
const outputRoot = resolve(consumerRoot, "types");
const checkOnly = process.argv.slice(2).includes("--check");

const schemaFiles = (await readdir(schemaRoot))
  .filter((name) => name.endsWith(".schema.json"))
  .sort();

let drift = false;
await mkdir(outputRoot, { recursive: true });
for (const schemaFile of schemaFiles) {
  const source = resolve(schemaRoot, schemaFile);
  const destination = resolve(
    outputRoot,
    schemaFile.replace(".schema.json", ".d.ts"),
  );
  const generated = await compileFromFile(source, {
    bannerComment:
      "/* Generated from schemas/. Do not edit; run npm run generate. */",
    format: true,
    unknownAny: false,
  });
  if (checkOnly) {
    const existing = await readFile(destination, "utf8").catch(() => "");
    if (existing !== generated) {
      console.error(`generated type drift: ${schemaFile}`);
      drift = true;
    }
  } else {
    await writeFile(destination, generated, "utf8");
  }
}

if (drift) {
  process.exitCode = 1;
}
