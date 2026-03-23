# Generic Capability Constraints

## The constraint

Generic APIs should accept only types that satisfy required capabilities.

## Feature toolkit

- `[-> T04](T04-generics-bounds.md)`
- `[-> T05](T05-type-classes.md)`
- `[-> T49](T49-associated-types.md)`

## Patterns

- Pattern A: trait bounds in API signatures.
```rust
fn render_all<T: std::fmt::Display>(xs: &[T]) -> String {
    xs.iter().map(ToString::to_string).collect::<Vec<_>>().join(",")
}
```
- Pattern B: associated types for coherent relationships.
```rust
trait Parser { type Output; fn parse(&self, s: &str) -> Self::Output; }
```

## Tradeoffs

- Stronger guarantees and better diagnostics versus more complex type signatures.
- Associated types improve coherence but can reduce generic flexibility.

## When to use which feature

- Start with simple trait bounds.
- Use associated types when relationships must stay coherent.

## Source anchors

- `book/src/ch10-01-syntax.md`
- `book/src/ch10-02-traits.md`
- `book/src/ch20-02-advanced-traits.md`
- `rust-by-example/src/generics/bounds.md`
- `rust-by-example/src/generics/assoc_items/types.md`
