# Union Types (`A | B`) and Intersection Types (`A & B`)

> **Since:** Scala 3.0

## What it is

Union types and intersection types are first-class type combinators in Scala 3 that express disjunction and conjunction of types without requiring a shared supertype or a new trait definition. A union type `A | B` denotes values that are either of type `A` or of type `B`, while an intersection type `A & B` denotes values that are simultaneously of type `A` and type `B`. Together they replace Scala 2's compound types (`with`) and remove the need for ad-hoc wrapper hierarchies when expressing alternatives.

## What constraint it lets you express

**Union types let you say "this value is one of several types" without introducing a common supertype; intersection types let you say "this value satisfies all of several type constraints simultaneously."** This is the key duality: `|` widens the set of accepted values, `&` narrows it by demanding combined capabilities.

## Minimal snippet

```scala
// Intersection: combining capabilities
trait Resettable:
  def reset(): Unit

trait Growable[T]:
  def add(t: T): Unit

def f(x: Resettable & Growable[String]) =
  x.reset()
  x.add("first")

// Union: accepting alternatives without a shared supertype
case class UserName(name: String)
case class Password(hash: Int)

def help(id: UserName | Password): String = id match
  case UserName(n) => s"user: $n"
  case Password(h) => s"pass: $h"
```

## Interaction with other features

- **Pattern matching.** Union types work naturally with `match` expressions for type narrowing. The compiler checks exhaustiveness when the union members are sealed or enumerated.
- **Commutativity.** Both operators are commutative: `A & B =:= B & A` and `A | B =:= B | A`.
- **Distributivity.** Intersection distributes over union: `A & (B | C) =:= (A & B) | (A & C)`.
- **Member merging (intersection).** When both sides of `&` define a member with the same name, the member's type in the intersection is the intersection of the two member types. For covariant type constructors this simplifies naturally (e.g., `List[A] & List[B]` becomes `List[A & B]`).
- **Type inference (union).** The compiler does not infer a union type unless the type is explicitly annotated or the common supertype is a `transparent` trait. Without annotation, `if cond then a else b` is widened to the least common non-transparent supertype.
- **Transparent traits.** Declaring a parent trait as `transparent` causes the compiler to infer the union type instead of widening to the parent.
- **Match types.** Union and intersection types can appear as scrutinees or pattern types in match type definitions. [-> UC-03](../usecases/UC10-encapsulation.md)
- **Givens / type classes.** You can provide given instances for intersection types to require combined evidence. [-> UC-05](../usecases/UC12-compile-time.md)

## Gotchas and limitations

1. **Union types are not inferred by default.** Writing `val x = if cond then a else b` where `a: A` and `b: B` yields the LUB (least upper bound), not `A | B`, unless the common parent is `transparent` or the type is annotated explicitly.
2. **No members on union types.** You cannot call methods on `A | B` directly (unless both `A` and `B` share the member through a common supertype). You must narrow first via pattern matching or type tests.
3. **Intersection of conflicting concrete types.** `String & Int` is an empty type (no values inhabit it). The compiler will not warn you about this; you simply cannot construct a value.
4. **Ordering-independent but rendering-dependent.** While `A & B` and `B & A` are the same type, error messages and IDE hints may display them differently.
5. **Intersection replaces `with` in types.** Scala 2's `A with B` type syntax is deprecated in favor of `A & B`. The semantics differ: `&` is commutative, `with` was not.

## Use-case cross-references

- [-> UC-03](../usecases/UC10-encapsulation.md) Match types can branch on union/intersection scrutinees.
- [-> UC-04](../usecases/UC11-effect-tracking.md) Dependent function types can return intersection-typed results where the path-dependent member combines capabilities.
- [-> UC-05](../usecases/UC12-compile-time.md) Given instances can be defined for intersection types to require combined evidence (e.g., `given [T: Ord & Show]`).
- [-> UC-06](../usecases/UC13-state-machines.md) Context functions can use union types as the parameter type to accept alternative capability providers.
