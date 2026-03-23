# Serialization with Serde

## The constraint

Data structures must be convertible to and from wire formats (JSON, TOML, bincode, etc.) with compile-time type safety. The serde ecosystem uses derive macros to generate serialization code, and the type system ensures that only types implementing `Serialize` / `Deserialize` can be encoded or decoded.

## Feature toolkit

- `[-> T06](../catalog/T06-derivation.md)`
- `[-> T05](../catalog/T05-type-classes.md)`
- `[-> T17](../catalog/T17-macros-metaprogramming.md)`
- `[-> T18](../catalog/T18-conversions-coercions.md)`

## Patterns

- Pattern A: derive `Serialize` and `Deserialize` for automatic conversion.
```rust
use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Debug)]
struct Config {
    host: String,
    port: u16,
    debug: bool,
}

let cfg = Config { host: "localhost".into(), port: 8080, debug: true };
let json = serde_json::to_string(&cfg).unwrap();
let parsed: Config = serde_json::from_str(&json).unwrap();
```

- Pattern B: serde attributes for field-level control.
```rust
use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize)]
struct User {
    #[serde(rename = "user_name")]
    name: String,
    #[serde(default)]
    role: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    avatar: Option<String>,
}
```

- Pattern C: enum serialization with tagged representations.
```rust
use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize)]
#[serde(tag = "type")]
enum Event {
    Click { x: i32, y: i32 },
    KeyPress { key: String },
    Scroll { delta: f64 },
}
// Serializes as: {"type":"Click","x":10,"y":20}
```

- Pattern D: custom serializer for domain types.
```rust
use serde::{Serialize, Serializer, Deserialize, Deserializer};

struct Timestamp(u64);

impl Serialize for Timestamp {
    fn serialize<S: Serializer>(&self, s: S) -> Result<S::Ok, S::Error> {
        s.serialize_str(&format!("{}ms", self.0))
    }
}

impl<'de> Deserialize<'de> for Timestamp {
    fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        let s = String::deserialize(d)?;
        let n = s.trim_end_matches("ms").parse::<u64>()
            .map_err(serde::de::Error::custom)?;
        Ok(Timestamp(n))
    }
}
```

## Tradeoffs

- Derive macros eliminate boilerplate but hide the generated code — errors in attribute usage surface as cryptic proc-macro diagnostics.
- serde's data model is format-agnostic, but some formats impose restrictions (e.g., JSON keys must be strings).
- Custom `Serialize`/`Deserialize` impls give full control but must be maintained alongside field changes.

## When to use which feature

- Derive `Serialize`/`Deserialize` for most data types — it covers the vast majority of use cases.
- Use serde attributes (`rename`, `default`, `skip`, `tag`) for format-level customization.
- Implement custom serializers only when the wire format differs fundamentally from the struct layout.
- Use generic `T: Serialize` bounds to write format-agnostic utility functions.

## Source anchors

- [serde.rs — Overview](https://serde.rs/)
- [serde.rs — Derive](https://serde.rs/derive.html)
- [serde.rs — Attributes](https://serde.rs/attributes.html)
- [serde.rs — Custom serialization](https://serde.rs/custom-serialization.html)
- [serde.rs — Enum representations](https://serde.rs/enum-representations.html)
