# Effect Tracking (via Result and the ? Operator)

Since: Rust 1.0 (`Result`); Rust 1.13 (`?` operator); Rust 1.39 (`async`/`await`)

## What it is

Rust does not have a formal effect system, but achieves the same constraint through **types that encode effects in the return signature**. The two primary mechanisms are:

**`Result<T, E>` + `?` for error effects.** Any function that can fail returns `Result<T, E>`. The `?` operator propagates errors early -- if the expression evaluates to `Err(e)`, the function returns `Err(e.into())` immediately. Because `Result` is in the return type, every caller in the chain *must* handle or propagate the error. Errors cannot be silently ignored.

**`async`/`await` for async effects.** An `async fn` returns `impl Future<Output = T>` instead of `T`. The caller must `.await` or spawn the future to drive it to completion. The `async` keyword in the signature makes the effect visible and forces callers to handle it.

**`unsafe` as an effect boundary.** `unsafe` blocks and `unsafe fn` mark code where the compiler cannot guarantee safety. The `unsafe` keyword acts as an effect marker: callers of `unsafe` functions must acknowledge the boundary with their own `unsafe` block.

Together these mechanisms ensure effects are **tracked in the type system and propagated explicitly**.

## What constraint it enforces

**Functions must declare their effects in their signatures, and callers must explicitly handle or propagate those effects.**

- A function returning `Result<T, E>` cannot have its error silently discarded -- the compiler warns on unused `Result` (`#[must_use]`).
- `?` only works inside functions that return `Result` (or `Option`), preventing accidental use in non-error-aware contexts.
- `async` functions cannot be called without `.await` or explicit future handling. The effect is visible at every call site.
- `unsafe` blocks require the programmer to explicitly opt in to unchecked operations.

## Minimal snippet

```rust
use std::fs;
use std::io;

fn read_config(path: &str) -> Result<String, io::Error> {
    let content = fs::read_to_string(path)?;  // ? propagates io::Error
    Ok(content.trim().to_owned())
}

fn main() {
    match read_config("config.toml") {
        Ok(cfg)  => println!("config: {cfg}"),
        Err(e)   => eprintln!("error: {e}"),
    }
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Null safety (Option)** [-> catalog/T13](T13-null-safety.md) | `Option<T>` and `Result<T, E>` share combinators (`map`, `and_then`, `?`). `opt.ok_or(err)` converts between them. |
| **Pattern matching** [-> catalog/T14](T14-type-narrowing.md) | `match result { Ok(v) => ..., Err(e) => ... }` narrows `Result` into its success or error type. |
| **Never type** [-> catalog/T34](T34-never-bottom.md) | `Result<T, Infallible>` signals that an operation cannot fail, making error handling a no-op. |
| **Traits** [-> catalog/T05](T05-type-classes.md) | The `Error` trait standardizes error types. `From` impls enable `?` to convert between error types automatically. |
| **Derive macros** [-> catalog/T06](T06-derivation.md) | `#[derive(thiserror::Error)]` generates `Display` and `Error` impls, reducing error-type boilerplate. |

## Gotchas and limitations

1. **`?` is not exception handling.** It is syntactic sugar for early return on `Err`. There is no stack unwinding, no try/catch, and no implicit propagation. Every function in the chain must have `Result` in its return type.

2. **Error type conversion with `?`.** The `?` operator calls `From::from(err)` to convert the error type. If the source error type does not implement `From` into the target, `?` will not compile. Use `map_err` for custom conversions.

3. **`unwrap()` hides the effect.** Calling `.unwrap()` on a `Result` converts it from "may fail" to "panics on failure." This masks the effect and should be avoided in production code.

4. **No checked effects for panics.** Panics (`panic!`, array out-of-bounds) are not tracked in the type system. A function with return type `T` may still panic. This is a deliberate trade-off for ergonomics.

5. **`async` color problem.** Once a function is `async`, every caller must also be async (or use a runtime's `block_on`). This "function coloring" can propagate through the entire call stack.

6. **`unsafe` is an assertion, not a guarantee.** `unsafe` says "I vouch for correctness here." The compiler does not verify the contents -- it trusts the programmer within the `unsafe` block.

## Beginner mental model

Think of `Result<T, E>` as a **stamped envelope**. The stamp says either "success" or "error." Every function that handles the envelope must check the stamp before reading the contents. The `?` operator is a mail sorter: it checks the stamp and, if it says "error," forwards the envelope back up the chain without opening it. No one can pretend the stamp is not there.

## Example A -- Error propagation with ? and From

```rust
use std::num::ParseIntError;

#[derive(Debug)]
enum AppError {
    Parse(ParseIntError),
    OutOfRange,
}

impl From<ParseIntError> for AppError {
    fn from(e: ParseIntError) -> Self { AppError::Parse(e) }
}

fn parse_port(s: &str) -> Result<u16, AppError> {
    let n: u16 = s.parse()?;           // ? converts ParseIntError -> AppError
    if n == 0 { return Err(AppError::OutOfRange); }
    Ok(n)
}

fn main() {
    println!("{:?}", parse_port("8080"));   // Ok(8080)
    println!("{:?}", parse_port("abc"));    // Err(Parse(...))
    println!("{:?}", parse_port("0"));      // Err(OutOfRange)
}
```

## Example B -- Async effect tracking

```rust
async fn fetch_data(url: &str) -> Result<String, reqwest::Error> {
    let body = reqwest::get(url).await?.text().await?;
    Ok(body)
}

// Caller must also be async or use block_on:
// #[tokio::main]
// async fn main() {
//     match fetch_data("https://example.com").await {
//         Ok(body) => println!("{}", &body[..80]),
//         Err(e)   => eprintln!("fetch failed: {e}"),
//     }
// }
```

The `async` keyword and `Result` return type make both effects (asynchrony and fallibility) visible in the signature.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- `Result` prevents ignoring errors, eliminating a class of invalid program states.
- [-> UC-23](../usecases/UC23-diagnostics.md) -- "`?` operator can only be used in a function that returns `Result`" is a common and instructive error.
- [-> UC-22](../usecases/UC22-conversions.md) -- `From` impls between error types enable seamless `?` propagation across module boundaries.

## Recommended libraries

| Library | Description |
|---------|-------------|
| [anyhow](https://docs.rs/anyhow) | Application-level error handling with context chaining and type-erased errors |
| [thiserror](https://docs.rs/thiserror) | Derive macro for custom error types with `Display` and `From` impls |
| [tokio](https://docs.rs/tokio) | Async runtime for driving `Future`-based code — the standard executor for async Rust |
| [color-eyre](https://docs.rs/color-eyre) | Colorized error reports with `SpanTrace` and `BackTrace` support for diagnostics |

## Source anchors

- `book/src/ch09-02-recoverable-errors-with-result.md`
- `book/src/ch09-03-to-panic-or-not-to-panic.md`
- `rust-reference/src/expressions/operator-expr.md` -- question mark operator
- `std::result` module documentation
- `book/src/ch17-01-what-is-oo.md` -- async/await
