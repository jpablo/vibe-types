# Variance & Subtyping Rules

> **Since:** Scala 3.0

## What it is

Variance annotations declare how the subtyping relationship of a type constructor relates to the subtyping relationship of its type arguments. **Covariance** (`+A`) means `F[B] <: F[A]` when `B <: A` -- the container varies *with* its element. **Contravariance** (`-A`) means `F[A] <: F[B]` when `B <: A` -- the container varies *against* its element. **Invariance** (plain `A`) means `F[A]` and `F[B]` are unrelated even when `A <: B`. Scala has the most explicit variance system among mainstream languages: every type parameter on a class or trait can be annotated, and the compiler enforces that the annotation is sound by checking every occurrence in covariant, contravariant, or invariant position.

## What constraint it lets you express

**Variance annotations let you declare and enforce substitutability rules for generic types at compile time.** A `List[+A]` guarantees that `List[Cat]` can be used wherever `List[Animal]` is expected (Liskov substitution). A `Function1[-A, +B]` guarantees that a function accepting `Animal` can substitute for one accepting `Cat` (contravariant input), while its result substitutes covariantly. The compiler rejects definitions that would violate these guarantees -- such as adding a covariant type parameter in a method argument position -- preventing unsound casts at the source.

## Minimal snippet

**Covariance:**

```scala
enum Opt[+A]:
  case Some(value: A)
  case None

val catOpt: Opt[Cat] = Opt.Some(Cat("Felix"))
val animalOpt: Opt[Animal] = catOpt  // OK: Opt[Cat] <: Opt[Animal]
```

**Contravariance:**

```scala
trait Printer[-A]:
  def print(value: A): Unit

val animalPrinter: Printer[Animal] = a => println(a.name)
val catPrinter: Printer[Cat] = animalPrinter  // OK: Printer[Animal] <: Printer[Cat]
// A printer that can print any animal can certainly print cats
```

**Invariance (mutable references must be invariant):**

```scala
class MutRef[A](var value: A)

val catRef: MutRef[Cat] = MutRef(Cat("Felix"))
// val animalRef: MutRef[Animal] = catRef  // error: MutRef is invariant in A
// If allowed, animalRef.value = Dog("Rex") would corrupt catRef
```

**Variance in method signatures (lower bound for covariant output):**

```scala
enum MyList[+A]:
  case Cons(head: A, tail: MyList[A])
  case Nil

  def prepend[B >: A](elem: B): MyList[B] =
    Cons(elem, this)

val cats: MyList[Cat] = MyList.Cons(Cat("Felix"), MyList.Nil)
val animals: MyList[Animal] = cats.prepend(Dog("Rex"))  // MyList[Animal]
```

**Function variance (`Function1[-A, +B]`):**

```scala
val f: Cat => Animal = (c: Cat) => c
val g: Animal => Cat = ???

// Function1 is contravariant in input, covariant in output:
val h: Animal => Animal = f  // error: Cat => Animal is not Animal => Animal
val i: Cat => Animal = g     // OK: Animal => Cat <: Cat => Animal
```

## Interaction with other features

| Feature | How it composes |
|---|---|
| **Enums / ADTs** [-> catalog/T01](T01-algebraic-data-types.md) | Enum type parameters carry variance: `enum Option[+A]`. Cases inherit the parent's variance. A case with a contravariant field (e.g., a callback) requires explicit `extends` with adjusted type parameters. |
| **Opaque types** [-> catalog/T03](T03-newtypes-opaque.md) | Opaque types can declare variance via bounds: `opaque type IArray[+T] = Array[T]`. Outside the defining scope, the variance is determined by the declared bounds, not the underlying representation. This enables "phantom variance" -- making an invariant type appear covariant. |
| **Generics & bounds** [-> catalog/T04](T04-generics-bounds.md) | Lower bounds (`B >: A`) are the standard escape hatch for using a covariant type parameter in contravariant position (e.g., method arguments in covariant containers). |
| **Type lambdas** [-> catalog/T40](T40-type-lambdas.md) | Type lambda parameters cannot carry variance annotations. Variance can only be declared on named type definitions (`type`, `trait`, `class`). |
| **Given instances** [-> catalog/T05](T05-type-classes.md) | Type-class instances for covariant types must be careful: `given Ordering[List[A]]` with covariant `List[+A]` requires that the instance handle the widened type correctly. |
| **Union / intersection types** [-> catalog/T02](T02-union-intersection.md) | Covariant type constructors distribute over intersections: `List[A & B] <: List[A] & List[B]`. Contravariant constructors distribute over unions. |

## Gotchas and limitations

1. **Covariant type in contravariant position.** The most common variance error: using `+A` as a method parameter type. The fix is a lower-bounded type parameter: `def add[B >: A](x: B)`. This is required for covariant collections to have `append`/`prepend` methods.
2. **Mutable fields force invariance.** A `var x: A` reads (covariant) and writes (contravariant) `A`, so `A` must be invariant. Use `val` for covariant types, or encapsulate mutation behind a private API.
3. **Java arrays are covariant (unsoundly).** Scala's `Array[A]` is invariant, unlike Java's `T[]` which is covariant. This is a deliberate soundness fix, but it means `Array[Cat]` cannot be passed where `Array[Animal]` is expected.
4. **Type parameter vs. type member variance.** Abstract type members cannot carry variance annotations directly. Their variance is inferred from usage positions. This is less explicit than type parameter annotations.
5. **Phantom variance via opaque types.** An opaque type `opaque type F[+A] = G[A]` where `G` is invariant is legal: the compiler checks variance only against the declared bounds (visible outside), not the underlying type (visible only inside). This is powerful but requires the author to ensure soundness manually within the defining scope.
6. **Contravariant types and `Nothing`.** Since `Nothing` is the bottom type, a `Printer[Nothing]` is the top of the `Printer` hierarchy (contravariance reverses the subtyping). This can be counterintuitive.

## Beginner mental model

Think of variance as answering: **"If I have a box of cats, can I use it where a box of animals is expected?"**

- **Covariant (`+A`):** Yes, a box of cats is a box of animals. Works for read-only containers (you only take things out).
- **Contravariant (`-A`):** The reverse -- a handler of animals is a handler of cats. Works for write-only/consumer types (you only put things in).
- **Invariant (`A`):** Neither -- a mutable box of cats is not a mutable box of animals, because someone could put a dog in.

The Liskov Substitution Principle is the formal justification: if `Cat <: Animal`, then any code expecting an `Animal` must work correctly when given a `Cat`. Variance annotations tell the compiler which type constructors preserve this substitutability and in which direction.

## Common type-checker errors

```
-- [E093] Variance Error ---
  trait Box[+A]:
    def set(value: A): Unit
                   ^
  covariant type A occurs in contravariant position in type A of parameter value

  Fix: use a lower-bounded type parameter:
    def set[B >: A](value: B): Unit
```

```
-- [E007] Type Mismatch Error ---
  val ref: MutRef[Animal] = MutRef[Cat](Cat("Felix"))
                            ^^^^^^^^^^^^^^^^^^^^^^^^
  Found:    MutRef[Cat]
  Required: MutRef[Animal]
  Note: Cat <: Animal, but class MutRef is invariant in type A.

  Fix: MutRef must be invariant because it is mutable. Use an immutable
  wrapper if you need covariance.
```

```
-- [E093] Variance Error ---
  enum Tree[+A]:
    case Leaf(value: A)
    case Node(left: Tree[A], right: Tree[A], f: A => Boolean)
                                                ^
  covariant type A occurs in contravariant position in type A => Boolean

  Fix: move the function out of the enum case, or use a lower-bounded
  method parameter instead.
```

## Use-case cross-references

- [-> UC-02](../usecases/UC02-domain-modeling.md) Covariant domain hierarchies for sum types and sealed traits
- [-> UC-07](../usecases/UC14-extensibility.md) Contravariant type classes for serialization / formatting
- [-> UC-17](../usecases/UC17-variance.md) Designing variance-correct collection APIs
- [-> UC-01](../usecases/UC01-invalid-states.md) Using variance to prevent invalid state transitions in typed state machines

## Source anchors

- [Scala 3 Reference: Variance](https://docs.scala-lang.org/scala3/reference/overview.html)
- [Scala 3 Book: Variance](https://docs.scala-lang.org/scala3/book/types-variance.html)
- [Scala API: Function1[-T1, +R]](https://www.scala-lang.org/api/3.x/scala/Function1.html)
