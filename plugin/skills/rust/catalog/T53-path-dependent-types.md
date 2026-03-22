# Path-Dependent Types (via Associated Types)

> **Since:** Rust 1.0 (associated types); Rust 1.65 (Generic Associated Types)

## What it is

Rust does not have path-dependent types as a named language feature, but its **associated types** serve the same structural role. In Scala, a path-dependent type `x.Inner` ties a type to a specific object instance. In Rust, `<T as Trait>::Assoc` ties a type to a specific impl — and since each concrete type has exactly one impl of a given trait, the associated type is **determined by the path through the type system**.

The key insight is that `<Vec<u32> as Iterator>::Item` is `u32`, while `<HashMap<String, i32> as Iterator>::Item` is `(String, i32)`. The "path" here is the concrete type, not a runtime object, but the effect is the same: the type member is fixed by the context. Generic Associated Types (GATs) extend this to higher-kinded patterns where the associated type itself carries parameters, enabling lending iterators, async traits, and other advanced patterns.

This file focuses on the **path-dependent aspect** of associated types — how the choice of concrete type determines the associated type, and how that determination propagates through generic code. For the full treatment of associated types, constants, and GATs, see [-> catalog/T49](T49-associated-types.md).

## What constraint it enforces

**The associated type is uniquely determined by the implementing type. Generic code can rely on this determination without knowing the concrete type, and the compiler threads the equality through all trait bounds.**

- `T: Iterator` implies a unique `T::Item`. Two different `T`s yield two unrelated `Item` types.
- Constraining `T: Iterator<Item = u32>` narrows the path — only types whose `Item` is `u32` are accepted.
- GATs add a second level: `T::Item<'a>` depends on both `T` and the lifetime `'a`.

## Minimal snippet

```rust
trait Container {
    type Item;
    fn first(&self) -> Option<&Self::Item>;
}

struct Names(Vec<String>);
struct Scores(Vec<u32>);

impl Container for Names {
    type Item = String;
    fn first(&self) -> Option<&String> { self.0.first() }
}

impl Container for Scores {
    type Item = u32;
    fn first(&self) -> Option<&u32> { self.0.first() }
}

// The return type depends on which Container you pass — path dependence.
fn peek<C: Container>(c: &C) -> Option<&C::Item> {
    c.first()
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Associated types** [-> catalog/T49](T49-associated-types.md) | T49 covers the full mechanics. This file focuses on the path-dependent interpretation: `T::Assoc` is determined by `T`, analogous to `x.Inner` in Scala. |
| **Type classes (traits)** [-> catalog/T05](T05-type-classes.md) | Traits are the vehicle for path-dependent types in Rust. Each impl block pins the associated type, creating the "one answer per type" property. |
| **Generics and bounds** [-> catalog/T04](T04-generics-bounds.md) | Generic bounds like `T: Trait<Assoc = u32>` constrain the path. Without bounds, `T::Assoc` is abstract; with bounds, it resolves to a concrete type. |
| **GATs** | `type Item<'a> where Self: 'a` makes the associated type depend on both the implementing type AND a lifetime — two-dimensional path dependence. |
| **Trait objects** | `dyn Trait<Assoc = u32>` erases the outer path (the concrete type) but pins the associated type. This is analogous to Scala's type projection from a concrete class. |

## Gotchas and limitations

1. **No runtime path dependence.** In Scala, `x.Inner` depends on the runtime identity of `x`. In Rust, `T::Assoc` depends on the compile-time type `T`. Rust has no mechanism for two values of the same type to carry different associated types — that would require dependent types.

2. **Fully qualified syntax for ambiguity.** When a type implements multiple traits with methods of the same name, use `<T as Trait>::Assoc` to disambiguate. This is Rust's explicit path syntax.

3. **Trait objects must pin associated types.** You cannot write `dyn Iterator` — you must write `dyn Iterator<Item = u32>`. The erasure of the concrete type means the associated type must be specified externally.

4. **GAT lifetime bounds.** GATs require `where Self: 'a` bounds that are easy to forget. The compiler's error messages for missing GAT bounds can be confusing.

5. **No type member outside traits.** Unlike Scala, where any class can have `type` members, Rust only supports associated types inside `trait` and `impl` blocks. Structs cannot declare type members directly.

6. **One impl per type per trait.** Rust's coherence rules enforce that a type has at most one impl of a given trait (excluding specialization, which is unstable). This is what makes associated types well-defined — without it, `T::Assoc` would be ambiguous.

## Beginner mental model

Think of each concrete type as **choosing answers to a trait's questions**. The trait `Iterator` asks "what item do you yield?" and `Vec<u32>::IntoIter` answers "`u32`." Once the type is known, the answer is fixed — you cannot get a different `Item` from the same iterator type. This is path dependence: the "path" is the concrete type, and the associated type follows from it automatically.

In Scala terms: Rust's `impl Iterator for MyIter { type Item = u32; }` is like Scala's `class MyIter extends Iterator { type Item = Int }` — the type member is pinned by the implementing class.

## Example A — Path dependence through generic code

```rust
use std::ops::Add;

fn double<T: Add<Output = T> + Copy>(x: T) -> T {
    x + x
}

// For i32: <i32 as Add>::Output = i32, so double returns i32
let n: i32 = double(5);

// For f64: <f64 as Add>::Output = f64, so double returns f64
let f: f64 = double(2.5);

// The return type DEPENDS ON the input type — path dependence at work.
```

## Example B — Simulating Scala's key-value pattern

```rust
trait TypedKey {
    type Value;
    fn name(&self) -> &str;
}

struct AgeKey;
struct NameKey;

impl TypedKey for AgeKey {
    type Value = u32;
    fn name(&self) -> &str { "age" }
}

impl TypedKey for NameKey {
    type Value = String;
    fn name(&self) -> &str { "name" }
}

// Each key determines its value type — but only at the type level,
// not per-instance as in Scala.
fn describe<K: TypedKey>(key: &K, val_str: &str) -> String
where K::Value: std::str::FromStr, <K::Value as std::str::FromStr>::Err: std::fmt::Debug
{
    format!("{} = {}", key.name(), val_str)
}
```

## Example C — GATs for higher-kinded path dependence

```rust
trait CollectionFamily {
    type Collection<T>: IntoIterator<Item = T>;

    fn empty<T>() -> Self::Collection<T>;
    fn singleton<T>(item: T) -> Self::Collection<T>;
}

struct VecFamily;

impl CollectionFamily for VecFamily {
    type Collection<T> = Vec<T>;

    fn empty<T>() -> Vec<T> { Vec::new() }
    fn singleton<T>(item: T) -> Vec<T> { vec![item] }
}

// The collection type depends on both the family AND the element type.
fn build_pair<F: CollectionFamily, T: Clone>(x: T) -> F::Collection<T> {
    F::singleton(x)
}
```

## Comparison with Scala

| Aspect | Scala 3 | Rust |
|--------|---------|------|
| Declaration | `type Inner` in any class/trait | `type Assoc;` only in traits |
| Path | Runtime object: `x.Inner` | Compile-time type: `T::Assoc` |
| Multiple answers per type | Yes (different instances, different types) | No (one impl per type per trait) |
| Projection | `T#Inner` (restricted in Scala 3) | `<T as Trait>::Assoc` (always available) |
| Higher-kinded | Via type lambdas and match types | Via GATs (`type Assoc<'a, T>`) |

## Use-case cross-references

- [-> UC-14](../usecases/UC14-extensibility.md) -- Traits with associated types define extension points; new impls provide new type answers.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Constraining associated types in bounds narrows generic code to specific type families.

## Source anchors

- *The Rust Programming Language* -- Ch. 20.2 "Advanced Traits: Associated Types"
- *Rust Reference* -- [Associated Items](https://doc.rust-lang.org/reference/items/associated-items.html)
- *Rust RFC 1598* -- [Generic Associated Types](https://blog.rust-lang.org/2022/10/28/gats-stabilization.html)
