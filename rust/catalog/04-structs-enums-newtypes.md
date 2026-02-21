# Structs, Enums, and Newtypes

## What it is

Rust data types encode domain state directly through fields and variants.

## What constraint it enforces

**Only explicitly modeled states are constructible at compile time.**

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

- Invariants beyond shape may require smart constructors.

## Use-case cross-references

- `[-> UC-01]`
