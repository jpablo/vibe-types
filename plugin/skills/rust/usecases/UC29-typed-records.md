# Typed Records

## The constraint

Data should be modeled as named-field structs so the compiler checks field names, types, and completeness at every construction and access site. Struct update syntax and destructuring provide ergonomic manipulation while maintaining full type safety.

## Feature toolkit

- `[-> T31](../catalog/T31-record-types.md)`
- `[-> T06](../catalog/T06-derivation.md)`
- `[-> T01](../catalog/T01-algebraic-data-types.md)`

## Patterns

- Pattern A: named-field struct with derived traits.
```rust
#[derive(Debug, Clone, PartialEq)]
struct User {
    name: String,
    email: String,
    age: u32,
}

let alice = User {
    name: "Alice".into(),
    email: "alice@example.com".into(),
    age: 30,
};
// Missing fields are a compile error:
// let bad = User { name: "Bob".into() };  // error: missing `email` and `age`
```

- Pattern B: struct update syntax for partial copying.
```rust
#[derive(Debug, Clone)]
struct Config {
    host: String,
    port: u16,
    debug: bool,
    max_connections: u32,
}

let default_cfg = Config {
    host: "localhost".into(),
    port: 8080,
    debug: false,
    max_connections: 100,
};

let dev_cfg = Config {
    debug: true,
    port: 3000,
    ..default_cfg.clone()  // remaining fields from default_cfg
};
```

- Pattern C: destructuring for field extraction.
```rust
struct Point { x: f64, y: f64, z: f64 }

fn distance_2d(p: &Point) -> f64 {
    let Point { x, y, .. } = p;  // destructure, ignore z
    (x * x + y * y).sqrt()
}

// Destructuring in match arms:
fn classify(p: &Point) -> &str {
    match p {
        Point { x, y, .. } if *x == 0.0 && *y == 0.0 => "origin",
        Point { z, .. } if *z > 100.0 => "high altitude",
        _ => "general",
    }
}
```

- Pattern D: tuple structs and unit structs for simple records.
```rust
struct Meters(f64);       // tuple struct — positional access
struct Marker;            // unit struct — zero-size type

let distance = Meters(42.0);
println!("{}", distance.0);  // access via .0

fn tag(_: Marker) { println!("tagged"); }
```

## Tradeoffs

- Named-field structs are self-documenting and compiler-checked but more verbose than tuples for simple groupings.
- Struct update syntax (`..base`) is ergonomic but moves fields from the source unless the type is `Clone`.
- Destructuring ensures all used fields are valid but requires updating patterns when fields are added.

## When to use which feature

- Use named-field structs for domain entities with multiple fields.
- Use struct update syntax for creating variations of a base configuration or record.
- Use destructuring in function parameters and match arms for clear, concise field access.
- Use tuple structs for newtype wrappers around a single value.
- Use private fields with public constructors to enforce invariants.

## Source anchors

- `book/src/ch05-01-defining-structs.md`
- `book/src/ch05-02-example-structs.md`
- `book/src/ch18-03-pattern-syntax.md`
- `rust-by-example/src/custom_types/structs.md`
- `rust-by-example/src/flow_control/match/destructuring/destructure_structures.md`
