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

## Use-case cross-references

- `[-> UC-05]`

## Source anchors

- `book/src/ch16-03-shared-state.md`
- `book/src/ch16-04-extensible-concurrency-sync-and-send.md`
