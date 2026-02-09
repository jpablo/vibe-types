# UC-10 -- Variance and Subtyping

## 1. The Constraint

**Control covariance, contravariance, and subtyping relationships precisely.**
Decide whether `Container[Dog]` is a subtype of `Container[Animal]`, whether two unrelated types can be combined in a single expression, and whether a wrapper type inherits or breaks the subtyping of its underlying type. Incorrect variance leads to unsound casts or overly rigid APIs; precise variance annotations prevent both.

## 2. Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Union / Intersection types | Express "one of" or "all of" several types without introducing a class hierarchy. Interact with variance: unions widen, intersections narrow. | [-> catalog/01] |
| Opaque types | Create a new type that does *not* inherit the subtyping relationships of its representation. | [-> catalog/12] |
| Type lambdas | Rearrange or partially apply type parameters so that variance aligns with a required shape. | [-> catalog/02] |
| Enums / ADTs | Enum cases are subtypes of the enum. Variance annotations on enum type parameters propagate to cases. | [-> catalog/11] |
| Open classes | Control which classes can be extended, directly affecting the subtyping lattice. | [-> catalog/13] |

## 3. Patterns

### Pattern A: Covariant Container with Union Return Types

A covariant container can return values at union types, naturally widening the result when two containers of different element types are combined.

```scala
enum MyList[+A]:
  case Nil
  case Cons(head: A, tail: MyList[A])

import MyList.*

val ints: MyList[Int] = Cons(1, Cons(2, Nil))
val strs: MyList[String] = Cons("a", Nil)

// Covariance allows using MyList[Int] where MyList[Int | String] is expected:
def combine[A](a: MyList[A], b: MyList[A]): MyList[A] = ???

val both: MyList[Int | String] = combine(ints, strs)
// Without union types, this would require an explicit common supertype.

// Covariance also means:
val animals: MyList[Animal] = Cons(Dog(), Cons(Cat(), Nil))
val dogs: MyList[Dog] = Cons(Dog(), Nil)
val all: MyList[Animal] = dogs  // ok: MyList[Dog] <: MyList[Animal]
```

```scala
trait Animal
class Dog extends Animal
class Cat extends Animal
```

### Pattern B: Intersection Types for Combined Constraints

Intersection types require a value to satisfy multiple interfaces simultaneously. This narrows the subtyping relationship: `A & B <: A` and `A & B <: B`.

```scala
trait Printable:
  def printMe(): Unit

trait Serializable:
  def toBytes: Array[Byte]

// Require both capabilities without defining a combined trait:
def process(x: Printable & Serializable): Unit =
  x.printMe()
  val bytes = x.toBytes
  println(s"${bytes.length} bytes")

class Report(data: String) extends Printable, Serializable:
  def printMe(): Unit = println(data)
  def toBytes: Array[Byte] = data.getBytes

process(Report("Q4"))  // ok: Report <: Printable & Serializable

// Contravariant position: a function accepting an intersection
// is MORE general than one accepting either type alone:
val f: (Printable & Serializable) => Unit = process
// f can be used wherever (Printable => Unit) or (Serializable => Unit) is expected?
// No -- function arguments are contravariant:
// (A => R) <: (B => R) when B <: A.
// (Printable & Serializable => Unit) is a SUPERtype of (Printable => Unit).
```

### Pattern C: Opaque Types Break Subtyping by Design

An opaque type creates a new type boundary. Outside its defining scope, there is no subtype relationship with the underlying type, even if the underlying type has one.

```scala
object Ids:
  opaque type UserId = Long
  object UserId:
    def apply(id: Long): UserId = id
    extension (id: UserId) def value: Long = id

  opaque type OrderId = Long
  object OrderId:
    def apply(id: Long): OrderId = id
    extension (id: OrderId) def value: Long = id

import Ids.*

def findUser(id: UserId): Unit = ()
def findOrder(id: OrderId): Unit = ()

val uid = UserId(42)
val oid = OrderId(42)

findUser(uid)   // ok
// findUser(oid)  // error: expected UserId, got OrderId
// findUser(42L)  // error: expected UserId, got Long

// Even though both are Long internally, the subtype relationship is severed.
// This is the key difference from a type alias, which preserves subtyping.
```

### Pattern D: Variance Annotations on Enum ADTs

Enum type parameters can carry `+` / `-` annotations. The compiler checks that every case is consistent with the declared variance.

```scala
enum Result[+E, +A]:
  case Success(value: A)
  case Failure(error: E)

// Covariance allows:
val ok: Result[Nothing, Int] = Result.Success(42)
val fail: Result[String, Nothing] = Result.Failure("boom")

val r1: Result[String, Int] = ok    // ok: Result[Nothing, Int] <: Result[String, Int]
val r2: Result[String, Int] = fail  // ok: Result[String, Nothing] <: Result[String, Int]

// With type bounds to constrain variance:
enum Validated[+E, +A]:
  case Valid(value: A)
  case Invalid(errors: List[E])

// Upper bounds interact with variance:
enum Expr[+A <: Number]:
  case Lit(value: A)
  case Add(left: Expr[A], right: Expr[A])

// Expr[Integer] <: Expr[Number] because +A and Integer <: Number.
```

## 4. Scala 2 Comparison

| Aspect | Scala 2 | Scala 3 |
|---|---|---|
| Variance annotations | `+` / `-` on class and trait type parameters, same syntax. | Same syntax, same rules. No change. |
| Combining unrelated types | Required a common supertype or a hand-rolled `Either` / `Coproduct`. | Union types (`A \| B`) express "one of" without a wrapper. |
| Narrowing to combined constraints | `A with B` compound types (non-commutative). | `A & B` intersection types (commutative, with sound member merging). |
| Breaking subtyping for newtypes | Value classes (`extends AnyVal`) preserved the subtype relationship in many contexts. Tagged types (shapeless) partially worked. | Opaque types fully sever the subtype relationship outside their scope. |
| Enum variance | Not applicable -- no `enum` keyword. Sealed trait hierarchies carried variance on the parent. | `enum` supports variance annotations directly; cases are checked for consistency. |
| Type lambdas for variance alignment | "Type lambda trick" with structural refinements: `({type L[A] = Map[K, A]})#L`. | First-class `[A] =>> Map[K, A]` syntax. |

## 5. When to Use Which Feature

| If you need... | Prefer |
|---|---|
| A container that is a subtype when its element is | **`+A` covariance** on the type parameter. Use union types for natural widening (Pattern A). |
| A value satisfying multiple interfaces | **Intersection types** `A & B` (Pattern B). No need to define a combined trait. |
| A wrapper type that is *not* a subtype of its representation | **Opaque types** (Pattern C). Guarantees type safety across domain boundaries. |
| An ADT with variance-aware cases | **Enum with `+`/`-` annotations** (Pattern D). The compiler checks case consistency. |
| Adapting a multi-parameter type to a unary shape with correct variance | **Type lambdas**: `[A] =>> Map[K, A]` preserves the variance of `Map`'s second parameter. |
| Controlling who can add new subtypes | **`open`** modifier on the base class, or `sealed` / `final` to close the hierarchy. |
