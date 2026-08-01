# Type Aliases

> **Since:** Scala 3.0

## What it is

A **type alias** (`type X = ...`) introduces a new name for an existing type without creating a distinct type at the type-checking level. The alias is fully transparent: `X` and its right-hand side are interchangeable everywhere. Scala 3 supports simple aliases (`type Name = String`), parameterized aliases (`type Pair[A] = (A, A)`), abstract type members in traits and classes (`type Elem`), and path-dependent types where the type's identity depends on the enclosing value. Type aliases differ fundamentally from **opaque types** (`opaque type X = ...`), which create a distinct type outside the defining scope.

## What constraint it lets you express

**Type aliases let you give meaningful names to complex types, reducing repetition and improving readability, while remaining fully transparent to the type checker.** They do not introduce a new type boundary -- code using the alias and code using the underlying type are freely interchangeable. Abstract type members add a different constraint: they let a trait declare "I have a type, but I do not reveal what it is," deferring the choice to the implementor.

## Minimal snippet

**Simple alias:**

```scala
type UserName = String
type Age = Int

case class User(name: UserName, age: Age)

val u: User = User("Alice", 30)
val n: String = u.name  // OK -- UserName is transparent, it IS String
```

**Parameterized alias:**

```scala
type Pair[A] = (A, A)
type Result[A] = Either[String, A]

def divide(a: Int, b: Int): Result[Int] =
  if b == 0 then Left("division by zero") else Right(a / b)

val p: Pair[Int] = (1, 2)  // same as (Int, Int)
```

**Abstract type member:**

```scala
trait Collection:
  type Elem
  def add(e: Elem): Unit
  def elements: List[Elem]

class IntBuffer extends Collection:
  type Elem = Int
  private val buf = scala.collection.mutable.ListBuffer[Int]()
  def add(e: Int): Unit = buf += e
  def elements: List[Int] = buf.toList
```

**Path-dependent type:**

```scala
trait Graph:
  type Node
  type Edge
  def connect(from: Node, to: Node): Edge

val g1: Graph = ???
val g2: Graph = ???
// g1.Node and g2.Node are distinct types, and so are g1.Edge and g2.Edge
// val e: g1.Edge = g2.connect(???, ???)  // Found: g2.Edge / Required: g1.Edge
```

**Type alias vs. opaque type:**

```scala
// Transparent alias -- NO type safety
type Meters = Double
type Seconds = Double
val d: Meters = 3.0
val t: Seconds = d   // compiles! Meters and Seconds are both Double

// Opaque type -- full type safety, see T03
object Units:
  opaque type Meters = Double
  opaque type Seconds = Double
  // Outside: Meters and Seconds are distinct types
```

## Interaction with other features

| Feature | How it composes |
|---|---|
| **Opaque types** [-> catalog/T03](T03-newtypes-opaque.md) | Opaque types are the "type-safe sibling" of type aliases. Use a transparent alias for convenience naming; use an opaque type when you need a distinct type that prevents accidental mixing. |
| **Match types** [-> catalog/T41](T41-match-types.md) | A type alias can be defined as a match type: `type Elem[X] = X match { case List[t] => t; case Option[t] => t }`, enabling type-level pattern matching. |
| **Generics & bounds** [-> catalog/T04](T04-generics-bounds.md) | Abstract type members can carry bounds (`type T >: Cat <: Animal`), providing the same constraint power as bounded type parameters but with path-dependent resolution. |
| **Dependent types** [-> catalog/T09](T53-path-dependent-types.md) | Path-dependent types (`x.T`) arise naturally from abstract type members and form the basis of Scala's dependent typing capability. |
| **Given instances** [-> catalog/T05](T05-type-classes.md) | Given instances can be provided for type aliases. Since the alias is transparent, an instance for `String` also serves `UserName` (if `type UserName = String`). This is a feature and a footgun -- opaque types avoid this. |
| **Type lambdas** [-> catalog/T40](T40-type-lambdas.md) | Named parameterized type aliases (`type MapTo[V] = [K] =>> Map[K, V]`) are often more readable than inline type lambdas. |

## Gotchas and limitations

1. **No type safety from transparent aliases.** `type Meters = Double` and `type Seconds = Double` are both `Double` to the compiler. Use opaque types when you need distinct types. [-> catalog/T03](T03-newtypes-opaque.md)
2. **Cyclic aliases are rejected.** `type A = List[A]` is illegal -- the compiler detects the cycle. Recursive types require a class or trait definition.
3. **Abstract type members and variance.** Abstract type members cannot carry explicit `+`/`-` variance annotations. Their variance is determined by usage positions, which can be less clear than type parameter annotations.
4. **Path-dependent type identity.** Two instances of the same class produce distinct path-dependent types: `a.T` and `b.T` are unrelated even if `a` and `b` have the same runtime class. This is powerful for type safety but can surprise when you want them to be the same.
5. **Type alias names are kept in error messages.** In `Found:` / `Required:` lines the compiler normally prints the alias name rather than its right-hand side (`Required: Handler`, not `Required: String => Unit`), which hides the shape you actually have to match. Compile with `-explain` to see the expansion in the subtyping trace.
6. **`Mirror` resolution sees *through* an alias -- which is not always what you want.** Because the alias is transparent, `type P2 = Point` gives you `summon[Mirror.Of[P2]]` for free and `derived` works through the alias, resolving to `Point`'s mirror. The flip side is that an alias can never carry a *different* instance from its underlying type. An `opaque type` is the one that has no `Mirror` (`Failed to synthesize an instance of type Mirror.Of[...]`), so derivation genuinely does not apply there and you must write the given yourself.
7. **Wildcard aliases.** `type F[_] = List[Int]` is valid (the type parameter is ignored), but this can be confusing. The compiler allows it but it may produce unexpected behavior with type-class resolution.

## Beginner mental model

A type alias is a **nickname**. Just as "Bob" and "Robert" refer to the same person, `type UserName = String` means `UserName` and `String` are the same type everywhere. The compiler freely substitutes one for the other. This is useful for readability but provides no protection against mixing up values. If you want protection -- "treat this as a different type even though it is stored the same way" -- use an opaque type instead.

An abstract type member (`type Elem`) is a **promise**: "this trait has an element type, but I will not tell you what it is until someone implements me."

## Common type-checker errors

```
-- [E007] Type Mismatch Error ---
  trait Container:
    type Elem
    def get: Elem

  val c1: Container = ???
  val c2: Container = ???
  val e: c1.Elem = c2.get
                    ^^^^^^
  Found:    c2.Elem
  Required: c1.Elem

  Fix: path-dependent types from different values are distinct.
  Use a common reference or a type parameter instead.
```

```
-- [E140] Cyclic Error ---
  type Tree = List[Tree]
       ^^^^
  illegal cyclic type reference: alias List[Tree] of type Tree refers back
  to the type itself
  Run with -explain-cyclic for more details.

  Fix: use a class or enum for recursive types:
    enum Tree:
      case Leaf(value: Int)
      case Branch(children: List[Tree])
```

```
-- [E007] Type Mismatch Error ---
  type Handler = String => Unit
  val h: Handler = 42
                   ^^
  Found:    (42 : Int)
  Required: Handler

  Note: the alias is *not* expanded -- the compiler prints `Handler`, so the
  message alone does not tell you the required shape. Recompile with
  -explain to get the trace: (42 : Int) <: Handler ==> (42 : Int) <:
  String => Unit ==> Int <: String => Unit = false.
```

## Use-case cross-references

- [-> UC-02](../usecases/UC02-domain-modeling.md) Naming complex domain types for readability
- [-> UC-10](../usecases/UC10-encapsulation.md) Abstract type members for encapsulating internal representations
- [-> UC-14](../usecases/UC14-extensibility.md) Path-dependent types for module-level type safety
- [-> UC-18](../usecases/UC18-type-arithmetic.md) Parameterized type aliases for type-level computation building blocks

## Source anchors

- [Scala 3 Reference: Type Aliases](https://docs.scala-lang.org/scala3/reference/new-types/type-lambdas.html)
- [Scala 3 Reference: Abstract Type Members](https://docs.scala-lang.org/scala3/book/types-abstract.html)
- [Scala 3 Reference: Opaque Types](https://docs.scala-lang.org/scala3/reference/other-new-features/opaques.html)
- [Scala 3 Reference: Path-Dependent Types](https://docs.scala-lang.org/scala3/book/types-dependent.html)
