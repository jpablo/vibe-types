---
name: rust
description: Rust compile-time safety techniques — ownership, borrowing, lifetimes, traits, generics, Send/Sync, const generics. Use when writing safe Rust, choosing type system features, or debugging compiler errors.
version: 1.0.0
---

# Rust — Compile-Time Safety Techniques

> **Base path:** `${CLAUDE_PLUGIN_ROOT}/rust`

## Full catalog (type system features → constraints they enforce)

- **Ownership & moves** — prevent use-after-free and double-free; ensure deterministic cleanup → `catalog/01-ownership-moves.md`
- **Borrowing & mutability** — eliminate data races and iterator invalidation via aliasing rules (`&T` xor `&mut T`) → `catalog/02-borrowing-mutability.md`
- **Lifetimes** — prevent dangling references; prove every reference valid for its usage → `catalog/03-lifetimes.md`
- **Structs, enums, newtypes** — make invalid states unrepresentable; exhaustive match forces handling all variants → `catalog/04-structs-enums-newtypes.md`
- **Generics & where clauses** — generic code compiles only when operations are justified by declared bounds → `catalog/05-generics-where-clauses.md`
- **Traits & impls** — enforce contracts on types; one impl per trait-type pair globally → `catalog/06-traits-impls.md`
- **Associated types & advanced traits** — lock output types per implementor; reduce caller confusion → `catalog/07-associated-types-advanced-traits.md`
- **Trait objects (`dyn`)** — runtime polymorphism when concrete types are unknown; only object-safe traits qualify → `catalog/08-trait-objects-dyn.md`
- **Inference, aliases, conversions** — maintain type safety while permitting local inference; no silent conversions → `catalog/09-inference-aliases-conversions.md`
- **Smart pointers & interior mutability** — flexible ownership (shared, interior-mutable) while preserving memory safety → `catalog/10-smart-pointers-interior-mutability.md`
- **Send & Sync** — prevent data races at compile time by controlling what crosses thread boundaries → `catalog/11-send-sync.md`
- **Const generics** — encode sizes, dimensions, capacities in types; distinct values = distinct types → `catalog/12-const-generics.md`
- **Coherence & orphan rules** — prevent conflicting impls across crates; ensure independent publishing → `catalog/13-coherence-orphan-rules.md`
- **Trait solver & param env** — deterministic zero-cost trait resolution; guides correct bounds → `catalog/14-trait-solver-param-env.md`

## Use cases (problem → which features help)

- **Preventing invalid states** — represent only valid domain states so invalid combinations won't compile (enums, newtypes, phantom types) → `usecases/01-preventing-invalid-states.md`
- **Ownership-safe APIs** — encode ownership transfer, borrowing, and lifetimes in signatures to prevent use-after-free in caller code → `usecases/02-ownership-safe-apis.md`
- **Generic capability constraints** — accept only types satisfying required traits; reject unsuitable types with clear errors → `usecases/03-generic-capability-constraints.md`
- **Extensible polymorphic interfaces** — allow plugins/alternative implementations without losing compile-time safety → `usecases/04-extensible-polymorphic-interfaces.md`
- **Compile-time concurrency** — threaded code compiles only when transfer and sharing are safe (`Send`/`Sync`) → `usecases/05-compile-time-concurrency-constraints.md`
- **Conversion boundaries** — make cross-domain conversions explicit and type-checked; surface lossy casts → `usecases/06-conversion-boundaries.md`
- **Trait impl failure diagnostics** — map confusing compiler errors back to fixable problems in bounds or impl structure → `usecases/07-trait-impl-failure-diagnostics.md`
- **Value-level invariants with types** — encode lengths, dimensions, shapes in types so mismatches are caught at compile time → `usecases/08-value-level-invariants-with-types.md`
