# Type-Level Arithmetic

## The Constraint

Perform numeric computations and enforce numeric constraints at compile time. Dimension mismatches, out-of-range indices, and invalid sizes become compile errors rather than runtime exceptions.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Compiletime ops | Type-level `+`, `-`, `*`, `/`, `<`, `>=` over singleton `Int` types | [-> T16](T16-compile-time-ops.md)(../catalog/T16-compile-time-ops.md) |
| Match types | Recursive type-level computation (Peano encoding, type-level lists) | [-> T41](T41-match-types.md)(../catalog/T41-match-types.md) |
| Inline / constValue | Force compile-time evaluation; extract singleton types as values | [-> T16](T16-compile-time-ops.md)(../catalog/T16-compile-time-ops.md) |
| Singleton types | Literal types like `3`, `true` that carry values into the type system | — |
| Macros | Escape hatch for arithmetic that exceeds `compiletime.ops` | [-> T17](T17-macros-metaprogramming.md)(../catalog/T17-macros-metaprogramming.md) |

## Patterns

### 1 — compiletime.ops.int for type-level arithmetic

Use `scala.compiletime.ops.int` to express constraints directly in types.

```scala
import scala.compiletime.ops.int.*

type Positive[N <: Int] = N > 0 =:= true

def posOnly[N <: Int & Singleton](n: N)(using Positive[N]): N = n

val ok  = posOnly(5)   // compiles — 5 > 0 is true
// val no = posOnly(-1) // compile error — -1 > 0 is false
```

### 2 — Type-safe vector dimensions

Encode length in the type to reject mismatched operations at compile time.

```scala
import scala.compiletime.ops.int.*

final class Vec[N <: Int](val data: Array[Double]):
  def length: N = data.length.asInstanceOf[N]

  infix def dot(that: Vec[N]): Double =
    data.zip(that.data).map(_ * _).sum

  def concat[M <: Int](that: Vec[M]): Vec[N + M] =
    Vec(data ++ that.data)

val v3: Vec[3] = Vec(Array(1.0, 2.0, 3.0))
val v2: Vec[2] = Vec(Array(4.0, 5.0))

val v5: Vec[5] = v3.concat(v2)  // compiles — 3 + 2 = 5
v3.dot(v3)                       // compiles — both Vec[3]
// v3.dot(v2)                    // compile error — Vec[3] vs Vec[2]
```

### 3 — Match type recursion for Peano-like encoding

When `compiletime.ops` is insufficient, model natural numbers as types.

```scala
sealed trait Nat
sealed trait Zero extends Nat
sealed trait Succ[N <: Nat] extends Nat

type NatToInt[N <: Nat] <: Int = N match
  case Zero    => 0
  case Succ[n] => scala.compiletime.ops.int.+[NatToInt[n], 1]

type Two   = Succ[Succ[Zero]]
type Three = Succ[Succ[Succ[Zero]]]

summon[NatToInt[Two]   =:= 2]
summon[NatToInt[Three] =:= 3]

type NatPlus[A <: Nat, B <: Nat] <: Nat = A match
  case Zero    => B
  case Succ[a] => Succ[NatPlus[a, B]]

summon[NatPlus[Two, Three] =:= Succ[Succ[Succ[Succ[Succ[Zero]]]]]]
```

### 4 — constValue to extract compile-time numbers

Bridge the type level and the value level using `constValue` and `constValueTuple`.

```scala
import scala.compiletime.{constValue, constValueTuple}

inline def dimensionOf[N <: Int]: Int = constValue[N]

val n: 5 = constValue[5]   // returns the literal 5

inline def describe[N <: Int]: String =
  inline constValue[N < 0] match
    case true  => "negative"
    case false =>
      inline constValue[N] match
        case 0 => "zero"
        case _ => "positive"

val s: String = describe[3]   // "positive" — resolved at compile time
// describe[-1]               // "negative"
// describe[0]                // "zero"
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Type-level numbers | Libraries like Shapeless `Nat` with Church/Peano encoding; slow compilation, limited range | `compiletime.ops.int` — built into the compiler, fast, works on `Int` literals |
| Dimension checks | Shapeless `Sized` or custom phantom types; verbose, fragile | Singleton `Int` types + `ops.int` — concise, first-class |
| Compile-time extraction | Shapeless `Witness` / `nat.toInt` macro — complex | `constValue[N]` — one call, no imports beyond `compiletime` |
| Recursive computation | Type-level programming via implicits and `Aux` pattern; hard to debug | Match types — pattern matching at the type level, readable, compiler-supported |

## When to Use Which Feature

**Default to `compiletime.ops.int`** for straightforward arithmetic constraints (bounds checking, dimension matching, capacity limits). It covers `+`, `-`, `*`, `/`, `%`, `<`, `>`, `<=`, `>=`, `==`, `!=` and compiles efficiently.

**Use match types** when the computation is recursive or structural (e.g., computing the length of an HList, flattening nested tuples). Match types read like value-level pattern matching.

**Use Peano encoding** only when you need inductive proofs or the recursion does not map to `Int` arithmetic (e.g., type-level lists, balanced trees).

**Reach for macros** when you need error messages that reference domain terms ("matrix dimensions 3x4 and 5x2 are incompatible") or when the computation exceeds what `compiletime.ops` supports.

**Use `constValue` / `constValueTuple`** to cross the type-value boundary whenever a compile-time constant needs to flow into runtime code.
