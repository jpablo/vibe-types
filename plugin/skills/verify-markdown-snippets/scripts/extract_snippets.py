#!/usr/bin/env python3
"""Extract fenced code blocks from a markdown file.

Emits a JSON list on stdout where each entry is:
    {"index": int, "line": int, "language": str | None, "source": str}

- `index` is 1-based over all fences in the file.
- `line` is the 1-based line number of the opening fence in the source file.
- `language` is the info string's first word, lowercased, or None if absent.
- `source` is the snippet content without the fences.

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
        language = info.split()[0].lower() if info else None
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
                "source": "\n".join(body) + ("\n" if body else ""),
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
