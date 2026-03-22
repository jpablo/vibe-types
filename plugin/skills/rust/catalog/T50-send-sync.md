# Send and Sync

## What it is

`Send` and `Sync` are *auto traits* (also called marker traits) in the Rust standard library. They carry no methods and add no runtime cost; they exist purely as compile-time flags that tell the type system whether a value can safely cross a thread boundary. `Send` means "ownership of this value can be transferred to another thread," while `Sync` means "a shared reference `&T` to this value can be accessed from another thread." The formal equivalence is: `T: Sync` if and only if `&T: Send`.

Because they are auto traits, the compiler derives them automatically. If every field of a struct is `Send`, the struct itself is `Send`; likewise for `Sync`. You never need to write `impl Send for MyStruct` unless you are wrapping a type that the compiler cannot prove safe on its own (most commonly raw pointers from FFI). This opt-in/opt-out design means the vast majority of user-defined types are `Send + Sync` without any annotation at all.

Most standard-library types are both `Send` and `Sync`. The notable exceptions form a short list that is worth memorizing: `Rc<T>` is neither `Send` nor `Sync` because its reference count is not atomic; `RefCell<T>` is `Send` but not `Sync` because its borrow flag is not thread-safe; raw pointers (`*const T`, `*mut T`) are neither `Send` nor `Sync` by default; and `Cell<T>` is `Send` but not `Sync` because interior mutation through `&Cell<T>` would be a data race. The thread-safe counterparts are `Arc<T>` (atomic reference counting), `Mutex<T>` and `RwLock<T>` (thread-safe interior mutability), which together give you the canonical shared-mutable-state pattern: `Arc<Mutex<T>>`.

This compile-time enforcement is what sets Rust apart from other systems languages. Java has no mechanism to prevent you from sharing a non-thread-safe object across threads; the `synchronized` keyword is a runtime tool you must remember to use. Go's concurrency model advises "don't communicate by sharing memory" but enforces nothing at compile time. C++ provides `std::mutex` but will happily let you forget to lock it. In Rust, `thread::spawn` requires the closure (and everything it captures) to be `Send + 'static`, so a non-`Send` type physically cannot reach another thread without an `unsafe` block. Data races on safe Rust code are not merely unlikely — they are impossible.

## What constraint it enforces

**A type that is not `Send` cannot have its ownership transferred to another thread, and a type that is not `Sync` cannot have its shared reference accessed from another thread.**

More specifically:

- **`Send` gates ownership transfer.** `std::thread::spawn` requires `F: Send + 'static`. If the closure captures a non-`Send` value, the program does not compile.
- **`Sync` gates shared-reference sharing.** Placing a value inside `Arc<T>` requires `T: Send + Sync` for the `Arc` itself to be `Send`. If `T` is not `Sync`, you cannot share `&T` across threads through an `Arc`.
- **Auto-derivation propagates.** The compiler checks every field: one non-`Send` field makes the whole struct non-`Send`. This is transitive — a `Vec<Rc<T>>` is not `Send` because `Rc<T>` is not `Send`.
- **`unsafe impl` is the escape hatch.** When wrapping FFI types or raw pointers that you know are thread-safe, you can write `unsafe impl Send for MyWrapper {}` — but the burden of proof is entirely on you.

## Minimal snippet

```rust
use std::thread;

let name = String::from("Alice");          // String is Send
thread::spawn(move || {                    // ownership of `name` moves to new thread
    println!("Hello from thread, {name}");
});
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Ownership** [-> catalog/01] | `Send` is fundamentally about transferring ownership to another thread. Move semantics guarantee the original thread no longer has access after the transfer. |
| **Borrowing** [-> catalog/02] | `Sync` is about sharing `&T` across threads. If `T: Sync`, multiple threads can hold `&T` simultaneously without data races. |
| **Lifetimes** [-> catalog/03] | `thread::spawn` requires `'static` in addition to `Send`, meaning captured data must be owned or have a `'static` lifetime. Scoped threads (`thread::scope`) relax this to allow borrowed data. |
| **Traits** [-> catalog/06] | `Send` and `Sync` are auto traits defined in `std::marker`. Negative implementations (`!Send`, `!Sync`) explicitly opt a type out. |
| **Smart Pointers** [-> catalog/10] | `Rc<T>` is the single-threaded pointer (not `Send`); `Arc<T>` is the thread-safe counterpart (`Send + Sync` when `T: Send + Sync`). `Mutex<T>` and `RwLock<T>` add `Sync` to interior-mutable types. |
| **Pattern Types** [-> catalog/09] | Newtype wrappers are the standard way to add `unsafe impl Send` to an FFI type while keeping the unsafe surface small. |

## Gotchas and limitations

1. **`Rc<T>` is not `Send`.** Its reference count uses non-atomic operations, so transferring an `Rc` to another thread would cause a data race on the count. Replace with `Arc<T>` for cross-thread sharing.

   ```rust
   // Will not compile:
   // let r = std::rc::Rc::new(42);
   // std::thread::spawn(move || println!("{r}"));
   ```

2. **`RefCell<T>` is not `Sync`.** Its runtime borrow tracking is not thread-safe; two threads calling `borrow_mut()` simultaneously would corrupt the borrow flag. Use `Mutex<T>` or `RwLock<T>` for thread-safe interior mutability.

3. **Raw pointers are neither `Send` nor `Sync`.** If you build a struct around `*mut T` for FFI, the compiler will not auto-derive either trait. You must write `unsafe impl Send for Wrapper {}` and verify the invariants yourself.

4. **`MutexGuard` is not `Send` but is `Sync`.** You cannot send a lock guard to another thread (the unlock must happen on the same thread that locked), but multiple threads can read through a shared reference to the guard if you arrange the lifetimes.

5. **`unsafe impl Send` is a safety contract.** Writing it for an FFI type is sometimes necessary, but you are personally guaranteeing the type's thread-safety invariants. Getting this wrong causes undefined behavior that the compiler cannot catch.

6. **Async runtimes add `Send` requirements.** In Tokio's multi-threaded runtime, futures must be `Send` to be scheduled across worker threads. Holding a non-`Send` type (like `Rc` or a `MutexGuard` from `RefCell`) across an `.await` point produces a compile error that can be confusing to diagnose.

7. **`Cell<T>` is `Send` but not `Sync`.** You can move a `Cell` to another thread (only one thread owns it), but you cannot share `&Cell<T>` across threads because `Cell::set` mutates through a shared reference, which would be a data race.

8. **Negative impls (`!Send`, `!Sync`) are unstable for user code.** The standard library uses them (e.g., `impl !Send for Rc<T> {}`), but on stable Rust you opt out by embedding a `PhantomData<*const ()>` field, which is neither `Send` nor `Sync`.

## Beginner mental model

Think of `Send` as a **shipping label**. If a type is `Send`, you can safely put it in a box and ship it to another thread. The receiving thread becomes the sole owner and the sending thread no longer has access. Most types are shippable: strings, vectors, integers, file handles. The few types that are not — like `Rc<T>` — are fragile packages that would break in transit because their internals assume single-threaded access.

`Sync` is a **reading-room pass**. If a type is `Sync`, multiple threads can sit down and read it at the same time through shared references (`&T`) without anyone seeing garbled data. Types like `Mutex<T>` earn their `Sync` status by providing internal locking. Types like `Cell<T>` lack `Sync` because they allow mutation through `&T`, which would let two threads write simultaneously. The mental shortcut: `Sync` answers "is it safe for two threads to look at this at the same time?"

## Example A — `thread::spawn` with a moved String (Send in action)

```rust
use std::thread;

fn main() {
    let message = String::from("hello from main");

    // String is Send, so ownership can transfer to the new thread.
    let handle = thread::spawn(move || {
        println!("{message}");
    });

    // `message` has been moved; it is no longer accessible here.
    handle.join().unwrap();
}
```

## Example B — `Arc<T>` for shared read-only data across threads

```rust
use std::sync::Arc;
use std::thread;

fn main() {
    let config = Arc::new(vec!["host=localhost", "port=8080"]);

    let mut handles = vec![];
    for i in 0..3 {
        let cfg = Arc::clone(&config); // cheap atomic increment
        handles.push(thread::spawn(move || {
            println!("Thread {i} reads config: {:?}", *cfg);
        }));
    }

    for h in handles {
        h.join().unwrap();
    }
    // `config` still accessible here — Arc keeps it alive until last clone drops.
}
```

## Example C — `Arc<Mutex<T>>` for shared mutable state

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];

    for _ in 0..5 {
        let c = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            let mut num = c.lock().unwrap();
            *num += 1;
        }));
    }

    for h in handles {
        h.join().unwrap();
    }

    println!("Final count: {}", *counter.lock().unwrap()); // 5
}
```

## Example D — `Rc<T>` failing to cross a thread boundary (compile error)

```rust,compile_fail
use std::rc::Rc;
use std::thread;

fn main() {
    let shared = Rc::new(42);
    // Rc<i32> is not Send — this will not compile.
    thread::spawn(move || {
        println!("{shared}");
    });
}
// error[E0277]: `Rc<i32>` cannot be sent between threads safely
```

## Example E — Why `Cell<T>` is Send but not Sync

```rust
use std::cell::Cell;
use std::thread;

fn main() {
    let cell = Cell::new(10);

    // Moving Cell to another thread is fine — Send is satisfied.
    thread::spawn(move || {
        cell.set(20); // sole owner, no data race
        println!("{}", cell.get());
    }).join().unwrap();

    // But sharing &Cell<T> across threads would NOT compile because Cell is not Sync:
    // let cell = Cell::new(10);
    // let r = &cell;
    // thread::spawn(move || println!("{}", r.get()));
    //   error: `Cell<i32>` cannot be shared between threads safely
}
```

## Example F — Scoped threads and relaxed lifetime requirements

```rust
fn main() {
    let mut data = vec![1, 2, 3];

    // `thread::scope` lets spawned threads borrow local variables
    // because the scope guarantees all threads join before it returns.
    thread::scope(|s| {
        s.spawn(|| {
            println!("scoped thread reads: {data:?}"); // borrows &data — no move needed
        });
    });
    // data is still accessible after the scope.
    data.push(4);
    println!("main continues: {data:?}");
}
```

Scoped threads require `T: Send` for moved values but relax the `'static` bound, allowing borrows of stack-local data as long as the borrow outlives the scope.

## Common compiler errors and how to read them

### `error[E0277]: <Type> cannot be sent between threads safely`

The most common Send/Sync error. You tried to move a non-`Send` type into a thread closure.

```
error[E0277]: `Rc<i32>` cannot be sent between threads safely
   --> src/main.rs:5:18
    |
5   |     thread::spawn(move || {
    |     ------------- ^------
    |     |             |
    |     |             `Rc<i32>` cannot be sent between threads safely
    |     required by a bound introduced by this call
    |
    = help: the trait `Send` is not implemented for `Rc<i32>`
```

**How to fix:** Replace `Rc<T>` with `Arc<T>`. For other non-`Send` types, check whether a thread-safe alternative exists or restructure the code to keep the value on one thread.

### `error[E0277]: <Type> cannot be shared between threads safely`

You tried to share `&T` across threads (typically via `Arc`) but `T` is not `Sync`.

```
error[E0277]: `RefCell<i32>` cannot be shared between threads safely
   --> src/main.rs:6:18
    |
6   |     thread::spawn(move || {
    |     ------------- required by a bound introduced by this call
    |
    = help: the trait `Sync` is not implemented for `RefCell<i32>`
    = note: if you want to do aliasing and mutation between multiple threads,
            use `std::sync::RwLock` instead
```

**How to fix:** Replace `RefCell<T>` with `Mutex<T>` or `RwLock<T>`. If you are using `Arc<RefCell<T>>`, switch to `Arc<Mutex<T>>`.

### `future cannot be sent between threads safely` (async contexts)

Tokio's multi-threaded runtime requires `Send` futures. Holding a non-`Send` type across `.await` triggers this error.

```
error: future cannot be sent between threads safely
   --> src/main.rs:8:5
    |
8   |     tokio::spawn(async move {
    |     ^^^^^^^^^^^^ future created by async block is not `Send`
    |
    = note: the type `Rc<String>` is not `Send`
```

**How to fix:** Replace `Rc` with `Arc`, or ensure the non-`Send` value is dropped before any `.await` point so it does not live across the suspend boundary.

### `error[E0277]: the trait bound 'Send' is not satisfied` on custom structs

Your struct contains a non-`Send` field, making the whole struct non-`Send`.

```
error[E0277]: `*mut u8` cannot be sent between threads safely
   --> src/main.rs:12:18
    |
12  |     thread::spawn(move || {
    |     ------------- required by a bound introduced by this call
    |
    = help: within `MyWrapper`, the trait `Send` is not implemented for `*mut u8`
```

**How to fix:** If you can guarantee thread safety, add `unsafe impl Send for MyWrapper {}`. Otherwise, restructure to avoid raw pointers or keep the type on a single thread.

## Use-case cross-references

- [-> UC-05](../usecases/UC21-concurrency.md) — Send and Sync are the foundation of compile-time concurrency safety, preventing data races at the type level.
- [-> UC-02](../usecases/UC20-ownership-apis.md) — API boundaries that accept `T: Send` communicate thread-transfer intent in the signature.

## Source anchors

- `book/src/ch16-01-threads.md`
- `book/src/ch16-03-shared-state.md`
- `book/src/ch16-04-extensible-concurrency-sync-and-send.md`
- `rust-by-example/src/std/arc.md`
- `std::marker::Send` and `std::marker::Sync` API documentation
