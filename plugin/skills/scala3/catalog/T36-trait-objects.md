# Trait-Based Dynamic Dispatch

> **Since:** Scala 2 (traits and abstract classes); Scala 3 refines with `open`, `sealed`, `Matchable` restrictions

## What it is

In Scala 3, **traits** and **abstract classes** provide runtime polymorphism through JVM virtual dispatch. A variable typed as a trait can hold any instance of a class that extends that trait, and method calls are resolved at runtime via the JVM's vtable mechanism. Unlike Rust, where trait references require an explicit `dyn Trait` marker and carry a fat pointer, *all* trait references in Scala are dynamically dispatched by default — there is no "static dispatch" mode for trait method calls through a supertype reference.

Traits can declare abstract methods (no body), concrete methods (with a default body), and state via `val`/`var` definitions. Abstract classes add the restriction of single inheritance but can take constructor parameters. Together, they form the backbone of Scala's object-oriented polymorphism and are the runtime counterpart to the compile-time polymorphism provided by type classes and given instances.

## What constraint it enforces

**A trait reference guarantees that the held value implements all of the trait's abstract members, with the concrete method called determined at runtime by the actual class of the object.** The `sealed` modifier restricts which classes can extend the trait (same file only), enabling exhaustive pattern matching. The `open` modifier documents that a class is designed for extension. `Matchable` controls whether a trait reference can be used as a pattern-match scrutinee.

## Minimal snippet

```scala
trait Animal:
  def name: String
  def sound: String
  def greet: String = s"I'm $name and I say $sound"  // concrete default

class Dog(val name: String) extends Animal:
  def sound = "Woof"

class Cat(val name: String) extends Animal:
  def sound = "Meow"

// Dynamic dispatch: the runtime type determines which `sound` is called
val pets: List[Animal] = List(Dog("Rex"), Cat("Whiskers"))
pets.map(_.greet)
// List("I'm Rex and I say Woof", "I'm Whiskers and I say Meow")
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type classes / givens** [-> catalog/T05](T05-type-classes.md) | Type classes provide compile-time (ad-hoc) polymorphism; traits provide runtime (subtype) polymorphism. Choose type classes when you need retroactive conformance without modifying existing types; choose traits when you need a common supertype for heterogeneous collections. |
| **ADTs / enums** [-> catalog/T01](T01-algebraic-data-types.md) | `sealed trait` + `case class` is the standard ADT encoding. Sealing restricts subclasses to the defining file, enabling exhaustive matches. |
| **Type narrowing / Matchable** [-> catalog/T14](T14-type-narrowing.md) | Pattern matching on a trait reference narrows the type. `Matchable` controls whether the reference permits matching at all, protecting opaque type abstractions. |
| **Encapsulation** [-> catalog/T21](T21-encapsulation.md) | `sealed` vs `open` vs default (adhoc-extension warning) gives library authors fine-grained control over who may extend a trait. `final` prevents all extension. |
| **Intersection types** [-> catalog/T02](T02-union-intersection.md) | A value can be typed as `Printable & Serializable`, requiring it to implement both traits. This is Scala's answer to multi-trait bounds. |

## Gotchas and limitations

1. **No static dispatch opt-in.** Unlike Rust's monomorphization of generics, Scala always dispatches trait method calls through the vtable when called through a supertype reference. The JIT compiler may devirtualize hot call sites, but this is not guaranteed.

2. **Diamond inheritance.** A class can mix in multiple traits that define the same method. Scala uses **linearization** to resolve conflicts: the rightmost trait in the `extends` clause wins, and `super` calls follow the linearization order. This can surprise developers coming from single-inheritance languages.

3. **Sealed does not mean final.** A `sealed` trait can still be extended — but only within the same source file. Code outside that file cannot add new subtypes, which enables exhaustive matching.

4. **Trait initialization order.** Traits with `val` definitions can cause `NullPointerException` if a subclass accesses a `val` before it is initialized. Use `lazy val` or `def` in traits to avoid initialization-order pitfalls.

5. **Abstract classes vs traits.** Abstract classes can have constructor parameters and are slightly more efficient on the JVM (single vtable instead of interface dispatch). However, a class can extend only one abstract class but many traits.

6. **Matchable restriction.** Under `-language:strictEquality` or explicit `Matchable` bounds, you cannot pattern-match on `Any`-typed references. Traits that need safe downcasting should extend `Matchable`.

## Beginner mental model

Think of a trait as a **contract with a built-in name tag**. Any class that signs the contract (extends the trait) must fulfill all the blank lines (abstract methods). When you hold a reference typed as the trait, you can call any method from the contract, and the JVM looks at the name tag at runtime to find the right implementation. You do not know (or need to know) which class actually signed — you just trust the contract.

## Example A — Sealed trait for exhaustive matching

```scala
sealed trait Shape:
  def area: Double

case class Circle(radius: Double) extends Shape:
  def area = math.Pi * radius * radius

case class Rect(w: Double, h: Double) extends Shape:
  def area = w * h

def describe(s: Shape): String = s match
  case Circle(r) => s"Circle with radius $r"
  case Rect(w, h) => s"Rectangle ${w}x$h"
  // No default needed — compiler knows the match is exhaustive
```

## Example B — Open class for framework extension

```scala
open class HttpHandler:
  def handle(req: Request): Response =
    Response(200, "OK")

// Client code in another file can extend because of `open`
class LoggingHandler extends HttpHandler:
  override def handle(req: Request): Response =
    println(s"Handling ${req.path}")
    super.handle(req)
```

## Use-case cross-references

- [-> UC-14](../usecases/UC14-extensibility.md) Traits define extension points; `open` / `sealed` control the extensibility boundary.
- [-> UC-01](../usecases/UC01-invalid-states.md) Sealed traits restrict inhabitants to known subtypes, making invalid states unrepresentable.

## Source anchors

- [Scala 3 Reference -- Traits](https://docs.scala-lang.org/scala3/reference/other-new-features/trait-parameters.html)
- [Scala 3 Reference -- Open Classes](https://docs.scala-lang.org/scala3/reference/other-new-features/open-classes.html)
- [Scala 3 Reference -- Matchable](https://docs.scala-lang.org/scala3/reference/other-new-features/matchable.html)
- [Scala 3 Book -- Traits](https://docs.scala-lang.org/scala3/book/domain-modeling-tools.html#traits)
