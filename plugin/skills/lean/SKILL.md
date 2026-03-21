---
description: Lean 4 compile-time safety techniques — dependent types, inductive types, type classes, termination checking, propositions as types, proof automation. Use when writing safe Lean 4, choosing type system features, or debugging compiler errors.
version: 1.0.0
---

# Lean 4 — Compile-Time Safety Techniques

> **Base path:** `${CLAUDE_PLUGIN_ROOT}/skills/lean`

## Full catalog (type system features → constraints they enforce)

- **Inductive types & pattern matching** — closed type hierarchies with exhaustive matching; compiler rejects incomplete matches → `catalog/01-inductive-types.md`
- **Dependent types & Pi types** — return/field types depend on values; compiler checks index consistency → `catalog/02-dependent-types.md`
- **Structures, inheritance, constructors** — named-field product types with single-constructor guarantees; `extends` for inheritance → `catalog/03-structures-inheritance.md`
- **Type classes & instance resolution** — constrain generic functions to types with required capabilities → `catalog/04-type-classes-instances.md`
- **Universes & universe polymorphism** — prevent type-in-type paradoxes; `Sort u`, `Type u`, `Prop` → `catalog/05-universes-polymorphism.md`
- **Propositions as types (Prop)** — encode invariants as `Prop`; compiler requires proof terms as evidence → `catalog/06-propositions-as-types.md`
- **Termination & well-founded recursion** — every recursive function must terminate; structural recursion or `termination_by` proof → `catalog/07-termination-checking.md`
- **Totality, partial functions** — functions must handle all inputs; `partial` opts out but taints the result → `catalog/08-totality-partial.md`
- **Monads, do-notation, IO** — side effects tracked via monadic types; `IO` demarcates impure computation → `catalog/09-monads-do-io.md`
- **Coercions & Coe** — automatic safe conversions between types; compiler inserts coercions where declared → `catalog/10-coercions-coe.md`
- **Auto-bound implicits & instances** — compiler infers implicit arguments; `[inst : C a]` constrains to types with evidence → `catalog/11-auto-bound-implicits.md`
- **Macros, elaboration, syntax** — compile-time metaprogramming via `syntax`, `macro_rules`, and `elab` → `catalog/12-macros-elaboration.md`
- **Proof automation (simp, decide, omega)** — automate proof obligations; state what must hold, let tactics verify it → `catalog/13-proof-automation.md`
- **Subtypes & refinement types** — attach predicates to types (`{ n : Nat // n > 0 }`); construction requires proof → `catalog/14-subtypes-refinements.md`
- **Opaque definitions & reducibility** — `opaque def` prevents unfolding outside the module; definitional encapsulation → `catalog/15-opaque-definitions.md`
- **Notation, attributes, options** — `@[simp]`, `@[inline]`, `@[reducible]` control how the checker treats definitions → `catalog/16-notation-attributes.md`

## Use cases (problem → which features help)

- **Preventing invalid states** — make illegal states unrepresentable at compile time (inductive types, subtypes, dependent types) → `usecases/01-preventing-invalid-states.md`
- **Domain modeling with dependent types** — model domain invariants as type-level constraints the compiler enforces → `usecases/02-domain-modeling-dependent-types.md`
- **Totality & exhaustiveness** — every function handles all inputs; no unmatched cases → `usecases/03-totality-exhaustiveness.md`
- **Compile-time invariants** — attach invariants to data; compiler verifies them via proofs → `usecases/04-compile-time-invariants.md`
- **Safe effectful programming** — track side effects via IO and monads; prevent untracked mutation → `usecases/05-safe-effectful-programming.md`
- **Generic programming with type classes** — constrain generic code to types with required capabilities → `usecases/06-generic-programming-type-classes.md`
- **Safe recursion & termination** — all recursion terminates; structural or well-founded proof → `usecases/07-safe-recursion-termination.md`
- **Encapsulation & module boundaries** — control what leaks across module boundaries → `usecases/08-encapsulation-module-boundaries.md`
- **Metaprogramming & syntax extension** — extend the language safely at compile time → `usecases/09-metaprogramming-syntax-extension.md`
- **Interop & escape hatches** — `sorry`, `partial`, `unsafe`, FFI — opt out with known boundaries → `usecases/10-interop-escape-hatches.md`
