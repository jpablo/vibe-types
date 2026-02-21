# Value-Level Invariants with Types

## The constraint

Encode numeric/value invariants in types so invalid values are rejected early.

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

## Tradeoffs

- Strong guarantees with potentially more complex type signatures.
- Some invariants still require runtime checks or smart constructors.

## When to use which feature

- Use const generics when invariant values are part of the type identity.
- Keep bounds minimal to preserve API ergonomics.

## Source anchors

- `rust/src/doc/rustc-dev-guide/src/const-generics.md`
- `book/src/ch20-03-advanced-types.md`
