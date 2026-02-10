# 17 -- Inline and Compile-Time Operations

> **Since:** Scala 3.0

## What It Is

Scala 3's `inline` keyword is a soft modifier that **guarantees** a definition will be inlined at every call site -- unlike the advisory `@inline` annotation from Scala 2. Inline definitions enable compile-time evaluation: `inline val` produces a compile-time constant, `inline def` is expanded in place, `inline if` and `inline match` require their conditions/scrutinees to reduce at compile time, and `transparent inline` methods can specialize their return type based on the expansion. The `scala.compiletime` package complements this with operations like `constValue`, `erasedValue`, `summonInline`, `summonFrom`, `error`, and the `scala.compiletime.ops` type-level arithmetic/boolean/string operations.

## What Constraint It Lets You Express

**`inline` guarantees code is expanded at the call site and evaluated at compile time when conditions are constants. `compiletime.ops` lifts arithmetic, boolean, and string operations to the type level. Together they enable conditional compilation, type-level computation, and compile-time specialization -- all checked by the compiler, not deferred to runtime.**

## Minimal Snippets

### inline val and inline def

```scala
object Config:
  inline val logging = false

inline def log(msg: String)(op: => Unit): Unit =
  inline if Config.logging then
    println(msg)
    op
  else op

log("debug") { heavyComputation() }
// With logging = false, compiles to just: heavyComputation()
```

### Recursive inline (compile-time unrolling)

```scala
inline def power(x: Double, n: Int): Double =
  if n == 0 then 1.0
  else if n == 1 then x
  else
    val y = power(x, n / 2)
    if n % 2 == 0 then y * y else y * y * x

power(expr, 10)
// Unrolls to straight-line multiplication code (no loop)
```

### transparent inline (return type specialization)

```scala
transparent inline def choose(b: Boolean): Any =
  inline if b then "hello" else 42

val x = choose(true)   // static type: String
val y = choose(false)  // static type: Int
```

### inline match (type-level dispatch)

```scala
transparent inline def defaultValue[T] =
  inline erasedValue[T] match
    case _: Int     => Some(0)
    case _: Boolean => Some(false)
    case _          => None

val d: Some[Int] = defaultValue[Int]       // type is Some[Int], not Option[Int]
val n: None.type = defaultValue[String]
```

### compiletime.ops (type-level arithmetic)

```scala
import scala.compiletime.ops.int.*

val x: 1 + 2 * 3 = 7            // type-level computation
val y: S[S[0]]   = 2             // S is successor: S[0] = 1, S[1] = 2

type Factorial[N <: Int] <: Int = N match
  case 0    => 1
  case S[n] => N * Factorial[n]

val f: Factorial[5] = 120
```

### constValue and erasedValue

```scala
import scala.compiletime.{constValue, erasedValue}
import scala.compiletime.ops.int.S

transparent inline def toIntC[N]: Int =
  inline constValue[N] match
    case 0        => 0
    case _: S[n1] => 1 + toIntC[n1]

inline val two = toIntC[2]  // computes to 2 at compile time
```

### summonInline and summonFrom

```scala
import scala.compiletime.{summonInline, summonFrom}

// summonFrom: functional implicit search with fallback
inline def setFor[T]: Set[T] = summonFrom {
  case given Ordering[T] => new TreeSet[T]
  case _                 => new HashSet[T]
}

// summonInline: delayed summon with proper error messages
inline def showType[T](using T: Type[T]): String =
  summonInline[Show[T]].show
```

### compiletime.error

```scala
import scala.compiletime.{error, codeOf}

inline def requirePositive(inline n: Int): Int =
  inline if n <= 0 then error("Expected positive, got: " + codeOf(n))
  else n

requirePositive(-1)  // compile error: Expected positive, got: -1
```

## Interaction with Other Features

| Feature | Interaction |
|---|---|
| **Match types** | `inline match` and match types are complementary. `inline match` evaluates at the term level during inlining; match types compute at the type level. They can be combined: a `transparent inline def` with an `inline match` whose return type is a match type. |
| **Macros (quotes/splices)** | Top-level splices `${ ... }` must appear inside `inline def`. Inline is the entry point to macro expansion. |
| **Given instances** | `transparent inline given` is special: if inlining produces an error, it is treated as an implicit search miss (not a hard error), allowing fallback to other candidates. |
| **Singleton types** | `inline val` always has a singleton literal type (e.g., `inline val x = 4` has type `4`). `transparent inline` methods can return singleton types. |
| **Type classes / derivation** | `summonInline` and `summonFrom` enable compile-time type class dispatch with branch elimination. |
| **Opaque types** | `constValue` can extract the underlying literal from an opaque type alias if it is a constant type. |
| **Erased definitions** | `erasedValue[T]` pretends to produce a value of type `T` for compile-time scrutiny; calling it at runtime is an error. It is related to `erased` parameters but serves a different purpose. |

## Gotchas and Limitations

- **Recursion depth limit.** Recursive inline methods are limited to 32 successive inlines by default. Adjust with `-Xmax-inlines`.
- **Inline methods must be fully applied.** A partial application like `Logger.log("msg", 2)` without all argument lists is ill-formed. Use wildcard arguments (`_`) to eta-expand.
- **Inline methods are effectively final.** They cannot be overridden (except by other inline methods). An abstract inline method can only be implemented by another inline method and cannot be called via dynamic dispatch.
- **`inline if` / `inline match` must reduce.** If the condition or scrutinee is not a compile-time constant, the compiler emits an error -- not a fallback to runtime.
- **`transparent inline` changes typing behavior.** The return type can be more specific than declared, which can cause unexpected type mismatches if callers depend on the declared type.
- **`compiletime.ops` requires singleton types.** Type-level operations only evaluate when all arguments are singleton types. Non-singleton arguments produce abstract types, not errors.
- **`summonFrom` can raise ambiguity errors.** If multiple given instances match a pattern in `summonFrom`, an ambiguity error is reported.
- **By-name vs. inline parameters.** `inline` parameters are like by-name but may be duplicated in the expansion. By-value parameters are bound to a `val`; by-name to a `def`.

## Use-Case Cross-References

- `[-> UC-01](../usecases/01-preventing-invalid-states.md)` Compile-time configuration and conditional compilation (logging, debug modes).
- `[-> UC-05](../usecases/05-compile-time-programming.md)` Type-level arithmetic for sized vectors, matrix dimensions, or bounded naturals.
- `[-> UC-08](../usecases/08-equality-comparison.md)` Compile-time specialization of type class instances with `summonFrom`.
- `[-> UC-11](../usecases/11-type-level-arithmetic.md)` Recursive inline for unrolling loops or generating specialized code paths.
- `[-> UC-05](../usecases/05-compile-time-programming.md)` Custom compile-time error messages for invalid type combinations.
- `[-> UC-05](../usecases/05-compile-time-programming.md)` Entry point for macro definitions via `inline def` + `${ ... }`.
