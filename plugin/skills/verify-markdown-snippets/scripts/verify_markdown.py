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
from verify_python import verify as verify_python_snippet  # noqa: E402
from verify_rust import verify as verify_rust_snippet  # noqa: E402

# match_expected_errors is imported lazily inside main() so the orchestrator
# can run without the optional claude-CLI bridge installed.

PYTHON_LANGS = {"python", "py"}
RUST_LANGS = {"rust", "rs"}
SUPPORTED_LANGUAGES = PYTHON_LANGS | RUST_LANGS

LANG_PROJECT_DIRS = {
    "python": "projects/python-project",
    "rust": "projects/rust-project",
}


def find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / ".git").exists():
            return p
    raise RuntimeError(f"could not find repo root (no .git) above {start}")


def snippet_extension(lang: str | None) -> str:
    if lang in PYTHON_LANGS:
        return "py"
    if lang in RUST_LANGS:
        return "rs"
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
    if lang in PYTHON_LANGS:
        return "python"
    if lang in RUST_LANGS:
        return "rust"
    return "other"


def _status_for(expect_error: bool, has_errors: bool, ran: bool, syntax_ok: bool) -> str:
    if not ran and syntax_ok:
        return "tool_error"
    if expect_error and has_errors:
        return "expected_fail"
    if expect_error and not has_errors:
        return "missing_expected_error"
    if has_errors:
        return "fail"
    return "ok"


def verify_all(snippets: list[dict]) -> list[dict]:
    results: list[dict] = []
    for snip in snippets:
        kind = classify(snip)
        expected_errors = snip.get("expected_errors", [])
        attributes = set(snip.get("attributes") or [])
        # A snippet is treated as an intentional fail demo (status lands in
        # the expected_fail family rather than plain `fail`) when any of:
        #   - rustdoc-style `compile_fail` fence attribute is present;
        #   - one or more `error:` / `error[E####]` comments appear inline.
        expect_error = (
            snip.get("expect_error", False)
            or "compile_fail" in attributes
            or bool(expected_errors)
        )
        entry: dict = {
            "index": snip["index"],
            "line": snip["line"],
            "language": snip["language"],
            "attributes": sorted(attributes),
            "source": snip["source"],
            "expect_error": expect_error,
            "expected_errors": expected_errors,
        }
        # Rustdoc-style `ignore` attribute: author has marked the snippet as
        # docs-only (e.g., requires external context, build script, or live
        # service). Skip without trying to compile.
        if "ignore" in attributes:
            entry["status"] = "skipped_ignore"
            entry["syntax"] = None
            entry["tool"] = None
            entry["tool_result"] = None
            results.append(entry)
            continue
        if kind == "python":
            res = verify_python_snippet(snip["source"])
            entry["tool"] = "pyright"
            entry["syntax"] = res["syntax"]
            entry["pyright"] = res["pyright"]
            entry["tool_result"] = res["pyright"]
            entry["status"] = _status_for(
                expect_error,
                has_errors=not res["syntax"]["ok"] or not res["pyright"]["ok"],
                ran=res["pyright"]["ran"],
                syntax_ok=res["syntax"]["ok"],
            )
        elif kind == "rust":
            res = verify_rust_snippet(snip["source"])
            entry["tool"] = "rustc"
            entry["syntax"] = res["syntax"]
            entry["rustc"] = res["rustc"]
            entry["tool_result"] = res["rustc"]
            entry["status"] = _status_for(
                expect_error,
                has_errors=not res["rustc"]["ok"],
                ran=res["rustc"]["ran"],
                syntax_ok=True,
            )
        elif kind == "unlabeled":
            entry["status"] = "skipped_no_lang"
            entry["syntax"] = None
            entry["tool"] = None
            entry["tool_result"] = None
        else:
            entry["status"] = "skipped_unsupported_lang"
            entry["syntax"] = None
            entry["tool"] = None
            entry["tool_result"] = None
        results.append(entry)
    return results


def build_summary(results: list[dict]) -> dict:
    counts = {
        "total": len(results),
        "python": 0,
        "rust": 0,
        "other": 0,
        "unlabeled": 0,
        "ok": 0,
        "fail": 0,
        "expected_fail": 0,
        "expected_fail_matched": 0,
        "expected_fail_mismatched": 0,
        "expected_fail_partial": 0,
        "missing_expected_error": 0,
        "skipped": 0,
        "tool_error": 0,
    }
    for r in results:
        status = r["status"]
        if r["language"] in PYTHON_LANGS:
            counts["python"] += 1
        elif r["language"] in RUST_LANGS:
            counts["rust"] += 1
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
        elif status == "expected_fail_matched":
            counts["expected_fail_matched"] += 1
        elif status == "expected_fail_mismatched":
            counts["expected_fail_mismatched"] += 1
        elif status == "expected_fail_partial":
            counts["expected_fail_partial"] += 1
        elif status == "missing_expected_error":
            counts["missing_expected_error"] += 1
        elif status == "tool_error":
            counts["tool_error"] += 1
        elif status in ("skipped_no_lang", "skipped_unsupported_lang", "skipped_ignore"):
            counts["skipped"] += 1
        else:
            counts["skipped"] += 1
    return counts


def _render_match_results(lines: list[str], r: dict) -> None:
    """Append the per-comment LLM judgement (from --match-errors) to the report."""
    em = r.get("error_matching") or {}
    if em.get("status") == "llm_error":
        lines.append("**Match results:** LLM call failed for this snippet.")
        lines.append("")
        return
    results = em.get("results") or []
    if not results:
        return
    lines.append("**Match results (LLM):**")
    lines.append("")
    expected = r.get("expected_errors", [])
    tool_result = r.get("tool_result") or {}
    actuals = tool_result.get("errors", [])
    for entry in results:
        idx = entry.get("expected_index")
        # `expected_index` is 1-based per the prompt contract. Guard against
        # missing/out-of-range values without crashing the whole render.
        comment = ""
        if isinstance(idx, int) and 1 <= idx <= len(expected):
            comment = expected[idx - 1].get("comment", "")
        matched = entry.get("matched")
        marker = "✅" if matched is True else "❌"
        actual_idx = entry.get("actual_index")
        actual_msg = ""
        if isinstance(actual_idx, int) and 1 <= actual_idx <= len(actuals):
            actual_msg = actuals[actual_idx - 1].get("message", "")
        reason = entry.get("reason", "")
        line = f"- {marker} `{comment}`"
        if actual_msg:
            line += f" ↔ `{actual_msg}`"
        if reason:
            line += f" — {reason}"
        lines.append(line)
    lines.append("")


def _render_actual_errors(lines: list[str], r: dict) -> None:
    """Append actual syntax/tool error details to the report lines."""
    if r.get("syntax") and not r["syntax"]["ok"]:
        err = r["syntax"]["error"]
        lines.append(f"**Syntax error** at line {err['line']}, col {err['col']}: {err['message']}")
        if err.get("text"):
            lines.append("")
            lines.append(f"    {err['text']}")
    else:
        lines.append("**Syntax:** ok")
    tool_name = (r.get("tool") or "tool").capitalize()
    tool_result = r.get("tool_result") or {}
    if tool_result.get("errors"):
        lines.append(f"**{tool_name}:** {len(tool_result['errors'])} error(s)")
        lines.append("")
        for e in tool_result["errors"]:
            rule = f" [{e['rule']}]" if e.get("rule") else ""
            lines.append(f"- line {e['line']}, col {e['col']}: {e['message']}{rule}")
    if tool_result.get("warnings"):
        lines.append("")
        lines.append(f"**{tool_name} warnings:** {len(tool_result['warnings'])}")
        for w in tool_result["warnings"]:
            rule = f" [{w['rule']}]" if w.get("rule") else ""
            lines.append(f"- line {w['line']}, col {w['col']}: {w['message']}{rule}")


def render_markdown_report(input_path: Path, results: list[dict], counts: dict) -> str:
    lines: list[str] = []
    lines.append(f"# Snippet verification report — {input_path.name}")
    lines.append("")
    lines.append(f"**File:** `{input_path}`")
    lines.append(
        f"**Checked:** {counts['total']} snippets "
        f"({counts['python']} python, {counts['rust']} rust, "
        f"{counts['other']} other, {counts['unlabeled']} unlabeled)"
    )
    def _expected_fail_parts() -> list[str]:
        out: list[str] = []
        if counts["expected_fail"]:
            out.append(f"{counts['expected_fail']} expected-fail")
        if counts["expected_fail_matched"]:
            out.append(f"{counts['expected_fail_matched']} matched")
        if counts["expected_fail_partial"]:
            out.append(f"{counts['expected_fail_partial']} partial")
        if counts["expected_fail_mismatched"]:
            out.append(f"{counts['expected_fail_mismatched']} mismatched")
        if counts["missing_expected_error"]:
            out.append(f"{counts['missing_expected_error']} missing-expected-error")
        return out

    unexpected = (
        counts["fail"]
        + counts["tool_error"]
        + counts["expected_fail_mismatched"]
        + counts["expected_fail_partial"]
    )
    if unexpected == 0:
        parts = [f"{counts['ok']} clean", *_expected_fail_parts(),
                 f"{counts['skipped']} skipped"]
        lines.append(f"**Status:** OK ({', '.join(parts)})")
    else:
        parts = [f"{counts['ok']} clean", *_expected_fail_parts(),
                 f"{counts['skipped']} skipped",
                 f"{counts['tool_error']} tool errors"]
        lines.append(
            f"**Status:** {unexpected} failing ({', '.join(parts)})"
        )
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| # | Line | Lang | Status | Errors | |")
    lines.append("|---|------|------|--------|--------|---|")
    for r in results:
        tool_result = r.get("tool_result") or {}
        err_count = len(tool_result.get("errors", [])) if tool_result.get("ran") else (
            1 if r.get("syntax") and not r["syntax"]["ok"] else 0
        )
        lang = r["language"] or "—"
        # ✅ = outcome matches expectation, ❌ = unexpected outcome
        status = r["status"]
        if status in ("ok", "expected_fail", "expected_fail_matched",
                       "skipped_no_lang", "skipped_unsupported_lang",
                       "skipped_ignore"):
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
                "If the contents are Python or Rust, add a language tag on the opening fence."
            )
        elif r["status"] == "skipped_unsupported_lang":
            lines.append(
                f"No verifier is wired up for `{r['language']}` yet. "
                f"Supported languages: {', '.join(sorted(SUPPORTED_LANGUAGES))}."
            )
        elif r["status"] == "skipped_ignore":
            lines.append(
                "This snippet is marked `ignore` (e.g. ` ```rust,ignore `). "
                "Verification was skipped at the author's request — typically "
                "because the snippet illustrates a multi-file or external-service "
                "construct that can't be compiled standalone."
            )
        elif r["status"] in (
            "expected_fail",
            "expected_fail_matched",
            "expected_fail_mismatched",
            "expected_fail_partial",
        ):
            tool_name = r.get("tool") or "the verifier"
            blurb = {
                "expected_fail": (
                    f"This snippet has inline `error:` comments and actual errors "
                    f"from {tool_name}. Likely an intentional demo."
                ),
                "expected_fail_matched": (
                    f"All expected-error comments matched actual {tool_name} "
                    "diagnostics (per the LLM judge)."
                ),
                "expected_fail_mismatched": (
                    f"None of the expected-error comments match any actual "
                    f"{tool_name} diagnostic. The comments may be stale, or describe "
                    "a different tool's output."
                ),
                "expected_fail_partial": (
                    f"Some expected-error comments matched actual {tool_name} "
                    "diagnostics, others did not. See per-comment results below."
                ),
            }[r["status"]]
            lines.append(blurb)
            lines.append("")
            lines.append("**Expected (from comments):**")
            lines.append("")
            for ee in r.get("expected_errors", []):
                lines.append(f"- line {ee['line']}: {ee['comment']}")
            lines.append("")
            _render_actual_errors(lines, r)
            lines.append("")
            _render_match_results(lines, r)
        elif r["status"] == "missing_expected_error":
            tool_name = r.get("tool") or "the verifier"
            lines.append(
                f"This snippet has `error:` comments but {tool_name} reports **no errors**. "
                "The comment may describe a different tool's diagnostic, or the error may "
                "have been fixed without updating the comment."
            )
            lines.append("")
            lines.append("**Expected (from comments):**")
            lines.append("")
            for ee in r.get("expected_errors", []):
                lines.append(f"- line {ee['line']}: {ee['comment']}")
        elif r["status"] == "tool_error":
            lines.append("The verifier could not run on this snippet.")
            tool_result = r.get("tool_result") or {}
            if tool_result.get("raw_stderr"):
                lines.append("")
                lines.append("```")
                lines.append(tool_result["raw_stderr"])
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
        help="Directory to write reports to (default: <repo-root>/projects/<lang>-project/reports/<timestamp>)",
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

    # Run the optional LLM matching step BEFORE rendering, so the markdown
    # report reflects the refined `expected_fail_matched|mismatched|partial`
    # statuses. `match_expected_errors` mutates `results` in place (the same
    # list lives inside `payload["snippets"]`) and updates `payload["counts"]`,
    # but we rebuild `counts` from scratch afterwards to keep one source of
    # truth.
    if args.match_errors:
        pre_counts = build_summary(results)
        if pre_counts.get("expected_fail", 0) > 0:
            try:
                from match_expected_errors import match_expected_errors  # noqa: PLC0415
            except ImportError:
                print(
                    "error: --match-errors requires match_expected_errors.py "
                    "(not installed in this skill).",
                    file=sys.stderr,
                )
                return 2
            print(
                f"Matching {pre_counts['expected_fail']} expected_fail snippet(s) "
                "via claude CLI..."
            )
            payload = {
                "input_file": str(args.path),
                "counts": pre_counts,
                "snippets": results,
            }
            payload = match_expected_errors(payload)
            results = payload["snippets"]

    counts = build_summary(results)

    if args.out:
        out_dir = args.out
    else:
        run_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        # Pick the project dir whose language dominates this file; default to
        # python-project for backward compatibility on docs with no code.
        if counts.get("rust", 0) > counts.get("python", 0):
            lang_dir = LANG_PROJECT_DIRS["rust"]
        else:
            lang_dir = LANG_PROJECT_DIRS["python"]
        out_dir = find_repo_root(SCRIPT_DIR) / lang_dir / "reports" / run_id
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
    json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")

    print(f"markdown report: {md_path}")
    print(f"json report:     {json_path}")
    summary_parts = [
        f"{counts['ok']} ok",
        f"{counts['fail']} fail",
        f"{counts['expected_fail']} expected-fail",
    ]
    if args.match_errors:
        summary_parts.extend([
            f"{counts['expected_fail_matched']} matched",
            f"{counts['expected_fail_partial']} partial",
            f"{counts['expected_fail_mismatched']} mismatched",
        ])
    summary_parts.extend([
        f"{counts['missing_expected_error']} missing-expected-error",
        f"{counts['skipped']} skipped",
        f"{counts['tool_error']} tool errors",
    ])
    print("summary: " + ", ".join(summary_parts))

    if counts["tool_error"] > 0:
        return 2
    # `expected_fail_mismatched` and `expected_fail_partial` are unexpected
    # outcomes from the author's perspective (the comments lied about what
    # the tool would say) — exit non-zero so CI catches them.
    if (counts["fail"] > 0
            or counts["expected_fail_mismatched"] > 0
            or counts["expected_fail_partial"] > 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
