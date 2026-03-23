# Immutability by Default and Mutability Markers

Since: Rust 1.0

## What it is

In Rust, **bindings are immutable by default**. `let x = 5;` creates a binding that cannot be reassigned. To permit mutation, you must explicitly opt in with `mut`: `let mut x = 5; x += 1;`. This extends to references: `&T` is a shared (immutable) reference, while `&mut T` is an exclusive (mutable) reference. The borrow checker enforces that at any given time, a value has either one `&mut T` or any number of `&T` references -- never both.

**`const`** defines compile-time constants (`const MAX: u32 = 100;`), which are inlined at every use site. **`static`** defines a value with a fixed memory address for the entire program lifetime.

**Interior mutability** provides a controlled escape hatch from the immutability default. `Cell<T>` allows mutation of `Copy` types through a shared reference. `RefCell<T>` allows borrowing the inner value mutably at runtime (panicking on violation). `Mutex<T>` and `RwLock<T>` provide thread-safe interior mutability. These types move the borrow check from compile time to runtime (or use atomic operations), trading static guarantees for flexibility.

The internal `Freeze` marker trait (not publicly usable) distinguishes types with no interior mutability, enabling certain compiler optimizations.

## What constraint it enforces

**Mutation is always explicit and visible. The compiler rejects mutation through immutable bindings or shared references, unless interior mutability is explicitly opted into.**

- `let x = 5; x = 6;` is a compile error. You must write `let mut x`.
- `&T` guarantees no mutation through that reference. Functions taking `&self` cannot modify the struct.
- Interior mutability types (`Cell`, `RefCell`) make the opt-in visible in the type signature.

## Minimal snippet

```rust
fn main() {
    let x = 5;
    // x += 1;           // error[E0384]: cannot assign twice to immutable variable

    let mut y = 5;
    y += 1;              // OK -- `mut` opted in
    println!("{y}");     // 6

    let s = String::from("hello");
    // s.push('!');      // error: cannot borrow `s` as mutable
    let mut s = s;       // re-bind as mutable
    s.push('!');
    println!("{s}");     // hello!
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Ownership** [-> catalog/T10](T10-ownership-moves.md) | Immutability is orthogonal to ownership. You can own an immutable value (cannot modify it) or a mutable value (can modify it). |
| **Borrowing** [-> catalog/T11](T11-borrowing-mutability.md) | `&T` vs `&mut T` is the reference-level expression of immutability. The borrow checker enforces exclusivity of `&mut T`. |
| **Callable typing** [-> catalog/T22](T22-callable-typing.md) | `FnMut` vs `Fn` mirrors `&mut` vs `&`. A closure capturing `&mut` state requires `FnMut`. |
| **Record types** [-> catalog/T31](T31-record-types.md) | Struct bindings are immutable by default. `mut` applies to the entire binding, not individual fields. |
| **Send / Sync** [-> catalog/T50](T50-send-sync.md) | `Cell<T>` is `!Sync` -- it cannot be shared across threads. `Mutex<T>` and `RwLock<T>` are `Sync`, providing thread-safe interior mutability. |

## Gotchas and limitations

1. **`mut` is per-binding, not per-field.** `let mut user = User { ... }` makes all fields mutable. You cannot make only some fields mutable on a given binding.

2. **Interior mutability is viral.** Once a struct contains a `Cell` or `RefCell`, it is no longer `Freeze`, and the compiler cannot assume shared references to it are immutable.

3. **`RefCell` panics at runtime.** Borrowing `RefCell` mutably while a shared borrow exists causes a panic, not a compile error. This is the trade-off for moving the borrow check to runtime.

4. **`const` is not the same as immutable `let`.** `const` items are compile-time constants inlined everywhere; `let` bindings are runtime values. `const` requires a value known at compile time.

5. **Shadowing is not mutation.** `let x = 5; let x = x + 1;` creates a new binding, not a mutation of the original. The types can even differ: `let x = "5"; let x: i32 = x.parse().unwrap();`.

## Beginner mental model

Think of `let` as writing in **permanent ink** -- once you write a value, it stays. `let mut` switches to **pencil**, allowing erasure and rewriting. Shared references (`&T`) are like giving someone a photocopy -- they can read but not change the original. Mutable references (`&mut T`) are like handing over the only pen -- one writer at a time. Interior mutability types (`Cell`, `RefCell`) are like a lockbox: the outside looks immutable, but if you have the right key (the `Cell`/`RefCell` API), you can change what is inside.

## Example A -- Interior mutability with Cell

```rust
use std::cell::Cell;

struct Counter {
    count: Cell<u32>,
}

impl Counter {
    fn new() -> Self { Counter { count: Cell::new(0) } }

    fn increment(&self) {  // note: &self, not &mut self
        self.count.set(self.count.get() + 1);
    }

    fn value(&self) -> u32 { self.count.get() }
}

fn main() {
    let c = Counter::new();  // no `mut` needed
    c.increment();
    c.increment();
    println!("count = {}", c.value());  // 2
}
```

## Example B -- RefCell for runtime borrow checking

```rust
use std::cell::RefCell;

fn main() {
    let data = RefCell::new(vec![1, 2, 3]);

    // Immutable borrow
    println!("len = {}", data.borrow().len());

    // Mutable borrow
    data.borrow_mut().push(4);
    println!("{:?}", data.borrow());  // [1, 2, 3, 4]

    // This would panic at runtime:
    // let _a = data.borrow();
    // let _b = data.borrow_mut();  // panic: already borrowed
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Immutable-by-default prevents accidental state changes that could create invalid states.
- [-> UC-21](../usecases/UC21-concurrency.md) -- `Mutex` and `RwLock` provide interior mutability that is safe across threads.
- [-> UC-20](../usecases/UC20-ownership-apis.md) -- The `&T` / `&mut T` distinction shapes API design around shared reads vs exclusive writes.

## Source anchors

- `book/src/ch03-01-variables-and-mutability.md`
- `book/src/ch15-05-interior-mutability.md`
- `rust-reference/src/interior-mutability.md`
- `std::cell` module documentation
