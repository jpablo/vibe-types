# State Machines

## The constraint

State transitions must be enforced at compile time. An object in state A can only call methods valid for state A, and transitions produce a new type representing the target state. Invalid transitions do not compile.

## Feature toolkit

- `[-> T27](../catalog/T27-erased-phantom.md)` — PhantomData for zero-cost state tags
- `[-> T01](../catalog/T01-algebraic-data-types.md)` — enums for runtime state machines
- `[-> T21](../catalog/T21-encapsulation.md)` — private fields to prevent state forgery

## Patterns

- Pattern A: typestate pattern — each state is a distinct type.
```rust
use std::marker::PhantomData;

struct Draft;
struct Review;
struct Published;

struct Article<S> {
    title: String,
    body: String,
    _state: PhantomData<S>,
}

impl Article<Draft> {
    fn new(title: impl Into<String>) -> Self {
        Article { title: title.into(), body: String::new(), _state: PhantomData }
    }

    fn write(&mut self, text: &str) {
        self.body.push_str(text);
    }

    fn submit(self) -> Article<Review> {
        Article { title: self.title, body: self.body, _state: PhantomData }
    }
}

impl Article<Review> {
    fn approve(self) -> Article<Published> {
        Article { title: self.title, body: self.body, _state: PhantomData }
    }

    fn reject(self) -> Article<Draft> {
        Article { title: self.title, body: self.body, _state: PhantomData }
    }
}

impl Article<Published> {
    fn url(&self) -> String {
        format!("/articles/{}", self.title.to_lowercase().replace(' ', "-"))
    }
}

// let draft = Article::<Draft>::new("Rust Typestates");
// draft.url();           // error: no method `url` on Article<Draft>
// draft.approve();       // error: no method `approve` on Article<Draft>
// let review = draft.submit();
// let published = review.approve();
// println!("{}", published.url()); // OK
```

- Pattern B: enum-based state machine — runtime transitions with exhaustive matching.
```rust
enum DoorState { Open, Closed, Locked }

impl DoorState {
    fn transition(self, action: Action) -> Self {
        match (self, action) {
            (DoorState::Closed, Action::Open)   => DoorState::Open,
            (DoorState::Open,   Action::Close)  => DoorState::Closed,
            (DoorState::Closed, Action::Lock)   => DoorState::Locked,
            (DoorState::Locked, Action::Unlock) => DoorState::Closed,
            (state, _) => state, // no-op for invalid transitions
        }
    }
}

enum Action { Open, Close, Lock, Unlock }
```

- Pattern C: consuming `self` to prevent reuse of old states.
```rust
struct Connection<S> { _state: PhantomData<S> }
struct Disconnected;
struct Connected;

impl Connection<Disconnected> {
    fn connect(self) -> Connection<Connected> {
        Connection { _state: PhantomData }
    }
}

impl Connection<Connected> {
    fn send(&self, _data: &[u8]) { /* ... */ }
    fn disconnect(self) -> Connection<Disconnected> {
        Connection { _state: PhantomData }
    }
}

// let c = Connection::<Disconnected> { _state: PhantomData };
// c.send(&[1, 2]); // error: no method `send` on Connection<Disconnected>
// let c = c.connect();
// c.send(&[1, 2]); // OK
```

## Tradeoffs

| Approach | Strength | Weakness |
|----------|----------|----------|
| Typestate (PhantomData) | Invalid transitions are compile errors, zero runtime cost | One type per state — verbose with many states |
| Enum state machine | All states in one type, easy to serialize | Invalid transitions only caught at runtime |
| Consuming `self` | Prevents using an object after a transition | Cannot keep a reference to the old state |

## When to use which feature

- Use typestate when the number of states is small and transitions must be compiler-enforced (protocols, connection lifecycles).
- Use enum state machines when states are dynamic, serializable, or there are many states.
- Always consume `self` on transitions to prevent use-after-transition bugs.

## Source anchors

- `book/src/ch18-03-oo-design-patterns.md` — state pattern
- `rust-by-example/src/generics/phantom.md`
- `rust-reference/src/special-types-and-traits.md` — PhantomData
