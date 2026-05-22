#!/usr/bin/env python3
"""Extract fenced code blocks from a markdown file.

Emits a JSON list on stdout where each entry is:
    {"index": int, "line": int, "language": str | None, "source": str,
     "expect_error": bool,
     "expected_errors": [{"line": int, "comment": str}, ...]}

- `index` is 1-based over all fences in the file.
- `line` is the 1-based line number of the opening fence in the source file.
- `language` is the info string's first word, lowercased, or None if absent.
- `source` is the snippet content without the fences.
- `expect_error` is True if the snippet contains a `# expect-error` keyword,
  signaling that the snippet is intentionally broken. NOTE: the orchestrator
  (verify_markdown.py) treats a snippet as expect-error if *any* of these
  signals is present:
    1. `expect_error` is True here (i.e., the keyword appears in the body), OR
    2. the snippet has one or more `# error:` description comments
       (`expected_errors` is non-empty), OR
    3. the fence carries a rustdoc-style `compile_fail` attribute.
  The keyword exists for snippets that are intentionally broken but where
  per-line `# error:` annotations would be noisy or impossible (e.g.,
  module-level failures).
- `expected_errors` lists inline `# error:` comments describing the expected
  errors (descriptions only — classification is driven by `expect_error`).

Handles both ``` and ~~~ fences, variable fence lengths (>= 3), and indented
fences per CommonMark. This is intentionally a small, boring state machine —
we want the extractor to be trivially correct, not clever.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# CommonMark fence rules we care about:
# - opening fence: >= 3 backticks or >= 3 tildes, optionally indented up to 3 spaces
# - info string follows the fence on the same line
# - closing fence: same char, same or greater length, no info string
FENCE_OPEN = re.compile(r"^(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})(?P<info>.*)$")

# The keyword that marks a snippet as intentionally broken.
# Can appear on its own line or inline: `# expect-error` or `code  # expect-error`
EXPECT_ERROR_KEYWORD = re.compile(r"#\s*expect-error\b", re.IGNORECASE)

# Matches inline error-indicator comments. Captures an error description
# composed of an optional rustc error code (E####) and an optional message.
# Covers patterns seen in the corpus across Python, Rust, and TS snippets:
#   code  # error: description
#   code  # type error: description
#   code  # TypeError: description
#   code  // error: description
#   code  // ERROR: description
#   code  // error[E0515]
#   code  // error[E0515]: description
EXPECTED_ERROR = re.compile(
    r"""(?:\#|//)
        \s*
        (?:type\s+)?
        (?:error|TypeError)
        (?:\[(?P<code>[A-Za-z]\d+)\])?         # optional [E0515]
        (?:\s*:\s*(?P<msg>.+))?                # optional : description
        \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _has_expect_error(body_lines: list[str]) -> bool:
    """Check if any line contains the `# expect-error` keyword."""
    return any(EXPECT_ERROR_KEYWORD.search(line) for line in body_lines)


def _extract_expected_errors(body_lines: list[str]) -> list[dict]:
    """Scan snippet body for inline comments describing expected errors."""
    errors: list[dict] = []
    for i, line in enumerate(body_lines):
        stripped = line.lstrip()
        m = EXPECTED_ERROR.search(stripped)
        if not m:
            continue
        # When the line starts with `//`, decide between two patterns:
        #   header comment:   `// error[E0382]: …`        (accept — describes
        #                                                  errors from the
        #                                                  following lines)
        #   commented-out:    `// foo();  // error[E0382]: …`  (skip — the
        #                                                  offending code is
        #                                                  itself a comment,
        #                                                  rustc never sees it)
        # Distinguish by looking at what sits between the leading `//` and
        # the matched error marker: only whitespace → header, anything else
        # → commented-out.
        if stripped.startswith("//"):
            prefix = stripped[2:m.start()]
            if prefix.strip() != "":
                continue
        code = m.group("code")
        msg = (m.group("msg") or "").strip()
        # Require either a rustc code or a description — bare "// error" with
        # nothing else is too ambiguous to act on.
        if not code and not msg:
            continue
        if code and msg:
            comment = f"[{code.upper()}] {msg}"
        elif code:
            comment = f"[{code.upper()}]"
        else:
            comment = msg
        errors.append({"line": i + 1, "comment": comment})
    return errors


def extract(markdown: str) -> list[dict]:
    lines = markdown.splitlines()
    snippets: list[dict] = []
    i = 0
    index = 0
    n = len(lines)
    while i < n:
        m = FENCE_OPEN.match(lines[i])
        if not m:
            i += 1
            continue
        fence = m.group("fence")
        fence_char = fence[0]
        fence_len = len(fence)
        indent = len(m.group("indent"))
        info = m.group("info").strip()
        # Info string supports rustdoc-style attributes separated by commas or
        # whitespace, e.g. ```rust,ignore  or  ```rust ignore. The first token
        # is the language; remaining tokens are attributes.
        info_tokens = [t for t in re.split(r"[,\s]+", info) if t]
        language = info_tokens[0].lower() if info_tokens else None
        attributes = {t.lower() for t in info_tokens[1:]}
        start_line = i + 1  # 1-based
        i += 1
        body: list[str] = []
        while i < n:
            line = lines[i]
            # Closing fence: same char, length >= opening, may be indented up to 3 spaces
            stripped = line.lstrip(" ")
            leading = len(line) - len(stripped)
            if (
                leading <= 3
                and len(stripped) >= fence_len
                and all(c == fence_char for c in stripped[:fence_len])
                and stripped[fence_len:].strip() == ""
            ):
                i += 1
                break
            # CommonMark says content is de-indented by the opening indent, but at most
            # by the number of spaces actually present. For our purposes preserving
            # content exactly is safer than trying to mimic a full CommonMark parser.
            body.append(line[indent:] if line.startswith(" " * indent) else line)
            i += 1
        else:
            # EOF before closing fence — still record the snippet, pyright will
            # complain about the content.
            pass
        index += 1
        snippets.append(
            {
                "index": index,
                "line": start_line,
                "language": language,
                "attributes": sorted(attributes),
                "source": "\n".join(body) + ("\n" if body else ""),
                "expect_error": _has_expect_error(body),
                "expected_errors": _extract_expected_errors(body),
            }
        )
    return snippets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Markdown file to scan")
    args = parser.parse_args()
    text = args.path.read_text(encoding="utf-8")
    snippets = extract(text)
    json.dump(snippets, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
