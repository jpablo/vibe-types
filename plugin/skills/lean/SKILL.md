---
name: vibe-types:lean
description: Lean 4 compile-time safety techniques — dependent types, inductive types, type classes, termination checking, propositions as types, proof automation. Use this skill whenever the user writes Lean 4 code, mentions dependent types, asks about theorem proving, discusses inductive types, type classes, tactics (simp, omega, decide), subtypes, termination proofs, or any Lean type system feature. Also use when formalizing invariants, writing proof-carrying code, or porting type patterns from Scala, Rust, or Haskell to Lean.
version: 0.2.0
---

# Lean 4 — Compile-Time Safety Techniques

> **Base path:** `${CLAUDE_PLUGIN_ROOT}/skills/lean`

## Core tenets

Let the type checker carry as much of correctness as it can. The idea is to move guarantees out of runtime checks, tests, and discipline and into the types, so that holding a value is itself evidence that its invariants hold. Wherever you can, make a bad state impossible to express instead of checking for it later. Treat these as defaults to apply with judgment, not as absolute rules.

- **Make illegal states unrepresentable.** Model the data so that an invalid combination of values does not typecheck. → `usecases/UC01-invalid-states.md`
- **Parse, don't validate.** At the boundary, turn a check into a value of a refined type that proves the check ran, rather than returning a boolean and discarding what you learned. → `catalog/T26-refinement-types.md`
- **Keep a functional core and an imperative shell.** Put the decisions and computation in pure functions that take values and return values, and push the effects (input and output, network calls, database access, the clock, randomness) out to a thin outer layer that calls into that core. The core stays deterministic and easy to test and reason about, and the shell is the only part that talks to the outside world. → `usecases/UC11-effect-tracking.md`
- **Upgrade information at the edges; never re-acquire it in the core.** Every parse, check, or branch gains information. Capture it in a type at the boundary and pass it inward, so that the core relies on the evidence it already has instead of re-deriving it by checking or parsing again. This is the second half of parse-don't-validate, applied to every decision point and not just to input. → `catalog/T58-witness-evidence.md`
- **Prefer a more precise type over a less precise one.** A type is more precise when its inhabitants (the distinct values it can hold, so `Bool` has two and a three-case enum has three) match the values that are legal for the job, holding every value that should occur and as few as possible that should not. A practical rule: among the types that can represent every legal value, choose the one with the fewest inhabitants, since the extra inhabitants are exactly the values that should never occur and that you would otherwise have to check for. For a yes or no choice, `Bool` is more precise than `Int`; a closed enum is more precise than a `String`; `NonEmptyList` is more precise than `List`. A newtype covers a second case: `UserId` and `OrderId` may have the same number of inhabitants as the integer underneath, but as distinct types they can no longer be passed in place of one another. The limiting case, a type with no illegal inhabitants at all, is just make illegal states unrepresentable. → `catalog/T03-newtypes-opaque.md`
- **Add precision where a wrong value would do real harm, and leave low-stakes values plain.** A precise type costs some friction to introduce and use, so add it where that cost is worth it. Reach for one when a wrong value would pass unnoticed (nothing fails to signal it), when it would be expensive (money, access, lost data), when the value crosses a boundary (untrusted input, a public API, anything stored or sent), or when the same fact is relied on in many places or far from where it was first established. Leave a value plain when it is used once, locally, never branched on, and a wrong value would be obvious and harmless, such as a string you only display, a log message, or a one-off script. Before introducing a new type, ask which never-legal value it rules out and what it would cost if that value occurred; if it rules nothing out, keep the plain type.
- **Prefer types over tests to capture invariants.** If the compiler can enforce a property, do not write a test for it. Keep tests for the behavior that types cannot express.
- **Make functions total, and let the compiler force every case.** A total function is defined for every input its parameter types allow: no input makes it throw, hang, or return a meaningless result. There are two ways to get there. Widen the output, returning `Option` or `Result` so that "no answer" becomes a case the caller has to handle. Or narrow the input, for example taking a `NonEmptyList` so that `head` always has an answer. When you match, cover every constructor and avoid a catch-all case unless the set of cases is genuinely open, so that adding a variant later becomes a compile error instead of a silent fall-through. For a branch that genuinely cannot occur, close it with a value of an empty type (the uninhabited type, written `Nothing`, `Never`, `!`, or `Empty` depending on the language), which has no inhabitants and so proves the branch unreachable, rather than throwing a "can't happen" error that a later change can turn into a real crash. Finally, prefer a definition that provably terminates over one you only expect to terminate. → `catalog/T51-totality.md`, `catalog/T28-termination.md`, `catalog/T34-never-bottom.md`
- **Make immutability the default, and mark mutation as the exception.** A value that cannot change after it is constructed cannot quietly become invalid behind the check that vouched for it. Require an explicit, visible marker to opt into mutation or shared aliasing, so that the type records which values are allowed to change. → `catalog/T32-immutability-markers.md`
- **Use state machines when appropriate.** When an object has a lifecycle or a protocol, encode its states as types so that an invalid transition does not compile. These are the invariants that hold across time, between calls, rather than inside a single value. → `usecases/UC13-state-machines.md`
- **Pass authority as a typed value instead of reaching for ambient power.** The right to do something powerful or effectful is itself a value, and a function should receive it as an argument rather than reach for it on its own. Treat as authority the ability to use the filesystem, make a network call, read the clock or a source of randomness, read an environment variable or a secret, start a subprocess, or move money. A function that needs one of these should take it as a parameter (a `Clock`, an `HttpClient`, a `PaymentGateway`, and so on) instead of calling a global or a singleton. A function whose type does not name a given authority then cannot use it, the caller decides what to pass down, and the code becomes easy to test by passing a different value. → `catalog/T12-effect-tracking.md`

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
- **Runtime polymorphism** *(via coercions + type classes)* — heterogeneous collections, existential wrappers for open dispatch → `catalog/T36-trait-objects.md`

- **Functor / Applicative / Monad** — native type classes; do-notation desugars to bind → `catalog/T54-functor-applicative-monad.md`
- **Monad transformers** — StateT, ReaderT, ExceptT; MonadLift between layers → `catalog/T55-monad-transformers.md`
- **Tagless final** *(via type class abstraction)* — polymorphic interpretation → `catalog/T56-tagless-final.md`
- **Typestate pattern** — indexed inductive types for protocol states → `catalog/T57-typestate.md`
- **Witness & evidence types** — Prop proofs as evidence; Decidable for runtime → `catalog/T58-witness-evidence.md`
- **Existential types** — Sigma types, existential quantification → `catalog/T59-existential-types.md`
- **Recursive types** — inductive types ARE recursive types; termination checked → `catalog/T61-recursive-types.md`
## Use cases (problem → which features help)

- **Preventing invalid states** — make illegal states unrepresentable at compile time (inductive types, subtypes, dependent types) → `usecases/UC01-invalid-states.md`
- **Domain modeling with dependent types** — model domain invariants as type-level constraints the compiler enforces → `usecases/UC02-domain-modeling.md`
- **Totality & exhaustiveness** — every function handles all inputs; no unmatched cases → `usecases/UC03-exhaustiveness.md`
- **Compile-time invariants** — attach invariants to data; compiler verifies them via proofs → `usecases/UC12-compile-time.md`
- **Safe effectful programming** — track side effects via IO and monads; prevent untracked mutation → `usecases/UC11-effect-tracking.md`
- **Generic programming with type classes** — constrain generic code to types with required capabilities → `usecases/UC04-generic-constraints.md`
- **Safe recursion & termination** — all recursion terminates; structural or well-founded proof → `usecases/UC24-termination.md`
- **Encapsulation & module boundaries** — control what leaks across module boundaries → `usecases/UC10-encapsulation.md`
