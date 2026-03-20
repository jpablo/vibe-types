# Rust By Example Findings

## Scope

- Source: `/Users/jpablo/GitHub/rust-by-example`
- Snapshot: `5383db524711` (2026-02-16)

## Priority Files

- `src/types.md`
- `src/types/inference.md`
- `src/types/alias.md`
- `src/custom_types.md`
- `src/custom_types/structs.md`
- `src/custom_types/enum.md`
- `src/generics.md`
- `src/generics/bounds.md`
- `src/generics/where.md`
- `src/generics/assoc_items/types.md`
- `src/generics/phantom.md`
- `src/trait.md`
- `src/trait/supertraits.md`
- `src/trait/impl_trait.md`
- `src/trait/dyn.md`
- `src/scope/lifetime.md`
- `src/scope/borrow/ref.md`
- `src/scope/borrow/mut.md`
- `src/conversion/from_into.md`
- `src/conversion/try_from_try_into.md`

## Extraction Order

1. `types` and `custom_types` for foundational constraints.
2. `generics` for parametric constraints and bounds.
3. `trait` for capability contracts and dispatch forms.
4. `scope/lifetime` for borrow and lifetime enforcement.
5. `conversion` for compile-time conversion contracts.

## Candidate Feature Buckets

- Ownership and borrowing shape: `src/scope/*`.
- Types and invalid-state modeling: `src/types/*`, `src/custom_types/*`.
- Generic bounds and associated types: `src/generics/*`.
- Trait contracts and polymorphism: `src/trait/*`.
- Conversion contracts: `src/conversion/*`.

## Candidate Use-Case Buckets

- Prevent invalid states with enums/newtypes/phantom types.
- Restrict generic APIs with bounds and where-clauses.
- Express safe polymorphism (`impl Trait` or `dyn Trait`) by constraint.
- Track reference validity with lifetimes and borrow rules.
- Enforce safe type conversion boundaries with `From`/`TryFrom`.

## Gaps and Risks

- Limited coverage of const generics and newer type-system features.
- Some chapters are pedagogical and omit formal edge-case language.
- Trait-system internals (coherence/solver details) are not authoritative here.
