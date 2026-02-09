# 07 -- Extension Methods

## 1. What It Is

Extension methods let you add new methods to a type after it has been defined, without modifying its source code, subclassing it, or wrapping it. An `extension` block introduces a receiver parameter and one or more `def` members that become callable with dot syntax on values of that type. The compiler translates each extension method into a regular method whose first parameter list is the receiver, so there is no runtime overhead beyond a normal method call.

## 2. What Constraint It Lets You Express

**You can attach new operations to types you do not own, and you can make those operations available only when specific type-class evidence exists.** A plain extension adds an unconditional method; a *conditional* extension (one with a `using` clause or context bound) adds a method that is visible only when the required given instance is in scope. This is the mechanism that turns a type-class trait plus a set of given instances into a first-class dot-syntax API.

## 3. Minimal Snippet

Unconditional extension:

```scala
case class Meters(value: Double)

extension (m: Meters)
  def toFeet: Double = m.value * 3.28084

Meters(10).toFeet // OK -- 32.8084
```

Conditional (type-class) extension:

```scala
trait Ordering[T]:
  def compare(a: T, b: T): Int

extension [T](xs: List[T])(using ord: Ordering[T])
  def sorted: List[T] = xs.sortWith((a, b) => ord.compare(a, b) < 0)

// List(3, 1, 2).sorted  -- compiles only when Ordering[Int] is in scope
```

Collective extension grouping several methods:

```scala
extension [T](xs: List[T])(using Ordering[T])
  def smallest(n: Int): List[T] = xs.sorted.take(n)
  def largest(n: Int): List[T]  = xs.sorted.takeRight(n)
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Given instances / using clauses** [-> catalog/05] | A `using` clause on an extension makes the method conditional. This is the standard way to define type-class syntax (e.g., `+` available only when `Numeric[T]` exists). |
| **Opaque types** [-> catalog/12] | Extension methods are the *primary* way to define the public API of an opaque type, since you cannot add members to a type alias. |
| **Type-class derivation** [-> catalog/08] | A derived type-class instance often pairs with extension methods that expose the instance's operations via dot syntax. |
| **Implicit scope / companion objects** | An extension method defined in a companion object (or a given inside one) is automatically found by the compiler through implicit scope lookup, so users need no import. |
| **Infix / operator syntax** | Extension methods can define operators (`<`, `+:`, etc.). Right-associative operators swap the receiver and parameter, matching normal Scala operator conventions. |

## 5. Gotchas and Limitations

- **Ambiguity with existing members.** If the receiver type already defines a member with the same name, the member always wins. An extension method is tried only after normal member lookup fails.
- **Ambiguous imports.** Importing the same extension method name from two sources at the same nesting level is an error -- unless only one of the imports leads to a well-typed expansion, in which case that one is selected.
- **Type parameter placement.** Type parameters on the `extension` keyword can only be passed explicitly when the method is called in non-extension (prefix) form, e.g., `sumBy[String](list)(_.length)`. In dot-call form you can only pass the method's own type parameters.
- **No state.** Extension methods cannot add fields. They are purely syntactic sugar for external functions.
- **Collective-extension scoping.** Inside a collective `extension` block, one extension method can call another directly (the receiver is implicitly applied), which looks like a member call but is really a re-application of the shared receiver.
- **Soft keyword.** `extension` is a soft keyword: it is only recognized as such at the start of a statement followed by `[` or `(`. In other positions it is an ordinary identifier.

## 6. Use-Case Cross-References

- [-> UC-01] Type-safe builder APIs using conditional extensions
- [-> UC-03] Newtypes with opaque types and extension methods
- [-> UC-05] Domain-specific operators via extension
- [-> UC-07] Retroactive type-class instances with extension syntax
