# Coherence and Orphan Rules

## What it is

Rust coherence rules determine when trait implementations are legal and non-overlapping.

## What constraint it enforces

**A trait impl is legal only when the trait is local or at least one mentioned type is local, and overlapping impl candidates are rejected.**

## Minimal snippet

```rust,compile_fail
use std::fmt::{Display, Formatter, Result};

// Both trait (`Display`) and type (`Vec<i32>`) are foreign.
impl Display for Vec<i32> {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        write!(f, "{:?}", self)
    }
}
```

## Interaction with other features

- Governs trait impl validity from `[-> catalog/06]`.
- Important for debugging in `[-> UC-07]`.

## Gotchas and limitations

- You cannot implement a foreign trait for a foreign type even when no impl exists today.
- Coherence checks potential future overlap as well, so some blanket impls fail to preserve downstream compatibility.

### Beginner mental model

Rust only lets you add trait implementations when you “own” part of the triplet: either the trait or the type comes from your crate. This avoids two crates implementing the same trait for the same type and conflicting later. Picture it as a party where only hosts or their invited guests get to decorate the room.

### Example A

```rust
trait LocalTrait {}
struct LocalType;

impl LocalTrait for LocalType {} // legal because both items are local.
```

### Example B

```rust,compile_fail
use std::fmt::{Display, Formatter, Result};

// error: cannot implement a foreign trait for a foreign type
impl Display for Vec<i32> {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        write!(f, "{:?}", self)
    }
}
```

### Common compiler errors and how to read them

- `error[E0117]: only traits defined in the current crate can be implemented for types defined outside of the crate` means you tried a foreign-trait/foreign-type pair; use a local newtype or local trait.
- `conflicting implementations of trait Trait for Type` – the compiler found another impl elsewhere, maybe downstream; use trait bounds or newtype wrappers instead of duplicate blanket impls.
- `impl Trait for Type` cannot be written because overlapping impls exist – these happen when the compiler cannot prove a single legal impl without breaking downstream compatibility; adjust your bounds or introduce more specific types to avoid overlap.

## Use-case cross-references

- `[-> UC-07]`

## Source anchors

- `rust/src/doc/reference/src/items/implementations.md`
- `rust/src/doc/reference/src/type-system.md`
- `rust/src/doc/rustc-dev-guide/src/coherence.md`
