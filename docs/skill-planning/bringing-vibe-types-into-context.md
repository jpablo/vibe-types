# Bringing vibe-types Into LLM Context

## Goal

When a developer uses an LLM coding assistant (Claude Code, etc.), the assistant
should **proactively recognise** situations where a compile-time safety technique
from vibe-types applies — even when the developer doesn't know the technique
exists — and either apply it directly or propose it for consideration.

This rules out mechanisms that require the user to invoke something explicitly
(slash commands, skills invoked by name) because the whole point is to help
people who don't yet know what to ask for.

---

## Mechanisms Evaluated

### 1. Custom Slash Commands (`~/.claude/commands/`)

**How it works:** Markdown files that expand into prompts when the user types
`/user:command-name`. Support `$ARGUMENTS` for parameterised queries.

**Verdict: Not suitable as primary mechanism.**

- Requires the user to know the command exists and invoke it.
- A user who doesn't know about phantom types will never type
  `/user:rust-types phantom types`.
- Useful as a secondary, explicit-loading mechanism for power users.

### 2. Skills

**How it works:** Enhanced custom commands whose descriptions appear in the
system reminder. The LLM sees the description and can invoke the skill when it
matches.

**Verdict: Helpful as a second stage, but insufficient alone.**

- The description acts as a trigger, but it is limited to ~1-2 lines.
- A short description like *"Use when designing types in Rust"* is too vague to
  fire on specific situations (e.g. two `u64` parameters that should be
  distinct types).
- The LLM needs to see **which techniques exist and what problems they solve**
  to recognise opportunities. A skill description cannot carry that level of
  detail.
- Skills work well as a loading mechanism once the LLM has already decided a
  technique is relevant.

### 3. MCP Server

**How it works:** A custom server exposing tools like
`lookup_type_feature(lang, feature)` or `search_type_catalog(lang, query)`.

**Verdict: Over-engineered for this content.**

- Still requires the LLM to know *when* to call the tool, which brings us back
  to the trigger problem.
- Adds infrastructure (build, deploy, maintain a server) for ~87 static
  markdown files.
- Could make sense if the corpus grows to hundreds of entries and needs
  search/filtering, but not today.

### 4. Full Docs Always in Context

**How it works:** Load all catalog and use-case files into every conversation.

**Verdict: Not feasible.**

- ~87 files across two languages (growing) would consume a large portion of
  the context window in every session, most of it irrelevant.

### 5. CLAUDE.md with Compact Trigger Index (Recommended)

**How it works:** A concise index (~5-10 lines per language) lives in
`~/.claude/CLAUDE.md` (or a project-level CLAUDE.md). Each line names a
technique and describes the **problem it solves** in plain terms. The LLM sees
this index in every conversation. When it recognises a match, it reads the full
catalog entry from the filesystem before recommending or applying the technique.

**Verdict: Best fit for proactive behaviour.**

- Always in context — no user action required.
- Minimal token cost (~30-50 lines total across languages).
- Problem-oriented descriptions enable pattern matching against user code:
  the LLM can connect "two `u64` parameters" → "newtypes prevent mixups".
- Full docs are loaded on demand, only when a specific technique is relevant.
- Works for users who don't know the techniques exist.

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────┐
│  Layer 1 — Trigger Index  (always in context)       │
│  Location: ~/.claude/CLAUDE.md or project CLAUDE.md │
│  Size: ~5-10 lines per language                     │
│  Content: technique → problem it solves → file path │
│  Role: lets the LLM recognise when to act           │
└──────────────────────┬──────────────────────────────┘
                       │ LLM reads file when triggered
                       ▼
┌─────────────────────────────────────────────────────┐
│  Layer 2 — Full Catalog Entries  (on demand)        │
│  Location: /path/to/vibe-types/<lang>/catalog/*.md  │
│  Size: ~1-3 pages per entry                         │
│  Content: definition, examples, gotchas, cross-refs │
│  Role: gives the LLM enough detail to apply or      │
│        propose the technique correctly               │
└─────────────────────────────────────────────────────┘
```

### Optional additions

- **Skills** can complement the index for explicit invocation
  (e.g. `/user:rust-types` to bulk-load a language's full catalog).
- **Project-level CLAUDE.md** can narrow the index to the language(s) relevant
  to a specific codebase, reducing noise.

---

## Example Trigger Index (for CLAUDE.md)

```markdown
## Compile-Time Safety Techniques (vibe-types)

When writing or reviewing code in these languages, consider the techniques
below. When one applies, read the full entry from
/Users/jpablo/GitHub/vibe-types/<lang>/catalog/ before recommending.
Prefer compile-time guarantees over runtime checks when practical.

### Rust
- Ownership & moves: prevent use-after-free, double-free [catalog/01]
- Borrowing & lifetimes: prevent data races, dangling references [catalog/02]
- Traits as bounds: constrain generic APIs to required capabilities [catalog/03]
- Enums + exhaustive match: force handling of all variants [catalog/05]
- Newtypes: prevent mixing up same-typed values (UserId vs OrderId) [catalog/07]
- Phantom types: encode state in types (HttpRequest<Unsent> vs <Sent>) [catalog/08]
- Typestate pattern: make invalid state transitions unrepresentable [UC-01]
- Send/Sync: enforce thread-safety properties at compile time [catalog/14]

### Scala 3
- Opaque types: zero-cost type distinctions [catalog/01]
- Union types: type-safe alternatives without class hierarchies [catalog/03]
- Match types: compute types from other types [catalog/05]
- Inline + compiletime: move checks to compile time [catalog/09]
- Given/using: enforce capability requirements implicitly [catalog/13]
```

---

## How It Plays Out in Practice

**Scenario:** User writes `fn transfer(from: u64, to: u64, amount: u64)`.

1. LLM sees the trigger index (always in context).
2. Matches: *"Newtypes: prevent mixing up same-typed values (UserId vs OrderId)"*.
3. Reads `/path/to/vibe-types/rust/catalog/07-newtype-pattern.md`.
4. Suggests: *"Consider wrapping these in newtypes — `AccountId(u64)` and
   `Amount(u64)` — so the compiler prevents accidentally passing an amount
   where an account ID is expected."*

The user didn't ask for this. They didn't know newtypes were an option. The
trigger index made it possible.

---

## Open Questions

- **Per-project vs global index:** Should users copy the index into each
  project's CLAUDE.md (filtered to the relevant language), or keep one global
  index?
- **Distribution:** How should vibe-types ship the index? A ready-to-paste
  snippet in the README? A setup script?
- **Index maintenance:** As new catalog entries are added, the index must be
  updated. Automate this with a script that generates the index from catalog
  file headers?
- **Multiple assistants:** This analysis focuses on Claude Code. Other tools
  (Cursor, Copilot, Windsurf) have different context mechanisms — document
  the equivalent approach for each.
