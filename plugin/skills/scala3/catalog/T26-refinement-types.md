# Refinement Types

> **Since:** Library-level (refined, Iron) on Scala 2/3 | **Language support:** opaque types + inline provide the foundation

## What it is

A refinement type is a base type narrowed by a predicate — a value of type `Refined[Int, Positive]` is an `Int` that has been proven positive. Scala 3 does not have built-in refinement types, but two libraries provide them with compile-time checking:

- **[refined](https://github.com/fthomas/refined)** — The original refinement type library. Defines `Refined[T, P]` where `P` is a predicate type. Mature ecosystem with integrations for Circe, Doobie, PureConfig, etc.
- **[Iron](https://github.com/Iltotore/iron)** — A Scala 3-native library using opaque types and inline for zero-overhead refinements. Leverages Scala 3's compile-time capabilities directly.

Both encode the predicate in the type, so a refined value carries a compile-time guarantee that the predicate holds.

## What constraint it enforces

**A refined value can only be constructed by passing a check (at compile time for literals, at runtime for dynamic values). The predicate is part of the type, so functions accepting `PosInt` cannot receive an unchecked `Int`.**

## Minimal snippet

### Using Iron (Scala 3-native)

```scala
import io.github.iltotore.iron.*
import io.github.iltotore.iron.constraint.numeric.*

type PosInt = Int :| Positive

val x: PosInt = 42        // OK — literal checked at compile time
// val y: PosInt = -1      // compile error: -1 does not satisfy Positive

def safeDivide(a: Int, b: Int :| StrictlyPositive): Int = a / b
// safeDivide(10, 0)       // compile error: 0 does not satisfy StrictlyPositive
```

### Using refined

```scala
import eu.timepit.refined.api.Refined
import eu.timepit.refined.numeric.Positive
import eu.timepit.refined.auto.*

type PosInt = Int Refined Positive

val x: PosInt = 42        // OK — macro checks literal at compile time
// val y: PosInt = -1      // compile error

// Runtime refinement for dynamic values
import eu.timepit.refined.refineV
val input: Int = getUserInput()
val result: Either[String, PosInt] = refineV[Positive](input)
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Opaque types** [-> T03](T03-newtypes-opaque.md)(T03-newtypes-opaque.md) | Iron uses opaque types internally — refined values have zero runtime overhead. |
| **Inline** [-> T16](T16-compile-time-ops.md)(T16-compile-time-ops.md) | Iron uses `inline` for compile-time predicate checking on literals. |
| **ADTs** [-> T01](T01-algebraic-data-types.md)(T01-algebraic-data-types.md) | Refinement types complement ADTs: ADTs model which states exist, refinements constrain the values within each state. |
| **Type-class derivation** [-> T06](T06-derivation.md)(T06-derivation.md) | Both libraries provide Codec/Encoder/Decoder instances so refined types integrate with JSON and database libraries. |

## Gotchas and limitations

1. **Compile-time checking only works for literals.** `val x: PosInt = 42` is checked at compile time, but `val x: PosInt = someVar` requires runtime validation via `refineV` (refined) or `.refine` (Iron), returning an `Either`.

2. **Two ecosystems.** `refined` has broader integrations (Circe, Doobie, PureConfig, http4s). Iron is newer and Scala 3-native but its integration ecosystem is growing. Choose one per project.

3. **Predicate composition.** Both libraries support combining predicates (`Positive And LessEqual[100]` in refined, `StrictlyPositive & Less[100]` in Iron), but the syntax differs.

4. **Not structural refinements.** These are value refinements (predicates on values), not Scala's structural types (`T { def name: String }`). See [-> T07](T07-structural-typing.md)(T07-structural-typing.md) for structural typing.

## Beginner mental model

Think of a refinement type as a **newtype with a built-in validator that runs at compile time when possible**. Instead of writing a smart constructor yourself, the library provides a generic mechanism: you declare the predicate (`Positive`, `NonEmpty`, `MatchesRegex["^[a-z]+$"]`), and the library enforces it — at compile time for literals, at runtime (returning `Either`) for dynamic values.

## Example A — Domain model with refined fields

```scala
import io.github.iltotore.iron.*
import io.github.iltotore.iron.constraint.all.*

type Username = String :| (MinLength[1] & MaxLength[32])
type Port     = Int :| Interval.OpenClosed[0, 65535]
type Email    = String :| Match["^[\\w.+-]+@[\\w-]+\\.[\\w.]+$"]

case class ServerConfig(
  host: String,
  port: Port,
  adminEmail: Email
)

val cfg = ServerConfig("localhost", 8080, "admin@example.com")
// ServerConfig("localhost", 0, "admin@example.com")  // compile error: 0 not in (0, 65535]
```

## Example B — Parse, don't validate with refinement types

```scala
import io.github.iltotore.iron.*
import io.github.iltotore.iron.constraint.numeric.*

// Runtime parsing returns Either — the "parse, don't validate" pattern
def parsePort(s: String): Either[String, Int :| Interval.OpenClosed[0, 65535]] =
  s.toIntOption match
    case Some(n) => n.refineEither[Interval.OpenClosed[0, 65535]]
    case None    => Left(s"not an integer: $s")

// Once parsed, the refined type flows through the system
def connect(port: Int :| Interval.OpenClosed[0, 65535]): Unit =
  println(s"Connecting to port $port")  // always valid, no re-check needed
```

## Recommended libraries

| Library | Scala version | Style | Key strength |
|---------|--------------|-------|-------------|
| [Iron](https://github.com/Iltotore/iron) | Scala 3 | Opaque types + inline | Zero overhead, Scala 3-native |
| [refined](https://github.com/fthomas/refined) | Scala 2 & 3 | `Refined[T, P]` wrapper | Mature ecosystem, broad integrations |

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Refinement types make invalid values unconstructable.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Domain primitives with built-in constraints (ports, emails, usernames).

## Source anchors

- [Iron documentation](https://iltotore.github.io/iron/docs/)
- [refined GitHub](https://github.com/fthomas/refined)
- [Iron GitHub](https://github.com/Iltotore/iron)
