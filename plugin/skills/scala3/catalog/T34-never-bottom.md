# Nothing & Bottom Type

> **Since:** Scala 3.0 (inherited from Scala 2; semantics unchanged) | **Latest changes:** Scala 3.3 (`-Yexplicit-nulls` stabilized)

## What it is

`Nothing` is Scala's **bottom type**: it is a subtype of every other type and has no inhabitants -- no value can ever have type `Nothing`. Expressions typed as `Nothing` must diverge (throw an exception, loop forever, or call `sys.error`). Because `Nothing` is a subtype of everything, it serves as the identity element for covariant type parameters: an empty `List[Nothing]` is assignable to `List[Int]`, `List[String]`, or any `List[A]`. The related `Null` type is the type of the `null` literal; under standard Scala it is a subtype of all reference types (but not value types), and under the explicit-nulls flag (`-Yexplicit-nulls`) it is removed from the subtype hierarchy, making `null` assignment a compile error without an explicit `T | Null` union.

## What constraint it lets you express

**`Nothing` lets the type system express computations that never produce a value, while remaining type-compatible with any context.** A method returning `Nothing` can appear wherever any type is expected -- in an `if/else` branch, as a collection element, or as a default case -- without breaking type inference. This makes `throw`, `???`, and non-terminating loops composable with any surrounding code. `Null` (with explicit nulls) lets you express at the type level whether a reference can be absent, shifting null-safety from runtime to compile time.

## Minimal snippet

**`Nothing` as the return type of divergent expressions:**

```scala
def fail(msg: String): Nothing = throw RuntimeException(msg)

// Nothing is compatible with any expected type:
val x: Int = if true then 42 else fail("unreachable")
val s: String = ???   // ??? : Nothing, compiles in any position
```

**`Nothing` in empty collections (covariant widening):**

```scala
val empty: List[Nothing] = Nil
val ints: List[Int] = empty       // OK: List[Nothing] <: List[Int]
val strs: List[String] = Nil      // Nil: List[Nothing] <: List[String]

// This works because List is covariant: List[+A]
// and Nothing <: Int, so List[Nothing] <: List[Int]
```

**`???` as a typed hole:**

```scala
def complexAlgorithm(data: List[Int]): Map[String, List[Double]] =
  ???   // compiles -- ??? : Nothing <: Map[String, List[Double]]
```

**`Null` type and explicit nulls:**

```scala
// With -Yexplicit-nulls:
val s: String = null        // error: Found Null, Required String
val s2: String | Null = null // OK: Null is part of the union

def fromJava(s: String | Null): Option[String] =
  if s != null then Some(s) else None
```

**`Nothing` in covariant return widening:**

```scala
enum Opt[+A]:
  case Some(value: A)
  case Non                // Non extends Opt[Nothing]

val none: Opt[Nothing] = Opt.Non
val intOpt: Opt[Int] = none   // OK: Opt[Nothing] <: Opt[Int]
val strOpt: Opt[String] = Opt.Non  // same: widens to any Opt[A]
```

## Interaction with other features

| Feature | How it composes |
|---|---|
| **Variance** [-> catalog/T08](T08-variance-subtyping.md) | `Nothing` is the bottom of the subtype lattice, so covariant containers (`List[+A]`, `Option[+A]`) can hold `Nothing` and widen to any element type. Contravariant containers reverse this: `Printer[Nothing]` is the *top* of the `Printer` hierarchy. |
| **Union / intersection types** [-> catalog/T02](T02-union-intersection.md) | `A | Nothing` simplifies to `A` (Nothing is the identity for unions). `A & Nothing` simplifies to `Nothing` (Nothing absorbs intersections). Under explicit nulls, `String | Null` is the idiomatic nullable type. |
| **Enums / ADTs** [-> catalog/T01](T01-algebraic-data-types.md) | Singleton enum cases with no type parameter (like `None`, `Nil`) extend the parent with `Nothing` as the type argument, enabling covariant widening. |
| **Generics & bounds** [-> catalog/T04](T04-generics-bounds.md) | `Nothing` satisfies any upper bound: `Nothing <: A` for all `A`. This means `Nothing` can be substituted for any bounded type parameter. Lower bounds `A >: Nothing` are always satisfied and thus vacuous. |
| **Type aliases** [-> catalog/T23](T23-type-aliases.md) | `type Never = Nothing` is a valid transparent alias. Libraries sometimes define `type Absurd = Nothing` for documentation purposes. |
| **Null safety** [-> catalog/T13](T13-null-safety.md) | Under `-Yexplicit-nulls`, `Null` is decoupled from the reference type hierarchy. Only `T | Null` can hold `null`, making nullable APIs explicit at the type level. |

## Gotchas and limitations

1. **`Nothing` has no values.** You cannot create a value of type `Nothing`. Any attempt to do so (e.g., `val x: Nothing = ???`) will throw at runtime. `Nothing` is useful only as a type, never as a value.
2. **Type inference and `Nothing`.** When the compiler cannot infer a type parameter, it sometimes defaults to `Nothing`, producing confusing errors downstream. For example, `List()` infers `List[Nothing]`, which may cause type mismatches when elements are added later.
3. **`Null` vs. `None` vs. `Nothing`.** These three are commonly confused. `Null` is the type of `null` (a value exists: `null`). `Nothing` has no values at all. `None` is a value of type `Option[Nothing]`. They sit at different levels: `Nothing <: Null <: AnyRef` (without explicit nulls).
4. **Explicit nulls is not the default.** The `-Yexplicit-nulls` flag must be enabled explicitly. Without it, `null` can be assigned to any reference type, and `Null` remains a subtype of all `AnyRef` subtypes.
5. **`throw` is an expression of type `Nothing`.** In Scala 3, `throw` is an expression, not a statement. Its type is `Nothing`, which is why `if cond then value else throw ...` type-checks: the `else` branch has type `Nothing`, which widens to the `then` branch's type.
6. **Java interop and `null`.** Java methods routinely return `null`. With explicit nulls, their return types are widened to `T | Null`, requiring explicit null checks. Without explicit nulls, the `null` flows through unchecked.
7. **`Nothing` and covariant type parameter defaults.** Libraries that define `type F[+A] = ...` may use `Nothing` as a default. For instance, `Either[Nothing, Int]` represents a right-biased value with no left case. Accidentally using `Nothing` (from failed inference) can mask logic errors.

## Beginner mental model

Think of `Nothing` as the **empty type** -- a type with zero possible values. It is the type-system equivalent of "this can never happen." Because it has no values, it is safe to pretend it is any type at all (a promise that is never called upon cannot be broken). This is why `throw` and `???` can appear anywhere: they promise to return any type, and they keep that promise by never returning at all.

In the type hierarchy:
- `Any` is at the top (supertype of everything).
- `Nothing` is at the bottom (subtype of everything).
- Every type sits between them: `Nothing <: Int <: AnyVal <: Any`.

`Null` is similar but narrower: it is the bottom of the *reference type* hierarchy (`Null <: String <: AnyRef <: Any`), and it has exactly one value: `null`.

## Common type-checker errors

```
-- [E007] Type Mismatch Error ---
  val xs = List()
  xs.head + 1
  ^^^^^^^^
  Found:    Nothing
  Required: Int

  Fix: the empty List() was inferred as List[Nothing].
  Provide a type annotation: val xs = List.empty[Int]
```

```
-- [E007] Type Mismatch Error ---  (with -Yexplicit-nulls)
  val name: String = javaObject.getName()
                     ^^^^^^^^^^^^^^^^^^^^
  Found:    String | Null
  Required: String

  Fix: handle the null case explicitly:
    val name: String = Option(javaObject.getName()).getOrElse("unknown")
    // or: val name: String = javaObject.getName().nn
```

```
-- [E007] Type Mismatch Error ---
  def absurd(n: Nothing): Int = n + 1
                                ^^^^^
  value + is not a member of Nothing

  Note: Nothing has no members of its own (it is abstract and uninhabited).
  However, the expression compiles if you ascribe: (n: Int) + 1
  -- but this method can never be called, so the point is moot.
```

```
-- [E172] Type Error ---
  val x: Nothing = 42
                   ^^
  Found:    Int
  Required: Nothing

  Fix: Nothing has no values. You cannot assign a value to Nothing.
  If you want a divergent expression, use throw or ???.
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) Using Nothing to represent impossible states in sealed hierarchies
- [-> UC-02](../usecases/UC02-domain-modeling.md) Empty collection types and covariant widening in domain models
- [-> UC-08](../usecases/UC08-error-handling.md) `Nothing` return type for error-handling functions that always throw
- [-> UC-16](../usecases/UC16-nullability.md) `Null` type and explicit nulls for null-safe APIs
- [-> UC-17](../usecases/UC17-variance.md) Bottom type interaction with variance in generic container design

## Source anchors

- [Scala 3 Reference: Type Hierarchy](https://docs.scala-lang.org/scala3/book/types-introduction.html)
- [Scala 3 Reference: Explicit Nulls](https://docs.scala-lang.org/scala3/reference/experimental/explicit-nulls.html)
- [Scala API: Nothing](https://www.scala-lang.org/api/3.x/scala/Nothing.html)
- [Scala API: Null](https://www.scala-lang.org/api/3.x/scala/Null.html)
