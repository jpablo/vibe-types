# Ownership and Move Semantics

## What it is

Rust assigns each value a single owner, and moves transfer ownership between bindings.

## What constraint it enforces

**A value cannot be used after ownership has been moved.**

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

- Move semantics differ from copy semantics for `Copy` types.

## Use-case cross-references

- `[-> UC-02]`
