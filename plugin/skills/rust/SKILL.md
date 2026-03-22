---
description: Rust compile-time safety techniques — ownership, borrowing, lifetimes, traits, generics, Send/Sync, const generics. Use when writing safe Rust, choosing type system features, or debugging compiler errors.
version: 1.0.0
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

## Use cases (problem → which features help)

- **Preventing invalid states** — represent only valid domain states so invalid combinations won't compile (enums, newtypes, phantom types) → `usecases/UC01-invalid-states.md`
- **Ownership-safe APIs** — encode ownership transfer, borrowing, and lifetimes in signatures to prevent use-after-free in caller code → `usecases/UC20-ownership-apis.md`
- **Generic capability constraints** — accept only types satisfying required traits; reject unsuitable types with clear errors → `usecases/UC04-generic-constraints.md`
- **Extensible polymorphic interfaces** — allow plugins/alternative implementations without losing compile-time safety → `usecases/UC14-extensibility.md`
- **Compile-time concurrency** — threaded code compiles only when transfer and sharing are safe (`Send`/`Sync`) → `usecases/UC21-concurrency.md`
- **Conversion boundaries** — make cross-domain conversions explicit and type-checked; surface lossy casts → `usecases/UC22-conversions.md`
- **Trait impl failure diagnostics** — map confusing compiler errors back to fixable problems in bounds or impl structure → `usecases/UC23-diagnostics.md`
- **Value-level invariants with types** — encode lengths, dimensions, shapes in types so mismatches are caught at compile time → `usecases/UC18-type-arithmetic.md`
