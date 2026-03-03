# Bringing vibe-types Into Pi Context

Companion to [bringing-vibe-types-into-context.md](bringing-vibe-types-into-context.md),
which analyses Claude Code mechanisms. This document evaluates the same goal
using **pi**'s feature set.

## Goal (same as companion doc)

The assistant should **proactively recognise** situations where a compile-time
safety technique from vibe-types applies — even when the developer doesn't know
the technique exists — and either apply it directly or propose it.

---

## Pi Mechanisms Evaluated

### 1. Skills (`SKILL.md` directories)

**How it works:** Directories containing a `SKILL.md` with YAML frontmatter
(`name`, `description`). Pi scans skill locations at startup and includes skill
names and descriptions in the system prompt. The agent loads the full `SKILL.md`
on demand via `read`. Users can also force-load with `/skill:name`.

Skill locations: `~/.pi/agent/skills/`, `.pi/skills/`, `.agents/skills/`,
packages, settings, or `--skill <path>`.

**Verdict: Best primary mechanism for pi.**

- **Progressive disclosure.** Only descriptions are always in context; full
  content loads on demand. This is the closest pi equivalent to the two-layer
  architecture (trigger index + full catalog) recommended for Claude Code.
- **Description as trigger.** The description (up to 1024 chars) can be
  problem-oriented, enabling the agent to recognise when to load the skill
  without the user asking. This is more generous than a CLAUDE.md index line
  but less than full docs.
- **On-demand file loading.** `SKILL.md` can reference catalog and use-case
  files via relative paths. The agent reads only what it needs.
- **Slash commands.** `/skill:vibe-types-rust` gives power users explicit
  access and works even if the agent fails to self-trigger.
- **Portable.** Skills in `~/.pi/agent/skills/` are global; skills in
  `.pi/skills/` are project-scoped. Users can choose.

**Limitation:** The same trigger problem from the companion doc applies — a
short description may not fire on every relevant situation. Mitigated by
writing problem-oriented descriptions (see proposed structure below).

### 2. Prompt Templates (`prompts/*.md`)

**How it works:** Markdown files that expand inline when the user types `/name`.
Support positional arguments. Loaded from `~/.pi/agent/prompts/`,
`.pi/prompts/`, packages, or settings.

**Verdict: Not suitable as primary mechanism.**

- Requires explicit user invocation — fails the proactive-recognition goal.
- No progressive disclosure; the entire template expands into the user's prompt.
- Useful as a convenience shortcut (e.g., `/vibe-types rust newtypes` to ask a
  specific question), but secondary at best.

### 3. MCP Servers

**How it works:** External servers exposing tools via the Model Context Protocol.

**Verdict: Over-engineered.**

- Same reasoning as the companion doc: still requires the agent to know *when*
  to call the tool, adds infrastructure for static markdown files, and does not
  improve trigger recognition.
- Could make sense at scale (hundreds of entries with search/filtering), but not
  today.

### 4. System Prompt / Settings

**How it works:** Pi's `settings.json` supports a `systemPrompt` field and
various context injection points.

**Verdict: Not suitable alone.**

- Injecting all catalog content into every conversation wastes context.
- A compact trigger index *could* be placed here, similar to the CLAUDE.md
  approach. However, pi's skill descriptions already serve this role natively
  and are the idiomatic mechanism.

---

## Recommended Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Layer 1 — Skill Descriptions  (always in system prompt) │
│  Location: ~/.pi/agent/skills/vibe-types-<lang>/         │
│  Size: ~200-500 chars per language                       │
│  Content: problem-oriented summary of available          │
│           techniques for that language                   │
│  Role: lets the agent recognise when to load the skill   │
└────────────────────────┬─────────────────────────────────┘
                         │ agent reads SKILL.md
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 2 — SKILL.md  (loaded on demand)                  │
│  Contains: compact technique index with relative paths   │
│  to full catalog entries                                 │
│  Role: gives the agent a map of what to read next        │
└────────────────────────┬─────────────────────────────────┘
                         │ agent reads specific catalog file
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 3 — Full Catalog Entries  (loaded on demand)      │
│  Location: /path/to/vibe-types/<lang>/catalog/*.md       │
│  Size: ~1-3 pages per entry                              │
│  Role: detailed guidance for applying the technique      │
└──────────────────────────────────────────────────────────┘
```

Three levels of progressive disclosure, all native to pi's skill system.

---

## Proposed Skill Structure

One skill per language, stored globally or symlinked:

```
~/.pi/agent/skills/
├── vibe-types-rust/
│   └── SKILL.md
├── vibe-types-scala3/
│   └── SKILL.md
├── vibe-types-typescript/
│   └── SKILL.md
├── vibe-types-haskell/
│   └── SKILL.md
├── vibe-types-python/
│   └── SKILL.md
├── vibe-types-java/
│   └── SKILL.md
├── vibe-types-ocaml/
│   └── SKILL.md
├── vibe-types-lean/
│   └── SKILL.md
├── vibe-types-agda/
│   └── SKILL.md
└── vibe-types-tlaplus/
    └── SKILL.md
```

### Example: `vibe-types-rust/SKILL.md`

```markdown
---
name: vibe-types-rust
description: >
  Compile-time safety techniques for Rust. Use when writing or reviewing Rust
  code to enforce invariants via the type system: newtypes to prevent mixing up
  same-typed values, phantom types to encode state, typestate to make invalid
  transitions unrepresentable, exhaustive enums, trait bounds, lifetime
  constraints, and Send/Sync for thread safety.
---

# Rust Type System Constraints — vibe-types

When a technique below matches the current task, read the linked catalog entry
before recommending or applying it. Prefer compile-time guarantees over runtime
checks when practical.

## Technique Index

| Technique | Problem it solves | File |
|-----------|-------------------|------|
| Ownership & moves | Use-after-free, double-free | [catalog/01](CATALOG_PATH/rust/catalog/01-ownership.md) |
| Borrowing & lifetimes | Data races, dangling refs | [catalog/02](CATALOG_PATH/rust/catalog/02-borrowing.md) |
| Traits as bounds | Unconstrained generic APIs | [catalog/03](CATALOG_PATH/rust/catalog/03-traits.md) |
| Enums + exhaustive match | Unhandled variants | [catalog/05](CATALOG_PATH/rust/catalog/05-enums.md) |
| Newtypes | Mixing up same-typed values | [catalog/07](CATALOG_PATH/rust/catalog/07-newtype.md) |
| Phantom types | Encoding state in types | [catalog/08](CATALOG_PATH/rust/catalog/08-phantom.md) |
| Typestate pattern | Invalid state transitions | [usecases/UC-01](CATALOG_PATH/rust/usecases/UC-01.md) |
| Send/Sync | Thread-safety enforcement | [catalog/14](CATALOG_PATH/rust/catalog/14-send-sync.md) |

Replace `CATALOG_PATH` with the absolute path to the vibe-types repository
when generating skills.
```

---

## How It Plays Out in Pi

**Scenario:** User writes `fn transfer(from: u64, to: u64, amount: u64)`.

1. Pi's system prompt includes: *"vibe-types-rust — Compile-time safety
   techniques for Rust. Use when writing or reviewing Rust code to enforce
   invariants via the type system: newtypes to prevent mixing up same-typed
   values…"*
2. Agent recognises the match and reads `SKILL.md` via `read`.
3. Agent sees the technique index, identifies "Newtypes: Mixing up same-typed
   values".
4. Agent reads the full catalog entry for newtypes.
5. Agent suggests: *"Consider wrapping these in newtypes — `AccountId(u64)` and
   `Amount(u64)` — so the compiler prevents accidentally swapping arguments."*

**Explicit invocation:** The user can also type `/skill:vibe-types-rust` to
force the full skill into context at any time.

---

## Comparison with Claude Code Approach

| Aspect | Claude Code (CLAUDE.md) | Pi (Skills) |
|--------|------------------------|-------------|
| Trigger mechanism | Index lines in CLAUDE.md | Skill descriptions in system prompt |
| Always-in-context size | ~5-10 lines per language | ~2-3 lines per language (description) |
| On-demand loading | Agent reads files from filesystem | Agent reads SKILL.md, then catalog files |
| Explicit invocation | Custom slash commands | `/skill:vibe-types-<lang>` |
| Progressive disclosure | 2 layers (index → catalog) | 3 layers (description → SKILL.md → catalog) |
| Distribution | Paste snippet into CLAUDE.md | Copy/symlink skill directories |

Pi's three-layer approach is slightly more token-efficient (shorter descriptions
always in context) at the cost of one extra read step.

---

## Open Questions

- **Symlinks vs copies:** Should skills symlink into the vibe-types repo (stays
  in sync, breaks if repo moves) or be generated copies (stable, requires
  regeneration on updates)?
- **Generation script:** A script should generate `SKILL.md` files from catalog
  contents — extracting technique names, problem descriptions, and file paths
  automatically.
- **Description tuning:** The 1024-char description limit is generous. Testing
  is needed to find the right balance between trigger accuracy and context cost
  across 10 languages.
- **Project-scoped skills:** For single-language projects, users may prefer
  `.pi/skills/` with only the relevant language skill to reduce system prompt
  noise.
- **Prompt template complement:** Consider adding a prompt template like
  `/vibe-types $1` for explicit queries (*"What type technique prevents mixing
  up IDs in Rust?"*) as a lightweight alternative to full skill loading.
