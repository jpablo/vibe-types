# Functor, Applicative, and Monad

> **Since:** Scala 3.0 (for-comprehensions since Scala 2; cats type-class hierarchy since cats 1.x)

## What it is

Functor, Applicative, and Monad form the core abstraction hierarchy for working with values in a computational context (`F[_]`). A **Functor** provides `map` to transform the value inside a context without changing the context's shape. An **Applicative** extends Functor with `pure` (lifting a plain value into the context) and `ap` (applying a function inside a context to a value inside a context). A **Monad** extends Applicative with `flatMap` (sequencing computations where each step can depend on the previous result).

Scala's standard library has limited built-in support — `Option`, `List`, `Either`, and `Future` all provide `map` and `flatMap` methods, and for-comprehensions desugar directly to `flatMap`/`map`/`withFilter` chains. However, there is no `Functor`, `Applicative`, or `Monad` trait in the stdlib. The **cats** library provides the full hierarchy with lawful type-class instances, enabling generic programming over any monadic effect.

## What constraint it enforces

**Code written against `Functor[F]`, `Applicative[F]`, or `Monad[F]` bounds can only use the operations provided by that abstraction level, ensuring the minimum capability required is declared and that implementations satisfy the associated laws (identity, composition, associativity).**

## Minimal snippet

```scala
import cats.Monad
import cats.syntax.all.*

def combine[F[_]: Monad](fa: F[Int], fb: F[Int]): F[Int] =
  for
    a <- fa
    b <- fb
  yield a + b

// Works with any Monad: Option, List, Either, IO, ...
val optResult = combine(Option(1), Option(2))       // Some(3)
val listResult = combine(List(1, 2), List(10, 20))  // List(11, 21, 12, 22)
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **For-comprehensions** | `for { a <- fa; b <- fb } yield expr` desugars to `fa.flatMap(a => fb.map(b => expr))`. This is Scala's do-notation equivalent. |
| **Type classes / givens** [-> T05](T05-type-classes.md) | `Functor`, `Applicative`, `Monad` are type classes provided via `given` instances. `[F[_]: Monad]` is a context bound requiring evidence. |
| **Type lambdas** [-> T04](T04-generics-bounds.md) | When `F` has more than one type parameter (e.g., `Either[E, A]`), a type lambda `[A] =>> Either[E, A]` adapts it to the `F[_]` shape required by Monad. |
| **Monad transformers** [-> T55](T55-monad-transformers.md) | `EitherT`, `OptionT`, `StateT` stack monadic effects, each requiring the underlying `F` to be a Monad. |
| **Tagless final** [-> T56](T56-tagless-final.md) | Algebras parameterized by `F[_]: Monad` can be interpreted with different effect types, separating description from execution. |
| **Higher-kinded types** | Scala 3 supports higher-kinded type parameters (`F[_]`) natively, which is essential for expressing Functor/Monad abstractions. |

## Gotchas and limitations

1. **No stdlib Monad trait.** Scala's standard library does not define `Functor`, `Applicative`, or `Monad` as traits. You must use cats (or a similar library) for the type-class hierarchy. The stdlib only provides the concrete methods (`map`, `flatMap`) on individual types.

2. **For-comprehension limitations.** For-comprehensions require `flatMap`, `map`, and optionally `withFilter` as concrete methods. They do not dispatch through a type-class instance — they call the methods directly on the object. To use for-comprehensions with a cats `Monad` instance, import `cats.syntax.flatMap.*` and `cats.syntax.functor.*`.

3. **Applicative vs Monad.** `Applicative` allows independent computations that can be parallelized; `Monad` implies sequencing. Using `Monad` when `Applicative` suffices over-constrains your code and prevents parallel execution (e.g., `IO.parMapN` requires `Applicative`, not `Monad`).

4. **Law compliance is not enforced by the compiler.** Nothing prevents you from writing a `Monad` instance that violates associativity or left/right identity. Use `cats.laws` and discipline tests to verify law compliance.

5. **Future is not a lawful Monad.** `scala.concurrent.Future` starts executing eagerly upon creation, so `pure` followed by `flatMap` does not behave the same as direct construction. Use cats-effect `IO` for a lawful, lazy alternative.

## Beginner mental model

Think of `F[_]` as a **container or context**: `Option` is a context that might be empty, `List` is a context with multiple values, `IO` is a context of deferred side effects. **Functor** lets you reach inside and transform the value (`map`). **Applicative** lets you combine multiple independent containers. **Monad** lets you chain steps where each step depends on the previous result (`flatMap`). For-comprehensions are syntactic sugar that makes monadic chaining read like imperative code.

## Example A -- Generic validation with Applicative

```scala
import cats.data.Validated
import cats.syntax.all.*

type V[A] = Validated[List[String], A]

val name: V[String] = "Alice".validNel
val age: V[Int] = "must be positive".invalidNel

val person = (name, age).mapN((n, a) => s"$n is $a")
// Invalid(NonEmptyList("must be positive"))
// Both errors accumulate — Applicative, not Monad
```

## Example B -- Effect-polymorphic service

```scala
import cats.Monad
import cats.syntax.all.*

trait UserRepo[F[_]]:
  def find(id: Long): F[Option[String]]

def greetUser[F[_]: Monad](repo: UserRepo[F], id: Long): F[String] =
  repo.find(id).map:
    case Some(name) => s"Hello, $name"
    case None       => "User not found"
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Applicative validation accumulates errors without short-circuiting, preventing partial state.
- [-> UC-09](../usecases/UC09-builder-config.md) -- Monadic chaining in for-comprehensions builds complex configurations step by step.
- [-> UC-11](../usecases/UC11-effect-tracking.md) -- Monad constraints on `F[_]` track which effects a computation requires.
- [-> UC-13](../usecases/UC13-state-machines.md) -- State monad encodes state transitions as pure monadic computations.

## Source anchors

- [cats Monad documentation](https://typelevel.org/cats/typeclasses/monad.html)
- [cats Functor documentation](https://typelevel.org/cats/typeclasses/functor.html)
- [cats Applicative documentation](https://typelevel.org/cats/typeclasses/applicative.html)
- Scala 3 reference: "Contextual Abstractions — Context Bounds"
