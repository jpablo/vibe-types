# Traits and Implementations

## What it is

Traits define behavior contracts; implementations provide concrete behavior per type.

## What constraint it enforces

**Types must satisfy declared trait contracts before they can be used with trait-constrained APIs.**

## Minimal snippet

```rust
trait Summary {
    fn summarize(&self) -> String;
}

fn notify<T: Summary>(item: &T) -> String {
    item.summarize()
}
```

## Interaction with other features

- Used by generics in `[-> catalog/05]`.
- Advanced forms in `[-> catalog/07]` and `[-> catalog/08]`.
- Core to `[-> UC-03]`, `[-> UC-04]`, `[-> UC-07]`.

## Gotchas and limitations

- Orphan/coherence rules restrict which trait/type pairs can be implemented in a crate.
- Trait methods require the trait to be in scope for method-call syntax in consumers.

## Use-case cross-references

- `[-> UC-03]`
- `[-> UC-04]`
- `[-> UC-05]`
- `[-> UC-07]`

## Source anchors

- `book/src/ch10-02-traits.md`
- `rust-by-example/src/trait.md`
