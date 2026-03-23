# Callable Typing: Fn Traits and Function Pointers

Since: Rust 1.0

## What it is

Rust models callable values through a **trait hierarchy**: `FnOnce`, `FnMut`, and `Fn`. Every closure the compiler generates automatically implements one or more of these traits based on how it captures its environment:

- **`FnOnce`** -- can be called once; may consume (move) captured variables.
- **`FnMut`** -- can be called multiple times; may mutate captured variables.
- **`Fn`** -- can be called multiple times; only immutably borrows captured variables.

The hierarchy is: `Fn: FnMut: FnOnce`. Any `Fn` closure also satisfies `FnMut` and `FnOnce`.

**Function pointers** `fn(A) -> B` are a separate, simpler type: they point to a named function or a non-capturing closure. Unlike `Fn` traits, function pointers are concrete types with a known size, so they can be stored in structs without boxing.

Higher-order functions accept callables via generic bounds: `fn apply<F: Fn(i32) -> i32>(f: F, x: i32) -> i32`. This enables zero-cost abstractions where the compiler monomorphizes each call site.

## What constraint it enforces

**The compiler tracks how a closure captures its environment and prevents calling it in ways that violate ownership or borrowing rules.**

- A closure that moves out of a captured variable can only be called once (`FnOnce`). Calling it again would use-after-move.
- A closure that mutates a captured variable requires exclusive access (`FnMut`). It cannot be shared across threads without synchronization.
- Generic bounds on `Fn`/`FnMut`/`FnOnce` make callback contracts explicit in function signatures.

## Minimal snippet

```rust
fn apply<F: Fn(i32) -> i32>(f: F, x: i32) -> i32 {
    f(x)
}

fn main() {
    let double = |x| x * 2;       // implements Fn(i32) -> i32
    println!("{}", apply(double, 5));  // 10

    let add: fn(i32, i32) -> i32 = |a, b| a + b;  // function pointer
    println!("{}", add(3, 4));                       // 7
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Traits** [-> catalog/T05](T05-type-classes.md) | `Fn`, `FnMut`, `FnOnce` are traits. Generic bounds and trait objects (`dyn Fn(...)`) work the same as for any other trait. |
| **Generics** [-> catalog/T04](T04-generics-bounds.md) | `fn map<F: FnMut(A) -> B>(f: F)` constrains the callable at compile time. Monomorphization inlines the closure for zero overhead. |
| **Trait objects** [-> catalog/T36](T36-trait-objects.md) | `Box<dyn Fn(i32) -> i32>` enables dynamic dispatch for callbacks. Required when the concrete closure type is not known at compile time. |
| **Ownership** [-> catalog/T10](T10-ownership-moves.md) | Closures capturing by move (`move \|\| { ... }`) take ownership of variables. This is essential for `spawn` and `async` blocks. |
| **Immutability** [-> catalog/T32](T32-immutability-markers.md) | `Fn` requires only shared borrows of captures; `FnMut` requires exclusive borrows. The hierarchy mirrors Rust's borrow semantics. |

## Gotchas and limitations

1. **Each closure has a unique, unnameable type.** Two closures with identical signatures have different types. You cannot declare a variable `let f: ??? = if cond { closure_a } else { closure_b }` without boxing (`Box<dyn Fn(...)>`).

2. **`FnOnce` closures cannot be called through `&self`.** If you accept `F: FnOnce()`, you must own the closure to call it. `&dyn FnOnce()` is not callable because calling would consume the value behind the reference.

3. **`move` keyword does not mean `FnOnce`.** A `move` closure takes ownership of captured variables, but if none of them are consumed by the closure body, it can still implement `Fn`. `move` controls *how* variables are captured, not *how many times* the closure can be called.

4. **Function pointers have no captures.** A `fn(A) -> B` cannot close over any state. Use a generic `F: Fn(A) -> B` or `Box<dyn Fn(A) -> B>` when captures are needed.

5. **Returning closures requires `impl Fn(...)` or boxing.** `fn make_adder(n: i32) -> impl Fn(i32) -> i32 { move |x| x + n }` works for a single return type. If multiple closure types may be returned, use `Box<dyn Fn(...)>`.

## Beginner mental model

Think of the three traits as **permission levels for a borrowed tool**. `FnOnce` is a single-use tool -- you can use it once and it is consumed. `FnMut` is a tool you can reuse but you need exclusive access (no one else can use it simultaneously). `Fn` is a shared tool -- anyone can use it at the same time. Every closure gets the most permissive level its captures allow.

## Example A -- FnMut closure that accumulates state

```rust
fn accumulate<F: FnMut(i32)>(values: &[i32], mut f: F) {
    for &v in values {
        f(v);
    }
}

fn main() {
    let mut sum = 0;
    accumulate(&[1, 2, 3, 4], |x| sum += x);
    println!("sum = {sum}");  // 10
}
```

## Example B -- Returning a closure with impl Fn

```rust
fn make_greeter(greeting: String) -> impl Fn(&str) -> String {
    move |name| format!("{greeting}, {name}!")
}

fn main() {
    let hello = make_greeter("Hello".into());
    let hola  = make_greeter("Hola".into());
    println!("{}", hello("Alice"));  // Hello, Alice!
    println!("{}", hola("Bob"));     // Hola, Bob!
}
```

## Use-case cross-references

- [-> UC-04](../usecases/UC04-generic-constraints.md) -- `Fn` trait bounds constrain higher-order function parameters with full compile-time checking.
- [-> UC-14](../usecases/UC14-extensibility.md) -- Callback-based APIs use `Fn` traits to let callers inject behavior without subclassing.
- [-> UC-20](../usecases/UC20-ownership-apis.md) -- `FnOnce` captures encode ownership transfer into callback contracts.

## Source anchors

- `book/src/ch13-01-closures.md`
- `rust-reference/src/types/closure.md`
- `rust-reference/src/types/function-pointer.md`
- `std::ops::Fn`, `std::ops::FnMut`, `std::ops::FnOnce` documentation
