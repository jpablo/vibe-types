---
name: vibe-types:lean
description: Lean 4 compile-time safety techniques — dependent types, inductive types, type classes, termination checking, propositions as types, proof automation. Use when writing safe Lean 4, choosing type system features, or debugging compiler errors.
version: 0.2.0
---

# Lean 4 — Compile-Time Safety Techniques

> **Base path:** `${CLAUDE_PLUGIN_ROOT}/skills/lean`

## Full catalog (type system features → constraints they enforce)

- **Inductive types & pattern matching** — closed type hierarchies with exhaustive matching; compiler rejects incomplete matches → `catalog/T01-algebraic-data-types.md`
- **Dependent types & Pi types** — return/field types depend on values; compiler checks index consistency → `catalog/T09-dependent-types.md`
- **Structures, inheritance, constructors** — named-field product types with single-constructor guarantees; `extends` for inheritance → `catalog/T31-record-types.md`
- **Type classes & instance resolution** — constrain generic functions to types with required capabilities → `catalog/T05-type-classes.md`
- **Universes & universe polymorphism** — prevent type-in-type paradoxes; `Sort u`, `Type u`, `Prop` → `catalog/T35-universes-kinds.md`
- **Propositions as types (Prop)** — encode invariants as `Prop`; compiler requires proof terms as evidence → `catalog/T29-propositions-as-types.md`
- **Termination & well-founded recursion** — every recursive function must terminate; structural recursion or `termination_by` proof → `catalog/T28-termination.md`
- **Totality, partial functions** — functions must handle all inputs; `partial` opts out but taints the result → `catalog/T51-totality.md`
- **Monads, do-notation, IO** — side effects tracked via monadic types; `IO` demarcates impure computation → `catalog/T12-effect-tracking.md`
- **Coercions & Coe** — automatic safe conversions between types; compiler inserts coercions where declared → `catalog/T18-conversions-coercions.md`
- **Auto-bound implicits & instances** — compiler infers implicit arguments; `[inst : C a]` constrains to types with evidence → `catalog/T38-implicits-auto-bound.md`
- **Macros, elaboration, syntax** — compile-time metaprogramming via `syntax`, `macro_rules`, and `elab` → `catalog/T17-macros-metaprogramming.md`
- **Proof automation (simp, decide, omega)** — automate proof obligations; state what must hold, let tactics verify it → `catalog/T30-proof-automation.md`
- **Subtypes & refinement types** — attach predicates to types (`{ n : Nat // n > 0 }`); construction requires proof → `catalog/T26-refinement-types.md`
- **Opaque definitions & reducibility** — `opaque def` prevents unfolding outside the module; definitional encapsulation → `catalog/T21-encapsulation.md`
- **Notation, attributes, options** — `@[simp]`, `@[inline]`, `@[reducible]` control how the checker treats definitions → `catalog/T39-notation-attributes.md`
- **Literal types** — dependent types subsume literal types; any value can appear in a type via indexing → `catalog/T52-literal-types.md`
- **Path-dependent types** — dependent types subsume path dependence; structures with type-valued fields → `catalog/T53-path-dependent-types.md`
- **Newtypes & opaque definitions** — single-field structures, `abbrev`, `opaque` for hidden definitions → `catalog/T03-newtypes-opaque.md`
- **Null safety** — no null in Lean; `Option α` is the standard pattern → `catalog/T13-null-safety.md`
- **Type narrowing** — pattern matching narrows types; dependent match refines per branch → `catalog/T14-type-narrowing.md`
- **Compile-time computation** — everything is compile-time; `#eval`, `decide`, `simp`, `native_decide` → `catalog/T16-compile-time-ops.md`
- **Equality safety** — `BEq`/`DecidableEq` are opt-in; propositional vs boolean equality → `catalog/T20-equality-safety.md`
- **Callable typing** — first-class functions, dependent function types, automatic currying → `catalog/T22-callable-typing.md`
- **Type aliases** — `abbrev` (reducible), `def` (semireducible), `opaque` (irreducible) → `catalog/T23-type-aliases.md`
- **Erased types & Prop** — `Prop` universe is erased at runtime; zero-cost proof evidence → `catalog/T27-erased-phantom.md`
- **Immutability** — everything immutable by default; `IO.Ref` for controlled mutation → `catalog/T32-immutability-markers.md`
- **Empty & False** — `Empty` type and `False` proposition; `absurd` for impossible cases → `catalog/T34-never-bottom.md`
- **Type lambdas** — type-level functions are just functions; no special syntax needed → `catalog/T40-type-lambdas.md`
- **Match on types** — dependent match works at the type level naturally → `catalog/T41-match-types.md`
- **Const generics** *(via dependent types)* — dependent types subsume value-parameterized types → `catalog/T15-const-generics.md`
- **Union types** *(via inductives)* — `Sum α β` or custom inductives for alternatives → `catalog/T02-union-intersection.md`
- **Generics** *(via type classes)* — instance arguments `[Ord α]` serve as bounds → `catalog/T04-generics-bounds.md`
- **Derivation** *(limited)* — `deriving Repr, BEq, Inhabited`; Mathlib extends further → `catalog/T06-derivation.md`
- **Extension methods** *(via scoped instances)* — namespaced dot notation, `open ... in` → `catalog/T19-extension-methods.md`
- **Coherence** *(via scoping)* — instance priority, `scoped instance`, overlap handling → `catalog/T25-coherence-orphan.md`
- **Self type** *(via dependent types)* — no `Self` keyword; dependent types express this naturally → `catalog/T33-self-type.md`
- **Instance resolution** — synthesis, backtracking, priority ordering → `catalog/T37-trait-solver.md`
- **Context functions** *(via instance arguments)* — `[Ord α]` is automatically supplied → `catalog/T42-context-functions.md`
- **Associated types** *(via structure fields)* — type-valued fields with `outParam` → `catalog/T49-associated-types.md`

## Use cases (problem → which features help)

- **Preventing invalid states** — make illegal states unrepresentable at compile time (inductive types, subtypes, dependent types) → `usecases/UC01-invalid-states.md`
- **Domain modeling with dependent types** — model domain invariants as type-level constraints the compiler enforces → `usecases/UC02-domain-modeling.md`
- **Totality & exhaustiveness** — every function handles all inputs; no unmatched cases → `usecases/UC03-exhaustiveness.md`
- **Compile-time invariants** — attach invariants to data; compiler verifies them via proofs → `usecases/UC12-compile-time.md`
- **Safe effectful programming** — track side effects via IO and monads; prevent untracked mutation → `usecases/UC11-effect-tracking.md`
- **Generic programming with type classes** — constrain generic code to types with required capabilities → `usecases/UC04-generic-constraints.md`
- **Safe recursion & termination** — all recursion terminates; structural or well-founded proof → `usecases/UC24-termination.md`
- **Encapsulation & module boundaries** — control what leaks across module boundaries → `usecases/UC10-encapsulation.md`
- **Metaprogramming & syntax extension** — extend the language safely at compile time → `usecases/UC25-metaprogramming.md`
- **Interop & escape hatches** — `sorry`, `partial`, `unsafe`, FFI — opt out with known boundaries → `usecases/UC26-escape-hatches.md`
