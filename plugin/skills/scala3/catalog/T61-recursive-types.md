# Recursive Types

> **Since:** Scala 2 (sealed trait hierarchies); Scala 3 (`enum` syntax since 3.0)

## What it is

A recursive type is a type whose definition refers to itself. In Scala 3, the primary mechanism is **sealed trait/enum hierarchies** where one or more variants contain fields of the enclosing type. `enum Tree[A] { case Leaf(v: A); case Branch(l: Tree[A], r: Tree[A]) }` defines a binary tree where `Branch` contains two `Tree` values -- the type appears in its own definition.

Scala 3's `enum` syntax provides concise recursive ADT definitions. Sealed traits offer the same capability with more control over the representation. Because the JVM manages memory with garbage collection, recursive types require no special indirection (unlike Rust's `Box` requirement) -- every object is heap-allocated behind a reference by default.

For **corecursive** (potentially infinite) structures, Scala uses `lazy val` to defer evaluation, enabling infinite streams, cyclic graphs, and other coinductive patterns.

## What constraint it enforces

**The compiler ensures exhaustive pattern matching over recursive types and tracks the recursive structure through the type system. Each variant's fields must conform to the declared types, and sealed hierarchies guarantee that no external code can add new variants.**

- Sealed enums are closed: the compiler knows all cases and requires exhaustive matches.
- Type parameters flow through the recursion: `Tree[Int]` ensures every leaf holds an `Int`.
- Recursive generic bounds (F-bounded polymorphism) let types refer to themselves in bounds.

## Minimal snippet

```scala
enum Tree[+A]:
  case Leaf(value: A)
  case Branch(left: Tree[A], right: Tree[A])

import Tree.*

def depth[A](t: Tree[A]): Int = t match
  case Leaf(_)       => 0
  case Branch(l, r)  => 1 + math.max(depth(l), depth(r))

val tree = Branch(Leaf(1), Branch(Leaf(2), Leaf(3)))
println(depth(tree))   // 2
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **ADTs** [-> catalog/T01](T01-algebraic-data-types.md) | Recursive types are recursive ADTs. Sealed enum hierarchies combine sum types (variants) with product types (fields) in recursive definitions. |
| **Variance** [-> catalog/T08](T08-variance-subtyping.md) | Covariant recursive types (`Tree[+A]`) allow `Tree[Int]` where `Tree[Any]` is expected. Variance annotations propagate through the recursive structure. |
| **Pattern matching** [-> catalog/T14](T14-type-narrowing.md) | The compiler ensures exhaustive matching over all recursive variants. Nested patterns destructure recursive structures in a single match. |
| **Type aliases** [-> catalog/T23](T23-type-aliases.md) | Recursive type aliases (`type Stream[A] = () => (A, Stream[A])`) define coinductive types. Scala 3 allows recursive opaque type aliases. |
| **Derivation** [-> catalog/T06](T06-derivation.md) | `derives` clauses on recursive enums generate type class instances that recurse through the structure (e.g., `derives Codec` for JSON serialization of trees). |

## Gotchas and limitations

1. **Stack overflow on deep recursion.** Recursive functions over deep structures can blow the stack. Use tail-recursive methods (with `@tailrec`), trampolining, or convert to iterative algorithms for very deep trees.

2. **No built-in structural recursion check.** Unlike Lean or Agda, Scala does not verify that recursive functions terminate. Infinite loops on recursive types compile without warning.

3. **Lazy val overhead.** Corecursive structures using `lazy val` incur synchronization overhead on first access (the JVM must check initialization). For high-throughput lazy streams, consider `LazyList` from the standard library.

4. **F-bounded polymorphism complexity.** Recursive bounds like `trait Comparable[A <: Comparable[A]]` are powerful but produce complex types that can be hard to read and lead to confusing error messages.

5. **No anonymous recursive types.** You cannot write an inline recursive type expression. Every recursive type must be declared as a named `enum`, `sealed trait`, or type alias.

## Beginner mental model

Think of a recursive type as a **Russian nesting doll** (matryoshka). A `Tree` is either a `Leaf` (the smallest doll, containing a value) or a `Branch` (a doll containing two smaller dolls, each of which is itself a `Tree`). The definition is self-referential -- a tree is made of trees -- but each concrete tree is finite (the nesting eventually reaches leaves).

## Example A -- Recursive expression evaluator

```scala
enum Expr:
  case Num(value: Double)
  case Add(left: Expr, right: Expr)
  case Mul(left: Expr, right: Expr)
  case Neg(inner: Expr)

import Expr.*

def eval(e: Expr): Double = e match
  case Num(v)    => v
  case Add(l, r) => eval(l) + eval(r)
  case Mul(l, r) => eval(l) * eval(r)
  case Neg(i)    => -eval(i)

val expr = Add(Num(1), Mul(Num(2), Neg(Num(3))))
println(eval(expr))   // -5.0
```

## Example B -- Corecursive infinite stream with lazy val

```scala
class Stream[+A](val head: A, next: => Stream[A]):
  lazy val tail: Stream[A] = next

  def take(n: Int): List[A] =
    if n <= 0 then Nil
    else head :: tail.take(n - 1)

def nats(from: Int): Stream[Int] =
  Stream(from, nats(from + 1))

val naturals = nats(0)
println(naturals.take(5))   // List(0, 1, 2, 3, 4)
// The stream is infinite — only evaluated as far as needed
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Sealed recursive types ensure all structural variants are accounted for, making incomplete handling a compile error.
- [-> UC-10](../usecases/UC10-encapsulation.md) -- Sealed recursive hierarchies prevent external code from adding invalid variants.
- [-> UC-13](../usecases/UC13-state-machines.md) -- Recursive types can model state machines where transitions produce new states of the same type.

## Source anchors

- [Scala 3 Reference -- Enumerations](https://docs.scala-lang.org/scala3/reference/enums/enums.html)
- [Scala 3 Reference -- Algebraic Data Types](https://docs.scala-lang.org/scala3/reference/enums/adts.html)
- [Scala API -- LazyList](https://scala-lang.org/api/3.x/scala/collection/immutable/LazyList.html)
- Martin Odersky, *Programming in Scala*, Ch. 15 -- "Case Classes and Pattern Matching"
