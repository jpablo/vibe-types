# Literal Types (Not a First-Class Feature)

> **Since:** N/A — Rust does not have literal types. This entry documents idiomatic alternatives.

## What it is

Rust does **not** have literal types — there is no way to write a type like `42` or `"hello"` that is inhabited by exactly one value. Unlike Scala 3's singleton types, TypeScript's literal types, or Python's `Literal["GET"]`, Rust's type system does not promote values into types.

However, the problems that literal types solve in other languages are addressed in Rust through three complementary mechanisms:

- **Const generics** (`const N: usize`) — parameterize types and functions by compile-time constant values, providing type-level integers without literal types.
- **Enums** — define closed sets of named values, replacing `Literal["red", "green", "blue"]` patterns from other languages.
- **The `typenum` crate** — encodes numbers as types for type-level arithmetic when const generics are insufficient.

## What constraint it enforces

**There is no literal-type constraint in Rust.** Instead:

- **Const generics** enforce that a value is known at compile time and that distinct values produce distinct types: `[u8; 3]` and `[u8; 4]` are different types.
- **Enums** enforce that a value is one of a closed set of variants. Pattern matching must be exhaustive.
- **`typenum`** provides type-level numbers with compile-time arithmetic checks.

## Minimal snippet

```rust
// Rust does NOT allow this (hypothetical, invalid syntax):
// fn process(method: "GET" | "POST") { ... }

// Instead, use an enum for closed value sets:
enum HttpMethod {
    Get,
    Post,
    Put,
    Delete,
}

fn process(method: HttpMethod) {
    match method {
        HttpMethod::Get    => println!("Reading"),
        HttpMethod::Post   => println!("Creating"),
        HttpMethod::Put    => println!("Updating"),
        HttpMethod::Delete => println!("Deleting"),
        // exhaustive — no wildcard needed
    }
}

// Use const generics for type-level values:
struct Vector<const N: usize> {
    data: [f64; N],
}

fn concat<const A: usize, const B: usize>(
    a: Vector<A>,
    b: Vector<B>,
) -> Vector<{ A + B }> {
    todo!()
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Const generics** [-> catalog/T15](T15-const-generics.md) | The closest Rust analogue to literal types for numeric values. `const N: usize` in a type parameter position makes `N` part of the type. |
| **Algebraic data types** [-> catalog/T01](T01-algebraic-data-types.md) | Enums are Rust's answer to "closed set of values." Where other languages use `Literal["a", "b"]`, Rust uses `enum { A, B }` with exhaustive matching. |
| **Pattern matching** | `match` on enums is exhaustive by default. Adding a variant without updating all match arms is a compile error — the same guarantee Literal + exhaustiveness gives in other languages. |
| **`typenum` crate** | For type-level arithmetic beyond what const generics support (e.g., type-level comparisons, type-level booleans), `typenum` encodes numbers as nested types. |

## Gotchas and limitations

1. **No string literal types.** You cannot restrict a `&str` parameter to specific values at the type level. Use an enum or a newtype with a private constructor and factory functions.

2. **Const generics are limited to primitives.** As of Rust 1.79, const generic parameters support `usize`, `i32`, `bool`, `char`, and other primitives. You cannot use `String`, `&str`, or custom types as const generic parameters (the `adt_const_params` feature is unstable).

3. **No const generic arithmetic in stable (limited).** Expressions like `{ A + B }` in const generic positions require the `generic_const_exprs` nightly feature for complex cases. Simple array-size arithmetic works on stable, but conditional logic does not.

4. **Enums are nominal, not structural.** Two enums with identical variants are different types. This is stricter than Literal types in TypeScript or Python, which are structural.

5. **`typenum` has steep ergonomics.** While powerful, `typenum`'s encoding (`U3` = `UInt<UInt<UTerm, B1>, B1>`) produces verbose error messages and requires familiarity with its type-level encoding.

6. **No value-to-type promotion.** Unlike dependently-typed languages, Rust cannot take a runtime value and use it as a type parameter. The value must be a `const` expression.

## Beginner mental model

Think of Rust as a language that says: **"If you want a restricted set of values, give each value a name."** Other languages let you say "this string must be `GET` or `POST`" directly in the type. Rust says "define an enum `Method { Get, Post }` and use that." For numeric constants in types, Rust uses const generics: `Array<5>` instead of a literal type `5`.

The trade-off: Rust's approach requires more upfront definitions (you must declare the enum), but gives you exhaustive matching, methods on variants, and zero-cost abstractions. Literal types in other languages are more concise but less structured.

## Example A — Enum replacing Literal string types

```rust
// Python equivalent: Literal["red", "green", "blue"]
#[derive(Debug, Clone, Copy)]
enum Color { Red, Green, Blue }

fn hex(c: Color) -> &'static str {
    match c {
        Color::Red   => "#FF0000",
        Color::Green => "#00FF00",
        Color::Blue  => "#0000FF",
        // exhaustive — adding a variant forces updating this match
    }
}

// hex("red");       // error: expected `Color`, found `&str`
hex(Color::Red);     // OK
```

## Example B — Const generics for type-level values

```rust
// Capacity is part of the type — distinct values = distinct types
struct BoundedStack<T, const CAP: usize> {
    data: Vec<T>,
}

impl<T, const CAP: usize> BoundedStack<T, CAP> {
    fn new() -> Self { BoundedStack { data: Vec::with_capacity(CAP) } }

    fn push(&mut self, value: T) -> Result<(), T> {
        if self.data.len() < CAP { self.data.push(value); Ok(()) }
        else { Err(value) }
    }
}

let mut s8: BoundedStack<i32, 8> = BoundedStack::new();
let mut s4: BoundedStack<i32, 4> = BoundedStack::new();
// s8 = s4;  // error: BoundedStack<i32, 8> ≠ BoundedStack<i32, 4>
```

## Example C — typenum for type-level arithmetic

```rust
use typenum::{U3, U4, Unsigned, Sum, op};

// Type-level addition: U3 + U4 = U7
type U7 = Sum<U3, U4>;
assert_eq!(<U7 as Unsigned>::to_usize(), 7);

// Type-level comparison (compile-time)
type IsLess = op!(U3 < U4);  // True
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Enums make invalid states unrepresentable.
- [-> UC-04](../usecases/UC04-generic-constraints.md) — Const generics constrain type parameters to specific values.
- [-> UC-18](../usecases/UC18-type-arithmetic.md) — Type-level arithmetic with const generics and typenum.

## Source anchors

- [Rust Reference — Const Generics](https://doc.rust-lang.org/reference/items/generics.html#const-generics)
- [Rust RFC 2000 — Const Generics](https://rust-lang.github.io/rfcs/2000-const-generics.html)
- [typenum crate](https://docs.rs/typenum/latest/typenum/)
- [Rust Blog — Const Generics MVP](https://blog.rust-lang.org/2021/02/26/const-generics-mvp-beta.html)
