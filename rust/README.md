# Rust Type System Constraint Guide

> Status: **In Progress**

This section will map Rust's type system features to the constraints they can enforce at compile time.

---

## How to Use This Guide

| If you want to... | Start here |
|-------------------|------------|
| Learn what a specific feature enforces | [Part I: Feature Catalog](#part-i-feature-catalog) |
| Enforce a specific compile-time constraint | [Part II: Use-Case Index](#part-ii-use-case-index) |

---

## Part I: Feature Catalog

| # | Document | Feature |
|---|----------|---------|
| 00 | [Reading Guide](catalog/00-overview.md) | Catalog format and conventions |
| 01 | [Ownership and Move Semantics](catalog/01-ownership-moves.md) | Move semantics and ownership transfer |
| 02 | [Borrowing and Mutability Rules](catalog/02-borrowing-mutability.md) | Reference aliasing and mutation rules |
| 03 | [Lifetimes](catalog/03-lifetimes.md) | Reference validity and lifetime relationships |
| 04 | [Structs, Enums, and Newtypes](catalog/04-structs-enums-newtypes.md) | Type modeling for state constraints |
| 05 | [Generics and Where Clauses](catalog/05-generics-where-clauses.md) | Trait-bounded generic constraints |
| 06 | [Traits and Implementations](catalog/06-traits-impls.md) | Capability contracts and impl checks |
| 07 | [Associated Types and Advanced Traits](catalog/07-associated-types-advanced-traits.md) | Related type constraints in traits |
| 08 | [Trait Objects and dyn](catalog/08-trait-objects-dyn.md) | Object-safe runtime polymorphism |
| 09 | [Inference, Aliases, and Conversion Traits](catalog/09-inference-aliases-conversions.md) | Inference and explicit conversion constraints |
| 10 | [Smart Pointers and Interior Mutability](catalog/10-smart-pointers-interior-mutability.md) | Ownership and mutation via wrappers |
| 11 | [Send and Sync](catalog/11-send-sync.md) | Concurrency marker trait constraints |
| 12 | [Const Generics](catalog/12-const-generics.md) | Value-level constraints in type parameters |
| 13 | [Coherence and Orphan Rules](catalog/13-coherence-orphan-rules.md) | Impl legality and overlap restrictions |
| 14 | [Trait Solver and Parameter Environments](catalog/14-trait-solver-param-env.md) | Obligation solving and typing environments |

---

## Part II: Use-Case Index

| # | Document | Constraint |
|---|----------|-----------|
| 00 | [Navigation Guide](usecases/00-overview.md) | Use-case format and navigation |
| 01 | [Preventing Invalid States](usecases/01-preventing-invalid-states.md) | Make invalid states unrepresentable |
| 02 | [Ownership-Safe APIs](usecases/02-ownership-safe-apis.md) | Encode ownership and borrowing in APIs |
| 03 | [Generic Capability Constraints](usecases/03-generic-capability-constraints.md) | Restrict generics by required behavior |
| 04 | [Extensible Polymorphic Interfaces](usecases/04-extensible-polymorphic-interfaces.md) | Choose static vs dynamic polymorphism safely |
| 05 | [Compile-Time Concurrency Constraints](usecases/05-compile-time-concurrency-constraints.md) | Enforce thread-safety constraints |
| 06 | [Conversion Boundaries](usecases/06-conversion-boundaries.md) | Explicit and safe type conversions |
| 07 | [Trait Impl Failure Diagnostics](usecases/07-trait-impl-failure-diagnostics.md) | Resolve trait/coherence compile errors |
| 08 | [Value-Level Invariants with Types](usecases/08-value-level-invariants-with-types.md) | Encode numeric/value invariants in types |

---

See the [main README](../README.md) for the full project overview and shared [appendix](../appendix/).
