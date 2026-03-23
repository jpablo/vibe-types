# Null Safety via Option

## The constraint

There is no `null` in Rust. Absence is represented by `Option<T>`, a sum type that is either `Some(value)` or `None`. The compiler forces callers to handle the `None` case before accessing the inner value, eliminating null-pointer errors at compile time.

## Feature toolkit

- `[-> T13](../catalog/T13-null-safety.md)`
- `[-> T01](../catalog/T01-algebraic-data-types.md)`
- `[-> T14](../catalog/T14-type-narrowing.md)`

## Patterns

- Pattern A: basic `Option` with pattern matching.
```rust
fn find_user(id: u64) -> Option<String> {
    if id == 1 { Some("Alice".into()) } else { None }
}

match find_user(1) {
    Some(name) => println!("Found: {name}"),
    None       => println!("Not found"),
}
```

- Pattern B: the `?` operator for early return on `None`.
```rust
fn full_name(first: Option<&str>, last: Option<&str>) -> Option<String> {
    let f = first?;  // returns None if first is None
    let l = last?;
    Some(format!("{f} {l}"))
}
```

- Pattern C: combinators for concise transformations.
```rust
let port: Option<u16> = Some(8080);

let addr = port
    .filter(|&p| p > 0)
    .map(|p| format!("127.0.0.1:{p}"))
    .unwrap_or_else(|| "127.0.0.1:80".into());
```

- Pattern D: `unwrap_or` and `unwrap_or_default` for safe defaults.
```rust
let config_timeout: Option<u64> = None;

let timeout = config_timeout.unwrap_or(30);        // 30
let retries: Option<u32> = None;
let r = retries.unwrap_or_default();                // 0 (u32::default())
```

- Pattern E: converting between `Option` and `Result`.
```rust
fn parse_port(s: &str) -> Result<u16, String> {
    s.parse::<u16>()
        .ok()                           // Result -> Option
        .filter(|&p| p > 0)
        .ok_or_else(|| format!("invalid port: {s}"))  // Option -> Result
}
```

## Tradeoffs

- `Option<T>` is zero-cost (niche optimization makes `Option<&T>` the same size as a raw pointer) but adds syntactic overhead compared to nullable references in other languages.
- Combinators like `map`/`and_then`/`filter` are concise but can be harder to debug than explicit `match`.
- `unwrap()` / `expect()` panic on `None`; prefer `?`, `unwrap_or`, or `match` in production code.

## When to use which feature

- Use `Option<T>` for any value that may be absent — function returns, struct fields, lookups.
- Use `?` in functions returning `Option` to propagate absence concisely.
- Use `unwrap_or` / `unwrap_or_default` when a sensible fallback exists.
- Reserve `unwrap()` / `expect()` for cases where `None` is a logic error (with a clear message).

## Source anchors

- `book/src/ch06-01-defining-an-enum.md`
- `book/src/ch06-02-match.md`
- `book/src/ch09-02-recoverable-errors-with-result.md`
- `rust-by-example/src/std/option.md`
- `rust-by-example/src/error/option_unwrap.md`
