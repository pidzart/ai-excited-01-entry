// Entry point for the ai-excited-01 submission "Supernova Crown".
//
// The artwork itself is entry.png, rendered by gen.py.  This script's
// whole job is delivery: copy entry.png into the directory named by
// the MAKEFUN_OUTPUT_DIR environment variable (falling back to
// /output), creating that directory first if it does not exist yet.
//
// Node 22 standard library only.

import { copyFileSync, existsSync, mkdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here: string = dirname(fileURLToPath(import.meta.url));
const source: string = join(here, "entry.png");
const outDir: string = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const target: string = join(outDir, "entry.png");

if (!existsSync(source)) {
  throw new Error(`entry.png not found next to main.ts (looked in ${here})`);
}

mkdirSync(outDir, { recursive: true });
copyFileSync(source, target);

const expected: number = statSync(source).size;
const delivered: number = statSync(target).size;
if (delivered !== expected) {
  throw new Error(
    `copy verification failed: wrote ${delivered} bytes, source is ${expected}`,
  );
}
console.log(`delivered entry.png (${delivered} bytes) -> ${target}`);
