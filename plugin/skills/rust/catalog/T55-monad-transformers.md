# Monad Transformers (via Middleware and Layered Architecture)

> **Since:** tower 0.3+ (Layer/Service pattern); stable Rust

## What it is

Rust has no monad transformer types, but the same compositional pattern — layering cross-cutting concerns around a core computation — appears throughout the ecosystem as **middleware** and **service layers**. The canonical example is the **tower** crate's `Service` trait and `Layer` abstraction: a `Service` processes requests and produces responses (potentially async and fallible), and a `Layer` wraps a `Service` to add behavior (timeouts, retries, logging, authentication) without modifying the inner service.

This is structurally analogous to monad transformers: each `Layer` adds an "effect" (timeout = error, retry = state, logging = writer) to the service stack, and the types compose. The difference is that Rust's approach is object-oriented (trait objects or generics over `Service`) rather than monadic, and the composition is explicit rather than automatic.

Beyond tower, the same pattern appears in HTTP frameworks (axum middleware, actix-web middleware), async runtimes, and even synchronous pipelines (iterator adaptors wrapping inner iterators).

## What constraint it enforces

**Each middleware layer enforces its contract at the type level: a timeout layer requires the inner service to be async, a retry layer requires a clone-able request, and the composed stack's type signature reveals every layer applied. The compiler rejects stacks where layer requirements are not met.**

## Minimal snippet

```rust
use tower::{Service, ServiceBuilder, ServiceExt};
use tower::timeout::TimeoutLayer;
use tower::retry::{RetryLayer, Policy};
use std::time::Duration;

// Compose layers around a base service
let service = ServiceBuilder::new()
    .layer(TimeoutLayer::new(Duration::from_secs(5)))
    .layer(RetryLayer::new(my_retry_policy))
    .service(my_base_service);

// The composed type encodes every layer:
// Retry<Timeout<MyService>>
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Traits** [-> T05](T05-type-classes.md) | `Service<Request>` is a trait with associated types `Response`, `Error`, and `Future`. Middleware is generic over any `S: Service`. |
| **Generics and bounds** [-> T04](T04-generics-bounds.md) | Layers constrain the inner service with trait bounds: `S: Service<Request> + Clone` for retry, `S: Service<Request>` with `S::Future: Send` for async. |
| **Async/await** [-> T12](T12-effect-tracking.md) | `Service::call` returns a `Future`. Async middleware composes futures, similar to how monadic bind composes computations. |
| **Functor/Monad patterns** [-> T54](T54-functor-applicative-monad.md) | `ServiceExt::map_response` is Functor map; `ServiceExt::and_then` is monadic bind on the response. Iterator adaptors follow the same pattern. |
| **Ownership and lifetimes** [-> T10](T10-ownership-moves.md) | Middleware must respect ownership: `Clone` bounds enable retry (cloning requests), and lifetimes constrain how long borrowed data lives through the stack. |

## Gotchas and limitations

1. **Type complexity.** Composed tower services produce deeply nested types like `Retry<RetryPolicy, Timeout<RateLimit<MyService>>>`. Use `BoxService` or `BoxCloneService` to erase the type when it becomes unwieldy, at the cost of dynamic dispatch.

2. **No automatic lifting.** Unlike monad transformers where `MonadLift` can auto-lift operations, each tower layer must explicitly decide how to forward calls. The `Layer` trait's `layer` method is the manual composition point.

3. **Error type alignment.** Each layer may produce its own error type. Composing layers requires error types to align (via `Into` conversions) or be unified into a common error enum. This is analogous to the transformer stack ordering problem.

4. **Backpressure and readiness.** `Service::poll_ready` introduces a readiness protocol that middleware must correctly propagate. Incorrectly implementing `poll_ready` in a custom layer can cause deadlocks or dropped requests.

5. **Not a general-purpose abstraction.** Tower's `Service`/`Layer` pattern is specific to request-response workflows. It does not generalize to arbitrary effect composition the way monad transformers do in Scala or Lean.

## Beginner mental model

Think of a tower `Service` as a **factory worker** on an assembly line. Each `Layer` is a **station** added before or after the worker: one station adds a timer (timeout), another adds a retry mechanism, another logs every item passing through. The `ServiceBuilder` assembles the stations in order. The final type tells you exactly which stations are in the line. If a station requires a specific capability from the worker (like being able to clone items for retry), the compiler checks that requirement at build time.

## Example A -- Custom middleware layer

```rust
use std::task::{Context, Poll};
use std::pin::Pin;
use std::future::Future;
use tower::Service;

// Logging middleware that wraps any service
struct LogService<S> {
    inner: S,
    prefix: String,
}

impl<S, Req> Service<Req> for LogService<S>
where
    S: Service<Req>,
    Req: std::fmt::Debug,
{
    type Response = S::Response;
    type Error = S::Error;
    type Future = S::Future;

    fn poll_ready(&mut self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        self.inner.poll_ready(cx)
    }

    fn call(&mut self, req: Req) -> Self::Future {
        println!("{}: {:?}", self.prefix, req);
        self.inner.call(req)
    }
}
```

## Example B -- Iterator adaptors as functor/monad composition

```rust
fn process_data(input: &[&str]) -> Vec<i32> {
    input.iter()
        .filter_map(|s| s.parse::<i32>().ok())  // OptionT-like: filter + map
        .map(|n| n * 2)                          // Functor: transform values
        .filter(|n| *n > 10)                     // MonadPlus: guard
        .collect()                               // realize the lazy stack
}

fn main() {
    let data = vec!["5", "abc", "10", "3", "20"];
    println!("{:?}", process_data(&data)); // [10, 20, 40] -- wait, 5*2=10 passes >10? no.
    // Actually: 5->10 (not >10), "abc"->skip, 10->20 (>10), 3->6 (not >10), 20->40 (>10)
    // Result: [20, 40]
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Middleware layers ensure required cross-cutting concerns (auth, validation) are always applied.
- [-> UC-08](../usecases/UC08-error-handling.md) -- Error-handling layers (retry, fallback) compose with the service stack for resilient error recovery.
- [-> UC-13](../usecases/UC13-state-machines.md) -- Service readiness (`poll_ready`) encodes a two-state machine (ready/not-ready) in the API.
- [-> UC-20](../usecases/UC20-ownership-apis.md) -- Middleware ownership and `Clone` bounds enforce correct request lifecycle through the stack.

## Source anchors

- [tower crate documentation](https://docs.rs/tower)
- [tower Service trait](https://docs.rs/tower/latest/tower/trait.Service.html)
- [tower Layer trait](https://docs.rs/tower/latest/tower/trait.Layer.html)
- [axum middleware guide](https://docs.rs/axum/latest/axum/middleware/index.html)
