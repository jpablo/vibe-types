# Associated Types and Advanced Traits

## What it is

Associated types and advanced trait features encode related type relationships in trait definitions.

## What constraint it enforces

**Each trait implementation must provide a consistent associated-type choice used by all trait methods.**

## Minimal snippet

```rust
trait Contains {
    type A;
    type B;

    fn contains(&self, a: &Self::A, b: &Self::B) -> bool;
}
```

## Interaction with other features

- Refines generic constraints from `[-> catalog/05]`.
- Builds on base trait model in `[-> catalog/06]`.
- Supports `[-> UC-03]`.

## Gotchas and limitations

- Associated types reduce call-site noise but remove some flexibility compared with generic trait parameters.
- Missing associated type definitions in impls break method signatures that rely on `Self::Type`.

## Use-case cross-references

- `[-> UC-03]`

## Source anchors

- `book/src/ch20-02-advanced-traits.md`
- `rust-by-example/src/generics/assoc_items/types.md`
