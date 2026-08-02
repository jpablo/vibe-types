# Feature Catalog — Reading Guide

## Purpose

Part I of this guide is the **Feature Catalog**: one document per Lean 4 type-system feature (or feature cluster). Each document answers:

> *Given this feature, what constraints can the Lean compiler enforce?*

Lean 4 is built on the Calculus of Inductive Constructions — a dependent type theory that doubles as a theorem prover. This catalog focuses on the **programming** side: using types to prevent bugs. The sixteen **core entries** (marked ★ under [Numbering](#numbering)) also carry a brief "Proof perspective" subsection for readers curious about the mathematical angle; the remaining entries do not.

## Document Structure Convention

Every catalog document follows this template. Sections 1–7, 10 and 11 are present in every entry; sections 8 and 9 are **optional** and appear only in the sixteen core entries marked ★ under [Numbering](#numbering).

1. **What it is** — one-paragraph definition of the feature.
2. **What constraint it enforces** — the key compile-time guarantee in bold.
3. **Minimal snippet** — shortest possible Lean snippet showing the guarantee.
4. **Interaction with other features** — how it composes with other catalog entries.
5. **Gotchas and limitations** — common pitfalls, caveats, Mathlib boundary.
6. **Beginner mental model** — intuitive framing for programmers from other languages.
7. **Example A / Example B** — practical snippets that show real usage shape.
8. **Common compiler errors and how to read them** *(optional; core entries only)* — map common Lean error messages to fixes.
9. **Proof perspective (brief)** *(optional; core entries only)* — what this feature means in the theorem-proving world.
10. **Use-case cross-references** — links to relevant `UC-nn` documents.
11. **Source anchors** — where the guidance comes from.

## How to Read

- If you already know the feature: read sections 2 and 6 first.
- If you are exploring: read sections 1 and 3 first.
- If you are combining features: focus on section 4.
- If you come from a proof background: start with section 9 — but note it exists only in the sixteen core entries (★).

## Beginner Reading Guidance

- **Start with inductive types:** pick [catalog/T01](T01-algebraic-data-types.md) and read sections 1–3 to see how Lean models data with exhaustive matching.
- **Pair with `#check` and `#eval`:** paste minimal snippets into a Lean file or the web editor; use `#check` to inspect types and `#eval` to run expressions.
- **Use cross-references as study links:** when one feature links to another (`[→ T29](T29-propositions-as-types.md)`, `[→ UC-13]`), treat them as "learn next" targets rather than reading the whole catalog in order. Use-case ids are also sparse — `UC01`–`UC24` with gaps.
- **Don't panic about proofs:** most catalog entries work without Mathlib. Where a feature (or part of one) needs Mathlib, the entry says so inline on its `Since:` line — see [T30](T30-proof-automation.md), whose header reads:

  > **Since:** Lean 4 (stable) | Some `simp` lemmas: **Requires Mathlib**

  Mathlib dependence is partial in every current entry, so no document carries a whole-document Mathlib banner.

## Numbering

Catalog documents carry a stable `Tnn` id used for cross-referencing. The
numbering runs `T01`–`T61` and is **sparse** — ids are permanent handles, not a
dense sequence, and the gaps (`T07`–`T08`, `T10`–`T11`, `T24`, `T43`–`T48`,
`T50`, `T60`) are simply unused. 48 entries exist today.

Entries marked ★ are the sixteen **core entries**: they follow the full
template including the optional sections 8 (Common compiler errors) and 9
(Proof perspective). All other entries omit those two sections.

| Id | File | Title |
|----|------|-------|
| ★ T01 | `T01-algebraic-data-types.md` | Inductive Types and Pattern Matching |
| T02 | `T02-union-intersection.md` | Union & Intersection Types (via Inductive Types and Type Classes) |
| T03 | `T03-newtypes-opaque.md` | Newtypes, Abbrev, and Opaque Wrappers |
| T04 | `T04-generics-bounds.md` | Generics & Bounded Polymorphism (via Type Classes and Universes) |
| ★ T05 | `T05-type-classes.md` | Type Classes and Instance Resolution |
| T06 | `T06-derivation.md` | Type-Class Derivation (Limited Built-in Support) |
| ★ T09 | `T09-dependent-types.md` | Dependent Types and Pi Types |
| ★ T12 | `T12-effect-tracking.md` | Monads, Do-Notation, and the IO Type |
| T13 | `T13-null-safety.md` | Null Safety — Option and the Absence of Null |
| T14 | `T14-type-narrowing.md` | Type Narrowing via Dependent Pattern Matching |
| T15 | `T15-const-generics.md` | Const Generics (Subsumed by Dependent Types) |
| T16 | `T16-compile-time-ops.md` | Compile-Time Computation |
| ★ T17 | `T17-macros-metaprogramming.md` | Macros, Elaboration, and Syntax Extensions |
| ★ T18 | `T18-conversions-coercions.md` | Coercions and Coe |
| T19 | `T19-extension-methods.md` | Extension Methods (Not a First-Class Feature) |
| T20 | `T20-equality-safety.md` | Equality Safety — BEq, DecidableEq, and Propositional Equality |
| ★ T21 | `T21-encapsulation.md` | Opaque Definitions and Reducibility |
| T22 | `T22-callable-typing.md` | Callable Typing — First-Class and Dependent Functions |
| T23 | `T23-type-aliases.md` | Type Aliases — Abbrev, Def, and Reducibility |
| T25 | `T25-coherence-orphan.md` | Coherence & Instance Resolution (via Scoping Rules) |
| ★ T26 | `T26-refinement-types.md` | Subtypes and Refinement Types |
| T27 | `T27-erased-phantom.md` | Erased and Phantom Types — Prop, Proof Erasure, and Subsingleton |
| ★ T28 | `T28-termination.md` | Termination and Well-Founded Recursion |
| ★ T29 | `T29-propositions-as-types.md` | Propositions as Types (Prop and Proof Terms) |
| ★ T30 | `T30-proof-automation.md` | Simp, Decide, Omega — Proof Automation |
| ★ T31 | `T31-record-types.md` | Structures, Inheritance, and Anonymous Constructors |
| T32 | `T32-immutability-markers.md` | Immutability by Default |
| T33 | `T33-self-type.md` | Self Type (via Dependent Types) |
| T34 | `T34-never-bottom.md` | Never / Bottom — Empty, False, and Absurd |
| ★ T35 | `T35-universes-kinds.md` | Universes and Universe Polymorphism |
| T36 | `T36-trait-objects.md` | Runtime Polymorphism (via Coercions and Type Classes) |
| T37 | `T37-trait-solver.md` | Instance Resolution (Lean's Trait Solver) |
| ★ T38 | `T38-implicits-auto-bound.md` | Auto-Bound Implicit and Instance Arguments |
| ★ T39 | `T39-notation-attributes.md` | Notation, Attributes, and Compiler Options |
| T40 | `T40-type-lambdas.md` | Type-Level Functions and Universe Polymorphism |
| T41 | `T41-match-types.md` | Match Types — Dependent Pattern Matching at the Type Level |
| T42 | `T42-context-functions.md` | Context Functions (via Instance Arguments) |
| T49 | `T49-associated-types.md` | Associated Types (via Structure Fields) |
| ★ T51 | `T51-totality.md` | Totality, Partial Functions, and `partial` |
| T52 | `T52-literal-types.md` | Literal Types (Subsumed by Dependent Types) |
| T53 | `T53-path-dependent-types.md` | Path-Dependent Types (Subsumed by Dependent Types) |
| T54 | `T54-functor-applicative-monad.md` | Functor, Applicative, and Monad |
| T55 | `T55-monad-transformers.md` | Monad Transformers |
| T56 | `T56-tagless-final.md` | Tagless Final (via Type Class Abstraction) |
| T57 | `T57-typestate.md` | Typestate |
| T58 | `T58-witness-evidence.md` | Witness and Evidence Types |
| T59 | `T59-existential-types.md` | Existential Types |
| T61 | `T61-recursive-types.md` | Recursive Types |

## Snippet Style

- Keep snippets minimal and focused on one compile-time property.
- Mark rejected lines with `-- error`.
- Mark accepted lines with `-- OK`.
- Prefer examples that isolate type constraints, not runtime behavior.
- Include the version/dependency requirement when a feature needs Mathlib.

## Version and Dependency Annotations

Every entry opens with a single `Since:` blockquote directly under its title.
Mathlib dependence is recorded **inline on that same line**, appended after a
`|` separator — there is no separate `Status:` line.

- `> **Since:** Lean 4 (stable)` — feature available in core Lean 4 (the common case).
- `> **Since:** Lean 4 (stable); indexed inductive types since Lean 4.0` — extra version detail after a `;`.
- ``> **Since:** Lean 4 (stable) | Some `simp` lemmas: **Requires Mathlib**`` — the [T30](T30-proof-automation.md) form: core feature, with a named part that depends on Mathlib4.

Scope the Mathlib note to what actually needs it. Only promote it to cover the
whole entry (`> **Since:** **Requires Mathlib**`) if the feature is unavailable
in core at all — no current entry is.
