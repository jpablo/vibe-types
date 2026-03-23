# Compile-Time Programming

## The Constraint

Move computation and validation from runtime to compile time. Errors surface during compilation, not in production. Constants are evaluated by the compiler, not by the JVM.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Inline | Compile-time evaluation, branching, and inlining | [-> T16](T16-compile-time-ops.md)(../catalog/T16-compile-time-ops.md) |
| Match types | Type-level pattern matching; compute types from types | [-> T41](T41-match-types.md)(../catalog/T41-match-types.md) |
| Compiletime ops | Type-level arithmetic and string operations | [-> T16](T16-compile-time-ops.md)(../catalog/T16-compile-time-ops.md) |
| Macros | Full compile-time metaprogramming via quotes and splices | [-> T17](T17-macros-metaprogramming.md)(../catalog/T17-macros-metaprogramming.md) |
| Type lambdas | Higher-kinded type-level functions | [-> T40](T40-type-lambdas.md)(../catalog/T40-type-lambdas.md) |

## Patterns

### 1 — `inline if` / `inline match` for compile-time branching

When the scrutinee is known at compile time, `inline match` selects a branch during compilation. Dead branches are eliminated entirely.

```scala
inline def describe(inline x: Any): String =
  inline x match
    case _: Int    => "integer"
    case _: String => "string"
    case _: Boolean => "boolean"

val a: "integer" = describe(42)       // literal type — resolved at compile time
val b: "string"  = describe("hello")

// describe(List(1))  // compile error — no matching branch
```

Code in eliminated branches is not type-checked, enabling conditional compilation:

```scala
inline val debug = false

inline def log(inline msg: String): Unit =
  inline if debug then println(msg)
  // when debug is false, println call is erased entirely
```

### 2 — `compiletime.ops` for type-level arithmetic

Perform arithmetic and comparisons at the type level using singleton types and built-in operations.

```scala
import compiletime.ops.int.*

type Pos[N <: Int] = N > 0

// A vector whose size is tracked at the type level
class Vec[N <: Int] private (val elems: Array[Double]):
  def append[M <: Int](other: Vec[M]): Vec[N + M] =
    Vec(elems ++ other.elems)

  def head(using N > 0 =:= true): Double = elems(0)

object Vec:
  def apply[N <: Int](elems: Array[Double]): Vec[N] = new Vec(elems)
  def of(xs: Double*): Vec[xs.length.type] = new Vec(xs.toArray)

val v2: Vec[2] = Vec.of(1.0, 2.0)
val v3: Vec[3] = Vec.of(3.0, 4.0, 5.0)
val v5: Vec[5] = v2.append(v3)    // 2 + 3 = 5, computed at compile time
```

### 3 — `constValue` / `constValueTuple` for extracting singleton types

Pull compile-time-known types into runtime values without boilerplate.

```scala
import compiletime.{constValue, constValueTuple}

// Extract a singleton type as a runtime value
val n: 42 = constValue[42]

// Extract a tuple of singletons
val rgb = constValueTuple[("red", "green", "blue")]
// rgb: ("red", "green", "blue") = ("red", "green", "blue")

// Useful in combination with match types:
type ElementNames[T] = T match
  case EmptyTuple => EmptyTuple
  case (name, _) *: rest => name *: ElementNames[rest]

type Schema = ("name", String) *: ("age", Int) *: EmptyTuple
type Names = ElementNames[Schema]   // ("name", "age")
val names = constValueTuple[Names]  // ("name", "age") at runtime
```

### 4 — Macro-based compile-time validation

When `inline` is not enough, macros give full access to the AST at compile time. Validate string formats, parse DSLs, or generate code.

```scala
import scala.quoted.*

object Regex:
  inline def checked(inline pattern: String): scala.util.matching.Regex =
    ${ checkedImpl('pattern) }

  private def checkedImpl(pattern: Expr[String])(using Quotes): Expr[scala.util.matching.Regex] =
    import quotes.reflect.*
    pattern.valueOrAbort match
      case p =>
        try
          java.util.regex.Pattern.compile(p)
          '{ new scala.util.matching.Regex($pattern) }
        catch
          case e: java.util.regex.PatternSyntaxException =>
            report.errorAndAbort(s"Invalid regex: ${e.getMessage}")

// Usage
val email = Regex.checked("""[\w.]+@[\w.]+""")   // compiles
// val bad = Regex.checked("""[unclosed""")        // compile error: Invalid regex
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Compile-time branching | Not available — all branches exist at runtime; `@switch` only optimized matching | `inline if` / `inline match` — branches resolved and eliminated at compile time |
| Type-level arithmetic | Church encodings via Shapeless `Nat`, or literal type hacks — slow compilation, poor errors | `compiletime.ops.int.*` — built-in, fast, clear error messages |
| Extracting singletons | `shapeless.Witness` — library-level, limited | `constValue` / `constValueTuple` — built into the language |
| Macros | `scala.reflect` macros — complex, tightly coupled to compiler internals, not portable | Quotes and splices (`'{ }` / `${ }`) — principled, hygienic, based on TASTy |
| Type lambdas | `({type L[A] = Either[String, A]})#L` — a hack with poor tooling | `[A] =>> Either[String, A]` — first-class syntax |

## When to Use Which Feature

**`inline`** is the first tool to reach for. It handles constant folding, dead-branch elimination, and compile-time validation of literals. Most compile-time needs can be met with `inline def`, `inline if`, and `inline match` alone.

**Match types** are appropriate when you need to compute a *type* from another type — mapping a tuple of types, selecting a codec based on a type parameter, or implementing type-level recursion. They replace Shapeless-style type-level programming for many use cases.

**`compiletime.ops`** handles type-level arithmetic and comparisons. Use it when your types carry numeric parameters (vector lengths, matrix dimensions, bounded integers) and you want the compiler to verify arithmetic properties.

**Macros** are the last resort. Use them when you need to inspect or transform the AST at compile time — validating string literals against a grammar, generating boilerplate from annotations, or embedding external DSLs. Prefer `inline` when it suffices, since macros add compilation complexity and are harder to maintain.

**Type lambdas** are a building block, not a technique on their own. Use them when higher-kinded types need partial application — e.g., passing `[A] =>> Either[Error, A]` where a `F[_]` is expected.
