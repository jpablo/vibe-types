# Scala 3 Type System Constraint Guide

An exhaustive reference mapping every Scala 3 type system feature to the constraints and properties it can enforce at compile time.

**Audience:** Experienced Scala developers who want to know *which feature solves which problem* — and vice versa.

---

## How to Use This Guide

| If you want to…                        | Start here                        |
|-----------------------------------------|-----------------------------------|
| Learn what a specific feature enables   | [Part I: Feature Catalog](#part-i-feature-catalog) |
| Enforce a specific property at compile time | [Part II: Use-Case Index](#part-ii-use-case-index) |
| See the full feature × use-case mapping | [Feature Matrix](appendix/feature-matrix.md) |
| Look up a term                          | [Glossary](appendix/glossary.md)  |

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
| 01 | [Union & Intersection Types](catalog/01-union-intersection.md) | `A \| B`, `A & B` |
| 02 | [Type Lambdas & HKTs](catalog/02-type-lambdas.md) | `[X] =>> F[X]`, higher-kinded types |
| 03 | [Match Types](catalog/03-match-types.md) | Type-level pattern matching |
| 04 | [Dependent & Polymorphic Function Types](catalog/04-dependent-polymorphic.md) | `(x: A) => x.T`, `[A] => A => A` |
| 05 | [Givens & Using Clauses](catalog/05-givens-using.md) | `given`, `using`, given imports |
| 06 | [Context Functions & Bounds](catalog/06-context-functions.md) | `T ?=> U`, context bounds |
| 07 | [Extension Methods](catalog/07-extension-methods.md) | `extension (x: T) def ...` |
| 08 | [Type Class Derivation](catalog/08-type-class-derivation.md) | `derives`, `Mirror` |
| 09 | [Multiversal Equality](catalog/09-multiversal-equality.md) | `CanEqual` |
| 10 | [Conversions & By-Name Params](catalog/10-conversions-by-name.md) | `Conversion`, by-name context params, deferred givens |
| 11 | [Enums, ADTs, GADTs](catalog/11-enums-adts-gadts.md) | `enum`, algebraic data types |
| 12 | [Opaque Types](catalog/12-opaque-types.md) | `opaque type` |
| 13 | [Open, Export, Transparent](catalog/13-open-export-transparent.md) | `open`, `export`, `transparent` |
| 14 | [Matchable & TypeTest](catalog/14-matchable-typetest.md) | `Matchable`, `TypeTest` |
| 15 | [Structural & Refined Types](catalog/15-structural-refined.md) | `Selectable`, refined types, named tuples |
| 16 | [Kind Polymorphism](catalog/16-kind-polymorphism.md) | `AnyKind` |
| 17 | [Inline & Compiletime](catalog/17-inline-compiletime.md) | `inline`, `compiletime` ops |
| 18 | [Macros](catalog/18-macros-quotes.md) | Quotes & Splices |
| 19 | [Explicit Nulls](catalog/19-explicit-nulls.md) | `T \| Null` |
| 20 | [Erased Definitions](catalog/20-erased-definitions.md) | `erased` |
| 21 | [Capture Checking](catalog/21-capture-checking.md) | `^`, `CanThrow`, pure functions |
| 22 | [Experimental & Preview](catalog/22-experimental-preview.md) | Named type args, `into`, modularity |
| 23 | [Changed & Dropped Features](catalog/23-changed-dropped.md) | Migration from Scala 2 |

---

## Part II: Use-Case Index

Organized by constraint. Each document answers: *"I want to enforce X — which features help?"*

| #  | Document | Constraint |
|----|----------|-----------|
| 00 | [Navigation Guide](usecases/00-overview.md) | How use-case docs are structured |
| 01 | [Preventing Invalid States](usecases/01-preventing-invalid-states.md) | Make illegal states unrepresentable |
| 02 | [Domain Modeling](usecases/02-domain-modeling.md) | Precise domain types |
| 03 | [Access & Encapsulation](usecases/03-access-encapsulation.md) | Hiding internals, controlling scope |
| 04 | [Effect Tracking](usecases/04-effect-tracking.md) | IO, exceptions, mutation at type level |
| 05 | [Compile-Time Programming](usecases/05-compile-time-programming.md) | Move computation to compile time |
| 06 | [Protocol & State Machines](usecases/06-protocol-state-machines.md) | Enforce call ordering, session types |
| 07 | [Extensibility](usecases/07-extensibility.md) | Open/closed extension points |
| 08 | [Equality & Comparison](usecases/08-equality-comparison.md) | Type-safe equality |
| 09 | [Nullability & Optionality](usecases/09-nullability-optionality.md) | Null safety |
| 10 | [Variance & Subtyping](usecases/10-variance-subtyping.md) | Covariance, contravariance, bounds |
| 11 | [Type-Level Arithmetic](usecases/11-type-level-arithmetic.md) | Compile-time numeric constraints |
| 12 | [Serialization & Codecs](usecases/12-serialization-codecs.md) | Derived serializers, schema safety |
| 13 | [DSL & Builder Patterns](usecases/13-dsl-builder-patterns.md) | Fluent APIs, phantom types |
| 14 | [Error Handling](usecases/14-error-handling.md) | Checked exceptions, error ADTs |
| 15 | [Migration from Scala 2](usecases/15-migration-scala2.md) | Porting implicit-heavy code |

---

## Appendix

| Document | Contents |
|----------|----------|
| [Glossary](appendix/glossary.md) | Key terminology |
| [Feature Matrix](appendix/feature-matrix.md) | Full feature × use-case cross-reference table |
| [Further Reading](appendix/further-reading.md) | Official docs, SIPs, talks, libraries |
| [Changelog](CHANGELOG.md) | Version history and update log |

---

## Scala Version Coverage

Each catalog document includes a version annotation showing which Scala 3.x version introduced the feature. The guide currently covers features through **Scala 3.8**. See the [Changelog](CHANGELOG.md) for update history.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| `[-> catalog/nn]` | Cross-reference to feature catalog entry *nn* |
| `[-> UC-nn]` | Cross-reference to use-case entry *nn* |
| ⚠️ | Gotcha or common pitfall |
| 🧪 | Experimental feature (may change) |
| ★ | Key constraint insight |
