# Compile-Time Concurrency Constraints

## The constraint

Threaded code should only compile when transfer and sharing are safe.

## Feature toolkit

- `[-> T50](T50-send-sync.md)`
- `[-> T05](T05-type-classes.md)`
- `[-> T24](T24-smart-pointers.md)`

## Patterns

- Pattern A: `Send`-bounded worker API.
```rust
fn run_in_thread<T: Send + 'static>(value: T) {
    std::thread::spawn(move || drop(value));
}
```
- Pattern B: shared ownership with synchronization wrappers.
```rust
use std::sync::{Arc, Mutex};
let n = Arc::new(Mutex::new(0));
```

## Tradeoffs

- Safety constraints may require additional wrapper types.
- Some ownership patterns that work single-threaded (`Rc`, `RefCell`) fail for multithreading.

## When to use which feature

- Use `Send`/`Sync` bounds at API boundaries.
- Choose pointer/wrapper types based on sharing semantics.

## Source anchors

- `book/src/ch16-03-shared-state.md`
- `book/src/ch16-04-extensible-concurrency-sync-and-send.md`
- `book/src/ch15-04-rc.md`
- `book/src/ch15-05-interior-mutability.md`
