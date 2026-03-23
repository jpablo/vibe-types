# Record Types: Named-Field Structs

Since: Rust 1.0

## What it is

Named-field structs are Rust's record types. A struct like `struct User { name: String, age: u32 }` groups named fields into a single value, each with its own type. This is Rust's equivalent of records in ML, data classes in Kotlin, or `@dataclass` in Python -- but with compile-time guarantees about initialization, ownership, and access.

**Struct update syntax** (`..other`) copies/moves remaining fields from another instance of the same type, making it easy to create modified copies. **Destructuring** in patterns binds fields to local variables: `let User { name, age } = user;`. **Tuple structs** (`struct Point(f64, f64)`) are a positional variant where fields are accessed by index rather than name.

All fields must be initialized at construction -- there are no uninitialized or default-assigned fields unless the type implements `Default` and you explicitly use `..Default::default()`.

## What constraint it enforces

**Every field must be provided at construction, and the compiler tracks ownership and borrowing of each field independently.**

- Missing a field in a struct literal is a compile error (`error[E0063]`).
- Moving a non-`Copy` field out of a struct invalidates that field; the remaining fields may still be usable (partial moves).
- Private fields prevent external construction, forcing use of constructors [-> catalog/T21](T21-encapsulation.md).

## Minimal snippet

```rust
struct User {
    name: String,
    age: u32,
    active: bool,
}

fn main() {
    let alice = User { name: "Alice".into(), age: 30, active: true };

    // Struct update syntax -- copies `active`, moves `name`
    let bob = User { name: "Bob".into(), age: 25, ..alice };

    // Destructuring
    let User { name, age, .. } = &bob;
    println!("{name}, age {age}");
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Algebraic data types** [-> catalog/T01](T01-algebraic-data-types.md) | Structs are product types; enums are sum types. Enum variants can contain named-field structs. |
| **Derive macros** [-> catalog/T06](T06-derivation.md) | `#[derive(Debug, Clone, PartialEq, Default)]` on a struct auto-generates trait impls from the field layout. |
| **Encapsulation** [-> catalog/T21](T21-encapsulation.md) | Fields default to private. A `pub struct` with private fields cannot be constructed outside its module. |
| **Pattern matching** [-> catalog/T14](T14-type-narrowing.md) | Structs can be destructured in `match`, `if let`, and `let` bindings. `..` ignores remaining fields. |
| **Immutability** [-> catalog/T32](T32-immutability-markers.md) | Struct bindings are immutable by default. `let mut user = ...` is required to modify fields. Mutability applies to the entire binding, not individual fields. |

## Gotchas and limitations

1. **Struct update syntax moves non-`Copy` fields.** `let b = User { age: 25, ..a }` moves `a.name` (a `String`) into `b`. After this, `a.name` is invalid but `a.age` (a `u32`, which is `Copy`) remains usable.

2. **No default values for individual fields.** Unlike Kotlin or Python, you cannot write `struct Config { retries: u32 = 3 }`. Use `Default` or a builder pattern instead.

3. **Field order matters for derived `PartialOrd`/`Ord`.** Derived ordering compares fields in declaration order. If `name` comes before `priority`, sorting is alphabetical by name, not by priority.

4. **Tuple structs lose field names.** `struct Point(f64, f64)` accesses fields as `.0` and `.1`. This is concise for small types but becomes unreadable for more than 2-3 fields.

5. **No structural typing.** Two structs with identical field names and types are distinct types. `struct A { x: i32 }` and `struct B { x: i32 }` are not interchangeable [-> catalog/T07](T07-structural-typing.md).

## Beginner mental model

Think of a named-field struct as a **form** where every blank has a label and a type. You must fill in every blank to create the form (no omissions allowed). The compiler is the clerk: it checks that every blank is filled, that you wrote the right kind of data in each blank, and that you have permission to read or modify each field based on the module's visibility rules.

## Example A -- Struct update syntax and Default

```rust
#[derive(Debug, Default)]
struct Config {
    host: String,
    port: u16,
    retries: u32,
    verbose: bool,
}

fn main() {
    let prod = Config {
        host: "db.prod.local".into(),
        port: 5432,
        ..Default::default()       // retries=0, verbose=false
    };
    println!("{prod:?}");
}
```

## Example B -- Destructuring in function parameters

```rust
struct Rect {
    width: f64,
    height: f64,
}

fn area(Rect { width, height }: &Rect) -> f64 {
    width * height
}

fn main() {
    let r = Rect { width: 10.0, height: 5.0 };
    println!("area = {}", area(&r));  // 50
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Mandatory field initialization and private fields ensure only valid instances are constructible.
- [-> UC-20](../usecases/UC20-ownership-apis.md) -- Structs with owned fields model resource ownership; partial moves let fields transfer independently.
- [-> UC-22](../usecases/UC22-conversions.md) -- `From` impls between struct types provide safe, explicit conversion paths.

## Source anchors

- `book/src/ch05-01-defining-structs.md`
- `book/src/ch05-02-example-structs.md`
- `rust-reference/src/items/structs.md`
- `rust-by-example/src/custom_types/structs.md`
