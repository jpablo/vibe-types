# Associated Types (via Type Members)

> **Since:** Scala 2 (abstract type members); Scala 3 refines with deferred givens, match types on type members, restricted type projections

## What it is

Scala's **abstract type members** in traits and classes are the direct analogue of associated types in Rust and type families in Haskell. A trait declares `type Elem` without specifying its concrete type; each implementing class or object fills it in. The result is a type that is *determined by the implementor*, not chosen by the caller — unlike a type parameter, which is caller-selected.

In Rust, you write `trait Iterator { type Item; }`. In Scala 3, you write `trait Iterator { type Item }` — nearly identical syntax. The key difference is access: Scala uses path-dependent types (`iter.Item`) whereas Rust uses `<I as Iterator>::Item`. Scala 3 also supports **refinement types** (`Iterator { type Item = Int }`) to specify the member without exposing the concrete class, and **match types** on type members for conditional type computation.

## What constraint it enforces

**An abstract type member requires each implementor to fix a type, and the compiler tracks which concrete type belongs to each instance through path-dependent typing. Callers can constrain the member via refinements without knowing the concrete class.**

## Minimal snippet

```scala
trait Container:
  type Elem
  def head: Elem
  def add(e: Elem): Container

class IntList(val items: List[Int]) extends Container:
  type Elem = Int
  def head = items.head
  def add(e: Int) = IntList(e :: items)

class StrSet(val items: Set[String]) extends Container:
  type Elem = String
  def head = items.head
  def add(e: String) = StrSet(items + e)

// Path-dependent access: c.Elem is tied to the specific instance
def firstTwo(c: Container): (c.Elem, c.Elem) = (c.head, c.head)

// Refinement type: constrain Elem without naming the class
def intContainer(c: Container { type Elem = Int }): Int = c.head + 1
```

## Type members vs type parameters

| Criterion | Type member (`type Elem`) | Type parameter (`[Elem]`) |
|-----------|---------------------------|---------------------------|
| **Who chooses** | The implementor | The caller |
| **Visible at use site** | Only if refined or path-accessed | Always visible in the type signature |
| **Multiple appearances** | Each member is named; no positional confusion | Positional parameters can be confusing with many params |
| **Partial application** | Natural: implement some members, leave others abstract | Requires type lambdas (`[A] =>> F[A, Int]`) |
| **Best for** | "Output" types determined by the implementation | "Input" types chosen by the consumer |

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Path-dependent types** [-> catalog/T53](T53-path-dependent-types.md) | Abstract type members are accessed through paths (`x.Elem`), making them path-dependent. Two instances of the same trait have distinct member types. |
| **Type classes / givens** [-> catalog/T05](T05-type-classes.md) | Type classes can use type members as associated types: `trait Functor { type F[_]; extension [A](fa: F[A]) def map[B](f: A => B): F[B] }`. More commonly, type parameters and type members are mixed. |
| **Type aliases** [-> catalog/T23](T23-type-aliases.md) | Concrete type members (`type Elem = Int`) are type aliases scoped to the instance. Abstract type members are aliases waiting to be defined. |
| **Match types** [-> catalog/T41](T41-match-types.md) | A type member can be defined as a match type: `type Elem = this.type match { case IntCol => Int; case StrCol => String }`. |
| **Refinement types** [-> catalog/T26](T26-refinement-types.md) | Refinement types (`Container { type Elem = Int }`) let you constrain a type member without committing to a specific implementing class. |

## Gotchas and limitations

1. **Type projections restricted.** In Scala 3, `Container#Elem` is only valid when `Container` is a concrete class. For abstract types, use path-dependent types or refinements instead. This closes a Scala 2 soundness hole.

2. **No "associated type defaults" syntax.** Unlike Rust's `type Item = ()` as a default, Scala does not have a dedicated "default that can be overridden" for type members. You can simulate it with a concrete type alias in a base trait that subclasses override, but it requires `override type Elem = ...`.

3. **Widening loses the path.** Assigning `val c: Container = myIntList` forgets that `c.Elem` is `Int`. The type member becomes abstract. Preserve singleton types with `val c: myIntList.type = myIntList` or use refinements.

4. **Variance.** Type members do not carry variance annotations themselves, but bounds (`type Elem <: Number`) can achieve similar effects. Covariant/contravariant needs are better served by type parameters.

5. **Binary compatibility.** Adding, removing, or changing an abstract type member is a binary-incompatible change. Plan type members as part of your public API contract.

## Beginner mental model

Think of a type member as a **blank line on a form**. The trait defines the form with a blank labeled "Elem: ___". Each class that fills out the form writes in a concrete type. When you hold a filled-out form (an instance), the compiler can read what was written on the blank — but only through that specific form. Two different filled-out forms might have different answers, and the compiler keeps them separate.

## Example A — Rust-style Iterator with associated type

```scala
trait Iter:
  type Item
  def next(): Option[Item]

class RangeIter(start: Int, end: Int) extends Iter:
  type Item = Int
  private var current = start
  def next(): Option[Int] =
    if current < end then
      val v = current; current += 1; Some(v)
    else None

// The return type is path-dependent: iter.Item
def collectAll(iter: Iter): List[iter.Item] =
  val buf = collection.mutable.ListBuffer.empty[iter.Item]
  var x = iter.next()
  while x.isDefined do
    buf += x.get
    x = iter.next()
  buf.toList

val nums: List[Int] = collectAll(RangeIter(0, 5))
```

## Example B — Refinement types for constrained APIs

```scala
trait Encoder:
  type Input
  type Output
  def encode(in: Input): Output

// Accept only encoders that produce String output
def logEncoded(enc: Encoder { type Output = String })(in: enc.Input): Unit =
  println(enc.encode(in))

object IntToString extends Encoder:
  type Input = Int
  type Output = String
  def encode(in: Int) = in.toString

logEncoded(IntToString)(42)  // "42"
```

## Use-case cross-references

- [-> UC-14](../usecases/UC14-extensibility.md) Abstract type members serve as extension points: plugins define their own types without polluting the caller's generic signatures.
- [-> UC-10](../usecases/UC10-encapsulation.md) Abstract type members hide concrete representations, stronger than private constructors.

## Source anchors

- [Scala 3 Reference -- Abstract Type Members](https://docs.scala-lang.org/scala3/reference/new-types/type-lambdas.html)
- [Scala 3 Reference -- Dropped: Type Projections](https://docs.scala-lang.org/scala3/reference/dropped-features/type-projection.html)
- [Scala 3 Reference -- Path-Dependent Types](https://docs.scala-lang.org/scala3/reference/new-types/dependent-function-types.html)
- Martin Odersky, *Programming in Scala*, Ch. 20 — "Abstract Members"
