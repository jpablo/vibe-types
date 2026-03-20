# Feature Catalog — Reading Guide

## Purpose

Part I of this guide is the **Feature Catalog**: one document per Lean 4 type-system feature (or feature cluster). Each document answers:

> *Given this feature, what constraints can the Lean compiler enforce?*

Lean 4 is built on the Calculus of Inductive Constructions — a dependent type theory that doubles as a theorem prover. This catalog focuses on the **programming** side: using types to prevent bugs. Each entry includes a brief "Proof perspective" subsection for readers curious about the mathematical angle.

## Document Structure Convention

Every catalog document follows this template:

1. **What it is** — one-paragraph definition of the feature.
2. **What constraint it enforces** — the key compile-time guarantee in bold.
3. **Minimal snippet** — shortest possible Lean snippet showing the guarantee.
4. **Interaction with other features** — how it composes with other catalog entries.
5. **Gotchas and limitations** — common pitfalls, caveats, Mathlib boundary.
6. **Beginner mental model** — intuitive framing for programmers from other languages.
7. **Example A / Example B** — practical snippets that show real usage shape.
8. **Common compiler errors and how to read them** — map common Lean error messages to fixes.
9. **Proof perspective (brief)** — what this feature means in the theorem-proving world.
10. **Use-case cross-references** — links to relevant `UC-nn` documents.
11. **Source anchors** — where the guidance comes from.

## How to Read

- If you already know the feature: read sections 2 and 6 first.
- If you are exploring: read sections 1 and 3 first.
- If you are combining features: focus on section 4.
- If you come from a proof background: start with section 9.

## Beginner Reading Guidance

- **Start with inductive types:** pick [catalog/01](01-inductive-types.md) and read sections 1–3 to see how Lean models data with exhaustive matching.
- **Pair with `#check` and `#eval`:** paste minimal snippets into a Lean file or the web editor; use `#check` to inspect types and `#eval` to run expressions.
- **Use cross-references as study links:** when one feature links to another (`[→ catalog/06]`, `[→ UC-05]`), treat them as "learn next" targets rather than reading the whole catalog in order.
- **Don't panic about proofs:** most catalog entries work without Mathlib. Entries that require Mathlib are marked with `> **Status:** Requires Mathlib`.

## Numbering

Catalog documents are numbered `01` through `16` for stable cross-referencing:

- `01-inductive-types.md`
- `02-dependent-types.md`
- `03-structures-inheritance.md`
- `04-type-classes-instances.md`
- `05-universes-polymorphism.md`
- `06-propositions-as-types.md`
- `07-termination-checking.md`
- `08-totality-partial.md`
- `09-monads-do-io.md`
- `10-coercions-coe.md`
- `11-auto-bound-implicits.md`
- `12-macros-elaboration.md`
- `13-proof-automation.md`
- `14-subtypes-refinements.md`
- `15-opaque-definitions.md`
- `16-notation-attributes.md`

## Snippet Style

- Keep snippets minimal and focused on one compile-time property.
- Mark rejected lines with `-- error`.
- Mark accepted lines with `-- OK`.
- Prefer examples that isolate type constraints, not runtime behavior.
- Include the version/dependency requirement when a feature needs Mathlib.

## Version and Dependency Annotations

- `> **Since:** Lean 4 (stable)` — feature available in core Lean 4.
- `> **Status:** Requires Mathlib` — feature depends on the Mathlib4 library.
