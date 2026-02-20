# Cross-Reference Plan (Draft IDs)

## Catalog Docs

- `rust/catalog/00-overview.md`
- `rust/catalog/01-ownership-moves.md` (`F01`)
- `rust/catalog/02-borrowing-mutability.md` (`F02`)
- `rust/catalog/03-lifetimes.md` (`F03`)
- `rust/catalog/04-structs-enums-newtypes.md` (`F04`)
- `rust/catalog/05-generics-where-clauses.md` (`F05`)
- `rust/catalog/06-traits-impls.md` (`F06`)
- `rust/catalog/07-associated-types-advanced-traits.md` (`F07`)
- `rust/catalog/08-trait-objects-dyn.md` (`F08`)
- `rust/catalog/09-inference-aliases-conversions.md` (`F09`)
- `rust/catalog/10-smart-pointers-interior-mutability.md` (`F10`)
- `rust/catalog/11-send-sync.md` (`F11`)
- `rust/catalog/12-const-generics.md` (`F12`)
- `rust/catalog/13-coherence-orphan-rules.md` (`F13`)
- `rust/catalog/14-trait-solver-param-env.md` (`F14`)

## Use-Case Docs

- `rust/usecases/00-overview.md`
- `rust/usecases/01-preventing-invalid-states.md` (`UC-01`)
- `rust/usecases/02-ownership-safe-apis.md` (`UC-02`)
- `rust/usecases/03-generic-capability-constraints.md` (`UC-03`)
- `rust/usecases/04-extensible-polymorphic-interfaces.md` (`UC-04`)
- `rust/usecases/05-compile-time-concurrency-constraints.md` (`UC-05`)
- `rust/usecases/06-conversion-boundaries.md` (`UC-06`)
- `rust/usecases/07-trait-impl-failure-diagnostics.md` (`UC-07`)
- `rust/usecases/08-value-level-invariants-with-types.md` (`UC-08`)

## Bidirectional Mapping

- `F01` -> `UC-02`
- `F02` -> `UC-02`
- `F03` -> `UC-02`
- `F04` -> `UC-01`
- `F05` -> `UC-03`, `UC-06`, `UC-08`
- `F06` -> `UC-03`, `UC-04`, `UC-05`, `UC-07`
- `F07` -> `UC-03`
- `F08` -> `UC-04`
- `F09` -> `UC-01`, `UC-06`
- `F10` -> `UC-02`, `UC-05`
- `F11` -> `UC-05`
- `F12` -> `UC-08`
- `F13` -> `UC-07`
- `F14` -> `UC-07`

## Authoring Order

1. `00-overview` docs.
2. High-confidence features (`F01` through `F11`).
3. High-confidence use-cases (`UC-01` through `UC-06`).
4. Medium-confidence internals (`F12` through `F14`, `UC-07`, `UC-08`).
