# Extensible Polymorphic Interfaces

## The constraint

Allow extension points while preserving compile-time guarantees on behavior.

## Feature toolkit

- `[-> catalog/06]`
- `[-> catalog/08]`

## Patterns

- Pattern A: static dispatch via generics.
```rust
fn draw_all<T: Draw>(xs: &[T]) { for x in xs { x.draw(); } }
```
- Pattern B: runtime extension via trait objects.
```rust
fn draw_dyn(xs: &[Box<dyn Draw>]) { for x in xs { x.draw(); } }
```

## Tradeoffs

- Static dispatch is faster and stricter; dynamic dispatch is more flexible.
- Trait objects require object safety and introduce vtable dispatch.

## When to use which feature

- Prefer generics in closed, performance-critical paths.
- Prefer trait objects for plugin-like open sets.

## Source anchors

- `book/src/ch10-02-traits.md`
- `book/src/ch18-02-trait-objects.md`
- `rust-by-example/src/trait/dyn.md`
