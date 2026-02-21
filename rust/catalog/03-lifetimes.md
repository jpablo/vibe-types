# Lifetimes

## What it is

Lifetimes describe how long references are valid and let the compiler check reference relationships.

## What constraint it enforces

**A reference cannot outlive the data it points to.**

## Minimal snippet

```rust
fn pick<'a>(a: &'a str, _b: &'a str) -> &'a str {
    a
}
```

## Interaction with other features

- Builds on borrowing rules in `[-> catalog/02]`.
- Used in generic APIs from `[-> catalog/05]`.
- Central to `[-> UC-02]`.

## Gotchas and limitations

- Lifetime elision hides details that matter in edge cases.

## Use-case cross-references

- `[-> UC-02]`
