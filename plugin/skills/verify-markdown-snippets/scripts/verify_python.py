#!/usr/bin/env python3
"""Verify a single Python snippet with ast.parse and pyright.

Reads snippet source from --source-file, or stdin if --source-file is '-'.
Runs pyright from within `projects/python-project/` so the project's venv and
pyright config are used.

Emits a JSON object on stdout:

    {
        "syntax": {"ok": bool, "error": {...} | null},
        "pyright": {
            "ok": bool,
            "ran": bool,
            "errors": [{"line": int, "col": int, "severity": str, "message": str, "rule": str | null}],
            "warnings": [ ... ],
            "raw_stderr": str | null,
            "exit_code": int | null
        }
    }

Exit codes:
    0 — verification ran cleanly (snippet may still have errors, see JSON)
    2 — pyright or the venv is not available; verification could not run
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
PYTHON_PROJECT = REPO_ROOT / "projects" / "python-project"

# Delegate syntax parsing to a subprocess in the project venv so the check
# matches the Python version that pyright targets. Using the system Python
# would reject newer syntax (match statements, PEP 695 type aliases, etc.)
# even when the project itself accepts them.
_SYNTAX_CHECK_SCRIPT = r"""
import ast, json, sys
src = sys.stdin.read()
try:
    ast.parse(src)
    print(json.dumps({"ok": True, "error": None}))
except SyntaxError as e:
    print(json.dumps({
        "ok": False,
        "error": {
            "line": e.lineno,
            "col": e.offset,
            "message": e.msg,
            "text": (e.text or "").rstrip(),
        },
    }))
"""


def check_syntax(source: str) -> dict:
    if not PYTHON_PROJECT.exists():
        return {
            "ok": False,
            "error": {
                "line": None,
                "col": None,
                "message": f"python-project not found at {PYTHON_PROJECT}",
                "text": "",
            },
        }
    try:
        proc = subprocess.run(
            ["uv", "run", "python", "-c", _SYNTAX_CHECK_SCRIPT],
            cwd=PYTHON_PROJECT,
            input=source,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return {
            "ok": False,
            "error": {
                "line": None,
                "col": None,
                "message": f"syntax check could not run: {e}",
                "text": "",
            },
        }
    if proc.returncode != 0 or not proc.stdout.strip():
        return {
            "ok": False,
            "error": {
                "line": None,
                "col": None,
                "message": (proc.stderr or proc.stdout or "unknown failure").strip()[:400],
                "text": "",
            },
        }
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "error": {
                "line": None,
                "col": None,
                "message": f"could not parse syntax-check output: {proc.stdout[:200]}",
                "text": "",
            },
        }


def run_pyright(source: str) -> dict:
    if not PYTHON_PROJECT.exists():
        return {
            "ok": False,
            "ran": False,
            "errors": [],
            "warnings": [],
            "raw_stderr": f"python-project not found at {PYTHON_PROJECT}",
            "exit_code": None,
        }

    # Write snippet to a temp file inside python-project so pyright picks up
    # the project config and venv. The directory name must not start with "."
    # — pyright's default include set skips hidden directories and would
    # silently analyze zero files.
    tmp_dir = PYTHON_PROJECT / "snippet_tmp"
    tmp_dir.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        dir=tmp_dir,
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(source)
        tmp_path = Path(f.name)

    try:
        proc = subprocess.run(
            ["uv", "run", "pyright", "--outputjson", str(tmp_path)],
            cwd=PYTHON_PROJECT,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        tmp_path.unlink(missing_ok=True)
        return {
            "ok": False,
            "ran": False,
            "errors": [],
            "warnings": [],
            "raw_stderr": "`uv` is not installed or not on PATH",
            "exit_code": None,
        }
    except subprocess.TimeoutExpired:
        tmp_path.unlink(missing_ok=True)
        return {
            "ok": False,
            "ran": False,
            "errors": [],
            "warnings": [],
            "raw_stderr": "pyright timed out after 60s",
            "exit_code": None,
        }
    finally:
        tmp_path.unlink(missing_ok=True)

    # Pyright exit codes:
    #   0 = no errors
    #   1 = errors reported (this is the common case we want to parse)
    #   >1 = pyright itself failed
    try:
        payload = json.loads(proc.stdout) if proc.stdout else {}
    except json.JSONDecodeError:
        return {
            "ok": False,
            "ran": False,
            "errors": [],
            "warnings": [],
            "raw_stderr": (proc.stderr or proc.stdout or "")[:4000],
            "exit_code": proc.returncode,
        }

    diagnostics = payload.get("generalDiagnostics", [])
    errors: list[dict] = []
    warnings: list[dict] = []
    for d in diagnostics:
        rng = d.get("range", {}).get("start", {})
        entry = {
            "line": (rng.get("line", 0) or 0) + 1,  # pyright is 0-indexed
            "col": (rng.get("character", 0) or 0) + 1,
            "severity": d.get("severity", "error"),
            "message": d.get("message", ""),
            "rule": d.get("rule"),
        }
        if entry["severity"] == "error":
            errors.append(entry)
        else:
            warnings.append(entry)

    return {
        "ok": len(errors) == 0,
        "ran": True,
        "errors": errors,
        "warnings": warnings,
        "raw_stderr": proc.stderr if proc.returncode > 1 else None,
        "exit_code": proc.returncode,
    }


def verify(source: str) -> dict:
    syntax = check_syntax(source)
    if not syntax["ok"]:
        # Don't bother running pyright on unparseable source — its error
        # message for syntax errors is less clear than Python's own.
        return {
            "syntax": syntax,
            "pyright": {
                "ok": False,
                "ran": False,
                "errors": [],
                "warnings": [],
                "raw_stderr": "skipped due to syntax error",
                "exit_code": None,
            },
        }
    return {"syntax": syntax, "pyright": run_pyright(source)}


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

    if not result["pyright"]["ran"] and not result["syntax"]["ok"]:
        return 0  # syntax error is a valid finding, not a tool failure
    if not result["pyright"]["ran"] and result["pyright"]["raw_stderr"] and "skipped" not in (result["pyright"]["raw_stderr"] or ""):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
