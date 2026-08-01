# Immutability Markers

> **Since:** Scala 1.0 (`val`, `final`) | Scala 3 continues and strengthens these

## What it is

Scala makes immutability the default: `val` declares an unreassignable binding, case class parameters are `val` by default, and the standard library favors immutable collections. Scala 3 adds further guardrails with stricter `sealed` and `final` checking. The key mechanisms:

- **`val` vs `var`** — `val` prevents rebinding after initialization. This is the bread-and-butter immutability marker and the idiomatic default.
- **`final`** — prevents override in subclasses (on members) or subclassing entirely (on classes). Scala members are genuinely *overridden*, not hidden as Java fields are, so `final` on a `val` is what stops a subclass from supplying a different initializer. (It is not what stops a `lazy val` from overriding a strict `val` — that is rejected outright, `final` or not: [E164] "lazy value … may not override a non-lazy value".) On a `val` without a type ascription, `final` additionally makes the definition a compile-time constant — see gotcha 4.
- **`sealed`** — restricts extension to the same file, enabling exhaustive matching and closed hierarchies.
- **Case classes** — parameters are `val` by default; instances have structural equality and `copy` for functional updates instead of mutation.
- **Immutable collections** — the default collections are immutable. Only `java.lang.*`, `scala.*` and `Predef.*` are auto-imported; they alias the immutable `List`, `Map`, `Set`, `Vector` and `Seq`, which is why those are immutable out of the box. `scala.collection.immutable.*` as a whole is *not* auto-imported — `Queue`, `TreeMap`, `SortedSet` and friends still need an explicit `import scala.collection.immutable.*`.

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

class Sub extends Base
  // override def core: Int = 0  // compile error: cannot override final member
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **ADTs / enums** [-> T01](T01-algebraic-data-types.md)(T01-algebraic-data-types.md) | Enum cases are implicitly `final` and `val`-like. Each case is a fixed value; adding `sealed` to the enum prevents external extension. |
| **Opaque types** [-> T03](T03-newtypes-opaque.md)(T03-newtypes-opaque.md) | Opaque type aliases are immutable by design — there's no `var` equivalent for type aliases. The underlying value cannot be modified without going through the companion. |
| **Case classes** [-> catalog/T31](T31-record-types.md) | Case class parameters are `val` by default. Use `copy` for functional updates: `user.copy(name = "Alice")` creates a new instance instead of mutating. |
| **Encapsulation** [-> T21](T21-encapsulation.md)(T21-encapsulation.md) | Combine `private` with `val` and `final` for defense in depth: private vals cannot be accessed externally, final prevents override internally. |
| **Extension methods** [-> T19](T19-extension-methods.md)(T19-extension-methods.md) | An extension method never overrides a member: a same-named member always wins, `final` or not, so the extension is silently unreachable. Nothing is rejected — the code compiles and runs the member. The compiler only flags it with an informational `[E194] Potential Issue Warning`: "Extension method `size` will never be selected from type `Box` because `Box` already has a member with the same name and compatible parameter types." |

## Gotchas and limitations

1. **`val` does not mean deeply immutable.** A `val xs = ArrayBuffer(1, 2, 3)` prevents rebinding `xs`, but the buffer contents can still be mutated. For deep immutability, use immutable collections (`List`, `Vector`, `Map`).

2. **`var` in case classes.** You *can* write `case class Foo(var x: Int)`, but this is strongly discouraged — it breaks the assumptions of `equals`, `hashCode`, and `copy`. Prefer `val` and `copy`.

3. **`lazy val` is a `val`.** Once initialized, a `lazy val` cannot be reassigned. But initialization is deferred and happens at most once — this is immutability with delayed evaluation, not mutability.

4. **`final` on a `val` is *not* redundant, even inside a `final class`.** It does two jobs, and only the first one becomes moot when the class cannot be extended. The second is type inference: a `final val` with **no type ascription** is inferred at the *constant singleton type* of its right-hand side, where a plain `val` widens to the underlying type. That difference survives inside a `final class` — `final` is the constant-folding marker, not a redundant override guard. Adding an ascription switches it back off:

   ```scala
   final class Limits:
     final val Max = 100        // inferred type is the constant type (100 : Int)
     val soft = 100             // inferred type is Int
     final val Hard: Int = 100  // ascription suppresses it — plain Int again

   val exact: 100 = (new Limits).Max   // compiles: Max really is (100 : Int)
   ```

   Constant-typed `final val`s are what make values usable as literal types (and as Java-style compile-time constants), so dropping `final` — or ascribing a type — is a real change in meaning, not a style choice.

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

// `sealed` restricts extension to THIS file — and this *is* that file, so the
// following is legal and compiles. Nothing is rejected here:
class SuperAdmin extends Permission

def describe(p: Permission): String = p match
  case Read(r)  => s"read $r"
  case Write(r) => s"write $r"
  case Admin    => "full access"
  // ...and the only consequence is a non-fatal warning:
  //   [E029] Pattern Match Exhaustivity Warning: match may not be exhaustive.
  //   It would fail on pattern case: _: SuperAdmin
```

The sharp edge is that `sealed` buys you nothing *within* the defining file: a
stray subclass added next to the hierarchy quietly defeats exhaustiveness
checking everywhere, and only a warning says so. The rejection appears only
from a **second file**, where `class SuperAdmin extends Permission` fails with
`[E112] Syntax Error: Cannot extend sealed trait Permission in a different
source file`. Keep sealed hierarchies in a file that contains
nothing but their cases, and treat E029 as an error (`-Werror`) if you rely on
exhaustiveness. See gotcha 6.

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
-- [E093] Syntax Error:
1 | class Sub extends FinalClass
  |       ^
  | class Sub cannot extend final class FinalClass
```

**Meaning:** The class is marked `final`. If you need to extend it, remove `final` (or use composition instead of inheritance).

### `Cannot override final member`

```
-- [E164] Declaration Error:
2 |   override def core: Int = 0
  |                ^
  | error overriding method core in class Base of type => Int;
  |   method core of type => Int cannot override final member method core in class Base
```

**Meaning:** The member is `final` in the parent class. You cannot change its implementation in subclasses. E164 is the general *override-declaration* error, so it also covers the related case where a `lazy val` tries to override a strict `val` — there the second line reads "lazy value `v` of type Int may not override a non-lazy value", and it is rejected whether or not the parent `val` is `final`.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Immutable values prevent state corruption; `sealed` enables exhaustive matching.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Immutable case classes model domain entities safely.
- [-> UC-10](../usecases/UC10-encapsulation.md) — `final` + `private` + `val` form defense-in-depth encapsulation.

## Source anchors

- [Scala 3 Reference — Final](https://docs.scala-lang.org/scala3/reference/other-new-features/final.html)
- [Scala 3 Book — Variables and Data Types](https://docs.scala-lang.org/scala3/book/taste-vars-data-types.html)
- [Scala 3 Reference — Sealed Classes](https://docs.scala-lang.org/scala3/reference/other-new-features/sealed-classes.html)
