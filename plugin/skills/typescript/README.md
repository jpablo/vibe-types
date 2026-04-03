# TypeScript Type System Constraint Guide

> Status: **In Progress**

An exhaustive reference mapping TypeScript type system features to the constraints and properties they can enforce at compile time. TypeScript's type system is structural and gradual: the compiler checks shape conformance rather than nominal identity, and enforcement levels are configurable from permissive (`any`) to strict (`--strict` with `noUncheckedIndexedAccess`). Despite being layered atop JavaScript, TypeScript supports sophisticated type-level computation — conditional types, mapped types, template literal types, infer, and recursive aliases — that rivals dedicated dependently-typed languages for everyday programming tasks.

This guide is organized into two parts. Part I (Feature Catalog) answers: *given a type system feature, what constraints can I enforce with it?* Part II (Use-Case Index) answers: *I want the compiler to enforce property X — which features help, and how?* The two parts are tightly cross-linked so you can navigate in either direction.

**Audience:** TypeScript developers who want to move beyond basic annotations and use the type system as a correctness tool — catching bugs at compile time, making illegal states unrepresentable, and encoding domain invariants directly in types.

---

## How to Use This Guide

| Goal | Start here |
|------|-----------|
| Learn about a specific feature | [Part I: Feature Catalog](#part-i-feature-catalog) |
| Find features for a specific problem | [Part II: Use-Case Index](#part-ii-use-case-index) |
| See cross-language coverage | [Techniques matrix](../../../taxonomy/techniques.md) |

### Cross-Reference Notation

Throughout the guide:

- **`[-> T##]`** links to a Feature Catalog document (e.g., `[-> T03](catalog/T03-newtypes-opaque.md)` → Branded Types)
- **`[-> UC-##]`** links to a Use-Case Index document (e.g., `[-> UC-01]` → Preventing Invalid States)
- Each catalog doc ends with use-case cross-refs; each use-case doc links back to relevant features.

### Version Coverage

The baseline for this guide is **TypeScript 4.x**, which introduced many of the more expressive features (template literal types, variadic tuples, `infer` in conditional types). Newer capabilities are noted with a `> **Since:** TypeScript X.Y` annotation in each catalog document. Features that require compiler flags (such as `strictNullChecks`, `noUncheckedIndexedAccess`, or `exactOptionalPropertyTypes`) are marked `> **Status:** Requires \`--strict\`` or the relevant flag name. The guide currently covers through **TypeScript 5.x**.

---

## Part I: Feature Catalog

Organized by feature. Each document answers: *"What can I enforce with this feature?"*

| # | Document | Feature | Key Constraint |
|---|----------|---------|----------------|
| 00 | [Reading Guide](catalog/00-overview.md) | Overview | — |
| 01 | [Discriminated Unions & ADTs](catalog/T01-algebraic-data-types.md) | Tagged unions, exhaustive `switch` | Invalid states unrepresentable |
| 02 | [Union & Intersection Types](catalog/T02-union-intersection.md) | `A \| B`, `A & B` | Alternatives and capability composition |
| 03 | [Branded/Opaque Types](catalog/T03-newtypes-opaque.md) | `type UserId = string & { __brand: "UserId" }` | Prevent value mix-ups at zero runtime cost |
| 04 | [Generics & Bounds](catalog/T04-generics-bounds.md) | `<T extends U>` | Code compiles only when constraints hold |
| 05 | [Interfaces & Structural Contracts](catalog/T05-type-classes.md) | `interface`, `implements` | Compiler-enforced structural capabilities |
| 06 | [Decorators & Schema Derivation](catalog/T06-derivation.md) | Stage-3 decorators, `zod.infer<>` | Auto-generate instances from shape |
| 07 | [Structural Typing](catalog/T07-structural-typing.md) | Shape conformance | No inheritance required |
| 08 | [Variance & Subtyping](catalog/T08-variance-subtyping.md) | Covariance/contravariance | Correct function and generic subtyping |
| 09 | [Effect Tracking](catalog/T12-effect-tracking.md) | `Promise<T>`, Result, fp-ts `IO` | Side effects visible in types |
| 10 | [Null Safety](catalog/T13-null-safety.md) | `strictNullChecks`, `T \| null` | Reference types non-nullable by default |
| 11 | [Type Narrowing & Exhaustiveness](catalog/T14-type-narrowing.md) | Type guards, `in`, `instanceof` | Narrow to specific branch; enforce coverage |
| 12 | [Decorators & Metaprogramming](catalog/T17-macros-metaprogramming.md) | Stage-3 decorators, conditional/mapped types | Type-level code generation |
| 13 | [Type Assertions & Coercions](catalog/T18-conversions-coercions.md) | `as`, `satisfies`, `is` predicates | Explicit opt-in conversions |
| 14 | [Encapsulation & Module Boundaries](catalog/T21-encapsulation.md) | `private`, `#field`, `readonly`, exports | Control surface area |
| 15 | [Callable Types & Overloads](catalog/T22-callable-typing.md) | Function types, overload signatures | Constrain callable shapes |
| 16 | [Type Aliases](catalog/T23-type-aliases.md) | `type Foo = ...`, utility types | Recursive aliases, named shapes |
| 17 | [Refinement Types](catalog/T26-refinement-types.md) | Branded types + smart constructors | Validated values with proof in type |
| 18 | [Phantom Types](catalog/T27-erased-phantom.md) | Brand intersection | Compile-time-only markers, zero runtime cost |
| 19 | [Record Types & Interfaces](catalog/T31-record-types.md) | `interface`, `Record<K,V>`, index signatures | Typed object shapes |
| 20 | [Immutability](catalog/T32-immutability-markers.md) | `readonly`, `as const`, `Readonly<T>` | Prevent reassignment |
| 21 | [Polymorphic `this`](catalog/T33-self-type.md) | `this` return type | Fluent builder chains, subclass-aware returns |
| 22 | [Never & Bottom Type](catalog/T34-never-bottom.md) | `never` | Exhaustiveness proofs, unreachable branches |
| 23 | [Runtime Polymorphism](catalog/T36-trait-objects.md) | Interfaces + class, `instanceof` | Dispatch with union narrowing |
| 24 | [Conditional Types](catalog/T41-match-types.md) | `T extends U ? X : Y`, `infer` | Type-level branching and computation |
| 25 | [Variadic Tuples](catalog/T45-paramspec-variadic.md) | `[...T]`, `infer` in tuple position | Typed rest parameters, tuple spreading |
| 26 | [Gradual Typing & `any`](catalog/T47-gradual-typing.md) | `any`, `unknown`, `--strict` flags | Escape hatches and enforcement levels |
| 27 | [Infer & Associated Types](catalog/T49-associated-types.md) | `infer R`, `ReturnType`, `Parameters` | Extract types from type positions |
| 28 | [Literal Types](catalog/T52-literal-types.md) | `"foo"`, `42`, `true` | Restrict to specific values; string discriminants |
| 29 | [Functor/Monad (fp-ts)](catalog/T54-functor-applicative-monad.md) | `map`, `chain`, `pipe` | Compositional effect chaining |
| 30 | [Typestate Pattern](catalog/T57-typestate.md) | Phantom brands tracking state | Invalid transitions don't compile |
| 31 | [Existential Types](catalog/T59-existential-types.md) | `<T>() => T` pattern | Hide concrete type while preserving contracts |
| 32 | [Recursive Types](catalog/T61-recursive-types.md) | Self-referential interfaces and `type` aliases | Trees, JSON, expression types |
| 33 | [Mapped Types & keyof/typeof](catalog/T62-mapped-types.md) | `{ [K in keyof T]: ... }`, `keyof`, `typeof` | Transform and query object shapes |
| 34 | [Template Literal Types](catalog/T63-template-literal-types.md) | `` `${A}${B}` `` | String-level type computation |

---

## Part II: Use-Case Index

Organized by constraint. Each document answers: *"I want to enforce X — which features help?"*

| # | Document | Constraint |
|---|----------|-----------|
| 00 | [Navigation Guide](usecases/00-overview.md) | Overview |
| 01 | [Preventing Invalid States](usecases/UC01-invalid-states.md) | Make illegal states unrepresentable |
| 02 | [Domain Modeling](usecases/UC02-domain-modeling.md) | Precise domain types with newtypes and hierarchies |
| 03 | [Exhaustiveness Checking](usecases/UC03-exhaustiveness.md) | Compiler enforces all variants handled |
| 04 | [Generic Constraints](usecases/UC04-generic-constraints.md) | Accept only types satisfying required shape |
| 05 | [Structural Contracts](usecases/UC05-structural-contracts.md) | Interface shape enforcement without inheritance |
| 06 | [Immutability](usecases/UC06-immutability.md) | Prevent mutation after construction |
| 07 | [Callable Contracts](usecases/UC07-callable-contracts.md) | Constrain function signatures and overloads |
| 08 | [Error Handling](usecases/UC08-error-handling.md) | Type-safe error channels via union types and Result |
| 09 | [Builder & Config Patterns](usecases/UC09-builder-config.md) | DSLs where invalid compositions are type errors |
| 10 | [Encapsulation](usecases/UC10-encapsulation.md) | Hide representations, control module surface |
| 11 | [State Machines](usecases/UC13-state-machines.md) | Enforce valid call ordering at type level |
| 12 | [Extensibility](usecases/UC14-extensibility.md) | Interface + declaration merging; open extension |
| 13 | [Equality Constraints](usecases/UC15-equality.md) | Prevent accidental cross-type comparisons |
| 14 | [Nullability](usecases/UC16-nullability.md) | Eliminate null bugs via strict null checks |
| 15 | [Variance](usecases/UC17-variance.md) | Control covariance/contravariance in generic positions |
| 16 | [Serialization](usecases/UC19-serialization.md) | Auto-derive schemas (Zod, io-ts) with full type safety |
| 17 | [Async & Concurrency](usecases/UC21-async-concurrency.md) | Type-safe async composition (Promise, Awaited, AbortSignal) |

---

## TypeScript Version Coverage

Each catalog document includes a `> **Since:** TypeScript X.Y` annotation. The guide covers the baseline feature set from TypeScript 4.0 through TypeScript 5.x. Features requiring specific compiler flags (`--strict`, `--noUncheckedIndexedAccess`, `--exactOptionalPropertyTypes`) are called out explicitly.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| `[-> T##]` | Cross-reference to feature catalog entry |
| `[-> UC-##]` | Cross-reference to use-case entry |
| `// error` | Line the compiler rejects |
| `// OK` | Line that compiles successfully |
| ⚠️ | Gotcha or common pitfall |
| ★ | Key constraint insight |
