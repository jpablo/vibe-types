# UC-07 -- Extensibility

## 1. The Constraint

**Design extension points -- control what can and cannot be extended.**
Library authors need to express: "this type is designed for subclassing" vs. "extend only through type classes" vs. "compose, don't inherit." Scala 3 replaces the implicit openness of Scala 2 classes with explicit controls.

## 2. Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Open classes | Mark a class as designed for inheritance outside its file; without `open`, extending produces a warning. | [-> catalog/13](../catalog/T21-encapsulation.md) |
| Export clauses | Surface members of a composed object, replacing inheritance with delegation. | [-> catalog/13](../catalog/T21-encapsulation.md) |
| Extension methods | Add operations to types you do not own, with or without type-class evidence. | [-> catalog/07](../catalog/T19-extension-methods.md) |
| Type-class derivation | Mechanically derive instances for ADTs, providing extensibility without subclassing. | [-> catalog/08](../catalog/T06-derivation.md) |
| Transparent traits | Hide implementation mixins from inferred types so they do not leak into public APIs. | [-> catalog/13](../catalog/T21-encapsulation.md) |
| Givens | Provide type-class instances that extend behavior retroactively. | [-> catalog/05](../catalog/T05-type-classes.md) |

## 3. Patterns

### Pattern A: Type-Class Pattern for Retroactive Extension

Define a trait, provide given instances, and use extension methods for syntax. New types gain the behavior by defining a new given -- no modification of existing code required.

```scala
trait Show[A]:
  extension (a: A) def show: String

given Show[Int] with
  extension (a: Int) def show: String = a.toString

given Show[Double] with
  extension (a: Double) def show: String = f"$a%.2f"

// Retroactive: adding Show to a third-party type
case class Point(x: Double, y: Double)

given Show[Point] with
  extension (p: Point) def show: String = s"(${p.x.show}, ${p.y.show})"

def log[A: Show](a: A): Unit = println(a.show)

// log(Point(1.0, 2.5))  =>  (1.00, 2.50)
```

### Pattern B: Extension Methods on Third-Party Types

When you do not need the full type-class indirection, plain extension methods add operations directly.

```scala
extension (s: String)
  def words: List[String] = s.split("\\s+").toList
  def initials: String    = s.words.map(_.head.toUpper).mkString

// "ada lovelace".initials  =>  "AL"

// Conditional extension: only available when an Ordering exists
extension [A](xs: List[A])(using Ordering[A])
  def median: A =
    val sorted = xs.sorted
    sorted(sorted.size / 2)

// List(3, 1, 2).median  =>  2
// List("x", "y").median  -- compiles only because Ordering[String] exists
```

### Pattern C: Export for Composition over Inheritance

Export clauses forward selected members of composed objects, making delegation as concise as inheritance but without coupling to a superclass.

```scala
class Logger:
  def info(msg: String): Unit  = println(s"[INFO] $msg")
  def error(msg: String): Unit = println(s"[ERROR] $msg")

class Metrics:
  def count(event: String): Unit = println(s"count: $event")
  def gauge(name: String, v: Double): Unit = println(s"$name=$v")

class Service:
  private val logger  = Logger()
  private val metrics = Metrics()

  export logger.*                           // info, error available on Service
  export metrics.{count, gauge as measure}  // count + renamed gauge

// val s = Service()
// s.info("started")       -- forwarded to logger
// s.measure("cpu", 0.42)  -- forwarded to metrics.gauge
```

### Pattern D: `open` Modifier for Controlled Inheritance

Without `open`, extending a class from another file triggers a warning. Use `open` to signal that a class is designed for subclassing; omit it to discourage ad-hoc extensions.

```scala
// Library code
open class Renderer:
  def render(node: Node): String = node.toString
  // Subclasses may override render to customize output.

class Node(val tag: String, val children: List[Node])

// Client code -- OK, Renderer is open
class HtmlRenderer extends Renderer:
  override def render(node: Node): String =
    s"<${node.tag}>${node.children.map(render).mkString}</${node.tag}>"

// Contrast: without `open`, this extension warns
class Formatter:
  def format(s: String): String = s.trim

// class FancyFormatter extends Formatter  // warning: Formatter is not open
```

Use `final` to prohibit extension entirely. Use the default (no modifier) when you neither intend nor forbid it but do not promise a stable extension contract.

## 4. Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Controlling inheritance | All non-`final` classes were implicitly open; no compile-time signal that a class was designed for extension. | `open` modifier makes the contract explicit. Extending a non-open, non-final class from another file warns. |
| Delegation / composition | Required manual forwarding methods or macro-based delegation. | `export` clauses generate forwarders automatically with full type fidelity. |
| Adding methods to types | Implicit classes (`implicit class RichString(s: String)`), requiring a wrapper allocation (unless a value class). | `extension` blocks: no wrapper, no implicit class boilerplate. Conditional extensions via `using`. |
| Type-class syntax | Implicit classes for syntax + implicit defs for instances. "Pimp my library" idiom. | `given`/`using` for instances, `extension` for syntax, `derives` for mechanical derivation. |
| Hiding mixins from inferred types | Not possible; all supertypes appeared in inferred signatures. | `transparent` trait suppresses itself from inferred types. |

## 5. When to Use Which Feature

| If you need... | Prefer |
|---|---|
| Retroactive polymorphism over types you do not own | **Type-class pattern** (Pattern A): trait + given + extension. Decouples the behavior from the type hierarchy. |
| A few convenience methods on a third-party type | **Plain extension methods** (Pattern B). No trait or given needed. |
| Reuse without inheritance coupling | **Export clauses** (Pattern C). Strictly better than inheriting from a utility class. |
| A class designed as a superclass for client extension | **`open` modifier** (Pattern D). Documents the contract and silences warnings. |
| A mixin that should not appear in inferred types | **`transparent` trait**. Keeps public API signatures clean. |
| Mechanical instance generation for case classes / enums | **Type-class derivation** (`derives`). Avoids writing boilerplate given instances for standard shapes. |
