# Master Use-Case Index

Language-agnostic inventory of type-safety use cases. Each entry has a stable ID that matches the filename used across all language use-case directories: `usecases/<ID>.md`.

A `✓` means the language has this file; `—` means it's a gap.

## Use cases

| ID | Use case | Problem it solves | Scala 3 | Python | Rust | Lean |
|----|----------|------------------|:-------:|:------:|:----:|:----:|
| UC01-invalid-states | Preventing invalid states | Make illegal states unrepresentable; invalid combinations are compile errors | ✓ | ✓ | ✓ | ✓ |
| UC02-domain-modeling | Domain modeling | Domain primitives carry semantic meaning; types prevent mix-ups | ✓ | ✓ | — | ✓ |
| UC03-exhaustiveness | Type narrowing & exhaustiveness | After a check, type is narrowed; all cases must be handled | — | ✓ | — | ✓ |
| UC04-generic-constraints | Generic capability constraints | Accept only types satisfying required capabilities; reject the rest | — | ✓ | ✓ | ✓ |
| UC05-structural-contracts | Structural contracts & duck typing | Static verification of duck-typed interfaces | — | ✓ | — | — |
| UC06-immutability | Immutability & finality | Prevent reassignment, override, and mutation after declaration | — | ✓ | — | — |
| UC07-callable-contracts | API contracts & callable typing | Callback/decorator signatures preserve parameter and return types | — | ✓ | — | — |
| UC08-error-handling | Error handling with types | Error paths tracked in the type system, not just convention | ✓ | ✓ | — | — |
| UC09-builder-config | Configuration & builder patterns | Required fields enforced; invalid construction is a compile error | ✓ | ✓ | — | — |
| UC10-encapsulation | Access & encapsulation | Hide representations; control what leaks across module boundaries | ✓ | — | — | ✓ |
| UC11-effect-tracking | Effect tracking & purity | Track side effects and capabilities at the type level | ✓ | — | — | ✓ |
| UC12-compile-time | Compile-time programming & validation | Move checks, branching, and code generation to compile time | ✓ | — | — | ✓ |
| UC13-state-machines | Protocol & state machines | Enforce valid call ordering at compile time; phantom builders | ✓ | — | — | — |
| UC14-extensibility | Extensibility & polymorphic interfaces | Allow plugins/alternative impls without losing type safety | ✓ | — | ✓ | — |
| UC15-equality | Equality & comparison safety | Prevent nonsensical equality checks at compile time | ✓ | — | — | — |
| UC16-nullability | Nullability & optionality | Eliminate NPEs; force handling of absent values | ✓ | — | — | — |
| UC17-variance | Variance & subtyping control | Control co/contravariance precisely; prevent unsound substitutions | ✓ | — | — | — |
| UC18-type-arithmetic | Type-level arithmetic & value invariants | Enforce numeric/dimensional constraints at compile time | ✓ | — | ✓ | — |
| UC19-serialization | Serialization codecs | Auto-derive serializers with full type safety | ✓ | — | — | — |
| UC20-ownership-apis | Ownership-safe APIs | Encode resource lifecycle in signatures; prevent use-after-free | — | — | ✓ | — |
| UC21-concurrency | Compile-time concurrency safety | Threaded code compiles only when transfer and sharing are safe | — | — | ✓ | — |
| UC22-conversions | Conversion boundaries | Make cross-domain conversions explicit and type-checked | — | — | ✓ | — |
| UC23-diagnostics | Trait/type error diagnostics | Map confusing compiler errors back to fixable problems | — | — | ✓ | — |
| UC24-termination | Safe recursion & termination | All recursion must provably terminate | — | — | — | ✓ |
| UC25-metaprogramming | Metaprogramming & syntax extension | Extend the language safely at compile time | — | — | — | ✓ |
| UC26-escape-hatches | Interop & escape hatches | Opt out of safety with known boundaries (sorry, unsafe, partial, FFI) | — | — | — | ✓ |
| UC27-gradual-adoption | Gradual adoption of type safety | Incrementally add types to an untyped codebase | — | ✓ | — | — |
| UC28-decorator-typing | Decorator / wrapper typing | Decorators preserve or transform function signatures visibly | — | ✓ | — | — |
| UC29-typed-records | Typed dictionaries & records | Dictionary-shaped data has known keys with typed values | — | ✓ | — | — |
| UC30-migration | Migration from previous version | Map old idioms to new type-safe equivalents | ✓ | — | — | — |

## Coverage summary

| Language | Covered | Total |
|----------|---------|-------|
| Scala 3  | 14      | /30   |
| Python   | 12      | /30   |
| Rust     | 8       | /30   |
| Lean     | 9       | /30   |
