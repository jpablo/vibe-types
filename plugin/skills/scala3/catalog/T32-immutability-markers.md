# Immutability Markers

> **Since:** Scala 1.0 (`val`, `final`) | Scala 3 continues and strengthens these

## What it is

Scala makes immutability the default: `val` declares an unreassignable binding, case class parameters are `val` by default, and the standard library favors immutable collections. Scala 3 adds further guardrails with stricter `sealed` and `final` checking. The key mechanisms:

- **`val` vs `var`** — `val` prevents rebinding after initialization. This is the bread-and-butter immutability marker and the idiomatic default.
- **`final`** — prevents override in subclasses (on members) or subclassing entirely (on classes). Unlike Java, `final` in Scala also prevents `val` from being overridden by a lazy val or another val with a different initializer.
- **`sealed`** — restricts extension to the same file, enabling exhaustive matching and closed hierarchies.
- **Case classes** — parameters are `val` by default; instances have structural equality and `copy` for functional updates instead of mutation.
- **Immutable collections** — `scala.collection.immutable.*` is imported by default. The `List`, `Map`, `Set` you use out of the box are immutable.

## What constraint it enforces

**`val` prevents rebinding; `final` prevents override and subclassing; `sealed` prevents extension outside the file. Together they enforce immutability at the binding, member, and hierarchy levels — all checked by the compiler, not just the type checker.**

## Minimal snippet

```scala
val x = 42
// x = 43         // compile error: Reassignment to val

final class Config(val host: String, val port: Int)
// class MyConfig extends Config("", 0)  // compile error: cannot extend final class

class Base:
  final def core: Int = 42

class Sub extends Base:
  // override def core: Int = 0  // compile error: cannot override final member
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **ADTs / enums** [-> T01](T01-algebraic-data-types.md)(T01-algebraic-data-types.md) | Enum cases are implicitly `final` and `val`-like. Each case is a fixed value; adding `sealed` to the enum prevents external extension. |
| **Opaque types** [-> T03](T03-newtypes-opaque.md)(T03-newtypes-opaque.md) | Opaque type aliases are immutable by design — there's no `var` equivalent for type aliases. The underlying value cannot be modified without going through the companion. |
| **Case classes** [-> catalog/T31](T31-record-types.md) | Case class parameters are `val` by default. Use `copy` for functional updates: `user.copy(name = "Alice")` creates a new instance instead of mutating. |
| **Encapsulation** [-> T21](T21-encapsulation.md)(T21-encapsulation.md) | Combine `private` with `val` and `final` for defense in depth: private vals cannot be accessed externally, final prevents override internally. |
| **Extension methods** [-> T19](T19-extension-methods.md)(T19-extension-methods.md) | Extension methods cannot override existing `final` methods — the compiler rejects ambiguity. |

## Gotchas and limitations

1. **`val` does not mean deeply immutable.** A `val xs = ArrayBuffer(1, 2, 3)` prevents rebinding `xs`, but the buffer contents can still be mutated. For deep immutability, use immutable collections (`List`, `Vector`, `Map`).

2. **`var` in case classes.** You *can* write `case class Foo(var x: Int)`, but this is strongly discouraged — it breaks the assumptions of `equals`, `hashCode`, and `copy`. Prefer `val` and `copy`.

3. **`lazy val` is a `val`.** Once initialized, a `lazy val` cannot be reassigned. But initialization is deferred and happens at most once — this is immutability with delayed evaluation, not mutability.

4. **`final` on `val` is sometimes redundant.** In a `final class`, all members are effectively final. In a non-final class, marking a `val` as `final` prevents subclass override — useful but sometimes forgotten.

5. **Immutable collections aren't zero-cost.** Immutable data structures use structural sharing (persistent data structures), which is efficient but not free. For hot paths with millions of updates, consider `ArraySeq` or local `Array` with controlled scope.

6. **`sealed` ≠ `final`.** A `sealed trait` can be extended within the same file (enabling exhaustive matching). A `final class` cannot be extended at all. They serve different purposes.

## Beginner mental model

Think of Scala's immutability as **layered defenses**:

- **`val`** = "this name always points to the same thing" (binding-level)
- **`final`** = "subclasses cannot change this" (hierarchy-level)
- **`sealed`** = "only this file can add variants" (extension-level)
- **Immutable collections** = "the contents cannot change either" (data-level)

Python's `Final` is closest to Scala's `val` + `final`, but Python only enforces it via the type checker (runtime ignores it). Scala enforces all of these at the compiler level — there's no way to bypass `val` without reflection or `unsafe`.

## Example A — Immutable configuration

```scala
final case class DbConfig(
  host: String,       // val by default — cannot reassign
  port: Int,
  maxConnections: Int
)

val config = DbConfig("localhost", 5432, 10)
// config.host = "remote"             // compile error: reassignment to val
// config = DbConfig("remote", 5432, 10)  // compile error: reassignment to val

val updated = config.copy(host = "remote")  // functional update — new instance
```

## Example B — Sealed hierarchy with final cases

```scala
sealed trait Permission
final case class Read(resource: String)    extends Permission
final case class Write(resource: String)   extends Permission
final case object Admin                    extends Permission

// class SuperAdmin extends Permission  // compile error: sealed, cannot extend here

def describe(p: Permission): String = p match
  case Read(r)  => s"read $r"
  case Write(r) => s"write $r"
  case Admin    => "full access"
  // compiler warns if a case is missing
```

## Common type-checker errors and how to read them

### `Reassignment to val`

```
-- [E052] Type Error:
1 | x = 43
  |     ^^
  | Reassignment to val x
```

**Meaning:** You tried to reassign a `val`. Use `var` if mutation is intended, or create a new binding with a different name.

### `Cannot extend final class`

```
-- [E093] Type Error:
1 | class Sub extends FinalClass
  |                   ^^^^^^^^^^
  | class FinalClass cannot be extended
```

**Meaning:** The class is marked `final`. If you need to extend it, remove `final` (or use composition instead of inheritance).

### `Cannot override final member`

```
-- [E164] Type Error:
2 | override def core: Int = 0
  |              ^^^^
  | Cannot override final member core in class Base
```

**Meaning:** The member is `final` in the parent class. You cannot change its implementation in subclasses.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Immutable values prevent state corruption; `sealed` enables exhaustive matching.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Immutable case classes model domain entities safely.
- [-> UC-10](../usecases/UC10-encapsulation.md) — `final` + `private` + `val` form defense-in-depth encapsulation.

## Source anchors

- [Scala 3 Reference — Final](https://docs.scala-lang.org/scala3/reference/other-new-features/final.html)
- [Scala 3 Book — Variables and Data Types](https://docs.scala-lang.org/scala3/book/taste-vars-data-types.html)
- [Scala 3 Reference — Sealed Classes](https://docs.scala-lang.org/scala3/reference/other-new-features/sealed-classes.html)
