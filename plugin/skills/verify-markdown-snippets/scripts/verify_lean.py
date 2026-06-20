#!/usr/bin/env python3
"""Verify a single Lean 4 snippet with `lake env lean`.

Reads snippet source from --source-file, or stdin if --source-file is '-'.
Writes the snippet into `projects/lean-project/snippet_tmp/` and compiles it
with `lake env lean`, so the pinned toolchain (`lean-toolchain`) and any lake
dependencies declared in the project are on the search path. Lean elaborates
and type-checks every top-level command at compile time, so a clean exit with
no `error:` diagnostics means the snippet is well-typed.

Snippets are compiled as ordinary `.lean` files. Top-level definitions
(`def`, `inductive`, `structure`, `class`, `instance`, `example`, `theorem`)
and command macros (`#check`, `#eval`) are all valid at the top level, so —
unlike the Rust/Scala verifiers — no wrapping is needed. A bare top-level
*term* is a genuine Lean error (use `#eval`/`#check`/`example`), and is
reported as such.

Emits a JSON object on stdout:

    {
        "syntax": {"ok": true, "error": null},     # always ok — lean handles syntax
        "lean": {
            "ok": bool,
            "ran": bool,
            "errors":   [{"line": int, "col": int, "severity": str, "message": str, "rule": null}],
            "warnings": [ ... ],
            "raw_stderr": str | null,
            "exit_code": int | null,
            "wrapped":   false
        }
    }

Exit codes:
    0 — verification ran cleanly (snippet may still have errors, see JSON)
    2 — lean/lake is not available; verification could not run
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
LEAN_PROJECT = REPO_ROOT / "projects" / "lean-project"


def _lake_exe() -> str:
    """Resolve the `lake` binary. elan installs it under ~/.elan/bin, which is
    not always on a non-interactive shell's PATH, so fall back to that."""
    found = shutil.which("lake")
    if found:
        return found
    fallback = Path.home() / ".elan" / "bin" / "lake"
    return str(fallback) if fallback.exists() else "lake"

# Lean 4 diagnostic header, e.g.:
#   /path/_snippet_ab.lean:3:0: error: unknown identifier 'foo'
#   /path/_snippet_ab.lean:7:21: error(lean.unknownIdentifier): Unknown constant `Float.pi`
#   /path/_snippet_ab.lean:5:2: warning: declaration uses 'sorry'
# Lean 4.31 tags many diagnostics with an error class in parentheses —
# `error(lean.xxx):` — which is optional and captured as `rule` when present.
# Message bodies (type-mismatch detail, etc.) follow on subsequent lines until
# the next header.
_DIAG = re.compile(
    r"^(?P<path>.+?\.lean):(?P<line>\d+):(?P<col>\d+):\s*"
    r"(?P<sev>error|warning)(?:\((?P<rule>[^)]*)\))?:\s*(?P<msg>.*)$"
)


def parse_diagnostics(output: str, target_name: str) -> tuple[list[dict], list[dict]]:
    """Parse Lean console diagnostics, keeping only those from our snippet file."""
    errors: list[dict] = []
    warnings: list[dict] = []
    current: dict | None = None
    detail: list[str] = []

    def flush() -> None:
        nonlocal current, detail
        if current is None:
            return
        head = current.pop("_msg", "")
        body = "\n".join(detail).strip()
        message = f"{head}\n{body}".strip() if body else head
        current["message"] = message or "(no message)"
        (errors if current["severity"] == "error" else warnings).append(current)
        current, detail = None, []

    for line in output.splitlines():
        m = _DIAG.match(line)
        if m:
            flush()
            if not m.group("path").endswith(target_name):
                current = None  # diagnostic from another file — drop it and its body
                continue
            current = {
                "line": int(m.group("line")),
                "col": int(m.group("col")),
                "severity": m.group("sev"),
                "rule": m.group("rule"),
                "_msg": m.group("msg"),
            }
        elif current is not None:
            detail.append(line)
    flush()
    return errors, warnings


def run_lean(source: str) -> dict:
    if not LEAN_PROJECT.exists():
        return {
            "ok": False, "ran": False, "errors": [], "warnings": [],
            "raw_stderr": f"lean-project not found at {LEAN_PROJECT}",
            "exit_code": None, "wrapped": False,
        }

    tmp_dir = LEAN_PROJECT / "snippet_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    target_name = f"_snippet_{uuid.uuid4().hex[:12]}.lean"
    target_path = tmp_dir / target_name
    target_path.write_text(source, encoding="utf-8")

    try:
        proc = subprocess.run(
            [_lake_exe(), "env", "lean", str(target_path)],
            cwd=LEAN_PROJECT,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except FileNotFoundError:
        target_path.unlink(missing_ok=True)
        return {
            "ok": False, "ran": False, "errors": [], "warnings": [],
            "raw_stderr": "`lake`/`lean` is not installed or not on PATH",
            "exit_code": None, "wrapped": False,
        }
    except subprocess.TimeoutExpired:
        target_path.unlink(missing_ok=True)
        return {
            "ok": False, "ran": False, "errors": [], "warnings": [],
            "raw_stderr": "lean compile timed out after 180s",
            "exit_code": None, "wrapped": False,
        }
    finally:
        target_path.unlink(missing_ok=True)

    # Lean writes diagnostics to stdout; parse both streams to be safe.
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    errors, warnings = parse_diagnostics(combined, target_name)

    raw_stderr = None
    if proc.returncode != 0 and not errors:
        # lean/lake itself failed (bad toolchain, import of an unbuilt dep, …)
        raw_stderr = (combined)[:4000]

    return {
        # Clean only when lean exited 0 with no errors from our file.
        "ok": proc.returncode == 0 and not errors,
        "ran": True,
        "errors": errors,
        "warnings": warnings,
        "raw_stderr": raw_stderr,
        "exit_code": proc.returncode,
        "wrapped": False,
    }


def verify(source: str) -> dict:
    return {
        "syntax": {"ok": True, "error": None},
        "lean": run_lean(source),
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

    if not result["lean"]["ran"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
