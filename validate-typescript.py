#!/usr/bin/env python3
"""
Validate and fix TypeScript snippets in markdown documentation files.

This script:
1. Extracts TypeScript code snippets from markdown files
2. Compiles them with tsc to check for errors
3. Uses AI to fix compilation errors (or annotate intentional ones)
4. Validates the fixes
"""

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SnippetLocation:
    """Tracks where a snippet was found."""

    file_path: str
    line_number: int  # first line of content (after opening fence)
    end_line: int     # last line of content (before closing fence)


@dataclass
class TypeScriptSnippet:
    """Represents a TypeScript code snippet with its metadata."""

    content: str
    location: SnippetLocation
    context: str = ""  # surrounding markdown text before the code block
    original_content: str = ""

    def __post_init__(self):
        if not self.original_content:
            self.original_content = self.content


@dataclass
class CompilationError:
    """Represents a TypeScript compilation error."""

    file: str
    line: int
    column: int
    message: str
    code: int = 0


def extract_typescript_snippets(
    file_path: str, context_lines: int = 15
) -> list[TypeScriptSnippet]:
    """Extract all TypeScript code blocks from a markdown file, with surrounding context."""
    snippets = []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Pattern to match any code fence (``` with optional language identifier).
    # Using * (not +) so closing fences (plain ```) also match with an empty group.
    code_block_pattern = re.compile(r"^```([a-zA-Z]*)")

    in_code_block = False
    block_start = 0
    current_language = ""
    current_content = []

    for i, line in enumerate(lines, 1):
        match = code_block_pattern.match(line.strip())

        if match:
            language = match.group(1).lower()

            if not in_code_block:
                if language in ("typescript", "ts"):
                    in_code_block = True
                    block_start = i
                    current_language = language
                    current_content = []
            else:
                # Ending the code block
                if current_language in ("typescript", "ts") and current_content:
                    content = "".join(current_content)

                    # Capture context: lines before the opening fence
                    context_start = max(0, block_start - 1 - context_lines)
                    context_end = block_start - 1  # up to (but not including) opening fence
                    context = "".join(lines[context_start:context_end])

                    snippets.append(
                        TypeScriptSnippet(
                            content=content,
                            location=SnippetLocation(
                                file_path=file_path,
                                line_number=block_start + 1,  # first content line
                                end_line=i - 1,               # last content line
                            ),
                            context=context,
                        )
                    )
                in_code_block = False
                current_content = []
                current_language = ""
        elif in_code_block and current_language in ("typescript", "ts"):
            current_content.append(line)

    return snippets


def find_markdown_files(inputs: list[str]) -> list[str]:
    """Find all markdown files in the given directories or files."""
    markdown_files = []

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


def compile_typescript(code: str) -> tuple[bool, list[CompilationError]]:
    """Compile TypeScript code and return errors if any."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
        f.write(code)
        temp_file = f.name

    try:
        result = subprocess.run(
            ["tsc", "--noEmit", "--strict", temp_file],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return True, []

        # tsc error format: /path/file.ts(line,col): error TS2322: message
        errors = []
        error_pattern = re.compile(
            r"^([^(]+)\((\d+),(\d+)\):\s+(error|warning)\s+TS(\d+):\s+(.+)$"
        )

        for line in (result.stderr + result.stdout).split("\n"):
            if not line.strip():
                continue
            m = error_pattern.match(line.strip())
            if m:
                errors.append(
                    CompilationError(
                        file=os.path.basename(m.group(1)),
                        line=int(m.group(2)),
                        column=int(m.group(3)),
                        message=m.group(6),
                        code=int(m.group(5)),
                    )
                )

        # If we got a non-zero exit but no parsed errors, surface raw output
        if not errors:
            raw = (result.stderr + result.stdout).strip()
            if raw:
                errors.append(CompilationError("tsc", 0, 0, raw[:200]))

        return False, errors

    except subprocess.TimeoutExpired:
        return False, [CompilationError("system", 0, 0, "Compilation timeout")]
    except FileNotFoundError:
        print("Error: tsc not found. Install with: npm install -g typescript")
        return False, [
            CompilationError(
                "system",
                0,
                0,
                "TypeScript compiler not found - install with 'npm install -g typescript'",
            )
        ]
    except Exception as e:
        print(f"Error running tsc: {e}")
        return False, [
            CompilationError("system", 0, 0, f"TypeScript compiler error: {str(e)}")
        ]
    finally:
        try:
            os.unlink(temp_file)
        except OSError:
            pass


def compile_with_stubs(
    code: str, errors: list[CompilationError]
) -> tuple[bool, list[CompilationError]]:
    """Re-compile a snippet with synthetic declare stubs for TS2304 missing names.

    Handles cross-snippet dependencies: if a snippet references a type declared in an
    earlier snippet, tsc reports TS2304 for each unknown name. We extract the names,
    prepend `declare const X: any; declare type X = any;` stubs, and recompile. The
    stubs live only in the temp file — the markdown source is never touched.

    Returns the result of the stub-injected compilation, or the original errors if there
    are no TS2304 errors to resolve.
    """
    missing_name_pattern = re.compile(r"Cannot find name '(.+?)'")
    names: set[str] = set()
    for e in errors:
        if e.code == 2304:
            m = missing_name_pattern.search(e.message)
            if m:
                names.add(m.group(1))

    if not names:
        return False, errors

    # Declare each missing name as both a value and a type so it works in any context.
    stubs = "\n".join(
        f"declare const {n}: any; declare type {n} = any;" for n in sorted(names)
    )
    return compile_typescript(stubs + "\n" + code)


def extract_code_from_response(response: str) -> str:
    """Extract TypeScript code from an AI response that may contain markdown or prose."""
    # Try to find a ```typescript or ```ts block
    ts_block = re.search(r"```(?:typescript|ts)\n(.*?)```", response, re.DOTALL)
    if ts_block:
        return ts_block.group(1)

    # Fall back to any ``` block
    any_block = re.search(r"```\n(.*?)```", response, re.DOTALL)
    if any_block:
        return any_block.group(1)

    # Return as-is if no fences found
    return response.strip()


def fix_with_ai(
    code: str, errors: list[CompilationError], context: str = ""
) -> Optional[str]:
    """Use opencode to fix TypeScript compilation errors or annotate intentional ones."""
    if not errors:
        return code

    error_descriptions = "\n".join(
        f"Line {e.line}, Column {e.column} (TS{e.code}): {e.message}"
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

    prompt = f"""You are reviewing a TypeScript code snippet extracted from documentation.

{context_section}
The TypeScript snippet:

```typescript
{code}
```

Compilation errors reported by tsc:
{error_descriptions}

Instructions:
1. Read the context above (if any) to decide whether each error is intentional.
   - If the surrounding text labels the snippet as showing incorrect/wrong/anti-pattern usage,
     the error is INTENTIONAL. In that case do NOT remove or rewrite the incorrect code.
     Instead, add a `// @ts-expect-error` comment on the line immediately before the
     offending line so that tsc accepts it while preserving the intent of the example.
   - If the error is a genuine bug in code that is meant to work correctly, fix it.
2. Maintain the original formatting and style.
3. Only change what is necessary.
4. Return ONLY the fixed TypeScript code with no additional explanation, no markdown fences.
"""

    try:
        result = subprocess.run(
            [
                "opencode",
                "run",
                "--dangerously-skip-permissions",
                prompt,
            ],
            capture_output=True,
            text=True,
        )

        output = result.stdout.strip()

        # Detect opencode help/error output (not a real response)
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

        # start_line is the first content line (1-indexed), end_line is the last.
        # Lines are 0-indexed in the list, so:
        #   content occupies lines[start_line-1 : end_line]
        # The opening fence is at lines[start_line-2] and closing at lines[end_line].

        fixed_content = fixed_snippet
        if not fixed_content.endswith("\n"):
            fixed_content += "\n"

        new_lines = (
            lines[: start_line - 1]          # everything up to (not incl.) first content line
            + [fixed_content]                  # replacement content
            + lines[end_line:]                 # closing fence and everything after
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return True

    except Exception as e:
        print(f"Error updating file {file_path}: {e}")
        return False


def main(directories: list[str] = None):
    """Main entry point."""
    if not directories:
        base_dir = Path(__file__).parent
        directories = [
            str(base_dir / "plugin" / "skills" / "typescript" / "catalog"),
            str(base_dir / "plugin" / "skills" / "typescript" / "usecases"),
        ]

    print(f"Searching for TypeScript snippets in: {directories}")

    markdown_files = find_markdown_files(directories)
    print(f"Found {len(markdown_files)} markdown files\n")

    total_snippets = 0
    snippets_with_errors = 0
    snippets_fixed = 0

    for file_path in markdown_files:
        print(f"Processing: {file_path}")

        snippets = extract_typescript_snippets(file_path)

        if not snippets:
            continue

        total_snippets += len(snippets)

        for snippet in snippets:
            success, errors = compile_typescript(snippet.content)

            if not success:
                # Try resolving cross-snippet references with synthetic declare stubs.
                # If all errors were just unknown names from earlier snippets, this
                # clears them without touching the markdown source.
                stub_success, stub_errors = compile_with_stubs(snippet.content, errors)
                if stub_success:
                    print(
                        f"  ✅ Snippet at line {snippet.location.line_number} valid "
                        f"(cross-snippet refs resolved via stubs)"
                    )
                    continue

                # Use the post-stub error list: it may be shorter if stubs resolved some
                # errors, leaving only the genuine ones for the AI.
                errors = stub_errors

                snippets_with_errors += 1
                print(
                    f"  ❌ Error in snippet at line {snippet.location.line_number}:"
                )
                for error in errors[:3]:
                    code_lines = snippet.content.split("\n")
                    if 0 < error.line <= len(code_lines):
                        actual_line = code_lines[error.line - 1].strip()
                        print(f"     Line {error.line}: {actual_line[:80]}")
                    print(f"     TS{error.code}: {error.message[:100]}")

                fixed_code = fix_with_ai(snippet.content, errors, snippet.context)

                if fixed_code:
                    print(f"  🤖 Fix generated by AI, validating...")

                    fix_success, fix_errors = compile_typescript(fixed_code)

                    if fix_success:
                        print(f"  ✅ Fix validated successfully")

                        if update_file_with_fix(
                            file_path,
                            fixed_code,
                            snippet.location.line_number,
                            snippet.location.end_line,
                        ):
                            snippets_fixed += 1
                            print(f"  📝 File updated")
                        else:
                            print(f"  ❌ Failed to update file")
                    else:
                        print(f"  ⚠️  Fix still has errors:")
                        for error in fix_errors[:3]:
                            print(f"     TS{error.code}: {error.message[:100]}")
                else:
                    print(f"  ⚠️  No fix generated (manual intervention required)")
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

    directories = sys.argv[1:] if len(sys.argv) > 1 else None
    main(directories)
