#!/usr/bin/env python3
"""Verify a single TypeScript snippet with the TypeScript compiler (tsc).

Reads snippet source from --source-file, or stdin if --source-file is '-'.
Writes the snippet to a temp `.ts` file inside `projects/typescript-project/`
and runs that project's pinned `tsc --noEmit --strict ...` so the TypeScript
version and strictness are stable across runs. Each snippet is checked on its
own (one file per tsc invocation), so a name used but not defined in the
snippet is a real "not copy-pasteable" finding, the same isolation policy the
other verifiers use.

Emits a JSON object on stdout:

    {
        "syntax": {"ok": true, "error": null},     # always ok — tsc handles syntax as diagnostics
        "tsc": {
            "ok": bool,
            "ran": bool,
            "errors":   [{"line": int, "col": int, "severity": str, "message": str, "rule": str | null}],
            "warnings": [ ... ],
            "raw_stderr": str | null,
            "exit_code": int | null
        }
    }

Exit codes:
    0 — verification ran cleanly (snippet may still have errors, see JSON)
    2 — tsc/node is not available; verification could not run
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
TS_PROJECT = REPO_ROOT / "projects" / "typescript-project"
# Tiny ambient `console` declaration compiled alongside each snippet. See the
# `--lib ES2022` (no DOM) note below.
GLOBALS_DTS = TS_PROJECT / "globals.d.ts"

# Strictness for snippet checking. Kept in sync with
# projects/typescript-project/tsconfig.json (tsc ignores tsconfig.json when a
# file is passed explicitly on the command line, so the flags live here too).
# `--lib ES2022` deliberately omits DOM: these are type-system docs, and the
# DOM lib's globals (Event, Comment, Selection, Permissions, ...) would collide
# with domain types the docs define. globals.d.ts supplies `console`.
TSC_FLAGS = [
    "--noEmit",
    "--strict",
    "--pretty", "false",
    "--target", "ES2022",
    "--module", "ESNext",
    "--moduleResolution", "bundler",
    "--lib", "ES2022",
    "--skipLibCheck",
    "--exactOptionalPropertyTypes",
    "--noUncheckedIndexedAccess",
    "--forceConsistentCasingInFileNames",
]

# tsc text diagnostic (`--pretty false`):  path/file.ts(LINE,COL): error TS1234: message
_DIAG = re.compile(
    r"^(?P<file>.+?)\((?P<line>\d+),(?P<col>\d+)\):\s+"
    r"(?P<sev>error|warning)\s+(?P<code>TS\d+):\s+(?P<msg>.*)$"
)


def _tsc_bin() -> Path:
    return TS_PROJECT / "node_modules" / ".bin" / "tsc"


def _not_ran(why: str) -> dict:
    return {
        "ok": False, "ran": False, "errors": [], "warnings": [],
        "raw_stderr": why, "exit_code": None,
    }


def run_tsc(source: str) -> dict:
    if not TS_PROJECT.exists():
        return _not_ran(f"typescript-project not found at {TS_PROJECT}")
    tsc = _tsc_bin()
    if not tsc.exists():
        return _not_ran(
            f"tsc not installed at {tsc}; run `npm install` in "
            f"{TS_PROJECT} (or `make setup`)"
        )

    tmp_dir = TS_PROJECT / "snippet_tmp"
    tmp_dir.mkdir(exist_ok=True)
    tmp_path = tmp_dir / f"_snippet_{uuid.uuid4().hex[:12]}.ts"
    tmp_path.write_text(source, encoding="utf-8")

    cmd = [str(tsc), *TSC_FLAGS]
    if GLOBALS_DTS.exists():
        cmd.append(str(GLOBALS_DTS))
    cmd.append(str(tmp_path))

    try:
        proc = subprocess.run(
            cmd,
            cwd=TS_PROJECT,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        tmp_path.unlink(missing_ok=True)
        return _not_ran("`node`/`tsc` is not installed or not on PATH")
    except subprocess.TimeoutExpired:
        tmp_path.unlink(missing_ok=True)
        return _not_ran("tsc timed out after 120s")
    finally:
        tmp_path.unlink(missing_ok=True)

    errors: list[dict] = []
    warnings: list[dict] = []
    # tsc prints diagnostics to stdout; node/loader failures go to stderr.
    for raw in (proc.stdout or "").splitlines():
        m = _DIAG.match(raw.strip())
        if not m:
            continue
        # Only diagnostics for our temp file — ignore any lib/global noise.
        if not m.group("file").endswith(tmp_path.name):
            continue
        entry = {
            "line": int(m.group("line")),
            "col": int(m.group("col")),
            "severity": m.group("sev"),
            "message": m.group("msg"),
            "rule": m.group("code"),
        }
        (errors if m.group("sev") == "error" else warnings).append(entry)

    # tsc exited non-zero but we parsed no error for our file — that means tsc
    # itself failed (bad flag, node error, missing lib) rather than the snippet
    # being wrong. Surface stderr/stdout and mark the run as not-ran so the
    # orchestrator reports a tool_error instead of a spurious snippet failure.
    if proc.returncode != 0 and not errors:
        raw = ((proc.stderr or "") + (proc.stdout or "")).strip()[:4000]
        if raw:
            return {
                "ok": False, "ran": False, "errors": [], "warnings": warnings,
                "raw_stderr": raw, "exit_code": proc.returncode,
            }

    return {
        "ok": len(errors) == 0,
        "ran": True,
        "errors": errors,
        "warnings": warnings,
        "raw_stderr": None,
        "exit_code": proc.returncode,
    }


def verify(source: str) -> dict:
    return {
        "syntax": {"ok": True, "error": None},
        "tsc": run_tsc(source),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-file",
        required=True,
        help="Path to a file containing the snippet source, or '-' for stdin.",
    )
    args = parser.parse_args()
    if args.source_file == "-":
        source = sys.stdin.read()
    else:
        source = Path(args.source_file).read_text(encoding="utf-8")

    result = verify(source)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")

    return 0 if result["tsc"]["ran"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
