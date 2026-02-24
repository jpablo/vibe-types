# Feature × Use-Case Cross-Reference Matrix

This table maps every catalog feature (rows) to every use-case constraint (columns). A cell marked **X** means the feature is directly applicable to that use-case.

Read across a row to see all the problems a feature solves.
Read down a column to see all the features relevant to a constraint.

---

## Legend

| Column | Use-Case |
|--------|----------|
| UC-01 | Preventing Invalid States |
| UC-02 | Domain Modeling |
| UC-03 | Access & Encapsulation |
| UC-04 | Effect Tracking |
| UC-05 | Compile-Time Programming |
| UC-06 | Protocol & State Machines |
| UC-07 | Extensibility |
| UC-08 | Equality & Comparison |
| UC-09 | Nullability & Optionality |
| UC-10 | Variance & Subtyping |
| UC-11 | Type-Level Arithmetic |
| UC-12 | Serialization & Codecs |
| UC-13 | DSL & Builder Patterns |
| UC-14 | Error Handling |
| UC-15 | Migration from Scala 2 |

---

## Matrix

| Feature \ Use-Case                        | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 |
|-------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|----|----|-----|
| 01 Union & Intersection Types             | X  | X  |    |    |    |    |    |    | X  | X  |    |    |    | X  |     |
| 02 Type Lambdas & HKTs                    |    |    |    |    | X  |    | X  |    |    | X  |    | X  |    |    |     |
| 03 Match Types                            | X  |    |    |    | X  |    |    |    | X  |    | X  | X  |    |    |     |
| 04 Dependent & Polymorphic Function Types |    |    |    |    |    | X  |    |    |    |    |    |    | X  |    |     |
| 05 Givens & Using Clauses                 |    |    |    | X  |    |    | X  |    |    |    |    | X  | X  |    | X   |
| 06 Context Functions & Bounds             |    |    |    | X  |    | X  | X  |    |    |    |    |    | X  | X  | X   |
| 07 Extension Methods                      |    |    |    |    |    |    | X  |    |    |    |    |    | X  |    | X   |
| 08 Type Class Derivation                  |    |    |    |    |    |    | X  |    |    |    |    | X  |    |    |     |
| 09 Multiversal Equality                   |    |    |    |    |    |    |    | X  |    |    |    |    |    |    |     |
| 10 Conversions & By-Name Params           |    |    |    |    |    |    |    |    |    |    |    |    |    |    | X   |
| 11 Enums, ADTs, GADTs                     | X  | X  |    |    |    | X  |    | X  |    | X  |    | X  | X  | X  |     |
| 12 Opaque Types                           | X  | X  | X  |    |    | X  |    | X  |    | X  |    |    | X  |    |     |
| 13 Open, Export, Transparent              |    |    | X  |    |    |    | X  |    |    | X  |    |    |    |    |     |
| 14 Matchable & TypeTest                   | X  |    |    |    |    |    |    |    |    |    |    |    |    |    |     |
| 15 Structural & Refined Types             |    | X  |    |    |    |    |    |    |    |    |    |    | X  |    |     |
| 16 Kind Polymorphism                      |    |    |    |    |    |    | X  |    |    | X  |    |    |    |    |     |
| 17 Inline & Compiletime                   | X  | X  |    |    | X  |    |    |    |    |    | X  | X  | X  |    |     |
| 18 Macros (Quotes & Splices)              |    |    |    |    | X  |    |    |    |    |    | X  | X  |    |    |     |
| 19 Explicit Nulls                         |    |    |    |    |    |    |    |    | X  |    |    |    |    |    |     |
| 20 Erased Definitions                     | X  |    |    |    |    | X  |    |    |    |    |    |    |    |    |     |
| 21 Capture Checking                       |    |    |    | X  |    |    |    |    |    |    |    |    |    | X  |     |
| 22 Experimental & Preview                 |    |    |    |    |    |    | X  |    |    |    |    |    |    |    |     |
| 23 Changed & Dropped Features             |    |    |    |    |    |    |    |    |    |    |    |    |    |    | X   |

---

## Reading the Matrix

**Highest coverage features** (most use-cases addressed):
- Enums, ADTs, GADTs (scala3/catalog/11) — 8 use-cases
- Opaque Types (scala3/catalog/12) — 7 use-cases
- Inline & Compiletime (scala3/catalog/17) — 6 use-cases
- Context Functions (scala3/catalog/06) — 6 use-cases
- Givens & Using (scala3/catalog/05) — 5 use-cases

**Highest coverage use-cases** (most features applicable):
- UC-07 Extensibility — 9 features
- UC-13 DSL & Builder Patterns — 8 features
- UC-01 Preventing Invalid States — 7 features
- UC-10 Variance & Subtyping — 6 features
- UC-12 Serialization & Codecs — 6 features

**Specialized features** (narrow but deep):
- Multiversal Equality (scala3/catalog/09) → only UC-08
- Explicit Nulls (scala3/catalog/19) → only UC-09
- Capture Checking (scala3/catalog/21) → UC-04, UC-14
- Erased Definitions (scala3/catalog/20) → UC-01, UC-06

---

## Rust Matrix (Draft)

Rust currently uses 14 catalog entries and 8 use-case entries.

### Legend

| Column | Use-Case |
|--------|----------|
| UC-01 | Preventing Invalid States |
| UC-02 | Ownership-Safe APIs |
| UC-03 | Generic Capability Constraints |
| UC-04 | Extensible Polymorphic Interfaces |
| UC-05 | Compile-Time Concurrency Constraints |
| UC-06 | Conversion Boundaries |
| UC-07 | Trait Impl Failure Diagnostics |
| UC-08 | Value-Level Invariants with Types |

### Matrix

| Feature \ Use-Case                              | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 |
|-------------------------------------------------|----|----|----|----|----|----|----|----|
| 01 Ownership and Move Semantics                 |    | X  |    |    |    |    |    |    |
| 02 Borrowing and Mutability Rules               |    | X  |    |    | X  |    |    |    |
| 03 Lifetimes                                    |    | X  |    |    |    |    |    |    |
| 04 Structs, Enums, and Newtypes                 | X  |    |    |    |    |    |    |    |
| 05 Generics and Where Clauses                   |    |    | X  |    |    | X  |    | X  |
| 06 Traits and Implementations                   |    |    | X  | X  | X  |    | X  |    |
| 07 Associated Types and Advanced Traits         |    |    | X  |    |    |    |    |    |
| 08 Trait Objects and dyn                        |    |    |    | X  |    |    |    |    |
| 09 Inference, Aliases, and Conversion Traits    | X  |    |    |    |    | X  |    |    |
| 10 Smart Pointers and Interior Mutability       |    | X  |    |    | X  |    |    |    |
| 11 Send and Sync                                |    |    |    |    | X  |    |    |    |
| 12 Const Generics                               |    |    |    |    |    |    |    | X  |
| 13 Coherence and Orphan Rules                   |    |    |    |    |    |    | X  |    |
| 14 Trait Solver and Parameter Environments      |    |    |    |    |    |    | X  |    |
