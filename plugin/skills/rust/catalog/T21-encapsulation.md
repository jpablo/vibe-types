# Encapsulation and Visibility

Since: Rust 1.0; `pub(crate)` and `pub(super)` since Rust 1.18

## What it is

Rust enforces encapsulation through a **visibility system** where items are **private by default**. Functions, structs, enums, constants, modules, and struct fields are all invisible outside their defining module unless explicitly marked with a visibility modifier:

- `pub` -- visible to everyone.
- `pub(crate)` -- visible within the current crate only.
- `pub(super)` -- visible to the parent module.
- `pub(in path)` -- visible within a specified ancestor module.
- *(no modifier)* -- private to the current module and its descendants.

Struct fields follow the same rules independently of the struct's own visibility. A `pub struct` with private fields **cannot be constructed** outside its module using literal syntax, forcing callers through constructor functions that can enforce invariants.

## What constraint it enforces

**Code outside a module boundary cannot access, construct, or destructure items that are not explicitly exposed.**

- Private struct fields prevent external construction and destructuring, funneling all creation through validated constructors.
- Private functions and types are implementation details invisible to dependents, enabling internal refactoring without breaking changes.
- `pub(crate)` enables sharing within a crate without exposing to downstream users, supporting internal modularity.

## Minimal snippet

```rust
mod auth {
    pub struct Token {
        raw: String,  // private -- cannot be accessed outside `auth`
    }

    impl Token {
        pub fn new(raw: &str) -> Self {
            assert!(!raw.is_empty(), "token must not be empty");
            Token { raw: raw.to_owned() }
        }

        pub fn as_str(&self) -> &str { &self.raw }
    }
}

fn main() {
    let t = auth::Token::new("abc123");
    println!("{}", t.as_str());
    // println!("{}", t.raw);   // error[E0616]: field `raw` is private
    // let auth::Token { raw } = t;  // error: field `raw` is private
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Newtypes** [-> catalog/T03](T03-newtypes-opaque.md) | Private inner fields make newtypes truly opaque. Without privacy, a tuple struct is just a transparent wrapper. |
| **Algebraic data types** [-> catalog/T01](T01-algebraic-data-types.md) | Enum variants inherit the enum's visibility, but struct fields within variants follow their own visibility rules. |
| **Traits** [-> catalog/T05](T05-type-classes.md) | Trait methods are always public when the trait is public. Visibility cannot be applied to individual trait methods. |
| **Record types** [-> catalog/T31](T31-record-types.md) | Structs used as records often have all-public fields; those enforcing invariants keep fields private. The module boundary is the decision point. |

## Gotchas and limitations

1. **Enum variant fields are public when the enum is public.** Unlike struct fields, fields inside an enum variant are visible wherever the enum is visible. You cannot make individual variant fields private.

2. **`pub` on a struct does not make fields public.** `pub struct Foo { bar: u32 }` has a public struct with a private field. External code can name `Foo` but cannot construct it. This is by design but surprises beginners.

3. **Private items are visible to child modules.** A private function in module `a` is accessible from `a::b`. Privacy flows *downward*, not *sideways*.

4. **`#[non_exhaustive]` adds another layer.** A `#[non_exhaustive]` public struct with all-public fields still cannot be constructed with literal syntax outside the defining crate.

5. **Re-exports can widen visibility.** `pub use internal::helper;` at the crate root makes a previously crate-private item fully public. Audit `pub use` statements when reviewing API surface.

## Beginner mental model

Think of a Rust module as a **building with locked doors**. Everything inside is private unless you install a door (`pub`) for visitors. `pub(crate)` is an employee entrance -- people within the organization can enter, but outsiders cannot. Struct fields are rooms inside the building: even if the building has a public lobby (`pub struct`), the back offices (private fields) require a key (constructor function) to access.

## Example A -- pub(crate) for internal sharing

```rust
mod db {
    pub(crate) struct Pool {
        pub(crate) connections: Vec<String>,
    }

    impl Pool {
        pub(crate) fn new() -> Self {
            Pool { connections: vec!["conn1".into()] }
        }
    }
}

// Accessible within the crate but not by downstream dependents
fn setup() {
    let pool = db::Pool::new();
    println!("{} connections", pool.connections.len());
}

fn main() { setup(); }
```

## Example B -- Enforcing invariants through private fields

```rust
mod temperature {
    #[derive(Debug)]
    pub struct Celsius(f64);

    impl Celsius {
        pub fn new(val: f64) -> Result<Self, &'static str> {
            if val < -273.15 {
                Err("temperature below absolute zero")
            } else {
                Ok(Celsius(val))
            }
        }

        pub fn value(&self) -> f64 { self.0 }
    }
}

fn main() {
    let t = temperature::Celsius::new(100.0).unwrap();
    println!("{:?} = {}C", t, t.value());

    // Celsius(-500.0) would bypass validation, but:
    // temperature::Celsius(-500.0);  // error: field `0` is private
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Private fields force construction through validated paths, making invalid states unrepresentable.
- [-> UC-20](../usecases/UC20-ownership-apis.md) -- Visibility controls which parts of an API are exposed, shaping how consumers interact with owned data.
- [-> UC-14](../usecases/UC14-extensibility.md) -- `pub(crate)` enables internal extensibility while maintaining a stable public API surface.

## Source anchors

- `book/src/ch07-03-paths-for-referring-to-an-item-in-the-module-tree.md`
- `rust-reference/src/visibility-and-privacy.md`
- `rust-by-example/src/mod/visibility.md`
