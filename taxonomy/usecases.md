# Master Use-Case Index

Language-agnostic inventory of type-safety use cases. Each entry has a stable ID that matches the filename used across all language use-case directories: `usecases/<ID>.md`.

Legend: [✓](link) native support | [~](link) achievable via other features | `—` gap (could be added) | `×` not expressible

## Use cases

| ID | Use case | Problem it solves | Scala 3 | Python | Rust | Lean |
|----|----------|------------------|---------|--------|------|------|
| UC01-invalid-states | Preventing invalid states | Make illegal states unrepresentable; prefer parsing (returning refined types) over validation (checking and discarding). See [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/) | [✓](../plugin/skills/scala3/usecases/UC01-invalid-states.md) | [✓](../plugin/skills/python/usecases/UC01-invalid-states.md) | [✓](../plugin/skills/rust/usecases/UC01-invalid-states.md) | [✓](../plugin/skills/lean/usecases/UC01-invalid-states.md)|
| UC02-domain-modeling | Domain modeling | Domain primitives carry semantic meaning; types prevent mix-ups | [✓](../plugin/skills/scala3/usecases/UC02-domain-modeling.md) | [✓](../plugin/skills/python/usecases/UC02-domain-modeling.md) | — | [✓](../plugin/skills/lean/usecases/UC02-domain-modeling.md)|
| UC03-exhaustiveness | Type narrowing & exhaustiveness | After a check, type is narrowed; all cases must be handled | — | [✓](../plugin/skills/python/usecases/UC03-exhaustiveness.md) | — | [✓](../plugin/skills/lean/usecases/UC03-exhaustiveness.md)|
| UC04-generic-constraints | Generic capability constraints | Accept only types satisfying required capabilities; reject the rest | — | [✓](../plugin/skills/python/usecases/UC04-generic-constraints.md) | [✓](../plugin/skills/rust/usecases/UC04-generic-constraints.md) | [✓](../plugin/skills/lean/usecases/UC04-generic-constraints.md)|
| UC05-structural-contracts | Structural contracts & duck typing | Static verification of duck-typed interfaces | — | [✓](../plugin/skills/python/usecases/UC05-structural-contracts.md) | — | —|
| UC06-immutability | Immutability & finality | Prevent reassignment, override, and mutation after declaration | — | [✓](../plugin/skills/python/usecases/UC06-immutability.md) | — | —|
| UC07-callable-contracts | API contracts & callable typing | Callback/decorator signatures preserve parameter and return types | — | [✓](../plugin/skills/python/usecases/UC07-callable-contracts.md) | — | —|
| UC08-error-handling | Error handling with types | Error paths tracked in the type system, not just convention | [✓](../plugin/skills/scala3/usecases/UC08-error-handling.md) | [✓](../plugin/skills/python/usecases/UC08-error-handling.md) | — | —|
| UC09-builder-config | Configuration & builder patterns | Required fields enforced; invalid construction is a compile error | [✓](../plugin/skills/scala3/usecases/UC09-builder-config.md) | [✓](../plugin/skills/python/usecases/UC09-builder-config.md) | — | —|
| UC10-encapsulation | Access & encapsulation | Hide representations; control what leaks across module boundaries | [✓](../plugin/skills/scala3/usecases/UC10-encapsulation.md) | — | — | [✓](../plugin/skills/lean/usecases/UC10-encapsulation.md)|
| UC11-effect-tracking | Effect tracking & purity | Track side effects and capabilities at the type level | [✓](../plugin/skills/scala3/usecases/UC11-effect-tracking.md) | — | — | [✓](../plugin/skills/lean/usecases/UC11-effect-tracking.md)|
| UC12-compile-time | Compile-time programming & validation | Move checks, branching, and code generation to compile time | [✓](../plugin/skills/scala3/usecases/UC12-compile-time.md) | — | — | [✓](../plugin/skills/lean/usecases/UC12-compile-time.md)|
| UC13-state-machines | Protocol & state machines | Enforce valid call ordering at compile time; phantom builders | [✓](../plugin/skills/scala3/usecases/UC13-state-machines.md) | — | — | —|
| UC14-extensibility | Extensibility & polymorphic interfaces | Allow plugins/alternative impls without losing type safety | [✓](../plugin/skills/scala3/usecases/UC14-extensibility.md) | — | [✓](../plugin/skills/rust/usecases/UC14-extensibility.md) | —|
| UC15-equality | Equality & comparison safety | Prevent nonsensical equality checks at compile time | [✓](../plugin/skills/scala3/usecases/UC15-equality.md) | — | — | —|
| UC16-nullability | Nullability & optionality | Eliminate NPEs; force handling of absent values | [✓](../plugin/skills/scala3/usecases/UC16-nullability.md) | — | — | —|
| UC17-variance | Variance & subtyping control | Control co/contravariance precisely; prevent unsound substitutions | [✓](../plugin/skills/scala3/usecases/UC17-variance.md) | — | — | —|
| UC18-type-arithmetic | Type-level arithmetic & value invariants | Enforce numeric/dimensional constraints at compile time | [✓](../plugin/skills/scala3/usecases/UC18-type-arithmetic.md) | — | [✓](../plugin/skills/rust/usecases/UC18-type-arithmetic.md) | —|
| UC19-serialization | Serialization codecs | Auto-derive serializers with full type safety | [✓](../plugin/skills/scala3/usecases/UC19-serialization.md) | — | — | —|
| UC20-ownership-apis | Ownership-safe APIs | Encode resource lifecycle in signatures; prevent use-after-free | — | — | [✓](../plugin/skills/rust/usecases/UC20-ownership-apis.md) | —|
| UC21-concurrency | Compile-time concurrency safety | Threaded code compiles only when transfer and sharing are safe | — | — | [✓](../plugin/skills/rust/usecases/UC21-concurrency.md) | —|
| UC22-conversions | Conversion boundaries | Make cross-domain conversions explicit and type-checked | — | — | [✓](../plugin/skills/rust/usecases/UC22-conversions.md) | —|
| UC23-diagnostics | Trait/type error diagnostics | Map confusing compiler errors back to fixable problems | — | — | [✓](../plugin/skills/rust/usecases/UC23-diagnostics.md) | —|
| UC24-termination | Safe recursion & termination | All recursion must provably terminate | — | — | — | [✓](../plugin/skills/lean/usecases/UC24-termination.md)|
| UC25-metaprogramming | Metaprogramming & syntax extension | Extend the language safely at compile time | — | — | — | [✓](../plugin/skills/lean/usecases/UC25-metaprogramming.md)|
| UC26-escape-hatches | Interop & escape hatches | Opt out of safety with known boundaries (sorry, unsafe, partial, FFI) | — | — | — | [✓](../plugin/skills/lean/usecases/UC26-escape-hatches.md)|
| UC27-gradual-adoption | Gradual adoption of type safety | Incrementally add types to an untyped codebase | — | [✓](../plugin/skills/python/usecases/UC27-gradual-adoption.md) | — | —|
| UC28-decorator-typing | Decorator / wrapper typing | Decorators preserve or transform function signatures visibly | — | [✓](../plugin/skills/python/usecases/UC28-decorator-typing.md) | — | —|
| UC29-typed-records | Typed dictionaries & records | Dictionary-shaped data has known keys with typed values | — | [✓](../plugin/skills/python/usecases/UC29-typed-records.md) | — | —|
| UC30-migration | Migration from previous version | Map old idioms to new type-safe equivalents | [✓](../plugin/skills/scala3/usecases/UC30-migration.md) | — | — | —|

## Coverage summary

| Language | Covered | Total |
|----------|---------|-------|
| Scala 3  | 14      | /30   |
| Python   | 12      | /30   |
| Rust     | 8       | /30   |
| Lean     | 9       | /30   |
