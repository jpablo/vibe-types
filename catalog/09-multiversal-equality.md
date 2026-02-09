# 09 -- Multiversal Equality

## 1. What It Is

Multiversal equality is an opt-in refinement of Scala's universal `==`/`!=` operators that uses the binary type class `CanEqual[L, R]` to control which pairs of types may be compared. In standard Scala (and Java), any two references can be compared, which silently accepts nonsensical comparisons like `"hello" == 42`. Multiversal equality makes such comparisons a compile-time error for types that declare a `CanEqual` instance, while remaining fully backward-compatible for types that have not opted in.

## 2. What Constraint It Lets You Express

**You can restrict `==` and `!=` so that only semantically meaningful comparisons compile, catching accidental cross-type equality checks at compile time.** Once a type has a reflexive `CanEqual` instance (via `derives CanEqual` or a given definition), comparisons involving that type are checked: `x == y` compiles only if a `CanEqual[T, U]` instance is available for the types of `x` and `y`. Enabling `strictEquality` extends this discipline to *all* types, removing the backward-compatibility fallback entirely.

## 3. Minimal Snippet

```scala
class Name(val value: String) derives CanEqual

val a = Name("Alice")
val b = Name("Bob")

a == b         // OK -- CanEqual[Name, Name] exists
a == "Alice"   // error: Values of types Name and String cannot be compared
```

Opting into cross-type comparison:

```scala
given CanEqual[Int, Long] = CanEqual.derived

42 == 42L      // OK
```

Full strict mode:

```scala
import scala.language.strictEquality

1 == 1         // error unless CanEqual[Int, Int] is in scope
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Type-class derivation** [-> catalog/08] | `derives CanEqual` generates a given instance with independent left and right type parameters, e.g., `CanEqual[Box[T], Box[U]]` requires `CanEqual[T, U]`. This propagates safe equality through generic wrappers. |
| **Enums and ADTs** [-> catalog/11] | Adding `derives CanEqual` to an enum ensures that cases of the same enum can be compared, but comparison with unrelated types is rejected. |
| **Given instances** [-> catalog/05] | You can define asymmetric equality (e.g., `CanEqual[A, B]` and `CanEqual[B, A]`) through explicit given definitions, controlling exactly which cross-type comparisons are allowed. |
| **Opaque types** [-> catalog/12] | An opaque type that derives `CanEqual` gets its own equality domain, independent of its underlying representation type. |
| **Collection operations** | `CanEqual` can be threaded into methods like `contains`, `indexOf`, and `diff` to prevent calling them with impossible argument types, by adding a `using CanEqual[T, U]` parameter. |

## 5. Gotchas and Limitations

- **Backward-compatibility fallback.** Without `strictEquality`, any two types that *both* lack a `CanEqual` instance can still be compared freely. The safety net only activates when at least one side has opted in. This is intentional for migration but means you get no protection for legacy types.
- **Two type parameters are essential.** `CanEqual` takes `[L, R]` rather than a single `[T]` to support the fallback rule ("neither side has a reflexive instance"). A single-parameter design would make the `Any` fallback always available, defeating the purpose.
- **Predefined instances.** The standard library ships `CanEqual` instances for numeric types, `Boolean`, `Char`, `Seq`, `Set`, and `Null`. Numeric types are cross-comparable (e.g., `Int` with `Long`). Two `Seq` subtypes are comparable if their element types are.
- **Lifting rule.** When `strictEquality` is not enabled, the compiler *lifts* types (replacing abstract types in covariant positions with their upper bound) before deciding subtype-based compatibility. This can admit comparisons that look unrelated at the surface.
- **No runtime effect.** `CanEqual` instances exist only for the type checker. At runtime, `==` still dispatches to `equals` as always.
- **Migration path.** The recommended approach is to first add `derives CanEqual` to your own types (which is safe even without `strictEquality`), then eventually enable `strictEquality` project-wide once the ecosystem has caught up.

## 6. Use-Case Cross-References

- [-> UC-02] Preventing accidental equality comparisons in domain models
- [-> UC-06] Safe equality for ADT hierarchies
- [-> UC-10] Hardening collection lookups with type-safe equality
