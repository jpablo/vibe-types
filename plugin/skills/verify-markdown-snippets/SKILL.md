---
name: verify-markdown-snippets
description: Verify every code snippet embedded in a markdown file for syntactic and type correctness, using the language-specific project under `projects/`. Use this skill proactively whenever the user asks to check, verify, validate, lint, or type-check code examples inside markdown — docs, tutorials, PR reviews of documentation changes, skill catalogs, blog posts, README files, anything with fenced code blocks. Also use it when the user is reviewing a pull request that touches markdown files containing code examples, or when they mention wanting to make sure their documentation code is "runnable" or "doesn't lie". The skill produces a per-snippet report (both markdown and JSON) listing exact syntax errors, type errors, and any snippets that lack a language tag.
---

# verify-markdown-snippets

## What this skill does

Given a markdown file, for every fenced code block:

1. Extract the snippet, its starting line number in the source file, and the language tag on the fence.
2. For Python (the only language in v1): run a pure-syntax check with `ast.parse`, then run `pyright` from the venv in `projects/python-project/`.
3. Produce a report — markdown for humans, JSON for tooling — pointing at the exact fence line and showing verbatim error output from the checker.

The point is to make documentation code **trustworthy**: readers should be able to copy a snippet out of a doc and have it work. When that's not the case, we want a fast, automated way to find every offender.

## Why pyright and not execution

The instinct is to actually run the code and see what explodes. Don't. Executing arbitrary snippets from a markdown file is slow, has side effects, and still won't catch things that fail in only some call sites.

Pyright (in standard mode) already surfaces the class of bugs we care about in documentation:

- **Syntax errors** — decorators on the wrong line, `def foo:` missing parentheses, unbalanced brackets. (`ast.parse` catches these too, and we run it first so the error is clearer.)
- **Dataclass default-ordering** — "Fields without default values cannot appear after fields with default values."
- **`Literal[...]` with forbidden values** — dicts, tuples of primitives, class objects.
- **Undefined names** — a snippet that forgot to `import` something or reference a name that isn't declared.
- **Wrong argument counts and types** on function/constructor calls.
- **TypedDict misuse**, bad `type X = ...` aliases, malformed generics.

That's the whole universe of bugs we found in the recent `python_examples` PR review. `ast.parse` + pyright covers it without running a single line of snippet code.

## How to run it

The skill ships a single orchestrator script. In almost every case, this is all you need:

```bash
cd /Users/jpablo/GitHub/vibe-types
python plugin/skills/verify-markdown-snippets/scripts/verify_markdown.py <path-to-markdown-file> [--out <report-dir>]
```

What happens:

1. `extract_snippets.py` walks the file and yields every fenced block with `(language, start_line, content)`.
2. For each Python block, `verify_python.py` writes it to a temp file inside `projects/python-project/` (so pyright picks up the project's `pyrightconfig.json` / `pyproject.toml` and the venv's installed packages), runs `ast.parse`, then runs `uv run pyright --outputjson <temp>`.
3. Results are aggregated into:
   - `<report-dir>/<input-stem>.report.md` — one section per snippet, human-readable.
   - `<report-dir>/<input-stem>.report.json` — structured, for downstream tooling.
4. If `--out` is omitted, both files are written next to the input markdown with the suffix `.report.md` / `.report.json`.

The orchestrator returns exit code 0 if every snippet is clean, 1 if any snippet has errors, 2 if the skill itself failed to run (missing venv, etc.).

## Report structure

Always use this exact structure for the markdown report so downstream tooling and reviewers know what to expect:

```markdown
# Snippet verification report — <input filename>

**File:** `<absolute or repo-relative path>`
**Checked:** <N> snippets (<M> python, <K> other, <U> unlabeled)
**Status:** <OK | N errors across M snippets>

## Summary

| # | Line | Lang | Status | Errors |
|---|------|------|--------|--------|
| 1 | 42 | python | ok | 0 |
| 2 | 118 | python | fail | 3 |
| 3 | 204 | — | skipped (no lang tag) | — |

## Snippet 1 — line 42 — python — ok

(no errors)

## Snippet 2 — line 118 — python — fail

**Syntax:** ok
**Pyright:** 3 errors

- `line 3, col 5`: Fields without default values cannot appear after fields with default values
- `line 7, col 1`: "Literal" accepts only values of type int, str, bytes, bool, enum, or None
- ...

### Source

    ```python
    ... the actual snippet verbatim ...
    ```

## Snippet 3 — line 204 — skipped (no language tag)

This fence has no language tag. Skipped. If this is Python, add ` ```python ` on the fence line.

### Source
    ``` ... ```
```

The JSON report mirrors the same information:

```json
{
  "input_file": "plugin/skills/python/catalog/T02-union-intersection.md",
  "checked_snippets": 8,
  "counts": {"python": 7, "other": 0, "unlabeled": 1, "ok": 4, "fail": 3, "skipped": 1},
  "snippets": [
    {
      "index": 1,
      "line": 42,
      "language": "python",
      "status": "ok",
      "syntax": {"ok": true, "error": null},
      "pyright": {"ok": true, "errors": []},
      "source": "..."
    },
    {
      "index": 2,
      "line": 118,
      "language": "python",
      "status": "fail",
      "syntax": {"ok": true, "error": null},
      "pyright": {
        "ok": false,
        "errors": [
          {"line": 3, "col": 5, "severity": "error", "message": "..."}
        ]
      },
      "source": "..."
    }
  ]
}
```

## How the pieces fit together

- `scripts/extract_snippets.py` — pure extractor. Takes a markdown path, emits JSON to stdout. Uses a simple state machine over fences (``` and ~~~, respecting info strings and fence length per CommonMark) so it handles nested fences and indented fences. Importantly: it is language-agnostic and does no verification.
- `scripts/verify_python.py` — takes a single snippet (stdin or file) and runs `ast.parse` + pyright in the `projects/python-project` environment. Returns a JSON result for that snippet.
- `scripts/verify_markdown.py` — the orchestrator. Glue code: extract → dispatch by language → aggregate → write markdown + JSON.

Keeping extraction, per-language verification, and reporting in separate scripts means adding a new language later (`verify_typescript.py`, `verify_rust.py`) doesn't require touching the other parts.

## Handling edge cases

**Unlabeled fences.** Report with `status: "skipped"` and `language: null`. Don't guess — false positives on language detection lead to confusing errors like "SyntaxError" on a snippet that was actually shell output. A one-line mention in the report is enough to prompt a fix.

**Non-Python languages (ts, rust, bash, json, etc.).** Same: skip with `status: "skipped"` and `language: "<detected>"`, and add a note in the report that no verifier is wired up for this language yet. Do **not** error out — the skill should still produce a useful report for the Python snippets.

**Snippets that reference names from earlier blocks in the same file.** Each snippet is checked in isolation (per the user's decision). If a snippet uses `Foo` without defining or importing it, pyright will report "Foo is not defined" — and that's a legitimate finding: the snippet as written is not copy-pasteable. Don't try to be clever and stitch blocks together.

**Intentional antipattern demonstrations.** Documentation often shows deliberately broken code to teach what not to do (e.g., `def unsafe(x: int | None) -> int: return x + 1  # error: unsupported operand`). This skill will flag those as failing — because from pyright's perspective they are. There's no way for the skill to distinguish "this is wrong on purpose" from "this is wrong by accident" without an author annotation. When presenting the report to a user, point out this limitation so they can skim the failures and mentally discount the intentional ones. A future version may support an `expect-errors` tag on the fence info string to mark demonstration snippets.

**Fences tagged `python` that aren't Python.** Sometimes authors use a ` ```python ` fence for rendered pyright/mypy output, tracebacks, or REPL sessions. These will fail parsing with confusing errors. The report entry will make the mismatch obvious (the snippet source is plainly not Python), and the fix is to retag the fence as ` ``` ` or ` ```text ` in the source document.

**Pyright produces warnings but no errors.** Treat only `severity == "error"` as a failing result. Include warnings in the report under a separate bullet, but they don't flip the status.

**Python version.** The `projects/python-project/pyproject.toml` pins `requires-python = ">=3.14"`. That means newer features (PEP 695 `type` aliases, `match` statements, `TypeVarTuple` unpacking syntax) are available. Don't downgrade.

**Pyright missing.** If `uv run pyright --version` fails inside `projects/python-project/`, exit with code 2 and a clear message telling the user to run `uv sync` there. Don't silently fall back to syntax-only.

**Hidden temp directories.** When writing snippet temp files inside `projects/python-project/`, do **not** put them in a directory whose name starts with a dot (`.snippet-tmp`, `.tmp`, etc.). Pyright's default include set skips hidden directories and will silently analyze zero files — you'll get a false green for every snippet. Use `snippet_tmp/` or similar. The skill's `verify_python.py` already does this; the warning is here so anyone extending the skill doesn't trip on it.

**System Python version mismatch.** The syntax check must run under the project's Python, not the system Python. On macOS, `/usr/bin/python3` is commonly 3.9, which rejects `match` statements, PEP 695 `type` aliases, and other modern syntax that the Python 3.14 project happily accepts. `verify_python.py` delegates `ast.parse` to a subprocess run via `uv run python` for exactly this reason.

## Invocation examples

Concrete things a reviewer might type that should trigger this skill:

- "Can you check every Python snippet in `plugin/skills/python/catalog/T02-union-intersection.md`?"
- "I'm reviewing PR #6, can you verify the code examples in the three changed markdown files?"
- "Make sure all the code in this tutorial actually typechecks."
- "Are any of the snippets in this doc broken?"
- "Run pyright over the fenced blocks in README.md."

Whenever the request is "markdown file + verify/check/lint the code inside it", use this skill rather than extracting snippets by hand.
