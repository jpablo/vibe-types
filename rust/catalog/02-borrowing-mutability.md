# Borrowing and Mutability Rules

## What it is

References borrow values without transferring ownership, subject to aliasing and mutability rules.

## What constraint it enforces

**You can have many immutable references or one mutable reference, but not both at the same time.**

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

- Simultaneous mutable borrows are rejected even when they seem short-lived.
- Borrow scopes may extend to last use, which can make mutable reborrows fail unexpectedly.

## Use-case cross-references

- `[-> UC-02]`
- `[-> UC-05]`

## Source anchors

- `book/src/ch04-02-references-and-borrowing.md`
- `rust-by-example/src/scope/borrow.md`
- `rust-by-example/src/scope/borrow/ref.md`
- `rust-by-example/src/scope/borrow/mut.md`
