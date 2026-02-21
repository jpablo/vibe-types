# Const Generics

## What it is

Const generics allow values (such as array lengths) to parameterize types and APIs.

## What constraint it enforces

**Type-level constants constrain which values and shapes are accepted at compile time.**

## Minimal snippet

```rust
fn zeros<const N: usize>() -> [u8; N] {
    [0; N]
}
```

## Interaction with other features

- Extends generic patterns from `[-> catalog/05]`.
- Used for value-level invariants in `[-> UC-08]`.

## Gotchas and limitations

- Feature coverage and edge cases can be version-sensitive across Rust releases.
- Const parameters model shape-level invariants well, but not every value-level rule can be encoded directly.

## Use-case cross-references

- `[-> UC-08]`

## Source anchors

- `rust/src/doc/rustc-dev-guide/src/const-generics.md`
- `book/src/ch20-03-advanced-types.md`
