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
- **Compile-time evaluation.** `inline` parameters must resolve to compile-time constants. The compiler rejects calls with runtime values where compile-time values are required.
- **Type-level arithmetic.** `compiletime.ops.int.*` provides `+`, `-`, `*`, `/`, `<`, `>=`, etc. on singleton `Int` types, checked at compile time.

## Minimal snippet

```scala
import scala.compiletime.constValue
import scala.compiletime.ops.int.*

// A type-safe vector with its length in the type
class Vec[N <: Int](val data: Array[Double]):
  def length: Int = constValue[N]

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
| **Match types** [-> catalog/03](T41-match-types.md) | Match types enable type-level pattern matching on singleton types — the mechanism for type-level `if`/`else` and recursion. |
| **Inline & compiletime** [-> catalog/17](T16-compile-time-ops.md) | `inline` forces compile-time evaluation; `constValue` bridges type-level singletons to value-level constants. These are the runtime extraction mechanism. |
| **Opaque types** [-> catalog/12](T03-newtypes-opaque.md) | Combine with singleton types for zero-cost dimensional wrappers: `opaque type Meters = Double` with type-level unit tracking. |
| **Generics** [-> catalog/T04](T04-generics-bounds.md) | Singleton types slot into generic type parameters with upper bounds: `[N <: Int]`. |
| **Type lambdas** [-> catalog/02](T40-type-lambdas.md) | Higher-kinded abstractions can be parameterized by singleton types for compile-time polymorphism. |

## Gotchas and limitations

1. **No first-class const parameters.** Unlike Rust's `const N: usize`, Scala uses regular type parameters bounded by singleton types (`N <: Int`). This means you write `Vec[3]` rather than `Vec<3>`, and the compiler infers/checks through the singleton type system.

2. **`constValue` requires a literal/singleton type.** If the type parameter has been widened to `Int` (e.g., through inference), `constValue` cannot extract the value and compilation fails.

3. **Type-level arithmetic is limited to `Int` and `Long`.** `compiletime.ops` provides operations for `int` and `long` singleton types. For other numeric types, you need custom match types.

4. **No runtime-to-compile-time bridge.** You cannot take a runtime `Int` and use it as a singleton type parameter. The value must be a literal or computed from other compile-time values. Use `inline` parameters to ensure arguments are compile-time constants.

5. **Error messages can be cryptic.** When type-level arithmetic fails, the error mentions types like `3 + 2` not matching `4`, which is clear, but complex expressions produce long type-level error messages.

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

val m23 = Matrix[2, 3](Array(Array(1, 2, 3), Array(4, 5, 6)))
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
Found:    Vec[(3 : Int) + (2 : Int)]
Required: Vec[(4 : Int)]
```

**Meaning:** Type-level arithmetic produced a different result than expected. The compiler computed 3 + 2 = 5 but you declared 4. Fix the expected type.

### `Cannot reduce match type`

```
Cannot reduce `InRange[N, 1, 100]` — type parameter N is not a concrete singleton type.
```

**Meaning:** The compiler cannot evaluate the match type because the type parameter isn't a known literal. Ensure the call site provides a literal type (use `inline` parameters to force this).

### `No given instance of type =:=[Nothing, N]`

**Meaning:** A type-level bounds check reduced to `Nothing`, meaning the value is out of range. The constraint was violated.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Encode valid ranges in types so out-of-bounds values don't compile.
- [-> UC-18](../usecases/UC18-type-arithmetic.md) — Type-level arithmetic for dimensional analysis and matrix operations.
- [-> UC-12](../usecases/UC12-compile-time.md) — Compile-time computation and specialization.

## Source anchors

- [Scala 3 Reference — Literal Types](https://docs.scala-lang.org/scala3/reference/new-types/literal-types.html)
- [Scala 3 Reference — Inline](https://docs.scala-lang.org/scala3/reference/metaprogramming/inline.html)
- [Scala 3 Reference — Match Types](https://docs.scala-lang.org/scala3/reference/new-types/match-types.html)
- [scala.compiletime.ops API](https://scala-lang.org/api/3.x/scala/compiletime/ops.html)
