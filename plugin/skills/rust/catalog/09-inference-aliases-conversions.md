# Inference, Aliases, and Conversion Traits

## What it is

Rust's type inference is inspired by the Hindley-Milner family of algorithms, but it operates *locally* — the compiler infers types within a function body by examining how values are created and used, without ever looking at callers of that function. You rarely need to annotate local variables because the compiler propagates constraints forward and backward through assignments, method calls, and return positions. This gives Rust a concise feel similar to dynamically-typed languages while retaining full static type safety.

Type aliases (`type Name = ConcreteType`) let you introduce a shorter or more descriptive name for an existing type. Crucially, an alias is *not* a new distinct type — it is a transparent synonym. The compiler treats `Name` and `ConcreteType` as identical in every context: they unify during type-checking, they accept each other's values, and no conversion is required to move between them. This makes aliases useful for readability (e.g., `type Result<T> = std::result::Result<T, MyError>`) but useless for domain-level type safety.

Conversion traits provide the ecosystem's standard vocabulary for turning one type into another. `From<T>` and `Into<T>` handle infallible conversions; `TryFrom<T>` and `TryInto<T>` handle fallible ones that return `Result`. `AsRef<T>` and `AsMut<T>` offer cheap reference-to-reference conversions for writing flexible function signatures. Finally, the `as` keyword performs primitive numeric casts — but these are *not* trait-based and can silently truncate or wrap values. Rust's design philosophy is that conversions must be explicit; unlike C's implicit integer promotions or Scala's implicit conversions, Rust never silently converts between types. You choose the conversion, and the type system verifies it.

## What constraint it enforces

**Inferred and converted types must satisfy declared signatures and trait contracts; no implicit conversion ever occurs without a programmer-visible marker.**

More specifically:

- **Inference is local and complete.** The compiler resolves every type variable inside a function body. If it cannot, it emits `E0282` and asks for an annotation — it never guesses across function boundaries.
- **Aliases are transparent.** A type alias introduces zero semantic distinction. `type A = u32` and `u32` are the same type everywhere — in trait implementations, match arms, and generic bounds.
- **`From` must be infallible.** An `impl From<X> for Y` must always succeed. If the conversion can fail, you must use `TryFrom` and return a `Result`.
- **Implementing `From` gives you `Into` for free.** A blanket impl in the standard library provides `Into<Y> for X` whenever `From<X> for Y` exists. You should almost never implement `Into` directly.
- **`as` casts are unchecked.** Primitive numeric casts via `as` perform wrapping, truncation, or sign-extension with no runtime error — the programmer accepts full responsibility for correctness.

## Minimal snippet

```rust
let mut v = Vec::new();
v.push(5_u8);           // inference resolves `v` to `Vec<u8>`

let n: u16 = 300;
let b = n as u8;        // silent truncation: b == 44
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Structs and Enums (newtypes)** [-> catalog/04] | Newtypes like `struct Meters(u32)` provide the type safety that aliases lack. Implement `From` on the newtype for ergonomic conversions. |
| **Generics and Trait Bounds** [-> catalog/05] | Generic functions use bounds like `Into<String>` or `AsRef<Path>` to accept multiple input types while keeping the API explicit. |
| **Traits and Trait Objects** [-> catalog/06] | `From`, `Into`, `TryFrom`, `TryInto`, `AsRef`, and `AsMut` are all traits — their coherence and orphan rules constrain where you can implement them. |
| **Error Handling** [-> catalog/08] | The `?` operator calls `From::from()` on error values, enabling automatic error-type conversion when `From` is implemented between error types. |
| **Smart Pointers** [-> catalog/10] | `Box<T>`, `Rc<T>`, and `Arc<T>` implement `From<T>`, `AsRef<T>`, and `AsMut<T>`, making conversions between owned and referenced views seamless. |

## Gotchas and limitations

1. **Type aliases provide NO type safety.** `type Meters = u32` and `type Seconds = u32` are both `u32`. You can pass a `Seconds` value where `Meters` is expected without any compiler complaint. For domain separation, use newtypes [-> catalog/04] instead.

   ```rust
   type Meters  = u32;
   type Seconds = u32;
   fn speed(d: Meters, t: Seconds) -> f64 { d as f64 / t as f64 }
   let time: Seconds = 10;
   let dist: Meters  = 100;
   speed(time, dist); // compiles fine — arguments swapped, bug undetected
   ```

2. **`as` casts silently truncate and wrap.** `256u16 as u8` yields `0` with no warning. Prefer `u8::try_from(val)` when the source range may exceed the target, so you get a `Result` instead of silent data loss.

3. **Inference is local — the turbofish or type annotations may be required.** When the compiler cannot determine a type from usage alone — e.g., parsing a string — you must annotate. The two common forms are the turbofish (`::<Type>`) and a `let` binding annotation.

   ```rust
   // error[E0282] without annotation — parse into what?
   let n = "42".parse::<i32>().unwrap(); // turbofish
   let m: i32 = "42".parse().unwrap();   // let annotation
   ```

4. **Implement `From`, not `Into`.** Because a blanket impl provides `Into<Y> for X` whenever `From<X> for Y` exists, implementing `Into` directly is redundant and prevents the reverse `From` from existing. Always implement `From`.

5. **`From` impls must be infallible.** If your conversion can fail (e.g., a value out of range), use `TryFrom`. Returning a panic from `From::from` technically compiles but violates the trait's contract and surprises callers.

6. **`AsRef` vs `Borrow` — subtle semantic difference.** Both provide `&T` access, but `Borrow<T>` carries an additional contract: the borrowed form must have the same `Eq`, `Ord`, and `Hash` behavior as the owned form. `AsRef` makes no such guarantee and is purely a conversion convenience.

7. **Orphan rules apply to conversion traits.** You cannot implement `From<TheirType> for TheirType` if neither type is defined in your crate. This is the same coherence rule as for any other trait [-> catalog/06], but it is frequently encountered when trying to convert between types from two external crates.

8. **Blanket impls can cause confusing errors.** The standard library's blanket `impl<T> From<T> for T` (the identity conversion) and `impl<T, U> Into<U> for T where U: From<T>` interact with your own impls. Conflicting blanket impls can produce opaque "upstream crates may add a new impl" errors.

## Beginner mental model

Think of type inference as a detective that reads your code for clues. When you write `let v = Vec::new()` and later call `v.push(42u8)`, the detective works backward: "the push takes a `u8`, so the Vec must be `Vec<u8>`." The detective is thorough inside a function but never peeks outside it — function signatures are the contracts, and the detective trusts them as-is.

For conversions, think of `From`/`Into` as *safe bridges* between types: the bridge exists only when someone builds it (writes the impl), and once built, traffic can flow in the declared direction without risk. `TryFrom`/`TryInto` are bridges with a tollbooth — they might reject your crossing and hand back an error. `as` casts, by contrast, are *jumping off the bridge* — you land somewhere, but nobody checks whether you landed safely.

## Example A — Type inference in action

```rust
fn main() {
    let mut v = Vec::new();    // type unknown so far: Vec<_>
    v.push(42u8);              // compiler infers Vec<u8>
    v.push(1);                 // 1 is inferred as u8 to match

    let sum: u16 = v.iter()
        .map(|&x| x as u16)
        .sum();                // sum() needs a return type — provided by `let sum: u16`
    println!("sum = {sum}");   // 43
}
```

## Example B — Type alias for readability

```rust
use std::collections::HashMap;

/// A transparent alias — `Registry` IS `HashMap<String, Vec<String>>`.
type Registry = HashMap<String, Vec<String>>;

fn find(reg: &Registry, key: &str) -> Option<&Vec<String>> {
    reg.get(key)
}

fn main() {
    let mut reg: Registry = HashMap::new();
    reg.entry("tools".into()).or_default().push("cargo".into());

    // Passing a raw HashMap where Registry is expected works — they are the same type.
    let plain: HashMap<String, Vec<String>> = HashMap::new();
    find(&plain, "tools"); // compiles without conversion
}
```

## Example C — `From`/`Into` implementation and usage

```rust
struct Celsius(f64);
struct Fahrenheit(f64);

impl From<Celsius> for Fahrenheit {
    fn from(c: Celsius) -> Self {
        Fahrenheit(c.0 * 9.0 / 5.0 + 32.0)
    }
}

fn print_temp(t: impl Into<Fahrenheit>) {
    let f: Fahrenheit = t.into();
    println!("{:.1} F", f.0);
}

fn main() {
    let boiling = Celsius(100.0);
    print_temp(boiling);               // From<Celsius> gives Into<Fahrenheit> for free
    print_temp(Fahrenheit(72.0));       // From<T> for T (identity) also works
}
```

## Example D — `TryFrom`/`TryInto` with error handling

```rust
use std::convert::TryFrom;

#[derive(Debug)]
struct Percentage(u8);

impl TryFrom<i32> for Percentage {
    type Error = String;

    fn try_from(value: i32) -> Result<Self, Self::Error> {
        if (0..=100).contains(&value) {
            Ok(Percentage(value as u8))
        } else {
            Err(format!("{value} is not a valid percentage (0-100)"))
        }
    }
}

fn main() {
    let valid = Percentage::try_from(85);
    println!("{valid:?}");   // Ok(Percentage(85))

    let invalid = Percentage::try_from(120);
    println!("{invalid:?}"); // Err("120 is not a valid percentage (0-100)")
}
```

## Example E — `AsRef` for flexible function arguments

```rust
use std::path::Path;

/// Accepts &str, String, PathBuf, or anything that cheaply yields &Path.
fn file_exists(p: impl AsRef<Path>) -> bool {
    p.as_ref().exists()
}

fn main() {
    println!("{}", file_exists("/tmp"));                           // &str
    println!("{}", file_exists(String::from("/tmp")));             // String
    println!("{}", file_exists(std::path::PathBuf::from("/tmp"))); // PathBuf
}
```

## Example F — `as` casts and their dangers

```rust
fn main() {
    // Truncation — high bits are silently discarded
    let big: u16 = 256;
    let small = big as u8;
    println!("{big} as u8 = {small}");  // 256 as u8 = 0

    // Sign extension — negative i8 becomes large u8
    let neg: i8 = -1;
    let unsigned = neg as u8;
    println!("{neg} as u8 = {unsigned}"); // -1 as u8 = 255

    // Safer alternative using TryFrom
    let val: u16 = 300;
    match u8::try_from(val) {
        Ok(n)  => println!("fits: {n}"),
        Err(e) => println!("overflow: {e}"), // overflow: out of range...
    }
}
```

## Common compiler errors and how to read them

### `error[E0282]: type annotations needed`

The compiler cannot infer a type from context alone. This commonly happens with turbofish-eligible methods like `parse()`, `collect()`, and `sum()`.

```
error[E0282]: type annotations needed
 --> src/main.rs:2:9
  |
2 |     let x = "42".parse().unwrap();
  |         ^ consider giving `x` a type
```

**How to fix:** Add a type annotation on the binding (`let x: i32 = ...`) or use the turbofish (`"42".parse::<i32>()`).

### `error[E0308]: mismatched types`

You provided one type where the compiler expected another, and no automatic conversion exists.

```
error[E0308]: mismatched types
 --> src/main.rs:5:18
  |
5 |     let x: u32 = 1.0_f64;
  |            ---   ^^^^^^^ expected `u32`, found `f64`
  |            |
  |            expected due to this
```

**How to fix:** Use an explicit conversion — `as` for primitives, `From::from()` / `.into()` for types with a `From` impl, or `TryFrom` if the conversion may fail.

### `error[E0277]: the trait bound 'Y: From<X>' is not satisfied`

You tried to call `.into()` or `From::from()` but no `From<X> for Y` impl exists.

```
error[E0277]: the trait bound `String: From<Vec<u8>>` is not satisfied
 --> src/main.rs:3:24
  |
3 |     let s: String = v.into();
  |                        ^^^^ the trait `From<Vec<u8>>` is not implemented for `String`
  |
  = help: the following implementations were found:
            <String as From<&str>>
```

**How to fix:** Implement `From<X> for Y` if you own one of the types, use a different conversion path (e.g., `String::from_utf8(v)` for `Vec<u8>`), or verify you have the right source/target pair.

### `error[E0604]: only `u8` can be cast as `char`

Not all primitive `as` casts are valid. The compiler restricts which type pairs `as` can bridge.

```
error[E0604]: only `u8` can be cast as `char`
 --> src/main.rs:3:13
  |
3 |     let c = 1024u32 as char;
  |             ^^^^^^^^^^^^^^^ invalid cast
```

**How to fix:** Use `char::from_u32(value)`, which returns `Option<char>` and validates the code point, or first convert to `u8` if you know the value is in ASCII range.

## Use-case cross-references

- [-> UC-01](../usecases/01-preventing-invalid-states.md) — Type aliases and newtypes model domain concepts; conversion traits define the bridges between them.
- [-> UC-06](../usecases/06-conversion-boundaries.md) — Generic APIs use `Into`, `AsRef`, and trait bounds to accept multiple input types while preserving type safety.

## Source anchors

- `rust-by-example/src/types/inference.md`
- `rust-by-example/src/types/alias.md`
- `rust-by-example/src/types/cast.md`
- `rust-by-example/src/conversion/from_into.md`
- `rust-by-example/src/conversion/try_from_try_into.md`
- `book/src/ch20-03-advanced-types.md`
- `std::convert` module documentation (`From`, `Into`, `TryFrom`, `TryInto`, `AsRef`, `AsMut`)
