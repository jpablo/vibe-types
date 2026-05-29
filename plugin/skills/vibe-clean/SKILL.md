---
name: vibe-types:clean
description: >
  Apply vibe-types catalog and use-case knowledge to refactor source files in
  place. Use when the user invokes /vibe-clean (or asks you to "vibe-clean" a
  file, directory, or branch) to systematically improve code using the
  techniques in the loaded vibe-types skill. Does NOT change observable
  behavior, public APIs, or test assertions.
version: 0.1.0
---

# vibe-types:clean — Apply vibe-types knowledge to source files

> **Skill root:** `${CLAUDE_PLUGIN_ROOT}/skills`

Refactor source files by applying every relevant technique from the vibe-types
catalog and use-case library. Work through `(knowledge-file × source-file)` pairs
sequentially, editing files in place with your native tools.

---

## Invocation

```
/vibe-clean --skill <lang> (--file <path> | --dir <path> | --branch <name>) [OPTIONS]
```

Exactly one of `--file`, `--dir`, or `--branch` must be given.  
Either `--skill` or `--skill-dir` must be given.

## Arguments

| Flag | Default | Description |
|---|---|---|
| `--skill <lang>` | — | Language: `typescript`, `python`, `rust`, `scala3`, `lean`, `haskell`, `ocaml`, `java` |
| `--skill-dir <path>` | — | Override: explicit path to skill directory |
| `--file <path>` | — | Single source file |
| `--dir <path>` | — | All matching files in directory (recursive) |
| `--branch <name>` | — | Files changed on this branch vs. merge-base |
| `--build <cmd>` | none | Shell command to verify after each edit |
| `--max-retries N` | 3 | Fix attempts per build failure |
| `--commit` | false | Commit after each (knowledge × source) pair |
| `--only T01,UC03,...` | all | Process only these knowledge IDs |
| `--dry-run` | false | Print plan without editing |
| `--consolidate` | false | Final coherence pass after all techniques |
| `--principles <file>` | built-in | Custom principles file for consolidation |
| `--base-branch <name>` | `main` | Base for `--branch` diff |
| `--progress <file>` | `.vibe-clean-progress` | Progress tracking file |

---

## Language → file extensions

```
typescript  →  .ts  .tsx  .mts  .cts
python      →  .py
rust        →  .rs
scala3      →  .scala  .sc
lean        →  .lean
haskell     →  .hs
ocaml       →  .ml  .mli
java        →  .java
```

---

## Step 1 — Resolve skill directory

```
SKILL_DIR = ${CLAUDE_PLUGIN_ROOT}/skills/<lang>/    # --skill given
SKILL_DIR = <path>                                   # --skill-dir given
```

Verify `SKILL_DIR` exists. If not, list the directories under
`${CLAUDE_PLUGIN_ROOT}/skills/` and stop.

---

## Step 2 — Collect knowledge files

1. Find all `.md` files under `SKILL_DIR/catalog/` and `SKILL_DIR/usecases/`
   (maxdepth 1 each), sorted by basename.
2. Skip `00-overview.md`.
3. If `--only` is given, keep only files whose basename starts with one of the
   provided IDs — e.g. `T01` matches `T01-algebraic-data-types.md`;
   `UC03` matches `UC03-exhaustiveness.md`.
4. For each file extract: `kid` = leading segment before first `-`; `ktitle` =
   first `# ` heading line.

---

## Step 3 — Collect source files

**`--file`**: verify the single path exists and matches the language extension.

**`--dir`**: run Bash `find` from the resolved directory, pruning these names:
`node_modules dist build target .git __pycache__ .next out coverage .cache
.tox .eggs .mypy_cache`. Keep only regular files matching the language
extensions. Sort output.

**`--branch`**: run `git diff --name-only <merge-base> <branch>` (where
`merge-base = git merge-base <branch> <base-branch>`), filter paths to language
extensions, verify each file exists on disk.

---

## Step 4 — Pre-flight checks

- `--commit` or `--branch` requires a git repository.
- Unless `--dry-run`: verify the target git repo has no uncommitted changes
  (excluding the progress file). If dirty, stop and ask the user to commit or
  stash first.
- Record `run_start_head = git rev-parse HEAD` for prior-diff tracking.

---

## Step 5 — Dry run

If `--dry-run`: print every planned `(knowledge-file, source-file)` pair, the
total count, and stop. Make no edits.

---

## Step 6 — Main loop

Read the progress file at the `--progress` path. Each line is either
`done <kfile> <sfile>` or `failed <kfile>`.

**Outer loop — knowledge files** (sorted order):

- If `failed <kfile>` is in the progress file: log "skipping (previously
  failed)" and continue to the next knowledge file.

**Inner loop — source files** (sorted order):

- If `done <kfile> <sfile>` is in the progress file: log "skip" and continue.

### Apply step

1. Compute `prior_diff` — changes already made to this source file during the
   current run:
   - `--commit` mode: `git diff <run_start_head>..HEAD -- <sfile>`
   - Otherwise: `git diff HEAD -- <sfile>`
2. Read the knowledge file.
3. Read the source file.
4. Edit the source file to apply techniques from the knowledge document:
   - Only make changes that the knowledge genuinely warrants.
   - Do NOT change observable behavior, public APIs, or test assertions.
   - Prefer minimal, targeted edits over wholesale rewrites.
   - If `prior_diff` is non-empty, treat those changes as settled — do not
     revert or contradict them.
   - If nothing in the knowledge file applies, leave the file untouched.

### Build step (if `--build`)

Run the build command via Bash. If it fails:

```
for attempt in 1 .. max-retries:
    read the build errors
    edit <sfile> to fix them (preserve the intent of prior changes)
    re-run the build
    if build passes → break
```

If the build still fails after `max-retries`:
- Revert the file: `git checkout -- <sfile>`
- Append `failed <kfile>` to the progress file.
- Print an error message with the progress file path.
- Stop the run. The user can fix the underlying issue and re-run to resume.

### Record

Append `done <kfile> <sfile>` to the progress file.

### Commit step (if `--commit`)

```bash
git add -A
git restore --staged <progress-file>   # never commit the progress file
```

If there are staged changes, commit:

```
cleanup(<kid>): <ktitle>

Knowledge: <github-blob-url-to-kfile>   # if determinable
Source: <relative-path-to-sfile>
```

---

## Step 7 — Consolidation pass (if `--consolidate`)

For each source file, compute its full diff across the run. If empty (file
unchanged), skip.

1. Read the principles: `--principles <file>` if given; otherwise use the
   built-in text below.
2. Read the source file.
3. Edit for overall coherence:
   - Resolve contradictions or redundancies introduced by the individual passes.
   - Align the design with the principles.
   - Ensure the file reads as if written with a single coherent intent.
   - Do NOT change observable behavior, public APIs, or test assertions.
   - If the file is already consistent, leave it untouched.
4. If `--build`: verify build; retry up to `--max-retries`; if still failing,
   revert and skip (non-fatal — continue to the next file).
5. If `--commit`: commit as `consolidate: <rel-path>`.

### Built-in consolidation principles

```
S — Single Responsibility: each type, function, and module has one clear reason to change.
O — Open/Closed: extend through new types or functions; avoid modifying stable abstractions.
L — Liskov Substitution: subtypes must honour the contracts of their interfaces.
I — Interface Segregation: keep interfaces narrow; callers depend only on what they use.
D — Dependency Inversion: high-level modules depend on abstractions, not concrete implementations.

DRY (Don't Repeat Yourself): extract shared logic and types rather than duplicating them.
KISS (Keep It Simple): prefer the simplest correct solution; avoid unnecessary abstraction.
Cohesion: group related types and functions; a module should have a single, clear purpose.
```

---

## Step 8 — Summary

Print:

```
Knowledge files:             N
Source files targeted:       N
Pairs attempted:             N
Pairs skipped (resuming):    N
Build errors fixed:          N
Files consolidated:          N   (only if --consolidate)
Commits created:             N   (only if --commit)
```

---

## Core rules (always apply)

1. Never change observable behavior, public APIs, or test assertions.
2. Prefer minimal, targeted edits over wholesale rewrites.
3. When unsure whether a technique applies, leave the file unchanged.
4. Always check the progress file before starting any pair — never redo
   completed work.
5. Keep each knowledge file's content in working context only for the pairs
   that use it; do not accumulate all knowledge files at once.
