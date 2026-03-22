# Master Technique Catalog

Language-agnostic inventory of type-safety techniques. Each entry has a stable ID used to cross-reference the per-language catalog documents.

**Legend:** language column shows the local catalog file (e.g., `catalog/04`) or `—` if not covered.

## Techniques

| ID | Technique | What it enforces | Scala 3 | Python | Rust | Lean |
|----|-----------|-----------------|---------|--------|------|------|
| T01-algebraic-data-types | ADTs, enums, inductive types & pattern matching | Closed variants; exhaustive handling; invalid states unrepresentable | `catalog/11` | `catalog/05` | `catalog/04` | `catalog/01` |
| T02-union-intersection | Union & intersection types | Type-level alternatives/combinations without class hierarchies | `catalog/01` | `catalog/02` | — | — |
| T03-newtypes-opaque | Newtypes & opaque types | Zero-cost distinct types; prevent value mix-ups | `catalog/12` | `catalog/04` | `catalog/04` | `catalog/15` |
| T04-generics-bounds | Generics & bounded polymorphism | Type parameters with bounds; generic code only compiles when constraints hold | `catalog/02`, `catalog/16` | `catalog/07`, `catalog/18` | `catalog/05` | `catalog/05` |
| T05-type-classes | Type classes, traits, protocols & implicits | Capability evidence; compiler supplies instances automatically | `catalog/05`, `catalog/06` | `catalog/09`, `catalog/10` | `catalog/06`, `catalog/07` | `catalog/04` |
| T06-derivation | Type-class derivation & auto-generation | Instances generated from compile-time structure | `catalog/08` | `catalog/06` | — | — |
| T07-structural-typing | Structural typing & refined types | Static duck typing; shape-based conformance without inheritance | `catalog/15` | `catalog/09` | — | — |
| T08-variance-subtyping | Variance & subtyping rules | Co/contravariance control; prevent unsound substitutions | `catalog/01` | `catalog/18` | — | — |
| T09-dependent-types | Dependent types & value-indexed types | Types depend on values; compiler checks index consistency | `catalog/04` | — | — | `catalog/02` |
| T10-ownership-borrowing | Ownership, borrowing & lifetimes | Prevent use-after-free, data races, dangling references | — | — | `catalog/01`, `catalog/02`, `catalog/03` | — |
| T11-concurrency-markers | Send/Sync & thread-safety markers | Compile-time control over what crosses thread boundaries | — | — | `catalog/11` | — |
| T12-effect-tracking | Effect tracking & capabilities | Track captured capabilities, side effects, purity at type level | `catalog/21` | — | — | `catalog/09` |
| T13-null-safety | Null safety & optionality | Reference types never null unless explicit; None must be handled | `catalog/19` | `catalog/01` | `catalog/04` | — |
| T14-type-narrowing | Type narrowing & exhaustiveness checking | After a check, type is narrowed; all branches must be handled | `catalog/14` | `catalog/13` | `catalog/04` | `catalog/01`, `catalog/08` |
| T15-const-generics | Const generics & value-level type parameters | Encode sizes, dimensions, capacities as type parameters | — | — | `catalog/12` | `catalog/02` |
| T16-compile-time-ops | Inline, compile-time computation & specialization | Constant folding, dead-branch elimination, compile-time checks | `catalog/17` | — | — | — |
| T17-macros-metaprogramming | Macros & metaprogramming | Type-safe compile-time code generation, syntax extension | `catalog/18` | — | — | `catalog/12` |
| T18-conversions-coercions | Type conversions & coercions | Explicit/implicit conversions; prevent silent lossy casts | `catalog/10` | — | `catalog/09` | `catalog/10` |
| T19-extension-methods | Extension methods & ad-hoc operations | Attach operations to types you don't own | `catalog/07` | — | — | — |
| T20-equality-safety | Equality & comparison constraints | Restrict `==` to semantically meaningful comparisons | `catalog/09` | — | — | — |
| T21-encapsulation | Encapsulation, visibility & module boundaries | Control what leaks across boundaries; hide representations | `catalog/13` | — | — | `catalog/15` |
| T22-callable-typing | Callable types, overloading & signature preservation | Constrain function signatures; preserve types through decorators | — | `catalog/11`, `catalog/08` | — | — |
| T23-type-aliases-inference | Type aliases, inference & gradual typing | Explicit aliases; inference; gradual adoption of type checking | — | `catalog/17`, `catalog/20` | `catalog/09` | — |
| T24-smart-pointers | Smart pointers & interior mutability | Flexible ownership wrappers preserving memory safety | — | — | `catalog/10` | — |
| T25-coherence-orphan | Coherence & orphan rules | One impl per trait-type pair; prevent conflicting cross-crate impls | — | — | `catalog/13` | — |
| T26-refinement-types | Subtypes, refinement types & annotated metadata | Attach predicates to types; construction requires evidence | — | `catalog/15` | — | `catalog/14` |
| T27-erased-phantom | Erased definitions & phantom types | Compile-time-only parameters; zero-cost type-level evidence | `catalog/20` | — | — | — |
| T28-termination-totality | Termination checking & totality | Every recursive function terminates; every input handled | — | — | — | `catalog/07`, `catalog/08` |
| T29-propositions-as-types | Propositions as types & proof terms | Encode invariants as types; compiler requires proof evidence | — | — | — | `catalog/06` |
| T30-proof-automation | Proof automation & tactics | Automated verification of proof obligations | — | — | — | `catalog/13` |
| T31-record-types | Typed dictionaries, records & data modeling | Named-field data with statically checked shapes | — | `catalog/03`, `catalog/06` | — | `catalog/03` |
| T32-immutability-markers | Final, frozen, const & immutability markers | Prevent reassignment, override, or mutation after declaration | — | `catalog/12` | — | — |
| T33-self-type | Self type & fluent returns | Methods return the receiver's type for chaining | — | `catalog/16` | — | — |
| T34-never-bottom | Never, NoReturn & bottom type | Mark unreachable code; exhaustiveness proofs | — | `catalog/14` | — | — |
| T35-universes-kinds | Universes & kind polymorphism | Type-of-types; prevent type-in-type paradoxes | `catalog/16` | — | — | `catalog/05` |
| T36-trait-objects | Trait objects & runtime polymorphism | Dynamic dispatch when concrete type unknown; object-safety rules | — | — | `catalog/08` | — |
| T37-trait-solver | Trait solver & resolution internals | Deterministic zero-cost trait resolution; guides correct bounds | — | — | `catalog/14` | — |
| T38-implicits-auto-bound | Auto-bound implicits & implicit arguments | Compiler infers context arguments; constrains to types with evidence | `catalog/05` | — | — | `catalog/11` |
| T39-notation-attributes | Notation, attributes & compiler directives | Control how checker/optimizer treats definitions | — | — | — | `catalog/16` |

## Coverage summary

| Language | Covered | Gaps (notable) |
|----------|---------|----------------|
| Scala 3  | 22/39   | T10 ownership, T11 concurrency, T15 const generics, T22 callable typing, T24 smart pointers, T28 termination, T29 propositions, T30 proof automation |
| Python   | 17/39   | T09 dependent types, T10 ownership, T11 concurrency, T12 effects, T15 const generics, T16 compile-time ops, T17 macros, T19 extensions, T21 encapsulation |
| Rust     | 15/39   | T02 union types, T06 derivation, T07 structural, T08 variance (explicit), T09 dependent, T12 effects, T16 compile-time ops, T17 macros (not cataloged separately) |
| Lean     | 15/39   | T02 union types, T10 ownership, T11 concurrency, T13 null safety, T22 callable typing, T23 inference, T32 immutability markers |
