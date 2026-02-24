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

### Beginner mental model

Think of a trait as a behavior checklist and each `impl` as the proof that a type meets every item on that list. Consumers only need the name of the trait, knowing the compiler enforces the rest.

### Example A

```rust
trait Summary {
    fn summarize(&self) -> String;
}

struct Article {
    title: &'static str,
}

impl Summary for Article {
    fn summarize(&self) -> String {
        format!("Article: {}", self.title)
    }
}
```

### Example B

```rust
// Continuing from Example A.
fn announce(item: &impl Summary) {
    println!("Breaking: {}", item.summarize());
}

let blog = Article { title: "Rust traits" };
announce(&blog);
```

### Common compiler errors and how to read them

- `error[E0277]: the trait bound `MyType: Summary` is not satisfied` means the compiler found a value that needs trait behavior (usually via a trait-bound function or method call), but you forgot to `impl` the trait for that type.
- `error[E0405]: cannot find trait `Summary` in this scope` happens when the trait name is misspelled or you forgot `use crate::Summary;` in the current module—bring the trait into scope before implementing or calling it.

## Use-case cross-references

- `[-> UC-03]`
- `[-> UC-04]`
- `[-> UC-05]`
- `[-> UC-07]`

## Source anchors

- `book/src/ch10-02-traits.md`
- `rust-by-example/src/trait.md`
