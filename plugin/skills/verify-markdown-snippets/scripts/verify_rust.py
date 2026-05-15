#!/usr/bin/env python3
"""Verify a single Rust snippet with `cargo check`.

Reads snippet source from --source-file, or stdin if --source-file is '-'.
Writes the snippet as a temporary bin target inside `projects/rust-project/`
and runs `cargo check --bin <name> --message-format=json` so the pinned
toolchain (`rust-toolchain.toml`) and any Cargo.toml dev-dependencies
(serde, anyhow, thiserror, …) are available to the snippet.

Emits a JSON object on stdout:

    {
        "syntax": {"ok": bool, "error": null},     # always ok — cargo check handles syntax
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
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
RUST_PROJECT = REPO_ROOT / "projects" / "rust-project"

# Rustdoc convention: if a snippet declares its own `fn main`, leave it alone.
# Otherwise wrap the whole thing in `fn _snippet() { ... }`. Rust allows
# nested items inside a function, so this handles both "items only" and
# "items mixed with statements" snippets without needing a deeper heuristic.
_FN_MAIN = re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+main\b", re.MULTILINE)


def needs_wrap(source: str) -> bool:
    return _FN_MAIN.search(source) is None


def _wrap(source: str) -> str:
    # Adds exactly one line before the snippet, so rustc line N → snippet line N-1.
    # Wraps in fn main() (not _snippet) so the file is a valid bin target —
    # `cargo rustc --bin` requires an entry point.
    return f"fn main() {{\n{source}\n}}\n"


def run_cargo_check(source: str) -> dict:
    if not RUST_PROJECT.exists():
        return {
            "ok": False, "ran": False, "errors": [], "warnings": [],
            "raw_stderr": f"rust-project not found at {RUST_PROJECT}",
            "exit_code": None, "wrapped": False,
        }

    wrapped = needs_wrap(source)
    final_source = _wrap(source) if wrapped else source

    # Each snippet becomes its own bin target inside src/bin/. Cargo discovers
    # files in src/bin/ as separate bin targets, and `cargo check --bin X`
    # only checks X — so leftover files from concurrent runs don't interfere.
    bin_dir = RUST_PROJECT / "src" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    target_name = f"_snippet_{uuid.uuid4().hex[:12]}"
    bin_path = bin_dir / f"{target_name}.rs"
    bin_path.write_text(final_source, encoding="utf-8")

    try:
        proc = subprocess.run(
            [
                # `cargo rustc` (not `cargo check`) is required here because it
                # is the only cargo subcommand that supports `-- <rustc args>`
                # passthrough. `--emit=metadata` reproduces `cargo check`'s
                # behavior (no linking).
                "cargo", "rustc",
                "--bin", target_name,
                "--message-format=json",
                "--quiet",
                "--",
                "--emit=metadata",
                # Snippets often have unused names by documentation convention.
                # Silence those so the report focuses on real type/syntax errors.
                "-A", "dead_code",
                "-A", "unused_imports",
                "-A", "unused_variables",
                "-A", "unused_mut",
                "-A", "unused_assignments",
                "-A", "unused_macros",
                "-A", "unused_must_use",
                # Snippets are typically extracted prose, not crates — the
                # crate-level missing-docs warning is noise.
                "-A", "missing_docs",
                # Catalog snippets legitimately demonstrate `unsafe`. The
                # project's `deny(unsafe_code)` lint is policy for in-tree
                # code, not for documentation we extract from.
                "-A", "unsafe_code",
            ],
            cwd=RUST_PROJECT,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except FileNotFoundError:
        bin_path.unlink(missing_ok=True)
        return {
            "ok": False, "ran": False, "errors": [], "warnings": [],
            "raw_stderr": "`cargo` is not installed or not on PATH",
            "exit_code": None, "wrapped": wrapped,
        }
    except subprocess.TimeoutExpired:
        bin_path.unlink(missing_ok=True)
        return {
            "ok": False, "ran": False, "errors": [], "warnings": [],
            "raw_stderr": "cargo check timed out after 180s",
            "exit_code": None, "wrapped": wrapped,
        }
    finally:
        bin_path.unlink(missing_ok=True)

    errors: list[dict] = []
    warnings: list[dict] = []
    parse_failures: list[str] = []
    line_offset = 1 if wrapped else 0  # rustc line N → snippet line N - offset

    for raw in proc.stdout.splitlines():
        raw = raw.strip()
        if not raw or not raw.startswith("{"):
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            parse_failures.append(raw[:200])
            continue
        if not isinstance(obj, dict):
            continue
        # Cargo emits several message kinds; only compiler-message carries
        # rustc diagnostics. Cargo's own build-script and artifact records
        # we discard.
        if obj.get("reason") != "compiler-message":
            continue
        d = obj.get("message") or {}
        level = d.get("level")
        if level not in ("error", "warning"):
            continue

        spans = d.get("spans") or []
        primary = next((s for s in spans if s.get("is_primary")), spans[0] if spans else None)
        if primary is None:
            continue
        # Only count diagnostics that originate in *our* snippet file. Cargo
        # also surfaces warnings from dependencies during initial compilation;
        # those would pollute the report.
        file_name = primary.get("file_name", "")
        if not file_name.endswith(f"{target_name}.rs"):
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
    # If cargo itself blew up (e.g., Cargo.toml broken), surface raw stderr.
    if proc.returncode != 0 and not errors:
        raw_stderr = (proc.stderr or "")[:4000] or raw_stderr

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
        "rustc": run_cargo_check(source),
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
