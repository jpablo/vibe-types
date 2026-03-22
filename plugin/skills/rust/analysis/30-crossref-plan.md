# Cross-Reference Plan (Draft IDs)

## Catalog Docs

- `rust/catalog/00-overview.md`
- `rust/catalog/T10-ownership-moves.md` (`F01`)
- `rust/catalog/T11-borrowing-mutability.md` (`F02`)
- `rust/catalog/T48-lifetimes.md` (`F03`)
- `rust/catalog/T01-algebraic-data-types.md` (`F04`)
- `rust/catalog/T04-generics-bounds.md` (`F05`)
- `rust/catalog/T05-type-classes.md` (`F06`)
- `rust/catalog/T49-associated-types.md` (`F07`)
- `rust/catalog/T36-trait-objects.md` (`F08`)
- `rust/catalog/T18-conversions-coercions.md` (`F09`)
- `rust/catalog/T24-smart-pointers.md` (`F10`)
- `rust/catalog/T50-send-sync.md` (`F11`)
- `rust/catalog/T15-const-generics.md` (`F12`)
- `rust/catalog/T25-coherence-orphan.md` (`F13`)
- `rust/catalog/T37-trait-solver.md` (`F14`)

## Use-Case Docs

- `rust/usecases/00-overview.md`
- `rust/usecases/UC01-invalid-states.md` (`UC-01`)
- `rust/usecases/UC20-ownership-apis.md` (`UC-02`)
- `rust/usecases/UC04-generic-constraints.md` (`UC-03`)
- `rust/usecases/UC14-extensibility.md` (`UC-04`)
- `rust/usecases/UC21-concurrency.md` (`UC-05`)
- `rust/usecases/UC22-conversions.md` (`UC-06`)
- `rust/usecases/UC23-diagnostics.md` (`UC-07`)
- `rust/usecases/UC18-type-arithmetic.md` (`UC-08`)

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
