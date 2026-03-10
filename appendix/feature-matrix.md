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

## Scala Matrix

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

---

## Python Matrix

Python uses 20 catalog entries and 12 use-case entries. Constraints are enforced by static type checkers (mypy/pyright) rather than a compiler.

### Legend

| Column | Use-Case |
|--------|----------|
| UC-01 | Preventing Invalid States |
| UC-02 | Domain Modeling |
| UC-03 | Type Narrowing and Exhaustiveness |
| UC-04 | Generic Constraints |
| UC-05 | Structural Contracts |
| UC-06 | Immutability and Finality |
| UC-07 | API Contracts and Callable Typing |
| UC-08 | Error Handling with Types |
| UC-09 | Configuration and Builder Patterns |
| UC-10 | Typed Dictionaries and Records |
| UC-11 | Decorator Typing |
| UC-12 | Gradual Adoption |

### Matrix

| Feature \ Use-Case                              | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 |
|-------------------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
| 01 Basic Annotations, Optional, None            | X  | X  | X  |    |    |    |    | X  |    |    |    | X  |
| 02 Union and Literal Types                      | X  | X  | X  |    |    |    |    | X  |    | X  |    |    |
| 03 TypedDict                                    |    | X  |    |    |    |    |    |    | X  | X  |    |    |
| 04 NewType                                      | X  | X  |    |    |    |    |    |    |    |    |    |    |
| 05 Enums with Static Typing                     | X  | X  | X  |    |    |    |    | X  |    |    |    |    |
| 06 Dataclasses and Typed Data Modeling          |    | X  |    |    |    | X  |    |    | X  |    |    |    |
| 07 Generics, TypeVar, Bounded Types             |    |    |    | X  | X  |    | X  |    |    |    | X  |    |
| 08 ParamSpec and TypeVarTuple                   |    |    |    |    |    |    | X  |    |    |    | X  |    |
| 09 Protocol (Structural Subtyping)              |    |    |    | X  | X  |    | X  |    |    |    |    |    |
| 10 Abstract Base Classes                        |    |    |    | X  | X  |    |    |    |    |    |    |    |
| 11 Callable Types and @overload                 |    |    |    |    |    |    | X  |    | X  |    | X  |    |
| 12 Final and ClassVar                           |    |    |    |    |    | X  |    |    |    |    |    |    |
| 13 TypeGuard, TypeIs, and Type Narrowing        |    |    | X  |    |    |    |    | X  |    |    |    |    |
| 14 Never and NoReturn                           |    |    | X  |    |    |    |    | X  |    |    |    |    |
| 15 Annotated and Type Metadata                  |    | X  |    |    |    |    |    |    | X  | X  |    |    |
| 16 Self Type                                    |    |    |    |    |    |    | X  |    | X  |    |    |    |
| 17 TypeAlias and the `type` Statement           |    |    |    |    |    |    |    |    |    |    |    | X  |
| 18 Generic Classes and Variance                 |    |    |    | X  |    |    |    |    |    |    | X  |    |
| 19 Unpack and **kwargs Typing                   |    |    |    |    |    |    |    |    | X  | X  |    |    |
| 20 Type Inference, Gradual Typing, Any          |    |    |    |    |    |    |    |    |    |    |    | X  |

### Reading the Python Matrix

**Highest coverage features** (most use-cases addressed):
- Basic Annotations, Optional, None (python/catalog/01) — 5 use-cases
- Union and Literal Types (python/catalog/02) — 5 use-cases
- Enums with Static Typing (python/catalog/05) — 4 use-cases
- Generics, TypeVar, Bounded Types (python/catalog/07) — 4 use-cases

**Highest coverage use-cases** (most features applicable):
- UC-02 Domain Modeling — 7 features
- UC-07 API Contracts and Callable Typing — 5 features
- UC-04 Generic Constraints — 4 features
- UC-01 Preventing Invalid States — 4 features

**Specialized features** (narrow but deep):
- Final and ClassVar (python/catalog/12) → only UC-06
- TypeAlias and `type` Statement (python/catalog/17) → only UC-12
- Type Inference, Gradual Typing, Any (python/catalog/20) → only UC-12

---

## Lean 4 Matrix

Lean 4 uses 16 catalog entries and 10 use-case entries. Lean is built on dependent type theory; the compiler is both a type checker and a proof checker.

### Legend

| Column | Use-Case |
|--------|----------|
| UC-01 | Preventing Invalid States |
| UC-02 | Domain Modeling with Dependent Types |
| UC-03 | Totality and Exhaustiveness |
| UC-04 | Compile-Time Invariants |
| UC-05 | Safe Effectful Programming |
| UC-06 | Generic Programming with Type Classes |
| UC-07 | Safe Recursion and Termination |
| UC-08 | Encapsulation and Module Boundaries |
| UC-09 | Metaprogramming and Syntax Extension |
| UC-10 | Interop and Escape Hatches |

### Matrix

| Feature \ Use-Case                        | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 |
|-------------------------------------------|----|----|----|----|----|----|----|----|----|----|
| 01 Inductive Types & Pattern Matching     | X  | X  | X  |    |    |    |    |    |    |    |
| 02 Dependent Types & Pi Types             | X  | X  |    | X  |    |    |    |    |    |    |
| 03 Structures & Inheritance               |    | X  |    |    |    |    |    | X  |    |    |
| 04 Type Classes & Instances               |    |    |    |    |    | X  |    |    |    |    |
| 05 Universes & Universe Polymorphism      |    |    |    |    |    | X  |    |    |    |    |
| 06 Propositions as Types                  | X  |    |    | X  |    |    |    |    |    |    |
| 07 Termination Checking                   |    |    | X  |    |    |    | X  |    |    |    |
| 08 Totality & partial                     |    |    | X  |    |    |    | X  |    |    | X  |
| 09 Monads, Do-Notation, IO               |    |    |    |    | X  |    |    |    |    |    |
| 10 Coercions & Coe                        |    | X  |    |    |    | X  |    |    |    |    |
| 11 Auto-Bound Implicits & Instances       |    |    |    |    |    | X  |    |    |    |    |
| 12 Macros & Elaboration                   |    |    |    |    |    |    |    |    | X  |    |
| 13 Proof Automation (simp, decide, omega) |    |    |    | X  |    |    | X  |    |    |    |
| 14 Subtypes & Refinement Types            | X  | X  |    | X  |    |    |    |    |    |    |
| 15 Opaque Definitions & Reducibility      |    |    |    |    |    |    |    | X  |    |    |
| 16 Notation, Attributes, Options          |    |    |    |    |    |    |    | X  | X  |    |

### Reading the Lean 4 Matrix

**Highest coverage features** (most use-cases addressed):
- Inductive Types & Pattern Matching (lean/catalog/01) — 3 use-cases
- Dependent Types & Pi Types (lean/catalog/02) — 3 use-cases
- Subtypes & Refinement Types (lean/catalog/14) — 3 use-cases
- Totality & partial (lean/catalog/08) — 3 use-cases

**Highest coverage use-cases** (most features applicable):
- UC-06 Generic Programming with Type Classes — 4 features
- UC-01 Preventing Invalid States — 4 features
- UC-04 Compile-Time Invariants — 3 features
- UC-02 Domain Modeling with Dependent Types — 4 features

**Specialized features** (narrow but deep):
- Monads, Do-Notation, IO (lean/catalog/09) → only UC-05
- Type Classes & Instances (lean/catalog/04) → only UC-06
- Universes & Universe Polymorphism (lean/catalog/05) → only UC-06
- Macros & Elaboration (lean/catalog/12) → only UC-09
