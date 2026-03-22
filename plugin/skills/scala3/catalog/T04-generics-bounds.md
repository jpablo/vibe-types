# Generics & Bounded Polymorphism

> **Since:** Scala 3.0

## What it is

Scala 3's generics system lets you parameterize classes, traits, and methods over types, while **bounds** constrain those type parameters to ensure the generic code can only be instantiated when the required operations exist. An **upper bound** (`A <: B`) restricts `A` to subtypes of `B`. A **lower bound** (`A >: B`) restricts `A` to supertypes of `B`. A **context bound** (`A: Ordering`) requires a given instance of `Ordering[A]` in scope. **F-bounded polymorphism** (`A <: Comparable[A]`) allows a type to refer to itself in its own bound, enabling fluent APIs and self-referential constraints. **Variance-site bounds** interact with covariant/contravariant positions to ensure type safety in generic containers.

## What constraint it lets you express

**Bounds let you restrict the set of types that may be substituted for a type parameter, so that generic code only compiles when the operations it uses are justified by the constraint.** An upper bound guarantees access to the supertype's members; a context bound guarantees a type-class instance; F-bounds guarantee self-referential operations like `compareTo`. Without bounds, the type parameter is unrestricted (`A <: Any`) and only universal operations are available.

## Minimal snippet

**Upper bound:**

```scala
def maxOf[A <: Comparable[A]](x: A, y: A): A =
  if x.compareTo(y) >= 0 then x else y

maxOf("hello", "world")  // OK -- String <: Comparable[String]
// maxOf(1, 2)            // error: Int is not <: Comparable[Int]
```

**Lower bound:**

```scala
enum Expr[+A]:
  case Lit(value: A)

  def widen[B >: A](default: B): B = this match
    case Lit(v) => v   // v: A, returned as B since A <: B
```

**Context bound (Scala 3.6 named syntax):**

```scala
def sorted[A: Ordering as ord](xs: List[A]): List[A] =
  xs.sorted(using ord)

sorted(List(3, 1, 2))  // OK -- given Ordering[Int] exists
```

**F-bounded polymorphism:**

```scala
trait Pet[A <: Pet[A]]:
  def name: String
  def renamed(newName: String): A

case class Cat(name: String) extends Pet[Cat]:
  def renamed(newName: String): Cat = copy(name = newName)

case class Dog(name: String) extends Pet[Dog]:
  def renamed(newName: String): Dog = copy(name = newName)

def rename[A <: Pet[A]](pet: A, n: String): A = pet.renamed(n)
val kitty: Cat = rename(Cat("Felix"), "Kitty")  // returns Cat, not Pet
```

**Combined bounds:**

```scala
def clamp[A <: Comparable[A]](value: A, lo: A, hi: A): A =
  if value.compareTo(lo) < 0 then lo
  else if value.compareTo(hi) > 0 then hi
  else value
```

## Interaction with other features

| Feature | How it composes |
|---|---|
| **Variance** [-> catalog/T08](T08-variance-subtyping.md) | Bounds constrain how variance annotations propagate: a covariant type parameter in an output position may need a lower bound (`B >: A`) in methods that accept arguments of the parameterized type. |
| **Given instances / using clauses** [-> catalog/T05](T05-type-classes.md) | Context bounds (`A: Ordering`) desugar to `using Ordering[A]` parameters. Named context bounds (`A: Ordering as ord`, Scala 3.6+) give direct access to the witness. |
| **Opaque types** [-> catalog/T03](T03-newtypes-opaque.md) | Opaque types can declare upper bounds (`opaque type Id <: String = String`) that are visible outside the defining scope, interacting with generic upper bounds at call sites. |
| **Type lambdas** [-> catalog/T40](T40-type-lambdas.md) | Type lambda parameters can carry bounds: `[X <: Comparable[X]] =>> Set[X]` restricts what can be applied. |
| **Match types** [-> catalog/T41](T41-match-types.md) | Match type scrutinees can be bounded type parameters, enabling type-level dispatch constrained by bounds. |
| **Extension methods** [-> catalog/T19](T19-extension-methods.md) | Extension methods can have bounded type parameters: `extension [A <: Numeric[A]](xs: List[A]) def sum: A`. |

## Gotchas and limitations

1. **Context bounds vs. upper bounds.** A context bound `A: Ordering` is *not* an upper bound -- it does not make `A` a subtype of anything. It requires a given `Ordering[A]` in scope. Confusing the two is a common beginner mistake.
2. **F-bounded polymorphism and type inference.** F-bounds like `A <: Comparable[A]` can confuse type inference when the bound is deeply nested or involves multiple type parameters. Explicit type arguments may be needed at call sites.
3. **Lower bounds and widening.** A lower bound `A >: B` means `A` can be any supertype of `B`, up to `Any`. This is essential for covariant collection methods like `List[+A].appended[B >: A](elem: B): List[B]`, where the result type widens.
4. **No multi-bounded syntax.** Scala has no built-in `A <: B & C` shorthand for multiple upper bounds, but you can use intersection types: `A <: Serializable & Comparable[A]`.
5. **View bounds are removed.** Scala 2's view bounds (`A <% B`) are gone. Use context bounds with `Conversion[A, B]` instead. [-> catalog/T18](T18-conversions-coercions.md)
6. **Bounds on abstract type members.** Type members in traits can carry bounds (`type T <: Animal`), providing the same constraint mechanism as type parameters but with path-dependent resolution.

## Beginner mental model

Think of type parameter bounds as **a contract the caller must satisfy**. When you write `def sort[A: Ordering](xs: List[A])`, you are saying: "I can sort any list, but you must prove the element type has an ordering." The compiler checks this proof at every call site. If the proof (a given instance) does not exist, the code does not compile -- not at runtime, at compile time.

## Common type-checker errors

```
-- [E057] Type Mismatch Error ---
  def process[A](x: A) = x.length
                          ^^^^^^^^
  value length is not a member of A

  Fix: add an upper bound: def process[A <: String](x: A) = x.length
```

```
-- [E172] Type Error ---
  maxOf(1, 2)
        ^
  Type argument Int does not conform to upper bound Comparable[Int]

  Fix: use a context bound with Ordering instead of Comparable for
  primitive types, or use java.lang.Integer explicitly.
```

```
-- Error ---
  sorted(List(Cat("a"), Dog("b")))
  No given instance of type Ordering[Pet[? <: Pet[?]]] was found

  Fix: provide a given Ordering for the specific type, or constrain
  the list to a single Pet subtype.
```

## Use-case cross-references

- [-> UC-02](../usecases/UC02-domain-modeling.md) Constraining domain types with upper bounds and type-class evidence
- [-> UC-05](../usecases/UC12-compile-time.md) Generic algorithms that require compile-time proof of capabilities
- [-> UC-07](../usecases/UC14-extensibility.md) F-bounded APIs for fluent builder patterns
- [-> UC-17](../usecases/UC17-variance.md) Variance-compatible bounds in generic collection design

## Source anchors

- [Scala 3 Reference: Type Parameter Bounds](https://docs.scala-lang.org/scala3/reference/overview.html)
- [Scala 3 Reference: Context Bounds](https://docs.scala-lang.org/scala3/reference/contextual/context-bounds.html)
- [Scala 3 Reference: Variance](https://docs.scala-lang.org/scala3/reference/overview.html)
