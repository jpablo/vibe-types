# Refinement Types

> **Since:** Pattern-level (newtype + smart constructor) | **Library support:** nutype, refined_type, bounded-integer

## What it is

Rust does not have built-in refinement types, but the newtype + private field + fallible constructor pattern achieves the same effect: a value of type `PortNumber` is a `u16` that has been validated to be in range. The predicate is enforced by the constructor, and the private field prevents bypassing it.

Several crates automate this pattern:

- **[nutype](https://github.com/greyblake/nutype)** — Derive macro that generates validated newtypes with compile-time checks for literals. The closest Rust gets to declarative refinement types.
- **[bounded-integer](https://docs.rs/bounded-integer)** — Macro for integer types with compile-time range bounds.

## What constraint it enforces

**A refined value can only be constructed through a validated path (smart constructor returning `Result`). The private inner field prevents direct construction, so holding a value of the refined type guarantees the predicate holds.**

## Minimal snippet

### Manual pattern

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PosU32(u32);  // private field

impl PosU32 {
    pub fn new(n: u32) -> Result<Self, &'static str> {
        if n > 0 { Ok(Self(n)) } else { Err("must be positive") }
    }

    pub fn get(self) -> u32 { self.0 }
}

// PosU32(0) — compile error: field is private
// PosU32::new(0) — returns Err
let x = PosU32::new(42).unwrap(); // Ok(PosU32(42))
```

### Using nutype

```rust
use nutype::nutype;

#[nutype(
    validate(greater = 0),
    derive(Debug, Clone, Copy, PartialEq, Eq)
)]
pub struct PosU32(u32);

let x = PosU32::try_new(42);  // Ok(PosU32(42))
let y = PosU32::try_new(0);   // Err(PosU32Error::GreaterViolated)

// For literals, nutype also provides a const constructor macro:
// let z = PosU32!(42);  // checked at compile time
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Structs, enums, newtypes** [-> T01](T01-algebraic-data-types.md)(T01-algebraic-data-types.md) | Refinement types are built on top of the newtype pattern — a single-field struct with a private field. |
| **Traits & impls** [-> T05](T05-type-classes.md)(T05-type-classes.md) | Refined types can implement `TryFrom<T>`, `Display`, `Serialize`/`Deserialize`, etc., integrating with the ecosystem. |
| **Generics & where clauses** [-> T04](T04-generics-bounds.md)(T04-generics-bounds.md) | Generic code can accept refined types via trait bounds, or be generic over the refinement predicate. |
| **Const generics** [-> T15](T15-const-generics.md)(T15-const-generics.md) | `bounded-integer` uses const generics to encode bounds in the type: `BoundedU16<1, 65535>`. |

## Gotchas and limitations

1. **No compile-time checking for non-literals.** Unlike Lean's proof system, Rust cannot verify predicates on arbitrary expressions at compile time. Dynamic values always go through a `Result`-returning constructor.

2. **Boilerplate without macros.** The manual pattern requires writing `new()`, `get()`, `TryFrom`, `Display`, etc. for every refined type. `nutype` eliminates most of this.

3. **Private field ≠ proof.** The guarantee rests on the module boundary — `pub(crate)` fields or `unsafe` can bypass the constructor. Keep the inner field strictly private.

4. **Serialization round-trips.** When deserializing a refined type (e.g., from JSON), the deserializer must go through the validating constructor. Libraries like `nutype` provide `serde` integration that does this automatically.

## Beginner mental model

Think of a refined type as a **locked box with a validator at the entrance**. You can only put values in through the validator (`try_new`), and once inside, the value is guaranteed valid. The lock is the private field — you can't reach in and change the value without going through the validator again.

## Example A — Domain model with refined fields

```rust
use nutype::nutype;

#[nutype(validate(greater = 0, less = 65536), derive(Debug, Clone, Copy))]
pub struct Port(u16);

#[nutype(validate(not_empty, len_char_max = 254, regex = r"^[\w.+-]+@[\w-]+\.[\w.]+$"), derive(Debug, Clone))]
pub struct Email(String);

#[nutype(validate(not_empty, len_char_max = 32), derive(Debug, Clone))]
pub struct Username(String);

pub struct ServerConfig {
    pub host: String,
    pub port: Port,
    pub admin_email: Email,
}
```

## Example B — Parse, don't validate with TryFrom

```rust
use std::convert::TryFrom;

#[derive(Debug, Clone, Copy)]
pub struct Port(u16);

impl TryFrom<u16> for Port {
    type Error = &'static str;
    fn try_from(n: u16) -> Result<Self, Self::Error> {
        if n > 0 && n < 65536 { Ok(Self(n)) } else { Err("port must be 1..65535") }
    }
}

// Parse from string in one step
impl TryFrom<&str> for Port {
    type Error = String;
    fn try_from(s: &str) -> Result<Self, Self::Error> {
        let n: u16 = s.parse().map_err(|e| format!("not a number: {e}"))?;
        Port::try_from(n).map_err(|e| e.to_string())
    }
}

fn connect(port: Port) {
    println!("Connecting to port {}", port.0); // always valid
}
```

## Recommended libraries

| Library | Style | Key strength |
|---------|-------|-------------|
| [nutype](https://github.com/greyblake/nutype) | Derive macro on newtype | Declarative, serde support, compile-time literal checks |
| [bounded-integer](https://docs.rs/bounded-integer) | Const-generic bounded int | Zero-overhead bounded integers |

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Refined newtypes make invalid values unconstructable.
- [-> UC-04](../usecases/UC04-generic-constraints.md) — Refined types as trait-bounded generic constraints.

## Source anchors

- [nutype documentation](https://docs.rs/nutype)
- [The Rust Book — Using Newtype Pattern](https://doc.rust-lang.org/book/ch19-04-advanced-types.html)
- [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)
