# The Never Type and Bottom

Since: Rust 1.0 (diverging functions); `!` type syntax stabilizing; `Infallible` since Rust 1.34

## What it is

The **never type** `!` represents computations that never produce a value -- they diverge. Expressions like `loop {}`, `panic!()`, `return`, `break`, and `continue` all have type `!`. Because a value of type `!` can never exist, the compiler allows it to **coerce to any type**, which is why `panic!()` can appear in a branch that expects `i32`, or `continue` can fill an `Option<T>` arm.

`!` is not yet fully stabilized as a type you can name in all positions, but it is usable in return position (`fn diverge() -> !`) and the compiler uses it internally everywhere. The standard library provides **`Infallible`** (`enum Infallible {}`) as a stable stand-in: an empty enum with no variants that can never be constructed, serving the same role as `!` in type positions like `Result<T, Infallible>`.

**Empty enums** (`enum Void {}`) follow the same principle: no variants means no values, and `match` on an empty enum requires zero arms, making exhaustiveness trivially satisfied.

## What constraint it enforces

**A function returning `!` or `Infallible` is guaranteed by the compiler to never return normally. Code after a diverging expression is unreachable.**

- The compiler proves that all paths through a `-> !` function diverge (loop, panic, process exit).
- `Result<T, Infallible>` signals to callers that the operation cannot fail -- `.unwrap()` is safe because `Err` can never be constructed.
- `!` coerces to any type, enabling diverging expressions in any type context.

## Minimal snippet

```rust
fn forever() -> ! {
    loop {
        // never returns
    }
}

fn parse_or_exit(s: &str) -> i32 {
    match s.parse::<i32>() {
        Ok(n) => n,
        Err(_) => {
            eprintln!("invalid integer");
            std::process::exit(1)   // returns !, coerces to i32
        }
    }
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Pattern matching** [-> catalog/T14](T14-type-narrowing.md) | Diverging arms in `match` coerce to the expected type. `Err(e) => panic!("{e}")` satisfies any return type. |
| **Null safety (Option)** [-> catalog/T13](T13-null-safety.md) | `Option<!>` can only be `None` -- `Some(!)` is uninhabitable. Useful in generic code that must be `Option` but never `Some`. |
| **Effect tracking (Result)** [-> catalog/T12](T12-effect-tracking.md) | `Result<T, Infallible>` indicates infallible operations. The `From<Infallible>` impl converts to any error type. |
| **Algebraic data types** [-> catalog/T01](T01-algebraic-data-types.md) | Empty enums are sum types with zero variants -- the type-level encoding of "impossible." |
| **Compile-time ops** [-> catalog/T16](T16-compile-time-ops.md) | `const` panics become compile errors, which is `!` at compile time -- the computation never produces a value. |

## Gotchas and limitations

1. **`!` is not fully stabilized.** You cannot write `let x: ! = ...` on stable Rust in all contexts. Use `Infallible` or empty enums as workarounds.

2. **`Infallible` and `!` are not yet unified.** They serve the same logical role but are different types. The plan is to make `Infallible` a type alias for `!` once `!` is fully stabilized.

3. **Unreachable code warnings.** Code after a diverging expression triggers `warning: unreachable expression`. This is usually correct -- if you see it unexpectedly, a branch is diverging when you did not intend it to.

4. **`!` in trait impls.** Implementing a trait for `!` is possible on nightly (`#![feature(never_type)]`) and allows generic code to handle the "impossible" case uniformly.

5. **Empty enums need `match` with no arms.** `match void {}` is valid and exhaustive when `void` is of an empty enum type. Beginners may not realize a zero-arm match is legal.

## Beginner mental model

Think of `!` as a **black hole** in the type system. A function returning `!` is a one-way street: execution enters but never comes back. Because the value can never exist, the compiler lets you pretend it is any type you need -- a `!` value would satisfy any obligation if it could exist, and since it cannot, there is no contradiction.

## Example A -- Infallible conversion with Result

```rust
use std::convert::Infallible;

fn always_works(s: &str) -> Result<String, Infallible> {
    Ok(s.to_uppercase())
}

fn main() {
    // Safe to unwrap -- Err(Infallible) can never be constructed
    let val = always_works("hello").unwrap();
    println!("{val}");  // HELLO

    // Or use into_ok() on nightly:
    // let val = always_works("hello").into_ok();
}
```

## Example B -- Empty enum as proof of impossibility

```rust
enum Void {}

fn handle_void(v: Void) -> i32 {
    match v {}  // zero arms -- exhaustive because Void has no variants
}

// This function signature guarantees it never returns an error
fn infallible_parse(n: u32) -> Result<String, Void> {
    Ok(n.to_string())
}

fn main() {
    match infallible_parse(42) {
        Ok(s) => println!("{s}"),
        Err(v) => match v {},  // unreachable but type-safe
    }
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- `!` and empty enums make certain error states literally unrepresentable at the type level.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- `Result<T, Infallible>` satisfies `Result`-based trait bounds while communicating infallibility.

## Source anchors

- `book/src/ch19-04-advanced-types.md` -- "The Never Type that Never Returns"
- `rust-reference/src/types/never.md`
- `std::convert::Infallible` documentation
- `nomicon/src/exotic-sizes.md` -- empty types
