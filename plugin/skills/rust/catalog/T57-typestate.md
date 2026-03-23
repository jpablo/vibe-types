# Typestate

> **Since:** Rust 1.0 (PhantomData since 1.0); stable

## What it is

Typestate is a design pattern where **a type's state is encoded as a type parameter**, and methods are only available in the correct state. In Rust, this is implemented using **`PhantomData<State>`** as a zero-sized field, combined with **private constructors** that ensure state transitions can only happen through designated methods. The compiler enforces that operations are called in the correct order, and the ownership system guarantees that stale references to previous states cannot be used.

This is the **canonical Rust pattern** for protocol enforcement and is widely used in the ecosystem. Examples include `hyper::http::request::Builder` (must set method before building), `tokio::net::TcpStream` (must connect before reading), and embedded HAL GPIO pin states (`Input`, `Output`, `Alternate`). The pattern is zero-cost: `PhantomData` has no runtime representation, so a `Connection<Connected>` and `Connection<Disconnected>` have identical memory layouts.

## What constraint it enforces

**Methods are only callable when the type parameter matches the required state. State transitions consume the old value and return a new value with the new state type. Rust's ownership system prevents use-after-transition — once you transition from `Door<Closed>` to `Door<Open>`, the `Door<Closed>` value is moved and cannot be used again.**

## Minimal snippet

```rust
use std::marker::PhantomData;

struct Closed;
struct Open;

struct Door<S> {
    _state: PhantomData<S>,
}

impl Door<Closed> {
    fn new() -> Self {
        Door { _state: PhantomData }
    }

    fn open(self) -> Door<Open> {
        println!("Opening door");
        Door { _state: PhantomData }
    }
}

impl Door<Open> {
    fn enter(&self) {
        println!("Entering!");
    }

    fn close(self) -> Door<Closed> {
        println!("Closing door");
        Door { _state: PhantomData }
    }
}

fn main() {
    let door = Door::new();       // Door<Closed>
    // door.enter();              // error: no method `enter` for Door<Closed>
    let door = door.open();       // Door<Open> — old Door<Closed> is moved
    door.enter();                 // OK
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Ownership and moves** [-> T10](T10-ownership-moves.md) | State transitions consume `self` by value, ensuring the old state cannot be reused. This is what makes Rust's typestate strictly safer than in languages without linear types. |
| **PhantomData** | `PhantomData<S>` is a zero-sized type that tells the compiler "this type logically contains an `S`" without actually storing one. It enables variance and drop-check interactions. |
| **Generics and bounds** [-> T04](T04-generics-bounds.md) | `impl Door<Closed>` is a specialized `impl` block — methods only exist for that specific state. This is more ergonomic than trait-bound dispatch for typestate. |
| **Traits** [-> T05](T05-type-classes.md) | Traits can be implemented only for specific states: `impl Display for Connection<Connected>`. Shared behavior across states uses a generic `impl<S> Connection<S>`. |
| **Sealed traits / private constructors** | State types are typically defined as empty structs in the same module with no public constructors. External code cannot forge a state token. |

## Gotchas and limitations

1. **Ownership is required for safety.** Typestate only works correctly when transitions consume `self`. If you use `&self` or `&mut self`, the old reference survives the transition. Always take `self` by value for state transitions.

2. **Cannot store typestate objects in homogeneous collections.** `Vec<Door<Open>>` and `Vec<Door<Closed>>` are different types. To store doors in mixed states, you need an enum wrapper or a trait object.

3. **Combinatorial state explosion.** Multiple independent state dimensions (e.g., `Connection<Auth, Encrypted, Pooled>`) require multiple phantom parameters. Consider using a single enum-like phantom type or a builder struct per dimension.

4. **PhantomData and auto traits.** `PhantomData<S>` affects whether the struct implements `Send` and `Sync` based on `S`. Use `PhantomData<fn() -> S>` if the phantom parameter should not affect auto traits.

5. **No runtime state inspection.** The state is purely type-level. If you need runtime state queries, use an enum instead of typestate.

## Beginner mental model

Think of typestate as a **key-card system**. A `Door<Closed>` is a key card that only works at the "open" terminal. When you swipe it (`open(self)`), the terminal takes your old card (ownership moves) and hands you a new `Door<Open>` card that works at the "enter" and "close" terminals. You cannot use the old card again — it has been consumed. The compiler is the security system: it checks which card you are holding and only lets you access the terminals your card type permits.

## Example A -- Builder pattern with required fields

```rust
use std::marker::PhantomData;

struct NoUrl; struct HasUrl;
struct NoMethod; struct HasMethod;

struct RequestBuilder<U, M> { url: String, method: String, _u: PhantomData<U>, _m: PhantomData<M> }

impl RequestBuilder<NoUrl, NoMethod> {
    fn new() -> Self { RequestBuilder { url: String::new(), method: String::new(), _u: PhantomData, _m: PhantomData } }
}
impl<M> RequestBuilder<NoUrl, M> {
    fn url(self, url: &str) -> RequestBuilder<HasUrl, M> {
        RequestBuilder { url: url.into(), method: self.method, _u: PhantomData, _m: PhantomData }
    }
}
impl<U> RequestBuilder<U, NoMethod> {
    fn method(self, m: &str) -> RequestBuilder<U, HasMethod> {
        RequestBuilder { url: self.url, method: m.into(), _u: PhantomData, _m: PhantomData }
    }
}
impl RequestBuilder<HasUrl, HasMethod> {
    fn build(self) -> String { format!("{} {}", self.method, self.url) }
}

fn main() {
    let req = RequestBuilder::new().url("https://example.com").method("GET").build();
    // RequestBuilder::new().url("...").build();  // error: no method `build`
    println!("{req}");  // "GET https://example.com"
}
```

## Example B -- Embedded GPIO pin states

```rust
use std::marker::PhantomData;

struct Input; struct Output;
struct Pin<MODE> { pin_number: u8, _mode: PhantomData<MODE> }

impl Pin<Input> {
    fn read(&self) -> bool { true }
    fn into_output(self) -> Pin<Output> { Pin { pin_number: self.pin_number, _mode: PhantomData } }
}
impl Pin<Output> {
    fn write(&mut self, value: bool) { println!("pin {} = {}", self.pin_number, value); }
    fn into_input(self) -> Pin<Input> { Pin { pin_number: self.pin_number, _mode: PhantomData } }
}

fn main() {
    let input_pin = Pin::<Input> { pin_number: 13, _mode: PhantomData };
    let _val = input_pin.read();
    // input_pin.write(true);  // error: no method `write` for Pin<Input>
    let mut output_pin = input_pin.into_output();
    output_pin.write(true);     // OK
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Typestate makes invalid state transitions a compile-time error, not a runtime panic.
- [-> UC-08](../usecases/UC08-error-handling.md) -- Protocol violations are caught at compile time instead of producing runtime errors.
- [-> UC-13](../usecases/UC13-state-machines.md) -- Typestate is the canonical encoding of state machines in Rust's type system.
- [-> UC-20](../usecases/UC20-ownership-apis.md) -- Ownership-based state transitions ensure resources are used exactly once per state.

## Source anchors

- `book/src/ch19-04-advanced-types.md` (PhantomData, zero-sized types)
- [Rust Design Patterns — Typestate](https://rust-unofficial.github.io/patterns/patterns/behavioural/typestate.html)
- [Embedded Rust Book — GPIO typestate](https://docs.rust-embedded.org/book/static-guarantees/typestate-programming.html)
- `std::marker::PhantomData` documentation
