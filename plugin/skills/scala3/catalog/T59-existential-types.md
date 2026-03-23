# Existential Types

> **Since:** Scala 2 (`forSome` syntax, removed in Scala 3); Scala 3 uses abstract type members, wildcard types (`?`), and path-dependent types for existential encoding

## What it is

An existential type says "there exists some type `T` satisfying certain bounds, but I will not tell you which one." In Scala 3, the explicit `forSome` syntax from Scala 2 has been removed, but the concept lives on through three mechanisms: **abstract type members** (`trait Box { type T; val value: T }`), **wildcard types** (`List[?]` meaning "a list of some unknown element type"), and **path-dependent types** where the concrete type is hidden behind an instance path.

Abstract type members are the most powerful encoding. A `trait Container { type Elem; def get: Elem }` hides the concrete `Elem` from clients. Each instance carries its own existentially-quantified element type. Wildcard types (`?`) are syntactic shorthand for existential positions in generic types -- `Map[String, ?]` means "a map from strings to some unknown value type."

## What constraint it enforces

**An existential type hides the concrete type from the consumer. The compiler ensures that values of the hidden type can only be used through the abstract interface -- you cannot cast, inspect, or assume anything about the hidden type beyond its declared bounds.**

- Abstract type members prevent clients from depending on the concrete representation.
- Wildcard `?` prevents extracting elements at a concrete type without evidence.
- Path-dependent types tie the existential to a specific instance, preventing cross-instance mixing.

## Minimal snippet

```scala
trait Box:
  type T
  val value: T
  def show: String

def mkBox[A](v: A)(using s: Show[A]): Box =
  new Box:
    type T = A
    val value = v
    def show = s.show(v)

val b: Box = mkBox(42)
// val n: Int = b.value  // error: found b.T, required Int
println(b.show)          // OK — uses the abstract interface
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Path-dependent types** [-> catalog/T53](T53-path-dependent-types.md) | Path-dependent types are Scala 3's primary existential encoding. `b.T` is existentially hidden unless you know `b`'s concrete type. |
| **Type aliases** [-> catalog/T23](T23-type-aliases.md) | Abstract type members (`type T`) are type aliases without a right-hand side. They become concrete when a subclass or object provides `type T = Int`. |
| **Opaque types** [-> catalog/T03](T03-newtypes-opaque.md) | Opaque types hide their definition outside the defining scope -- a form of existential hiding with zero boxing overhead. |
| **Variance** [-> catalog/T08](T08-variance-subtyping.md) | Wildcards interact with variance: `List[? <: Animal]` is a covariant existential. The bounds on `?` mirror the variance of the type parameter. |
| **Match types** [-> catalog/T41](T41-match-types.md) | Match types can deconstruct existentially-hidden types when enough information is available, recovering the concrete type at compile time. |

## Gotchas and limitations

1. **No `forSome` in Scala 3.** The Scala 2 syntax `List[T] forSome { type T }` is gone. Use `List[?]` for simple cases or abstract type members for full existential encoding.

2. **Type projections restricted.** `Box#T` (accessing the abstract type member without a path) is forbidden for abstract types in Scala 3. You must go through a specific instance: `val b: Box = ...; b.T`.

3. **Wildcards lose information.** `val xs: List[?] = List(1, 2, 3)` forgets that the elements are `Int`. To recover the type, you need pattern matching with a type test, which involves unchecked casts at runtime.

4. **No direct existential packing/unpacking.** Unlike Haskell's `ExistentialQuantification` or ML's `pack`/`unpack`, Scala has no explicit existential introduction form. You create existentials by widening to a supertype with an abstract member.

5. **Equality across existentials is tricky.** Two `Box` values may have different hidden types, so `b1.value == b2.value` may not compile or may use `Any`-level equality. Structure code to compare within a single existential scope.

## Beginner mental model

Think of an existential type as a **sealed envelope**. The sender puts a value inside (say, an `Int`) and seals it. The envelope's label says "contains something with a `show` method" but not what concrete type is inside. The receiver can call `show` on the contents without opening the envelope (without knowing the concrete type). They cannot reach in and treat the contents as an `Int` -- the seal enforces abstraction.

## Example A -- Heterogeneous collection with existential elements

```scala
trait Showable:
  type T
  val value: T
  def display: String

def wrap[A](v: A)(f: A => String): Showable =
  new Showable:
    type T = A
    val value = v
    def display = f(v)

val items: List[Showable] = List(
  wrap(42)(_.toString),
  wrap("hello")(identity),
  wrap(3.14)(d => f"$d%.1f")
)

items.foreach(s => println(s.display))  // 42, hello, 3.1
// items.head.value + 1                 // error: found items.head.T, required Int
```

## Example B -- Wildcard types for type-erased containers

```scala
def printLength(xs: List[?]): Unit =
  println(s"length = ${xs.length}")

printLength(List(1, 2, 3))       // OK — List[Int] widens to List[?]
printLength(List("a", "b"))      // OK — List[String] widens to List[?]

def firstElement(xs: List[?]): Any =
  xs.head   // returns Any — the element type is existentially hidden

// def typedFirst(xs: List[?]): Int = xs.head  // error: found Any, required Int
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Existential types hide internal representations, preventing clients from constructing invalid states by depending on concrete types.
- [-> UC-10](../usecases/UC10-encapsulation.md) -- Abstract type members provide the strongest encapsulation in Scala, hiding the representation behind an existential boundary.
- [-> UC-13](../usecases/UC13-state-machines.md) -- Existentially-typed state values can hide the current state's type while exposing only valid transitions through the abstract interface.

## Source anchors

- [Scala 3 Reference -- Dropped: Existential Types](https://docs.scala-lang.org/scala3/reference/dropped-features/existential-types.html)
- [Scala 3 Reference -- Wildcard Arguments in Types](https://docs.scala-lang.org/scala3/reference/changed-features/wildcards.html)
- [Scala 3 Reference -- Abstract Type Members](https://docs.scala-lang.org/scala3/reference/new-types/type-lambdas.html)
- Martin Odersky, *Programming in Scala*, Ch. 20 -- "Abstract Members"
