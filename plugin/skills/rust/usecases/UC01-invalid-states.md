# Preventing Invalid States

## The constraint

Represent only valid domain states in types so invalid combinations cannot compile.

## Feature toolkit

- `[-> catalog/04]`
- `[-> catalog/09]`

## Patterns

- Pattern A: enums for closed alternatives.
```rust
enum AuthState { Anonymous, LoggedIn { user_id: u64 } }
```
- Pattern B: smart constructor + private newtype field.
```rust
pub struct Guess(i32);
impl Guess {
    pub fn new(v: i32) -> Self {
        assert!((1..=100).contains(&v));
        Self(v)
    }
}
```

## Tradeoffs

- Better safety and clearer intent at the cost of extra wrapper/constructor code.
- Aliases alone are insufficient for strong boundaries; prefer newtypes for true separation.

## When to use which feature

- Use enums for closed state spaces.
- Use newtypes for stronger boundaries around primitives.

## Source anchors

- `book/src/ch06-01-defining-an-enum.md`
- `book/src/ch09-03-to-panic-or-not-to-panic.md`
- `book/src/ch20-03-advanced-types.md`
