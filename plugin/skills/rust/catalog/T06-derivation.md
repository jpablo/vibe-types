# Derive Macros and Automatic Trait Implementation

Since: Rust 1.0 (`#[derive]`); Rust 1.15 (custom derive via proc macros)

## What it is

`#[derive(Debug, Clone, PartialEq, Serialize)]` instructs the compiler to **generate trait implementations** automatically from the shape of a struct or enum. For each listed trait the compiler inspects every field, confirms the field's type already implements the trait, and emits a mechanical `impl` block -- no hand-written code required.

The standard library provides built-in derives for: `Debug`, `Clone`, `Copy`, `PartialEq`, `Eq`, `Hash`, `Default`, `PartialOrd`, and `Ord`. Beyond these, **custom derive macros** (procedural macros of the `#[proc_macro_derive]` kind) let library authors define their own derivable traits -- `Serialize`, `Deserialize` (serde), `Error` (thiserror), `Builder`, and hundreds more from the ecosystem. Custom derives are implemented in separate `proc-macro` crates using the `syn` and `quote` libraries [-> catalog/T17](T17-macros-metaprogramming.md).

## What constraint it enforces

**Derived implementations are structurally correct by construction and fail at compile time if any field does not satisfy the derived trait's requirements.**

- If you `#[derive(Clone)]` on a struct containing a field that is not `Clone`, the compiler emits a clear error naming the offending field.
- Derived `PartialEq` compares every field; derived `Hash` hashes every field -- you cannot accidentally skip a field.
- Derived `Ord` uses field declaration order, which may not match your domain's intended ordering; in that case you must implement the trait manually.

## Minimal snippet

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct Point {
    x: i32,
    y: i32,
}

fn main() {
    let a = Point { x: 1, y: 2 };
    let b = a.clone();
    println!("{a:?}");            // Debug
    assert_eq!(a, b);             // PartialEq + Eq
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Traits** [-> catalog/T05](T05-type-classes.md) | Derive is syntactic sugar for `impl Trait for Type`. The generated code follows the same rules as hand-written impls. |
| **Algebraic data types** [-> catalog/T01](T01-algebraic-data-types.md) | Derive works on both structs and enums. For enums, each variant must satisfy the trait independently. |
| **Newtypes** [-> catalog/T03](T03-newtypes-opaque.md) | Newtypes frequently derive `Debug`, `Clone`, `PartialEq` to inherit behavior from the inner type with minimal boilerplate. |
| **Macros / metaprogramming** [-> catalog/T17](T17-macros-metaprogramming.md) | Custom derive macros are a form of proc macro. They receive the token stream of the annotated item and emit new `impl` blocks. |
| **Equality safety** [-> catalog/T20](T20-equality-safety.md) | `#[derive(PartialEq, Eq)]` opts the type into equality comparison. Without it, `==` is not available. |

## Gotchas and limitations

1. **All fields must implement the trait.** `#[derive(Clone)]` on a struct with a non-`Clone` field will fail. The error message names the problematic field.

2. **Derived `PartialOrd`/`Ord` use field declaration order.** The first field is compared first, then the second, and so on. If your struct has `name` before `priority`, derived ordering sorts by name, not priority. Reorder fields or implement the trait manually.

3. **Derived `Default` requires all fields to be `Default`.** `Option<T>` is `Default` (defaults to `None`), but many types are not. You may need a full `impl Default` block instead.

4. **`Copy` implies `Clone` but not vice versa.** `#[derive(Copy)]` requires `Clone` to also be derived or implemented. Additionally, `Copy` is only valid if all fields are `Copy` -- no heap-allocated types like `String` or `Vec`.

5. **Custom derives can generate surprising code.** A derive macro from an external crate may add methods, trait impls, or even new types. Always read the documentation of third-party derive macros before applying them.

6. **No partial derives.** You cannot derive a trait for a subset of fields. If one field should be excluded (e.g., from `PartialEq`), you must implement the trait manually.

## Beginner mental model

Think of `#[derive(...)]` as a **copy machine for boilerplate**. You hand the compiler a checklist of traits, and for each one it inspects your type's fields, confirms the parts are compatible, and prints out a correct implementation. If any field is missing the prerequisite (like a `Clone` impl), the machine jams and tells you exactly which part is the problem.

## Example A -- Deriving common traits on a struct

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash, Default)]
struct Config {
    host: String,
    port: u16,
    retries: u32,
}

fn main() {
    let default = Config::default();
    println!("{default:?}");
    // Config { host: "", port: 0, retries: 0 }

    let custom = Config { host: "db.local".into(), port: 5432, retries: 3 };
    assert_ne!(default, custom);
}
```

## Example B -- Custom derive from the ecosystem (serde)

```rust
use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize)]
struct Event {
    name: String,
    timestamp: u64,
    #[serde(default)]
    tags: Vec<String>,
}

fn main() {
    let json = r#"{"name":"deploy","timestamp":1700000000}"#;
    let event: Event = serde_json::from_str(json).unwrap();
    println!("{event:?}");
    // Event { name: "deploy", timestamp: 1700000000, tags: [] }
}
```

The `Serialize` and `Deserialize` derives are proc macros from the `serde` crate. They generate field-by-field serialization code at compile time with zero runtime reflection.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Derived `PartialEq` and `Debug` help test that only valid states are constructible.
- [-> UC-23](../usecases/UC23-diagnostics.md) -- Missing derive bounds produce some of the most common compiler errors; understanding derive helps read diagnostics.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Generic containers often require `T: Clone + Debug`; derive is the standard way to satisfy those bounds.

## Source anchors

- `book/src/appendix-03-derivable-traits.md`
- `rust-reference/src/attributes/derive.md`
- `rust-reference/src/procedural-macros.md` -- proc_macro_derive
- `rust-by-example/src/trait/derive.md`
