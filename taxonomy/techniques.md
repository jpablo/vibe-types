# Master Technique Catalog

Language-agnostic inventory of type-safety techniques. Each entry has a stable ID that matches the filename used across all language catalogs: `catalog/<ID>.md`.

A `✓` means the language has this file; `—` means it's a gap.

## Techniques

| ID | Technique | What it enforces | Scala 3 | Python | Rust | Lean |
|----|-----------|-----------------|:-------:|:------:|:----:|:----:|
| T01-algebraic-data-types | ADTs, enums, inductive types & pattern matching | Closed variants; exhaustive handling; invalid states unrepresentable | ✓ | ✓ | ✓ | ✓ |
| T02-union-intersection | Union & intersection types | Type-level alternatives/combinations without class hierarchies | ✓ | ✓ | — | — |
| T03-newtypes-opaque | Newtypes & opaque types | Zero-cost distinct types; prevent value mix-ups | ✓ | ✓ | — | — |
| T04-generics-bounds | Generics & bounded polymorphism | Type parameters with bounds; generic code only compiles when constraints hold | — | ✓ | ✓ | — |
| T05-type-classes | Type classes, traits, protocols & abstract bases | Capability evidence; compiler supplies instances automatically | ✓ | ✓ | ✓ | ✓ |
| T06-derivation | Type-class derivation & auto-generation | Instances generated from compile-time structure | ✓ | ✓ | — | — |
| T07-structural-typing | Structural typing & refined types | Static duck typing; shape-based conformance without inheritance | ✓ | ✓ | — | — |
| T08-variance-subtyping | Variance & subtyping rules | Co/contravariance control; prevent unsound substitutions | — | ✓ | — | — |
| T09-dependent-types | Dependent types & value-indexed types | Types depend on values; compiler checks index consistency | ✓ | — | — | ✓ |
| T10-ownership-moves | Ownership & move semantics | Prevent use-after-free and double-free; deterministic cleanup | — | — | ✓ | — |
| T11-borrowing-mutability | Borrowing & mutability rules | Eliminate data races via aliasing rules (`&T` xor `&mut T`) | — | — | ✓ | — |
| T12-effect-tracking | Effect tracking & capabilities | Track captured capabilities, side effects, purity at type level | ✓ | — | — | ✓ |
| T13-null-safety | Null safety & optionality | Reference types never null unless explicit; None must be handled | ✓ | ✓ | — | — |
| T14-type-narrowing | Type narrowing & exhaustiveness checking | After a check, type is narrowed; all branches must be handled | ✓ | ✓ | — | — |
| T15-const-generics | Const generics & value-level type parameters | Encode sizes, dimensions, capacities as type parameters | — | — | ✓ | — |
| T16-compile-time-ops | Inline & compile-time computation | Constant folding, dead-branch elimination, compile-time specialization | ✓ | — | — | — |
| T17-macros-metaprogramming | Macros & metaprogramming | Type-safe compile-time code generation, syntax extension | ✓ | — | — | ✓ |
| T18-conversions-coercions | Type conversions & coercions | Explicit/implicit conversions; prevent silent lossy casts | ✓ | — | ✓ | ✓ |
| T19-extension-methods | Extension methods | Attach operations to types you don't own | ✓ | — | — | — |
| T20-equality-safety | Equality & comparison constraints | Restrict `==` to semantically meaningful comparisons | ✓ | — | — | — |
| T21-encapsulation | Encapsulation, visibility & module boundaries | Control what leaks across boundaries; hide representations | ✓ | — | — | ✓ |
| T22-callable-typing | Callable types, overloading & signature preservation | Constrain function signatures; preserve types through decorators | — | ✓ | — | — |
| T23-type-aliases | Type aliases & the `type` statement | Explicit alias declarations; lazy evaluation and forward references | — | ✓ | — | — |
| T24-smart-pointers | Smart pointers & interior mutability | Flexible ownership wrappers preserving memory safety | — | — | ✓ | — |
| T25-coherence-orphan | Coherence & orphan rules | One impl per trait-type pair; prevent conflicting cross-crate impls | — | — | ✓ | — |
| T26-refinement-types | Subtypes, refinement types & annotated metadata | Attach predicates to types; construction requires evidence | — | ✓ | — | ✓ |
| T27-erased-phantom | Erased definitions & phantom types | Compile-time-only parameters; zero-cost type-level evidence | ✓ | — | — | — |
| T28-termination | Termination checking & well-founded recursion | Every recursive function must provably terminate | — | — | — | ✓ |
| T29-propositions-as-types | Propositions as types & proof terms | Encode invariants as types; compiler requires proof evidence | — | — | — | ✓ |
| T30-proof-automation | Proof automation & tactics | Automated verification of proof obligations | — | — | — | ✓ |
| T31-record-types | Typed dictionaries, records & structures | Named-field data with statically checked shapes | — | ✓ | — | ✓ |
| T32-immutability-markers | Final, frozen & immutability markers | Prevent reassignment, override, or mutation after declaration | — | ✓ | — | — |
| T33-self-type | Self type & fluent returns | Methods return the receiver's type for chaining | — | ✓ | — | — |
| T34-never-bottom | Never, NoReturn & bottom type | Mark unreachable code; exhaustiveness proofs | — | ✓ | — | — |
| T35-universes-kinds | Universes & kind polymorphism | Type-of-types; prevent type-in-type paradoxes | ✓ | — | — | ✓ |
| T36-trait-objects | Trait objects & runtime polymorphism | Dynamic dispatch when concrete type unknown; object-safety rules | — | — | ✓ | — |
| T37-trait-solver | Trait solver & resolution internals | Deterministic zero-cost trait resolution; guides correct bounds | — | — | ✓ | — |
| T38-implicits-auto-bound | Auto-bound implicits & implicit arguments | Compiler infers context arguments; constrains to types with evidence | — | — | — | ✓ |
| T39-notation-attributes | Notation, attributes & compiler directives | Control how checker/optimizer treats definitions | — | — | — | ✓ |
| T40-type-lambdas | Type lambdas & higher-kinded abstraction | Abstract over type constructors; partially apply binary constructors | ✓ | — | — | — |
| T41-match-types | Match types & type-level pattern matching | Compute types from types via pattern matching; type-level conditionals | ✓ | — | — | — |
| T42-context-functions | Context functions & context bounds | Abstract over contextual dependencies as types | ✓ | — | — | — |
| T43-experimental-preview | Experimental features & preview | Named type args, `into`, modularity — not yet stable | ✓ | — | — | — |
| T44-changed-dropped | Changed & dropped features | Removed unsound features; more predictable inference | ✓ | — | — | — |
| T45-paramspec-variadic | ParamSpec & TypeVarTuple | Preserve callable signatures through decorators; variadic generics | — | ✓ | — | — |
| T46-kwargs-typing | Unpack & **kwargs typing | Constrain individual keyword argument types via TypedDict | — | ✓ | — | — |
| T47-gradual-typing | Type inference & gradual typing | Checker infers types; Any disables checks; --strict controls enforcement | — | ✓ | — | — |
| T48-lifetimes | Lifetimes & reference validity | Prevent dangling references; prove every reference valid for its usage | — | — | ✓ | — |
| T49-associated-types | Associated types & advanced traits | Lock output types per implementor; reduce caller confusion | — | — | ✓ | — |
| T50-send-sync | Send & Sync markers | Prevent data races by controlling what crosses thread boundaries | — | — | ✓ | — |
| T51-totality | Totality & partial functions | Functions must handle all inputs; `partial` opts out but taints result | — | — | — | ✓ |

## Coverage summary

| Language | Covered | Total |
|----------|---------|-------|
| Scala 3  | 23      | /51   |
| Python   | 20      | /51   |
| Rust     | 14      | /51   |
| Lean     | 16      | /51   |
