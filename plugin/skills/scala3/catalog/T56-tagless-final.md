# Tagless Final

> **Since:** Scala 3.0 (pattern established in Scala 2 with cats/cats-effect; fully supported in Scala 3)

## What it is

Tagless final is a design pattern where **algebras are defined as traits parameterized by an effect type `F[_]`**, and programs are written against those abstract interfaces. The concrete effect (`IO`, `Task`, `Either`, a test mock) is chosen only at the "end of the world" — when the program is actually run. This separates **description** (what the program does) from **execution** (how effects are performed).

A tagless final algebra is a trait like `trait UserRepo[F[_]]` with abstract methods returning `F[...]`. Business logic is written as functions constrained by `[F[_]: Monad]` (or more specific type classes), and different interpreters provide different `F` implementations. For production, `F = IO`; for testing, `F = Id` or a state monad; for tracing, `F` might add logging.

This pattern is the backbone of cats-effect and ZIO-based Scala applications and is the idiomatic way to achieve dependency injection and testability in functional Scala.

## What constraint it enforces

**Code written against tagless final algebras can only use the operations declared in the algebra traits and the capabilities provided by the `F` type-class bounds. The compiler rejects any direct use of concrete effects, ensuring the program is truly polymorphic in its effect type.**

## Minimal snippet

```scala
import cats.Monad
import cats.syntax.all.*

trait Console[F[_]]:
  def readLine: F[String]
  def printLine(s: String): F[Unit]

def greet[F[_]: Monad](console: Console[F]): F[Unit] =
  for
    _    <- console.printLine("What is your name?")
    name <- console.readLine
    _    <- console.printLine(s"Hello, $name!")
  yield ()

// Production interpreter: F = IO
// Test interpreter: F = State[TestState, _]
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Functor/Applicative/Monad** [-> T54](T54-functor-applicative-monad.md) | Tagless final programs are constrained by `[F[_]: Monad]` or finer bounds (`Applicative`, `MonadError`), expressing the minimum effect capability required. |
| **Type classes / givens** [-> T05](T05-type-classes.md) | Algebras are type-class-like traits. Interpreters are provided as given instances or explicit values. Context bounds supply the monadic evidence. |
| **Monad transformers** [-> T55](T55-monad-transformers.md) | Interpreters can target monad transformer stacks. `type App[A] = EitherT[IO, AppError, A]` is a common concrete `F`. |
| **Higher-kinded types** | `F[_]` in trait parameters requires Scala's support for higher-kinded type parameters, which Scala 3 provides natively. |
| **Extension methods** [-> T19](T19-extension-methods.md) | Extension methods can add derived operations to algebras without modifying the trait definition. |
| **Opaque types** [-> T03](T03-newtypes-opaque.md) | Domain types (newtypes) can be used within tagless final algebras to enforce domain boundaries at the type level. |

## Gotchas and limitations

1. **Boilerplate.** Every algebra requires a trait, and every interpreter requires an implementation of every method. For large applications with many algebras, this can be verbose. Scala 3's concise syntax helps, but the pattern remains heavier than direct coding.

2. **Type inference difficulty.** Complex tagless final programs with multiple algebras and type-class constraints can overwhelm Scala's type inference. Explicit type annotations or type aliases for the effect stack are often necessary.

3. **Performance overhead.** Polymorphic `F[_]` calls go through type-class dispatch (though JIT inlining often eliminates this). For hot paths, consider specializing to a concrete effect type.

4. **Testing convenience vs. production complexity.** The main benefit is testability (swap `IO` for a pure interpreter), but if you never actually test with a different `F`, the abstraction adds complexity without payoff.

5. **Natural transformations for interpreter composition.** Combining multiple interpreters (e.g., a caching layer + database layer) requires natural transformations (`FunctionK`, `~>`), which add another layer of abstraction.

6. **Not built into the language.** Tagless final is a community pattern, not a language feature. There is no compiler support or special syntax — it emerges from the combination of higher-kinded types, type classes, and for-comprehensions.

## Beginner mental model

Think of a tagless final algebra as a **script** for a play. The script says "Actor enters, says line, exits" but does not specify which actor or which stage. An **interpreter** is a specific production: the Broadway production uses real actors on a real stage (`IO`), the rehearsal uses stand-ins reading from cards (`State`), and the review uses a recording (`Writer`). The script is the same; only the production changes. This is the power of tagless final: write once, run in any context.

## Example A -- Repository algebra with test interpreter

```scala
import cats.Monad
import cats.data.State
import cats.syntax.all.*

trait KVStore[F[_]]:
  def put(key: String, value: String): F[Unit]
  def get(key: String): F[Option[String]]

// Test interpreter using State monad
type TestState = Map[String, String]
type TestF[A] = State[TestState, A]

given KVStore[TestF] with
  def put(key: String, value: String): TestF[Unit] =
    State.modify(_ + (key -> value))
  def get(key: String): TestF[Option[String]] =
    State.inspect(_.get(key))

def program[F[_]: Monad](store: KVStore[F]): F[Option[String]] =
  for
    _ <- store.put("greeting", "hello")
    v <- store.get("greeting")
  yield v

// Test: program(summon[KVStore[TestF]]).run(Map.empty).value
// => (Map("greeting" -> "hello"), Some("hello"))
```

## Example B -- Multiple algebras composed

```scala
import cats.MonadError
import cats.syntax.all.*

type AppError = String

trait Auth[F[_]]:
  def authenticate(token: String): F[String]  // returns username

trait Notifications[F[_]]:
  def send(user: String, msg: String): F[Unit]

def notifyUser[F[_]: [G[_]] =>> MonadError[G, AppError]](
    auth: Auth[F],
    notif: Notifications[F],
    token: String
): F[Unit] =
  for
    user <- auth.authenticate(token)
    _    <- notif.send(user, "Welcome back!")
  yield ()
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Algebras can enforce that operations are only available in valid states by parameterizing the algebra accordingly.
- [-> UC-09](../usecases/UC09-builder-config.md) -- ReaderT-based interpreters inject configuration into tagless final programs.
- [-> UC-11](../usecases/UC11-effect-tracking.md) -- The `F[_]` constraint in the type signature tracks exactly which effects a computation requires.
- [-> UC-13](../usecases/UC13-state-machines.md) -- Algebras can model state machines where operations are only available in certain states.

## Source anchors

- [cats-effect documentation — Tagless Final](https://typelevel.org/cats-effect/docs/typeclasses)
- [Practical FP in Scala (book by Gabriel Volpe)](https://leanpub.com/pfp-scala) — canonical tagless final reference
- Scala 3 reference: "Contextual Abstractions — Context Bounds"
