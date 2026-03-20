# Conversion Boundaries

## The constraint

Conversions across domain boundaries should be explicit and type-checked.

## Feature toolkit

- `[-> catalog/09]`
- `[-> catalog/05]`

## Patterns

- Pattern A: `TryFrom` for fallible conversion.
```rust
use std::convert::TryFrom;
let n = i32::try_from(7_i64).unwrap();
```
- Pattern B: generic helper with conversion bound.
```rust
fn into_u64<T: Into<u64>>(x: T) -> u64 { x.into() }
```

## Tradeoffs

- Explicit conversion code is more verbose but safer.
- Numeric casts with `as` may lose information; conversion traits better communicate intent.

## When to use which feature

- Use `TryFrom` when failure is meaningful.
- Use `From` for guaranteed lossless conversions.

## Source anchors

- `rust-by-example/src/conversion/from_into.md`
- `rust-by-example/src/conversion/try_from_try_into.md`
- `rust-by-example/src/types/cast.md`
- `book/src/ch20-03-advanced-types.md`
