# Path-Dependent Types

> **Since:** Scala 2 (type members and path-dependent types); Scala 3 refines rules — type projections `T#Inner` restricted to concrete types

## What it is

In Scala 3, a trait or class can declare a **type member** with `type Inner`. The type of that member depends on the specific *instance* through which you access it: given `val x: Outer` and `val y: Outer`, the types `x.Inner` and `y.Inner` are distinct. This is a **path-dependent type** — the "path" (`x.` or `y.`) is part of the type identity.

Path-dependent types let you tie types to specific object identities without exposing concrete representations. An abstract `type Node` inside a `Graph` trait means each graph instance carries its own node type, and the compiler prevents mixing nodes from different graphs. This is the mechanism behind type-safe heterogeneous collections, plugin-style extensibility, and the "cake pattern" (now largely superseded by simpler idioms in Scala 3).

In Scala 3, **type projections** (`T#Inner`) are restricted: you can only project from a concrete class, not from an abstract type parameter. This closes a long-standing soundness hole in Scala 2 and makes path-dependent types the primary way to work with type members.

## What constraint it enforces

**A type member's identity depends on the runtime path (object instance) through which it is accessed. The compiler treats `a.T` and `b.T` as unrelated types unless it can prove `a` and `b` are the same object.**

- Two instances of the same class produce incompatible type members by default.
- Widening to the enclosing class's abstract type member erases the path: `Outer#Inner` (when allowed) forgets which instance.
- Type members can be abstract (no `=`), bounded (`>:` / `<:`), or concrete (`= Int`).

## Minimal snippet

```scala
trait Cage:
  type Animal
  def resident: Animal
  def admit(a: Animal): Unit

val dogCage = new Cage:
  type Animal = String        // just a name for this example
  def resident = "Rex"
  def admit(a: String) = println(s"Welcome $a")

val catCage = new Cage:
  type Animal = Int           // different concrete type
  def resident = 42
  def admit(a: Int) = println(s"Cat #$a admitted")

dogCage.admit(dogCage.resident)   // OK — types align
// dogCage.admit(catCage.resident) // error: Found catCage.Animal, Required dogCage.Animal
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type aliases** [-> catalog/T23](T23-type-aliases.md) | Type members are type aliases scoped to an instance. Abstract type members are aliases without a right-hand side — filled in by subclasses or concrete objects. |
| **Dependent function types** [-> catalog/T09](T09-dependent-types.md) | A method `def get(k: Key): k.Value` uses path-dependent types through dependent method types. Scala 3 makes these first-class with `(k: Key) => k.Value`. |
| **Encapsulation** [-> catalog/T21](T21-encapsulation.md) | Abstract type members hide representations. Clients see `graph.Node` without knowing it is `Int` internally — stronger than private constructors. |
| **Type classes** [-> catalog/T05](T05-type-classes.md) | Abstract type members are an alternative to type parameters on traits. Type members avoid "type parameter pollution" in deeply nested generic code. |
| **Match types** [-> catalog/T41](T41-match-types.md) | A type member can be defined as a match type: `type Elem = this.type match { case IntCol => Int; case StrCol => String }`. |
| **Opaque types** [-> catalog/T03](T03-newtypes-opaque.md) | Opaque types are conceptually type members whose definition is hidden outside the defining scope. They complement path-dependent types for encapsulation. |

## Gotchas and limitations

1. **Type projections restricted in Scala 3.** `T#Inner` is only allowed when `T` is a concrete class type. Writing `def foo[T <: Outer]: T#Inner` no longer compiles. Use path-dependent types (`(t: T) => t.Inner`) or match types instead.

2. **Singleton type narrowing.** To use path-dependent types on a `val`, the compiler must track the singleton type. Assigning to a `var` or widening to a supertype loses the path: `val c: Cage = dogCage` means `c.Animal` is abstract, not `String`.

3. **Type members vs type parameters — design choice.** Type members work well when the type is "output-like" (determined by the implementor). Type parameters work well when the type is "input-like" (chosen by the caller). Mixing them arbitrarily creates confusing APIs.

4. **No general type projection escape.** In Scala 2, `Cage#Animal` let you refer to "any cage's animal." In Scala 3, this is only valid for concrete outer types. For abstract cases, use existential encoding with match types or polymorphic functions.

5. **Path stability.** The path must be a stable identifier — a `val`, `object`, or `this`. Method results and `var`s are not stable paths, so `def getCage: Cage` does not give you a usable `getCage.Animal`.

6. **Equality proofs.** To pass a value from one path to a method expecting another, you may need to prove the paths are equal. Scala 3 does not have built-in path-equality witnesses; restructure code to share the same path.

## Beginner mental model

Imagine every object carries a **personal suitcase of types**. When you declare `type Animal` inside a class, each instance packs its own `Animal` type into its suitcase. The type `myDog.Animal` literally means "the Animal type inside myDog's suitcase." Two different objects have two different suitcases — even if they are instances of the same class — so their types do not mix.

## Example A — Type-safe key-value store

Each key knows its own value type. The compiler prevents storing or retrieving the wrong type.

```scala
trait Key:
  type Value
  def name: String

def intKey(n: String): Key { type Value = Int } =
  new Key { type Value = Int; def name = n }

def strKey(n: String): Key { type Value = String } =
  new Key { type Value = String; def name = n }

class Store:
  private var data: Map[String, Any] = Map.empty

  def put(k: Key)(v: k.Value): Unit =
    data = data.updated(k.name, v)

  def get(k: Key): Option[k.Value] =
    data.get(k.name).map(_.asInstanceOf[k.Value])

val age = intKey("age")
val name = strKey("name")
val store = Store()

store.put(age)(30)          // OK — age.Value is Int
store.put(name)("Alice")    // OK — name.Value is String
// store.put(age)("thirty") // error: Found String, Required age.Value (Int)
```

## Example B — Abstract type members for module-style encapsulation

```scala
trait Graph:
  type Node
  type Edge

  def nodes: Set[Node]
  def edges(n: Node): Set[Edge]
  def target(e: Edge): Node

class CityGraph extends Graph:
  type Node = String
  type Edge = (String, String, Int)   // (from, to, distance)

  private val edgeList = Set(("A", "B", 10), ("B", "C", 20))

  def nodes = edgeList.flatMap(e => Set(e._1, e._2))
  def edges(n: String) = edgeList.filter(_._1 == n)
  def target(e: (String, String, Int)) = e._2

def traverse(g: Graph)(start: g.Node): List[g.Node] =
  // The compiler ensures we only use nodes from THIS graph
  g.edges(start).map(g.target).toList

val city = CityGraph()
traverse(city)("A")          // OK — "A" is a city.Node (String)
// traverse(city)(42)         // error: Found Int, Required city.Node
```

## Example C — Dependent method types with refinements

```scala
trait TypedColumn:
  type Elem
  def get(row: Int): Elem

val ages: TypedColumn { type Elem = Int } = new TypedColumn:
  type Elem = Int
  def get(row: Int) = row * 10    // dummy

val names: TypedColumn { type Elem = String } = new TypedColumn:
  type Elem = String
  def get(row: Int) = s"user-$row"

def readCell(col: TypedColumn)(row: Int): col.Elem = col.get(row)

val a: Int    = readCell(ages)(1)     // inferred as Int
val n: String = readCell(names)(1)    // inferred as String
```

## Use-case cross-references

- [-> UC-10](../usecases/UC10-encapsulation.md) -- Hide implementations behind abstract type members; clients program against `graph.Node` without knowing the concrete representation.
- [-> UC-02](../usecases/UC02-domain-modeling.md) -- Type-safe heterogeneous collections where each key determines its value type.
- [-> UC-14](../usecases/UC14-extensibility.md) -- Abstract type members as extension points: plugins define their own node/edge/config types.
- [-> UC-13](../usecases/UC13-state-machines.md) -- Type members can track per-instance state, making state transitions path-dependent.

## Source anchors

- [Scala 3 Reference -- Abstract Type Members](https://docs.scala-lang.org/scala3/reference/new-types/type-lambdas.html)
- [Scala 3 Reference -- Dependent Function Types](https://docs.scala-lang.org/scala3/reference/new-types/dependent-function-types.html)
- [Scala 3 Reference -- Dropped: Type Projections](https://docs.scala-lang.org/scala3/reference/dropped-features/type-projection.html)
- [Scala 3 Reference -- Match Types](https://docs.scala-lang.org/scala3/reference/new-types/match-types.html)
- Martin Odersky, *Programming in Scala*, Ch. 20 — "Abstract Members"
