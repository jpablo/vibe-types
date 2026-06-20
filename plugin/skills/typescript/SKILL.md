---
name: vibe-types:typescript
description: TypeScript compile-time safety techniques — discriminated unions, structural typing, conditional types, literal types, branded types, mapped types, template literal types, strictNullChecks, generics. Use this skill whenever the user writes TypeScript, asks about type errors, discusses discriminated unions, branded types, generic constraints, conditional types, mapped types, or any TypeScript type system feature. Also use when porting type patterns from Scala, Rust, Python, or Haskell to TypeScript.
version: 0.2.0
---

# TypeScript — Compile-Time Safety Techniques

> **Base path:** `${CLAUDE_PLUGIN_ROOT}/skills/typescript`

## Core tenets

Let the type checker carry as much of correctness as it can. The idea is to move guarantees out of runtime checks, tests, and discipline and into the types, so that holding a value is itself evidence that its invariants hold. Wherever you can, make a bad state impossible to express instead of checking for it later. Treat these as defaults to apply with judgment, not as absolute rules.

- **Make illegal states unrepresentable.** Model the data so that an invalid combination of values does not typecheck.
- **Parse, don't validate.** At the boundary, turn a check into a value of a refined type that proves the check ran, rather than returning a boolean and discarding what you learned.
- **Keep a functional core and an imperative shell.** Put the decisions and computation in pure functions that take values and return values, and push the effects (input and output, network calls, database access, the clock, randomness) out to a thin outer layer that calls into that core. The core stays deterministic and easy to test and reason about, and the shell is the only part that talks to the outside world.
- **Upgrade information at the edges; never re-acquire it in the core.** Every parse, check, or branch gains information. Capture it in a type at the boundary and pass it inward, so that the core relies on the evidence it already has instead of re-deriving it by checking or parsing again. This is the second half of parse-don't-validate, applied to every decision point and not just to input.
- **Prefer a more precise type over a less precise one.** A type is more precise when its inhabitants (the distinct values it can hold, so `Bool` has two and a three-case enum has three) match the values that are legal for the job, holding every value that should occur and as few as possible that should not. A practical rule: among the types that can represent every legal value, choose the one with the fewest inhabitants, since the extra inhabitants are exactly the values that should never occur and that you would otherwise have to check for. For a yes or no choice, `Bool` is more precise than `Int`; a closed enum is more precise than a `String`; `NonEmptyList` is more precise than `List`. A newtype covers a second case: `UserId` and `OrderId` may have the same number of inhabitants as the integer underneath, but as distinct types they can no longer be passed in place of one another. The limiting case, a type with no illegal inhabitants at all, is just make illegal states unrepresentable.
- **Add precision where a wrong value would do real harm, and leave low-stakes values plain.** A precise type costs some friction to introduce and use, so add it where that cost is worth it. Reach for one when a wrong value would pass unnoticed (nothing fails to signal it), when it would be expensive (money, access, lost data), when the value crosses a boundary (untrusted input, a public API, anything stored or sent), or when the same fact is relied on in many places or far from where it was first established. Leave a value plain when it is used once, locally, never branched on, and a wrong value would be obvious and harmless, such as a string you only display, a log message, or a one-off script. Before introducing a new type, ask which never-legal value it rules out and what it would cost if that value occurred; if it rules nothing out, keep the plain type.
- **Prefer types over tests to capture invariants.** If the compiler can enforce a property, do not write a test for it. Keep tests for the behavior that types cannot express.
- **Make functions total, and let the compiler force every case.** A total function is defined for every input its parameter types allow: no input makes it throw, hang, or return a meaningless result. There are two ways to get there. Widen the output, returning `Option` or `Result` so that "no answer" becomes a case the caller has to handle. Or narrow the input, for example taking a `NonEmptyList` so that `head` always has an answer. When you match, cover every constructor and avoid a catch-all case unless the set of cases is genuinely open, so that adding a variant later becomes a compile error instead of a silent fall-through. For a branch that genuinely cannot occur, close it with a value of an empty type (the uninhabited type, written `Nothing`, `Never`, `!`, or `Empty` depending on the language), which has no inhabitants and so proves the branch unreachable, rather than throwing a "can't happen" error that a later change can turn into a real crash. Finally, prefer a definition that provably terminates over one you only expect to terminate.
- **Make immutability the default, and mark mutation as the exception.** A value that cannot change after it is constructed cannot quietly become invalid behind the check that vouched for it. Require an explicit, visible marker to opt into mutation or shared aliasing, so that the type records which values are allowed to change.
- **Use state machines when appropriate.** When an object has a lifecycle or a protocol, encode its states as types so that an invalid transition does not compile. These are the invariants that hold across time, between calls, rather than inside a single value.
- **Pass authority as a typed value instead of reaching for ambient power.** The right to do something powerful or effectful is itself a value, and a function should receive it as an argument rather than reach for it on its own. Treat as authority the ability to use the filesystem, make a network call, read the clock or a source of randomness, read an environment variable or a secret, start a subprocess, or move money. A function that needs one of these should take it as a parameter (a `Clock`, an `HttpClient`, a `PaymentGateway`, and so on) instead of calling a global or a singleton. A function whose type does not name a given authority then cannot use it, the caller decides what to pass down, and the code becomes easy to test by passing a different value.

## Full catalog (type system features → constraints they enforce)

- **Discriminated unions & ADTs** — closed tagged unions; exhaustive `switch`; invalid states unrepresentable → `catalog/T01-algebraic-data-types.md`
- **Union & intersection types** — `A | B`, `A & B`; express alternatives without class hierarchies → `catalog/T02-union-intersection.md`
- **Branded/opaque types** — `type UserId = string & { __brand: "UserId" }`; prevent value mix-ups at zero runtime cost → `catalog/T03-newtypes-opaque.md`
- **Generics & bounds** — `<T extends U>`; generic code only compiles when constraints hold → `catalog/T04-generics-bounds.md`
- **Decorators & schema derivation** — stage-3 decorators, `zod.infer<>`, `reflect-metadata`; auto-generate instances from shape → `catalog/T06-derivation.md`
- **Structural typing** — TypeScript's core is structural; shape conformance without inheritance → `catalog/T07-structural-typing.md`
- **Variance & subtyping** — implicit covariance/contravariance in function and generic positions → `catalog/T08-variance-subtyping.md`
- **Effect tracking** — `Promise<T>`, `Result` patterns, fp-ts `IO`; track side effects at type level → `catalog/T12-effect-tracking.md`
- **Null safety** — `strictNullChecks`, `T | null | undefined`, optional chaining; reference types never null by default → `catalog/T13-null-safety.md`
- **Type narrowing & exhaustiveness** — type guards, `in`, `instanceof`, discriminant checks; narrow to specific branch → `catalog/T14-type-narrowing.md`
- **Decorators & metaprogramming** — stage-3 decorators; type-level tricks with conditional/mapped types → `catalog/T17-macros-metaprogramming.md`
- **Type assertions & coercions** — `as`, `satisfies`, `is` predicates; explicit opt-in conversions → `catalog/T18-conversions-coercions.md`
- **Encapsulation & module boundaries** — `private`, `#field`, `readonly`, module exports; control surface area → `catalog/T21-encapsulation.md`
- **Callable types & overloads** — function types, overload signatures, `ReturnType<F>` → `catalog/T22-callable-typing.md`
- **Type aliases** — `type Foo = ...`; recursive aliases, utility types → `catalog/T23-type-aliases.md`
- **Refinement types** — branded types + smart constructors; validate at boundary, carry proof in type → `catalog/T26-refinement-types.md`
- **Phantom types** — brand intersection pattern; compile-time-only type markers, zero runtime cost → `catalog/T27-erased-phantom.md`
- **Record types & interfaces** — `interface`, object literal types, `Record<K, V>`, index signatures → `catalog/T31-record-types.md`
- **Immutability** — `readonly`, `as const`, `Readonly<T>`, `ReadonlyArray<T>`; prevent reassignment → `catalog/T32-immutability-markers.md`
- **Polymorphic `this`** — fluent builder chains; subclass-aware return types → `catalog/T33-self-type.md`
- **Never & bottom type** — `never`; exhaustiveness proofs; unreachable branches → `catalog/T34-never-bottom.md`
- **Runtime polymorphism** — interfaces + class; `instanceof` dispatch; union narrowing → `catalog/T36-trait-objects.md`
- **Conditional types** — `T extends U ? X : Y`; `infer`; type-level branching and computation → `catalog/T41-match-types.md`
- **Variadic tuples** — `[...T]`; `infer` in tuple position; spreading tuple types → `catalog/T45-paramspec-variadic.md`
- **Gradual typing & `any`** — `any`, `unknown`, `--strict` flags; escape hatches and enforcement levels → `catalog/T47-gradual-typing.md`
- **Infer & associated types** — `infer R` in conditional types; `ReturnType`, `Parameters`, `Awaited` → `catalog/T49-associated-types.md`
- **Literal types** — `"foo"`, `42`, `true`; restrict types to specific values; string discriminants → `catalog/T52-literal-types.md`
- **Functor/Monad (fp-ts)** — `map`, `chain`, `pipe`; compositional effect chaining via fp-ts Option/Either/Task → `catalog/T54-functor-applicative-monad.md`
- **Typestate pattern** — phantom brands track state; invalid transitions don't compile → `catalog/T57-typestate.md`
- **Existential types** — `<T>() => T` pattern; hide concrete type while preserving contracts → `catalog/T59-existential-types.md`
- **Recursive types** — self-referential interfaces and `type` aliases; trees, JSON, expressions → `catalog/T61-recursive-types.md`
- **Mapped types & keyof/typeof** — `{ [K in keyof T]: ... }`; `keyof`, `typeof`; transform and query object shapes → `catalog/T62-mapped-types.md`
- **Template literal types** — `` `${A}${B}` ``; string-level type computation; route patterns, CSS → `catalog/T63-template-literal-types.md`
- **Async iteration & generators** — `AsyncIterator`, `for await...of`, async generators; type-safe async streams → `catalog/T64-async-iteration.md`

## Use cases (problem → which features help)

- **Preventing invalid states** — discriminated unions, branded types, phantom types → `usecases/UC01-invalid-states.md`
- **Domain modeling** — newtypes, smart constructors, closed hierarchies → `usecases/UC02-domain-modeling.md`
- **Exhaustiveness checking** — compiler enforces all variants handled → `usecases/UC03-exhaustiveness.md`
- **Generic constraints** — accept only types satisfying required shape → `usecases/UC04-generic-constraints.md`
- **Structural contracts** — interface shape enforcement without inheritance → `usecases/UC05-structural-contracts.md`
- **Immutability** — prevent mutation after construction → `usecases/UC06-immutability.md`
- **Callable contracts** — constrain function signatures and overloads → `usecases/UC07-callable-contracts.md`
- **Error handling** — type-safe error channels via union types and Result → `usecases/UC08-error-handling.md`
- **Builder & config patterns** — DSLs where invalid compositions are type errors → `usecases/UC09-builder-config.md`
- **Encapsulation** — hide representations, control module surface → `usecases/UC10-encapsulation.md`
- **State machines** — enforce valid call ordering at type level → `usecases/UC13-state-machines.md`
- **Extensibility** — interface + declaration merging; open extension → `usecases/UC14-extensibility.md`
- **Equality constraints** — prevent accidental cross-type comparisons → `usecases/UC15-equality.md`
- **Nullability** — eliminate null bugs via strict null checks → `usecases/UC16-nullability.md`
- **Variance** — control covariance/contravariance in generic positions → `usecases/UC17-variance.md`
- **Serialization** — auto-derive schemas (Zod, io-ts) with full type safety → `usecases/UC19-serialization.md`
- **Async & concurrency** — type-safe async composition (Promise, Awaited, AbortSignal) → `usecases/UC21-async-concurrency.md`
