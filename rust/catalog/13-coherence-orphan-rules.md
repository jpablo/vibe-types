# Coherence and Orphan Rules

## What it is

Rust coherence rules determine when trait implementations are legal and non-overlapping.

## What constraint it enforces

**Conflicting or orphaned trait impls are rejected at compile time.**

## Minimal snippet

```rust
// Conceptual constraint:
// impl ExternalTrait for ExternalType {} // error (orphan rule)
```

## Interaction with other features

- Governs trait impl validity from `[-> catalog/06]`.
- Important for debugging in `[-> UC-07]`.

## Gotchas and limitations

- Blanket impls can interact with coherence in non-obvious ways.

## Use-case cross-references

- `[-> UC-07]`
