# Exhaustive Matching

## The constraint

Every possible variant of an enum must be handled. Adding a new variant forces all consumers to update, preventing forgotten cases at compile time.

## Feature toolkit

- `[-> T01](../catalog/T01-algebraic-data-types.md)` — enums as sum types
- `[-> T14](../catalog/T14-type-narrowing.md)` — pattern matching and type narrowing

## Patterns

- Pattern A: `match` with exhaustiveness checking.
```rust
enum Command { Start, Stop, Restart }

fn handle(cmd: Command) -> &'static str {
    match cmd {
        Command::Start   => "starting",
        Command::Stop    => "stopping",
        Command::Restart => "restarting",
        // Adding Command::Pause later -> compile error here
    }
}
```

- Pattern B: `#[non_exhaustive]` for cross-crate evolution.
```rust
// In library crate:
#[non_exhaustive]
pub enum ApiError {
    NotFound,
    Unauthorized,
}

// In consumer crate — wildcard arm required:
fn describe(e: ApiError) -> &'static str {
    match e {
        ApiError::NotFound     => "not found",
        ApiError::Unauthorized => "unauthorized",
        _                      => "unknown error",  // required by #[non_exhaustive]
    }
}
```

- Pattern C: `let-else` for single-variant extraction with early return.
```rust
enum Packet { Data(Vec<u8>), Control }

fn process(pkt: Packet) {
    let Packet::Data(bytes) = pkt else {
        println!("ignoring control packet");
        return;
    };
    println!("processing {} bytes", bytes.len());
}
```

- Pattern D: `if let` for optional handling without exhaustiveness.
```rust
if let Some(user) = find_user(id) {
    greet(&user);
}
```

## Tradeoffs

| Approach | Strength | Weakness |
|----------|----------|----------|
| `match` (exhaustive) | Compiler catches missing variants | Verbose for enums with many variants |
| `#[non_exhaustive]` | Library can add variants without breaking semver | Consumers must always have a wildcard arm |
| `let-else` | Concise single-variant extraction | Only handles one variant; rest must diverge |
| `if let` | Convenient for optional handling | Silently ignores non-matching variants |

## When to use which feature

- Use `match` when every variant must be explicitly handled (state machines, command dispatch).
- Use `#[non_exhaustive]` on public enums in libraries that may evolve.
- Use `let-else` when you need one variant and want to bail early on anything else.
- Use `if let` for convenience when only one variant matters and ignoring others is correct.

## Source anchors

- `book/src/ch06-02-match.md`
- `book/src/ch18-01-all-the-places-for-patterns.md`
- `rust-reference/src/attributes/type_system.md` — `#[non_exhaustive]`
- `rust-by-example/src/flow_control/match.md`
