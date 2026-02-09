# UC-08 -- Equality and Comparison

## 1. The Constraint

**Prevent nonsensical equality comparisons at compile time.**
In standard Scala (and Java), any two values can be compared with `==`, even when the comparison can never be `true` -- for example, `42 == "hello"` or `Option(1) == List(1)`. Scala 3's multiversal equality makes such comparisons a compile-time error, forcing you to declare which type pairs are legitimately comparable.

## 2. Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Multiversal equality | The `strictEquality` language import makes `==` and `!=` require a `CanEqual` instance. | [-> catalog/09] |
| CanEqual | The type class the compiler looks for to permit `==` between two types. | [-> catalog/09] |
| Enums / ADTs | `derives CanEqual` on an enum generates the instance for all cases. | [-> catalog/11] |
| Opaque types | An opaque type is a distinct type; under strict equality it gets its own equality domain. | [-> catalog/12] |

## 3. Patterns

### Pattern A: Enabling `strictEquality`

Turn on strict equality project-wide via a compiler flag or per-file via an import. After that, comparing unrelated types is an error.

```scala
import scala.language.strictEquality

val x: Int = 42
val s: String = "hello"

// x == s  // error: Values of types Int and String cannot be compared with == or !=

x == 42    // ok: same type
```

The compiler flag equivalent is `-language:strictEquality`.

### Pattern B: Deriving `CanEqual` for ADTs

Use `derives CanEqual` on an enum or sealed hierarchy to allow comparisons among its members.

```scala
import scala.language.strictEquality

enum Color derives CanEqual:
  case Red, Green, Blue

val a: Color = Color.Red
val b: Color = Color.Blue

a == b    // ok: CanEqual[Color, Color] is derived
// a == 42  // error: Values of types Color and Int cannot be compared
```

For a sealed trait hierarchy, derive on the parent:

```scala
sealed trait Shape derives CanEqual
case class Circle(r: Double) extends Shape
case class Rect(w: Double, h: Double) extends Shape

Circle(1.0) == Rect(2.0, 3.0)  // ok: both are Shape
```

### Pattern C: Custom `CanEqual` for Domain Types

When two distinct types should be comparable, provide a given `CanEqual` instance explicitly.

```scala
import scala.language.strictEquality

case class Celsius(value: Double)
case class Fahrenheit(value: Double)

// Allow cross-comparison in both directions
given CanEqual[Celsius, Fahrenheit] = CanEqual.derived
given CanEqual[Fahrenheit, Celsius] = CanEqual.derived

Celsius(100) == Fahrenheit(212)  // compiles (semantics are yours to define)
// Celsius(100) == 100            // error: no CanEqual[Celsius, Int]
```

Restricting comparison prevents accidental cross-domain bugs:

```scala
case class UserId(value: Long) derives CanEqual
case class OrderId(value: Long) derives CanEqual

// UserId(1) == OrderId(1)  // error: no CanEqual[UserId, OrderId]
// This catches a real bug -- IDs from different domains should not be compared.
```

### Pattern D: Opaque Types and Equality

An opaque type is distinct from its underlying type. Under strict equality, this means it has its own equality domain. You must explicitly provide a `CanEqual` if comparisons with other types are desired.

```scala
import scala.language.strictEquality

object Units:
  opaque type Meters = Double
  object Meters:
    def apply(d: Double): Meters = d
    given CanEqual[Meters, Meters] = CanEqual.derived

  opaque type Feet = Double
  object Feet:
    def apply(d: Double): Feet = d
    given CanEqual[Feet, Feet] = CanEqual.derived

import Units.*

Meters(1.0) == Meters(2.0)  // ok
Feet(3.0) == Feet(3.0)      // ok
// Meters(1.0) == Feet(3.28)  // error: no CanEqual[Meters, Feet]
// Meters(1.0) == 1.0         // error: no CanEqual[Meters, Double]
```

This is a significant benefit of opaque types: you get type-safe equality for free once strict equality is enabled.

## 4. Scala 2 Comparison

| Aspect | Scala 2 | Scala 3 |
|---|---|---|
| Default equality | Universal: any two values can be compared with `==`. `42 == "hello"` compiles without warning. | Same default, but `strictEquality` opt-in makes it a type error. |
| Restricting equality | Not built in. Libraries like Scalactic's `===` or cats `Eq` type class provided checked equality, but required a different operator. | `CanEqual` works with the standard `==` and `!=` operators. No special syntax needed. |
| ADT equality | No mechanism to auto-derive safe equality for case class hierarchies. | `derives CanEqual` on an enum or sealed trait. |
| Newtype equality | Value classes (`extends AnyVal`) still used universal equality. | Opaque types under `strictEquality` are in their own equality domain by default. |

## 5. When to Use Which Feature

| If you need... | Prefer |
|---|---|
| Project-wide safety against nonsensical comparisons | Enable **`strictEquality`** via compiler flag. Add `CanEqual` instances as needed. |
| Safe equality for an ADT | **`derives CanEqual`** on the enum or sealed trait (Pattern B). |
| Cross-type comparison between two specific domain types | **Explicit `given CanEqual`** instances (Pattern C). Provide both directions. |
| Preventing comparison of structurally identical but semantically different types | **Opaque types** (Pattern D). Each opaque type is its own equality island. |
| Gradual migration | Start without `strictEquality`; add `derives CanEqual` to new types. Enable the flag when coverage is sufficient. The compiler errors guide you to missing instances. |
