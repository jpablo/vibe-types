# Traits and Implementations

## What it is

Traits are Rust's mechanism for defining shared behavior across types. A trait declares a set of method signatures (and optionally default bodies) that any type can implement. When a type provides an `impl Trait for Type` block, it commits to fulfilling every required method in the contract. Generic code can then constrain its type parameters with trait bounds (`T: Summary`), guaranteeing at compile time that only types supplying the right behavior are accepted. Unlike dynamically dispatched interfaces in many OOP languages, trait bounds are resolved statically by default, producing monomorphized machine code with zero runtime overhead.

Traits go well beyond simple interfaces. A trait can supply **default method implementations** that adopters inherit for free and may optionally override. Traits can require **supertraits** (`trait Printable: Display`), meaning a type must implement `Display` before it can implement `Printable`. Rust also has **marker traits** — traits with no methods at all — such as `Send`, `Sync`, and `Copy`, which act as compile-time flags the compiler uses to enforce safety invariants. The `#[derive(...)]` attribute lets the compiler generate standard trait implementations automatically for types whose fields all satisfy the trait, eliminating boilerplate for `Debug`, `Clone`, `PartialEq`, `Hash`, and others.

It helps to contrast traits with similar concepts in other languages. Java interfaces (pre-Java 8) had no method bodies; since Java 8 they support `default` methods, but they still cannot hold per-instance state and they resolve via vtable at runtime. Scala traits can carry both methods and fields (state), making them closer to mixins. Haskell type classes are the closest analogue: like Rust traits, they define behavior contracts resolved at compile time, support default implementations, and enable ad-hoc polymorphism — but Haskell's type class resolution is global and open, whereas Rust's coherence (orphan) rules [-> T25](T25-coherence-orphan.md) ensure there is at most one implementation of a given trait for a given type within the entire dependency graph.

## What constraint it enforces

**Types must satisfy declared trait contracts before they can be used with trait-constrained APIs, and each trait-type pair may have at most one implementation in the program.**

More specifically:

- **Compile-time contract checking.** If a function requires `T: Clone + Debug`, the compiler rejects any call where `T` does not implement both traits. No value can "sneak past" a bound.
- **Coherence / orphan rule.** At most one `impl Trait for Type` can exist. You cannot implement a foreign trait for a foreign type — at least one of the two must be local to your crate [-> T25](T25-coherence-orphan.md).
- **Exhaustive implementation.** An `impl` block must supply every required method. Omitting even one produces `error[E0046]`.
- **Scope gating.** A trait's methods are available for method-call syntax only when the trait is in scope (`use` it or import its parent module). This prevents accidental name collisions across crates.

## Minimal snippet

```rust
trait Summary {
    fn summarize(&self) -> String;
}

struct Article { title: String }

impl Summary for Article {
    fn summarize(&self) -> String {
        format!("Article: {}", self.title)
    }
}

fn notify(item: &impl Summary) {
    println!("Breaking: {}", item.summarize());
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Generics** [-> T04](T04-generics-bounds.md) | Trait bounds constrain generic type parameters. `fn print<T: Display>(v: T)` accepts any type implementing `Display`. Where clauses provide the same power with clearer syntax for complex bounds. |
| **Associated types & advanced traits** [-> T49](T49-associated-types.md) | Associated types let a trait fix an output type per implementation (e.g., `Iterator::Item`), reducing the number of generic parameters callers must specify. |
| **Trait objects (`dyn`)** [-> T36](T36-trait-objects.md) | `dyn Trait` enables dynamic dispatch when the concrete type is unknown at compile time. Only *object-safe* traits (no `Self`-returning methods, no generic methods) can be used behind `dyn`. |
| **Structs & enums** [-> T01](T01-algebraic-data-types.md) | Traits give behavior to data. A struct defines layout; a trait defines capabilities. Combining `#[derive(...)]` with custom `impl` blocks is the standard pattern for building types. |
| **Coherence & orphan rules** [-> T25](T25-coherence-orphan.md) | The orphan rule limits where `impl` blocks can live, ensuring global uniqueness. Newtypes [-> T01](T01-algebraic-data-types.md) are the standard workaround when you need to implement a foreign trait for a foreign type. |
| **Send and Sync** [-> T50](T50-send-sync.md) | `Send` and `Sync` are marker traits auto-implemented by the compiler. Whether a type is `Send` or `Sync` depends on the traits and properties of its fields. |

## Gotchas and limitations

1. **Orphan rule blocks cross-crate impls.** You cannot `impl Display for Vec<T>` in your own crate because both `Display` and `Vec` are foreign. The workaround is the newtype pattern [-> T25](T25-coherence-orphan.md): wrap `Vec<T>` in a local struct and implement the trait on the wrapper.

2. **Trait must be in scope to call its methods.** If you implement `Summary` for `Article` in module `a`, code in module `b` cannot call `article.summarize()` unless `use a::Summary;` is present. The compiler will suggest the `use` statement when this happens.

3. **Default methods can be silently overridden.** When a trait provides a default body and an implementor overrides it, callers may get surprising behavior. There is no `override` keyword or annotation — the compiler does not warn that a default was replaced.

4. **`Self` in return position breaks object safety.** A method like `fn clone(&self) -> Self` prevents the trait from being used as `dyn Trait` because the compiler cannot know the concrete return size at runtime. If you need dynamic dispatch, avoid `Self` in method signatures or provide a separate object-safe sub-trait.

5. **Conflicting method names require disambiguation.** When two traits define a method with the same name and a type implements both, calling the method by name is ambiguous. You must use **fully qualified syntax**: `<Type as Trait>::method(&value)`.

   ```rust
   trait Pilot { fn fly(&self); }
   trait Wizard { fn fly(&self); }
   struct Human;
   impl Pilot for Human { fn fly(&self) { println!("captain speaking"); } }
   impl Wizard for Human { fn fly(&self) { println!("up!"); } }
   // human.fly();                         // error: ambiguous
   Pilot::fly(&Human);                     // OK
   <Human as Wizard>::fly(&Human);         // OK — fully qualified
   ```

6. **Blanket implementations are powerful but can conflict.** The standard library uses blankets like `impl<T: Display> ToString for T`. If you define a new trait and add a blanket impl, downstream crates may find they can no longer add their own impls without conflicting (`error[E0119]`).

7. **`#[derive]` only works for standard traits.** You can derive `Debug`, `Clone`, `Copy`, `PartialEq`, `Eq`, `Hash`, `Default`, `PartialOrd`, and `Ord` out of the box. Custom derive for your own traits requires writing a procedural macro, which lives in a separate `proc-macro` crate.

8. **Implementing a trait for `&T` vs for `T`.** `impl Trait for &T` and `impl Trait for T` are distinct. A blanket like `impl<T: Trait> Trait for &T` is sometimes added for ergonomics, but omitting it means `&MyType` does not automatically satisfy bounds that `MyType` does. This trips up beginners working with iterator adaptors and closures.

## Beginner mental model

Think of a trait as a **job description**: it lists the abilities a candidate must have. An `impl Trait for Type` block is the **resume** that proves the type can do the job. When generic code says `T: Summary`, it is a job posting — only candidates with the right resume get hired. The compiler is the recruiter: it checks every resume at compile time and rejects unqualified applicants immediately.

Default methods are like skills the job description says "nice to have — we provide training." Every implementor gets the default for free but can bring their own version instead. Supertraits are prerequisites: "must already be certified in `Display` before applying for `Printable`." Marker traits are background checks — `Send` and `Sync` carry no methods but certify the type is safe to use in specific contexts (threads). The `#[derive]` attribute is an automatic credential generator: if all your fields already have the skill, the compiler can prove you do too.

## Example A — Define a trait and implement it for a struct

```rust
trait Greet {
    fn greeting(&self) -> String;
}

struct User { name: String }

impl Greet for User {
    fn greeting(&self) -> String {
        format!("Hello, {}!", self.name)
    }
}

fn main() {
    let u = User { name: "Alice".into() };
    println!("{}", u.greeting());  // "Hello, Alice!"
}
```

## Example B — Default methods and overriding

```rust
trait Greet {
    fn greeting(&self) -> String {
        String::from("Hello, stranger!")       // default implementation
    }
}

struct Anonymous;
impl Greet for Anonymous {}                    // inherits the default

struct User { name: String }
impl Greet for User {
    fn greeting(&self) -> String {             // overrides the default
        format!("Hello, {}!", self.name)
    }
}

fn main() {
    println!("{}", Anonymous.greeting());      // "Hello, stranger!"
    println!("{}", User { name: "Bob".into() }.greeting()); // "Hello, Bob!"
}
```

## Example C — Supertraits: `trait Printable: Display`

```rust
use std::fmt;

trait Printable: fmt::Display {
    fn print(&self) {
        println!("{self}");         // can use Display because it is a supertrait
    }
}

struct Point { x: f64, y: f64 }

impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}

impl Printable for Point {}         // works because Point: Display

fn main() {
    Point { x: 1.0, y: 2.0 }.print();  // "(1, 2)"
}
```

## Example D — Derive macros for common traits

```rust
#[derive(Debug, Clone, PartialEq)]
struct Color {
    r: u8,
    g: u8,
    b: u8,
}

fn main() {
    let red = Color { r: 255, g: 0, b: 0 };
    let also_red = red.clone();

    println!("{:?}", red);               // Debug: Color { r: 255, g: 0, b: 0 }
    assert_eq!(red, also_red);           // PartialEq comparison
}
```

`#[derive]` generates an `impl` block for each listed trait. It requires every field's type to already implement the trait — if even one field does not, the derive fails at compile time.

## Example E — Fully qualified disambiguation when traits collide

```rust
trait UsName  { fn name(&self) -> &str; }
trait EuName  { fn name(&self) -> &str; }

struct Product;

impl UsName for Product { fn name(&self) -> &str { "Widget" } }
impl EuName for Product { fn name(&self) -> &str { "Gadget" } }

fn main() {
    let p = Product;
    // p.name();                               // error: ambiguous
    println!("{}", <Product as UsName>::name(&p));  // "Widget"
    println!("{}", <Product as EuName>::name(&p));  // "Gadget"
}
```

When two traits define methods with the same signature, Rust refuses to guess. Fully qualified syntax removes all ambiguity.

## Example F — Blanket implementation pattern

```rust
use std::fmt;

trait Log {
    fn log(&self);
}

// Blanket: every type that implements Display automatically implements Log
impl<T: fmt::Display> Log for T {
    fn log(&self) {
        println!("[LOG] {self}");
    }
}

fn main() {
    "hello".log();       // &str: Display  -> Log
    42_i32.log();        // i32:  Display  -> Log
    3.14_f64.log();      // f64:  Display  -> Log
}
```

Blanket implementations extend behavior to an entire family of types at once. The standard library's `impl<T: Display> ToString for T` follows the same pattern.

## Common compiler errors and how to read them

### `error[E0277]: the trait bound 'MyType: Summary' is not satisfied`

You passed a value to a function or method that requires a trait bound the type does not meet.

```
error[E0277]: the trait bound `Tweet: Summary` is not satisfied
 --> src/main.rs:12:12
  |
12 |     notify(&tweet);
  |            ^^^^^^ the trait `Summary` is not implemented for `Tweet`
```

**How to fix:** Add `impl Summary for Tweet { ... }` with all required methods. If the trait lives in another crate, make sure you `use` it.

### `error[E0405]: cannot find trait 'Summary' in this scope`

The trait name is not imported in the current module.

```
error[E0405]: cannot find trait `Summary` in this scope
 --> src/lib.rs:5:6
  |
5 | impl Summary for Article {
  |      ^^^^^^^ not found in this scope
```

**How to fix:** Add `use crate::Summary;` (or the appropriate path) at the top of the file. If the trait is in an external crate, add a `use external_crate::Summary;` import.

### `error[E0119]: conflicting implementations of trait`

Two `impl` blocks for the same trait-type pair exist, or a blanket implementation overlaps with a specific one.

```
error[E0119]: conflicting implementations of trait `Log` for type `String`
 --> src/main.rs:10:1
  |
6  | impl<T: Display> Log for T { ... }
  | ---------------------------------- first implementation here
10 | impl Log for String { ... }
  | ^^^^^^^^^^^^^^^^^^^^^^^^^ conflicting implementation for `String`
```

**How to fix:** Remove the specific impl and rely on the blanket, or restructure the blanket to exclude the conflicting type using negative bounds or specialization (nightly-only).

### `error[E0046]: not all trait items implemented`

Your `impl` block is missing one or more required methods.

```
error[E0046]: not all trait items implemented, missing: `summarize`
 --> src/main.rs:8:1
  |
2 | trait Summary {
  |     fn summarize(&self) -> String;
  |     ------------------------------ `summarize` needs to be implemented
...
8 | impl Summary for Article {}
  | ^^^^^^^^^^^^^^^^^^^^^^^^^^ missing `summarize` in implementation
```

**How to fix:** Add the missing method(s) inside the `impl` block. If the trait provides a default implementation you are happy with, the method can be omitted — but required methods (no body in the trait definition) must always be supplied.

## Use-case cross-references

- [-> UC-03](../usecases/UC04-generic-constraints.md) — Using trait bounds to constrain generic parameters so APIs only accept types with the right capabilities.
- [-> UC-04](../usecases/UC14-extensibility.md) — Designing extensible interfaces where new types can be added without modifying existing code.
- [-> UC-05](../usecases/UC21-concurrency.md) — Marker traits `Send` and `Sync` enforce thread-safety at compile time.

## Recommended libraries

| Library | Description |
|---------|-------------|
| [serde](https://docs.rs/serde) | Serialization framework built on `Serialize`/`Deserialize` traits — the canonical example of trait-based generic programming |
| [rayon](https://docs.rs/rayon) | Data parallelism via `ParallelIterator` trait — drop-in parallel `iter()` using trait extension methods |
| [tower](https://docs.rs/tower) | `Service` trait for async request/response middleware — composable, trait-driven service stacks |

## Source anchors

- `book/src/ch10-02-traits.md`
- `book/src/ch19-03-advanced-traits.md`
- `rust-by-example/src/trait.md`
- `rust-by-example/src/trait/derive.md`
- `rust-by-example/src/trait/supertraits.md`
- `rust-by-example/src/trait/disambiguating.md`
