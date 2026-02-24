# Send and Sync

## What it is

`Send` and `Sync` are marker traits that express thread-transfer and shared-reference safety.

## What constraint it enforces

**Types that do not satisfy `Send`/`Sync` cannot be moved/shared across thread boundaries in disallowed ways.**

## Minimal snippet

```rust
use std::sync::{Arc, Mutex};
use std::thread;

let data = Arc::new(Mutex::new(0));
let d2 = Arc::clone(&data);
thread::spawn(move || {
    *d2.lock().unwrap() += 1;
});
```

## Interaction with other features

- Built on trait system in `[-> catalog/06]`.
- Common with smart pointers in `[-> catalog/10]`.
- Central to `[-> UC-05]`.

## Gotchas and limitations

- `Rc<T>` and `RefCell<T>` are not `Send`/`Sync`, so they fail in multithreaded sharing patterns.
- Manual `Send`/`Sync` impls require `unsafe` and careful invariants.

### Beginner mental model

`Send` is the compiler double-checking that ownership can hop onto another thread, `Sync` ensures shared references stay safe when multiple threads peek at the same data. Imagine `Send` as a train ticket (transfer ownership) and `Sync` as a shared reading room (multiple `&T` sit together without conflict).

### Example A

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let counter = Arc::new(Mutex::new(0));
    let handle = thread::spawn({
        let c = Arc::clone(&counter);
        move || {
            *c.lock().unwrap() += 1; // Arc<Mutex<>> is both Send and Sync, so the lock can be shared safely.
        }
    });

    handle.join().unwrap();
    println!("counter = {}", *counter.lock().unwrap());
}
```

### Example B

```rust,compile_fail
fn main() {
    let shared = std::rc::Rc::new(0);
    std::thread::spawn(move || {
        drop(shared); // error: `Rc<i32>` is not Send, so it cannot live on another thread.
    });
}
```

### Common compiler errors and how to read them

- `the trait Send is not implemented for Rc<i32>` – look for the type that lacks `Send` and find a `Send`-safe wrapper (`Arc`) or keep it on one thread.
- `the trait Sync is not implemented for MyType` – the issue is with shared `&MyType`; either avoid sharing mutable state or add `Mutex`/`RwLock` depending on interior mutability assurances.
- `method requires ... Send` vs `method requires ... Sync` – match the bound (`thread::spawn` needs `Send`, concurrent shared state often requires `Sync` through `&T` references).

## Use-case cross-references

- `[-> UC-05]`

## Source anchors

- `book/src/ch16-03-shared-state.md`
- `book/src/ch16-04-extensible-concurrency-sync-and-send.md`
