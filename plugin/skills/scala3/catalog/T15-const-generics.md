# Singleton Types, Literal Types & Compile-Time Value Parameters

> **Since:** Scala 3.0 (singleton types, `inline`, `constValue`) | Scala 2.13 had limited literal types

## What it is

Scala 3 does not have a dedicated `const N: Int` generic parameter syntax like Rust. Instead, it achieves the same effect through a combination of features:

- **Singleton / literal types** — every literal value has a type that is just that value: `42` has type `42`, `"hello"` has type `"hello"`. These types are subtypes of their widened form (`42 <: Int`).
- **`inline` parameters** — force compile-time evaluation of arguments, ensuring values are known statically.
- **`constValue[T]`** — extract the value from a singleton type at compile time.
- **`compiletime.ops`** — type-level arithmetic, boolean, and string operations on singleton types.
- **Match types** — compute types from types, enabling type-level conditionals and recursion.

Together, these let you encode sizes, dimensions, and capacities in types — the same role Rust's const generics play — but with more generality since any singleton type works, not just primitive scalars.

## What constraint it enforces

**Distinct literal values produce distinct types. Type-level operations on singleton types are checked at compile time, so dimensional mismatches, invalid sizes, and arithmetic errors become type errors.**

More specifically:

- **Distinct values = distinct types.** `Matrix[3, 4]` and `Matrix[4, 3]` are different types. A function expecting one rejects the other.
- **Compile-time evaluation.** An `inline` parameter substitutes the argument *expression* into the body at the call site; on its own it does not demand a constant. Constant-ness is forced only where the body demands it — `inline if`, `inline match`, `constValue`, `error`, or `Expr.valueOrAbort` in a macro. Those constructs are what reject a runtime value.
- **Type-level arithmetic.** `compiletime.ops.int.*` provides `+`, `-`, `*`, `/`, `<`, `>=`, etc. on singleton `Int` types, checked at compile time.

## Minimal snippet

```scala
import scala.compiletime.constValue
import scala.compiletime.ops.int.*

// A type-safe vector with its length in the type
class Vec[N <: Int](val data: Array[Double]):
  inline def length: Int = constValue[N]

// Type-level addition: concatenating two vectors
def concat[A <: Int, B <: Int](a: Vec[A], b: Vec[B]): Vec[A + B] =
  Vec[A + B](a.data ++ b.data)

val v3 = Vec[3](Array(1.0, 2.0, 3.0))
val v2 = Vec[2](Array(4.0, 5.0))
val v5: Vec[5] = concat(v3, v2)      // OK — 3 + 2 = 5
// val bad: Vec[4] = concat(v3, v2)   // compile error — Vec[5] ≠ Vec[4]
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Match types** [-> T41](T41-match-types.md)(T41-match-types.md) | Match types enable type-level pattern matching on singleton types — the mechanism for type-level `if`/`else` and recursion. |
| **Inline & compiletime** [-> T16](T16-compile-time-ops.md)(T16-compile-time-ops.md) | `inline` forces compile-time evaluation; `constValue` bridges type-level singletons to value-level constants. These are the runtime extraction mechanism. |
| **Opaque types** [-> T03](T03-newtypes-opaque.md)(T03-newtypes-opaque.md) | Combine with singleton types for zero-cost dimensional wrappers: `opaque type Meters = Double` with type-level unit tracking. |
| **Generics** [-> catalog/T04](T04-generics-bounds.md) | Singleton types slot into generic type parameters with upper bounds: `[N <: Int]`. |
| **Type lambdas** [-> T40](T40-type-lambdas.md)(T40-type-lambdas.md) | Higher-kinded abstractions can be parameterized by singleton types for compile-time polymorphism. |

## Gotchas and limitations

1. **No first-class const parameters.** Unlike Rust's `const N: usize`, Scala uses regular type parameters bounded by singleton types (`N <: Int`). This means you write `Vec[3]` rather than `Vec<3>`, and the compiler infers/checks through the singleton type system.

2. **`constValue` requires a literal/singleton type.** If the type parameter has been widened to `Int` (e.g., through inference), `constValue` cannot extract the value and compilation fails.

3. **Type-level ops cover several primitive kinds.** `compiletime.ops` provides operation packages for `int` and `long`, and also `float`, `double`, `string`, `boolean`, and `any`. For anything not covered, you need custom match types.

4. **No runtime-to-compile-time bridge.** You cannot take a runtime `Int` and use it as a singleton type parameter. The value must be a literal or computed from other compile-time values. An `inline` parameter is *not* the gate: `inline def twice(inline n: Int) = n + n` happily accepts `twice(scala.util.Random.nextInt())`, because the argument is simply substituted into the body. To actually require a constant, consume the parameter with something that needs one — `inline if`, `inline match`, `constValue`, or `error`.

5. **Error messages can be cryptic.** When type-level arithmetic fails, the operands are already reduced, so you see the computed `(5 : Int)` not matching `(4 : Int)` — clear enough — but complex expressions and unreduced match types produce long type-level error messages.

6. **Match type reduction.** Complex type-level computations using match types may hit the compiler's reduction limit. Use `@annotation.tailrec`-style patterns or increase the limit if needed.

## Beginner mental model

Think of singleton types as **promoting values to the type level**. The number `3` is both a value (of type `Int`) and a type (the type `3`, which is a subtype of `Int`). Once a value is in the type, the compiler can do arithmetic on it, compare it, and reject mismatches — all before your code runs.

Compared to Rust's const generics: Rust added a dedicated syntax (`const N: usize`) for a specific use case. Scala 3 achieves the same result through its existing type system — singleton types were already there, and `compiletime.ops` adds the arithmetic. The result is more general (any singleton type, not just scalars) but less syntactically obvious.

## Example A — Type-safe matrix multiplication

```scala
import scala.compiletime.ops.int.*

class Matrix[Rows <: Int, Cols <: Int](
  val data: Array[Array[Double]]
)

// Multiplication: (M × N) * (N × P) = (M × P)
// The shared dimension N must match — enforced by the type system
def multiply[M <: Int, N <: Int, P <: Int](
  a: Matrix[M, N],
  b: Matrix[N, P]   // N must be the same singleton type
): Matrix[M, P] =
  // implementation omitted — the constraint is in the signature
  ???

val m23 = Matrix[2, 3](Array(Array(1.0, 2.0, 3.0), Array(4.0, 5.0, 6.0)))
val m34 = Matrix[3, 4](???)
val result: Matrix[2, 4] = multiply(m23, m34)  // OK — inner dimension 3 matches

// val bad = multiply(m23, Matrix[4, 2](???))
// compile error: Matrix[3, _] expected but Matrix[4, _] found
```

## Example B — Compile-time bounds checking

```scala
import scala.compiletime.ops.int.*

type InRange[N <: Int, Lo <: Int, Hi <: Int] = (N >= Lo) match
  case true => (N <= Hi) match
    case true  => N
    case false => Nothing
  case false => Nothing

// Only accepts singleton Int types in [1, 65535]
type Port[N <: Int] = InRange[N, 1, 65535]

inline def port[N <: Int](using ev: Port[N] =:= N): N = compiletime.constValue[N]

val p80: 80 = port[80]           // OK
val p443: 443 = port[443]        // OK
// val bad = port[0]              // compile error: Nothing ≠ 0
// val bad2 = port[70000]         // compile error: Nothing ≠ 70000
```

## Common type-checker errors and how to read them

### `Found: Vec[5], Required: Vec[4]`

```
Found:    Vec[(5 : Int)]
Required: Vec[(4 : Int)]
```

**Meaning:** Type-level arithmetic produced a different result than expected. The compiler computed 3 + 2 = 5 but you declared 4. Fix the expected type. Note that `compiletime.ops` types are reduced *before* the mismatch is printed, so you see the computed `Vec[(5 : Int)]` rather than an unreduced `Vec[(3 : Int) + (2 : Int)]`.

### `Note: a match type could not be fully reduced`

```
Found:    (n : N)
Required: InRange[N, (1 : Int), (100 : Int)]

Note: a match type could not be fully reduced:

  trying to reduce  InRange[N, (1 : Int), (100 : Int)]
  failed since selector N >= (1 : Int)
  does not match  case (true : Boolean) => ...
  and cannot be shown to be disjoint from it either.
```

**Meaning:** There is no standalone "cannot reduce" error — you get an ordinary type mismatch, and the attached note explains *why* the match type is still stuck. Here `N` is abstract, so the selector `N >= 1` reduces to neither `true` nor `false`, and reduction cannot advance past the first case. Ensure the call site pins `N` to a literal singleton type.

### `Cannot prove that Port[(0 : Int)] =:= (0 : Int).`

```
-- [E172] Type Error: ...
13 |val bad = port[0]
   |                ^
   |                Cannot prove that Port[(0 : Int)] =:= (0 : Int).
```

**Meaning:** A type-level bounds check reduced to `Nothing`, so the requested evidence does not exist and the value is out of range. Missing `=:=` evidence gets this dedicated E172 wording — it is *not* reported as a generic `No given instance of type =:=[...]` message.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Encode valid ranges in types so out-of-bounds values don't compile.
- [-> UC-18](../usecases/UC18-type-arithmetic.md) — Type-level arithmetic for dimensional analysis and matrix operations.
- [-> UC-12](../usecases/UC12-compile-time.md) — Compile-time computation and specialization.

## Source anchors

- [Scala 3 Reference — Literal Types](https://docs.scala-lang.org/scala3/reference/new-types/literal-types.html)
- [Scala 3 Reference — Inline](https://docs.scala-lang.org/scala3/reference/metaprogramming/inline.html)
- [Scala 3 Reference — Match Types](https://docs.scala-lang.org/scala3/reference/new-types/match-types.html)
- [scala.compiletime.ops API](https://scala-lang.org/api/3.x/scala/compiletime/ops.html)
