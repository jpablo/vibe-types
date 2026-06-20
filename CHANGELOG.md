# Changelog

All notable changes to this guide are documented here.

Format: each entry records the date, the language (if applicable), and what changed.

---

## 2026-06-20 — Documentation correctness pass (pre-launch review)

- Reviewed all five language guides and shared docs for code/advice correctness.
- Fixed verified factual errors, including: inverted monad-transformer state/error
  semantics (Scala `T55`, Lean `T55`); Scala `Float`/`Double` literal types
  (`T52`); opaque-type "no boxing / zero-cost always" overclaims (Scala);
  non-exhaustive `match` described as a compile error rather than a warning
  (Scala); Lean's `Nat.add` "definitionally commutative" claim (`T09`); `<:<`
  variance (`T58`); plus ~25 smaller corrections across Scala, Lean, TypeScript,
  Python, and Rust.
- Rewrote `python/catalog/T61-recursive-types.md`, whose second half had become
  corrupted (leaked editorial text, broken code fences, `any` vs `Any`).
- Fixed broken internal links (98 Scala use-case→catalog links, TypeScript
  cross-references, taxonomy depth) and stale source URLs (Lean reference manual
  links, a PEP 3119 typo).
- Synced stale counts and statuses across `README.md`, the taxonomy matrices, and
  the plugin manifests; TypeScript is now listed as a complete guide (previously
  "Planned"), and wired into the quick-index tooling, the SessionStart hook, the
  install-context command, and `make tenets-check`.

---

## 2026-06-20 — Lean 4 guide + Lean snippet verification

- Added the Lean 4 skill: 48 technique-catalog entries + 18 use-case documents,
  a quick index, and the embedded core tenets.
- Added Lean support to the verify-markdown-snippets skill — each ` ```lean `
  fence is checked with `lake env lean` against the core library (no Mathlib).

---

## 2026-06-19 — TypeScript guide + canonical core tenets

- Added the TypeScript skill: 35 technique-catalog entries + 17 use-case
  documents, a reference `tsconfig` project, and TypeScript support in
  verify-markdown-snippets.
- Added `docs/core-tenets.md` as the canonical, language-agnostic statement of
  the type-safety tenets; embedded an adapted copy in each language skill and
  added `make tenets-check` to keep them in sync.

---

## 2026-06-12 — Scala reference project + Scala snippet verification

- Added `projects/scala-project/` — reference sbt build for strongly typed
  functional Scala 3:
  - sbt 1.12.11 (latest stable), Scala 3.8.4, scalafmt 3.11.1.
  - Strict compiler baseline with rationale comments: `-Wsafe-init`,
    `-Wvalue-discard`, `-Wnonunit-statement`, `-Wunused:all`, `-new-syntax`,
    `-Werror`; optional hardening (`-source:future`, `-language:strictEquality`,
    `-Yexplicit-nulls`) documented but off by default.
  - Library baseline matching the catalog's ecosystem entries: cats-core,
    cats-effect, zio, iron (+ munit for tests).
- Added Scala support to the verify-markdown-snippets skill:
  - New `scripts/verify_scala.py` — compiles each ` ```scala ` fence with
    `scala-cli`, pinned to the Scala version and dependencies parsed from
    `projects/scala-project/build.sbt` (single source of truth), with a
    relaxed doc-friendly flag subset plus `-experimental`.
  - REPL-style snippets with bare top-level statements are auto-retried
    wrapped in an `@main def` stub, diagnostics mapped back to snippet lines.
  - Orchestrator, report renderer, and LLM error-matcher now handle
    `scala` fences; reports for Scala-dominant files land in
    `projects/scala-project/reports/<timestamp>/`.

---

## 2026-03-09 — Python type system constraint guide

- Added complete Python typing guide: 20 catalog entries + 12 use-case entries.
- Feature Catalog (`python/catalog/01` – `20`):
  - Basic annotations & None, Union & Literal, TypedDict, NewType, Enums,
    Dataclasses, Generics & TypeVar, ParamSpec & TypeVarTuple, Protocol,
    ABC, Callable & @overload, Final & ClassVar, TypeGuard & TypeIs,
    Never & NoReturn, Annotated, Self, TypeAlias & `type` statement,
    Generic classes & variance, Unpack & **kwargs, Inference & gradual typing.
- Use-Case Index (`python/usecases/01` – `12`):
  - Preventing invalid states, Domain modeling, Type narrowing & exhaustiveness,
    Generic constraints, Structural contracts, Immutability & finality,
    API contracts & callable typing, Error handling with types,
    Configuration & builder patterns, Typed dictionaries & records,
    Decorator typing, Gradual adoption.
- Each catalog entry follows the 11-section template (what it is, constraint,
  minimal snippet, interactions, gotchas, beginner mental model, two examples,
  common type-checker errors, use-case cross-references, source anchors).
- Each use-case entry follows the 6-section template (constraint, feature
  toolkit, patterns, tradeoffs, when to use which feature, source anchors).
- Added Python 20×12 matrix to `appendix/feature-matrix.md`.
- Added `skills/python.md` — compact trigger index for LLM context integration.
- Updated `python/README.md` as the Python landing page with full tables.

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
- Evaluated mechanisms for bringing vibe-types into LLM context (slash commands,
  skills, MCP servers, CLAUDE.md) and documented the rationale for the chosen
  approach.

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
