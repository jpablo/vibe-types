# Matchable and TypeTest

> **Since:** Scala 3.0

## What It Is

`Matchable` is a universal marker trait sitting between `Any` and the concrete root classes `AnyVal` and `AnyRef` in the Scala 3 type hierarchy. It controls which values may be used as the scrutinee of a pattern match. `TypeTest[S, T]` is a type class in `scala.reflect` that provides a safe, compiler-verified way to perform runtime type tests on abstract types -- replacing the unsound `ClassTag.unapply` mechanism from Scala 2. Together, `Matchable` restricts _where_ pattern matching is allowed, while `TypeTest` governs _how_ type tests on abstract types are performed soundly.

## What Constraint It Lets You Express

**`Matchable` prevents pattern matching from breaking type abstractions (opaque types, unbounded type parameters), and `TypeTest` ensures that runtime type checks on abstract types are sound by requiring an explicit witness rather than relying on erased class information alone.**

## Minimal Snippets

### Matchable

```scala
opaque type IArray[+T] = Array[? <: T]

val imm: IArray[Int] = ???
imm match
  case a: Array[Int] => a(0) = 1
// Warning: pattern selector should be an instance of Matchable,
//          but it has unmatchable type IArray[Int]
```

Fix by bounding a type parameter with `Matchable` when matching is needed:

```scala
def process[T <: Matchable](x: T): String = x match
  case s: String => s
  case i: Int    => i.toString
  case _         => "other"
```

### TypeTest

```scala
import scala.reflect.TypeTest

trait Peano:
  type Nat
  type Zero <: Nat
  type Succ <: Nat

  given TypeTest[Nat, Zero]
  given TypeTest[Nat, Succ]

  def divOpt(m: Nat, n: Nat)(using TypeTest[Nat, Zero], TypeTest[Nat, Succ]): Option[(Nat, Nat)] =
    n match
      case _: Zero => None           // safe -- TypeTest witnesses the check
      case s: Succ => Some(safeDiv(m, s))
```

The `Typeable[T]` alias simplifies context bounds when the source type is `Any`:

```scala
import scala.reflect.Typeable

def f[T: Typeable]: Boolean =
  "abc" match
    case _: T => true
    case _    => false

f[String] // true
f[Int]    // false
```

## Interaction with Other Features

| Feature | Interaction |
|---|---|
| **Opaque types** | `Matchable` exists precisely to protect opaque type abstractions from being circumvented via pattern matching. An opaque type is not `Matchable` unless its bound is. |
| **Unbounded type parameters** | A type parameter `T` (bounded only by `Any`) is not `Matchable`. To pattern-match on it, bound it with `T <: Matchable`. |
| **Universal equality / `equals`** | The `equals(that: Any)` override must cast `that.asInstanceOf[Matchable]` before matching, signaling that universal equality is inherently unsafe with abstract types. |
| **Multiversal equality** | `strictEquality` complements `Matchable` by turning `==` between unrelated types into a compile error, addressing the same class of abstraction-breaking problems. |
| **Transparent traits** | `Matchable` is automatically treated as transparent, so it is dropped from inferred intersection types. |
| **ClassTag (legacy)** | `TypeTest` replaces `ClassTag.unapply`. `ClassTag` only checks the class component and is unsound for parameterized or abstract types. A deprecation warning is emitted when `ClassTag` is used for type tests after Scala 3.0. |
| **Inline match** | `inline match` performs type tests at compile time and does not require `TypeTest` instances because no runtime check occurs. |

## Gotchas and Limitations

- **`Matchable` warnings are gated.** In Scala 3.x, the warning requires `-source future-migration` or higher. It will become a default warning in a future version.
- **`equals` and `Matchable`.** Because `equals` takes `Any`, every override that pattern-matches on `that` needs `that.asInstanceOf[Matchable]`. The cast always succeeds at runtime since both erase to `Object`.
- **TypeTest does not solve erasure entirely.** The compiler synthesizes `TypeTest` instances that may produce unchecked warnings if the target type has erased type parameters (e.g., `TypeTest[Any, List[Int]]`).
- **TypeTest is contravariant in S.** `TypeTest[-S, T]` means a `TypeTest[Any, T]` (i.e., `Typeable[T]`) can be used wherever a `TypeTest[S, T]` is needed.
- **Synthesized instances.** When no explicit `TypeTest` is in scope, the compiler generates one that internally does a standard class-based `isInstanceOf` check, which may be unchecked for generic types.
- **`Matchable` has no methods.** It is a pure marker trait. Methods like `getClass` and `isInstanceOf` remain on `Any` for now but may migrate to `Matchable` in the future.

## Use-Case Cross-References

- `[-> UC-03](../usecases/UC10-encapsulation.md)` Protecting opaque type invariants from pattern-match circumvention.
- `[-> UC-06](../usecases/UC13-state-machines.md)` Safe runtime dispatch on abstract type members in a cake pattern or module system.
- `[-> UC-09](../usecases/UC16-nullability.md)` ADT exhaustivity where sealed hierarchies use abstract types internally.
- `[-> UC-14](../usecases/UC08-error-handling.md)` Replacing `ClassTag`-based type tests with `TypeTest` for soundness in generic code.
- `[-> UC-08](../usecases/UC15-equality.md)` Implementing `equals` correctly under strict Matchable checking.
