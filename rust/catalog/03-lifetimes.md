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

### Beginner mental model

Lifetimes are the story of who outlives whom—each reference promises to stay valid for a stretch that the compiler can verify before it lets you use the data.

### Example A (code)

```rust
fn pick_first<'a>(a: &'a str, b: &str) -> &'a str {
    a
}

let s1 = String::from("apple");
let result = pick_first(&s1, "banana");
assert_eq!(result, "apple");
```

### Example B (code)

```rust
struct Borrowed<'a> {
    text: &'a str,
}

let name = String::from("Sky");
let holder = Borrowed { text: &name };
println!("holder sees {}", holder.text);
```

### Common compiler errors and how to read them

- `error[E0515]: cannot return reference to local variable` tracks the short-lived binding (often `a` or `x`) and shows it is dropped at the end of the function, so you need to tie the return reference to an input lifetime instead.
- `error[E0597]: `x` does not live long enough` points to both the use site and the borrow whose scope ended earlier; extend the lifetime of the owner or move the data to avoid the early drop.

## Use-case cross-references

- `[-> UC-02]`

## Source anchors

- `book/src/ch10-03-lifetime-syntax.md`
- `rust-by-example/src/scope/lifetime.md`
