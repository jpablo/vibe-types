# Callable Contracts

## The constraint

Functions, closures, and function pointers are typed through the `Fn`, `FnMut`, and `FnOnce` trait hierarchy. The compiler enforces that callables are invoked with correct argument types and that their capture semantics (borrow, mutable borrow, or move) match the calling context.

## Feature toolkit

- `[-> T22](../catalog/T22-callable-typing.md)`
- `[-> T04](../catalog/T04-generics-bounds.md)`
- `[-> T36](../catalog/T36-trait-objects.md)`

## Patterns

- Pattern A: `Fn` trait bounds for reusable callbacks.
```rust
fn apply_twice<F: Fn(i32) -> i32>(f: F, x: i32) -> i32 {
    f(f(x))
}

let result = apply_twice(|n| n + 1, 10); // 12
```

- Pattern B: `FnMut` for closures that mutate captured state.
```rust
fn call_n_times<F: FnMut()>(mut f: F, n: usize) {
    for _ in 0..n {
        f();
    }
}

let mut count = 0;
call_n_times(|| count += 1, 5);
assert_eq!(count, 5);
```

- Pattern C: `FnOnce` for closures that consume captured values.
```rust
fn consume_and_run<F: FnOnce() -> String>(f: F) -> String {
    f() // f can only be called once — it may move captured values
}

let name = String::from("world");
let greeting = consume_and_run(move || format!("hello, {name}"));
// `name` is moved into the closure and consumed
```

- Pattern D: function pointers (`fn`) for stateless callbacks.
```rust
fn add_one(x: i32) -> i32 { x + 1 }

// fn pointers are a concrete type, not a trait
let f: fn(i32) -> i32 = add_one;
assert_eq!(f(10), 11);

// Useful in FFI or when no captured state is needed
fn apply(f: fn(i32) -> i32, x: i32) -> i32 { f(x) }
```

- Pattern E: `Box<dyn Fn>` for storing callbacks in structs.
```rust
struct EventHandler {
    on_click: Box<dyn Fn(i32, i32) + Send>,
}

impl EventHandler {
    fn click(&self, x: i32, y: i32) {
        (self.on_click)(x, y);
    }
}
```

## Tradeoffs

- `Fn` / `FnMut` / `FnOnce` bounds express capture semantics precisely but require understanding the hierarchy.
- Generic `impl Fn(...)` gives zero-cost static dispatch; `dyn Fn(...)` enables runtime flexibility at the cost of indirection.
- Function pointers (`fn(...)`) have no overhead and are FFI-compatible but cannot capture environment.

## When to use which feature

- Use `Fn` bounds when the callback is called multiple times and borrows its captures immutably.
- Use `FnMut` when the callback needs to mutate captured state.
- Use `FnOnce` when the callback is called at most once and may consume captures (e.g., thread spawn).
- Use `fn(...)` pointers for stateless callbacks or FFI boundaries.
- Use `Box<dyn Fn>` when callbacks must be stored in collections or structs.

## Source anchors

- `book/src/ch13-01-closures.md`
- `book/src/ch20-05-advanced-functions-and-closures.md`
- `rust-by-example/src/fn/closures.md`
- `rust-by-example/src/fn/closures/input_functions.md`
