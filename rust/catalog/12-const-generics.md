# Const Generics

## What it is

Const generics allow values (such as array lengths) to parameterize types and APIs.

## What constraint it enforces

**Const-generic parameters expose compile-time scalar values in type signatures, so shape-level constraints are enforced before runtime.**

## Minimal snippet

```rust
struct FixedGrid<const ROWS: usize, const COLS: usize>([[u8; COLS]; ROWS]);

impl<const ROWS: usize, const COLS: usize> FixedGrid<ROWS, COLS> {
    fn new() -> Self {
        FixedGrid([[0; COLS]; ROWS])
    }
}
```

## Interaction with other features

- Extends generic patterns from `[-> catalog/05]`.
- Used for value-level invariants in `[-> UC-08]`.

## Gotchas and limitations

- Const parameters only accept scalar types (`u8`/`u16`/`u32`/`u64`/`u128`/`usize`/`i8`/`i16`/`i32`/`i64`/`i128`/`isize`/`bool`/`char`), so richer value constraints need wrappers or runtime checks.
- Anonymous const expressions used for array lengths or const arguments cannot capture generic parameters, which is why `const_evaluatable_unchecked` or explicit wrapper consts are needed before the compiler can stabilize more flexible const expressions.
- Const parameters model shape-level invariants well, but not every value-level rule can be encoded directly.

## Use-case cross-references

- `[-> UC-08]`

## Source anchors

- `rust/src/doc/reference/src/items/generics.md`
- `rust/src/doc/reference/src/type-system.md`
- `rust/src/doc/rustc-dev-guide/src/const-generics.md`
- `book/src/ch20-03-advanced-types.md`
