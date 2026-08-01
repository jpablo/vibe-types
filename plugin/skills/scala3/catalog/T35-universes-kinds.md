# Kind Polymorphism

> **Since:** Scala 3.0

## What It Is

Kind polymorphism in Scala 3 allows type parameters to range over types of any kind -- proper types (like `Int`), unary type constructors (like `List`), binary type constructors (like `Map`), or any higher-kinded shape. This is achieved through the special type `scala.AnyKind`, which can be used as an upper bound on a type parameter. A type parameter bounded by `AnyKind` is called an _any-kinded type_ and can accept type arguments of arbitrary kinds, enabling abstractions that work uniformly across the kind spectrum.

## What Constraint It Lets You Express

**`AnyKind` lets you write definitions that are generic over the _kind_ of their type argument -- you can abstract over whether something is a plain type, a `* -> *` constructor, a `* -> * -> *` constructor, or any other shape, without committing to a particular arity.**

## Minimal Snippet

```scala
import scala.reflect.TypeTest

// A type tag that works for types of any kind
def typeInfo[T <: AnyKind]: String =
  "some type"

typeInfo[Int]              // T is a proper type (kind: *)
typeInfo[List]             // T is a unary constructor (kind: * -> *)
typeInfo[Map]              // T is a binary constructor (kind: * -> * -> *)
typeInfo[[X] =>> String]   // T is a type lambda (kind: * -> *)
```

A more practical use -- a universal `TypeTag`-like given that works across kinds:

```scala
// Type[T] in the quotes system already uses AnyKind:
//   abstract class Type[T <: AnyKind]
// This allows Type to represent Int, List, Map, etc. uniformly.

import scala.quoted.*

def showType[T <: AnyKind : Type](using Quotes): String =
  Type.show[T]
```

## Interaction with Other Features

| Feature | Interaction |
|---|---|
| **`Type[T]` (quotes)** | `Type` is declared as `Type[T <: AnyKind]`, which is the canonical use of kind polymorphism. It allows macros to handle types, type constructors, and higher-kinded types uniformly. |
| **Given instances / type classes** | Kind polymorphism enables defining given instances that work for any-kinded types. For example, a universal `Type.of` given is defined as `given of: [T <: AnyKind] => Quotes => Type[T]`. |
| **Match types** | Match type scrutinees can be any-kinded, enabling dispatch on the kind of a type argument. |
| **Type lambdas** | Type lambdas (`[X] =>> F[X]`) produce higher-kinded types that can be passed to any-kinded parameters. |
| **Opaque types** | An opaque type can have an any-kinded bound, though this is rarely needed in practice. |
| **Subtyping** | `AnyKind` is a supertype of all types regardless of their kind. It is kind-compatible with every other type but has no type parameters and no members. |

## Gotchas and Limitations

- **Severely restricted usage.** An any-kinded type variable cannot be used as the type of a value, cannot be instantiated with type parameters, and cannot appear in positions that require a proper type. The only thing you can do with it is pass it to another any-kinded type parameter.
- **No members.** `AnyKind` is a synthesized class with no members at all. It cannot be instantiated or extended (`abstract final`).
- **Not a supertype of `Any` in the usual sense.** While `AnyKind` sits above all types in the kind hierarchy, the normal type hierarchy (`Any`, `AnyVal`, `AnyRef`) remains separate. `AnyKind` is a special construct handled by the compiler.
- **Implicit resolution limitations.** Because an any-kinded type has no structure, implicit search cannot inspect it. Useful patterns typically require combining `AnyKind` bounds with other mechanisms like `Type` instances in macros.
- **The `-Yno-kind-polymorphism` flag is deprecated** as of Scala 3.7.0, has no effect, and will be removed. Kind polymorphism is now a stable feature.

## Coming from Lean

`AnyKind` is *not* the Scala counterpart of `Sort u`: the two hierarchies climb different ladders. Lean stratifies by universe **level**; `AnyKind` abstracts over **kind**, i.e. type-constructor arity.

In Lean, `Prop` and `Type u` are notation for `Sort`, related by the definitional *equalities* `Prop = Sort 0` and `Type u = Sort (u+1)`. The *typing judgments* are a separate matter and sit one step up: `Prop : Type 0`, `Type 0 : Type 1`, and in general `Type u : Type (u+1)`. That infinite tower is essential — it is what rules out `Type : Type` and Girard's paradox — and Lean lets you quantify over it with universe polymorphism (`Sort u`, `Type u` with `u` a level variable).

Scala has no universe levels at all, so `Sort u` and universe polymorphism have no Scala counterpart. There is also no Scala entity named `Type` denoting proper types: the top *proper type* is `Any`, and the code-font `Type` used elsewhere in this file is `scala.quoted.Type`, an ordinary class.

What `AnyKind` ranges over is the arity of a type constructor: `*` (`Int`), `* -> *` (`List`), `* -> * -> *` (`Map`), `(* -> *) -> *` (`[F[_]] =>> Int`), and so on — that hierarchy is unbounded too, just along a different axis. Lean needs no `AnyKind` because it spells those shapes as ordinary function types between universes: Scala's `F[_]` is simply Lean's `Type -> Type`. Kind polymorphism is a convenience for writing arity-agnostic signatures; it carries none of the consistency burden that Lean's universes do.

## Use-Case Cross-References

- `[-> UC-06](../usecases/UC13-state-machines.md)` Macro libraries that need to represent and manipulate types of any kind via `Type[T <: AnyKind]`.
- `[-> UC-11](../usecases/UC18-type-arithmetic.md)` Generic type-level programming that abstracts over type constructor arity.
- `[-> UC-05](../usecases/UC12-compile-time.md)` Quote pattern matching on higher-kinded types using `type f[X]; f` patterns.
- `[-> UC-07](../usecases/UC14-extensibility.md)` Defining universal type tags or type witnesses that work across all kinds.
