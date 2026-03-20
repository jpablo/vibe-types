# Merged Feature Map (Draft)

This map merges the three source streams into draft catalog and use-case candidates.

## Feature Candidates

- `F01 Ownership and Move Semantics`
  - Constraint: values have a single owner; moves invalidate previous bindings.
  - Sources: `book/src/ch04-01-what-is-ownership.md`, `rust-by-example/src/scope/move.md`
  - Confidence: `high`

- `F02 Borrowing and Mutability Rules`
  - Constraint: aliasing and mutability combinations are statically restricted.
  - Sources: `book/src/ch04-02-references-and-borrowing.md`, `rust-by-example/src/scope/borrow/*`
  - Confidence: `high`

- `F03 Lifetimes`
  - Constraint: references cannot outlive data; lifetime relationships are checked.
  - Sources: `book/src/ch10-03-lifetime-syntax.md`, `rust-by-example/src/scope/lifetime.md`
  - Confidence: `high`

- `F04 Data Modeling with Structs/Enums/Newtypes`
  - Constraint: illegal states are excluded through type shape.
  - Sources: `book/src/ch05-01-defining-structs.md`, `rust-by-example/src/custom_types/*`
  - Confidence: `high`

- `F05 Generics and Where Clauses`
  - Constraint: APIs require specific type capabilities at compile time.
  - Sources: `book/src/ch10-00-generics.md`, `rust-by-example/src/generics/*`
  - Confidence: `high`

- `F06 Traits and Implementations`
  - Constraint: behavior contracts are explicit and checked for implementors.
  - Sources: `book/src/ch10-02-traits.md`, `rust-by-example/src/trait.md`
  - Confidence: `high`

- `F07 Associated Types and Advanced Traits`
  - Constraint: tie related types to implementations and reduce API ambiguity.
  - Sources: `book/src/ch20-02-advanced-traits.md`, `rust-by-example/src/generics/assoc_items/types.md`
  - Confidence: `high`

- `F08 Trait Objects and dyn`
  - Constraint: object-safe dynamic dispatch boundaries are statically enforced.
  - Sources: `book/src/ch18-02-trait-objects.md`, `rust-by-example/src/trait/dyn.md`
  - Confidence: `high`

- `F09 Type Inference, Aliases, and Conversion Traits`
  - Constraint: inferred or converted types must satisfy declared signatures/traits.
  - Sources: `rust-by-example/src/types/inference.md`, `rust-by-example/src/conversion/from_into.md`, `book/src/ch20-03-advanced-types.md`
  - Confidence: `high`

- `F10 Smart Pointers and Interior Mutability`
  - Constraint: mutation and ownership patterns are encoded by wrapper types.
  - Sources: `book/src/ch15-00-smart-pointers.md`, `book/src/ch15-05-interior-mutability.md`
  - Confidence: `high`

- `F11 Concurrency Marker Traits`
  - Constraint: cross-thread send/share guarantees are enforced by `Send`/`Sync`.
  - Sources: `book/src/ch16-04-extensible-concurrency-sync-and-send.md`
  - Confidence: `high`

- `F12 Const Generics`
  - Constraint: values at the type level constrain APIs and implementations.
  - Sources: `rust/src/doc/rustc-dev-guide/src/const-generics.md`
  - Confidence: `high`

- `F13 Coherence and Orphan Rules`
  - Constraint: trait impl overlap/orphan violations are compile-time errors.
  - Sources: `rust/src/doc/rustc-dev-guide/src/coherence.md`
  - Confidence: `high`

- `F14 Trait Solver and Param Environments`
  - Constraint: obligations are solved against parameter environments/canonical forms.
  - Sources: `rust/src/doc/rustc-dev-guide/src/type-inference.md`, `rust/src/doc/rustc-dev-guide/src/typing-parameter-envs.md`, `rust/src/doc/rustc-dev-guide/src/solve/trait-solving.md`
  - Confidence: `high`

## Use-Case Candidates

- `UC-01 Prevent Invalid States`
  - Features: `F04`, `F09`

- `UC-02 Model Ownership-Safe APIs`
  - Features: `F01`, `F02`, `F03`, `F10`

- `UC-03 Enforce Capability Constraints on Generics`
  - Features: `F05`, `F06`, `F07`

- `UC-04 Build Extensible Polymorphic Interfaces`
  - Features: `F06`, `F08`

- `UC-05 Constrain Concurrency at Compile Time`
  - Features: `F11`, `F06`, `F10`

- `UC-06 Design Conversion Boundaries`
  - Features: `F09`, `F05`

- `UC-07 Explain Trait-Impl Failures`
  - Features: `F13`, `F14`, `F06`

- `UC-08 Express Value-Level Invariants in Types`
  - Features: `F12`, `F05`

## Conflict Resolution Rule

When source wording conflicts:

1. Prefer Rust Reference (when available).
2. Then rustc-dev-guide for compiler behavior detail.
3. Then Rust Book and Rust By Example for explanatory phrasing.
