# Lean 4 Type System Constraint Guide

> Status: **In Progress** — 16 feature catalog entries, 10 use-case documents.

Lean 4 is both a programming language and a theorem prover built on dependent type theory (Calculus of Inductive Constructions). This guide focuses on the **programming** side — using Lean's type system to prevent bugs at compile time. Each catalog entry includes a "Proof perspective" subsection for readers curious about the mathematical angle.

---

## How to Use This Guide

| Goal | Start here |
|------|-----------|
| Learn what a specific feature enforces | [Part I: Feature Catalog](#part-i-feature-catalog) |
| Find which features solve a specific problem | [Part II: Use-Case Index](#part-ii-use-case-index) |
| See which features cover which problems | [Techniques](../../../taxonomy/techniques.md) |

### Cross-Reference Notation

- `[→ catalog/nn]` links to a catalog entry.
- `[→ UC-nn]` links to a use-case entry.
- `-- error` / `-- OK` mark rejected/accepted lines in Lean snippets.

### Version and Dependency Annotations

- `> **Since:** Lean 4 (stable)` — available in core Lean 4.
- `> **Status:** Requires Mathlib` — depends on the Mathlib4 library.

---

## Part I: Feature Catalog

| # | Document | Feature | Key Constraint |
|---|----------|---------|----------------|
| 00 | [Reading Guide](catalog/00-overview.md) | Overview | — |
| 01 | [Inductive Types](catalog/T01-algebraic-data-types.md) | Inductive Types and Pattern Matching | Closed type hierarchies with exhaustive matching; compiler rejects incomplete matches |
| 02 | [Dependent Types](catalog/T09-dependent-types.md) | Dependent Types and Pi Types | Return/field types depend on values; compiler checks index consistency |
| 03 | [Structures](catalog/T31-record-types.md) | Structures, Inheritance, Anonymous Constructors | Named-field product types with single-constructor guarantees; `extends` for inheritance |
| 04 | [Type Classes](catalog/T05-type-classes.md) | Type Classes and Instance Resolution | Constrain generic functions to types with required capabilities |
| 05 | [Universes](catalog/T35-universes-kinds.md) | Universes and Universe Polymorphism | Prevent type-in-type paradoxes; `Sort u`, `Type u`, `Prop` |
| 06 | [Propositions as Types](catalog/T29-propositions-as-types.md) | Propositions as Types (Prop and Proof Terms) | Encode invariants as `Prop`; compiler requires proof terms as evidence |
| 07 | [Termination](catalog/T28-termination.md) | Termination and Well-Founded Recursion | Every recursive function must terminate; structural recursion or `termination_by` proof |
| 08 | [Totality](catalog/T51-totality.md) | Totality, Partial Functions, and `partial` | Functions must handle all inputs; `partial` opts out but taints the result |
| 09 | [Monads & IO](catalog/T12-effect-tracking.md) | Monads, Do-Notation, and the IO Type | Side effects tracked via monadic types; `IO` demarcates impure computation |
| 10 | [Coercions](catalog/T18-conversions-coercions.md) | Coercions and Coe | Automatic safe conversions between types; compiler inserts coercions where declared |
| 11 | [Implicits](catalog/T38-implicits-auto-bound.md) | Auto-Bound Implicit and Instance Arguments | Compiler infers implicit arguments; `[inst : C a]` constrains to types with evidence |
| 12 | [Macros](catalog/T17-macros-metaprogramming.md) | Macros, Elaboration, and Syntax Extensions | Compile-time metaprogramming via `syntax`, `macro_rules`, and `elab` |
| 13 | [Proof Automation](catalog/T30-proof-automation.md) | Simp, Decide, Omega — Proof Automation | Automate proof obligations; state what must hold, let tactics verify it |
| 14 | [Subtypes](catalog/T26-refinement-types.md) | Subtypes and Refinement Types | Attach predicates to types (`{ n : Nat // n > 0 }`); construction requires proof |
| 15 | [Opaque Defs](catalog/T21-encapsulation.md) | Opaque Definitions and Reducibility | `opaque def` prevents unfolding outside the module; definitional encapsulation |
| 16 | [Notation](catalog/T39-notation-attributes.md) | Notation, Attributes, and Compiler Options | `@[simp]`, `@[inline]`, `@[reducible]` control how the checker treats definitions |

---

## Part II: Use-Case Index

| # | Document | Constraint |
|---|----------|-----------|
| 00 | [Navigation Guide](usecases/00-overview.md) | Overview |
| 01 | [Preventing Invalid States](usecases/UC01-invalid-states.md) | Make illegal states unrepresentable at compile time |
| 02 | [Domain Modeling](usecases/UC02-domain-modeling.md) | Model domain invariants as type-level constraints the compiler enforces |
| 03 | [Totality & Exhaustiveness](usecases/UC03-exhaustiveness.md) | Every function handles all inputs; no unmatched cases |
| 04 | [Compile-Time Invariants](usecases/UC12-compile-time.md) | Attach invariants to data; compiler verifies them via proofs |
| 05 | [Safe Effectful Programming](usecases/UC11-effect-tracking.md) | Track side effects via IO and monads; prevent untracked mutation |
| 06 | [Generic Programming](usecases/UC04-generic-constraints.md) | Constrain generic code to types with required capabilities |
| 07 | [Safe Recursion](usecases/UC24-termination.md) | All recursion terminates; structural or well-founded proof |
| 08 | [Encapsulation](usecases/UC10-encapsulation.md) | Control what leaks across module boundaries |
| 09 | [Metaprogramming](usecases/UC25-metaprogramming.md) | Extend the language safely at compile time |
| 10 | [Escape Hatches](usecases/UC26-escape-hatches.md) | `sorry`, `partial`, `unsafe`, FFI — opt out with known boundaries |

---

## Cross-References

- [Glossary](../../../appendix/glossary.md)
- [Techniques](../../../taxonomy/techniques.md)
- [Further Reading](../../../appendix/further-reading.md)
- [Source Material](../../../taxonomy/sources.md#lean-4)
