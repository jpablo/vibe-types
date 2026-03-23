# Concurrency (via Libraries)

## The Constraint

Track concurrent effects, enforce structured concurrency, and prevent data races at the type level. Scala 3 has no built-in `Send`/`Sync` markers, but library ecosystems — ZIO, Cats Effect, Akka Typed, and Ox — encode concurrency discipline into their type systems.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Effect tracking | Library effect types (`IO`, `ZIO`, `Task`) encode side effects in the type signature | [-> T12](T12-effect-tracking.md)(../catalog/T12-effect-tracking.md) |
| Type classes | `Concurrent`, `Async`, `Temporal` hierarchies constrain which effects a function may use | [-> T05](T05-type-classes.md)(../catalog/T05-type-classes.md) |
| Context functions | Thread capabilities (scopes, runtimes) implicitly through call chains | [-> T42](T42-context-functions.md)(../catalog/T42-context-functions.md) |
| Opaque types | Zero-cost wrappers for fiber IDs, refs, and scoped tokens | [-> T03](T03-newtypes-opaque.md)(../catalog/T03-newtypes-opaque.md) |

## Patterns

### 1 — ZIO effect types for typed concurrency

ZIO encodes the environment, error channel, and success type. Concurrent combinators are type-safe.

```scala
import zio.*

// ZIO[R, E, A]: needs environment R, may fail with E, succeeds with A
val fetchUser: ZIO[Any, Throwable, String] = ZIO.attempt("Alice")
val fetchOrder: ZIO[Any, Throwable, Int]   = ZIO.attempt(42)

// Run in parallel — types compose:
val both: ZIO[Any, Throwable, (String, Int)] =
  fetchUser.zipPar(fetchOrder)

// Fibers are typed:
val forked: ZIO[Any, Nothing, Fiber[Throwable, String]] =
  fetchUser.fork

// Structured concurrency with scoped fibers:
val scoped: ZIO[Scope, Throwable, String] =
  ZIO.scoped {
    for
      fiber <- fetchUser.forkScoped
      result <- fiber.join
    yield result
  }
```

### 2 — Cats Effect with Concurrent type class

Cats Effect uses a type-class hierarchy to constrain which effects a function may perform.

```scala
import cats.effect.*
import cats.syntax.all.*

// Only requires Concurrent — works with IO or any effect type
def fetchBoth[F[_]: Concurrent](
  fa: F[String],
  fb: F[Int]
): F[(String, Int)] =
  (fa, fb).parTupled

// Ref for safe shared mutable state:
def counter[F[_]: Ref.Make: Monad]: F[Ref[F, Int]] =
  Ref.of[F, Int](0)

// Resource for structured lifecycle:
def managed[F[_]: Async]: Resource[F, String] =
  Resource.make(Async[F].delay("acquired"))(r => Async[F].delay(()))
```

### 3 — Akka Typed actors for message-typed concurrency

Akka Typed actors accept only messages matching their declared protocol type.

```scala
import akka.actor.typed.*
import akka.actor.typed.scaladsl.*

enum Command:
  case Greet(name: String, replyTo: ActorRef[Greeting])
  case Stop

case class Greeting(message: String)

val greeter: Behavior[Command] = Behaviors.receive { (ctx, msg) =>
  msg match
    case Command.Greet(name, replyTo) =>
      replyTo ! Greeting(s"Hello, $name!")
      Behaviors.same
    case Command.Stop =>
      Behaviors.stopped
}
// greeter ! "raw string"  // compile error — Command expected
```

### 4 — Ox for structured concurrency with scoped threads

Ox uses Scala 3 context functions and scoped values for structured concurrency on JDK 21+ virtual threads.

```scala
import ox.*

// Structured scope — all forks must complete before the scope exits:
val result: (String, Int) = supervised {
  val f1 = forkUser(fork(fetchName()))
  val f2 = fork(fetchAge())
  (f1.join(), f2.join())
}

def fetchName(): String = "Alice"
def fetchAge(): Int = 30

// Racing — first to complete wins, others are cancelled:
val fastest: String = supervised {
  raceSuccess(
    () => { Thread.sleep(100); "slow" },
    () => "fast"
  )
}
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Effect types | ZIO and Cats Effect worked on 2.12/2.13; same pattern | Same libraries target Scala 3; context functions simplify capability passing |
| Akka Typed | Available from Akka 2.6 on Scala 2 | Same API; `enum` makes protocol definitions cleaner |
| Structured concurrency | Library-only (ZIO scopes, Cats Resource) | Ox leverages Scala 3 context functions + JDK 21 virtual threads |
| Thread safety markers | No built-in Send/Sync; convention-based | Still no built-in markers; capture checking (experimental) may add compiler-tracked capabilities |

## When to Use Which Feature

**Use ZIO** when you want a batteries-included effect system with typed errors, layers for dependency injection, and built-in concurrency primitives. Best for applications that fully commit to the ZIO ecosystem.

**Use Cats Effect** when you want to write polymorphic code that abstracts over the effect type. Ideal for libraries and teams already using the Typelevel stack.

**Use Akka Typed** for actor-based systems where concurrency is modeled as typed message passing between long-lived entities.

**Use Ox** for straightforward structured concurrency on virtual threads without the overhead of a full effect system. Best for applications on JDK 21+ that prefer imperative style with safety guarantees.
