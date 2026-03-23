# Linear and Affine Types

> **Since:** Rust 1.0 (ownership, move semantics, `Copy` trait)

## What it is

Rust's ownership system is **affine typing** embedded in a practical systems language. Every value can be used **at most once** -- when you pass it to a function or assign it to another variable, the original binding is invalidated (moved). This is affine rather than strictly linear because values can be dropped without being used (the compiler inserts `drop` automatically).

The `Copy` trait opts a type out of move semantics: `Copy` types are implicitly duplicated on assignment, so the original remains valid. Types that manage resources (heap memory, file handles, sockets) are intentionally non-`Copy`, forcing the programmer to handle ownership explicitly.

This is Rust's signature feature reframed through type theory: what other languages achieve through garbage collection, reference counting, or manual memory management, Rust achieves through a substructural type system enforced entirely at compile time.

## What constraint it enforces

**Each non-`Copy` value has exactly one owner. Moving a value transfers ownership; the original binding becomes unusable. The compiler rejects any program that uses a value after it has been moved.**

- **At-most-once use (affine):** A value can be moved or dropped, but not used after being moved.
- **Deterministic destruction:** When the owner goes out of scope, `drop` runs exactly once.
- **No implicit aliasing:** Non-`Copy` types cannot be silently duplicated, preventing use-after-free and double-free at compile time.

## Minimal snippet

```rust
fn consume(s: String) {
    println!("consumed: {s}");
}   // s is dropped here

fn main() {
    let greeting = String::from("hello");
    consume(greeting);
    // println!("{greeting}");  // error[E0382]: borrow of moved value: `greeting`
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Ownership and moves** [-> catalog/T10](T10-ownership-moves.md) | Move semantics ARE affine typing in practice. T10 covers the mechanics; this entry provides the type-theoretic framing. |
| **Borrowing** [-> catalog/T11](T11-borrowing-mutability.md) | Borrowing (`&T`, `&mut T`) allows temporary access without consuming the value, extending affine types with controlled aliasing. |
| **Smart pointers** [-> catalog/T24](T24-smart-pointers.md) | `Rc<T>` and `Arc<T>` add reference counting, opting out of strict affine semantics for shared ownership. `Box<T>` preserves single-ownership affine behavior on the heap. |
| **PhantomData** [-> catalog/T27](T27-erased-phantom.md) | Phantom types combined with affine move semantics create single-use proof tokens -- consuming the token proves the action was performed exactly once. |
| **Send / Sync** [-> catalog/T50](T50-send-sync.md) | Affine ownership enables safe concurrency: moving a value to another thread transfers exclusive access, and `Send` marks which types can cross thread boundaries. |

## Gotchas and limitations

1. **Affine, not linear.** Rust allows dropping values without using them. True linear types would require every value to be consumed exactly once. Rust's `#[must_use]` attribute provides a lint-level approximation but does not enforce linear usage.

2. **`Copy` is all-or-nothing.** A type either implements `Copy` (no move, always copied) or does not (always moved). There is no partial copy or selective field movement. Deriving `Copy` requires all fields to be `Copy`.

3. **Implicit drops can surprise.** Reassigning a variable drops the old value silently: `let mut x = expensive(); x = cheap();` drops the first value. Use `std::mem::drop(x)` for explicit, self-documenting destruction.

4. **Closures and move semantics.** A `move` closure takes ownership of captured variables. Forgetting `move` on a closure passed to `thread::spawn` causes lifetime errors because the closure would borrow from the enclosing scope.

5. **No "use exactly once" enforcement.** The type system does not reject code that creates a value and immediately drops it. For must-use semantics, combine `#[must_use]` with API design that makes the value necessary for a subsequent operation.

6. **Destructuring partially moves.** Pattern-matching a struct can move some fields and borrow others. After a partial move, you can access the un-moved fields but not the struct as a whole. This is useful but the error messages can be confusing.

## Beginner mental model

Think of ownership as a **physical object** -- a book. You can hold a book (own it), hand it to someone (move it), or let someone look at it while you still hold it (borrow). Once you hand the book away, your hands are empty -- you cannot read it anymore. The `Copy` trait is like a photocopier: `i32` is so cheap to copy that handing it over actually gives a photocopy, keeping your original.

This is what type theorists call "affine typing": each resource is used at most once. Rust makes this practical for everyday programming.

## Example A -- Resource cleanup with affine ownership

```rust
use std::fs::File;
use std::io::Write;

fn write_and_close(mut file: File) {
    writeln!(file, "data").unwrap();
    // file is dropped here — OS handle closed automatically
}

fn main() {
    let f = File::create("/tmp/example.txt").unwrap();
    write_and_close(f);
    // f is moved — cannot use it here
    // writeln!(f, "more");  // error[E0382]: borrow of moved value
}
```

## Example B -- Single-use capability token

```rust
struct DeletePermission {
    _private: (),   // cannot be constructed outside this module
}

fn authorize(password: &str) -> Option<DeletePermission> {
    if password == "correct" {
        Some(DeletePermission { _private: () })
    } else {
        None
    }
}

fn delete_all(perm: DeletePermission) {
    // perm is consumed — cannot be reused
    drop(perm);   // explicit for clarity; happens at end of scope anyway
    println!("all records deleted");
}

fn main() {
    if let Some(perm) = authorize("correct") {
        delete_all(perm);
        // delete_all(perm);  // error[E0382]: use of moved value
    }
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Affine types make double-use and use-after-free unrepresentable at the type level.
- [-> UC-13](../usecases/UC13-state-machines.md) -- Move semantics enforce that each state transition consumes the current state, preventing illegal re-entry.
- [-> UC-20](../usecases/UC20-ownership-apis.md) -- APIs designed around ownership transfer use affine typing to express resource lifecycle contracts.

## Source anchors

- `book/src/ch04-01-what-is-ownership.md`
- `book/src/ch04-02-references-and-borrowing.md`
- `rust-reference/src/types/closure.md` -- move closures
- `nomicon/src/ownership.md`
- Walker, "Substructural Type Systems" (2005) -- theoretical foundation for affine/linear types
