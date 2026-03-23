# Union & Intersection Types (via Enums and Trait Bounds)

Since: Rust 1.0

## What it is

Rust does not have union types (`A | B`) or intersection types (`A & B`) as first-class syntax. Instead, it achieves the same constraints through two separate mechanisms:

**Sum types (union equivalent):** Enums model "a value is one of several types." Where TypeScript writes `string | number`, Rust declares `enum StringOrNumber { Str(String), Num(i64) }`. Every consumer must `match` to determine the variant, and the compiler enforces exhaustiveness. The `either` crate provides a generic `Either<L, R>` for ad-hoc two-type unions without declaring a custom enum.

**Trait bound combinations (intersection equivalent):** Where TypeScript writes `A & B`, Rust uses `T: Clone + Debug + Send`. A value satisfying this bound *simultaneously* implements all listed traits. Supertraits (`trait Printable: Display + Debug`) achieve the same composition at the trait definition level.

These are not syntactic sugar for the same concept as in TypeScript or Scala -- they are distinct type-system features that cover the same design space.

## What constraint it enforces

**Sum types force exhaustive handling of every variant. Trait bound intersections require that a type satisfies every listed trait simultaneously.**

- You cannot access the inner value of an enum variant without matching on it first.
- A function with `T: Read + Write` rejects types that implement only one of the two traits.
- There is no implicit "upcast" from a variant to the enum or from a concrete type to a trait bound -- conversions are explicit.

## Minimal snippet

```rust
// Sum type (union equivalent)
enum Value {
    Int(i64),
    Text(String),
    Flag(bool),
}

fn describe(v: &Value) -> String {
    match v {
        Value::Int(n)  => format!("integer: {n}"),
        Value::Text(s) => format!("text: {s}"),
        Value::Flag(b) => format!("flag: {b}"),
    }
}

// Intersection equivalent via trait bounds
fn log_and_clone<T: std::fmt::Debug + Clone>(val: &T) -> T {
    println!("{val:?}");
    val.clone()
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Algebraic data types** [-> catalog/T01](T01-algebraic-data-types.md) | Enums are Rust's sum types. Each variant can carry different data. Pattern matching deconstructs them. |
| **Traits** [-> catalog/T05](T05-type-classes.md) | `T: A + B` is the intersection mechanism. Traits can also have supertraits: `trait C: A + B`. |
| **Generics** [-> catalog/T04](T04-generics-bounds.md) | Trait bounds on generics serve as compile-time intersection constraints. |
| **Pattern matching** [-> catalog/T14](T14-type-narrowing.md) | `match` on enums narrows the type, extracting variant-specific data. |
| **Trait objects** [-> catalog/T36](T36-trait-objects.md) | `dyn Read + Write` is a dynamic intersection -- though only one non-auto trait is allowed without `dyn Trait<..> + AutoTrait` syntax. |

## Gotchas and limitations

1. **Enum variants are not standalone types.** `Value::Int` is a constructor, not a type. You cannot write `fn process(v: Value::Int)`. If you need a variant as its own type, extract it into a struct and reference it from the variant.

2. **No anonymous unions.** Rust has no `A | B` syntax. Every union must be declared as a named enum. The `either` crate's `Either<A, B>` provides a generic two-variant enum but loses domain semantics.

3. **`dyn` trait objects limit intersection.** `dyn TraitA + TraitB` is only allowed when at most one is a non-auto trait. For multiple non-auto traits, use a supertrait: `trait Combined: TraitA + TraitB {}`.

4. **No structural unions.** TypeScript's `{ a: number } | { b: string }` has no Rust equivalent. You must declare an enum with named variants, even for one-off combinations.

5. **Adding an enum variant is a breaking change.** Unlike TypeScript union extension, adding a variant to a public enum breaks downstream `match` statements unless the enum is `#[non_exhaustive]`.

6. **Trait bound intersections are nominal.** `T: Debug + Clone` requires *both* trait impls. There is no way to say "implements at least one of these" (union of traits) in Rust's type system.

## Beginner mental model

Think of an **enum** as a labeled box that can contain exactly one of several item types -- you must open the box and check the label before accessing the contents. Think of **trait bounds** (`T: A + B`) as a checklist: the type must have every item checked off before it is accepted. Together, enums give you "one of these types" and trait bounds give you "all of these capabilities."

## Example A -- Either crate for ad-hoc unions

```rust
// Using the `either` crate
use either::Either;

fn parse_input(s: &str) -> Either<i64, String> {
    match s.parse::<i64>() {
        Ok(n)  => Either::Left(n),
        Err(_) => Either::Right(s.to_owned()),
    }
}

fn main() {
    match parse_input("42") {
        Either::Left(n)  => println!("number: {n}"),
        Either::Right(s) => println!("string: {s}"),
    }
}
```

## Example B -- Supertrait as intersection

```rust
use std::fmt;

trait Loggable: fmt::Display + fmt::Debug {
    fn log(&self) {
        println!("[LOG] {self} ({self:?})");
    }
}

// Blanket impl: any type implementing both Display and Debug is Loggable
impl<T: fmt::Display + fmt::Debug> Loggable for T {}

fn main() {
    42_i32.log();            // [LOG] 42 (42)
    "hello".log();           // [LOG] hello ("hello")
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Enums restrict values to declared variants, preventing invalid combinations.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Trait bound intersections constrain generic parameters to types with multiple capabilities.
- [-> UC-14](../usecases/UC14-extensibility.md) -- Enums with `#[non_exhaustive]` allow future variant additions; supertraits allow composing trait contracts.

## Source anchors

- `book/src/ch06-01-defining-an-enum.md`
- `book/src/ch10-02-traits.md` -- trait bounds
- `rust-reference/src/items/enumerations.md`
- `rust-reference/src/trait-bounds.md`
- `either` crate documentation
