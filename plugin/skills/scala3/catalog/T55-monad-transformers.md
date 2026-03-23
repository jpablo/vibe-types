# Monad Transformers

> **Since:** Scala 3.0 (cats monad transformers since cats 1.x)

## What it is

Monad transformers let you **compose multiple monadic effects into a single monad stack**. When you need a computation that can both fail (`Either`) and perform IO (`IO`), you cannot simply nest `IO[Either[E, A]]` and use a single for-comprehension — the types do not align. A monad transformer like `EitherT[IO, E, A]` wraps the nested structure and provides a unified `Monad` instance, so for-comprehensions work through the entire stack.

The cats library provides the standard transformers: **`EitherT[F, E, A]`** wraps `F[Either[E, A]]` (error handling), **`OptionT[F, A]`** wraps `F[Option[A]]` (optionality), **`StateT[F, S, A]`** wraps `S => F[(S, A)]` (stateful computation), **`ReaderT[F, R, A]`** (also known as `Kleisli[F, R, A]`) wraps `R => F[A]` (dependency injection), and **`WriterT[F, W, A]`** wraps `F[(W, A)]` (logging/accumulation).

## What constraint it enforces

**Monad transformers enforce that effects compose in a well-typed stack where each layer's operations are available through a unified monadic interface, and effects from inner layers must be explicitly lifted to be used at the outer level.**

## Minimal snippet

```scala
import cats.data.EitherT
import cats.effect.IO

type AppError = String

def findUser(id: Long): EitherT[IO, AppError, String] =
  EitherT.rightT("Alice")

def checkAge(name: String): EitherT[IO, AppError, Int] =
  EitherT.rightT(30)

val program: EitherT[IO, AppError, String] =
  for
    name <- findUser(1L)
    age  <- checkAge(name)
  yield s"$name is $age"
// Single for-comprehension handles both IO and Either
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Functor/Applicative/Monad** [-> T54](T54-functor-applicative-monad.md) | Transformers require the base `F` to be a Monad. The transformer itself is also a Monad, enabling for-comprehension chaining. |
| **Type classes / givens** [-> T05](T05-type-classes.md) | Transformer instances are provided as given instances. `EitherT` gets a `Monad` instance when `F` has one. |
| **Tagless final** [-> T56](T56-tagless-final.md) | Tagless final algebras are often interpreted into a monad transformer stack. `type App[A] = EitherT[IO, AppError, A]` is a common concrete effect type. |
| **For-comprehensions** | Transformers unify the stack so a single for-comprehension sequences operations across all effect layers. |
| **Type lambdas** [-> T04](T04-generics-bounds.md) | `EitherT[IO, AppError, *]` has kind `* -> *`, matching `F[_]`. Type lambdas or kind-projector syntax adapt multi-parameter transformers to the expected shape. |

## Gotchas and limitations

1. **Performance overhead.** Each transformer layer adds an allocation per `flatMap` step. Deep stacks (`EitherT[StateT[ReaderT[IO, Config, _], AppState, _], Error, _]`) can have measurable overhead. Consider using effect systems (ZIO, cats-effect + `Ref`) as an alternative.

2. **Lifting is required.** To use a base `IO` operation inside `EitherT[IO, E, A]`, you must lift: `EitherT.liftF(ioAction)`. Forgetting to lift causes type mismatches. cats' `MonadError` and `Ask` type classes can reduce manual lifting.

3. **Stack ordering matters.** `EitherT[StateT[IO, S, _], E, A]` and `StateT[EitherT[IO, E, _], S, A]` have different semantics: in the first, an error discards state changes; in the second, state persists through errors.

4. **Type inference struggles.** Complex transformer stacks can exceed Scala's type inference capabilities. Explicit type annotations on intermediate values or helper type aliases are often necessary.

5. **Composability ceiling.** Transformers compose two effects at a time. Adding a third layer means wrapping a transformer in another transformer, leading to quadratic boilerplate. This is the primary motivation for effect systems like ZIO and Polaris.

## Beginner mental model

Think of monad transformers as **adapters that merge two power outlets into one**. `IO` provides the "side effect" outlet, `Either` provides the "error handling" outlet. `EitherT[IO, E, A]` is an adapter that gives you a single outlet supporting both. You plug your for-comprehension into the combined outlet and use both powers seamlessly. The cost: you need explicit "lifting" when you have a plug that only fits one of the original outlets.

## Example A -- OptionT for optional results in IO

```scala
import cats.data.OptionT
import cats.effect.IO

def lookupEnv(key: String): OptionT[IO, String] =
  OptionT(IO(sys.env.get(key)))

def lookupPort: OptionT[IO, Int] =
  lookupEnv("PORT").mapFilter(_.toIntOption)

val config: OptionT[IO, (String, Int)] =
  for
    host <- lookupEnv("HOST")
    port <- lookupPort
  yield (host, port)
// None if either variable is missing; IO for the side effect of reading env
```

## Example B -- StateT for stateful computation

```scala
import cats.data.StateT
import cats.effect.IO

type Counter[A] = StateT[IO, Int, A]

def increment: Counter[Unit] =
  StateT.modify(n => n + 1)

def getCount: Counter[Int] =
  StateT.get

val program: Counter[String] =
  for
    _     <- increment
    _     <- increment
    _     <- increment
    count <- getCount
  yield s"Final count: $count"

// program.run(0) => IO((3, "Final count: 3"))
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- `EitherT` and `OptionT` ensure error and absence handling is threaded through the entire computation.
- [-> UC-09](../usecases/UC09-builder-config.md) -- `ReaderT` (Kleisli) injects configuration through a computation stack without explicit parameter passing.
- [-> UC-11](../usecases/UC11-effect-tracking.md) -- Transformer stacks make the full set of effects visible in the type signature.
- [-> UC-13](../usecases/UC13-state-machines.md) -- `StateT` encodes state-machine transitions as pure, composable monadic computations.

## Source anchors

- [cats EitherT documentation](https://typelevel.org/cats/datatypes/eithert.html)
- [cats OptionT documentation](https://typelevel.org/cats/datatypes/optiont.html)
- [cats StateT documentation](https://typelevel.org/cats/datatypes/state.html)
- [cats Kleisli (ReaderT) documentation](https://typelevel.org/cats/datatypes/kleisli.html)
