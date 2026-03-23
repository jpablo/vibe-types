# Rust Type System Constraint Guide

> Status: **In Progress**

This section will map Rust's type system features to the constraints they can enforce at compile time.

---

## How to Use This Guide

| If you want to... | Start here |
|-------------------|------------|
| Learn what a specific feature enforces | [Part I: Feature Catalog](#part-i-feature-catalog) |
| Enforce a specific compile-time constraint | [Part II: Use-Case Index](#part-ii-use-case-index) |

Every catalog entry includes:

- A beginner mental model
- Two runnable examples
- Common compiler errors and how to interpret them

---

## Part I: Feature Catalog

| # | Document | Feature |
|---|----------|---------|
| 00 | [Reading Guide](catalog/00-overview.md) | Catalog format and conventions |
| 01 | [Ownership and Move Semantics](catalog/T10-ownership-moves.md) | Move semantics and ownership transfer |
| 02 | [Borrowing and Mutability Rules](catalog/T11-borrowing-mutability.md) | Reference aliasing and mutation rules |
| 03 | [Lifetimes](catalog/T48-lifetimes.md) | Reference validity and lifetime relationships |
| 04 | [Structs, Enums, and Newtypes](catalog/T01-algebraic-data-types.md) | Type modeling for state constraints |
| 05 | [Generics and Where Clauses](catalog/T04-generics-bounds.md) | Trait-bounded generic constraints |
| 06 | [Traits and Implementations](catalog/T05-type-classes.md) | Capability contracts and impl checks |
| 07 | [Associated Types and Advanced Traits](catalog/T49-associated-types.md) | Related type constraints in traits |
| 08 | [Trait Objects and dyn](catalog/T36-trait-objects.md) | Object-safe runtime polymorphism |
| 09 | [Inference, Aliases, and Conversion Traits](catalog/T18-conversions-coercions.md) | Inference and explicit conversion constraints |
| 10 | [Smart Pointers and Interior Mutability](catalog/T24-smart-pointers.md) | Ownership and mutation via wrappers |
| 11 | [Send and Sync](catalog/T50-send-sync.md) | Concurrency marker trait constraints |
| 12 | [Const Generics](catalog/T15-const-generics.md) | Value-level constraints in type parameters |
| 13 | [Coherence and Orphan Rules](catalog/T25-coherence-orphan.md) | Impl legality and overlap restrictions |
| 14 | [Trait Solver and Parameter Environments](catalog/T37-trait-solver.md) | Obligation solving and typing environments |

---

## Part II: Use-Case Index

| # | Document | Constraint |
|---|----------|-----------|
| 00 | [Navigation Guide](usecases/00-overview.md) | Use-case format and navigation |
| 01 | [Preventing Invalid States](usecases/UC01-invalid-states.md) | Make invalid states unrepresentable |
| 02 | [Ownership-Safe APIs](usecases/UC20-ownership-apis.md) | Encode ownership and borrowing in APIs |
| 03 | [Generic Capability Constraints](usecases/UC04-generic-constraints.md) | Restrict generics by required behavior |
| 04 | [Extensible Polymorphic Interfaces](usecases/UC14-extensibility.md) | Choose static vs dynamic polymorphism safely |
| 05 | [Compile-Time Concurrency Constraints](usecases/UC21-concurrency.md) | Enforce thread-safety constraints |
| 08 | [Value-Level Invariants with Types](usecases/UC18-type-arithmetic.md) | Encode numeric/value invariants in types |

---

See the [main README](../../../README.md) for the full project overview and shared [docs](../../../docs/).
