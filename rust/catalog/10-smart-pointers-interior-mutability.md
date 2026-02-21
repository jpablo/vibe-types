# Smart Pointers and Interior Mutability

## What it is

Smart pointer types encode ownership, sharing, and mutation policies in their APIs.

## What constraint it enforces

**Access, sharing, and mutation are constrained by pointer/wrapper semantics, with some checks moved to runtime for interior mutability.**

## Minimal snippet

```rust
use std::cell::RefCell;

let x = RefCell::new(1);
*x.borrow_mut() = 2; // OK
```

## Interaction with other features

- Depends on ownership and borrowing in `[-> catalog/01]` and `[-> catalog/02]`.
- Often appears in `[-> UC-02]` and `[-> UC-05]`.

## Gotchas and limitations

- `RefCell<T>` enforces borrow rules at runtime and can panic when rules are violated.
- `Rc<T>` and `RefCell<T>` are single-threaded tools and do not satisfy thread-safety marker traits.

## Use-case cross-references

- `[-> UC-02]`
- `[-> UC-05]`

## Source anchors

- `book/src/ch15-00-smart-pointers.md`
- `book/src/ch15-04-rc.md`
- `book/src/ch15-05-interior-mutability.md`
- `book/src/ch15-06-reference-cycles.md`
