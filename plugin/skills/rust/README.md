# Rust Type System Constraint Guide

> Status: **In Progress**

This section will map Rust's type system features to the constraints they can enforce at compile time.

---

## How to Use This Guide

| If you want to... | Start here |
|-------------------|------------|
| Learn what a specific feature enforces | [Part I: Feature Catalog](#part-i-feature-catalog) |
| Enforce a specific compile-time constraint | [Part II: Use-Case Index](#part-ii-use-case-index) |

Core catalog entries include:

- A beginner mental model
- Two runnable examples
- Common compiler errors and how to interpret them

---

## Part I: Feature Catalog

| #  | Document | Feature |
|----|----------|---------|
| 00 | [Reading Guide](catalog/00-overview.md) | Catalog format and conventions |
| 01 | [Structs, Enums, and Newtypes](catalog/T01-algebraic-data-types.md) | Algebraic data types and state modeling |
| 02 | [Union & Intersection Types](catalog/T02-union-intersection.md) | Sum types via enums; intersections via trait bounds |
| 03 | [Newtype Pattern and Opaque Wrappers](catalog/T03-newtypes-opaque.md) | Distinct types from existing representations |
| 04 | [Generics and Where Clauses](catalog/T04-generics-bounds.md) | Trait-bounded generic constraints |
| 05 | [Traits and Implementations](catalog/T05-type-classes.md) | Capability contracts and impl checks |
| 06 | [Derive Macros](catalog/T06-derivation.md) | Automatic trait implementation |
| 07 | [Structural Typing](catalog/T07-structural-typing.md) | Why Rust is nominal, not structural |
| 08 | [Variance & Subtyping](catalog/T08-variance-subtyping.md) | Implicit variance over lifetimes |
| 09 | [Ownership and Move Semantics](catalog/T10-ownership-moves.md) | Move semantics and ownership transfer |
| 10 | [Borrowing and Mutability Rules](catalog/T11-borrowing-mutability.md) | Reference aliasing and mutation rules |
| 11 | [Effect Tracking](catalog/T12-effect-tracking.md) | Fallibility via `Result` and the `?` operator |
| 12 | [Null Safety via Option](catalog/T13-null-safety.md) | Absence encoded in the type system |
| 13 | [Type Narrowing via Pattern Matching](catalog/T14-type-narrowing.md) | Refining types through `match` |
| 14 | [Const Generics](catalog/T15-const-generics.md) | Value-level constraints in type parameters |
| 15 | [Compile-Time Computation](catalog/T16-compile-time-ops.md) | `const fn` and const evaluation |
| 16 | [Macros and Metaprogramming](catalog/T17-macros-metaprogramming.md) | Declarative and procedural macros |
| 17 | [Inference, Aliases, and Conversion Traits](catalog/T18-conversions-coercions.md) | Inference and explicit conversion constraints |
| 18 | [Extension Methods](catalog/T19-extension-methods.md) | Adding methods via trait implementations |
| 19 | [Equality and Comparison Safety](catalog/T20-equality-safety.md) | Opt-in `Eq`/`Ord` and total ordering |
| 20 | [Encapsulation and Visibility](catalog/T21-encapsulation.md) | Module-level access control |
| 21 | [Callable Typing](catalog/T22-callable-typing.md) | `Fn`/`FnMut`/`FnOnce` traits and function pointers |
| 22 | [Type Aliases](catalog/T23-type-aliases.md) | Naming without nominal distinction |
| 23 | [Smart Pointers and Interior Mutability](catalog/T24-smart-pointers.md) | Ownership and mutation via wrappers |
| 24 | [Coherence and Orphan Rules](catalog/T25-coherence-orphan.md) | Impl legality and overlap restrictions |
| 25 | [Refinement Types](catalog/T26-refinement-types.md) | Constructor-validated invariants |
| 26 | [PhantomData and Zero-Size Markers](catalog/T27-erased-phantom.md) | Type-level tagging without runtime cost |
| 27 | [Record Types](catalog/T31-record-types.md) | Named-field structs |
| 28 | [Immutability Markers](catalog/T32-immutability-markers.md) | `let` vs `let mut` and shared XOR mutable |
| 29 | [The Self Type](catalog/T33-self-type.md) | `Self` in traits and impls |
| 30 | [The Never Type](catalog/T34-never-bottom.md) | `!` and unreachable computations |
| 31 | [Trait Objects and `dyn`](catalog/T36-trait-objects.md) | Object-safe runtime polymorphism |
| 32 | [Trait Solver and Parameter Environments](catalog/T37-trait-solver.md) | Obligation solving and typing environments |
| 33 | [Lifetimes](catalog/T48-lifetimes.md) | Reference validity and lifetime relationships |
| 34 | [Associated Types and Advanced Traits](catalog/T49-associated-types.md) | Related type constraints in traits |
| 35 | [Send and Sync](catalog/T50-send-sync.md) | Concurrency marker trait constraints |
| 36 | [Literal Types](catalog/T52-literal-types.md) | Why Rust lacks first-class literal types |
| 37 | [Path-Dependent Types](catalog/T53-path-dependent-types.md) | Associated types as path-dependent types |
| 38 | [Functor, Applicative, Monad](catalog/T54-functor-applicative-monad.md) | `map`/`and_then` patterns on `Iterator`, `Option`, `Result` |
| 39 | [Monad Transformers](catalog/T55-monad-transformers.md) | Layered effects via middleware patterns |
| 40 | [Tagless Final](catalog/T56-tagless-final.md) | Trait-based dependency injection |
| 41 | [Typestate](catalog/T57-typestate.md) | State machines encoded in types |
| 42 | [Witness and Evidence Types](catalog/T58-witness-evidence.md) | Proof carriers via PhantomData and marker traits |
| 43 | [Existential Types](catalog/T59-existential-types.md) | `impl Trait` and hidden concrete types |
| 44 | [Linear and Affine Types](catalog/T60-linear-affine.md) | Use-once and use-at-most-once disciplines |
| 45 | [Recursive Types](catalog/T61-recursive-types.md) | Self-referential data via indirection |

---

## Part II: Use-Case Index

| #  | Document | Constraint |
|----|----------|-----------|
| 00 | [Navigation Guide](usecases/00-overview.md) | Use-case format and navigation |
| 01 | [Preventing Invalid States](usecases/UC01-invalid-states.md) | Make invalid states unrepresentable |
| 02 | [Domain Modeling](usecases/UC02-domain-modeling.md) | Newtypes and ADTs for domain concepts |
| 03 | [Exhaustive Matching](usecases/UC03-exhaustiveness.md) | Force handling of every variant |
| 04 | [Generic Capability Constraints](usecases/UC04-generic-constraints.md) | Restrict generics by required behavior |
| 05 | [Structural Contracts](usecases/UC05-structural-contracts.md) | Express requirements via trait bounds |
| 06 | [Immutability by Default](usecases/UC06-immutability.md) | Prevent accidental mutation |
| 07 | [Callable Contracts](usecases/UC07-callable-contracts.md) | Constrain closures via `Fn`/`FnMut`/`FnOnce` |
| 08 | [Error Handling](usecases/UC08-error-handling.md) | Encode fallibility with `Result` |
| 09 | [Builder and Configuration Patterns](usecases/UC09-builder-config.md) | Typestate-driven safe construction |
| 10 | [Module Encapsulation](usecases/UC10-encapsulation.md) | Hide invariants behind visibility boundaries |
| 11 | [Effect Tracking](usecases/UC11-effect-tracking.md) | Surface effects in signatures |
| 12 | [Compile-Time Programming](usecases/UC12-compile-time.md) | `const`, generics, and macros for compile-time work |
| 13 | [State Machines](usecases/UC13-state-machines.md) | Encode transitions in types (typestate) |
| 14 | [Extensible Polymorphic Interfaces](usecases/UC14-extensibility.md) | Choose static vs dynamic polymorphism safely |
| 15 | [Equality Opt-In](usecases/UC15-equality.md) | Control derivation of `Eq` and `PartialEq` |
| 16 | [Null Safety via Option](usecases/UC16-nullability.md) | Replace null with explicit `Option` |
| 17 | [Variance](usecases/UC17-variance.md) | Reason about subtyping over lifetimes and PhantomData |
| 18 | [Value-Level Invariants with Types](usecases/UC18-type-arithmetic.md) | Encode numeric/value invariants in types |
| 19 | [Serialization with Serde](usecases/UC19-serialization.md) | Derive-based safe (de)serialization |
| 20 | [Ownership-Safe APIs](usecases/UC20-ownership-apis.md) | Encode ownership and borrowing in APIs |
| 21 | [Compile-Time Concurrency Constraints](usecases/UC21-concurrency.md) | Enforce thread-safety via `Send`/`Sync` |

---

See the [main README](../../../README.md) for the full project overview and shared [docs](../../../docs/).
