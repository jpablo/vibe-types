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

- Some advanced const-generic behavior may be version-sensitive.

## Use-case cross-references

- `[-> UC-08]`
