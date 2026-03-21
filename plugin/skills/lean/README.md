# Lean 4 Type System Constraint Guide

> Status: **In Progress** — 16 feature catalog entries, 10 use-case documents.

Lean 4 is both a programming language and a theorem prover built on dependent type theory (Calculus of Inductive Constructions). This guide focuses on the **programming** side — using Lean's type system to prevent bugs at compile time. Each catalog entry includes a "Proof perspective" subsection for readers curious about the mathematical angle.

---

## How to Use This Guide

| Goal | Start here |
|------|-----------|
| Learn what a specific feature enforces | [Part I: Feature Catalog](#part-i-feature-catalog) |
| Find which features solve a specific problem | [Part II: Use-Case Index](#part-ii-use-case-index) |
| See which features cover which problems | [Feature Matrix](../../../appendix/feature-matrix.md) (Lean section) |

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
| 01 | [Inductive Types](catalog/01-inductive-types.md) | Inductive Types and Pattern Matching | Closed type hierarchies with exhaustive matching; compiler rejects incomplete matches |
| 02 | [Dependent Types](catalog/02-dependent-types.md) | Dependent Types and Pi Types | Return/field types depend on values; compiler checks index consistency |
| 03 | [Structures](catalog/03-structures-inheritance.md) | Structures, Inheritance, Anonymous Constructors | Named-field product types with single-constructor guarantees; `extends` for inheritance |
| 04 | [Type Classes](catalog/04-type-classes-instances.md) | Type Classes and Instance Resolution | Constrain generic functions to types with required capabilities |
| 05 | [Universes](catalog/05-universes-polymorphism.md) | Universes and Universe Polymorphism | Prevent type-in-type paradoxes; `Sort u`, `Type u`, `Prop` |
| 06 | [Propositions as Types](catalog/06-propositions-as-types.md) | Propositions as Types (Prop and Proof Terms) | Encode invariants as `Prop`; compiler requires proof terms as evidence |
| 07 | [Termination](catalog/07-termination-checking.md) | Termination and Well-Founded Recursion | Every recursive function must terminate; structural recursion or `termination_by` proof |
| 08 | [Totality](catalog/08-totality-partial.md) | Totality, Partial Functions, and `partial` | Functions must handle all inputs; `partial` opts out but taints the result |
| 09 | [Monads & IO](catalog/09-monads-do-io.md) | Monads, Do-Notation, and the IO Type | Side effects tracked via monadic types; `IO` demarcates impure computation |
| 10 | [Coercions](catalog/10-coercions-coe.md) | Coercions and Coe | Automatic safe conversions between types; compiler inserts coercions where declared |
| 11 | [Implicits](catalog/11-auto-bound-implicits.md) | Auto-Bound Implicit and Instance Arguments | Compiler infers implicit arguments; `[inst : C a]` constrains to types with evidence |
| 12 | [Macros](catalog/12-macros-elaboration.md) | Macros, Elaboration, and Syntax Extensions | Compile-time metaprogramming via `syntax`, `macro_rules`, and `elab` |
| 13 | [Proof Automation](catalog/13-proof-automation.md) | Simp, Decide, Omega — Proof Automation | Automate proof obligations; state what must hold, let tactics verify it |
| 14 | [Subtypes](catalog/14-subtypes-refinements.md) | Subtypes and Refinement Types | Attach predicates to types (`{ n : Nat // n > 0 }`); construction requires proof |
| 15 | [Opaque Defs](catalog/15-opaque-definitions.md) | Opaque Definitions and Reducibility | `opaque def` prevents unfolding outside the module; definitional encapsulation |
| 16 | [Notation](catalog/16-notation-attributes.md) | Notation, Attributes, and Compiler Options | `@[simp]`, `@[inline]`, `@[reducible]` control how the checker treats definitions |

---

## Part II: Use-Case Index

| # | Document | Constraint |
|---|----------|-----------|
| 00 | [Navigation Guide](usecases/00-overview.md) | Overview |
| 01 | [Preventing Invalid States](usecases/01-preventing-invalid-states.md) | Make illegal states unrepresentable at compile time |
| 02 | [Domain Modeling](usecases/02-domain-modeling-dependent-types.md) | Model domain invariants as type-level constraints the compiler enforces |
| 03 | [Totality & Exhaustiveness](usecases/03-totality-exhaustiveness.md) | Every function handles all inputs; no unmatched cases |
| 04 | [Compile-Time Invariants](usecases/04-compile-time-invariants.md) | Attach invariants to data; compiler verifies them via proofs |
| 05 | [Safe Effectful Programming](usecases/05-safe-effectful-programming.md) | Track side effects via IO and monads; prevent untracked mutation |
| 06 | [Generic Programming](usecases/06-generic-programming-type-classes.md) | Constrain generic code to types with required capabilities |
| 07 | [Safe Recursion](usecases/07-safe-recursion-termination.md) | All recursion terminates; structural or well-founded proof |
| 08 | [Encapsulation](usecases/08-encapsulation-module-boundaries.md) | Control what leaks across module boundaries |
| 09 | [Metaprogramming](usecases/09-metaprogramming-syntax-extension.md) | Extend the language safely at compile time |
| 10 | [Escape Hatches](usecases/10-interop-escape-hatches.md) | `sorry`, `partial`, `unsafe`, FFI — opt out with known boundaries |

---

## Cross-References

- [Glossary](../../../appendix/glossary.md)
- [Feature Matrix](../../../appendix/feature-matrix.md) (Lean section)
- [Further Reading](../../../appendix/further-reading.md)
- [Source Material](inputs.md)
