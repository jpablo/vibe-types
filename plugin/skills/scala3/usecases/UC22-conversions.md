# Conversions

## The Constraint

Convert between types explicitly and safely. Scala 3 replaces Scala 2's implicit conversions with the `Conversion` type class, making conversions visible, searchable, and opt-in. Opaque type smart constructors and `From`/`To` patterns provide additional compile-time-checked conversion paths.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Conversion type class | The standard mechanism for user-defined implicit conversions in Scala 3 | [-> T18](T18-conversions-coercions.md)(../catalog/T18-conversions-coercions.md) |
| Opaque types | Smart constructors as controlled conversion boundaries | [-> T03](T03-newtypes-opaque.md)(../catalog/T03-newtypes-opaque.md) |
| Extension methods | Add conversion methods to existing types without wrapping | [-> T19](T19-extension-methods.md)(../catalog/T19-extension-methods.md) |
| Union types | Accept multiple source types without conversion | [-> T02](T02-union-intersection.md)(../catalog/T02-union-intersection.md) |

## Patterns

### 1 — Conversion type class for implicit widening

Define a `given Conversion[A, B]` and import `scala.language.implicitConversions` to enable automatic use.

```scala
import scala.language.implicitConversions

case class Meters(value: Double)
case class Kilometers(value: Double)

// Lossy direction is explicit (Meters -> Km); safe direction is implicit:
given Conversion[Kilometers, Meters] with
  def apply(km: Kilometers): Meters = Meters(km.value * 1000)

def distanceInMeters(m: Meters): String = s"${m.value}m"

distanceInMeters(Kilometers(5.0))  // automatically converted to Meters(5000.0)
// distanceInMeters(42.0)          // compile error — no Conversion[Double, Meters]
```

### 2 — Opaque type smart constructors as gated conversions

Opaque types expose conversions only through explicit factory methods, preventing accidental construction.

```scala
object domain:
  opaque type Email = String

  object Email:
    def from(s: String): Either[String, Email] =
      if s.contains("@") then Right(s) else Left(s"invalid email: $s")

    // Unsafe escape hatch — clearly marked:
    def unsafeFrom(s: String): Email = s

  extension (e: Email) def value: String = e

import domain.*

val ok = Email.from("a@b.com")    // Right(a@b.com)
val bad = Email.from("not-email") // Left(invalid email: not-email)
// val e: Email = "raw"            // compile error — no implicit conversion
```

### 3 — From/To pattern with type classes

Define a `From` type class for explicit, discoverable conversions between domain types.

```scala
trait From[A, B]:
  def convert(a: A): B

object From:
  extension [A](a: A)
    def into[B](using f: From[A, B]): B = f.convert(a)

case class Celsius(value: Double)
case class Fahrenheit(value: Double)

given From[Celsius, Fahrenheit] with
  def convert(c: Celsius): Fahrenheit = Fahrenheit(c.value * 9 / 5 + 32)

given From[Fahrenheit, Celsius] with
  def convert(f: Fahrenheit): Celsius = Celsius((f.value - 32) * 5 / 9)

val boiling = Celsius(100).into[Fahrenheit]   // Fahrenheit(212.0)
val freezing = Fahrenheit(32).into[Celsius]   // Celsius(0.0)
```

### 4 — Extension methods for ad-hoc conversion

Add `.toX` methods to existing types without implicit magic.

```scala
extension (s: String)
  def toIntOption: Option[Int] =
    try Some(s.toInt) catch case _: NumberFormatException => None

  def toSlug: String =
    s.toLowerCase.replaceAll("[^a-z0-9]+", "-").stripPrefix("-").stripSuffix("-")

"42".toIntOption     // Some(42)
"Hello World!".toSlug // "hello-world"
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Implicit conversions | `implicit def` — invisible, easy to misuse; source of surprising coercions | `Conversion[A, B]` — explicit type class; requires `import scala.language.implicitConversions` |
| Discoverability | Implicit defs hard to find; scattered across companion objects and imports | `given Conversion` is grep-able and shows in IDE "implicits" views |
| Smart constructors | `extends AnyVal` wrappers with `.apply` — boxing pitfalls | Opaque types — truly zero-cost; companion `.from` methods |
| Extension methods | `implicit class` with overhead | `extension` — first-class syntax, no wrapper allocation |

## When to Use Which Feature

**Use `Conversion`** sparingly for well-known safe widenings (e.g., `Int` to `Long`, `Kilometers` to `Meters`). Every implicit conversion is a potential readability trap — keep the set small and well-documented.

**Use opaque type smart constructors** as the primary conversion pattern for domain types. They make invalid conversions unrepresentable and valid conversions explicit.

**Use the `From`/`To` type-class pattern** when you have a systematic family of conversions (units, serialisation formats, DTO mapping) and want a uniform `.into[B]` syntax.

**Use extension methods** (`.toX`) for simple, one-off conversions where the caller should see exactly what is happening. This is the most readable option for most cases.
