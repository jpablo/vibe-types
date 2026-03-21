# Value-Level Invariants with Types

## The constraint

Encode numeric/value invariants in types so invalid shapes are rejected before runtime.

## Feature toolkit

- `[-> catalog/12]`
- `[-> catalog/05]`

## Patterns

- Pattern A: const-generic array sizes.
```rust
fn take_block<const N: usize>(x: [u8; N]) -> [u8; N] { x }
```
- Pattern B: const-parameterized domain wrappers.
```rust
struct Matrix<const R: usize, const C: usize>([[f64; C]; R]);
```
- Pattern C: compile-time grid type combining row/column scalars into a single constructor guard.
```rust
struct FixedGrid<const ROWS: usize, const COLS: usize>([[u8; COLS]; ROWS]);

impl<const ROWS: usize, const COLS: usize> FixedGrid<ROWS, COLS> {
    fn new() -> Self {
        FixedGrid([[0; COLS]; ROWS])
    }
}
```

## Tradeoffs

- Strong guarantees with potentially more complex type signatures.
- Some invariants still require runtime checks or smart constructors.

## Gotchas

- Const parameters are limited to scalar types, so not every domain-level value invariant is representable directly.
- Generic const-expression limits can force helper consts or runtime checks in complex cases.

## When to use which feature

- Use const generics when invariant values are part of the type identity.
- Keep bounds minimal to preserve API ergonomics.

## Source anchors

- `rust/src/doc/reference/src/items/generics.md`
- `rust/src/doc/reference/src/type-system.md`
- `rust/src/doc/rustc-dev-guide/src/const-generics.md`
- `book/src/ch20-03-advanced-types.md`
