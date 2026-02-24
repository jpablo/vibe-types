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

### Beginner mental model

Generics are templates where every hole declares what capability the filler must have, and `where` clauses keep the list of requirements readable and precise.

### Example A (code)

```rust
fn sum<I>(iter: I) -> i32
where
    I: IntoIterator<Item = i32>,
{
    iter.into_iter().sum()
}

let total = sum(vec![1, 2, 3]);
println!("total = {}", total);
```

### Example B (code)

```rust
use std::fmt::Display;

struct Wrapper<T>
where
    T: Display,
{
    value: T,
}

fn show<T>(w: Wrapper<T>) {
    println!("wrapped: {}", w.value);
}

show(Wrapper { value: "ok" });
```

### Common compiler errors and how to read them

- `error[E0277]: the trait bound \`Type: Trait\` is not satisfied` points to the operation that needs the bound; add the required trait to the parameter or adjust the code so it no longer uses the trait method.
- `error[E0599]: no method named ... found for type ...` often means the method exists behind a missing bound (for example `T: Display`); add the needed trait bound or call a method that all candidate types support.

## Use-case cross-references

- `[-> UC-03]`
- `[-> UC-06]`
- `[-> UC-08]`

## Source anchors

- `book/src/ch10-01-syntax.md`
- `rust-by-example/src/generics/bounds.md`
- `rust-by-example/src/generics/where.md`
