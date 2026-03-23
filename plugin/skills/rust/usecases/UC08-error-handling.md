# Error Handling

## The constraint

Functions that can fail must declare failure in their return type. Callers must handle or propagate errors explicitly — silent error swallowing cannot compile.

## Feature toolkit

- `[-> T12](../catalog/T12-effect-tracking.md)` — Result, ? operator, effect tracking
- `[-> T01](../catalog/T01-algebraic-data-types.md)` — error enums as sum types
- `[-> T06](../catalog/T06-derivation.md)` — deriving Error with thiserror
- `[-> T18](../catalog/T18-conversions-coercions.md)` — From impls for ? conversion

## Patterns

- Pattern A: custom error enum with `thiserror`.
```rust
use thiserror::Error;

#[derive(Debug, Error)]
enum AppError {
    #[error("config not found: {0}")]
    ConfigMissing(String),
    #[error("invalid port: {0}")]
    BadPort(#[from] std::num::ParseIntError),
    #[error("IO failure")]
    Io(#[from] std::io::Error),
}

fn load_port(path: &str) -> Result<u16, AppError> {
    let text = std::fs::read_to_string(path)?;       // io::Error -> AppError
    let port: u16 = text.trim().parse()?;             // ParseIntError -> AppError
    Ok(port)
}
```

- Pattern B: `anyhow` for application-level error propagation.
```rust
use anyhow::{Context, Result};

fn setup() -> Result<()> {
    let cfg = std::fs::read_to_string("app.toml")
        .context("failed to read config")?;
    let port: u16 = cfg.trim().parse()
        .context("invalid port number")?;
    println!("listening on :{port}");
    Ok(())
}
```

- Pattern C: converting between `Option` and `Result`.
```rust
fn first_word(s: &str) -> Result<&str, &'static str> {
    s.split_whitespace().next().ok_or("empty string")
}
```

- Pattern D: the `?` chain — early return on error.
```rust
fn read_username() -> Result<String, std::io::Error> {
    let mut s = std::fs::read_to_string("username.txt")?;
    s.truncate(s.trim_end().len());
    Ok(s)
}
```

## Tradeoffs

| Approach | Strength | Weakness |
|----------|----------|----------|
| Custom error enum | Callers can match on specific variants | Boilerplate for From impls (mitigated by thiserror) |
| `anyhow::Error` | Minimal boilerplate, context chaining | Erases concrete type — cannot match on variants |
| `Box<dyn Error>` | No external deps, type-erased | Awkward downcasting, no context chain |
| `unwrap()` / `expect()` | Quick prototyping | Panics in production; hides the error effect |

## When to use which feature

- Use `thiserror` in libraries to define structured, matchable error types.
- Use `anyhow` in applications where callers only need to display or log errors.
- Use `?` everywhere to propagate errors — avoid `unwrap()` in production paths.
- Use `Result<T, Infallible>` to signal that a function cannot fail.

## Source anchors

- `book/src/ch09-02-recoverable-errors-with-result.md`
- `book/src/ch09-03-to-panic-or-not-to-panic.md`
- `rust-by-example/src/error/multiple_error_types.md`
- [thiserror documentation](https://docs.rs/thiserror)
- [anyhow documentation](https://docs.rs/anyhow)
