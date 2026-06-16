# Effect Tracking

## The constraint

Side effects — errors, asynchrony, unsafety — must be declared in the function signature so callers are forced to handle them. The inner value cannot be used without going through the effect wrapper (ignoring the wrapper itself is possible — `#[must_use]` is a warn-by-default lint, and `let _ =` silences it).

## Feature toolkit

- `[-> T12](../catalog/T12-effect-tracking.md)` — Result, async, unsafe as effects
- `[-> T13](../catalog/T13-null-safety.md)` — Option for absence
- `[-> T05](../catalog/T05-type-classes.md)` — Error trait, From conversions

## Patterns

- Pattern A: `Result<T, E>` tracks fallibility.
```rust
struct Config { port: u16 }
enum ConfigError { InvalidPort(std::num::ParseIntError) }

fn parse_config(s: &str) -> Result<Config, ConfigError> {
    let port: u16 = s.parse().map_err(ConfigError::InvalidPort)?;
    Ok(Config { port })
}
// Caller cannot reach the Config without going through the Result — match, ?, or a combinator
```

- Pattern B: `async` tracks asynchronous I/O.
```rust,ignore
async fn fetch(url: &str) -> Result<String, reqwest::Error> {
    let body = reqwest::get(url).await?.text().await?;
    Ok(body)
}
// Nothing runs until the caller .awaits or spawns — the async effect is visible in the type
// (dropping the Future without polling it is legal and does no work)
```

- Pattern C: `unsafe` as an effect boundary.
```rust
/// # Safety
/// `ptr` must be valid and aligned for `T`.
unsafe fn deref_raw<T>(ptr: *const T) -> T
where T: Copy
{
    // SAFETY: the caller guarantees `ptr` is valid and aligned (see doc contract above).
    unsafe { *ptr }
}

let val = 42;
// Must opt in to the unsafe effect:
let copied = unsafe { deref_raw(&val as *const i32) };
```

- Pattern D: combining effects — async + fallible.
```rust,ignore
async fn save_user(db: &Pool, user: &User) -> Result<(), DbError> {
    let conn = db.acquire().await?;    // async + fallible
    conn.execute("INSERT ...").await?; // async + fallible
    Ok(())
}
```

## Tradeoffs

| Effect | Mechanism | Strength | Weakness |
|--------|-----------|----------|----------|
| Error | `Result<T, E>` | Explicit, composable with `?` | Verbose for deeply nested call chains |
| Absence | `Option<T>` | Eliminates null | Double-wrapping (`Option<Option<T>>`) can confuse |
| Async | `async fn` → `Future` | Visible in signature, zero-cost | Function coloring — async propagates upward |
| Unsafe | `unsafe` blocks/fns | Narrows audit surface | Compiler trusts programmer inside the block |

## When to use which feature

- Return `Result` for any operation that can fail; avoid `panic!` in library code.
- Return `Option` for lookups that may not find a value.
- Mark functions `async` when they perform I/O or need to yield.
- Confine `unsafe` to the smallest possible block and document invariants.

## Source anchors

- `book/src/ch09-02-recoverable-errors-with-result.md`
- `book/src/ch17-01-futures-and-syntax.md` — async/await
- `book/src/ch20-01-unsafe-rust.md`
- `rust-reference/src/expressions/operator-expr.md` — ? operator
