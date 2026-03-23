---
name: vibe-types:scala
description: Scala 3 compile-time safety techniques — opaque types, enums/ADTs/GADTs, givens, match types, inline, capture checking. Use this skill whenever the user writes Scala 3 code, mentions type safety, asks about compiler errors, discusses ADTs, opaque types, given instances, context functions, match types, extension methods, or any Scala type system feature. Also use when porting type patterns from Rust, Python, or Haskell to Scala 3.
version: 0.2.0
---

# Scala 3 — Compile-Time Safety Techniques

> **Base path:** `${CLAUDE_PLUGIN_ROOT}/skills/scala3`

## Full catalog (type system features → constraints they enforce)

- **Union & intersection types** — express alternatives without common supertype (`A | B`); combine capabilities (`A & B`) → `catalog/T02-union-intersection.md`
- **Type lambdas** — abstract over type constructors inline; partially apply binary constructors for type-class shapes → `catalog/T40-type-lambdas.md`
- **Match types** — compute types from types via pattern matching; type-level conditional logic → `catalog/T41-match-types.md`
- **Givens & using clauses** — principled type-class dispatch; compiler supplies evidence automatically → `catalog/T05-type-classes.md`
- **Context functions & context bounds** — abstract over contextual dependencies as types; lightweight capability annotation → `catalog/T42-context-functions.md`
- **Extension methods** — attach operations to types you don't own; conditional syntax via type-class evidence → `catalog/T19-extension-methods.md`
- **Type-class derivation** — auto-generate instances for any ADT from compile-time structure → `catalog/T06-derivation.md`
- **Multiversal equality** — restrict `==` so only semantically meaningful comparisons compile → `catalog/T20-equality-safety.md`
- **Conversions, by-name params, deferred givens** — explicit opt-in conversions; break circular given dependencies → `catalog/T18-conversions-coercions.md`
- **Enums, ADTs, GADTs** — closed variant sets with exhaustive matching; per-branch type refinement → `catalog/T01-algebraic-data-types.md`
- **Opaque types** — zero-cost distinct types sharing same representation; prevent value mix-ups without boxing → `catalog/T03-newtypes-opaque.md`
- **open, export, transparent** — control extensibility; delegate via composition; suppress traits from inferred types → `catalog/T21-encapsulation.md`
- **Matchable & TypeTest** — prevent pattern matching from breaking type abstractions; sound runtime type tests → `catalog/T14-type-narrowing.md`
- **Structural & refined types, named tuples** — statically-checked duck typing; lightweight records without case classes → `catalog/T07-structural-typing.md`
- **Kind polymorphism** — type parameters ranging over any kind; universal type tags → `catalog/T35-universes-kinds.md`
- **Inline & compile-time ops** — constant folding, dead-branch elimination, compile-time specialization → `catalog/T16-compile-time-ops.md`
- **Macros (quotes & splices)** — type-safe compile-time code generation and AST transformation → `catalog/T17-macros-metaprogramming.md`
- **Explicit nulls** — reference types never hold null unless explicitly `T | Null` → `catalog/T13-null-safety.md`
- **Erased definitions** — compile-time-only parameters; zero-cost type-level evidence → `catalog/T27-erased-phantom.md`
- **Capture checking & CanThrow** — track captured capabilities; effect tracking and purity enforcement at type level → `catalog/T12-effect-tracking.md`
- **Experimental: named type args, `into`, modularity** — selective type parameter binding; fine-grained conversion control → `catalog/T43-experimental-preview.md`
- **Changed & dropped features** — more predictable inference and resolution; removed unsound Scala 2 features → `catalog/T44-changed-dropped.md`
- **Refinement types** — value-level predicates enforced at compile time via Iron or refined libraries → `catalog/T26-refinement-types.md`
- **Generics & bounded polymorphism** — upper/lower bounds, context bounds, F-bounded polymorphism → `catalog/T04-generics-bounds.md`
- **Variance & subtyping** — covariant `+A`, contravariant `-A`, invariant; Liskov at the type level → `catalog/T08-variance-subtyping.md`
- **Callable types & overloading** — function types, SAM types, eta-expansion, method overloading → `catalog/T22-callable-typing.md`
- **Type aliases** — transparent aliases, parameterized aliases, type members, path-dependent types → `catalog/T23-type-aliases.md`
- **Record types & data modeling** — case classes, named tuples, product types with auto-derived methods → `catalog/T31-record-types.md`
- **Self types** — self-type annotations (`self: T =>`), capability requirements without inheritance → `catalog/T33-self-type.md`
- **Nothing & bottom type** — universal subtype, `throw`, `???`, empty collections, covariant widening → `catalog/T34-never-bottom.md`
- **Singleton types & compile-time value parameters** — literal types, `constValue`, `compiletime.ops`; encode sizes/dimensions in types → `catalog/T15-const-generics.md`
- **Literal types** — every literal has a singleton type; foundation for type-level computation and value discrimination → `catalog/T52-literal-types.md`
- **Path-dependent types** — type members, instance-dependent types (`x.Inner`), abstract type members → `catalog/T53-path-dependent-types.md`
- **Immutability markers** — `val`, `final`, `sealed`, immutable collections; immutability is the default → `catalog/T32-immutability-markers.md`
- **Trait-based dynamic dispatch** — traits + abstract classes for runtime polymorphism; JVM vtable → `catalog/T36-trait-objects.md`
- **Given/implicit resolution** — Scala's trait solver: search scopes, priority, divergence detection → `catalog/T37-trait-solver.md`
- **Associated types** — abstract type members in traits; alternative to type parameters → `catalog/T49-associated-types.md`
- **Annotations & compiler directives** — `@inline`, `@tailrec`, `@targetName`, `@deprecated` → `catalog/T39-notation-attributes.md`
- **Dependent types** *(via path-dependent + match types)* — approximate value-indexed patterns → `catalog/T09-dependent-types.md`
- **Coherence & instance scoping** *(via given import rules)* — no orphan rule; import-based visibility → `catalog/T25-coherence-orphan.md`

- **Functor / Applicative / Monad** — map, flatMap, pure; compositional effect chaining via cats → `catalog/T54-functor-applicative-monad.md`
- **Monad transformers** — EitherT, StateT, ReaderT; compose effects in a stack → `catalog/T55-monad-transformers.md`
- **Tagless final** — decouple program description from interpretation; swap runtimes → `catalog/T56-tagless-final.md`
- **Typestate pattern** — phantom types track state; invalid transitions don't compile → `catalog/T57-typestate.md`
- **Witness & evidence types** — =:=, <:<, given evidence; compiler proves preconditions → `catalog/T58-witness-evidence.md`
- **Existential types** — abstract type members, wildcard types; hide concrete types → `catalog/T59-existential-types.md`
- **Recursive types** — sealed enum/trait hierarchies defined in terms of themselves → `catalog/T61-recursive-types.md`
## Use cases (problem → which features help)

- **Preventing invalid states** — make impossible states impossible via ADTs, opaque types, phantom types, GADTs → `usecases/UC01-invalid-states.md`
- **Domain modeling** — newtypes, smart constructors, closed state hierarchies, capability composition → `usecases/UC02-domain-modeling.md`
- **Access & encapsulation** — hide representations, selective delegation, controlled inheritance, scope qualifiers → `usecases/UC10-encapsulation.md`
- **Effect tracking** — checked exceptions, capability passing, Reader/Writer patterns, tagless final → `usecases/UC11-effect-tracking.md`
- **Compile-time programming** — inline branching, type-level arithmetic, macros for validation and codegen → `usecases/UC12-compile-time.md`
- **Protocol & state machines** — enforce valid call ordering at compile time; phantom builders, GADT protocols → `usecases/UC13-state-machines.md`
- **Extensibility** — type-class pattern, extension methods, export for delegation, open modifier → `usecases/UC14-extensibility.md`
- **Equality & comparison** — prevent nonsensical equality checks; multiversal equality, CanEqual derivation → `usecases/UC15-equality.md`
- **Nullability & optionality** — eliminate NPEs through explicit nulls, union types, match types → `usecases/UC16-nullability.md`
- **Variance & subtyping** — control covariance/contravariance precisely; opaque types breaking subtyping → `usecases/UC17-variance.md`
- **Type-level arithmetic** — enforce numeric constraints at compile time; compiletime.ops, match type recursion → `usecases/UC18-type-arithmetic.md`
- **Serialization codecs** — auto-derive serializers with full type safety; Mirror inspection, schema validation → `usecases/UC19-serialization.md`
- **DSL & builder patterns** — type-safe DSLs where invalid compositions are compile errors; context functions, phantom builders → `usecases/UC09-builder-config.md`
- **Error handling** — CanThrow capabilities, error ADTs, union type channels → `usecases/UC08-error-handling.md`
