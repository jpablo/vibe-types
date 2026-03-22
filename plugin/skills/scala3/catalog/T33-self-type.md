# Self Types

> **Since:** Scala 3.0 (inherited from Scala 2; syntax unchanged)

## What it is

A **self-type annotation** (`self: T =>`) on a trait or class declares that any concrete implementation of that trait must also be a subtype of `T`, without actually extending `T`. Inside the annotated trait, `this` has type `T & Self`, giving access to all of `T`'s members. This is different from inheritance (`extends T`): the trait does not become a subtype of `T` in the type hierarchy, and `T` does not appear in the trait's linearization. Self types express a **requirement** ("I need `T`'s capabilities") without establishing an "is-a" relationship. This mechanism underpins the cake pattern and modular composition patterns unique to Scala.

## What constraint it lets you express

**A self-type annotation constrains `this` so that any class mixing in the annotated trait must also mix in (or extend) the required type, enforced at the point of instantiation rather than at the point of definition.** This enables traits to depend on capabilities they do not inherit, allowing orthogonal composition: a `Logging` trait can require `HasConfig` without extending it, and the compiler ensures that any concrete class mixing in `Logging` also provides `HasConfig`.

## Minimal snippet

**Basic self-type:**

```scala
trait HasLogger:
  def log(msg: String): Unit

trait UserService:
  self: HasLogger =>

  def createUser(name: String): Unit =
    log(s"Creating user: $name")   // OK -- self: HasLogger guarantees log exists
    // ... actual creation logic
```

**Concrete class must satisfy the self-type constraint:**

```scala
// OK: satisfies HasLogger requirement
class AppService extends UserService with HasLogger:
  def log(msg: String): Unit = println(msg)

// error: illegal inheritance -- UserService requires HasLogger
// class BrokenService extends UserService
```

**Self-type vs. inheritance:**

```scala
trait A:
  def hello: String = "A"

// Inheritance: B IS an A
trait B extends A:
  def greet: String = hello

// Self-type: C REQUIRES an A but is NOT an A
trait C:
  self: A =>
  def greet: String = hello  // OK -- A's members are accessible

val b: A = new B {}   // OK: B <: A
// val c: A = new C with A {}  // C is not <: A; must use (C with A)
val c: C & A = new C with A {}  // OK
```

**Cake pattern (modular composition):**

```scala
trait DatabaseComponent:
  def query(sql: String): List[Map[String, Any]]

trait UserRepositoryComponent:
  self: DatabaseComponent =>

  def findUser(id: Int): Option[Map[String, Any]] =
    query(s"SELECT * FROM users WHERE id = $id").headOption

trait EmailComponent:
  def sendEmail(to: String, body: String): Unit

trait NotificationComponent:
  self: UserRepositoryComponent & EmailComponent =>

  def notifyUser(id: Int, msg: String): Unit =
    findUser(id).foreach: user =>
      sendEmail(user("email").toString, msg)

// Wire everything together:
object ProductionApp
    extends NotificationComponent
    with UserRepositoryComponent
    with DatabaseComponent
    with EmailComponent:
  def query(sql: String) = ???  // real DB
  def sendEmail(to: String, body: String) = ???  // real email
```

**Named self reference:**

```scala
trait Outer:
  outer =>   // names `this` as `outer` for disambiguation

  trait Inner:
    def enclosing: Outer = outer  // refers to Outer's this
```

## Interaction with other features

| Feature | How it composes |
|---|---|
| **Intersection types** [-> catalog/T02](T02-union-intersection.md) | Multiple self-type requirements use intersection: `self: A & B =>`. The concrete class must mix in all required types. |
| **Given instances** [-> catalog/T05](T05-type-classes.md) | A self-type can require a trait that provides given instances, making capabilities available within the trait body without explicit imports. |
| **Opaque types** [-> catalog/T03](T03-newtypes-opaque.md) | Self types can require traits that define opaque types, giving the requiring trait access to operations defined on those opaque types (but not the underlying representation). |
| **Enums / ADTs** [-> catalog/T01](T01-algebraic-data-types.md) | Self types are rarely used with enums (which are sealed). The cake pattern applies more to service/module composition than to data modeling. |
| **Extension methods** [-> catalog/T19](T19-extension-methods.md) | Extension methods offer an alternative to self types for adding capabilities: instead of requiring a trait via self-type, you can extend the type externally. The choice depends on whether you need access to private members. |
| **Export clauses** [-> catalog/T21](T21-encapsulation.md) | Export clauses provide another form of delegation without inheritance. Self types compose traits at the type level; exports compose values at the member level. Both avoid inheritance. |

## Gotchas and limitations

1. **Self types do not establish subtyping.** `trait A { self: B => }` does *not* make `A <: B`. You cannot pass an `A` where a `B` is expected. The constraint only flows inward (inside `A`, `this` has type `A & B`) and at instantiation (any class implementing `A` must also implement `B`).
2. **Circular self types are allowed (and used).** `trait A { self: B => }` and `trait B { self: A => }` is legal. This enables mutual dependency in the cake pattern but can be confusing and hard to test.
3. **Self types are checked late.** The constraint is only verified when a concrete class is instantiated. An abstract class with an unsatisfied self-type compiles fine; the error appears only when you try to `new` it.
4. **Scala's self types vs. Python's `Self`.** Python's `typing.Self` annotates return types to enable fluent interfaces (`def set(self, ...) -> Self`). Scala's self-type annotations constrain `this`, which is a fundamentally different mechanism. For Python-like `Self` return types in Scala, use F-bounded polymorphism. [-> catalog/T04](T04-generics-bounds.md)
5. **The cake pattern has fallen out of favor.** While self types enable the cake pattern, modern Scala 3 idioms prefer constructor-based dependency injection, `given`/`using` for capabilities, or effect systems. The cake pattern remains valid but is considered heavyweight.
6. **Self-type annotations cannot be `private`.** The self-type requirement is visible to anyone who reads the trait's signature. There is no way to hide the dependency.
7. **Name shadowing.** The self-type name (`self`, `this`, or any identifier) can shadow outer `this` references. Use distinct names (`outer =>`) to avoid confusion in nested traits.

## Beginner mental model

Think of a self-type as a **prerequisite declaration**: "I, trait `UserService`, require that whoever mixes me in also brings `HasLogger`." It is like a university course saying "requires MATH 101" -- you do not become MATH 101 by taking this course, but you cannot enroll without it.

This is different from `extends HasLogger`, which says "I *am* a HasLogger" and puts `HasLogger` in the inheritance chain. Self types keep the inheritance chains separate while ensuring the capability is present.

## Common type-checker errors

```
-- [E157] Type Error ---
  trait Repo:
    self: Database =>
    def find(id: Int): Option[Row]

  class MyRepo extends Repo
                        ^^^^
  illegal inheritance: self-type MyRepo does not conform to
  Repo's self type Repo & Database

  Fix: mix in the required trait:
    class MyRepo extends Repo with Database
```

```
-- [E007] Type Mismatch Error ---
  trait HasAuth:
    self: HasLogger =>
    def login(): Unit = log("logged in")

  val auth: HasLogger = new HasAuth with HasLogger { ... }
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  Found:    HasAuth & HasLogger
  Required: HasLogger

  Note: HasAuth is NOT a subtype of HasLogger despite the self-type.
  Fix: ascribe to the intersection type, or restructure with inheritance.
```

```
-- Error ---
  trait A:
    self: B =>
    def foo: Int = bar

  trait B:
    def bar: String

  val x = new A with B { def bar = "hello" }
  x.foo  // returns Int, but bar returns String
  ^^^^
  Found:    String
  Required: Int

  Fix: self-type gives access to B's members, but types must still align.
  The expression `bar` has type String, not Int.
```

## Use-case cross-references

- [-> UC-02](../usecases/UC02-domain-modeling.md) Modular domain services with self-type requirements
- [-> UC-10](../usecases/UC10-encapsulation.md) Encapsulating module dependencies without inheritance
- [-> UC-11](../usecases/UC11-effect-tracking.md) Capability requirements via self-type annotations
- [-> UC-14](../usecases/UC14-extensibility.md) Extensible module systems using the cake pattern

## Source anchors

- [Scala 3 Reference: Self Types](https://docs.scala-lang.org/scala3/book/domain-modeling-tools.html#traits)
- [Scala 3 Reference: Trait Composition](https://docs.scala-lang.org/scala3/book/domain-modeling-tools.html)
- [Scala Specification: Self Type Annotations](https://scala-lang.org/files/archive/spec/3.4/05-classes-and-objects.html)
