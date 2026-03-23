---
name: vibe-types:rust
description: Rust compile-time safety techniques — ownership, borrowing, lifetimes, traits, generics, Send/Sync, const generics. Use this skill whenever the user writes Rust code, mentions ownership or borrowing, asks about lifetime errors, discusses trait bounds, Send/Sync, derive macros, PhantomData, newtype patterns, or any Rust type system feature. Also use when debugging borrow checker errors or porting type patterns from Scala, Python, or Haskell to Rust.
version: 0.2.0
---

# Rust — Compile-Time Safety Techniques

> **Base path:** `${CLAUDE_PLUGIN_ROOT}/skills/rust`

## Full catalog (type system features → constraints they enforce)

- **Ownership & moves** — prevent use-after-free and double-free; ensure deterministic cleanup → `catalog/T10-ownership-moves.md`
- **Borrowing & mutability** — eliminate data races and iterator invalidation via aliasing rules (`&T` xor `&mut T`) → `catalog/T11-borrowing-mutability.md`
- **Lifetimes** — prevent dangling references; prove every reference valid for its usage → `catalog/T48-lifetimes.md`
- **Structs, enums, newtypes** — make invalid states unrepresentable; exhaustive match forces handling all variants → `catalog/T01-algebraic-data-types.md`
- **Generics & where clauses** — generic code compiles only when operations are justified by declared bounds → `catalog/T04-generics-bounds.md`
- **Traits & impls** — enforce contracts on types; one impl per trait-type pair globally → `catalog/T05-type-classes.md`
- **Associated types & advanced traits** — lock output types per implementor; reduce caller confusion → `catalog/T49-associated-types.md`
- **Trait objects (`dyn`)** — runtime polymorphism when concrete types are unknown; only object-safe traits qualify → `catalog/T36-trait-objects.md`
- **Inference, aliases, conversions** — maintain type safety while permitting local inference; no silent conversions → `catalog/T18-conversions-coercions.md`
- **Smart pointers & interior mutability** — flexible ownership (shared, interior-mutable) while preserving memory safety → `catalog/T24-smart-pointers.md`
- **Send & Sync** — prevent data races at compile time by controlling what crosses thread boundaries → `catalog/T50-send-sync.md`
- **Const generics** — encode sizes, dimensions, capacities in types; distinct values = distinct types → `catalog/T15-const-generics.md`
- **Coherence & orphan rules** — prevent conflicting impls across crates; ensure independent publishing → `catalog/T25-coherence-orphan.md`
- **Trait solver & param env** — deterministic zero-cost trait resolution; guides correct bounds → `catalog/T37-trait-solver.md`
- **Refinement types** — newtype + smart constructor pattern; validated values with private fields; nutype derive macro → `catalog/T26-refinement-types.md`
- **Literal types** — Rust lacks first-class literal types; const generics, enums, and `typenum` serve as alternatives → `catalog/T52-literal-types.md`
- **Path-dependent types** — associated types as path-dependent analogs; GATs for higher-kinded path dependence → `catalog/T53-path-dependent-types.md`
- **Newtypes** — zero-cost wrapper types with private fields; prevent value mix-ups → `catalog/T03-newtypes-opaque.md`
- **Derive macros** — `#[derive(Debug, Clone, Serialize)]`; auto-generate trait impls from structure → `catalog/T06-derivation.md`
- **Null safety** — no null in Rust; `Option<T>` enforces handling of absent values → `catalog/T13-null-safety.md`
- **Type narrowing** — `if let`, `match`, `let-else`; exhaustive pattern matching → `catalog/T14-type-narrowing.md`
- **Compile-time computation** — `const fn`, `const` blocks, compile-time evaluation → `catalog/T16-compile-time-ops.md`
- **Macros** — `macro_rules!`, proc macros, `syn`/`quote` for code generation → `catalog/T17-macros-metaprogramming.md`
- **Equality safety** — `PartialEq`/`Eq` are opt-in; no accidental cross-type equality → `catalog/T20-equality-safety.md`
- **Encapsulation** — `pub`/`pub(crate)`/private-by-default module system → `catalog/T21-encapsulation.md`
- **Callable typing** — `Fn`/`FnMut`/`FnOnce` trait hierarchy; closures and function pointers → `catalog/T22-callable-typing.md`
- **Type aliases** — `type Alias = ConcreteType`; transparent aliases vs newtypes → `catalog/T23-type-aliases.md`
- **Phantom types** — `PhantomData<T>` for variance control, typestate, lifetime markers → `catalog/T27-erased-phantom.md`
- **Record types** — named-field structs; struct update syntax; destructuring → `catalog/T31-record-types.md`
- **Immutability** — immutable by default; `mut` is opt-in; `const` for compile-time constants → `catalog/T32-immutability-markers.md`
- **Self type** — `Self` refers to the implementing type; builders, `From`/`Into` → `catalog/T33-self-type.md`
- **Never type** — `!` bottom type; `Infallible`; empty enums; coerces to any type → `catalog/T34-never-bottom.md`
- **Union types** *(via enums)* — enums as sum types; trait bounds as intersection → `catalog/T02-union-intersection.md`
- **Structural typing** *(via traits)* — nominal typing with trait-based contracts → `catalog/T07-structural-typing.md`
- **Variance** *(implicit rules)* — compiler-inferred variance; `PhantomData` for control → `catalog/T08-variance-subtyping.md`
- **Effect tracking** *(via Result)* — `Result<T,E>` + `?`; `async`/`await`; `unsafe` boundaries → `catalog/T12-effect-tracking.md`
- **Extension methods** *(via traits)* — extension trait pattern; orphan rules → `catalog/T19-extension-methods.md`

## Use cases (problem → which features help)

- **Preventing invalid states** — represent only valid domain states so invalid combinations won't compile (enums, newtypes, phantom types) → `usecases/UC01-invalid-states.md`
- **Ownership-safe APIs** — encode ownership transfer, borrowing, and lifetimes in signatures to prevent use-after-free in caller code → `usecases/UC20-ownership-apis.md`
- **Generic capability constraints** — accept only types satisfying required traits; reject unsuitable types with clear errors → `usecases/UC04-generic-constraints.md`
- **Extensible polymorphic interfaces** — allow plugins/alternative implementations without losing compile-time safety → `usecases/UC14-extensibility.md`
- **Compile-time concurrency** — threaded code compiles only when transfer and sharing are safe (`Send`/`Sync`) → `usecases/UC21-concurrency.md`
- **Conversion boundaries** — make cross-domain conversions explicit and type-checked; surface lossy casts → `usecases/UC22-conversions.md`
- **Trait impl failure diagnostics** — map confusing compiler errors back to fixable problems in bounds or impl structure → `usecases/UC23-diagnostics.md`
- **Value-level invariants with types** — encode lengths, dimensions, shapes in types so mismatches are caught at compile time → `usecases/UC18-type-arithmetic.md`
