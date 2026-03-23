# Structural Typing (Not a First-Class Feature)

Since: N/A (Rust uses nominal typing)

## What it is

Rust does not have structural typing natively. It is a **nominally typed** language: two types are compatible only if they share the same name (or one is explicitly convertible to the other). Two structs with identical field names, field types, and layout are still distinct, incompatible types. There is no duck typing, no implicit interface satisfaction, and no "if it has the right shape, it fits."

However, Rust achieves the same constraints that structural typing provides through **trait bounds** and **generics**. Instead of "any type with a `.len()` method," Rust says `T: HasLen` where `HasLen` is a trait declaring `fn len(&self) -> usize`. The contract is explicit, named, and checked at compile time. This is more verbose but avoids the accidental compatibility that structural typing can introduce (two types with a `.close()` method that mean entirely different things).

**Trait objects** (`dyn Trait`) provide dynamic dispatch over types satisfying a trait, which is the closest Rust gets to structural polymorphism -- but the type must still explicitly implement the trait.

## What constraint it enforces

**Types are compatible only when they share the same name or implement the same named trait. Shape alone is not sufficient.**

- `struct A { x: i32 }` and `struct B { x: i32 }` are incompatible even though they have identical structure.
- A type must have an explicit `impl Trait for Type` block to satisfy a trait bound. Having the right methods by coincidence is not enough.
- This prevents accidental compatibility and makes type relationships explicit in the code.

## Minimal snippet

```rust
struct Meters(f64);
struct Seconds(f64);

// Identical structure, but:
// let m: Meters = Seconds(1.0);  // error[E0308]: mismatched types

trait Measurable {
    fn value(&self) -> f64;
}

impl Measurable for Meters  { fn value(&self) -> f64 { self.0 } }
impl Measurable for Seconds { fn value(&self) -> f64 { self.0 } }

fn print_measurement(m: &dyn Measurable) {
    println!("{}", m.value());
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Traits** [-> catalog/T05](T05-type-classes.md) | Traits are Rust's replacement for structural contracts. They define explicit behavior requirements that types opt into. |
| **Generics** [-> catalog/T04](T04-generics-bounds.md) | `fn process<T: Read + Write>(io: T)` constrains by capability, not structure. The bound is checked at compile time. |
| **Newtypes** [-> catalog/T03](T03-newtypes-opaque.md) | Newtypes rely on nominal typing to distinguish types that have the same underlying structure. |
| **Coherence / orphan rules** [-> catalog/T25](T25-coherence-orphan.md) | Nominal typing plus coherence ensures each trait-type pair has exactly one implementation globally. |
| **Record types** [-> catalog/T31](T31-record-types.md) | Two structs with the same fields are still distinct. Rust records are nominal, not structural. |

## Gotchas and limitations

1. **No implicit interface satisfaction.** Even if `MyType` has a method `fn len(&self) -> usize`, it does not satisfy `ExactSizeIterator` unless you write `impl ExactSizeIterator for MyType`. This is by design but can feel verbose.

2. **No row polymorphism.** Rust has no way to say "any struct with at least fields `x: i32` and `y: i32`." Generic code must use trait bounds, not field-level constraints.

3. **Macro workarounds exist.** Macros can generate trait impls for multiple structurally similar types, reducing the verbosity of nominal typing, but the underlying system remains nominal.

4. **Tuples and arrays are structurally typed within their category.** `(i32, String)` is the same type everywhere -- but this is not "structural typing" in the general sense; it is just that tuples are anonymous product types with a fixed naming convention.

5. **Serde and other frameworks simulate structural behavior.** `#[derive(Serialize, Deserialize)]` makes types interoperable based on their field structure for serialization, but the Rust type system itself still treats them as distinct.

## Beginner mental model

Think of Rust's type system as a **government ID office**. Two people can have the same height, weight, and eye color, but they still need their own unique ID (type name) to be recognized. A trait is like a professional certification: even if you know how to do the work, you must get the certificate (write the `impl`) before the system recognizes your qualifications.

## Example A -- Explicit trait impl required despite matching method

```rust
trait Describable {
    fn describe(&self) -> String;
}

struct Cat { name: String }
struct Car { name: String }

// Cat has a `describe` conceptually, but must explicitly impl the trait:
impl Describable for Cat {
    fn describe(&self) -> String {
        format!("cat named {}", self.name)
    }
}

// Car also has the same shape but is NOT Describable without impl
// impl Describable for Car { ... }  // uncomment to make it work

fn show(item: &dyn Describable) {
    println!("{}", item.describe());
}

fn main() {
    let cat = Cat { name: "Whiskers".into() };
    show(&cat);
    // let car = Car { name: "Tesla".into() };
    // show(&car);  // error: Car does not implement Describable
}
```

## Example B -- Generic bounds as the structural-typing substitute

```rust
use std::io::{Read, Write, Cursor};

fn echo<T: Read + Write>(io: &mut T, buf: &mut [u8]) -> std::io::Result<()> {
    let n = io.read(buf)?;
    io.write_all(&buf[..n])?;
    Ok(())
}

fn main() {
    let mut cursor = Cursor::new(vec![1, 2, 3, 4]);
    let mut buf = [0u8; 4];
    echo(&mut cursor, &mut buf).unwrap();
    println!("{:?}", &buf[..]);  // [1, 2, 3, 4]
}
```

The function does not care *what* `T` is -- only that it provides `Read` and `Write` capabilities. This is Rust's answer to structural typing.

## Use-case cross-references

- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Trait bounds replace structural constraints with explicit, named contracts.
- [-> UC-14](../usecases/UC14-extensibility.md) -- New types can implement existing traits, extending the system without structural compatibility risks.
- [-> UC-01](../usecases/UC01-invalid-states.md) -- Nominal typing prevents accidental type compatibility that could allow invalid state mixing.

## Source anchors

- `book/src/ch10-02-traits.md` -- "Traits: Defining Shared Behavior"
- `rust-reference/src/type-system.md`
- `rust-reference/src/items/implementations.md`
