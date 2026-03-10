---
name: scala3
description: Scala 3 compile-time safety techniques — opaque types, enums/ADTs/GADTs, givens, match types, inline, capture checking. Use when writing type-safe Scala 3, choosing type system features, or debugging compiler errors.
version: 1.0.0
---

# Scala 3 — Compile-Time Safety Techniques

> **Base path:** `${CLAUDE_PLUGIN_ROOT}/scala3`

## Full catalog (type system features → constraints they enforce)

- **Union & intersection types** — express alternatives without common supertype (`A | B`); combine capabilities (`A & B`) → `catalog/01-union-intersection.md`
- **Type lambdas** — abstract over type constructors inline; partially apply binary constructors for type-class shapes → `catalog/02-type-lambdas.md`
- **Match types** — compute types from types via pattern matching; type-level conditional logic → `catalog/03-match-types.md`
- **Dependent & polymorphic function types** — return type depends on argument value/type; first-class polymorphic values → `catalog/04-dependent-polymorphic.md`
- **Givens & using clauses** — principled type-class dispatch; compiler supplies evidence automatically → `catalog/05-givens-using.md`
- **Context functions & context bounds** — abstract over contextual dependencies as types; lightweight capability annotation → `catalog/06-context-functions.md`
- **Extension methods** — attach operations to types you don't own; conditional syntax via type-class evidence → `catalog/07-extension-methods.md`
- **Type-class derivation** — auto-generate instances for any ADT from compile-time structure → `catalog/08-type-class-derivation.md`
- **Multiversal equality** — restrict `==` so only semantically meaningful comparisons compile → `catalog/09-multiversal-equality.md`
- **Conversions, by-name params, deferred givens** — explicit opt-in conversions; break circular given dependencies → `catalog/10-conversions-by-name.md`
- **Enums, ADTs, GADTs** — closed variant sets with exhaustive matching; per-branch type refinement → `catalog/11-enums-adts-gadts.md`
- **Opaque types** — zero-cost distinct types sharing same representation; prevent value mix-ups without boxing → `catalog/12-opaque-types.md`
- **open, export, transparent** — control extensibility; delegate via composition; suppress traits from inferred types → `catalog/13-open-export-transparent.md`
- **Matchable & TypeTest** — prevent pattern matching from breaking type abstractions; sound runtime type tests → `catalog/14-matchable-typetest.md`
- **Structural & refined types, named tuples** — statically-checked duck typing; lightweight records without case classes → `catalog/15-structural-refined.md`
- **Kind polymorphism** — type parameters ranging over any kind; universal type tags → `catalog/16-kind-polymorphism.md`
- **Inline & compile-time ops** — constant folding, dead-branch elimination, compile-time specialization → `catalog/17-inline-compiletime.md`
- **Macros (quotes & splices)** — type-safe compile-time code generation and AST transformation → `catalog/18-macros-quotes.md`
- **Explicit nulls** — reference types never hold null unless explicitly `T | Null` → `catalog/19-explicit-nulls.md`
- **Erased definitions** — compile-time-only parameters; zero-cost type-level evidence → `catalog/20-erased-definitions.md`
- **Capture checking & CanThrow** — track captured capabilities; effect tracking and purity enforcement at type level → `catalog/21-capture-checking.md`
- **Experimental: named type args, `into`, modularity** — selective type parameter binding; fine-grained conversion control → `catalog/22-experimental-preview.md`
- **Changed & dropped features** — more predictable inference and resolution; removed unsound Scala 2 features → `catalog/23-changed-dropped.md`

## Use cases (problem → which features help)

- **Preventing invalid states** — make impossible states impossible via ADTs, opaque types, phantom types, GADTs → `usecases/01-preventing-invalid-states.md`
- **Domain modeling** — newtypes, smart constructors, closed state hierarchies, capability composition → `usecases/02-domain-modeling.md`
- **Access & encapsulation** — hide representations, selective delegation, controlled inheritance, scope qualifiers → `usecases/03-access-encapsulation.md`
- **Effect tracking** — checked exceptions, capability passing, Reader/Writer patterns, tagless final → `usecases/04-effect-tracking.md`
- **Compile-time programming** — inline branching, type-level arithmetic, macros for validation and codegen → `usecases/05-compile-time-programming.md`
- **Protocol & state machines** — enforce valid call ordering at compile time; phantom builders, GADT protocols → `usecases/06-protocol-state-machines.md`
- **Extensibility** — type-class pattern, extension methods, export for delegation, open modifier → `usecases/07-extensibility.md`
- **Equality & comparison** — prevent nonsensical equality checks; multiversal equality, CanEqual derivation → `usecases/08-equality-comparison.md`
- **Nullability & optionality** — eliminate NPEs through explicit nulls, union types, match types → `usecases/09-nullability-optionality.md`
- **Variance & subtyping** — control covariance/contravariance precisely; opaque types breaking subtyping → `usecases/10-variance-subtyping.md`
- **Type-level arithmetic** — enforce numeric constraints at compile time; compiletime.ops, match type recursion → `usecases/11-type-level-arithmetic.md`
- **Serialization codecs** — auto-derive serializers with full type safety; Mirror inspection, schema validation → `usecases/12-serialization-codecs.md`
- **DSL & builder patterns** — type-safe DSLs where invalid compositions are compile errors; context functions, phantom builders → `usecases/13-dsl-builder-patterns.md`
- **Error handling** — CanThrow capabilities, error ADTs, union type channels → `usecases/14-error-handling.md`
- **Migration from Scala 2** — map implicits to givens, implicit classes to extensions, conversions to Conversion type class → `usecases/15-migration-scala2.md`
