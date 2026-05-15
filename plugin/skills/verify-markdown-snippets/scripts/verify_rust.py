#!/usr/bin/env python3
"""Verify a single Rust snippet with rustc.

Reads snippet source from --source-file, or stdin if --source-file is '-'.
Runs `rustc` from within `projects/rust-project/` so the pinned toolchain
(`rust-toolchain.toml`) is used.

Emits a JSON object on stdout:

    {
        "syntax": {"ok": bool, "error": null},     # always ok — rustc handles syntax
        "rustc": {
            "ok": bool,
            "ran": bool,
            "errors":   [{"line": int, "col": int, "severity": str, "message": str, "rule": str | null}],
            "warnings": [ ... ],
            "raw_stderr": str | null,
            "exit_code": int | null,
            "wrapped":   bool                       # true if the snippet was wrapped in fn _snippet()
        }
    }

Exit codes:
    0 — verification ran cleanly (snippet may still have errors, see JSON)
    2 — rustc is not available; verification could not run
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
RUST_PROJECT = REPO_ROOT / "projects" / "rust-project"
EDITION = "2024"

# Rustdoc convention: if a snippet declares its own `fn main`, leave it alone.
# Otherwise wrap the whole thing in `fn _snippet() { ... }`. Rust allows
# nested items inside a function, so this handles both "items only" and
# "items mixed with statements" snippets without needing a deeper heuristic.
_FN_MAIN = re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+main\b", re.MULTILINE)


def needs_wrap(source: str) -> bool:
    return _FN_MAIN.search(source) is None


def _wrap(source: str) -> str:
    # Adds exactly one line before the snippet, so rustc line N → snippet line N-1.
    return f"fn _snippet() {{\n{source}\n}}\n"


def run_rustc(source: str) -> dict:
    if not RUST_PROJECT.exists():
        return {
            "ok": False, "ran": False, "errors": [], "warnings": [],
            "raw_stderr": f"rust-project not found at {RUST_PROJECT}",
            "exit_code": None, "wrapped": False,
        }

    wrapped = needs_wrap(source)
    final_source = _wrap(source) if wrapped else source

    tmp_dir = RUST_PROJECT / "snippet_tmp"
    tmp_dir.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".rs", dir=tmp_dir, delete=False, encoding="utf-8",
    ) as f:
        f.write(final_source)
        tmp_path = Path(f.name)
    meta_path = tmp_path.with_suffix(".rmeta")

    try:
        proc = subprocess.run(
            [
                "rustc",
                "--edition", EDITION,
                "--crate-type", "lib",
                "--error-format=json",
                "--emit=metadata",
                "-o", str(meta_path),
                # Snippets often contain unused names — that's a documentation
                # convention, not a defect. Silence those so we can focus on
                # real syntax/type errors.
                "-A", "dead_code",
                "-A", "unused_imports",
                "-A", "unused_variables",
                "-A", "unused_mut",
                "-A", "unused_assignments",
                "-A", "unused_macros",
                "-A", "unused_must_use",
                str(tmp_path),
            ],
            cwd=RUST_PROJECT,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        tmp_path.unlink(missing_ok=True)
        return {
            "ok": False, "ran": False, "errors": [], "warnings": [],
            "raw_stderr": "`rustc` is not installed or not on PATH",
            "exit_code": None, "wrapped": wrapped,
        }
    except subprocess.TimeoutExpired:
        tmp_path.unlink(missing_ok=True)
        return {
            "ok": False, "ran": False, "errors": [], "warnings": [],
            "raw_stderr": "rustc timed out after 60s",
            "exit_code": None, "wrapped": wrapped,
        }
    finally:
        tmp_path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)

    errors: list[dict] = []
    warnings: list[dict] = []
    parse_failures: list[str] = []
    line_offset = 1 if wrapped else 0  # rustc line N → snippet line N - offset

    for raw in proc.stderr.splitlines():
        raw = raw.strip()
        if not raw or not raw.startswith("{"):
            continue
        try:
            d = json.loads(raw)
        except json.JSONDecodeError:
            parse_failures.append(raw[:200])
            continue
        if not isinstance(d, dict):
            continue
        level = d.get("level")
        if level not in ("error", "warning"):
            continue

        spans = d.get("spans") or []
        primary = next((s for s in spans if s.get("is_primary")), spans[0] if spans else None)
        # Skip span-less summary lines like "aborting due to N previous errors";
        # they're noise, the underlying errors are reported separately.
        if primary is None:
            continue
        line_no = primary.get("line_start", 0) - line_offset
        col_no = primary.get("column_start", 0)
        code = d.get("code")
        rule = code.get("code") if isinstance(code, dict) else None

        entry = {
            "line": max(line_no, 0),
            "col": col_no,
            "severity": level,
            "message": d.get("message", ""),
            "rule": rule,
        }
        if level == "error":
            errors.append(entry)
        else:
            warnings.append(entry)

    raw_stderr = "\n".join(parse_failures)[:4000] if parse_failures else None
    # If rustc itself blew up (no JSON, nonzero exit), surface the raw stderr.
    if proc.returncode != 0 and not errors and not warnings:
        raw_stderr = (proc.stderr or proc.stdout or "")[:4000]

    return {
        "ok": len(errors) == 0,
        "ran": True,
        "errors": errors,
        "warnings": warnings,
        "raw_stderr": raw_stderr,
        "exit_code": proc.returncode,
        "wrapped": wrapped,
    }


def verify(source: str) -> dict:
    return {
        "syntax": {"ok": True, "error": None},
        "rustc": run_rustc(source),
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

    if not result["rustc"]["ran"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
