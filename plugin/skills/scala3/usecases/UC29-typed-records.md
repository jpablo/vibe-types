# Typed Records

## The Constraint

Represent structured data with named, typed fields. The compiler checks field names, types, and access at every use site. Functional updates produce new values without mutation, and the type system tracks the change.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Record types (case classes) | Named product types with compiler-generated accessors, equality, and copy | [-> T31](T31-record-types.md)(../catalog/T31-record-types.md) |
| Named tuples | Lightweight named fields without defining a class (Scala 3.5+) | [-> T31](T31-record-types.md)(../catalog/T31-record-types.md) |
| Opaque types | Refine field types with zero-cost wrappers | [-> T03](T03-newtypes-opaque.md)(../catalog/T03-newtypes-opaque.md) |
| Derivation | Auto-generate codecs, show instances, and equality from the record shape | [-> T06](T06-derivation.md)(../catalog/T06-derivation.md) |

## Patterns

### 1 — Case class as the primary record type

Case classes give you named fields, immutability, structural equality, pattern matching, and `copy` for free.

```scala
case class User(name: String, age: Int, active: Boolean)

val alice = User("Alice", 30, active = true)

// Typed field access:
val n: String = alice.name
// val x: Int = alice.name   // compile error — String ≠ Int

// Pattern matching:
alice match
  case User(name, age, true) => s"$name ($age) is active"
  case User(name, _, false)  => s"$name is inactive"
```

### 2 — Functional updates with copy

`copy` creates a new instance with selected fields changed. The compiler checks that the new values match the field types.

```scala
case class Config(host: String, port: Int, ssl: Boolean, maxRetries: Int)

val dev  = Config("localhost", 8080, ssl = false, maxRetries = 0)
val prod = dev.copy(host = "prod.example.com", ssl = true, maxRetries = 3)

// dev is unchanged:
assert(dev.host == "localhost")
assert(prod.ssl)

// Type error on wrong field type:
// val bad = dev.copy(port = "not a number")  // compile error
```

### 3 — Named tuples for lightweight records (Scala 3.5+)

Named tuples provide record-like syntax without a class definition. Useful for local computations, return types, and intermediate data.

```scala
type Point = (x: Double, y: Double)

val p: Point = (x = 1.0, y = 2.0)
val q: Point = (x = p.x + 1, y = p.y + 1)

// Named access:
val dist = math.sqrt(p.x * p.x + p.y * p.y)

// Works in function signatures:
def translate(p: Point, dx: Double, dy: Double): Point =
  (x = p.x + dx, y = p.y + dy)
```

### 4 — Nested records with opaque field types

Combine case classes with opaque types for type-safe, self-documenting records.

```scala
object domain:
  opaque type Email = String
  object Email:
    def apply(s: String): Email = s  // production code: validate here
  extension (e: Email) def value: String = e

  opaque type UserId = Long
  object UserId:
    def apply(v: Long): UserId = v
  extension (id: UserId) def value: Long = id

import domain.*

case class Address(street: String, city: String, zip: String)
case class UserProfile(id: UserId, email: Email, address: Address)

val profile = UserProfile(
  id = UserId(1001),
  email = Email("alice@example.com"),
  address = Address("123 Main St", "Springfield", "62701")
)

// Deep functional update:
val moved = profile.copy(
  address = profile.address.copy(city = "Shelbyville")
)
```

### 5 — Derived instances from record shape

Case classes support `derives` to auto-generate type class instances based on their field structure.

```scala
import scala.deriving.Mirror

// Assuming a Show or Codec type class with a derived given:
case class Event(name: String, timestamp: Long, payload: String)
  derives CanEqual

val e1 = Event("click", 1000L, "{}")
val e2 = Event("click", 1000L, "{}")
assert(e1 == e2)   // CanEqual derived — safe equality

// With a JSON library that supports derives:
// case class Event(...) derives JsonCodec
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Case classes | Same core feature; same `copy` method | Same; `derives` clause added for type class derivation |
| Named tuples | Not available; Shapeless records or plain tuples | Built-in from Scala 3.5 — `(x: Int, y: Int)` |
| Functional updates | `copy` only | `copy` + named tuples; optics libraries (Monocle) for deep updates |
| Pattern matching | Same | Same; improved exhaustiveness checking |
| Derivation | Macro-based (Shapeless, Magnolia) | Built-in `Mirror` + `derives` clause — no external macro dependency |

## When to Use Which Feature

**Use case classes** for all persistent domain data — the combination of immutability, equality, pattern matching, and `copy` makes them the default choice.

**Use named tuples** for ephemeral data — function return types, intermediate computations, local groupings — where defining a class adds ceremony without value.

**Use opaque types for field types** when two fields share the same underlying type but must not be confused (IDs, emails, monetary amounts).

**Use `derives`** to auto-generate codecs, equality, ordering, and show instances. This keeps records focused on data and delegates behaviour to type classes.
