---
description: Add a vibe-types quick index to a CLAUDE.md file for always-on type safety guidance
disable-model-invocation: true
argument-hint: "[language]"
---

# Install vibe-types context

This command adds a language-specific quick index snippet to a CLAUDE.md file so that type-safety guidance is always available in context.

## Steps

1. **Choose the language.** If `$ARGUMENTS` specifies a language, use it. Otherwise:
   - First, detect the project language by checking for signature files: `*.py` or `pyproject.toml` → Python, `Cargo.toml` or `*.rs` → Rust, `lakefile.lean` or `*.lean` → Lean 4, `build.sbt` or `build.sc` or `*.scala` → Scala 3.
   - Present the numbered menu below. If a language was detected, mark it as `(detected)` and make it the default. Accept just the number or Enter for the default.

```
Which language? [default: 2 — detected Rust project]
  1. Python
  2. Rust  (detected)
  3. Lean 4
  4. Scala 3
  5. All
```

2. **Choose the target file.** Present this numbered menu and accept just the number:

```
Where should the snippet go?
  1. ~/.claude/CLAUDE.md        (personal, all projects)
  2. .claude/CLAUDE.md          (project, version-controlled)
  3. .claude/CLAUDE.local.md    (project, gitignored)
  4. Custom path
```

If the user picks 4, ask for the path.

3. **Read the target file** (if it exists) to check whether the snippet is already present. Look for the marker `<!-- vibe-types:<lang> -->`. If found, tell the user it's already installed and ask whether to replace it.

4. **Append the snippet** to the end of the file (create it if it doesn't exist). Read the snippet from the canonical source file at `${CLAUDE_PLUGIN_ROOT}/skills/<lang>/quick-index.md` (where `<lang>` is `python`, `rust`, `lean`, or `scala3`). Wrap the content in marker comments `<!-- vibe-types:<lang> -->` / `<!-- /vibe-types:<lang> -->`. Include a blank line before the marker.

5. **Confirm** what was added and where.
