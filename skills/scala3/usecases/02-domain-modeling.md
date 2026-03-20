# Domain Modeling

## The Constraint

Express precise domain types that reject invalid values at compile time. A `NonEmptyString` is never empty; an `Email` always contains an `@`. The type system carries the proof, not runtime assertions.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Opaque types | Zero-cost wrappers for domain primitives | [-> catalog/12](../catalog/12-opaque-types.md) |
| Enums / ADTs | Closed sets of domain states and events | [-> catalog/11](../catalog/11-enums-adts-gadts.md) |
| Union / Intersection types | Ad-hoc "one of" or "all of" without boilerplate hierarchies | [-> catalog/01](../catalog/01-union-intersection.md) |
| Refined types (via inline) | Compile-time validation of literal values | [-> catalog/15](../catalog/15-structural-refined.md) |
| Inline validation | `inline` + `compiletime.error` to reject bad literals at compile time | [-> catalog/17](../catalog/17-inline-compiletime.md) |

## Patterns

### 1 — Opaque types for domain primitives

Wrap raw types to prevent accidental misuse. Validation happens once, at the boundary.

```scala
object domain:
  opaque type Email = String
  object Email:
    def parse(raw: String): Either[String, Email] =
      if raw.contains("@") then Right(raw)
      else Left(s"Invalid email: $raw")

  opaque type NonEmptyString = String
  object NonEmptyString:
    def from(s: String): Option[NonEmptyString] =
      Option.when(s.nonEmpty)(s)

  extension (e: Email) def value: String = e
  extension (s: NonEmptyString) def value: String = s

import domain.*

case class User(name: NonEmptyString, contact: Email)

// Construction always goes through the smart constructor:
val user: Either[String, User] =
  for
    name  <- NonEmptyString.from("Alice").toRight("empty name")
    email <- Email.parse("alice@example.com")
  yield User(name, email)
```

### 2 — Smart constructors with inline validation

When values are known at compile time (literals), reject invalid ones before the program runs.

```scala
object port:
  opaque type Port = Int
  object Port:
    inline def apply(inline p: Int): Port =
      inline if p < 1 || p > 65535 then
        compiletime.error("Port must be between 1 and 65535")
      else p

    def fromInt(p: Int): Option[Port] =
      Option.when(p >= 1 && p <= 65535)(p)

  extension (p: Port) def value: Int = p

import port.*

val http = Port(80)       // compiles
val https = Port(443)     // compiles
// val bad = Port(99999)  // compile error: "Port must be between 1 and 65535"
```

### 3 — Enum hierarchies for domain states

Model the lifecycle of a domain entity as a sealed hierarchy. Each state carries exactly the data it needs.

```scala
enum OrderStatus:
  case Draft(items: List[String])
  case Submitted(items: List[String], submittedAt: java.time.Instant)
  case Shipped(trackingId: String)
  case Delivered(signature: String)
  case Cancelled(reason: String)

def ship(status: OrderStatus): OrderStatus = status match
  case OrderStatus.Submitted(_, _) =>
    OrderStatus.Shipped(trackingId = "TRK-001")
  case other =>
    throw IllegalStateException(s"Cannot ship from $other")
    // Better: use phantom types (see usecase 01) to make this a compile error
```

### 4 — Intersection types for combining capabilities

Compose fine-grained trait capabilities without committing to a fixed class hierarchy.

```scala
trait HasName:
  def name: String

trait HasEmail:
  def email: String

trait HasRole:
  def role: String

// A function that requires both name and email, but not role:
def sendWelcome(user: HasName & HasEmail): String =
  s"Welcome ${user.name}, confirmation sent to ${user.email}"

// A function that requires all three:
def auditLog(user: HasName & HasEmail & HasRole): String =
  s"[${user.role}] ${user.name} <${user.email}>"

case class FullUser(name: String, email: String, role: String)
    extends HasName, HasEmail, HasRole

val u = FullUser("Alice", "alice@example.com", "admin")
sendWelcome(u)  // compiles — FullUser <: HasName & HasEmail
auditLog(u)     // compiles — FullUser <: HasName & HasEmail & HasRole
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Domain primitives | Value classes (`extends AnyVal`) — single field only, boxing issues under erasure | Opaque types — zero cost always, multiple extensions, no boxing |
| Smart constructors | Same `apply`/`from` pattern, but no `inline` validation; checks always at runtime | `inline` + `compiletime.error` rejects bad literals at compile time |
| Sealed hierarchies | `sealed trait` + `case class` — verbose, no built-in `values`/`ordinal` | `enum` — concise, derives useful members automatically |
| Capability composition | Compound types (`A with B`) — order-dependent, no true intersection | Intersection types (`A & B`) — commutative, first-class |
| Literal validation | Shapeless `Witness` or refined-types library for compile-time checks | Built-in `inline if` + `compiletime.error`; no library needed for simple cases |

## When to Use Which Feature

**Opaque types** are the default choice for any domain primitive — IDs, quantities, validated strings. Prefer them over case class wrappers when you need zero overhead and the type has a single underlying representation.

**Inline validation** is appropriate when literal values are common in your codebase (ports, HTTP status codes, configuration constants). For values computed at runtime, fall back to smart constructors returning `Option` or `Either`.

**Enums** model domain states. Use parameterized cases when each state carries different data. Consider phantom-type-based state machines (usecase 01) when you need the compiler to enforce valid transitions.

**Intersection types** shine when capabilities are fine-grained and mixed ad hoc. If you find yourself creating deep trait hierarchies just to combine behaviors, intersection types let callers specify exactly what they need without a fixed inheritance tree.

**Union types** (`A | B`) are useful for "one of" scenarios where you do not want a shared supertype — e.g., `String | Int` as a JSON value. Prefer sealed enums when the alternatives have domain meaning and you want exhaustive matching.
