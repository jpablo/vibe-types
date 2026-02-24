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

### Beginner mental model

Borrowing is like lending a book: you can loan it to many readers if they only look, but only one reader can rewrite while no one else holds it.

### Example A (code)

```rust
let data = vec![1, 2, 3];
let first = &data[0];
println!("first = {}", first);
// let mut_ref = &mut data; // error: cannot borrow `data` as mutable because it is also borrowed as immutable
```

### Example B (code)

```rust
let mut counter = 0;
{
    let mut_ref = &mut counter;
    *mut_ref += 1;
} // mutable borrow ends here
let again = &counter; // now only immutable borrows remain
println!("counter = {}", again);
```

### Common compiler errors and how to read them

- `error[E0502]: cannot borrow 'x' as mutable because it is also borrowed as immutable` points to both the immutable loan and the attempted mutable borrow; drop or limit the immutable reference before mutating.
- `error[E0506]: cannot assign to 'x' because it is borrowed` traces back to the borrow keeping the value off-limits for mutation; shorten the borrow scope or clone the data when necessary.

## Use-case cross-references

- `[-> UC-02]`
- `[-> UC-05]`

## Source anchors

- `book/src/ch04-02-references-and-borrowing.md`
- `rust-by-example/src/scope/borrow.md`
- `rust-by-example/src/scope/borrow/ref.md`
- `rust-by-example/src/scope/borrow/mut.md`
