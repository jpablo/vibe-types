# Structs, Enums, and Newtypes

## What it is

Rust data types encode domain state directly through fields and variants.

## What constraint it enforces

**Only explicitly modeled states are constructible, and pattern matching forces callers to handle declared variants.**

## Minimal snippet

```rust
enum Payment {
    Cash,
    Card { last4: u16 },
}
```

## Interaction with other features

- Often combined with trait impls from `[-> catalog/06]`.
- Supports invalid-state prevention in `[-> UC-01]`.

## Gotchas and limitations

- Struct update syntax can move non-`Copy` fields and invalidate the source instance.
- Field/variant shape alone is not enough for range/business invariants; smart constructors are often required.

### Beginner mental model

Structs and enums are blueprints for concrete states; every instance must specify which doors (fields) are open and which variant it belongs to.

### Example A (code)

```rust
struct Point {
    x: i32,
    y: i32,
}

let origin = Point { x: 0, y: 0 };
```

### Example B (code)

```rust
enum Outcome {
    Success(u8),
    Failure(String),
}

fn describe(result: Outcome) {
    match result {
        Outcome::Success(code) => println!("code {code}"),
        Outcome::Failure(reason) => println!("error: {reason}"),
    }
}

describe(Outcome::Success(42));
```

### Common compiler errors and how to read them

- `error[E0063]: missing fields` names the fields you left out; include them or use `..Default::default()` when the type implements `Default`.
- `error[E0027]: pattern does not mention all fields` happens when a struct pattern omits fields that must be handled; add the missing bindings or use `..` to ignore the rest.

## Use-case cross-references

- `[-> UC-01]`

## Source anchors

- `book/src/ch05-01-defining-structs.md`
- `book/src/ch06-01-defining-an-enum.md`
- `book/src/ch09-03-to-panic-or-not-to-panic.md`
- `rust-by-example/src/custom_types/structs.md`
- `rust-by-example/src/custom_types/enum.md`
