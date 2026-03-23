# Tagless Final (via Trait-Based Dependency Injection)

> **Since:** Rust 1.0 (traits); stable

## What it is

Rust does not have a "tagless final" pattern by name, but the same goal — **decoupling business logic from concrete implementations** — is achieved through **trait-based dependency injection**. You define behavior as a trait (the algebra), write generic functions constrained by that trait (the program), and provide different implementations (interpreters) for production, testing, and other contexts.

Where Scala's tagless final parameterizes by an effect type `F[_]`, Rust parameterizes by a concrete trait implementor `T: Repository`. The effect type is implicit: methods can return `Result<A, E>` (fallible), `impl Future<Output = Result<A, E>>` (async + fallible), or plain values. The key insight is the same: program against an abstract interface, and choose the concrete implementation at the call site.

This pattern is pervasive in Rust: `std::io::Read` and `std::io::Write` are abstract I/O algebras, `Iterator` is an abstract sequence algebra, and application-level traits for repositories, services, and clients follow the same structure.

## What constraint it enforces

**Functions constrained by trait bounds can only call methods declared on those traits. The compiler rejects any use of concrete implementation details, ensuring the code works with any conforming implementation and enabling seamless swapping for tests.**

## Minimal snippet

```rust
trait UserRepo {
    fn find(&self, id: u64) -> Option<String>;
    fn save(&self, id: u64, name: &str);
}

fn greet_user(repo: &impl UserRepo, id: u64) -> String {
    match repo.find(id) {
        Some(name) => format!("Hello, {name}!"),
        None => "User not found".to_string(),
    }
}

// Production: impl UserRepo for PostgresRepo { ... }
// Test: impl UserRepo for MockRepo { ... }
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Traits** [-> T05](T05-type-classes.md) | Algebras are traits. Implementations are `impl Trait for ConcreteType` blocks. Trait bounds constrain generic code to the required interface. |
| **Generics and bounds** [-> T04](T04-generics-bounds.md) | `fn process<R: Repository>(repo: &R)` is the generic version; `fn process(repo: &impl Repository)` is the sugared form. Both achieve effect polymorphism. |
| **Trait objects** | `dyn Repository` enables dynamic dispatch when the concrete type is unknown at compile time. Useful for heterogeneous collections of interpreters. |
| **Async traits** | `async fn` in traits (stabilized in Rust 1.75) allows async algebras directly. Before that, `async-trait` crate was required. |
| **Functor/Monad patterns** [-> T54](T54-functor-applicative-monad.md) | Methods on algebra traits return `Result` or `Option`, bringing monadic error handling into the trait-based abstraction. |
| **Middleware layers** [-> T55](T55-monad-transformers.md) | tower's `Service` trait is itself a tagless final algebra for request-response processing. Layers add capabilities without modifying the algebra. |

## Gotchas and limitations

1. **No higher-kinded abstraction.** You cannot write a single trait generic over the "effect type" (`F[_]`) the way Scala can. Each trait either returns concrete types (`Option<T>`, `Result<T, E>`) or uses associated types. This means you cannot swap between sync and async with the same trait without `async-trait` or GATs.

2. **Object safety constraints.** Traits used as `dyn Trait` must be object-safe: no generic methods, no `Self` in return types. This limits what algebras can express when dynamic dispatch is needed.

3. **Orphan rules limit interpreter placement.** You can only implement a trait for a type if you own the trait or the type. This means external algebra traits cannot be implemented for external types without newtype wrappers [-> T03](T03-newtypes-opaque.md).

4. **Async trait limitations.** `async fn` in traits returns `impl Future`, which is not dyn-compatible. For dynamic dispatch, use `trait-variant` or box the future manually.

5. **No automatic interpreter composition.** Composing multiple algebras requires a concrete type that implements all of them, or a generic function with multiple trait bounds. There is no automatic "stacking" like monad transformers.

## Beginner mental model

Think of a trait as a **power outlet standard** (the algebra): it defines the shape of the plug (method signatures). Your generic code is an **appliance** built for that standard — it works anywhere the outlet exists. The production outlet connects to the real power grid (database, network); the test outlet connects to a battery pack (in-memory mock). The appliance does not know or care which power source is behind the outlet. The compiler ensures every outlet fully satisfies the standard.

## Example A -- Async repository with test double

```rust
use std::collections::HashMap;

#[async_trait::async_trait]
trait UserRepo: Send + Sync {
    async fn find(&self, id: u64) -> Option<String>;
    async fn save(&self, id: u64, name: String);
}

// Test implementation
struct MockRepo {
    data: tokio::sync::RwLock<HashMap<u64, String>>,
}

#[async_trait::async_trait]
impl UserRepo for MockRepo {
    async fn find(&self, id: u64) -> Option<String> {
        self.data.read().await.get(&id).cloned()
    }
    async fn save(&self, id: u64, name: String) {
        self.data.write().await.insert(id, name);
    }
}

async fn rename_user(repo: &dyn UserRepo, id: u64, new_name: String) -> bool {
    if repo.find(id).await.is_some() {
        repo.save(id, new_name).await;
        true
    } else {
        false
    }
}
```

## Example B -- Multiple trait bounds for composed algebras

```rust
trait Logger {
    fn log(&self, msg: &str);
}

trait Notifier {
    fn notify(&self, user: &str, msg: &str) -> Result<(), String>;
}

// Generic code requiring both algebras
fn process_order(
    logger: &impl Logger,
    notifier: &impl Notifier,
    user: &str,
) -> Result<(), String> {
    logger.log(&format!("Processing order for {user}"));
    notifier.notify(user, "Your order is being processed")?;
    logger.log("Order processed successfully");
    Ok(())
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Trait bounds ensure only valid operations are callable, preventing misuse of incomplete implementations.
- [-> UC-08](../usecases/UC08-error-handling.md) -- Algebra traits define error types in their signatures, making error handling explicit and swappable per interpreter.
- [-> UC-13](../usecases/UC13-state-machines.md) -- Trait-based algebras can model state machines where different states expose different operations.
- [-> UC-20](../usecases/UC20-ownership-apis.md) -- Ownership and lifetime bounds on algebra traits enforce correct resource management across implementations.

## Source anchors

- `book/src/ch10-02-traits.md` (defining and implementing traits)
- `book/src/ch17-02-trait-objects.md` (dynamic dispatch with `dyn`)
- [async-trait crate](https://docs.rs/async-trait)
- [Rust API Guidelines — Traits](https://rust-lang.github.io/api-guidelines/interoperability.html)
