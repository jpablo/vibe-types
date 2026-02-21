# Lifetimes

## What it is

Lifetimes describe how long references are valid and let the compiler check reference relationships.

## What constraint it enforces

**References cannot outlive the data they point to, and returned borrows must be tied to valid input lifetimes.**

## Minimal snippet

```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() >= y.len() { x } else { y }
}
```

## Interaction with other features

- Builds on borrowing rules in `[-> catalog/02]`.
- Used in generic APIs from `[-> catalog/05]`.
- Central to `[-> UC-02]`.

## Gotchas and limitations

- Returning references to local values is rejected because locals are dropped at function end.
- Lifetime elision helps common cases but hides relationships that must be explicit in multi-reference APIs.

## Use-case cross-references

- `[-> UC-02]`

## Source anchors

- `book/src/ch10-03-lifetime-syntax.md`
- `rust-by-example/src/scope/lifetime.md`
