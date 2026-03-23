# Coherence and Orphan Rules

## What it is

Coherence is the property that for every combination of a trait and a type, there is *at most one* implementation visible in the entire compiled program. The compiler enforces this globally: it does not matter how many crates are linked together, no two of them may provide competing `impl Trait for Type` entries. This guarantee is what allows Rust to resolve method calls and trait bounds unambiguously without any runtime dispatch tiebreakers.

The *orphan rule* is the mechanism that makes coherence achievable in a world of independently published crates. It states that you may write `impl Trait for Type` only if your crate owns the trait **or** your crate owns the type (with some nuances around "covered" type parameters). Without this restriction, two crate authors could both publish `impl Display for Vec<i32>`, and any program that depended on both would face an irreconcilable conflict at link time. The orphan rule prevents the conflict from ever arising by forbidding both authors from writing that impl in the first place.

Several refinements sit on top of these two core ideas. *Blanket impls* like `impl<T: Display> ToString for T` in the standard library satisfy coherence because `std` owns `ToString`, but they have far-reaching consequences: no downstream crate can add its own `impl ToString for MyType` because the blanket already covers it. The compiler also performs *negative reasoning* — it considers impls that *might* be added by upstream crates in the future when deciding whether your impl is safe, preserving semver compatibility. Certain types marked `#[fundamental]` (`&T`, `&mut T`, `Box<T>`) receive special treatment: the compiler acts as though the *inner* type determines locality, so you can implement a foreign trait for `&MyLocalType`. Finally, the *newtype pattern* is the standard escape hatch — wrapping a foreign type in a local single-field struct makes the wrapper local, letting you implement any trait you want on it.

## What constraint it enforces

**For any (trait, type) pair, exactly zero or one `impl` block exists across the entire dependency graph, and you may only write that block if your crate owns the trait or the type.**

More specifically:

- **No overlapping impls.** If two `impl` blocks could apply to the same concrete type, the compiler rejects the program even if the overlap is only theoretical (i.e., no concrete type triggers both today).
- **Orphan restriction.** An `impl<T..> ForeignTrait for ForeignType<T..>` is illegal unless at least one type parameter `T` is "covered" by a local type (e.g., `ForeignTrait for Vec<LocalType>` is allowed because the local type appears in the type argument).
- **Forward compatibility.** The compiler assumes upstream crates may add new impls in future versions, so it conservatively rejects impls that *could* conflict later. This is why adding a blanket impl to a library is a semver-breaking change.
- **Deterministic dispatch.** Because at most one impl exists, the compiler can resolve every trait method call at compile time with no ambiguity, keeping zero-cost abstractions truly zero-cost.

## Minimal snippet

```rust,compile_fail
use std::fmt;

// Both `Display` (trait) and `Vec<i32>` (type) are foreign — orphan rule violation.
impl fmt::Display for Vec<i32> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:?}", self)
    }
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Traits and trait bounds** [-> T05](T05-type-classes.md) | Coherence is the reason trait bounds resolve to a single impl. Every `where T: Trait` can select exactly one implementation, enabling monomorphization without ambiguity. |
| **Generics** [-> T04](T04-generics-bounds.md) | Generic impls (`impl<T> Trait for Vec<T>`) widen the surface area of coherence checks. A single blanket impl can cover infinitely many concrete types, blocking downstream impls for all of them. |
| **Smart pointers** [-> T24](T24-smart-pointers.md) | `Box<T>` is `#[fundamental]`, so `impl ForeignTrait for Box<LocalType>` is legal even though `Box` itself is foreign. `Rc<T>` and `Arc<T>` are *not* fundamental. |
| **Newtype pattern** [-> T01](T01-algebraic-data-types.md) | The most common workaround for orphan-rule violations. A `struct Wrapper(ForeignType)` is local, so any trait can be implemented on it. |
| **Send and Sync** [-> T50](T50-send-sync.md) | These auto-traits have blanket impls for all eligible types. Coherence ensures that a type is either `Send` or not — there is no conflicting opt-in from different crates. |

## Gotchas and limitations

1. **The newtype workaround requires manual delegation.** Wrapping `Vec<T>` in `struct MyVec(Vec<T>)` makes `MyVec` local, but you lose all of `Vec`'s trait impls. You must manually implement `Deref`, `Iterator`, `Index`, etc., or use a crate like `derive_more` to forward them.

2. **Blanket impls block more than you'd expect.** The standard library's `impl<T> From<T> for T` (the identity conversion) means you cannot write `impl From<MyType> for MyType` — the blanket already covers it, even though both sides are local.

   ```rust,compile_fail
   struct Foo;
   // error[E0119]: conflicting implementation — blocked by `impl<T> From<T> for T`
   impl From<Foo> for Foo {
       fn from(f: Foo) -> Self { f }
   }
   ```

3. **Adding a blanket impl is a breaking change.** If a library adds `impl<T: Debug> MyTrait for T`, every downstream crate that had its own `impl MyTrait for SomeDebugType` will break. This is why blanket impls in public crates must be introduced with extreme care (and a major version bump).

4. **Coherence errors can cite impls you never wrote.** When the compiler reports a conflict, the other impl may live deep inside a transitive dependency. The error message names the conflicting impl, but tracing it requires inspecting the dependency tree.

5. **`#[fundamental]` is unstable for user-defined types.** Only `&T`, `&mut T`, and `Box<T>` are fundamental in stable Rust. You cannot mark your own wrapper type as fundamental to gain the same relaxed orphan-rule treatment.

6. **You cannot implement a foreign trait for a tuple of foreign types.** Even though tuples feel "structural," they are defined in `core`, so `impl ForeignTrait for (ForeignA, ForeignB)` is an orphan-rule violation.

7. **Specialization would relax overlap — but it is unstable.** The `min_specialization` feature allows a more specific impl to override a more general one, but it has been unstable for years and its design is not finalized.

8. **Newtype proliferation.** Projects that frequently hit orphan-rule walls can accumulate many thin wrapper types, each forwarding a large surface of traits. This is a real maintenance burden and a sign that the abstraction boundaries may need rethinking.

## Beginner mental model

Think of the Rust ecosystem as a collection of **sovereign territories** (crates). Each territory can make laws (trait impls) about things it owns — its own traits and its own types. You are free to declare "my type implements your trait" because your type is on your land, and you are free to declare "your type implements my trait" because your trait is your invention. But you are *not* allowed to declare "someone else's type implements someone else's trait" — that is legislating on foreign soil, and if a third territory tried the same thing, there would be a conflict with no authority to resolve it.

The newtype pattern is like importing a foreign good and repackaging it under your own brand. Once wrapped, the package is yours, and you can attach any label (trait impl) you like. The cost is that you must manually forward all the original capabilities that consumers expect. The `#[fundamental]` exception for `&T` and `Box<T>` is a pragmatic concession: references and boxes are so thin that the compiler treats them as transparent wrappers, letting you impl traits for `&YourType` as naturally as for `YourType` itself.

## Example A — Local trait on local type

```rust
trait Summarize {
    fn summary(&self) -> String;
}

struct Article { title: String, body: String }

// Both `Summarize` and `Article` are defined in this crate — always legal.
impl Summarize for Article {
    fn summary(&self) -> String {
        format!("{}: {}...", self.title, &self.body[..40.min(self.body.len())])
    }
}
```

## Example B — Foreign trait on local type

```rust
use std::fmt;

struct Degrees(f64);

// `Display` is foreign, but `Degrees` is local — legal.
impl fmt::Display for Degrees {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:.1}°", self.0)
    }
}

fn main() {
    println!("{}", Degrees(98.6));  // prints "98.6°"
}
```

## Example C — Foreign trait on foreign type (illegal)

```rust,compile_fail
use std::fmt;

// Both `Display` and `Vec<String>` are foreign — orphan rule violation.
impl fmt::Display for Vec<String> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.join(", "))
    }
}
// error[E0117]: only traits defined in the current crate can be implemented
//               for types defined outside of the crate
```

## Example D — Newtype workaround

```rust
use std::fmt;

// Wrap the foreign type in a local struct.
struct CommaSeparated(Vec<String>);

impl fmt::Display for CommaSeparated {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0.join(", "))
    }
}

// Optionally implement Deref so callers can use Vec methods transparently.
impl std::ops::Deref for CommaSeparated {
    type Target = Vec<String>;
    fn deref(&self) -> &Self::Target { &self.0 }
}

fn main() {
    let items = CommaSeparated(vec!["a".into(), "b".into(), "c".into()]);
    println!("{items}");         // Display: "a, b, c"
    println!("len={}", items.len()); // Deref to Vec: len() works
}
```

## Example E — Blanket impl blocking a downstream impl

```rust,compile_fail
use std::string::ToString;

struct Port(u16);

// This is already covered by `impl<T: Display> ToString for T` in std.
// If we also impl Display for Port (which we should), the blanket provides
// ToString automatically — writing our own would conflict.
impl ToString for Port {
    fn to_string(&self) -> String {
        format!(":{}", self.0)
    }
}
// error[E0119]: conflicting implementations of trait `ToString` for type `Port`
//              — upstream crates may add a new impl of trait `std::fmt::Display`
```

The fix: implement `Display` instead and let the blanket derive `ToString` for you.

```rust
use std::fmt;

struct Port(u16);

impl fmt::Display for Port {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, ":{}", self.0)
    }
}

fn main() {
    let p = Port(8080);
    println!("{p}");             // Display
    println!("{}", p.to_string()); // ToString via blanket — no conflict
}
```

## Example F — `#[fundamental]` types

```rust
use std::fmt;

struct Sensor { id: u32, value: f64 }

// `Display` is foreign, `&Sensor` involves a foreign reference type,
// but `&T` is #[fundamental] — the compiler treats the inner type
// as the locality marker. Since `Sensor` is local, this is legal.
impl fmt::Display for &Sensor {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "sensor-{}={:.2}", self.id, self.value)
    }
}

fn main() {
    let s = Sensor { id: 1, value: 3.14 };
    println!("{}", &s); // "sensor-1=3.14"
}
```

## Common compiler errors and how to read them

### `error[E0117]: only traits defined in the current crate can be implemented for types defined outside of the crate`

The classic orphan-rule violation. You tried to implement a foreign trait for a foreign type.

```
error[E0117]: only traits defined in the current crate can be implemented
              for types defined outside of the crate
 --> src/main.rs:3:1
  |
3 | impl fmt::Display for Vec<String> {
  | ^^^^^^^^^^^^^^^^^^^^^^-----------
  |                       |
  |                       `Vec` is not defined in the current crate
```

**How to fix:** Wrap the foreign type in a local newtype (`struct MyVec(Vec<String>)`) and implement the trait on the wrapper, or define a local trait instead.

### `error[E0119]: conflicting implementations of trait`

Two impl blocks could apply to the same type. Often one is a blanket impl from a dependency.

```
error[E0119]: conflicting implementations of trait `ToString` for type `Port`
 --> src/main.rs:5:1
  |
5 | impl ToString for Port {
  | ^^^^^^^^^^^^^^^^^^^^^^^
  |
  = note: conflicting implementation in crate `alloc`:
          - impl<T> ToString for T where T: Display + ?Sized;
```

**How to fix:** Remove the conflicting impl and rely on the blanket (implement `Display` to get `ToString` for free), or use more specific trait bounds to narrow the overlap.

### `error[E0210]: type parameter ... must be covered by another type`

You used a generic parameter in a foreign-trait impl without "covering" it with a local type.

```
error[E0210]: type parameter `T` must be covered by another type
              when it appears before the first local type
 --> src/main.rs:3:1
  |
3 | impl<T> From<T> for MyWrapper {
  |      ^ type parameter `T` must be covered by another type
```

**How to fix:** Restructure so the uncovered parameter appears inside a local type (e.g., `impl<T> From<LocalAdapter<T>> for MyWrapper`), or remove the generic and implement for concrete types only.

### `error[E0120]: the Drop trait may only be implemented for local types`

A specialization of the orphan rule for `Drop`. You cannot implement `Drop` for a type defined in another crate, even if no other `Drop` impl exists.

```
error[E0120]: the `Drop` trait may only be implemented for local types
 --> src/main.rs:1:1
  |
1 | impl Drop for String {
  | ^^^^^^^^^^^^^^^^^^^^^ `String` is not defined in the current crate
```

**How to fix:** Use a local wrapper type if you need custom drop behavior for a foreign type.

## Use-case cross-references

- [-> UC-07](../usecases/UC23-diagnostics.md) — Strategies for diagnosing and working around orphan-rule and coherence errors in real projects.
- [-> UC-02](../usecases/UC20-ownership-apis.md) — API design must account for coherence when exposing traits meant to be implemented by downstream crates.
- [-> UC-05](../usecases/UC21-concurrency.md) — Blanket impls of `Send` and `Sync` rely on coherence to guarantee thread-safety properties globally.

## Source anchors

- `rust/src/doc/reference/src/items/implementations.md`
- `rust/src/doc/reference/src/type-system.md`
- `rust/src/doc/rustc-dev-guide/src/coherence.md`
- `book/src/ch10-02-traits.md` (orphan rule introduction)
- `rust-by-example/src/trait/impl_trait.md`
