# Coherence and Orphan Rules

## What it is

Rust coherence rules determine when trait implementations are legal and non-overlapping.

## What constraint it enforces

**A trait impl is legal only when the trait is local or at least one mentioned type is local, and overlapping impl candidates are rejected.**

## Minimal snippet

```rust
// Both trait and type are foreign, so coherence rejects this outright.
// Example requires operating on a local trait or type instead.
impl serde::Serialize for http::Request {} // <-- error: orphan rule
```

## Interaction with other features

- Governs trait impl validity from `[-> catalog/06]`.
- Important for debugging in `[-> UC-07]`.

## Gotchas and limitations

- You cannot implement a foreign trait for a foreign type even when no impl exists today.
- Coherence checks potential future overlap as well, so some blanket impls fail to preserve downstream compatibility.

## Use-case cross-references

- `[-> UC-07]`

## Source anchors

- `rust/src/doc/reference/src/items/implementations.md`
- `rust/src/doc/reference/src/type-system.md`
- `rust/src/doc/rustc-dev-guide/src/coherence.md`
