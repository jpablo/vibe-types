#!/usr/bin/env python3
"""Match expected-error comments against actual pyright errors using an LLM.

Reads a JSON report produced by verify_markdown.py, finds all entries with
status "expected_fail", and calls `claude -p` to judge whether each expected
error comment has a semantically matching actual error from pyright.

Updates each expected_fail entry's status to one of:
  - expected_fail_matched  — all expected comments match actual errors
  - expected_fail_mismatched — no expected comments match any actual error
  - expected_fail_partial — some match, some don't

Usage:
    match_expected_errors.py <report.json> [--out <updated-report.json>]

If --out is omitted, the input file is updated in-place.

Exit codes:
    0 — matching completed
    1 — claude CLI not available or matching failed
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


# Best-effort mapping from the orchestrator's `tool` value to a human-readable
# language name for the LLM prompt. Falls back to "code" / "the type checker"
# for unknown tools so the prompt stays sensible if a new verifier is added.
_TOOL_LANG = {
    "pyright": "Python",
    "rustc": "Rust",
    "scalac": "Scala",
}


def _build_prompt(snippet: dict) -> str:
    expected = snippet["expected_errors"]
    tool = snippet.get("tool") or "the type checker"
    language = _TOOL_LANG.get(tool, "code")
    actual_errors: list[str] = []
    if snippet.get("syntax") and not snippet["syntax"]["ok"]:
        err = snippet["syntax"]["error"]
        actual_errors.append(
            f"line {err.get('line', '?')}: [syntax] {err.get('message', 'unknown')}"
        )
    # `tool_result` is the orchestrator's tool-agnostic alias for whichever
    # verifier ran (pyright | rustc | …); using it keeps this script working
    # for any language the orchestrator dispatches to.
    tool_result = snippet.get("tool_result") or {}
    for e in tool_result.get("errors", []):
        actual_errors.append(f"line {e['line']}: {e['message']}")

    expected_lines = "\n".join(
        f"  {i+1}. line {e['line']}: \"{e['comment']}\""
        for i, e in enumerate(expected)
    )
    actual_lines = "\n".join(
        f"  {i+1}. {e}" for i, e in enumerate(actual_errors)
    )

    return f"""You are comparing expected-error comments from a {language} code snippet against actual errors reported by {tool}.

Expected errors (from inline # error: comments):
{expected_lines}

Actual errors (from {tool}):
{actual_lines}

For each expected error, determine if there is an actual error that is semantically equivalent — they don't need to match word-for-word, but they should describe the same type error or issue. Consider that:
- "expected X, got Y" and "cannot be assigned to parameter of type X" describe the same mismatch
- "TypeError: Can't instantiate" and "Cannot instantiate abstract class" are equivalent
- An actual error on a nearby line (within 2 lines) of the expected line may still match

Respond with ONLY a JSON object, no markdown formatting:
{{"results": [{{"expected_index": 1, "matched": true, "actual_index": 1, "reason": "brief explanation"}}, ...]}}

Include one entry per expected error. Set actual_index to null if no match found."""


def _call_claude(prompt: str) -> dict | None:
    try:
        proc = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        print("error: 'claude' CLI not found on PATH", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print("error: claude CLI timed out after 60s", file=sys.stderr)
        return None

    if proc.returncode != 0:
        print(f"error: claude CLI exited with code {proc.returncode}", file=sys.stderr)
        if proc.stderr:
            print(proc.stderr[:500], file=sys.stderr)
        return None

    # The --output-format json wraps the response in a JSON envelope with a "result" field
    try:
        envelope = json.loads(proc.stdout)
        text = envelope.get("result", proc.stdout)
    except json.JSONDecodeError:
        text = proc.stdout

    # Extract JSON from the response (may be wrapped in markdown code fences)
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove opening and closing fences
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"error: could not parse LLM response as JSON: {text[:200]}", file=sys.stderr)
        return None


def match_expected_errors(report: dict) -> dict:
    """Process a report, matching expected errors for expected_fail snippets."""
    for snippet in report.get("snippets", []):
        if snippet.get("status") != "expected_fail":
            continue

        prompt = _build_prompt(snippet)
        result = _call_claude(prompt)

        if result is None:
            snippet["error_matching"] = {"status": "llm_error", "results": []}
            continue

        results = result.get("results", [])
        snippet["error_matching"] = {"status": "completed", "results": results}

        matched_count = sum(1 for r in results if r.get("matched"))
        total = len(snippet["expected_errors"])

        if matched_count == total:
            snippet["status"] = "expected_fail_matched"
        elif matched_count == 0:
            snippet["status"] = "expected_fail_mismatched"
        else:
            snippet["status"] = "expected_fail_partial"

    # Update counts
    counts = report.get("counts", {})
    ef = counts.get("expected_fail", 0)
    matched = sum(1 for s in report["snippets"] if s["status"] == "expected_fail_matched")
    mismatched = sum(1 for s in report["snippets"] if s["status"] == "expected_fail_mismatched")
    partial = sum(1 for s in report["snippets"] if s["status"] == "expected_fail_partial")
    remaining = sum(1 for s in report["snippets"] if s["status"] == "expected_fail")
    counts["expected_fail"] = remaining
    counts["expected_fail_matched"] = matched
    counts["expected_fail_mismatched"] = mismatched
    counts["expected_fail_partial"] = partial

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="JSON report from verify_markdown.py")
    parser.add_argument(
        "--out", type=Path, default=None,
        help="Output path for updated report (default: overwrite input)",
    )
    args = parser.parse_args()

    if not args.report.exists():
        print(f"error: file not found: {args.report}", file=sys.stderr)
        return 1

    report = json.loads(args.report.read_text(encoding="utf-8"))

    ef_count = sum(1 for s in report.get("snippets", []) if s.get("status") == "expected_fail")
    if ef_count == 0:
        print("No expected_fail snippets to match.")
        return 0

    print(f"Matching {ef_count} expected_fail snippet(s) via claude CLI...")
    report = match_expected_errors(report)

    out_path = args.out or args.report
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Updated report written to: {out_path}")

    matched = sum(1 for s in report["snippets"] if s["status"] == "expected_fail_matched")
    mismatched = sum(1 for s in report["snippets"] if s["status"] == "expected_fail_mismatched")
    partial = sum(1 for s in report["snippets"] if s["status"] == "expected_fail_partial")
    print(f"Results: {matched} matched, {mismatched} mismatched, {partial} partial")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
