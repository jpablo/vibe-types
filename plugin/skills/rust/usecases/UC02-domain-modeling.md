# Domain Modeling

## The constraint

Represent domain concepts as distinct, composable types so that business rules are enforced by the compiler rather than by convention or runtime checks.

## Feature toolkit

- `[-> T01](../catalog/T01-algebraic-data-types.md)` — structs, enums, newtypes
- `[-> T03](../catalog/T03-newtypes-opaque.md)` — opaque wrappers for primitive boundaries
- `[-> T06](../catalog/T06-derivation.md)` — derive common traits automatically
- `[-> T21](../catalog/T21-encapsulation.md)` — visibility and module boundaries

## Patterns

- Pattern A: newtypes to distinguish primitives with the same representation.
```rust
struct UserId(u64);
struct OrderId(u64);

fn cancel_order(_user: UserId, _order: OrderId) { /* ... */ }

// cancel_order(OrderId(1), UserId(2));  // error[E0308]: mismatched types
```

- Pattern B: enums for closed domain alternatives.
```rust
enum Currency { Usd, Eur, Gbp }
enum Payment {
    Card { last_four: String, currency: Currency },
    BankTransfer { iban: String },
    Crypto { wallet: String },
}
```

- Pattern C: struct composition over inheritance.
```rust
struct Address { street: String, city: String, zip: String }
struct Customer { name: String, billing: Address, shipping: Address }
```

- Pattern D: builder pattern for complex construction.
```rust
struct Config { host: String, port: u16, retries: u32 }

struct ConfigBuilder { host: Option<String>, port: Option<u16>, retries: u32 }

impl ConfigBuilder {
    fn new() -> Self { Self { host: None, port: None, retries: 3 } }
    fn host(mut self, h: impl Into<String>) -> Self { self.host = Some(h.into()); self }
    fn port(mut self, p: u16) -> Self { self.port = Some(p); self }
    fn build(self) -> Result<Config, &'static str> {
        Ok(Config {
            host: self.host.ok_or("host required")?,
            port: self.port.ok_or("port required")?,
            retries: self.retries,
        })
    }
}
```

## Tradeoffs

| Approach | Strength | Weakness |
|----------|----------|----------|
| Newtypes | Zero-cost type distinction | Boilerplate for conversions/trait impls |
| Enums | Exhaustive matching, closed set | Cannot add variants without modifying the enum |
| Struct composition | Flexible, clear ownership | Deeper nesting can obscure relationships |
| Builder | Incremental, validated construction | Extra code vs direct struct literal |

## When to use which feature

- Use newtypes when two values share a representation but must not be mixed (IDs, units, tokens).
- Use enums when the domain has a fixed set of alternatives.
- Use struct composition to combine reusable value objects.
- Use builders when construction involves defaults, validation, or many optional fields.

## Source anchors

- `book/src/ch05-01-defining-structs.md`
- `book/src/ch06-01-defining-an-enum.md`
- `book/src/ch20-03-advanced-types.md`
- `rust-by-example/src/custom_types/structs.md`
