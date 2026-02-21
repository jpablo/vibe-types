# Ownership and Move Semantics

## What it is

Rust assigns each value a single owner, and moves transfer ownership between bindings.

## What constraint it enforces

**A value cannot be used after ownership has been moved, and cleanup runs when the current owner goes out of scope.**

## Minimal snippet

```rust
let s = String::from("x");
let t = s;
// println!("{}", s); // error: use of moved value
println!("{}", t); // OK
```

## Interaction with other features

- Works with borrowing rules in `[-> catalog/02]`.
- Shapes API design in `[-> UC-02]`.

## Gotchas and limitations

- `Copy` types do not move on assignment, so examples with integers can hide ownership transfer behavior.
- Partial moves can leave a parent value unusable when non-`Copy` fields are moved out.

## Use-case cross-references

- `[-> UC-02]`

## Source anchors

- `book/src/ch04-01-what-is-ownership.md`
- `rust-by-example/src/scope/move.md`
- `rust-by-example/src/scope/move/partial_move.md`
