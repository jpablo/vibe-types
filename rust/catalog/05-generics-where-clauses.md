# Generics and Where Clauses

## What it is

Generic parameters and `where` clauses constrain which types can instantiate APIs.

## What constraint it enforces

**Generic code compiles only when every operation in the body is justified by declared bounds.**

## Minimal snippet

```rust
use std::fmt::Debug;

fn print_option<T>(v: T)
where
    Option<T>: Debug,
{
    println!("{:?}", Some(v));
}
```

## Interaction with other features

- Depends on trait contracts in `[-> catalog/06]`.
- Extended by associated types in `[-> catalog/07]`.
- Drives `[-> UC-03]`, `[-> UC-06]`, `[-> UC-08]`.

## Gotchas and limitations

- Over-constraining type parameters can block valid callers and reduce reuse.
- Bounds must match the exact used type (`Option<T>: Debug` differs from `T: Debug`).

## Use-case cross-references

- `[-> UC-03]`
- `[-> UC-06]`
- `[-> UC-08]`

## Source anchors

- `book/src/ch10-01-syntax.md`
- `rust-by-example/src/generics/bounds.md`
- `rust-by-example/src/generics/where.md`
