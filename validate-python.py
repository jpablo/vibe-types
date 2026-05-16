#!/usr/bin/env python3
"""
Validate and fix Python snippets in markdown documentation files.

This script:
1. Extracts Python code snippets from markdown files
2. Validates them with pyright (# error: inline comments indicate expected type errors)
3. Uses AI (opencode) to fix unexpected pyright errors or add # type: ignore
4. Validates the fixes and updates files in place
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).parent
PYTHON_PROJECT = REPO_ROOT / "projects" / "python-project"

# Matches inline # error annotations (with or without colon/message) on non-comment lines.
# (comment-only lines like `    # error: ...` are filtered separately by the caller.)
_INLINE_ERROR = re.compile(
    r'\s*#\s*(?:expect\s*-\s*error|(?:type[\s:]+)?error|TypeError)(?::\s*.*)?$',
    re.IGNORECASE,
)

# Matches # pyright: directives that are NOT valid pyright commands.
# Valid ones are: ignore, basic, standard, strict, off, on.
# Lines like `# pyright: error: ...` are documentation comments, not real directives.
_INVALID_PYRIGHT_DIRECTIVE = re.compile(
    r'(#\s*)pyright:\s*(?!ignore|basic|standard|strict|off|on)(.+)$',
    re.IGNORECASE,
)


@dataclass
class SnippetLocation:
    file_path: str
    line_number: int  # first content line (1-based, after opening fence)
    end_line: int     # last content line (1-based, before closing fence)


@dataclass
class PythonSnippet:
    content: str
    location: SnippetLocation
    context: str = ""
    original_content: str = ""

    def __post_init__(self) -> None:
        if not self.original_content:
            self.original_content = self.content


@dataclass
class PyrightError:
    line: int
    col: int
    severity: str
    message: str
    rule: Optional[str] = None


def extract_python_snippets(
    file_path: str, context_lines: int = 15
) -> list[PythonSnippet]:
    """Extract all Python code blocks from a markdown file with surrounding context."""
    snippets: list[PythonSnippet] = []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    code_block_pattern = re.compile(r"^```([a-zA-Z]*)")
    in_code_block = False
    block_start = 0
    current_language = ""
    current_content: list[str] = []

    for i, line in enumerate(lines, 1):
        match = code_block_pattern.match(line.strip())
        if match:
            language = match.group(1).lower()
            if not in_code_block:
                if language in ("python", "py"):
                    in_code_block = True
                    block_start = i
                    current_language = language
                    current_content = []
            else:
                if current_language in ("python", "py") and current_content:
                    content = textwrap.dedent("".join(current_content))
                    context_start = max(0, block_start - 1 - context_lines)
                    context_end = block_start - 1
                    context = "".join(lines[context_start:context_end])
                    snippets.append(
                        PythonSnippet(
                            content=content,
                            location=SnippetLocation(
                                file_path=file_path,
                                line_number=block_start + 1,
                                end_line=i - 1,
                            ),
                            context=context,
                        )
                    )
                in_code_block = False
                current_content = []
                current_language = ""
        elif in_code_block and current_language in ("python", "py"):
            current_content.append(line)

    return snippets


def find_markdown_files(inputs: list[str]) -> list[str]:
    """Find all markdown files in the given directories or files."""
    markdown_files: list[str] = []
    for input_path in inputs:
        if not os.path.exists(input_path):
            print(f"Warning: Path not found: {input_path}")
            continue
        if os.path.isfile(input_path):
            if input_path.endswith(".md"):
                markdown_files.append(input_path)
            continue
        for root, _, files in os.walk(input_path):
            for file in files:
                if file.endswith(".md"):
                    markdown_files.append(os.path.join(root, file))
    return markdown_files


def _is_comment_only_line(line: str) -> bool:
    return line.lstrip().startswith("#")


def get_inline_error_lines(code: str) -> set[int]:
    """Return 1-based line numbers that have inline # error: annotations.

    Excludes comment-only lines (where the whole line is a comment).
    """
    result: set[int] = set()
    for i, line in enumerate(code.splitlines(), 1):
        if _is_comment_only_line(line):
            continue
        if _INLINE_ERROR.search(line):
            result.add(i)
    return result


def prepare_for_validation(code: str) -> str:
    """Replace inline # error: annotations with # type: ignore for pyright validation.

    Only transforms lines that have code before the # error: marker; comment-only
    lines are left as-is (they don't generate pyright errors themselves).
    """
    result: list[str] = []
    for line in code.splitlines():
        if _is_comment_only_line(line):
            # Neutralize `# pyright: error:` style comments — they look like directives
            # to pyright but are actually documentation annotations in these files.
            result.append(_INVALID_PYRIGHT_DIRECTIVE.sub(r'\1\2', line))
            continue
        m = _INLINE_ERROR.search(line)
        if m:
            result.append(line[: m.start()] + "  # type: ignore")
        else:
            result.append(line)
    return "\n".join(result) + ("\n" if code.endswith("\n") else "")


def run_pyright_raw(code: str) -> tuple[bool, list[PyrightError]]:
    """Run pyright on a code snippet. Returns (all_ok, errors)."""
    if not PYTHON_PROJECT.exists():
        return False, [
            PyrightError(0, 0, "error", f"python-project not found at {PYTHON_PROJECT}")
        ]

    tmp_dir = PYTHON_PROJECT / "snippet_tmp"
    tmp_dir.mkdir(exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        dir=tmp_dir,
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(code)
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
        return False, [PyrightError(0, 0, "error", "uv is not installed or not on PATH")]
    except subprocess.TimeoutExpired:
        tmp_path.unlink(missing_ok=True)
        return False, [PyrightError(0, 0, "error", "pyright timed out after 60s")]
    finally:
        tmp_path.unlink(missing_ok=True)

    try:
        payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        raw = (proc.stderr or proc.stdout or "").strip()
        return False, [PyrightError(0, 0, "error", raw[:200])]

    diagnostics = payload.get("generalDiagnostics", [])
    errors: list[PyrightError] = []
    for d in diagnostics:
        rng = d.get("range", {}).get("start", {})
        entry = PyrightError(
            line=(rng.get("line", 0) or 0) + 1,  # pyright is 0-indexed
            col=(rng.get("character", 0) or 0) + 1,
            severity=d.get("severity", "error"),
            message=d.get("message", ""),
            rule=d.get("rule"),
        )
        if entry.severity == "error":
            errors.append(entry)

    return len(errors) == 0, errors


def validate_snippet(code: str) -> tuple[bool, list[PyrightError]]:
    """Validate a snippet, treating inline # error: lines as expected.

    Converts inline # error: annotations to # type: ignore before running pyright,
    then filters out spurious 'unnecessary type ignore' errors on those transformed lines.
    """
    prepared = prepare_for_validation(code)
    transformed_lines = get_inline_error_lines(code)
    ok, errors = run_pyright_raw(prepared)
    if ok:
        return True, []

    # Filter "unnecessary type ignore" on lines we transformed from # error:
    # (this fires when the annotation was wrong and pyright wouldn't have reported
    # anything — that's a documentation issue but not a blocking validation failure).
    real_errors = [
        e
        for e in errors
        if not (
            (e.rule or "").lower() == "reportunnecessarytypeignorecomment"
            and e.line in transformed_lines
        )
    ]
    return len(real_errors) == 0, real_errors


# Names that should be imported from `typing` rather than stubbed as `Any` variables.
# Using `X: Any` for a typing construct causes pyright to reject it in type expressions
# with `reportInvalidTypeForm: Variable not allowed in type expression`.
_TYPING_NAMES: frozenset[str] = frozenset([
    "AbstractSet", "Any", "Callable", "ClassVar", "Concatenate", "Counter",
    "DefaultDict", "Deque", "Dict", "Final", "FrozenSet", "Generator", "Generic",
    "Hashable", "IO", "Iterator", "List", "Literal", "LiteralString", "Mapping",
    "Match", "MutableMapping", "MutableSequence", "MutableSet", "NamedTuple",
    "Never", "NewType", "NoReturn", "Optional", "ParamSpec", "Pattern", "Protocol",
    "Required", "NotRequired", "Self", "Sequence", "Set", "Sized", "SupportsAbs",
    "SupportsBytes", "SupportsComplex", "SupportsFloat", "SupportsInt",
    "SupportsRound", "TextIO", "Tuple", "Type", "TypeAlias", "TypeGuard",
    "TypeVar", "TypeVarTuple", "TypedDict", "Union", "Unpack",
    "assert_never", "assert_type", "cast", "dataclass_transform", "final",
    "get_args", "get_origin", "get_type_hints", "overload", "reveal_type",
    "runtime_checkable",
])


def compile_with_stubs(
    code: str, errors: list[PyrightError]
) -> tuple[bool, list[PyrightError]]:
    """Retry validation with stubs for undefined names (cross-snippet dependencies).

    Handles the same problem as the TypeScript script's compile_with_stubs: snippets
    often reference types or variables defined in earlier snippets in the same file.
    Known typing names get a proper `from typing import X`; everything else gets `X: Any`.
    """
    undefined_pattern = re.compile(r'"(.+?)" is not defined')
    names: set[str] = set()
    for e in errors:
        rule = (e.rule or "").lower()
        if rule in ("reportundefinedvariable", "reportpossiblyunbound") or "is not defined" in e.message:
            m = undefined_pattern.search(e.message)
            if m:
                names.add(m.group(1))

    if not names:
        return False, errors

    typing_imports = names & _TYPING_NAMES
    value_stubs = names - _TYPING_NAMES

    stubs_lines: list[str] = []
    if typing_imports:
        stubs_lines.append(f"from typing import {', '.join(sorted(typing_imports))}")
    if value_stubs:
        stubs_lines.append("from typing import Any, TypeAlias")
        # TypeAlias lets pyright accept these names in type expressions (e.g. Optional[User]).
        # Plain `X: Any` is a variable and pyright rejects it with reportInvalidTypeForm.
        stubs_lines.extend(f"{n}: TypeAlias = Any" for n in sorted(value_stubs))

    stubs = "\n".join(stubs_lines) + "\n"
    return validate_snippet(stubs + code)


def extract_code_from_response(response: str) -> str:
    """Extract Python code from an AI response that may contain markdown or prose."""
    py_block = re.search(r"```(?:python|py)\n(.*?)```", response, re.DOTALL)
    if py_block:
        return py_block.group(1)
    any_block = re.search(r"```\n(.*?)```", response, re.DOTALL)
    if any_block:
        return any_block.group(1)
    return response.strip()


def fix_with_ai(
    code: str, errors: list[PyrightError], context: str = ""
) -> Optional[str]:
    """Use opencode to fix Python type errors or annotate intentional ones."""
    if not errors:
        return code

    error_descriptions = "\n".join(
        f"Line {e.line}, Column {e.col} ({e.rule or 'error'}): {e.message}"
        for e in errors
    )

    context_section = ""
    if context.strip():
        context_section = f"""
The following markdown text appears just before this code snippet. Use it to understand
whether the errors are intentional (e.g. the snippet demonstrates an anti-pattern,
wrong usage, or is labelled "Wrong" / "Error"):

--- CONTEXT START ---
{context.strip()}
--- CONTEXT END ---
"""

    prompt = f"""You are reviewing a Python code snippet extracted from type-safety documentation.

{context_section}
The Python snippet:

```python
{code}
```

Issues reported by pyright:
{error_descriptions}

Your task is to produce a corrected version of this snippet. Consider ALL of the following:

1. **Syntax errors**: If the snippet has syntax errors, fix them so the code is valid Python.

2. **Type errors — intentional vs. genuine**:
   - If the offending line already has a `# error:` comment, the error is INTENTIONAL
     (it documents what pyright reports). Keep the `# error:` comment and append
     `  # type: ignore` at the very end of the line:
       code  # error: original message  # type: ignore
   - If the surrounding context marks the snippet as demonstrating wrong/anti-pattern usage,
     the error is INTENTIONAL — add `# type: ignore` to the end of the offending line.
   - If the error is a genuine bug in code that is meant to work correctly, fix it.

3. **Conceptual correctness**: Read the markdown context carefully. If the snippet does NOT
   correctly illustrate the technique or use case described in the context — for example,
   it fails to demonstrate the type constraint, uses the feature incorrectly, or contradicts
   the teaching intent — rewrite the snippet so it properly illustrates the concept.
   Preserve any intentional error lines (with `# error:` annotations) that are part of the
   teaching, and make sure the "correct usage" lines actually work and type-check cleanly.

Keep the original formatting and style. Only change what is necessary.
Return ONLY the corrected Python code with no additional explanation, no markdown fences.
"""

    try:
        result = subprocess.run(
            ["opencode", "run", "--dangerously-skip-permissions", prompt],
            capture_output=True,
            text=True,
        )
        output = result.stdout.strip()
        if not output or "Commands:" in output or "Positionals:" in output:
            stderr_preview = result.stderr[:200] if result.stderr else "(empty)"
            print(
                f"  Warning: opencode returned no usable response "
                f"(stdout: {len(output)} chars, stderr: {stderr_preview})"
            )
            return None
        return extract_code_from_response(output)
    except FileNotFoundError:
        print("  Warning: opencode not found. Manual fix required.")
        return None
    except Exception as e:
        print(f"  Warning: Error running opencode: {e}")
        return None


def update_file_with_fix(
    file_path: str,
    fixed_snippet: str,
    start_line: int,
    end_line: int,
) -> bool:
    """Replace the snippet content in a markdown file (between the fences)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        fixed_content = fixed_snippet
        if not fixed_content.endswith("\n"):
            fixed_content += "\n"

        # start_line is the first content line (1-indexed), end_line is the last.
        # Lines are 0-indexed in the list, so content occupies lines[start_line-1 : end_line].
        # The opening fence is at lines[start_line-2] and closing fence at lines[end_line].
        new_lines = (
            lines[: start_line - 1]  # everything up to (not incl.) first content line
            + [fixed_content]         # replacement content as a single string
            + lines[end_line:]        # closing fence and everything after
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return True
    except Exception as e:
        print(f"Error updating file {file_path}: {e}")
        return False


def main(directories: Optional[list[str]] = None) -> None:
    """Main entry point."""
    if not directories:
        base_dir = Path(__file__).parent
        directories = [
            str(base_dir / "plugin" / "skills" / "python" / "catalog"),
            str(base_dir / "plugin" / "skills" / "python" / "usecases"),
        ]

    if not PYTHON_PROJECT.exists():
        print(f"Error: Python project not found at {PYTHON_PROJECT}")
        print("The script requires projects/python-project/ with uv and pyright configured.")
        return

    print(f"Searching for Python snippets in: {directories}")

    markdown_files = find_markdown_files(directories)
    print(f"Found {len(markdown_files)} markdown files\n")

    total_snippets = 0
    snippets_with_errors = 0
    snippets_fixed = 0

    for file_path in markdown_files:
        print(f"Processing: {file_path}")
        snippets = extract_python_snippets(file_path)
        if not snippets:
            continue

        total_snippets += len(snippets)

        for snippet in snippets:
            ok, errors = validate_snippet(snippet.content)

            if not ok:
                # Try resolving cross-snippet references with Any stubs first.
                stub_ok, stub_errors = compile_with_stubs(snippet.content, errors)
                if stub_ok:
                    print(
                        f"  ✅ Snippet at line {snippet.location.line_number} valid "
                        f"(cross-snippet refs resolved via stubs)"
                    )
                    continue

                # Use the post-stub error list — may be shorter if stubs resolved some errors.
                errors = stub_errors

                snippets_with_errors += 1
                print(f"  ❌ Error in snippet at line {snippet.location.line_number}:")
                for error in errors[:3]:
                    code_lines = snippet.content.splitlines()
                    if 0 < error.line <= len(code_lines):
                        actual_line = code_lines[error.line - 1].strip()
                        print(f"     Line {error.line}: {actual_line[:80]}")
                    print(f"     {error.rule or 'error'}: {error.message[:100]}")

                fixed_code = fix_with_ai(snippet.content, errors, snippet.context)

                if fixed_code:
                    print("  🤖 Fix generated by AI, validating...")
                    fix_ok, fix_errors = validate_snippet(fixed_code)
                    if not fix_ok:
                        stub_fix_ok, _ = compile_with_stubs(fixed_code, fix_errors)
                        if stub_fix_ok:
                            fix_ok, fix_errors = True, []

                    if not fix_ok:
                        # First fix didn't pass — retry once with validation errors as context.
                        print("  🔄 Retrying AI fix with validation feedback...")
                        fixed_code2 = fix_with_ai(fixed_code, fix_errors, snippet.context)
                        if fixed_code2:
                            retry_ok, retry_errors = validate_snippet(fixed_code2)
                            if not retry_ok:
                                stub_retry_ok, _ = compile_with_stubs(fixed_code2, retry_errors)
                                if stub_retry_ok:
                                    retry_ok, retry_errors = True, []
                            if retry_ok:
                                fixed_code = fixed_code2
                                fix_ok, fix_errors = True, []
                            else:
                                fix_errors = retry_errors  # surface the retry's errors

                    if fix_ok:
                        print("  ✅ Fix validated successfully")
                        if update_file_with_fix(
                            file_path,
                            fixed_code,
                            snippet.location.line_number,
                            snippet.location.end_line,
                        ):
                            snippets_fixed += 1
                            print("  📝 File updated")
                        else:
                            print("  ❌ Failed to update file")
                    else:
                        print("  ⚠️  Fix still has errors:")
                        for error in fix_errors[:3]:
                            print(f"     {error.rule or 'error'}: {error.message[:100]}")
                else:
                    print("  ⚠️  No fix generated (manual intervention required)")
            else:
                print(f"  ✅ Snippet at line {snippet.location.line_number} is valid")

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Total snippets found:           {total_snippets}")
    print(f"  Snippets with errors:           {snippets_with_errors}")
    print(f"  Snippets fixed:                 {snippets_fixed}")
    print(f"  Snippets requiring manual fix:  {snippets_with_errors - snippets_fixed}")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    dirs = sys.argv[1:] if len(sys.argv) > 1 else None
    main(dirs)
