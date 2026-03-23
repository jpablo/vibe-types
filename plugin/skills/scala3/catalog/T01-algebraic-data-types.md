# Enums, ADTs, and GADTs

> **Since:** Scala 3.0

## 1. What It Is

Scala 3's `enum` keyword unifies simple enumerations, algebraic data types (ADTs), and generalized algebraic data types (GADTs) under a single syntactic construct. A simple enum defines a sealed set of named singleton values (like Java enums). An ADT uses parameterized `case` members to model sum-of-products. A GADT refines type parameters in individual cases via explicit `extends` clauses, enabling the compiler to narrow types within pattern-match branches. Under the hood, an `enum` compiles to a `sealed` class extending `scala.reflect.Enum`, with each case becoming either a val (singleton) or a case class (parameterized).

## 2. What Constraint It Lets You Express

**You can restrict the inhabitants of a type to a closed, compiler-known set of alternatives, gaining exhaustive pattern matching, and -- with GADTs -- the ability to refine type information per branch so that the type checker enforces invariants that differ across cases.**

- *Enums* constrain values to a fixed list; the compiler warns on non-exhaustive matches.
- *ADTs* constrain the shape of data: each case carries exactly its declared fields.
- *GADTs* constrain the relationship between type parameters and cases: matching on a case refines the type parameter, enabling type-safe operations that vary by branch.

## 3. Minimal Snippet

**Simple enum:**

```scala
enum Direction:
  case North, South, East, West

def describe(d: Direction): String = d match
  case Direction.North => "up"
  case Direction.South => "down"
  case Direction.East  => "right"
  case Direction.West  => "left"
  // exhaustive -- no warning
```

**ADT (sum of products):**

```scala
enum Expr:
  case Lit(value: Int)
  case Add(a: Expr, b: Expr)
  case Neg(e: Expr)

def eval(e: Expr): Int = e match
  case Expr.Lit(v)    => v
  case Expr.Add(a, b) => eval(a) + eval(b)
  case Expr.Neg(e)    => -eval(e)
```

**GADT (type-refining cases):**

```scala
enum Expr[A]:
  case IntLit(value: Int)       extends Expr[Int]
  case BoolLit(value: Boolean)  extends Expr[Boolean]
  case Add(a: Expr[Int], b: Expr[Int]) extends Expr[Int]
  case Cond(test: Expr[Boolean], ifTrue: Expr[A], ifFalse: Expr[A])

def eval[A](e: Expr[A]): A = e match
  case Expr.IntLit(v)  => v         // A is refined to Int here
  case Expr.BoolLit(v) => v         // A is refined to Boolean here
  case Expr.Add(a, b)  => eval(a) + eval(b)
  case Expr.Cond(t, a, b) => if eval(t) then eval(a) else eval(b)
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Type-class derivation** [-> T06](T06-derivation.md) | `enum Tree[T] derives Eq, Ordering` triggers automatic generation of instances for each case via `Mirror.Sum` and `Mirror.Product`. |
| **Multiversal equality** [-> T20](T20-equality-safety.md) | `derives CanEqual` on an enum restricts `==` to comparing values of that enum (or compatible types), preventing cross-hierarchy comparisons. |
| **Pattern matching / match types** [-> T07](T07-structural-typing.md) | Enum cases are the primary targets of pattern matches; GADTs refine types in branches. Match types can dispatch on enum-like sealed hierarchies at the type level. |
| **Extension methods** [-> T19](T19-extension-methods.md) | Methods can be added to an enum or its cases after the fact. A common pattern is adding syntax via extensions rather than polluting the enum body. |
| **Opaque types** [-> T03](T03-newtypes-opaque.md) | Enums and opaque types serve overlapping goals (restricting inhabitants), but enums work at the value level while opaque types work at the type level. They compose when an enum case wraps an opaque type. |

## 5. Gotchas and Limitations

- **Type widening.** The type of an enum case constructor application is widened to the parent enum type, not the specific case type. To get the precise type, use `new` or an explicit type ascription: `val x: Option.Some[Int] = Option.Some(1)`.
- **Variance and cases.** Parameterized cases inherit the variance annotations of the parent enum. If the variance causes a contradiction (e.g., a contravariant type used covariantly in a field), the compiler requires an explicit `extends` clause with a fresh, invariant type parameter.
- **Enum case scoping.** Enum case declarations are scoped *outside* the enum template body. They cannot access inner members of the enum class. References to the companion object must be fully qualified (e.g., `Planet.earthMass`), not imported.
- **No companion for cases.** You cannot define a companion object for an enum case inside the enum body. An object with the same name in the enum template is a distinct, unrelated object.
- **Java compatibility.** To use a Scala enum as a Java enum, extend `java.lang.Enum[E]`. Parameterized ADT cases are not compatible with Java enums.
- **Exhaustiveness.** The compiler checks exhaustiveness for `sealed` hierarchies (which all enums are). Adding a case to an enum will produce warnings at all non-exhaustive match sites, serving as a compile-time contract.
- **Ordinal and helpers.** Every enum value has an `ordinal: Int` method. The companion gets `values: Array[E]`, `valueOf(name: String): E`, and `fromOrdinal(n: Int): E`.

## Recommended Libraries

| Library | Role | Link |
|---|---|---|
| **circe** | JSON codecs for ADTs; automatic derivation for enum/sealed hierarchies | [circe.github.io](https://circe.github.io/circe/) |
| **enumeratum** | Enhanced enums with exhaustive helpers, JSON/Play integrations (Scala 2 compat; Scala 3 enums cover most use cases natively) | [github.com/lloydmeta/enumeratum](https://github.com/lloydmeta/enumeratum) |
| **iron** | Refined types over ADTs; compile-time constraints on enum-wrapped values | [github.com/Iltotore/iron](https://github.com/Iltotore/iron) |

## Coming from Lean

Scala 3's `enum` with GADTs corresponds to Lean's *indexed inductive families*. Where Lean writes `inductive Expr : Type → Type where | intLit : Int → Expr Int`, Scala writes `case IntLit(v: Int) extends Expr[Int]`. Both achieve per-branch type refinement in pattern matching. The key difference: Lean's inductive families can index by *values* (e.g., `Vec α n` where `n : Nat`), while Scala's GADTs only refine *type parameters*.

## 6. Use-Case Cross-References

- [-> UC-02](../usecases/UC02-domain-modeling.md) Domain modeling with closed type hierarchies
- [-> UC-05](../usecases/UC12-compile-time.md) Type-safe expression trees (GADT interpreters)
- [-> UC-06](../usecases/UC13-state-machines.md) Exhaustive command/event handling
- [-> UC-09](../usecases/UC16-nullability.md) Deriving serialization for sum types
