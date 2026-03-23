# Existential Types

> **Since:** Rust 1.0 (`dyn Trait` as trait objects); Rust 1.26 (`impl Trait` in return position); `dyn` keyword required since Rust 1.27

## What it is

An existential type says "there exists some concrete type satisfying a trait bound, but the caller does not know which one." Rust has two forms of existential types: **trait objects** (`dyn Trait`) and **opaque return types** (`impl Trait` in return position).

`dyn Trait` is a **dynamically-dispatched existential**. A `Box<dyn Draw>` holds a value of some type that implements `Draw`, erased behind a vtable. The caller interacts only through the trait's methods. `impl Trait` in return position is a **statically-dispatched opaque existential**. The compiler knows the concrete type but hides it from the caller -- each call site sees only the trait interface, while the compiler monomorphizes for performance.

Together, these mechanisms enable polymorphic APIs, heterogeneous collections, and encapsulated return types without exposing implementation details.

## What constraint it enforces

**Existential types hide the concrete type behind a trait interface. The consumer can only call methods defined by the trait -- they cannot downcast, pattern-match, or assume any specific concrete type.**

- `dyn Trait` erases the concrete type at runtime via a vtable. Size is unknown, requiring indirection (`Box`, `&`, `Arc`).
- `impl Trait` in return position hides the concrete type at the API boundary while preserving monomorphization.
- Both forms prevent the caller from depending on implementation details.

## Minimal snippet

```rust
trait Summarize {
    fn summary(&self) -> String;
}

struct Article { title: String }
impl Summarize for Article {
    fn summary(&self) -> String { format!("Article: {}", self.title) }
}

struct Tweet { body: String }
impl Summarize for Tweet {
    fn summary(&self) -> String { format!("Tweet: {}", self.body) }
}

// dyn existential — heterogeneous collection
fn all_summaries(items: &[Box<dyn Summarize>]) -> Vec<String> {
    items.iter().map(|i| i.summary()).collect()
}

// impl existential — opaque return type
fn make_notification() -> impl Summarize {
    Article { title: "Breaking News".into() }
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Trait objects** [-> catalog/T36](T36-trait-objects.md) | `dyn Trait` IS the runtime existential. Trait objects carry a vtable for dynamic dispatch and erase the concrete type. |
| **Generics and bounds** [-> catalog/T04](T04-generics-bounds.md) | `impl Trait` in argument position is sugar for a generic bound (`fn f(x: impl T)` == `fn f<X: T>(x: X)`). In return position, it is a true opaque existential. |
| **Smart pointers** [-> catalog/T24](T24-smart-pointers.md) | `Box<dyn Trait>`, `Rc<dyn Trait>`, and `Arc<dyn Trait>` provide the indirection needed for dynamically-sized existentials. |
| **Associated types** [-> catalog/T49](T49-associated-types.md) | `dyn Iterator<Item = i32>` fixes the associated type while hiding the concrete iterator. Without fixing the associated type, the trait is not object-safe. |
| **Encapsulation** [-> catalog/T21](T21-encapsulation.md) | `impl Trait` return types hide implementation details without boxing, complementing module-level privacy for encapsulation. |

## Gotchas and limitations

1. **Object safety.** Not all traits can be made into `dyn Trait`. A trait is object-safe only if its methods do not use `Self` in return position (by value), have no generic type parameters, and do not require `Sized`. Methods with `where Self: Sized` are excluded from the vtable.

2. **No downcasting by default.** Given `Box<dyn Summarize>`, you cannot recover the concrete `Article` type without opting in via `Any` and `downcast_ref`. This is by design -- existentials hide the concrete type.

3. **Performance cost of dyn.** Trait objects introduce vtable indirection (one pointer dereference per method call) and prevent inlining. For hot paths, prefer `impl Trait` or generics. `dyn Trait` is best when heterogeneity is essential.

4. **impl Trait is not a named type.** You cannot write `let x: impl Summarize = ...` in a `let` binding (except in nightly with `type_alias_impl_trait`). `impl Trait` is limited to function signatures.

5. **Lifetimes with dyn.** `dyn Trait` has an implicit lifetime bound. `Box<dyn Trait>` defaults to `Box<dyn Trait + 'static>`. For borrowed existentials, you must specify: `&'a dyn Trait + 'a`. Getting this wrong causes confusing lifetime errors.

6. **No existential type equality.** Two `impl Trait` return types from different functions are considered different types even if the concrete type happens to be the same. You cannot assign one to a variable expecting the other.

## Beginner mental model

Think of `dyn Trait` as a **gift wrapped in opaque paper**. You know the gift "can be summarized" (implements `Summarize`), but you cannot see what is inside the wrapping. You can only interact through the wrapping's interface (the trait's methods). `impl Trait` is similar but the store (compiler) knows exactly what is inside -- it just prints "gift that can be summarized" on the receipt (function signature) so you do not depend on the specific item.

## Example A -- Heterogeneous collection with trait objects

```rust
trait Shape {
    fn area(&self) -> f64;
    fn name(&self) -> &str;
}

struct Circle { radius: f64 }
impl Shape for Circle {
    fn area(&self) -> f64 { std::f64::consts::PI * self.radius * self.radius }
    fn name(&self) -> &str { "circle" }
}

struct Rect { w: f64, h: f64 }
impl Shape for Rect {
    fn area(&self) -> f64 { self.w * self.h }
    fn name(&self) -> &str { "rectangle" }
}

fn total_area(shapes: &[Box<dyn Shape>]) -> f64 {
    shapes.iter().map(|s| s.area()).sum()
}

fn main() {
    let shapes: Vec<Box<dyn Shape>> = vec![
        Box::new(Circle { radius: 2.0 }),
        Box::new(Rect { w: 3.0, h: 4.0 }),
    ];
    println!("total area: {:.2}", total_area(&shapes)); // 24.57
}
```

## Example B -- Opaque return type with impl Trait

```rust
fn fibonacci() -> impl Iterator<Item = u64> {
    let mut a = 0u64;
    let mut b = 1u64;
    std::iter::from_fn(move || {
        let val = a;
        let next = a + b;
        a = b;
        b = next;
        Some(val)
    })
}

fn main() {
    let fibs: Vec<u64> = fibonacci().take(10).collect();
    println!("{fibs:?}");  // [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    // The concrete iterator type is hidden — caller sees only `impl Iterator`
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Existential types hide concrete representations, preventing clients from constructing or manipulating values outside the defined interface.
- [-> UC-13](../usecases/UC13-state-machines.md) -- `impl Trait` return types can hide state machine internals while exposing only valid transitions.
- [-> UC-20](../usecases/UC20-ownership-apis.md) -- `Box<dyn Trait>` transfers ownership of existentially-typed values, combining ownership semantics with type erasure.

## Source anchors

- `rust-reference/src/types/trait-object.md`
- `rust-reference/src/types/impl-trait.md`
- `book/src/ch17-02-trait-objects.md`
- `book/src/ch10-02-traits.md` -- "Returning Types that Implement Traits"
- `nomicon/src/exotic-sizes.md` -- dynamically sized types
