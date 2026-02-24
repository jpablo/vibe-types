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

### Beginner mental model

A trait can promise multiple related types (like `Input` and `Output`). Associated types let each implementation declare concrete members so callers work with `Self::TypeName` without repeating generics.

### Example A

```rust
trait PairContainer {
    type Item;

    fn add(&mut self, item: Self::Item);
    fn contains(&self, item: &Self::Item) -> bool;
}

struct Bucket(Vec<i32>);

impl PairContainer for Bucket {
    type Item = i32;

    fn add(&mut self, item: i32) {
        self.0.push(item);
    }

    fn contains(&self, item: &i32) -> bool {
        self.0.contains(item)
    }
}
```

### Example B

```rust
// Continuing from Example A.
fn check_balance<C: PairContainer<Item = i32>>(container: &C, needle: i32) -> bool {
    container.contains(&needle)
}

let mut bucket = Bucket(Vec::new());
bucket.add(5);
assert!(check_balance(&bucket, 5));
```

### Common compiler errors and how to read them

- `error[E0207]: the type parameter `Item` must be used as the type parameter `PairContainer::Item` in trait objects` flags that you tried to use a trait object (`&dyn PairContainer`) while the trait exposes a bare associated type; add extra constraints (e.g., use `dyn PairContainer<Item = i32>`) or prefer generics.
- `error[E0195]: lifetime parameters or types are incorrectly declared in the trait` usually comes from forgetting to declare `type Item;` in the trait or giving the impl a different name; match each trait-associated type exactly.

## Use-case cross-references

- `[-> UC-03]`

## Source anchors

- `book/src/ch20-02-advanced-traits.md`
- `rust-by-example/src/generics/assoc_items/types.md`
