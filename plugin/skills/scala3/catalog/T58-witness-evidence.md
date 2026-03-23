# Witness and Evidence Types

> **Since:** Scala 2 (`=:=`, `<:<`); Scala 3 refines with `summon`, `Conversion`, given-based evidence

## What it is

Witness and evidence types encode **proofs at the type level** that the compiler supplies via implicit (given) search. The core types are `=:=[A, B]` (evidence that `A` and `B` are the same type) and `<:<[A, B]` (evidence that `A` is a subtype of `B`). A method that demands `(using ev: A =:= B)` can only be called when the compiler can prove the two types are equal.

In Scala 3, `summon[T]` retrieves any given instance, so `summon[A =:= B]` either succeeds (proving equality) or fails at compile time. `Conversion[A, B]` provides evidence that `A` can be implicitly converted to `B`. Together with given instances, context bounds, and inline matches, evidence types let you write APIs where capabilities are unlocked only when the caller can provide the right proof.

## What constraint it enforces

**A method guarded by an evidence parameter cannot be called unless the compiler can synthesize a value of the evidence type. This turns type-level relationships into compile-time-checked prerequisites.**

- `=:=[A, B]` enforces type equality: the method is callable only when `A` and `B` are identical.
- `<:<[A, B]` enforces subtyping: the method is callable only when `A <: B`.
- Custom evidence (e.g., `given CanSerialize[A]`) encodes domain-specific capabilities.

## Minimal snippet

```scala
def collapse[A, B](a: A, b: B)(using ev: A =:= B): List[A] =
  List(a, ev.flip(b))   // ev.flip converts B back to A

collapse(1, 2)              // OK — Int =:= Int
// collapse(1, "two")       // error: Cannot prove that Int =:= String
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type classes** [-> catalog/T05](T05-type-classes.md) | Evidence types are type classes whose instances the compiler auto-derives. `=:=` and `<:<` have a single canonical given instance each. |
| **Context functions** [-> catalog/T42](T42-context-functions.md) | Evidence parameters are context parameters (`using`). Context functions let you thread evidence through lambdas without explicit passing. |
| **Match types** [-> catalog/T41](T41-match-types.md) | `inline` methods with `summon` can branch on evidence availability, selecting implementations at compile time based on type relationships. |
| **Path-dependent types** [-> catalog/T53](T53-path-dependent-types.md) | `=:=` evidence provides `apply` and `flip` methods that convert values between the two proven-equal types, similar to a path-dependent cast. |
| **Opaque types** [-> catalog/T03](T03-newtypes-opaque.md) | Evidence types complement opaque types: an opaque `Token` can require `given Authenticated` evidence before exposing its inner value. |

## Gotchas and limitations

1. **Evidence is not free at runtime.** `=:=` and `<:<` instances are objects allocated on the heap. In hot loops, consider `inline` methods or `@specialized` to avoid boxing. Scala 3 `inline` + `erasedValue` can eliminate evidence at compile time.

2. **Ambiguous implicits.** If multiple given instances could provide the evidence, the compiler rejects the call with an ambiguity error. Keep evidence instances canonical and avoid overlapping givens.

3. **Contravariant evidence pitfall.** `<:<` is covariant in the second parameter but invariant in the first. `Nothing <:< Any` exists, but you cannot use it to prove `List[Nothing] <:< List[Any]` without additional evidence.

4. **No negation.** You cannot express "A is NOT equal to B" as an evidence type. The `NotGiven[A =:= B]` pattern from Scala 3 approximates this but has edge cases with ambiguity.

5. **Summoning inside macros.** `summon` inside inline methods resolves at the call site, not the definition site. This is powerful but can surprise when the call-site scope lacks the expected givens.

## Beginner mental model

Think of evidence types as **ID badges**. A method guarded by `(using ev: A =:= B)` is a locked door that only opens when you present a badge proving A equals B. The compiler is the badge office -- it automatically issues the badge if the proof is obvious, or refuses if it cannot verify the claim. You never forge badges yourself; the compiler's badge office is the single source of truth.

## Example A -- Conditional method with =:= evidence

```scala
enum Container[A]:
  case Box(value: A)

  // flatten is only available when A is itself a Container
  def flatten[B](using ev: A =:= Container[B]): Container[B] =
    ev(this.value)    // convert A to Container[B]

val nested = Container.Box(Container.Box(42))
val flat = nested.flatten   // OK — A is Container[Int]

val simple = Container.Box(42)
// simple.flatten            // error: Cannot prove that Int =:= Container[B]
```

## Example B -- Custom domain evidence with given

```scala
sealed trait Permission
object Permission:
  case object Admin extends Permission
  case object Reader extends Permission

trait IsAdmin[P <: Permission]
given IsAdmin[Permission.Admin.type] with {}

def deleteAll[P <: Permission]()(using ev: IsAdmin[P]): Unit =
  println("All records deleted")

def withAdmin(): Unit =
  given p: IsAdmin[Permission.Admin.type] = summon
  deleteAll[Permission.Admin.type]()   // OK — evidence found

// deleteAll[Permission.Reader.type]() // error: no given instance of IsAdmin[Reader]
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Evidence types make invalid operations unrepresentable by requiring compile-time proof of preconditions.
- [-> UC-10](../usecases/UC10-encapsulation.md) -- Evidence-guarded methods expose capabilities selectively without runtime checks.
- [-> UC-13](../usecases/UC13-state-machines.md) -- State transitions can require evidence that the current state permits the transition.

## Source anchors

- [Scala 3 Reference -- Context Parameters](https://docs.scala-lang.org/scala3/reference/contextual/using-clauses.html)
- [Scala API -- scala.=:=](https://scala-lang.org/api/3.x/scala/=:=.html)
- [Scala API -- scala.<:<](https://scala-lang.org/api/3.x/scala/$less$colon$less.html)
- [Scala 3 Reference -- Given Instances](https://docs.scala-lang.org/scala3/reference/contextual/givens.html)
- [Scala 3 Reference -- summon](https://docs.scala-lang.org/scala3/reference/contextual/using-clauses.html#summoning-instances)
