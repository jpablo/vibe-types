# Master Use-Case Index

Language-agnostic inventory of type-safety use cases — problems that the type system can solve. Each entry has a stable ID used to cross-reference the per-language use-case documents.

**Legend:** language column shows the local use-case file (e.g., `usecases/01`) or `—` if not covered.

## Use cases

| ID | Use case | Problem it solves | Scala 3 | Python | Rust | Lean |
|----|----------|------------------|---------|--------|------|------|
| UC01-invalid-states | Preventing invalid states | Make illegal states unrepresentable so invalid combinations are compile errors | `usecases/01` | `usecases/01` | `usecases/01` | `usecases/01` |
| UC02-domain-modeling | Domain modeling | Domain primitives carry semantic meaning; types prevent mix-ups | `usecases/02` | `usecases/02` | — | `usecases/02` |
| UC03-exhaustiveness | Type narrowing & exhaustiveness | After a check, type is narrowed; all cases must be handled | — | `usecases/03` | — | `usecases/03` |
| UC04-generic-constraints | Generic capability constraints | Accept only types satisfying required capabilities; reject the rest | — | `usecases/04` | `usecases/03` | `usecases/06` |
| UC05-structural-contracts | Structural contracts & duck typing | Static verification of duck-typed interfaces | — | `usecases/05` | — | — |
| UC06-immutability | Immutability & finality | Prevent reassignment, override, and mutation after declaration | — | `usecases/06` | — | — |
| UC07-callable-contracts | API contracts & callable typing | Callback/decorator signatures preserve parameter and return types | — | `usecases/07` | — | — |
| UC08-error-handling | Error handling with types | Error paths tracked in the type system, not just convention | `usecases/14` | `usecases/08` | — | — |
| UC09-builder-config | Configuration & builder patterns | Required fields enforced; invalid construction is a compile error | `usecases/13` | `usecases/09` | — | — |
| UC10-encapsulation | Access & encapsulation | Hide representations; control what leaks across module boundaries | `usecases/03` | — | — | `usecases/08` |
| UC11-effect-tracking | Effect tracking & purity | Track side effects and capabilities at the type level | `usecases/04` | — | — | `usecases/05` |
| UC12-compile-time | Compile-time programming & validation | Move checks, branching, and code generation to compile time | `usecases/05` | — | — | `usecases/04` |
| UC13-state-machines | Protocol & state machines | Enforce valid call ordering at compile time; phantom builders | `usecases/06` | — | — | — |
| UC14-extensibility | Extensibility & polymorphic interfaces | Allow plugins/alternative impls without losing type safety | `usecases/07` | — | `usecases/04` | — |
| UC15-equality | Equality & comparison safety | Prevent nonsensical equality checks at compile time | `usecases/08` | — | — | — |
| UC16-nullability | Nullability & optionality | Eliminate NPEs; force handling of absent values | `usecases/09` | — | — | — |
| UC17-variance | Variance & subtyping control | Control co/contravariance precisely; prevent unsound substitutions | `usecases/10` | — | — | — |
| UC18-type-arithmetic | Type-level arithmetic & numeric constraints | Enforce numeric constraints at compile time | `usecases/11` | — | `usecases/08` | — |
| UC19-serialization | Serialization codecs | Auto-derive serializers with full type safety | `usecases/12` | — | — | — |
| UC20-ownership-apis | Ownership-safe APIs | Encode resource lifecycle in signatures; prevent use-after-free | — | — | `usecases/02` | — |
| UC21-concurrency | Compile-time concurrency safety | Threaded code compiles only when transfer and sharing are safe | — | — | `usecases/05` | — |
| UC22-conversions | Conversion boundaries | Make cross-domain conversions explicit and type-checked | — | — | `usecases/06` | — |
| UC23-diagnostics | Trait/type error diagnostics | Map confusing compiler errors back to fixable problems | — | — | `usecases/07` | — |
| UC24-termination | Safe recursion & termination | All recursion must provably terminate | — | — | — | `usecases/07` |
| UC25-metaprogramming | Metaprogramming & syntax extension | Extend the language safely at compile time | — | — | — | `usecases/09` |
| UC26-escape-hatches | Interop & escape hatches | Opt out of safety with known boundaries (sorry, unsafe, partial, FFI) | — | — | — | `usecases/10` |
| UC27-gradual-adoption | Gradual adoption of type safety | Incrementally add types to an untyped codebase | — | `usecases/12` | — | — |
| UC28-decorator-typing | Decorator / wrapper typing | Decorators preserve or transform function signatures visibly | — | `usecases/11` | — | — |
| UC29-typed-records | Typed dictionaries & records | Dictionary-shaped data has known keys with typed values | — | `usecases/10` | — | — |
| UC30-migration | Migration from previous version | Map old idioms to new type-safe equivalents | `usecases/15` | — | — | — |

## Coverage summary

| Language | Covered | Notable gaps |
|----------|---------|-------------|
| Scala 3  | 14/30   | UC03 exhaustiveness, UC04 generic constraints, UC05 structural, UC06 immutability, UC07 callable, UC20 ownership, UC21 concurrency, UC24 termination |
| Python   | 12/30   | UC10 encapsulation, UC11 effects, UC12 compile-time, UC13 state machines, UC14 extensibility, UC17 variance, UC18 type arithmetic, UC20 ownership |
| Rust     | 8/30    | UC02 domain modeling, UC03 exhaustiveness, UC08 error handling, UC09 builder, UC10 encapsulation, UC11 effects, UC12 compile-time, UC13 state machines |
| Lean     | 9/30    | UC02 domain modeling gap (has it), UC05 structural, UC06 immutability, UC07 callable, UC08 error handling, UC13 state machines, UC19 serialization |

## Cross-cutting observations

- **UC01 (preventing invalid states)** is the only use case covered by all 4 languages — a natural starting point for any new language.
- **Rust** has the fewest use-case documents (8) but several are unique to its ownership model (UC20, UC21, UC22, UC23).
- **Scala 3** has the broadest use-case coverage (14) with several unique entries (UC13 state machines, UC15 equality, UC17 variance, UC19 serialization).
- **Python** fills a unique niche with UC05 (structural contracts), UC27 (gradual adoption), UC28 (decorator typing), UC29 (typed records).
- **Lean** is the only language covering UC24 (termination), UC25 (metaprogramming), and UC26 (escape hatches) — reflecting its theorem-prover heritage.
