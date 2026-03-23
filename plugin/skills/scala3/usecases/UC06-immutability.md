# Immutability

## The Constraint

Ensure that data, once created, cannot be changed. Immutability eliminates a whole class of bugs — race conditions, unexpected aliasing, stale references — and lets the compiler reason about code more aggressively.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Immutability markers (val, final) | Prevent reassignment and overriding at the binding level | [-> T32](T32-immutability-markers.md)(../catalog/T32-immutability-markers.md) |
| Case classes | Immutable product types by default; compiler-generated `copy` for functional updates | [-> T01](T01-algebraic-data-types.md)(../catalog/T01-algebraic-data-types.md) |
| Sealed hierarchies | Closed set of immutable variants | [-> T01](T01-algebraic-data-types.md)(../catalog/T01-algebraic-data-types.md) |
| Opaque types | Immutable wrappers with zero runtime cost | [-> T03](T03-newtypes-opaque.md)(../catalog/T03-newtypes-opaque.md) |
| Immutable collections | Default collections in `scala.collection.immutable` | [-> T32](T32-immutability-markers.md)(../catalog/T32-immutability-markers.md) |

## Patterns

### 1 — val vs var

`val` prevents reassignment. `var` allows it. Prefer `val` everywhere; use `var` only when a mutable accumulator is genuinely clearer.

```scala
val name = "Alice"   // immutable binding
// name = "Bob"      // compile error: reassignment to val

var counter = 0      // mutable — use sparingly
counter += 1         // allowed
```

### 2 — Case class immutability and functional updates

All fields of a `case class` are `val` by default. Use `copy` for functional updates instead of mutation.

```scala
case class Config(host: String, port: Int, ssl: Boolean)

val base = Config("localhost", 8080, ssl = false)
val prod = base.copy(host = "prod.example.com", ssl = true)

// base is unchanged:
assert(base.host == "localhost")
assert(prod.host == "prod.example.com")
```

### 3 — Sealed enums for closed immutable state

Combine `enum` with immutable data to model state without mutable fields.

```scala
enum Outcome:
  case Success(value: String)
  case Failure(error: String, retryable: Boolean)

def retry(o: Outcome): Outcome = o match
  case Outcome.Failure(err, true) => Outcome.Failure(err, retryable = false) // new value
  case other                      => other                                    // unchanged
```

### 4 — Immutable collections as the default

Scala's default imports give you immutable `List`, `Map`, `Set`, and `Vector`. Mutable variants require an explicit import.

```scala
val xs = List(1, 2, 3)
val ys = xs :+ 4            // new list — xs is unchanged
// xs(0) = 99               // compile error — no update method

val m = Map("a" -> 1)
val m2 = m + ("b" -> 2)     // new map
// m("a") = 99              // compile error

// Mutable requires explicit opt-in:
import scala.collection.mutable
val buf = mutable.ArrayBuffer(1, 2, 3)
buf += 4                     // mutates in place
```

### 5 — final to prevent overriding

Mark classes or members `final` to prevent subclasses from introducing mutable overrides.

```scala
final case class Coordinate(x: Double, y: Double)
// class Mutable extends Coordinate(0, 0)  // compile error — cannot extend final class

class Base:
  final val id: Int = 42
  // subclasses cannot override id with a var
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| val / var | Same semantics | Same semantics |
| Case class fields | `val` by default; could write `case class C(var x: Int)` | Same — `var` fields still allowed but strongly discouraged |
| Immutable collections | Default; same library | Same library; `LazyList` replaces `Stream` |
| final | Same | Same; `enum` cases are implicitly final |
| Functional updates | `copy` method on case classes | `copy` + named tuples in Scala 3.5+ offer more flexibility |

## When to Use Which Feature

**Default to `val` and immutable collections.** This is the baseline — depart from it only with justification.

**Use case classes** for all domain data. The compiler gives you `copy`, `equals`, `hashCode`, and pattern matching for free.

**Use `final`** on case classes and key bindings to prevent subclasses from reintroducing mutability.

**Reach for mutable state** only inside performance-critical tight loops or local accumulators that never escape their scope. Wrap mutable state behind an immutable API.
