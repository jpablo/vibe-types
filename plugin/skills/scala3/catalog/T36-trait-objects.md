# Trait-Based Dynamic Dispatch

> **Since:** Scala 2 (traits, abstract classes, `sealed`); Scala 3 adds `open`, the `Matchable` marker, and trait constructor parameters

## What it is

In Scala 3, **traits** and **abstract classes** provide runtime polymorphism through JVM virtual dispatch. A variable typed as a trait can hold any instance of a class that extends that trait, and method calls are resolved at runtime via the JVM's vtable mechanism. Unlike Rust, where trait references require an explicit `dyn Trait` marker and carry a fat pointer, *all* trait references in Scala are dynamically dispatched by default — there is no "static dispatch" mode for trait method calls through a supertype reference.

Traits can declare abstract methods (no body), concrete methods (with a default body), and state via `val`/`var` definitions. Since Scala 3 they can also take constructor parameters, so that is *not* what separates them from abstract classes; the difference is that a trait's parameters may only be supplied by the class that extends it **directly**. What abstract classes actually add is single inheritance (a class extends at most one) and slightly cheaper dispatch. Together, they form the backbone of Scala's object-oriented polymorphism and are the runtime counterpart to the compile-time polymorphism provided by type classes and given instances.

## What constraint it enforces

**A trait reference guarantees that the held value implements all of the trait's abstract members, with the concrete method called determined at runtime by the actual class of the object.** The `sealed` modifier restricts which classes can extend the trait (same file only), enabling exhaustive pattern matching. The `open` modifier documents that a class is designed for extension. `Matchable` sits between `Any` and `AnyRef`/`AnyVal` and gates pattern matching on `Any`-typed scrutinees; it places no restriction on trait references, since every trait extends `AnyRef` and `AnyRef <: Matchable`.

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
| **Type narrowing / Matchable** [-> catalog/T14](T14-type-narrowing.md) | Pattern matching on a trait reference narrows the type, and is always permitted: a trait extends `AnyRef`, and `AnyRef <: Matchable`. `Matchable` only bites on `Any`-typed values, `Any`-bounded abstract types, and opaque types -- and then only as an `[E165]` warning under `-source:future`. It protects opaque-type abstractions, not trait references. |
| **Encapsulation** [-> catalog/T21](T21-encapsulation.md) | `sealed` (subtypes confined to the same file) vs `open` vs plain gives library authors control over who may extend a trait. `final` is not a point on that scale for traits -- `final trait T` is `[E065] Syntax Error: trait T may not be final`; `final` applies to classes. And "plain" is silent by default: extending a non-`open` class from another file only produces the adhoc-extension feature warning under `-source:future`, and even there it is silenced by `import scala.language.adhocExtensions`. |
| **Intersection types** [-> catalog/T02](T02-union-intersection.md) | A value can be typed as `Printable & Serializable`, requiring it to implement both traits. This is Scala's answer to multi-trait bounds. |

## Gotchas and limitations

1. **No static dispatch opt-in.** Unlike Rust's monomorphization of generics, Scala always dispatches trait method calls through the vtable when called through a supertype reference. The JIT compiler may devirtualize hot call sites, but this is not guaranteed.

2. **Diamond inheritance.** A class can mix in multiple traits that define the same method. Scala uses **linearization** to resolve conflicts: the rightmost trait in the `extends` clause wins, and `super` calls follow the linearization order. This can surprise developers coming from single-inheritance languages.

3. **Sealed does not mean final.** A `sealed` trait can still be extended — but only within the same source file. Code outside that file cannot add new subtypes, which enables exhaustive matching.

4. **Trait initialization order.** Traits with `val` definitions can cause `NullPointerException` if a subclass accesses a `val` before it is initialized. Use `lazy val` or `def` in traits to avoid initialization-order pitfalls.

5. **Abstract classes vs traits.** Constructor parameters are *not* the differentiator — Scala 3 traits take them too. The restriction is that a trait's parameters may only be supplied by the class that extends it **directly**: one trait may not call another trait's constructor, and a class that inherits a parameterized trait only indirectly must name it again in its own `extends` clause to pass the arguments.

   ```scala
   trait Greeter(val who: String):
     def greet: String = s"hello $who"

   class Person(n: String) extends Greeter(n)   // OK: direct extension

   trait Polite extends Greeter                 // OK: no arguments here
   class Host extends Polite, Greeter("host")   // must re-list Greeter to pass args
   ```

   The genuine differentiators are **single inheritance** (a class extends at most one abstract class, but any number of traits) and slightly cheaper dispatch on the JVM (class vtable instead of interface dispatch).

6. **What `Matchable` does — and does not — do.** A `Matchable` bound *enables* pattern matching; it never disables it. A trait reference is always matchable, because a plain trait extends `AnyRef` and `AnyRef <: Matchable` — so writing `trait Foo extends Matchable` is a no-op. The restriction only applies to `Any`-typed values, `Any`-bounded abstract types (`[T]` with no upper bound), and opaque types, and it surfaces as an `[E165]` *warning* ("pattern selector should be an instance of Matchable") only under `-source:future`; with default flags there is no diagnostic at all. `-language:strictEquality` is a different feature entirely: it requires `CanEqual` evidence for `==`/`!=` (`[E172]`) and produces no diagnostic on a `match`.

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
case class Request(path: String)
case class Response(status: Int, body: String)

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
