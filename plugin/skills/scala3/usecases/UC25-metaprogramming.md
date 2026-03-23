# Metaprogramming

## The Constraint

Generate, inspect, or transform code at compile time. Scala 3 offers a layered metaprogramming stack: `inline` for compile-time expansion, `compiletime` operations for type-level computation, and quotes/splices for full macro power — all with stronger safety guarantees than Scala 2 macros.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Inline | Guaranteed compile-time inlining; `inline if`, `inline match` for specialisation | [-> T16](T16-compile-time-ops.md)(../catalog/T16-compile-time-ops.md) |
| compiletime ops | `constValue`, `summonInline`, `erasedValue`, `error` for type-level computation | [-> T16](T16-compile-time-ops.md)(../catalog/T16-compile-time-ops.md) |
| Macros (quotes & splices) | `'{ ... }` and `${ ... }` for AST-level code generation | [-> T17](T17-macros-metaprogramming.md)(../catalog/T17-macros-metaprogramming.md) |
| Match types | Compute types from types at compile time without macros | [-> T41](T41-match-types.md)(../catalog/T41-match-types.md) |
| Derivation | Compiler-assisted type class derivation via `Mirror` | [-> T06](T06-derivation.md)(../catalog/T06-derivation.md) |

## Patterns

### 1 — Inline for compile-time branching

`inline` methods are expanded at the call site. `inline if` and `inline match` resolve branches at compile time, eliminating dead code.

```scala
inline def stringify[T](value: T): String =
  inline value match
    case _: Int     => "an integer"
    case _: String  => "a string"
    case _: Boolean => "a boolean"
    case _          => "something else"

// At compile time, only one branch survives:
val s = stringify(42)    // compiles to: val s = "an integer"
```

### 2 — compiletime operations for type-level queries

Query types at compile time without writing a full macro.

```scala
import scala.compiletime.*
import scala.deriving.Mirror

inline def fieldNames[T](using m: Mirror.ProductOf[T]): List[String] =
  constValueTuple[m.MirroredElemLabels].toList.map(_.toString)

case class User(name: String, age: Int, active: Boolean)

val names = fieldNames[User]   // List("name", "age", "active") — computed at compile time
```

### 3 — Quotes and splices for code generation

For full AST manipulation, use `'{ expr }` (quote) to represent code and `${ expr }` (splice) to insert generated code.

```scala
import scala.quoted.*

// Macro definition (in a separate compilation unit):
inline def showExpr(inline expr: Any): String = ${ showExprImpl('expr) }

def showExprImpl(expr: Expr[Any])(using Quotes): Expr[String] =
  import quotes.reflect.*
  val source = expr.asTerm.pos.sourceCode.getOrElse("<unknown>")
  Expr(s"$source")

// Usage:
val debug = showExpr(1 + 2)    // "1 + 2" — the source text, computed at compile time
```

### 4 — Macro for compile-time validation

Validate values at compile time when they are known literals.

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

// Usage:
val r = Regex.checked("[a-z]+")    // OK
// val bad = Regex.checked("[a-z")  // compile error: Invalid regex: ...
```

### 5 — Mirror-based derivation

Use `Mirror` to derive type class instances generically for product and sum types.

```scala
import scala.deriving.Mirror
import scala.compiletime.*

trait Show[T]:
  def show(t: T): String

object Show:
  given Show[Int] with
    def show(t: Int): String = t.toString
  given Show[String] with
    def show(t: String): String = s"\"$t\""

  inline given derived[T](using m: Mirror.ProductOf[T]): Show[T] =
    new Show[T]:
      def show(t: T): String =
        val elems = t.asInstanceOf[Product].productIterator.mkString(", ")
        s"${constValue[m.MirroredLabel]}($elems)"

case class Point(x: Int, y: Int) derives Show

summon[Show[Point]].show(Point(1, 2))   // "Point(1, 2)"
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Inline | `@inline` annotation — advisory only; JVM decides | `inline` keyword — guaranteed expansion; compile-time branching |
| Compile-time ops | Not available; required macros for even simple type queries | `compiletime.*` — summonInline, constValue, error without macros |
| Macros | `scala.reflect` macros — powerful but fragile; tied to compiler internals | Quotes/splices — principled, sandboxed, phase-correct |
| Code generation | Macro annotations (`@deriveX`) and whitebox macros | `derives` clause + `Mirror`; macros for advanced cases |
| Match types | Not available | First-class; compute return types from input types without macros |

## When to Use Which Feature

**Start with `inline`** for specialisation, dead-code elimination, and simple compile-time branching. Most "I need a macro" situations are solved by `inline` + `compiletime` ops.

**Use `Mirror`-based derivation** for type class instances over case classes and enums. No macros needed — the compiler provides the structural information.

**Use match types** when you need to compute a return type from an input type (e.g., mapping a tuple of types to a tuple of values).

**Reach for quotes/splices** only when you need to inspect or generate ASTs — compile-time validation, source-code logging, or performance-critical code generation. Keep macros in a separate compilation unit.
