# Structs, Enums, and Newtypes

## What it is

Rust data types encode domain state directly through fields and variants.

## What constraint it enforces

**Only explicitly modeled states are constructible, and pattern matching forces callers to handle declared variants.**

## Minimal snippet

```rust
enum Payment {
    Cash,
    Card { last4: u16 },
}
```

## Interaction with other features

- Often combined with trait impls from `[-> catalog/06]`.
- Supports invalid-state prevention in `[-> UC-01]`.

## Gotchas and limitations

- Struct update syntax can move non-`Copy` fields and invalidate the source instance.
- Field/variant shape alone is not enough for range/business invariants; smart constructors are often required.

## Use-case cross-references

- `[-> UC-01]`

## Source anchors

- `book/src/ch05-01-defining-structs.md`
- `book/src/ch06-01-defining-an-enum.md`
- `book/src/ch09-03-to-panic-or-not-to-panic.md`
- `rust-by-example/src/custom_types/structs.md`
- `rust-by-example/src/custom_types/enum.md`
