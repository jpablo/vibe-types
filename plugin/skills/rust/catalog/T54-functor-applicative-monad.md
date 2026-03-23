# Functor, Applicative, and Monad (via Iterator, Option, and Result)

> **Since:** Rust 1.0 (Iterator, Option, Result); stable

## What it is

Rust has no `Functor`, `Applicative`, or `Monad` traits, but the patterns they encode are pervasive in the standard library. **Iterator** is a Functor: `map` transforms each element without changing the iteration structure. **Option** and **Result** provide `map` (Functor), `and_then` (monadic bind / `flatMap`), and constructor functions like `Some`/`Ok` (analogous to `pure`). The **`?` operator** is Rust's equivalent of do-notation for `Result` and `Option` — it desugars to an early return on the error/none case, enabling monadic chaining with imperative syntax.

Because Rust lacks higher-kinded types (`F[_]`), you cannot write a single generic `Monad` trait that abstracts over `Option`, `Result`, `Vec`, etc. Instead, each type provides its own `map` and `and_then` methods with consistent semantics. Libraries like `futures` extend these patterns to async contexts with `map`, `and_then`, and `then` on `Future`.

## What constraint it enforces

**Each type's `map` and `and_then` methods enforce that transformations stay within the type's context (Option remains Option, Result remains Result), and the `?` operator enforces that error/absence handling is explicit and propagated through the call chain.**

## Minimal snippet

```rust
fn parse_and_double(s: &str) -> Result<i64, String> {
    s.parse::<i64>()
        .map_err(|e| e.to_string())  // Functor over the error
        .map(|n| n * 2)              // Functor over the value
}

fn add_parsed(a: &str, b: &str) -> Result<i64, String> {
    // ? operator = monadic bind with early return
    let x = a.parse::<i64>().map_err(|e| e.to_string())?;
    let y = b.parse::<i64>().map_err(|e| e.to_string())?;
    Ok(x + y)
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Iterator** [-> T04](T04-generics-bounds.md) | `Iterator::map`, `filter`, `flat_map` are Functor/Monad operations over sequences. `collect` is the terminal operation that realizes the chain. |
| **Option and Result** [-> T13](T13-null-safety.md) | `Option::map`, `Option::and_then`, `Result::map`, `Result::and_then` provide Functor and Monad operations for nullable and fallible values. |
| **`?` operator** [-> T12](T12-effect-tracking.md) | The `?` operator desugars to a match + early return, acting as Rust's do-notation for `Result` and `Option`. Works with any type implementing `Try`. |
| **Closures and Fn traits** | `map` and `and_then` accept closures (`FnOnce`), making transformation chains ergonomic and zero-cost after inlining. |
| **Async/await** | `Future::map` and `Future::and_then` (from the `futures` crate) extend the pattern to async contexts. `async`/`await` is the do-notation for futures. |

## Gotchas and limitations

1. **No higher-kinded types.** You cannot write `fn lift<F: Functor, A, B>(f: fn(A) -> B, fa: F<A>) -> F<B>` in Rust. Each type's `map` is an inherent method, not a trait method on a unified `Functor` trait. GATs (generic associated types, stable since 1.65) enable some workarounds but not full HKT.

2. **`and_then` vs `flat_map` naming.** `Option` and `Result` use `and_then` for monadic bind, while `Iterator` uses `flat_map`. The semantics are the same but the names differ, which can confuse newcomers.

3. **`?` only works in functions returning `Result` or `Option`.** You cannot use `?` in `main()` unless `main` returns `Result`. Since Rust 1.26, `fn main() -> Result<(), E>` is supported.

4. **No Applicative accumulation.** There is no built-in way to run multiple `Result` computations and accumulate all errors. `?` short-circuits on the first error. For accumulation, use a crate like `frunk` or collect results manually.

5. **Iterator laziness.** `Iterator::map` is lazy — nothing happens until you consume the iterator (e.g., with `collect`, `for_each`, `sum`). Forgetting to consume produces a compiler warning but no results.

## Beginner mental model

Think of `Option` as a box that might be empty and `Result` as a box that holds either a value or an error. `map` lets you transform the value inside without opening the box manually. `and_then` lets you chain operations where each step might produce a new box (and any empty/error box short-circuits the chain). The `?` operator is a shorthand: "if the box has a value, unwrap it and continue; if not, return the error/none immediately." Iterator works the same way but for sequences of values.

## Example A -- Chaining Option with and_then

```rust
fn get_first_char_upper(s: Option<&str>) -> Option<char> {
    s.and_then(|s| s.chars().next())     // monadic bind: Option -> Option
     .map(|c| c.to_ascii_uppercase())    // functor: transform inner value
}

fn main() {
    assert_eq!(get_first_char_upper(Some("hello")), Some('H'));
    assert_eq!(get_first_char_upper(Some("")), None);
    assert_eq!(get_first_char_upper(None), None);
}
```

## Example B -- Error propagation with ?

```rust
use std::num::ParseIntError;

#[derive(Debug)]
struct Config { width: u32, height: u32 }

fn parse_config(w: &str, h: &str) -> Result<Config, ParseIntError> {
    // Each ? is a monadic bind — early return on Err
    let width = w.parse()?;
    let height = h.parse()?;
    Ok(Config { width, height })
}

fn main() {
    println!("{:?}", parse_config("80", "24"));   // Ok(Config { width: 80, height: 24 })
    println!("{:?}", parse_config("80", "abc"));  // Err(ParseIntError { .. })
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- `Option` and `Result` chaining prevents operating on absent or erroneous values.
- [-> UC-08](../usecases/UC08-error-handling.md) -- `?` operator and `Result::and_then` provide composable, type-safe error propagation.
- [-> UC-13](../usecases/UC13-state-machines.md) -- Iterator combinators encode stateful pipelines as lazy, composable chains.
- [-> UC-20](../usecases/UC20-ownership-apis.md) -- `map` and `and_then` consume owned values, enforcing move semantics through the chain.

## Source anchors

- `book/src/ch06-02-match.md` (Option pattern matching)
- `book/src/ch09-02-recoverable-errors-with-result.md` (Result and `?`)
- `book/src/ch13-02-iterators.md` (Iterator map/filter/flat_map)
- `rust-by-example/src/error/option_unwrap/and_then.md`
- `std::option::Option::and_then`, `std::result::Result::and_then`
