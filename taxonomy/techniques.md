# Master Technique Catalog

Language-agnostic inventory of type-safety techniques. Each entry has a stable ID that matches the filename used across all language catalogs: `catalog/<ID>.md`.

Language columns link to the per-language file; `—` marks a gap.

## Techniques

| ID | Technique | What it enforces | Scala 3 | Python | Rust | Lean |
|----|-----------|-----------------|---------|--------|------|------|
| T01-algebraic-data-types | ADTs, enums, inductive types & pattern matching | Closed variants; exhaustive handling; invalid states unrepresentable | [scala3](../plugin/skills/scala3/catalog/T01-algebraic-data-types.md) | [python](../plugin/skills/python/catalog/T01-algebraic-data-types.md) | [rust](../plugin/skills/rust/catalog/T01-algebraic-data-types.md) | [lean](../plugin/skills/lean/catalog/T01-algebraic-data-types.md)|
| T02-union-intersection | Union & intersection types | Type-level alternatives/combinations without class hierarchies | [scala3](../plugin/skills/scala3/catalog/T02-union-intersection.md) | [python](../plugin/skills/python/catalog/T02-union-intersection.md) | — | —|
| T03-newtypes-opaque | Newtypes & opaque types | Zero-cost distinct types; prevent value mix-ups | [scala3](../plugin/skills/scala3/catalog/T03-newtypes-opaque.md) | [python](../plugin/skills/python/catalog/T03-newtypes-opaque.md) | — | —|
| T04-generics-bounds | Generics & bounded polymorphism | Type parameters with bounds; generic code only compiles when constraints hold | — | [python](../plugin/skills/python/catalog/T04-generics-bounds.md) | [rust](../plugin/skills/rust/catalog/T04-generics-bounds.md) | —|
| T05-type-classes | Type classes, traits, protocols & abstract bases | Capability evidence; compiler supplies instances automatically | [scala3](../plugin/skills/scala3/catalog/T05-type-classes.md) | [python](../plugin/skills/python/catalog/T05-type-classes.md) | [rust](../plugin/skills/rust/catalog/T05-type-classes.md) | [lean](../plugin/skills/lean/catalog/T05-type-classes.md)|
| T06-derivation | Type-class derivation & auto-generation | Instances generated from compile-time structure | [scala3](../plugin/skills/scala3/catalog/T06-derivation.md) | [python](../plugin/skills/python/catalog/T06-derivation.md) | — | —|
| T07-structural-typing | Structural typing & refined types | Static duck typing; shape-based conformance without inheritance | [scala3](../plugin/skills/scala3/catalog/T07-structural-typing.md) | [python](../plugin/skills/python/catalog/T07-structural-typing.md) | — | —|
| T08-variance-subtyping | Variance & subtyping rules | Co/contravariance control; prevent unsound substitutions | — | [python](../plugin/skills/python/catalog/T08-variance-subtyping.md) | — | —|
| T09-dependent-types | Dependent types & value-indexed types | Types depend on values; compiler checks index consistency | [scala3](../plugin/skills/scala3/catalog/T09-dependent-types.md) | — | — | [lean](../plugin/skills/lean/catalog/T09-dependent-types.md)|
| T10-ownership-moves | Ownership & move semantics | Prevent use-after-free and double-free; deterministic cleanup | — | — | [rust](../plugin/skills/rust/catalog/T10-ownership-moves.md) | —|
| T11-borrowing-mutability | Borrowing & mutability rules | Eliminate data races via aliasing rules (`&T` xor `&mut T`) | — | — | [rust](../plugin/skills/rust/catalog/T11-borrowing-mutability.md) | —|
| T12-effect-tracking | Effect tracking & capabilities | Track captured capabilities, side effects, purity at type level | [scala3](../plugin/skills/scala3/catalog/T12-effect-tracking.md) | — | — | [lean](../plugin/skills/lean/catalog/T12-effect-tracking.md)|
| T13-null-safety | Null safety & optionality | Reference types never null unless explicit; None must be handled | [scala3](../plugin/skills/scala3/catalog/T13-null-safety.md) | [python](../plugin/skills/python/catalog/T13-null-safety.md) | — | —|
| T14-type-narrowing | Type narrowing & exhaustiveness checking | After a check, type is narrowed; all branches must be handled | [scala3](../plugin/skills/scala3/catalog/T14-type-narrowing.md) | [python](../plugin/skills/python/catalog/T14-type-narrowing.md) | — | —|
| T15-const-generics | Const generics & value-level type parameters | Encode sizes, dimensions, capacities as type parameters | — | — | [rust](../plugin/skills/rust/catalog/T15-const-generics.md) | —|
| T16-compile-time-ops | Inline & compile-time computation | Constant folding, dead-branch elimination, compile-time specialization | [scala3](../plugin/skills/scala3/catalog/T16-compile-time-ops.md) | — | — | —|
| T17-macros-metaprogramming | Macros & metaprogramming | Type-safe compile-time code generation, syntax extension | [scala3](../plugin/skills/scala3/catalog/T17-macros-metaprogramming.md) | — | — | [lean](../plugin/skills/lean/catalog/T17-macros-metaprogramming.md)|
| T18-conversions-coercions | Type conversions & coercions | Explicit/implicit conversions; prevent silent lossy casts | [scala3](../plugin/skills/scala3/catalog/T18-conversions-coercions.md) | — | [rust](../plugin/skills/rust/catalog/T18-conversions-coercions.md) | [lean](../plugin/skills/lean/catalog/T18-conversions-coercions.md)|
| T19-extension-methods | Extension methods | Attach operations to types you don't own | [scala3](../plugin/skills/scala3/catalog/T19-extension-methods.md) | — | — | —|
| T20-equality-safety | Equality & comparison constraints | Restrict `==` to semantically meaningful comparisons | [scala3](../plugin/skills/scala3/catalog/T20-equality-safety.md) | — | — | —|
| T21-encapsulation | Encapsulation, visibility & module boundaries | Control what leaks across boundaries; hide representations | [scala3](../plugin/skills/scala3/catalog/T21-encapsulation.md) | — | — | [lean](../plugin/skills/lean/catalog/T21-encapsulation.md)|
| T22-callable-typing | Callable types, overloading & signature preservation | Constrain function signatures; preserve types through decorators | — | [python](../plugin/skills/python/catalog/T22-callable-typing.md) | — | —|
| T23-type-aliases | Type aliases & the `type` statement | Explicit alias declarations; lazy evaluation and forward references | — | [python](../plugin/skills/python/catalog/T23-type-aliases.md) | — | —|
| T24-smart-pointers | Smart pointers & interior mutability | Flexible ownership wrappers preserving memory safety | — | — | [rust](../plugin/skills/rust/catalog/T24-smart-pointers.md) | —|
| T25-coherence-orphan | Coherence & orphan rules | One impl per trait-type pair; prevent conflicting cross-crate impls | — | — | [rust](../plugin/skills/rust/catalog/T25-coherence-orphan.md) | —|
| T26-refinement-types | Subtypes, refinement types & annotated metadata | Attach predicates to types; construction requires evidence | — | [python](../plugin/skills/python/catalog/T26-refinement-types.md) | — | [lean](../plugin/skills/lean/catalog/T26-refinement-types.md)|
| T27-erased-phantom | Erased definitions & phantom types | Compile-time-only parameters; zero-cost type-level evidence | [scala3](../plugin/skills/scala3/catalog/T27-erased-phantom.md) | — | — | —|
| T28-termination | Termination checking & well-founded recursion | Every recursive function must provably terminate | — | — | — | [lean](../plugin/skills/lean/catalog/T28-termination.md)|
| T29-propositions-as-types | Propositions as types & proof terms | Encode invariants as types; compiler requires proof evidence | — | — | — | [lean](../plugin/skills/lean/catalog/T29-propositions-as-types.md)|
| T30-proof-automation | Proof automation & tactics | Automated verification of proof obligations | — | — | — | [lean](../plugin/skills/lean/catalog/T30-proof-automation.md)|
| T31-record-types | Typed dictionaries, records & structures | Named-field data with statically checked shapes | — | [python](../plugin/skills/python/catalog/T31-record-types.md) | — | [lean](../plugin/skills/lean/catalog/T31-record-types.md)|
| T32-immutability-markers | Final, frozen & immutability markers | Prevent reassignment, override, or mutation after declaration | — | [python](../plugin/skills/python/catalog/T32-immutability-markers.md) | — | —|
| T33-self-type | Self type & fluent returns | Methods return the receiver's type for chaining | — | [python](../plugin/skills/python/catalog/T33-self-type.md) | — | —|
| T34-never-bottom | Never, NoReturn & bottom type | Mark unreachable code; exhaustiveness proofs | — | [python](../plugin/skills/python/catalog/T34-never-bottom.md) | — | —|
| T35-universes-kinds | Universes & kind polymorphism | Type-of-types; prevent type-in-type paradoxes | [scala3](../plugin/skills/scala3/catalog/T35-universes-kinds.md) | — | — | [lean](../plugin/skills/lean/catalog/T35-universes-kinds.md)|
| T36-trait-objects | Trait objects & runtime polymorphism | Dynamic dispatch when concrete type unknown; object-safety rules | — | — | [rust](../plugin/skills/rust/catalog/T36-trait-objects.md) | —|
| T37-trait-solver | Trait solver & resolution internals | Deterministic zero-cost trait resolution; guides correct bounds | — | — | [rust](../plugin/skills/rust/catalog/T37-trait-solver.md) | —|
| T38-implicits-auto-bound | Auto-bound implicits & implicit arguments | Compiler infers context arguments; constrains to types with evidence | — | — | — | [lean](../plugin/skills/lean/catalog/T38-implicits-auto-bound.md)|
| T39-notation-attributes | Notation, attributes & compiler directives | Control how checker/optimizer treats definitions | — | — | — | [lean](../plugin/skills/lean/catalog/T39-notation-attributes.md)|
| T40-type-lambdas | Type lambdas & higher-kinded abstraction | Abstract over type constructors; partially apply binary constructors | [scala3](../plugin/skills/scala3/catalog/T40-type-lambdas.md) | — | — | —|
| T41-match-types | Match types & type-level pattern matching | Compute types from types via pattern matching; type-level conditionals | [scala3](../plugin/skills/scala3/catalog/T41-match-types.md) | — | — | —|
| T42-context-functions | Context functions & context bounds | Abstract over contextual dependencies as types | [scala3](../plugin/skills/scala3/catalog/T42-context-functions.md) | — | — | —|
| T43-experimental-preview | Experimental features & preview | Named type args, `into`, modularity — not yet stable | [scala3](../plugin/skills/scala3/catalog/T43-experimental-preview.md) | — | — | —|
| T44-changed-dropped | Changed & dropped features | Removed unsound features; more predictable inference | [scala3](../plugin/skills/scala3/catalog/T44-changed-dropped.md) | — | — | —|
| T45-paramspec-variadic | ParamSpec & TypeVarTuple | Preserve callable signatures through decorators; variadic generics | — | [python](../plugin/skills/python/catalog/T45-paramspec-variadic.md) | — | —|
| T46-kwargs-typing | Unpack & **kwargs typing | Constrain individual keyword argument types via TypedDict | — | [python](../plugin/skills/python/catalog/T46-kwargs-typing.md) | — | —|
| T47-gradual-typing | Type inference & gradual typing | Checker infers types; Any disables checks; --strict controls enforcement | — | [python](../plugin/skills/python/catalog/T47-gradual-typing.md) | — | —|
| T48-lifetimes | Lifetimes & reference validity | Prevent dangling references; prove every reference valid for its usage | — | — | [rust](../plugin/skills/rust/catalog/T48-lifetimes.md) | —|
| T49-associated-types | Associated types & advanced traits | Lock output types per implementor; reduce caller confusion | — | — | [rust](../plugin/skills/rust/catalog/T49-associated-types.md) | —|
| T50-send-sync | Send & Sync markers | Prevent data races by controlling what crosses thread boundaries | — | — | [rust](../plugin/skills/rust/catalog/T50-send-sync.md) | —|
| T51-totality | Totality & partial functions | Functions must handle all inputs; `partial` opts out but taints result | — | — | — | [lean](../plugin/skills/lean/catalog/T51-totality.md)|

## Coverage summary

| Language | Covered | Total |
|----------|---------|-------|
| Scala 3  | 23      | /51   |
| Python   | 20      | /51   |
| Rust     | 14      | /51   |
| Lean     | 16      | /51   |
