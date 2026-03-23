# Generic Constraints

## The Constraint

Restrict type parameters to types that provide required capabilities. The compiler rejects instantiations that lack the necessary evidence, ensuring generic code is used only with types that satisfy its assumptions.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Context bounds | `[T: Ordering]` — require a type-class instance for `T` | [-> T05](T05-type-classes.md)(../catalog/T05-type-classes.md) |
| Upper / lower bounds | `[A <: Comparable[A]]` — restrict to subtypes or supertypes | [-> T01](T01-algebraic-data-types.md)(../catalog/T01-algebraic-data-types.md) |
| Using clauses | `(using Ord[T])` — pass evidence explicitly or implicitly | [-> T05](T05-type-classes.md)(../catalog/T05-type-classes.md) |
| Type lambdas | `[A] =>> Either[E, A]` — adapt type shapes for constraints | [-> T08](T08-type-lambdas.md)(../catalog/T08-type-lambdas.md) |
| Union / intersection | Combine or alternate constraints ad hoc | [-> T02](T02-union-intersection.md)(../catalog/T02-union-intersection.md) |
| =:= / <:< evidence | Compile-time proof of type equality or subtyping | [-> T16](T16-compile-time-ops.md)(../catalog/T16-compile-time-ops.md) |

## Patterns

### 1 — Context bounds for type-class requirements

The most common form of generic constraint. The compiler fills in the evidence automatically from available givens.

```scala
def sorted[A: Ordering](xs: List[A]): List[A] = xs.sorted

// Named context bounds (Scala 3.6+):
def topN[A: Ordering as ord](xs: List[A], n: Int): List[A] =
  xs.sorted(using ord).take(n)

// Multiple context bounds:
def dedup[A: Ordering : Eq](xs: List[A]): List[A] =
  xs.sorted.distinctBy(Eq[A].eqv(_, _))

// No Ordering for functions → compile error:
// sorted(List((x: Int) => x))  // error: No given instance of Ordering[Int => Int]
```

### 2 — Upper and lower bounds

Restrict type parameters by subtype or supertype relationships.

```scala
// Upper bound: A must be a subtype of Comparable[A]
def maxComparable[A <: Comparable[A]](x: A, y: A): A =
  if x.compareTo(y) >= 0 then x else y

// Lower bound: result type is the least upper bound
def prepend[A, B >: A](xs: List[A], elem: B): List[B] =
  elem :: xs

// Combining bounds:
sealed trait Animal
class Dog extends Animal
class Cat extends Animal

def adopt[A >: Dog <: Animal](a: A): String = s"adopted: $a"
// adopt(Dog())    // OK
// adopt(Cat())    // OK — Cat >: Dog? No, this uses <: Animal
```

### 3 — F-bounded polymorphism

A type parameter that references itself in its bound. Common for fluent APIs and self-referencing containers.

```scala
trait Builder[Self <: Builder[Self]]:
  def add(item: String): Self
  def build: List[String]

class ListBuilder(items: List[String] = Nil) extends Builder[ListBuilder]:
  def add(item: String): ListBuilder = ListBuilder(items :+ item)
  def build: List[String] = items

def buildAll[B <: Builder[B]](builder: B, items: List[String]): List[String] =
  items.foldLeft(builder)((b, i) => b.add(i)).build

val result = buildAll(ListBuilder(), List("a", "b", "c"))
// List("a", "b", "c")
```

### 4 — Evidence parameters with =:= and <:<

Request compile-time proof of type relationships. Useful for conditional method availability.

```scala
class Container[A](val value: A):
  // flatten is only available when A is itself a Container
  def flatten[B](using ev: A =:= Container[B]): Container[B] =
    ev(value)

  // toList only when A <:< Iterable
  def toList(using ev: A <:< Iterable[?]): List[Any] =
    ev(value).toList

val nested = Container(Container(42))
val flat: Container[Int] = nested.flatten  // compiles

// Container(42).flatten  // error: Cannot prove Int =:= Container[B]
```

### 5 — Intersection types for multi-constraint requirements

Combine unrelated type-class requirements without nesting context bounds.

```scala
trait Printable:
  def print: String

trait Loggable:
  def logLine: String

def report(item: Printable & Loggable): String =
  s"${item.print} [log: ${item.logLine}]"

case class Entry(name: String, level: Int) extends Printable, Loggable:
  def print: String   = s"Entry($name)"
  def logLine: String = s"$name@$level"

report(Entry("alpha", 1))  // compiles — Entry satisfies both traits
```

### 6 — Type lambdas for shape adaptation

When a constraint expects `F[_]` but you have a multi-parameter type, type lambdas adapt the shape.

```scala
trait Functor[F[_]]:
  extension [A](fa: F[A]) def map[B](f: A => B): F[B]

// Either has two type parameters; fix the error type:
given [E]: Functor[[A] =>> Either[E, A]] with
  extension [A](fa: Either[E, A])
    def map[B](f: A => B): Either[E, B] = fa.map(f)
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Context bounds | `[T: Ordering]` — same syntax, but `implicitly[Ordering[T]]` to access | `summon[Ordering[T]]` or named context bound `[T: Ordering as ord]` |
| Upper/lower bounds | Identical syntax and semantics | Same, plus union/intersection types for ad-hoc alternatives |
| F-bounded | Worked, but `implicit` self-type tricks were common and verbose | Cleaner with `using` clauses; less need thanks to extension methods |
| Evidence parameters | `(implicit ev: A =:= B)` — worked but leaked the implicit keyword | `(using ev: A =:= B)` — clearer intent; erased evidence possible |
| Type lambdas | Not available; required type-lambda plugin or `({type L[A] = Either[E, A]})#L` | First-class: `[A] =>> Either[E, A]` |

## When to Use Which Feature

**Use context bounds** as the default for type-class constraints. They are concise, widely understood, and compose with derivation.

**Use upper bounds** when subtype polymorphism is the right model (e.g., restricting to a sealed hierarchy or a Java interface like `Comparable`).

**Use F-bounded types** for fluent builder APIs where methods return the concrete subtype. Prefer type classes when possible, as F-bounds couple the interface to the type parameter.

**Use evidence parameters** (`=:=`, `<:<`) to make methods conditionally available based on type relationships. This avoids separate wrapper types.

**Use type lambdas** when adapting multi-parameter types to single-parameter type-class slots. They replace the Scala 2 type-projection workaround cleanly.
