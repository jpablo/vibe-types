# Smart Pointers and Interior Mutability

## What it is

Smart pointer types encode ownership, sharing, and mutation policies in their APIs.

## What constraint it enforces

**Access and mutation patterns are constrained by pointer and wrapper type semantics.**

## Minimal snippet

```rust
use std::cell::RefCell;

let x = RefCell::new(1);
*x.borrow_mut() = 2; // OK
```

## Interaction with other features

- Depends on ownership and borrowing in `[-> catalog/01]` and `[-> catalog/02]`.
- Often appears in `[-> UC-02]` and `[-> UC-05]`.

## Gotchas and limitations

- Some checks move to runtime for interior mutability wrappers.

## Use-case cross-references

- `[-> UC-02]`
- `[-> UC-05]`
