# Changelog

All notable changes to this guide are documented here.

Format: each entry records the date, the Scala version (if applicable), and what changed.

---

## 2026-03-06 — Skills: compact trigger indexes for LLM context

- Added `skills/rust.md` and `skills/scala3.md` — compact per-language trigger
  indexes listing each catalog entry and use case as a one-line
  problem-oriented description with a path to the full doc.
- Intended usage: paste into `~/.claude/CLAUDE.md` (or project-level
  `CLAUDE.md`) so the LLM always has the index in context and can proactively
  recognise when a compile-time safety technique applies — even for users who
  don't know the technique exists.
- Architecture: two-layer (trigger index → full catalog entry). No
  intermediate skill/command layer needed; the index is compact enough to serve
  as both trigger and navigation.
- Added `docs/skill-planning/bringing-vibe-types-into-context.md` documenting
  the evaluation of mechanisms (slash commands, skills, MCP servers, CLAUDE.md)
  and rationale for the chosen approach.

---

## 2026-02-24 — Rust catalog teaching expansion

- Expanded all Rust catalog entries (`rust/catalog/01-ownership-moves.md` through `rust/catalog/14-trait-solver-param-env.md`) to be more beginner-friendly.
- Added per-feature teaching sections:
  - beginner mental model,
  - two practical examples,
  - common compiler errors and how to read them.
- Updated `rust/catalog/00-overview.md` with richer beginner reading guidance and updated document structure conventions.
- Updated `rust/README.md` to advertise the new catalog teaching format.
- Normalized examples and formatting for consistency (including compile-fail annotations where appropriate).

---

## 2026-02-24 — Rust guide scaffold and first pass

- Added Rust landing page index with catalog and use-case tables
- Added Rust feature catalog docs:
  - `rust/catalog/00-overview.md`
  - `rust/catalog/01-ownership-moves.md` through `rust/catalog/14-trait-solver-param-env.md`
- Added Rust use-case docs:
  - `rust/usecases/00-overview.md`
  - `rust/usecases/01-preventing-invalid-states.md` through `rust/usecases/08-value-level-invariants-with-types.md`
- Added source analysis and planning artifacts under `rust/analysis/`
- Added Rust input source list in `rust/inputs.md`
- Enriched all Rust catalog and use-case docs with:
  - stronger constraint wording,
  - minimal patterns/snippets,
  - gotchas/limitations,
  - source anchors.

---

## 2026-02-13 — Multi-language restructure

- Renamed project from `scala3-type-guide` to `vibe-types`
- Moved Scala 3 content into `scala3/` subdirectory (`catalog/`, `usecases/`)
- Created `scala3/README.md` as the Scala 3 landing page
- Rewrote root `README.md` as a multi-language hub
- Added placeholder directories for TypeScript, Rust, Python, Haskell, and Lean
- Fixed internal links after directory restructure

---

## 2026-02-08 — Initial release

- Created complete guide with 44 documents
- Feature Catalog: 23 documents covering all Scala 3 type system features
- Use-Case Index: 15 documents mapping constraints to features
- Appendix: glossary (40+ terms), feature matrix (23×15), further reading
- Added Scala version annotations to all catalog documents

### Version coverage

Features documented as of this release:

| Scala Version | Features |
|---------------|----------|
| 3.0 | Union/intersection types, type lambdas, match types, dependent/polymorphic function types, givens/using, context functions/bounds, extension methods, type class derivation, multiversal equality, conversions, enums/ADTs/GADTs, opaque types, open/export/transparent, matchable/TypeTest, structural/refined types, kind polymorphism, inline/compiletime, macros, explicit nulls (experimental), erased definitions (experimental) |
| 3.2 | Capture checking (experimental) |
| 3.4 | `open` class warning becomes default |
| 3.5 | Given disambiguation rule 9 (most-general preference) |
| 3.6 | New given syntax (`[T] => ...`), named context bounds (`as`), aggregate bounds (`{Ord, Show}`), context bounds on type members and polymorphic functions, deferred givens |
| 3.7 | Named tuples |
| 3.8 | `into` type (preview) |

### Experimental / research features

- Explicit nulls — experimental since 3.0
- Erased definitions — experimental since 3.0
- Capture checking — experimental research project since 3.2
- Named type arguments — experimental since 3.0
- Modularity (`tracked`, applied constructor types) — experimental
