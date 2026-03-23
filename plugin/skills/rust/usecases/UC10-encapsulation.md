# Module Encapsulation

## The constraint

Internal implementation details must be hidden behind module boundaries. Only explicitly exposed items form the public API, preventing external code from depending on or constructing internal state.

## Feature toolkit

- `[-> T21](../catalog/T21-encapsulation.md)` — pub/private visibility system
- `[-> T03](../catalog/T03-newtypes-opaque.md)` — opaque newtypes with private fields
- `[-> T05](../catalog/T05-type-classes.md)` — sealed traits for closed extension

## Patterns

- Pattern A: private fields with constructor + accessor.
```rust
mod money {
    #[derive(Debug, Clone, Copy)]
    pub struct Cents(u64); // private field

    impl Cents {
        pub fn new(amount: u64) -> Self { Self(amount) }
        pub fn get(self) -> u64 { self.0 }
    }
}

// money::Cents(100);           // error: field `0` is private
let c = money::Cents::new(100); // OK
```

- Pattern B: `pub(crate)` for internal-only sharing.
```rust
mod db {
    pub struct Connection { /* ... */ }
    pub(crate) fn raw_query(_conn: &Connection, _sql: &str) {
        // Accessible within the crate but not to downstream users
    }
}
```

- Pattern C: sealed trait — a trait that external crates cannot implement.
```rust
mod sealed {
    pub trait Sealed {}       // private module -> trait is unnameable outside
}

pub trait Format: sealed::Sealed {
    fn render(&self) -> String;
}

pub struct Json;
impl sealed::Sealed for Json {}
impl Format for Json {
    fn render(&self) -> String { "{}".into() }
}

// External crates cannot implement Format because they cannot implement Sealed
```

- Pattern D: newtype boundary — exposing behavior without exposing representation.
```rust
mod auth {
    pub struct Token(String);

    impl Token {
        pub fn issue(user: &str) -> Self {
            Self(format!("tok_{user}_abc123"))
        }
        pub fn as_header(&self) -> String {
            format!("Bearer {}", self.0)
        }
    }
}

let t = auth::Token::issue("alice");
println!("{}", t.as_header());
// Cannot access t.0 or construct Token directly
```

## Tradeoffs

| Approach | Strength | Weakness |
|----------|----------|----------|
| Private fields | Forces validated construction paths | Requires explicit accessor methods |
| `pub(crate)` | Enables internal sharing without public exposure | Can leak if re-exported carelessly |
| Sealed traits | Prevents external implementations | Limits extensibility — cannot add impls downstream |
| Newtype boundary | Hides representation entirely | Boilerplate for forwarding trait impls |

## When to use which feature

- Default to private. Only add `pub` when an item is part of the intended API surface.
- Use `pub(crate)` for helpers shared across modules but not exposed to consumers.
- Use sealed traits when you need a closed set of implementors (e.g., format types, backends).
- Use newtypes when the internal representation must never leak to callers.

## Source anchors

- `book/src/ch07-03-paths-for-referring-to-an-item-in-the-module-tree.md`
- `rust-reference/src/visibility-and-privacy.md`
- `rust-by-example/src/mod/visibility.md`
- `api-guidelines/src/future-proofing.md` — sealed traits
