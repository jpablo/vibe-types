# Builder and Configuration Patterns

## The constraint

Complex objects should be constructed incrementally with validation, defaults, and clear required-vs-optional distinction — enforced at compile time where possible.

## Feature toolkit

- `[-> T01](../catalog/T01-algebraic-data-types.md)` — structs for configuration data
- `[-> T06](../catalog/T06-derivation.md)` — derive Builder, Default
- `[-> T27](../catalog/T27-erased-phantom.md)` — PhantomData for typestate builders
- `[-> T03](../catalog/T03-newtypes-opaque.md)` — newtypes for validated config values

## Patterns

- Pattern A: `Default` trait for configuration with sensible defaults.
```rust
#[derive(Debug)]
struct ServerConfig {
    host: String,
    port: u16,
    max_connections: usize,
}

impl Default for ServerConfig {
    fn default() -> Self {
        Self { host: "127.0.0.1".into(), port: 8080, max_connections: 100 }
    }
}

// Struct update syntax for partial overrides
let cfg = ServerConfig { port: 3000, ..Default::default() };
```

- Pattern B: typestate builder — required fields enforced at compile time.
```rust
use std::marker::PhantomData;

struct Missing;
struct Set;

struct Builder<H, P> {
    host: Option<String>,
    port: Option<u16>,
    _state: PhantomData<(H, P)>,
}

impl Builder<Missing, Missing> {
    fn new() -> Self {
        Builder { host: None, port: None, _state: PhantomData }
    }
}

impl<P> Builder<Missing, P> {
    fn host(self, h: impl Into<String>) -> Builder<Set, P> {
        Builder { host: Some(h.into()), port: self.port, _state: PhantomData }
    }
}

impl<H> Builder<H, Missing> {
    fn port(self, p: u16) -> Builder<H, Set> {
        Builder { host: self.host, port: Some(p), _state: PhantomData }
    }
}

impl Builder<Set, Set> {
    fn build(self) -> ServerConfig {
        ServerConfig {
            host: self.host.unwrap(),
            port: self.port.unwrap(),
            max_connections: 100,
        }
    }
}

// Builder::new().build();           // error: no method `build` on Builder<Missing, Missing>
// Builder::new().host("x").build(); // error: no method `build` on Builder<Set, Missing>
let cfg = Builder::new().host("0.0.0.0").port(443).build(); // OK
```

- Pattern C: `derive_builder` for generated builders.
```rust
use derive_builder::Builder;

#[derive(Builder, Debug)]
#[builder(setter(into))]
struct AppConfig {
    host: String,
    port: u16,
    #[builder(default = "3")]
    retries: u32,
}

let cfg = AppConfigBuilder::default()
    .host("db.local")
    .port(5432u16)
    .build()
    .unwrap();
```

## Tradeoffs

| Approach | Strength | Weakness |
|----------|----------|----------|
| `Default` + struct update | Minimal code, idiomatic | No compile-time enforcement of required fields |
| Typestate builder | Missing fields are compile errors | Verbose, combinatorial state types |
| `derive_builder` | Zero boilerplate | Runtime error on missing fields, extra dependency |

## When to use which feature

- Use `Default` when all fields have sensible defaults and no field is strictly required.
- Use typestate builders in libraries where misconfiguration should be a compile error.
- Use `derive_builder` when builder ergonomics matter more than compile-time guarantees.

## Source anchors

- `book/src/ch05-01-defining-structs.md` — struct update syntax
- `std::default::Default` trait documentation
- [derive_builder documentation](https://docs.rs/derive_builder)
