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

### Beginner mental model

Ownership is like holding a baton—only one variable can grip it at a time, and whoever holds it must pass it along or drop it explicitly when done.

### Example A (code)

```rust
fn greet(name: String) {
    println!("Hello, {name}!");
}

let name = String::from("Taylor");
greet(name);
// println!("{name}"); // error: use of moved value `name`
```

### Example B (code)

```rust
let greeting = String::from("hi");
let copy = greeting.clone(); // duplicates the data so `greeting` stays valid
println!("{} {}", greeting, copy);
```

### Common compiler errors and how to read them

- `error[E0382]: use of moved value` identifies the exact binding (`name`) that lost ownership and usually includes another note like `value moved here` to show the original owner and line. Follow the note back to find which move invalidated the value.
- `error[E0507]: cannot move out of borrowed content` occurs when you try to move from a reference; the compiler points to the borrow site so you can switch to cloning or borrowing mutably instead.

## Use-case cross-references

- `[-> UC-02]`

## Source anchors

- `book/src/ch04-01-what-is-ownership.md`
- `rust-by-example/src/scope/move.md`
- `rust-by-example/src/scope/move/partial_move.md`
