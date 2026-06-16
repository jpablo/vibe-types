#!/usr/bin/env python3
"""Verify a single Scala snippet with `scala-cli compile`.

Reads snippet source from --source-file, or stdin if --source-file is '-'.
Writes the snippet into `projects/scala-project/snippet_tmp/` and compiles it
with scala-cli, pinned to the Scala version and library dependencies declared
in `projects/scala-project/build.sbt` (parsed here, so build.sbt stays the
single source of truth).

Why scala-cli and not sbt: sbt pays 10-20s of full build-tool startup per
invocation and recompiles the whole project, which is prohibitive when a
catalog file has ten snippets. scala-cli compiles a single isolated file —
while still using the exact compiler version and dependency set of the
reference sbt project. (We run it with --server=false; see the comment at the
call site.)

Snippets are compiled as regular `.scala` compilation units (top-level defs,
enums, givens are fine). REPL-style snippets with bare top-level *statements*
(`a == b  // error: ...` demos) initially fail with "Illegal start of toplevel
definition" (E103); when that happens the snippet is retried wrapped in an
`@main def` stub — Scala allows local classes, givens, and imports inside a
method body — and diagnostic positions are mapped back to the original source.

Emits a JSON object on stdout:

    {
        "syntax": {"ok": bool, "error": null},     # always ok — scalac handles syntax
        "scalac": {
            "ok": bool,
            "ran": bool,
            "errors":   [{"line": int, "col": int, "severity": str, "message": str, "rule": str | null}],
            "warnings": [ ... ],
            "raw_stderr": str | null,
            "exit_code": int | null,
            "wrapped":   bool                       # true if the snippet was wrapped in an @main stub
        }
    }

Exit codes:
    0 — verification ran cleanly (snippet may still have errors, see JSON)
    2 — scala-cli is not available; verification could not run
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
SCALA_PROJECT = REPO_ROOT / "projects" / "scala-project"
BUILD_SBT = SCALA_PROJECT / "build.sbt"

# Flags the snippets are compiled with. Deliberately a *relaxed subset* of the
# reference build's scalacOptions (see build.sbt): documentation snippets
# legitimately contain unused names and may show either syntax, so -Werror,
# -Wunused:all and -new-syntax are omitted. -Wvalue-discard etc. still run but
# only produce warnings here (no -Werror), which the report lists without
# failing the snippet.
SNIPPET_SCALAC_OPTIONS = [
    "-deprecation",
    "-feature",
    "-unchecked",
    "-Wvalue-discard",
    "-Wnonunit-statement",
    # Catalog entries demonstrate experimental features (capture checking,
    # safer exceptions, erased definitions). On a stable Scala release those
    # imports are rejected unless the compiler runs in experimental mode.
    "-experimental",
    # Keep diagnostics machine-parseable.
    "-color:never",
]

_SCALA_VERSION = re.compile(r'val\s+scala3Version\s*=\s*"([^"]+)"|scalaVersion\s*:=\s*"([^"]+)"')
# Matches `"org" %% "name" % "version"` (optionally followed by `% Test` etc.).
_DEPENDENCY = re.compile(r'"([\w.\-]+)"\s*%%\s*"([\w.\-]+)"\s*%\s*"([\w.\-+]+)"')

# Scala 3 diagnostic header, e.g.:
#   -- [E007] Type Mismatch Error: /path/_snippet_ab.scala:3:15 ------------
#   -- Error: /path/_snippet_ab.scala:5:0 ----------------------------------
_DIAG_HEADER = re.compile(
    r"^--\s*(?:\[(?P<code>\w+)\]\s*)?(?P<kind>[^:]*?)\s*(?P<sev>Error|Warning):\s*"
    r"(?P<path>.+?):(?P<line>\d+):(?P<col>\d+)"
)
# Detail lines inside a diagnostic block: `  |             Required: Int`
_DIAG_DETAIL = re.compile(r"^\s*\|(?P<text>.*)$")
_CARETS_ONLY = re.compile(r"^\^+$")


def parse_build_sbt() -> dict:
    """Extract the Scala version and dependency coordinates from build.sbt."""
    text = BUILD_SBT.read_text(encoding="utf-8")
    version = None
    m = _SCALA_VERSION.search(text)
    if m:
        version = m.group(1) or m.group(2)
    deps = [f"{org}::{name}:{ver}" for org, name, ver in _DEPENDENCY.findall(text)]
    return {"scala_version": version, "dependencies": deps}


def parse_diagnostics(output: str, target_filename: str) -> tuple[list[dict], list[dict]]:
    """Parse Scala 3 console diagnostics, keeping only those from our snippet file."""
    errors: list[dict] = []
    warnings: list[dict] = []
    current: dict | None = None
    details: list[str] = []

    def flush() -> None:
        nonlocal current, details
        if current is None:
            return
        message = current.pop("_kind", "")
        body = " ".join(d for d in details if d)
        if body:
            message = f"{message}: {body}" if message else body
        current["message"] = message or "(no message)"
        (errors if current["severity"] == "error" else warnings).append(current)
        current, details = None, []

    for raw_line in output.splitlines():
        m = _DIAG_HEADER.match(raw_line)
        if m:
            flush()
            if not m.group("path").endswith(target_filename):
                continue  # diagnostic from another file (stale workspace entry)
            current = {
                "line": int(m.group("line")),
                "col": int(m.group("col")),
                "severity": m.group("sev").lower(),
                "rule": m.group("code"),
                "_kind": m.group("kind").strip(),
            }
            continue
        if current is None:
            continue
        d = _DIAG_DETAIL.match(raw_line)
        if d:
            text = d.group("text").strip()
            if (
                text
                and not _CARETS_ONLY.match(text)
                and "longer explanation available" not in text
            ):
                details.append(text)
        elif raw_line.strip() and not raw_line.lstrip()[0].isdigit():
            # Neither a `|` detail line nor a numbered source-echo line:
            # the diagnostic block has ended.
            flush()
    flush()
    return errors, warnings


# Scala 3's parser error for a bare statement at the top level of a .scala
# file. Seeing it triggers the wrap-and-retry path below.
_TOPLEVEL_STATEMENT_RULE = "E103"


def _wrap(source: str) -> str:
    """Wrap a REPL-style snippet in an @main stub.

    Adds exactly one line above the snippet and two columns of indentation,
    so diagnostics map back as line - 1 / col - 2. Local classes, enums,
    givens, and imports are all legal inside a method body, so definition
    snippets survive the wrap too.
    """
    indented = "\n".join(
        f"  {line}" if line.strip() else line for line in source.splitlines()
    )
    return f"@main def _snippetMain(): Unit =\n{indented}\n"


def run_scala_cli(source: str) -> dict:
    result = _compile_once(source, wrapped=False)
    if result["ran"] and any(
        e.get("rule") == _TOPLEVEL_STATEMENT_RULE for e in result["errors"]
    ):
        retry = _compile_once(_wrap(source), wrapped=True)
        # Keep the wrapped result only if wrapping actually fixed the
        # top-level-statement parse (otherwise the original errors are the
        # honest report).
        if retry["ran"] and not any(
            e.get("rule") == _TOPLEVEL_STATEMENT_RULE for e in retry["errors"]
        ):
            return retry
    return result


def _compile_once(source: str, *, wrapped: bool) -> dict:
    if not SCALA_PROJECT.exists() or not BUILD_SBT.exists():
        return {
            "ok": False, "ran": False, "errors": [], "warnings": [],
            "raw_stderr": f"scala-project not found at {SCALA_PROJECT}",
            "exit_code": None, "wrapped": wrapped,
        }

    config = parse_build_sbt()
    if not config["scala_version"]:
        return {
            "ok": False, "ran": False, "errors": [], "warnings": [],
            "raw_stderr": f"could not parse scalaVersion from {BUILD_SBT}",
            "exit_code": None, "wrapped": wrapped,
        }

    tmp_dir = SCALA_PROJECT / "snippet_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    target_name = f"_snippet_{uuid.uuid4().hex[:12]}.scala"
    target_path = tmp_dir / target_name
    target_path.write_text(source, encoding="utf-8")

    cmd = [
        "scala-cli", "compile",
        # Bypass the Bloop compile server: Bloop shipped with scala-cli (as of
        # 1.8.x) fails to resolve the multi-jar compiler bridge of Scala 3.8+
        # ("Expected single file for component ...scala3-sbt-bridge...").
        # Plain in-process scalac is slower per snippet but always correct.
        "--server=false",
        "--scala", config["scala_version"],
    ]
    for dep in config["dependencies"]:
        cmd += ["--dep", dep]
    for opt in SNIPPET_SCALAC_OPTIONS:
        cmd += ["-O", opt]
    cmd.append(str(target_path))

    try:
        proc = subprocess.run(
            cmd,
            cwd=SCALA_PROJECT,
            capture_output=True,
            text=True,
            # Generous: the first run may download the Scala 3 compiler and
            # all dependencies.
            timeout=600,
        )
    except FileNotFoundError:
        target_path.unlink(missing_ok=True)
        return {
            "ok": False, "ran": False, "errors": [], "warnings": [],
            "raw_stderr": "`scala-cli` is not installed or not on PATH",
            "exit_code": None, "wrapped": wrapped,
        }
    except subprocess.TimeoutExpired:
        target_path.unlink(missing_ok=True)
        return {
            "ok": False, "ran": False, "errors": [], "warnings": [],
            "raw_stderr": "scala-cli compile timed out after 600s",
            "exit_code": None, "wrapped": wrapped,
        }
    finally:
        target_path.unlink(missing_ok=True)

    # scala-cli writes compiler diagnostics to stderr; parse both streams to
    # be safe across versions.
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    errors, warnings = parse_diagnostics(combined, target_name)

    if wrapped:
        # Map positions in the wrapped file back to the original snippet:
        # _wrap() adds one header line and two columns of indentation.
        for diag in (*errors, *warnings):
            diag["line"] = max(diag["line"] - 1, 0)
            diag["col"] = max(diag["col"] - 2, 0)

    raw_stderr = None
    if proc.returncode != 0 and not errors:
        # scala-cli itself failed (bad dep coordinates, download failure, …)
        raw_stderr = (proc.stderr or "")[:4000]

    return {
        # Clean only when the compiler exited 0 with no errors from our file.
        # (rc != 0 with zero parsed errors means scala-cli itself failed —
        # raw_stderr carries the explanation in that case.)
        "ok": proc.returncode == 0 and not errors,
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
        "scalac": run_scala_cli(source),
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

    if not result["scalac"]["ran"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
