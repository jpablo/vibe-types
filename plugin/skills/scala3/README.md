# Scala 3 Type System Constraint Guide

An exhaustive reference mapping every Scala 3 type system feature to the constraints and properties it can enforce at compile time.

**Audience:** Experienced Scala developers who want to know *which feature solves which problem* — and vice versa.

---

## How to Use This Guide

| If you want to…                        | Start here                        |
|-----------------------------------------|-----------------------------------|
| Learn what a specific feature enables   | [Part I: Feature Catalog](#part-i-feature-catalog) |
| Enforce a specific property at compile time | [Part II: Use-Case Index](#part-ii-use-case-index) |
| See the full feature × use-case mapping | [Techniques](../../../taxonomy/techniques.md) |

---

## Cross-Reference Notation

Throughout the guide:

- **`[-> catalog/nn]`** links to a Feature Catalog document (e.g., `[-> catalog/12]` → Opaque Types)
- **`[-> UC-nn]`** links to a Use-Case Index document (e.g., `[-> UC-04]` → Effect Tracking)
- Each catalog doc ends with use-case cross-refs; each use-case doc links back to relevant features.

---

## Part I: Feature Catalog

Organized by feature. Each document answers: *"What can I enforce with this feature?"*

| #  | Document | Feature |
|----|----------|---------|
| 00 | [Reading Guide](catalog/00-overview.md) | How catalog docs are structured |
| 01 | [Union & Intersection Types](catalog/T02-union-intersection.md) | `A \| B`, `A & B` |
| 02 | [Type Lambdas & HKTs](catalog/T40-type-lambdas.md) | `[X] =>> F[X]`, higher-kinded types |
| 03 | [Match Types](catalog/T41-match-types.md) | Type-level pattern matching |
| 04 | [Dependent & Polymorphic Function Types](catalog/T09-dependent-types.md) | `(x: A) => x.T`, `[A] => A => A` |
| 05 | [Givens & Using Clauses](catalog/T05-type-classes.md) | `given`, `using`, given imports |
| 06 | [Context Functions & Bounds](catalog/T42-context-functions.md) | `T ?=> U`, context bounds |
| 07 | [Extension Methods](catalog/T19-extension-methods.md) | `extension (x: T) def ...` |
| 08 | [Type Class Derivation](catalog/T06-derivation.md) | `derives`, `Mirror` |
| 09 | [Multiversal Equality](catalog/T20-equality-safety.md) | `CanEqual` |
| 10 | [Conversions & By-Name Params](catalog/T18-conversions-coercions.md) | `Conversion`, by-name context params, deferred givens |
| 11 | [Enums, ADTs, GADTs](catalog/T01-algebraic-data-types.md) | `enum`, algebraic data types |
| 12 | [Opaque Types](catalog/T03-newtypes-opaque.md) | `opaque type` |
| 13 | [Open, Export, Transparent](catalog/T21-encapsulation.md) | `open`, `export`, `transparent` |
| 14 | [Matchable & TypeTest](catalog/T14-type-narrowing.md) | `Matchable`, `TypeTest` |
| 15 | [Structural & Refined Types](catalog/T07-structural-typing.md) | `Selectable`, refined types, named tuples |
| 16 | [Kind Polymorphism](catalog/T35-universes-kinds.md) | `AnyKind` |
| 17 | [Inline & Compiletime](catalog/T16-compile-time-ops.md) | `inline`, `compiletime` ops |
| 18 | [Macros](catalog/T17-macros-metaprogramming.md) | Quotes & Splices |
| 19 | [Explicit Nulls](catalog/T13-null-safety.md) | `T \| Null` |
| 20 | [Erased Definitions](catalog/T27-erased-phantom.md) | `erased` |
| 21 | [Capture Checking](catalog/T12-effect-tracking.md) | `^`, `CanThrow`, pure functions |
| 22 | [Experimental & Preview](catalog/T43-experimental-preview.md) | Named type args, `into`, modularity |
| 23 | [Changed & Dropped Features](catalog/T44-changed-dropped.md) | Migration from Scala 2 |

---

## Part II: Use-Case Index

Organized by constraint. Each document answers: *"I want to enforce X — which features help?"*

| #  | Document | Constraint |
|----|----------|-----------|
| 00 | [Navigation Guide](usecases/00-overview.md) | How use-case docs are structured |
| 01 | [Preventing Invalid States](usecases/UC01-invalid-states.md) | Make illegal states unrepresentable |
| 02 | [Domain Modeling](usecases/UC02-domain-modeling.md) | Precise domain types |
| 03 | [Access & Encapsulation](usecases/UC10-encapsulation.md) | Hiding internals, controlling scope |
| 04 | [Effect Tracking](usecases/UC11-effect-tracking.md) | IO, exceptions, mutation at type level |
| 05 | [Compile-Time Programming](usecases/UC12-compile-time.md) | Move computation to compile time |
| 06 | [Protocol & State Machines](usecases/UC13-state-machines.md) | Enforce call ordering, session types |
| 07 | [Extensibility](usecases/UC14-extensibility.md) | Open/closed extension points |
| 08 | [Equality & Comparison](usecases/UC15-equality.md) | Type-safe equality |
| 09 | [Nullability & Optionality](usecases/UC16-nullability.md) | Null safety |
| 10 | [Variance & Subtyping](usecases/UC17-variance.md) | Covariance, contravariance, bounds |
| 11 | [Type-Level Arithmetic](usecases/UC18-type-arithmetic.md) | Compile-time numeric constraints |
| 12 | [Serialization & Codecs](usecases/UC19-serialization.md) | Derived serializers, schema safety |
| 13 | [DSL & Builder Patterns](usecases/UC09-builder-config.md) | Fluent APIs, phantom types |
| 14 | [Error Handling](usecases/UC08-error-handling.md) | Checked exceptions, error ADTs |
| 15 | [Migration from Scala 2](usecases/UC30-migration.md) | Porting implicit-heavy code |

---

## Scala Version Coverage

Each catalog document includes a version annotation showing which Scala 3.x version introduced the feature. The guide currently covers features through **Scala 3.8**. See the [Changelog](../../../CHANGELOG.md) for update history.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| `[-> catalog/nn]` | Cross-reference to feature catalog entry *nn* |
| `[-> UC-nn]` | Cross-reference to use-case entry *nn* |
| ⚠️ | Gotcha or common pitfall |
| 🧪 | Experimental feature (may change) |
| ★ | Key constraint insight |
