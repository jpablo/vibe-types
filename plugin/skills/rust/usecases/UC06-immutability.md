# Immutability by Default

## The constraint

Bindings and references are immutable unless explicitly opted into mutation. The compiler enforces that only `mut` bindings can be reassigned, only `&mut` references can modify data, and `const` values are evaluated at compile time. Interior mutability (`Cell`, `RefCell`, `Mutex`) provides controlled escape hatches under strict rules.

## Feature toolkit

- `[-> T11](../catalog/T11-borrowing-mutability.md)`
- `[-> T32](../catalog/T32-immutability-markers.md)`
- `[-> T24](../catalog/T24-smart-pointers.md)`

## Patterns

- Pattern A: immutable by default — `mut` opt-in for bindings and references.
```rust
let x = 5;
// x = 6;          // error: cannot assign twice to immutable variable

let mut y = 5;
y = 6;             // OK — explicitly mutable

fn push_item(v: &mut Vec<i32>, item: i32) {
    v.push(item);  // OK — &mut reference
}
```

- Pattern B: `const` and `static` for compile-time constants.
```rust
const MAX_RETRIES: u32 = 3;
static APP_NAME: &str = "myapp";

// const values are inlined at every use site.
// static values have a single memory location.
```

- Pattern C: interior mutability with `Cell` and `RefCell` for single-threaded cases.
```rust
use std::cell::{Cell, RefCell};

struct Counter {
    count: Cell<u32>,          // mutation behind shared reference
    log: RefCell<Vec<String>>, // borrow-checked at runtime
}

impl Counter {
    fn increment(&self) {
        self.count.set(self.count.get() + 1);
        self.log.borrow_mut().push(format!("count={}", self.count.get()));
    }
}
```

- Pattern D: `Mutex` and `RwLock` for thread-safe interior mutability.
```rust
use std::sync::{Arc, Mutex};

let shared = Arc::new(Mutex::new(Vec::new()));
let handle = shared.clone();

std::thread::spawn(move || {
    handle.lock().unwrap().push(42); // safe mutation across threads
});
```

## Tradeoffs

- Immutable-by-default prevents accidental mutation but requires `mut` annotations throughout call chains.
- `Cell`/`RefCell` move borrow checks to runtime, trading compile-time guarantees for flexibility.
- `Mutex`/`RwLock` add synchronization overhead but are the only sound option for shared mutable state across threads.

## When to use which feature

- Default to immutable bindings and references everywhere.
- Use `mut` only when mutation is genuinely needed.
- Use `Cell` for simple `Copy` types that need interior mutability without borrowing.
- Use `RefCell` when you need interior mutability with complex borrows in single-threaded code.
- Use `Mutex`/`RwLock` for shared mutable state across threads.

## Source anchors

- `book/src/ch03-01-variables-and-mutability.md`
- `book/src/ch04-02-references-and-borrowing.md`
- `book/src/ch15-05-interior-mutability.md`
- `rust-by-example/src/scope/borrow/mut.md`
