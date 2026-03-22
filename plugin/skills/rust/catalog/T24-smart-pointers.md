# Smart Pointers and Interior Mutability

## What it is

Smart pointers in Rust are structs that implement the `Deref` and/or `Drop` traits, allowing them to behave like references while carrying additional semantics — heap allocation, reference counting, or runtime borrow checking. Unlike raw references (`&T`, `&mut T`), smart pointers *own* the data they point to, and their `Drop` implementation ensures deterministic cleanup when they go out of scope. The simplest smart pointer is `Box<T>`, which allocates a value on the heap with single ownership and zero-cost indirection (no metadata beyond the pointer itself).

When a single owner is not enough, Rust provides reference-counted pointers. `Rc<T>` enables *shared ownership* in single-threaded contexts: multiple `Rc` handles point to the same heap allocation, and the value is dropped only when the last handle is dropped. For multi-threaded programs, `Arc<T>` (atomic reference counting) provides the same semantics with thread-safe reference count updates. Both `Rc` and `Arc` give out only `&T` (shared references), so the data they wrap is immutable by default — which is where interior mutability enters the picture.

Interior mutability is a design pattern that lets you mutate data even when only a shared reference (`&T`) is available. This sidesteps the compile-time rule "either one `&mut T` or many `&T`" by moving the borrow check to runtime. `Cell<T>` provides interior mutability for `Copy` types with no runtime overhead beyond the operations themselves — you `get` and `set` the value, and no borrow is ever handed out. `RefCell<T>` works with any type by handing out dynamically-checked `Ref<T>` and `RefMut<T>` guards; violating the borrow rules at runtime causes a panic rather than a compile error. Two additional types round out the toolkit: `Weak<T>` creates non-owning handles to `Rc`/`Arc` data to break reference cycles, and `Cow<'a, T>` (clone-on-write) defers allocation decisions by borrowing when possible and cloning only when mutation is needed. Compared to C++ `shared_ptr` and `unique_ptr`, Rust's smart pointers integrate with the ownership and trait system so the compiler can still enforce safety guarantees at the boundaries where runtime checks are not used.

## What constraint it enforces

**Access, sharing, and mutation are constrained by pointer/wrapper semantics; interior mutability moves borrow checks from compile time to runtime, preserving memory safety at the cost of possible runtime panics.**

- **Single heap ownership (`Box<T>`).** The value is on the heap with exactly one owner. Moving the `Box` moves ownership; dropping the `Box` frees the allocation.
- **Shared ownership (`Rc<T>`, `Arc<T>`).** Multiple handles share one allocation. The data is immutable through the shared reference; mutation requires combining with an interior-mutability wrapper.
- **Runtime borrow rules (`RefCell<T>`).** At most one `RefMut` (mutable guard) *or* any number of `Ref` (immutable guards) may be alive at the same time. Violations panic at runtime.
- **Copy-only interior mutability (`Cell<T>`).** Values are copied in and out rather than borrowed, so no guards or runtime borrow tracking is needed — but the type must implement `Copy`.
- **Cycle prevention (`Weak<T>`).** Weak references do not increment the strong count and do not keep the value alive, breaking ownership cycles that would otherwise leak memory.

## Minimal snippet

```rust
use std::cell::RefCell;
use std::rc::Rc;

let shared = Rc::new(RefCell::new(vec![1, 2, 3]));
let handle = Rc::clone(&shared);          // second owner
handle.borrow_mut().push(4);              // mutate through shared reference
assert_eq!(*shared.borrow(), vec![1, 2, 3, 4]);
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Ownership / Moves** [-> catalog/01] | `Box<T>` preserves single-owner semantics on the heap. Moving a `Box` moves ownership; moving an `Rc` increments the reference count instead. |
| **Borrowing** [-> catalog/02] | `RefCell<T>` re-implements the `&T` / `&mut T` discipline at runtime. `Deref` on `Box` and `Rc` lets them be used wherever a reference is expected. |
| **Lifetimes** [-> catalog/03] | `Ref<'_, T>` and `RefMut<'_, T>` carry a lifetime tied to the `RefCell` borrow, ensuring guards do not outlive the cell. `Cow<'a, T>` carries an explicit lifetime for the borrowed variant. |
| **Traits and Generics** [-> catalog/05] | Smart pointers implement `Deref`, `Drop`, `Clone`, `AsRef`, and others, enabling generic code that works transparently with both references and pointers. |
| **Send and Sync** [-> catalog/11] | `Rc<T>` is `!Send` and `!Sync`. `Arc<T>` is `Send + Sync` when `T: Send + Sync`. `RefCell<T>` is `!Sync`. These bounds prevent accidental sharing across threads. |
| **Error Handling** [-> catalog/08] | `RefCell::try_borrow` and `try_borrow_mut` return `Result` instead of panicking, enabling graceful recovery from borrow conflicts. |

## Gotchas and limitations

1. **`RefCell` panics at runtime if borrow rules are violated.** Two live `borrow_mut()` calls, or a `borrow_mut()` while a `borrow()` is alive, cause an immediate panic. The compiler cannot catch this — you must reason about guard lifetimes yourself.

   ```rust
   let cell = RefCell::new(1);
   let a = cell.borrow_mut();
   let b = cell.borrow_mut(); // panic: already mutably borrowed
   ```

2. **`Rc` and `RefCell` are NOT thread-safe.** `Rc<T>` is `!Send` and `!Sync`; `RefCell<T>` is `!Sync`. For multi-threaded shared mutable state, use `Arc<Mutex<T>>` or `Arc<RwLock<T>>` instead.

3. **Reference cycles with `Rc<RefCell<T>>` cause memory leaks.** If two `Rc` values refer to each other, neither strong count ever reaches zero and the memory is never freed. Use `Weak<T>` to break at least one direction of the cycle.

4. **`Deref` coercion can be surprising.** `Box<String>` auto-derefs to `&String` and then to `&str`, so a `Box<String>` can be passed where `&str` is expected. This convenience can obscure ownership and allocation boundaries when reading code.

5. **`Cell` only works with `Copy` types.** `Cell::get` returns a copy of the inner value, so non-`Copy` types cannot use it. For non-`Copy` interior mutability, use `RefCell` (or `Cell::replace` / `Cell::take` for specific patterns).

6. **Interior mutability does not escape the borrow checker — it relocates it.** The safety guarantee still holds, but errors become runtime panics instead of compile-time rejections. This trades compile-time certainty for flexibility.

7. **`Rc<RefCell<T>>` can be a code smell.** Pervasive use often signals that ownership has not been designed clearly. Consider whether restructuring data ownership, using indices into a `Vec`, or using an arena allocator would be simpler.

8. **`Box<T>` requires heap allocation.** While `Box` is zero-cost for indirection (no metadata beyond the pointer), the allocation itself has a cost. For small, short-lived values, stack allocation is preferable.

## Beginner mental model

Think of `Box<T>` as putting a value in a labeled box on a shelf (the heap) — only one person holds the key. `Rc<T>` is like a library book: many readers can check it out simultaneously, and the library only discards it when the last reader returns their copy. Nobody can scribble in it, though, because everyone shares the same copy.

`RefCell<T>` is the "honor system" version of Rust's borrowing rules. Normally the compiler acts as a strict librarian who checks every borrow at the desk before you leave. With `RefCell`, the librarian steps away and trusts you to follow the rules — but if you break them (two people writing at once), an alarm goes off (a panic). `Cell<T>` is even simpler: you can only swap sticky notes (small `Copy` values) in and out of a slot, so there is no borrowing at all.

## Example A — `Box<T>` for heap allocation and recursive types

```rust
// Recursive types need indirection; `Box` provides heap allocation
// with single ownership.
enum List {
    Cons(i32, Box<List>),
    Nil,
}

fn main() {
    let list = List::Cons(1, Box::new(List::Cons(2, Box::new(List::Nil))));

    fn sum(l: &List) -> i32 {
        match l {
            List::Cons(val, next) => val + sum(next),
            List::Nil => 0,
        }
    }
    assert_eq!(sum(&list), 3);
}
```

## Example B — `Rc<T>` for shared ownership

```rust
use std::rc::Rc;

fn main() {
    let shared_name = Rc::new(String::from("Alice"));

    let greeting = Rc::clone(&shared_name);  // strong count: 2
    let farewell = Rc::clone(&shared_name);   // strong count: 3

    println!("Hello, {greeting}!");
    println!("Goodbye, {farewell}!");
    println!("Rc strong count: {}", Rc::strong_count(&shared_name)); // 3
}
// All three Rc handles are dropped; the String is freed once.
```

## Example C — `RefCell<T>` for interior mutability

```rust
use std::cell::RefCell;

struct Logger {
    messages: RefCell<Vec<String>>,
}

impl Logger {
    fn log(&self, msg: &str) {
        // `&self` is a shared reference, yet we can mutate `messages`
        self.messages.borrow_mut().push(msg.to_string());
    }
    fn dump(&self) {
        for m in self.messages.borrow().iter() {
            println!("{m}");
        }
    }
}

fn main() {
    let logger = Logger { messages: RefCell::new(Vec::new()) };
    logger.log("started");
    logger.log("finished");
    logger.dump();
}
```

## Example D — `Rc<RefCell<T>>` for shared mutable state

```rust
use std::cell::RefCell;
use std::rc::Rc;

fn main() {
    let data = Rc::new(RefCell::new(vec![1]));

    let writer = Rc::clone(&data);
    let reader = Rc::clone(&data);

    writer.borrow_mut().push(2);
    writer.borrow_mut().push(3);

    assert_eq!(*reader.borrow(), vec![1, 2, 3]);
}
```

## Example E — `Weak<T>` for breaking reference cycles

```rust
use std::cell::RefCell;
use std::rc::{Rc, Weak};

struct Node {
    value: i32,
    parent: RefCell<Weak<Node>>,
    children: RefCell<Vec<Rc<Node>>>,
}

fn main() {
    let leaf = Rc::new(Node {
        value: 3,
        parent: RefCell::new(Weak::new()),
        children: RefCell::new(vec![]),
    });

    let branch = Rc::new(Node {
        value: 5,
        parent: RefCell::new(Weak::new()),
        children: RefCell::new(vec![Rc::clone(&leaf)]),
    });

    // Parent is a Weak reference — no ownership cycle
    *leaf.parent.borrow_mut() = Rc::downgrade(&branch);

    // Upgrading a Weak returns Option<Rc<Node>>
    let parent = leaf.parent.borrow().upgrade().unwrap();
    assert_eq!(parent.value, 5);
}
```

## Example F — `Cell<T>` for simple interior mutability with Copy types

```rust
use std::cell::Cell;

struct Counter {
    count: Cell<u32>,
}

impl Counter {
    fn increment(&self) {
        // No borrow_mut needed — Cell copies the value in and out
        self.count.set(self.count.get() + 1);
    }
}

fn main() {
    let c = Counter { count: Cell::new(0) };
    c.increment();
    c.increment();
    assert_eq!(c.count.get(), 2);
}
```

## Common compiler errors and how to read them

### `error[E0499]: cannot borrow as mutable more than once at a time`

This compile-time error appears with regular `&mut` references, not `RefCell`. With `RefCell`, the same violation is a *runtime* panic.

```
error[E0499]: cannot borrow `data` as mutable more than once at a time
 --> src/main.rs:4:18
  |
3 |     let a = &mut data;
  |             --------- first mutable borrow occurs here
4 |     let b = &mut data;
  |                  ^^^^ second mutable borrow occurs here
5 |     println!("{a}");
  |               - first borrow later used here
```

**How to fix:** Limit the scope of the first mutable borrow so it is dropped before the second begins, or restructure to avoid needing two mutable references simultaneously.

### `error[E0277]: `Rc<T>` cannot be sent between threads safely`

`Rc<T>` does not implement `Send`. Attempting to move it into a thread triggers this error.

```
error[E0277]: `Rc<String>` cannot be sent between threads safely
 --> src/main.rs:5:18
  |
5 |     thread::spawn(move || {
  |                   ^^^^^^^ `Rc<String>` cannot be sent between threads safely
  |
  = help: the trait `Send` is not implemented for `Rc<String>`
```

**How to fix:** Replace `Rc<T>` with `Arc<T>` for thread-safe reference counting. If you also need mutation, pair it with `Mutex<T>` or `RwLock<T>` instead of `RefCell<T>`.

### `error[E0277]: `RefCell<T>` cannot be shared between threads safely`

`RefCell<T>` is `!Sync`, so it cannot be referenced from multiple threads even behind an `Arc`.

```
error[E0277]: `RefCell<Vec<i32>>` cannot be shared between threads safely
 --> src/main.rs:6:18
  |
6 |     thread::spawn(move || {
  |                   ^^^^^^^ `RefCell<Vec<i32>>` cannot be shared
  |                           between threads safely
  |
  = help: the trait `Sync` is not implemented for `RefCell<Vec<i32>>`
```

**How to fix:** Replace `Arc<RefCell<T>>` with `Arc<Mutex<T>>` or `Arc<RwLock<T>>` for thread-safe interior mutability.

### Runtime panic: `already mutably borrowed: BorrowError`

This is not a compile error — it is a runtime panic from `RefCell` when borrow rules are violated dynamically.

```
thread 'main' panicked at 'already mutably borrowed: BorrowError',
    src/main.rs:4:18
```

**How to fix:** Ensure that `RefMut` guards are dropped before taking another borrow. Use explicit blocks `{ ... }` to limit guard lifetimes, or use `try_borrow` / `try_borrow_mut` to handle conflicts gracefully with `Result`.

## Use-case cross-references

- [-> UC-02](../usecases/UC20-ownership-apis.md) — Designing APIs that use smart pointers to express ownership transfer, shared access, and interior mutability contracts.
- [-> UC-05](../usecases/UC21-concurrency.md) — Thread-safety constraints determine whether `Rc`/`RefCell` or `Arc`/`Mutex` is required.
- [-> UC-08](../usecases/UC18-type-arithmetic.md) — Smart pointer wrappers can enforce runtime invariants that complement compile-time type constraints.

## Source anchors

- `book/src/ch15-00-smart-pointers.md`
- `book/src/ch15-01-box.md`
- `book/src/ch15-04-rc.md`
- `book/src/ch15-05-interior-mutability.md`
- `book/src/ch15-06-reference-cycles.md`
- `rust-by-example/src/std/box.md`
- `rust-by-example/src/std/rc.md`
