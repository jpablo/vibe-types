# Preventing Invalid States

## The constraint

Represent only valid domain states in types so invalid combinations cannot compile.

## Feature toolkit

- `[-> T01](T01-algebraic-data-types.md)`
- `[-> T18](T18-conversions-coercions.md)`

## Patterns

- Pattern A: enums for closed alternatives.
```rust
enum AuthState { Anonymous, LoggedIn { user_id: u64 } }
```
- Pattern B: smart constructor + private newtype field.
```rust
pub struct Guess(i32);
impl Guess {
    pub fn new(v: i32) -> Self {
        assert!((1..=100).contains(&v));
        Self(v)
    }
}
```

- Pattern C: parse, don't validate — return a refined type instead of panicking.
```rust
use std::num::NonZeroU16;

// Validation: checks and panics — caller gains no type-level info
fn validate_port(n: u16) {
    assert!(n > 0 && n < 65536, "invalid port");
}

// Parsing: checks and returns a refined type
#[derive(Debug, Clone, Copy)]
pub struct PortNumber(NonZeroU16);

impl PortNumber {
    pub fn parse(n: u16) -> Result<Self, &'static str> {
        NonZeroU16::new(n)
            .filter(|p| p.get() < 65536)
            .map(PortNumber)
            .ok_or("port must be 1..65535")
    }

    pub fn get(self) -> u16 {
        self.0.get()
    }
}

// Also works via TryFrom for idiomatic conversion
impl TryFrom<u16> for PortNumber {
    type Error = &'static str;
    fn try_from(n: u16) -> Result<Self, Self::Error> {
        Self::parse(n)
    }
}

// Downstream code never needs to re-validate
fn connect(port: PortNumber) {
    println!("Connecting to port {}", port.get()); // always valid
}
```

**Key insight:** functions returning `()` or panicking after checks are validation — they discard the information. Functions returning `Result<T, E>` or `Option<T>` with a refined type are parsing — they preserve it. Prefer parsing. Rust's `TryFrom` trait is the idiomatic way to express a parsing conversion.

See: [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)

## Tradeoffs

- Better safety and clearer intent at the cost of extra wrapper/constructor code.
- Aliases alone are insufficient for strong boundaries; prefer newtypes for true separation.

## When to use which feature

- Use enums for closed state spaces.
- Use newtypes for stronger boundaries around primitives.

## Source anchors

- `book/src/ch06-01-defining-an-enum.md`
- `book/src/ch09-03-to-panic-or-not-to-panic.md`
- `book/src/ch20-03-advanced-types.md`
