---
name: vibe-types:typescript
description: TypeScript compile-time safety techniques — discriminated unions, structural typing, conditional types, literal types, branded types, mapped types, template literal types, strictNullChecks, generics. Use this skill whenever the user writes TypeScript, asks about type errors, discusses discriminated unions, branded types, generic constraints, conditional types, mapped types, or any TypeScript type system feature. Also use when porting type patterns from Scala, Rust, Python, or Haskell to TypeScript.
version: 0.2.0
---

# TypeScript — Compile-Time Safety Techniques

> **Base path:** `${CLAUDE_PLUGIN_ROOT}/skills/typescript`

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
