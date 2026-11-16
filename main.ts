// ai-excited-01 entrypoint.
//
// The artwork itself is rendered ahead of time by gen.py and shipped in
// this repository as entry.png, right beside this file.  All this
// program has to do at grade time is deliver that image, untouched, to
// the output directory the runner names:
//
//   * MAKEFUN_OUTPUT_DIR set   -> copy there
//   * MAKEFUN_OUTPUT_DIR unset -> copy to /output
//
// After copying, the file is read back and its length is compared with
// the source, so a truncated or partial copy fails loudly instead of
// silently submitting a broken image.

import { copyFileSync, mkdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// Resolve the folder this file lives in, wherever the repo was cloned.
const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, "entry.png");

// Pick the destination: the runner's env var wins, /output is the
// documented fallback.
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const target = join(outDir, "entry.png");

// Create the output folder (including parents) when it is missing;
// recursive mkdir is a no-op when it already exists.
mkdirSync(outDir, { recursive: true });

// Ship the image byte for byte.
copyFileSync(source, target);

// Read-back check: the copy on disk must be exactly as long as the
// original.  statSync gives us the byte length without loading the
// whole PNG into memory.
const sourceBytes = statSync(source).size;
const copiedBytes = statSync(target).size;
if (copiedBytes !== sourceBytes) {
  throw new Error(
    `copy mismatch: source is ${sourceBytes} bytes, copy is ${copiedBytes}`,
  );
}

console.log(`entry.png delivered to ${target} (${copiedBytes} bytes)`);
