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

### Beginner mental model

Smart pointers wrap ownership rules: `Rc` copies shared handles without copying data, `RefCell` checks borrow rules at runtime, and `Box` simply stores a value on the heap. Interior mutability lets you change data through `&` by moving the checks to runtime.

### Example A

```rust
use std::rc::Rc;
use std::cell::RefCell;

let shared = Rc::new(RefCell::new(5));
{
    let mut value = shared.borrow_mut();
    *value += 1;
}
println!("value: {}", *shared.borrow());
```

### Example B

```rust
use std::cell::RefCell;

fn append(cell: &RefCell<Vec<i32>>, item: i32) {
    cell.borrow_mut().push(item);
}

let list = RefCell::new(vec![1]);
append(&list, 2);
```

### Common compiler errors and how to read them

- `error[E0499]: cannot borrow `...` as mutable more than once at a time` means you have overlapping `borrow_mut()` live at the same time; limit the scope of each mutable borrow or drop it before taking another.
- `error[E0502]: cannot borrow `...` as immutable because it is also borrowed as mutable` occurs when a mutable borrow is still alive while you try to create an immutable borrow; end the mutable borrow first (often by limiting its scope).

## Use-case cross-references

- `[-> UC-02]`
- `[-> UC-05]`

## Source anchors

- `book/src/ch15-00-smart-pointers.md`
- `book/src/ch15-04-rc.md`
- `book/src/ch15-05-interior-mutability.md`
- `book/src/ch15-06-reference-cycles.md`
