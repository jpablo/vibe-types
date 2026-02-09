# Type Lambdas (`[X] =>> F[X]`)

## What it is

A type lambda is an anonymous, higher-kinded type expression in Scala 3 that lets you partially apply or rearrange type constructor parameters directly in a type position, without introducing a named type alias. Written as `[X] =>> F[X]`, it is the type-level analogue of a value-level lambda `(x) => f(x)`. Type lambdas eliminate the need for the "type lambda trick" (using structural refinements) that was prevalent in Scala 2 libraries.

## What constraint it lets you express

**Type lambdas let you abstract over type constructors inline, expressing higher-kinded relationships (like Functor, Monad, or any `* -> *` abstraction) without auxiliary type aliases.** This is critical whenever a type class expects a unary type constructor but you have a binary one (e.g., `Either[E, _]`) or need to rearrange type parameters.

## Minimal snippet

```scala
// Partially applying a binary type constructor:
// Map[K, V] has kind (*, *) -> *, but Functor expects * -> *
type MapWithKey[K] = [V] =>> Map[K, V]

// Equivalent to a named alias, but usable inline:
trait Functor[F[_]]:
  extension [A](fa: F[A])
    def map[B](f: A => B): F[B]

// Using a type lambda directly as a type argument:
given eitherFunctor[E]: Functor[[A] =>> Either[E, A]] with
  extension [A](fa: Either[E, A])
    def map[B](f: A => B): Either[E, B] = fa.map(f)
```

## Interaction with other features

- **Given instances.** Type lambdas are most commonly used when providing given instances for type classes that expect a unary type constructor but the target type has more parameters. [-> UC-05]
- **Context bounds.** You can use type lambdas inside context bounds: `[F[_]: [G[_]] =>> Monad[G]]`, though this is unusual and typically a named alias is clearer.
- **Match types.** Type lambdas can appear inside match type bodies, enabling computed higher-kinded types. [-> UC-03]
- **Polymorphic function types.** Type lambdas define types at the type level (`=>>`) while polymorphic function types define polymorphic values at the term level (`=>`). They are complementary: type lambdas are applied in type expressions, polymorphic functions are applied in term expressions. [-> UC-04]
- **Variance.** Type parameters of type lambdas cannot carry `+` or `-` variance annotations. Variance is only tracked on named type definitions (`type`, `trait`, `class`).
- **Bounds.** Type parameters of type lambdas can have upper and lower bounds (e.g., `[X <: Comparable[X]] =>> Set[X]`).

## Gotchas and limitations

1. **No variance annotations.** You cannot write `[+X] =>> F[X]`. Variance must be declared on named type definitions. This can force you to introduce a type alias when variance matters for subtyping.
2. **Readability.** Deeply nested type lambdas quickly become hard to read. Prefer named `type` aliases for anything beyond a single level of partial application.
3. **Not value-level.** Type lambdas exist purely at the type level. They cannot be instantiated, passed around as values, or pattern-matched against at runtime. For value-level polymorphism, use polymorphic function types (`[A] => ...`).
4. **Kind restrictions.** Type lambda parameters must be first-order types. You cannot nest type lambdas in parameter positions to express higher-order kinds directly (e.g., `[F[_[_]]] =>> ...` requires explicit kind annotations via bounds).
5. **Erasure.** Like all type-level constructs, type lambdas are erased at runtime. They have no runtime representation and cannot be reflected upon.

## Use-case cross-references

- [-> UC-03] Match types can produce type-lambda-shaped results for computed higher-kinded types.
- [-> UC-04] Polymorphic function types are the value-level counterpart to type lambdas.
- [-> UC-05] Given instances frequently use type lambdas to adapt multi-parameter type constructors to unary type class shapes.
- [-> UC-06] Context bounds on type parameters that are themselves higher-kinded rely on type lambdas for partial application.
