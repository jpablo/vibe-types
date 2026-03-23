# Structural Contracts (via Trait Bounds)

## The constraint

Accept any type that satisfies a set of capabilities, without requiring a shared base type. Rust is nominally typed, but trait bounds on generics approximate structural typing: if a type implements the required traits, it is accepted regardless of its concrete name or module.

## Feature toolkit

- `[-> T04](../catalog/T04-generics-bounds.md)`
- `[-> T07](../catalog/T07-structural-typing.md)`
- `[-> T36](../catalog/T36-trait-objects.md)`
- `[-> T05](../catalog/T05-type-classes.md)`

## Patterns

- Pattern A: trait bounds as structural requirements on generics.
```rust
use std::fmt::Display;

fn log_item<T: Display + Send>(item: &T) {
    println!("[log] {item}");
}
```
Any type that implements `Display + Send` is accepted — no shared base needed.

- Pattern B: `where` clauses for readability with multiple bounds.
```rust
fn process<T>(item: T)
where
    T: Clone + std::fmt::Debug + PartialOrd,
{
    let backup = item.clone();
    println!("{backup:?}");
}
```

- Pattern C: `dyn Trait` for runtime-dispatched structural contracts.
```rust
fn render_all(items: &[&dyn std::fmt::Display]) {
    for item in items {
        println!("{item}");
    }
}

let items: Vec<&dyn std::fmt::Display> = vec![&42, &"hello", &3.14];
render_all(&items);
```

- Pattern D: trait objects in collections for heterogeneous data.
```rust
trait Plugin: Send + Sync {
    fn name(&self) -> &str;
    fn execute(&self);
}

struct Registry {
    plugins: Vec<Box<dyn Plugin>>,
}

impl Registry {
    fn run_all(&self) {
        for p in &self.plugins {
            println!("Running {}", p.name());
            p.execute();
        }
    }
}
```

## Tradeoffs

- Trait bounds enable static dispatch with zero runtime cost but require monomorphisation (code size growth).
- `dyn Trait` enables heterogeneous collections and dynamic dispatch but adds indirection, loses inlining, and requires object safety.
- Unlike true structural typing, the provider must explicitly `impl Trait` — accidental conformance is impossible.

## When to use which feature

- Use generic bounds for performance-critical, statically dispatched APIs.
- Use `dyn Trait` when types are unknown at compile time or you need heterogeneous containers.
- Combine both: accept `impl Trait` in public APIs but store `Box<dyn Trait>` internally.

## Source anchors

- `book/src/ch10-02-traits.md`
- `book/src/ch18-02-trait-objects.md`
- `rust-by-example/src/generics/bounds.md`
- `rust-by-example/src/trait/dyn.md`
