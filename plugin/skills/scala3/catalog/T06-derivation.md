# 08 -- Type-Class Derivation

> **Since:** Scala 3.0

## 1. What It Is

Type-class derivation is a compiler-supported mechanism that automatically generates given instances for type classes on algebraic data types. By writing `derives TC` on a class, trait, enum, or object, the compiler emits a given definition in the companion object that delegates to `TC.derived`. The `derived` method typically inspects the type's structure at compile time through a `Mirror` instance -- a compiler-generated type-level description of a type's product fields or sum alternatives -- and assembles a correct type-class implementation without any boilerplate from the data-type author.

## 2. What Constraint It Lets You Express

**You can require that a type-class instance exists for every product/sum type that declares it, with the implementation generated entirely from the type's compile-time structure.** The `derives` clause shifts the obligation: instead of hand-writing a given for `Eq[MyTree]`, `Ordering[MyTree]`, or `Show[MyTree]`, you declare the intent and let the compiler synthesize the instances. This guarantees structural consistency -- the derived instance always reflects the current set of fields or cases -- and it fails at compile time when a constituent type lacks the required instance.

## 3. Minimal Snippet

```scala
// Type-class trait with a derived entry point
trait Eq[T]:
  def eqv(x: T, y: T): Boolean

object Eq:
  // 'derived' uses Mirror to generate the implementation
  inline def derived[T](using scala.deriving.Mirror.Of[T]): Eq[T] = ??? // macro or inline logic

// Data type opting in
enum Tree[T] derives Eq:
  case Leaf(value: T)
  case Branch(left: Tree[T], right: Tree[T])

// The compiler generates in Tree's companion:
//   given [T: Eq] => Eq[Tree[T]] = Eq.derived
```

Manual derivation for types you do not own:

```scala
given [T: Ordering] => Ordering[Option[T]] = Ordering.derived
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Mirror types** | `Mirror.Product` exposes field types (`MirroredElemTypes`) and labels; `Mirror.Sum` exposes case types and an `ordinal` method. Derivation logic pattern-matches on these mirrors to build instances structurally. |
| **Inline / metaprogramming** [-> catalog/17] | The `derived` method is usually `inline def`, using `inline match`, `summonInline`, and `erasedValue` to recurse over tuple-encoded element types at compile time. |
| **Enums and ADTs** [-> catalog/11] | `derives` is especially natural on `enum` types: the compiler generates `Mirror.Sum` for the enum and `Mirror.Product` for each case, enabling fully automatic derivation. |
| **Context bounds / given instances** [-> catalog/05] | A derived instance for `Tree[T]` automatically requires `[T: TC]` when the type class parameter has kind `*`. This propagates constraints downward through the type structure. |
| **CanEqual** [-> catalog/09] | `CanEqual` has special derivation rules: it generates a two-parameter instance with independent left/right type parameters, enabling cross-type equality checking within a sum hierarchy. |

## 5. Gotchas and Limitations

- **Mirror availability.** Mirrors are generated automatically for enums, enum cases, case objects, and (conditionally) case classes and sealed hierarchies. Non-sealed traits, classes without a visible constructor, and Java classes cannot have mirrors synthesized.
- **Recursive types.** The lazy `val` pattern in `derived` (e.g., `lazy val elemInstances = ...`) is essential to prevent infinite expansion when a product field refers back to the enclosing sum type.
- **Compile-time cost.** Because `derived` is typically `inline`, heavy use across many types can increase compilation time. Libraries like Shapeless 3 mitigate this by amortizing the inline work.
- **Single type parameter only.** Standard derivation works for type classes with a single type parameter (plus the special case of `CanEqual`). Multi-parameter type classes cannot be derived through the built-in mechanism.
- **Kind matching.** When the type class's parameter and the deriving type have different kinds, the compiler uses type lambdas to align them. This can produce surprising generated signatures if the kind structure is complex.
- **No runtime footprint (by default).** Mirror type members are pure types with no runtime representation unless explicitly used. This keeps the feature zero-cost when instances are resolved at compile time.

## 6. Use-Case Cross-References

- [-> UC-04](../usecases/UC11-effect-tracking.md) Auto-deriving codecs (JSON, binary) for domain models
- [-> UC-06](../usecases/UC13-state-machines.md) Structural equality and ordering for ADTs
- [-> UC-09](../usecases/UC16-nullability.md) Generic programming over product/sum shapes
- [-> UC-12](../usecases/UC19-serialization.md) Compile-time schema generation from case class mirrors
