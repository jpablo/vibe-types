# Borrowing and Mutability Rules

## What it is

References borrow values without transferring ownership, subject to aliasing and mutability rules.

## What constraint it enforces

**You cannot have mutable and immutable aliases active at the same time.**

## Minimal snippet

```rust
let mut x = 0;
let r1 = &x;
// let r2 = &mut x; // error: cannot borrow as mutable while immutably borrowed
println!("{}", r1); // OK
```

## Interaction with other features

- Extends ownership in `[-> catalog/01]`.
- Lifetime relationships live in `[-> catalog/03]`.
- Core for `[-> UC-02]` and `[-> UC-05]`.

## Gotchas and limitations

- Non-lexical lifetimes can make borrow scopes less obvious.

## Use-case cross-references

- `[-> UC-02]`
- `[-> UC-05]`
