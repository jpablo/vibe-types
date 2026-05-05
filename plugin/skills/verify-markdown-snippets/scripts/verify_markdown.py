#!/usr/bin/env python3
"""Orchestrator: extract snippets from a markdown file, verify each one, write reports.

Usage:
    verify_markdown.py <markdown-path> [--out <report-dir>]

Produces, in the language project directory (or in --out if given):
    <stem>.report.md             — human-readable
    <stem>.report.json           — machine-readable
    <stem>.snippet-NN.<ext>      — one file per fenced block, for manual review

Default output directory is `<repo-root>/projects/python-project/reports/<timestamp>/`
(only Python is supported today; see LANG_PROJECT_DIRS to add more). Pass
`--out <dir>` to write directly into a fixed directory instead.

Exit codes:
    0 — all checked snippets clean
    1 — at least one snippet has errors
    2 — skill itself failed to run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from extract_snippets import extract  # noqa: E402
from match_expected_errors import match_expected_errors  # noqa: E402
from verify_python import verify as verify_python_snippet  # noqa: E402

SUPPORTED_LANGUAGES = {"python", "py"}

LANG_PROJECT_DIRS = {
    "python": "projects/python-project",
}


def find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / ".git").exists():
            return p
    raise RuntimeError(f"could not find repo root (no .git) above {start}")


def snippet_extension(lang: str | None) -> str:
    if lang in SUPPORTED_LANGUAGES:
        return "py"
    if lang is None:
        return "txt"
    return lang if lang.isalnum() else "txt"


def write_snippet_files(stem: str, results: list[dict], out_dir: Path) -> None:
    """Write each snippet to its own file in out_dir; record relative path on each result."""
    width = max(2, len(str(len(results))))
    for r in results:
        ext = snippet_extension(r["language"])
        filename = f"{stem}.snippet-{r['index']:0{width}d}.{ext}"
        path = out_dir / filename
        path.write_text(r["source"], encoding="utf-8")
        r["snippet_file"] = filename


def classify(snippet: dict) -> str:
    lang = snippet["language"]
    if lang is None:
        return "unlabeled"
    if lang in SUPPORTED_LANGUAGES:
        return "python"
    return "other"


def verify_all(snippets: list[dict]) -> list[dict]:
    results: list[dict] = []
    for snip in snippets:
        kind = classify(snip)
        expect_error = snip.get("expect_error", False)
        expected_errors = snip.get("expected_errors", [])
        entry: dict = {
            "index": snip["index"],
            "line": snip["line"],
            "language": snip["language"],
            "source": snip["source"],
            "expect_error": expect_error,
            "expected_errors": expected_errors,
        }
        if kind == "python":
            res = verify_python_snippet(snip["source"])
            entry["syntax"] = res["syntax"]
            entry["pyright"] = res["pyright"]
            has_errors = not res["syntax"]["ok"] or not res["pyright"]["ok"]
            if not res["pyright"]["ran"] and res["syntax"]["ok"]:
                entry["status"] = "tool_error"
            elif expect_error and has_errors:
                entry["status"] = "expected_fail"
            elif expect_error and not has_errors:
                entry["status"] = "missing_expected_error"
            elif has_errors:
                entry["status"] = "fail"
            else:
                entry["status"] = "ok"
        elif kind == "unlabeled":
            entry["status"] = "skipped_no_lang"
            entry["syntax"] = None
            entry["pyright"] = None
        else:
            entry["status"] = "skipped_unsupported_lang"
            entry["syntax"] = None
            entry["pyright"] = None
        results.append(entry)
    return results


def build_summary(results: list[dict]) -> dict:
    counts = {
        "total": len(results),
        "python": 0,
        "other": 0,
        "unlabeled": 0,
        "ok": 0,
        "fail": 0,
        "expected_fail": 0,
        "missing_expected_error": 0,
        "skipped": 0,
        "tool_error": 0,
    }
    for r in results:
        status = r["status"]
        if r["language"] in SUPPORTED_LANGUAGES:
            counts["python"] += 1
        elif r["language"] is None:
            counts["unlabeled"] += 1
        else:
            counts["other"] += 1
        if status == "ok":
            counts["ok"] += 1
        elif status == "fail":
            counts["fail"] += 1
        elif status == "expected_fail":
            counts["expected_fail"] += 1
        elif status == "missing_expected_error":
            counts["missing_expected_error"] += 1
        elif status == "tool_error":
            counts["tool_error"] += 1
        else:
            counts["skipped"] += 1
    return counts


def _render_actual_errors(lines: list[str], r: dict) -> None:
    """Append actual syntax/pyright error details to the report lines."""
    if r.get("syntax") and not r["syntax"]["ok"]:
        err = r["syntax"]["error"]
        lines.append(f"**Syntax error** at line {err['line']}, col {err['col']}: {err['message']}")
        if err.get("text"):
            lines.append("")
            lines.append(f"    {err['text']}")
    else:
        lines.append("**Syntax:** ok")
    if r.get("pyright") and r["pyright"].get("errors"):
        lines.append(f"**Pyright:** {len(r['pyright']['errors'])} error(s)")
        lines.append("")
        for e in r["pyright"]["errors"]:
            rule = f" [{e['rule']}]" if e.get("rule") else ""
            lines.append(f"- line {e['line']}, col {e['col']}: {e['message']}{rule}")
    if r.get("pyright") and r["pyright"].get("warnings"):
        lines.append("")
        lines.append(f"**Pyright warnings:** {len(r['pyright']['warnings'])}")
        for w in r["pyright"]["warnings"]:
            rule = f" [{w['rule']}]" if w.get("rule") else ""
            lines.append(f"- line {w['line']}, col {w['col']}: {w['message']}{rule}")


def render_markdown_report(input_path: Path, results: list[dict], counts: dict) -> str:
    lines: list[str] = []
    lines.append(f"# Snippet verification report — {input_path.name}")
    lines.append("")
    lines.append(f"**File:** `{input_path}`")
    lines.append(
        f"**Checked:** {counts['total']} snippets "
        f"({counts['python']} python, {counts['other']} other, {counts['unlabeled']} unlabeled)"
    )
    if counts["fail"] == 0 and counts["tool_error"] == 0:
        parts = [f"{counts['ok']} clean"]
        if counts["expected_fail"]:
            parts.append(f"{counts['expected_fail']} expected-fail")
        if counts["missing_expected_error"]:
            parts.append(f"{counts['missing_expected_error']} missing-expected-error")
        parts.append(f"{counts['skipped']} skipped")
        lines.append(f"**Status:** OK ({', '.join(parts)})")
    else:
        parts = [f"{counts['ok']} clean"]
        if counts["expected_fail"]:
            parts.append(f"{counts['expected_fail']} expected-fail")
        if counts["missing_expected_error"]:
            parts.append(f"{counts['missing_expected_error']} missing-expected-error")
        parts.append(f"{counts['skipped']} skipped")
        parts.append(f"{counts['tool_error']} tool errors")
        lines.append(
            f"**Status:** {counts['fail']} failing ({', '.join(parts)})"
        )
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| # | Line | Lang | Status | Errors | |")
    lines.append("|---|------|------|--------|--------|---|")
    for r in results:
        err_count = len(r["pyright"]["errors"]) if r.get("pyright") and r["pyright"].get("ran") else (
            1 if r.get("syntax") and not r["syntax"]["ok"] else 0
        )
        lang = r["language"] or "—"
        # ✅ = outcome matches expectation, ❌ = unexpected outcome
        status = r["status"]
        if status in ("ok", "expected_fail", "expected_fail_matched",
                       "skipped_no_lang", "skipped_unsupported_lang"):
            check = "✅"
        elif status == "fail" or status == "missing_expected_error":
            check = "❌"
        elif status == "expected_fail_mismatched":
            check = "❌"
        elif status == "expected_fail_partial":
            check = "❌"
        else:  # tool_error, etc.
            check = "❌"
        lines.append(
            f"| {r['index']} | {r['line']} | {lang} | {r['status']} | {err_count} | {check} |"
        )
    lines.append("")

    for r in results:
        header = f"## Snippet {r['index']} — line {r['line']} — {r['language'] or 'no lang tag'} — {r['status']}"
        lines.append(header)
        lines.append("")
        if r["status"] == "ok":
            lines.append("(no errors)")
        elif r["status"] == "skipped_no_lang":
            lines.append(
                "This fence has no language tag and was skipped. "
                "If the contents are Python, add ` ```python ` on the opening fence."
            )
        elif r["status"] == "skipped_unsupported_lang":
            lines.append(
                f"No verifier is wired up for `{r['language']}` yet. "
                "Only Python is supported in this version."
            )
        elif r["status"] == "expected_fail":
            lines.append(
                "This snippet has inline `# error:` comments and actual errors from pyright. "
                "Likely an intentional demo."
            )
            lines.append("")
            lines.append("**Expected (from comments):**")
            lines.append("")
            for ee in r.get("expected_errors", []):
                lines.append(f"- line {ee['line']}: {ee['comment']}")
            lines.append("")
            _render_actual_errors(lines, r)
        elif r["status"] == "missing_expected_error":
            lines.append(
                "This snippet has `# error:` comments but pyright reports **no errors**. "
                "The comment may describe a mypy-only error, or the error may have been "
                "fixed without updating the comment."
            )
            lines.append("")
            lines.append("**Expected (from comments):**")
            lines.append("")
            for ee in r.get("expected_errors", []):
                lines.append(f"- line {ee['line']}: {ee['comment']}")
        elif r["status"] == "tool_error":
            lines.append("The verifier could not run on this snippet.")
            if r.get("pyright") and r["pyright"].get("raw_stderr"):
                lines.append("")
                lines.append("```")
                lines.append(r["pyright"]["raw_stderr"])
                lines.append("```")
        else:  # fail
            _render_actual_errors(lines, r)

        lines.append("")
        lines.append("### Source")
        lines.append("")
        if r.get("snippet_file"):
            lines.append(f"File: [`{r['snippet_file']}`]({r['snippet_file']})")
            lines.append("")
        lang = r["language"] or ""
        lines.append(f"```{lang}")
        lines.append(r["source"].rstrip("\n"))
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Markdown file to verify")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Directory to write reports to (default: <repo-root>/projects/python-project/reports/<timestamp>)",
    )
    parser.add_argument(
        "--match-errors",
        action="store_true",
        help="Use claude CLI to judge whether expected-error comments match actual pyright errors.",
    )
    args = parser.parse_args()

    if not args.path.exists():
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 2

    markdown = args.path.read_text(encoding="utf-8")
    snippets = extract(markdown)
    results = verify_all(snippets)
    counts = build_summary(results)

    if args.out:
        out_dir = args.out
    else:
        run_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        out_dir = find_repo_root(SCRIPT_DIR) / LANG_PROJECT_DIRS["python"] / "reports" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.path.stem
    md_path = out_dir / f"{stem}.report.md"
    json_path = out_dir / f"{stem}.report.json"

    write_snippet_files(stem, results, out_dir)
    md_path.write_text(render_markdown_report(args.path, results, counts), encoding="utf-8")
    json_payload = {
        "input_file": str(args.path),
        "counts": counts,
        "snippets": results,
    }

    if args.match_errors and counts.get("expected_fail", 0) > 0:
        print(f"Matching {counts['expected_fail']} expected_fail snippet(s) via claude CLI...")
        json_payload = match_expected_errors(json_payload)
        counts = json_payload["counts"]

    json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")

    print(f"markdown report: {md_path}")
    print(f"json report:     {json_path}")
    print(
        f"summary: {counts['ok']} ok, {counts['fail']} fail, "
        f"{counts['expected_fail']} expected-fail, "
        f"{counts['missing_expected_error']} missing-expected-error, "
        f"{counts['skipped']} skipped, {counts['tool_error']} tool errors"
    )

    if counts["tool_error"] > 0:
        return 2
    if counts["fail"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
