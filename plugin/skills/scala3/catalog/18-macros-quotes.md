# 18 -- Macros: Quotes and Splices

> **Since:** Scala 3.0

## What It Is

Scala 3 macros are built on a principled multi-stage programming system. **Quotes** `'{ ... }` delay (stage) code for a future compilation phase, producing a value of type `Expr[T]`. **Splices** `${ ... }` evaluate code one stage earlier, inserting the resulting AST into the surrounding quote or program. A macro is an `inline def` whose body contains a top-level splice that calls a separately compiled method to generate code at compile time. The system is statically typed, hygienic, and cross-stage safe: `Expr[T]` tracks the expression type, `Type[T]` carries type information across stages, and `Quotes` provides the context for quote operations.

## What Constraint It Lets You Express

**Quotes and splices enable arbitrary compile-time code generation with full type safety. You can inspect expression structure via quote pattern matching, transform ASTs, summon implicits at the call site, produce custom compile errors, and generate specialized code -- all while the compiler guarantees that generated code is well-typed and hygienic.**

## Minimal Snippets

### Basic macro (code generation)

```scala
// Macro implementation (must be compiled before use)
import scala.quoted.*

def unrolledPowerCode(x: Expr[Double], n: Int)(using Quotes): Expr[Double] =
  if n == 0 then '{ 1.0 }
  else if n == 1 then x
  else '{ $x * ${ unrolledPowerCode(x, n - 1) } }

// Macro entry point
inline def power(x: Double, inline n: Int): Double =
  ${ powerCode('x, 'n) }

def powerCode(x: Expr[Double], n: Expr[Int])(using Quotes): Expr[Double] =
  unrolledPowerCode(x, n.valueOrAbort)
```

```scala
// Usage
power(3.14, 3)  // expands to: 3.14 * 3.14 * 3.14
```

### Lifting values into quotes

```scala
val expr2: Expr[Int] = Expr(1 + 1)  // lifts the value 2 into '{ 2 }
// Compare with '{ 1 + 1 } which stages the computation
```

Custom lifting via `ToExpr`:

```scala
given OptionToExpr: [T: {Type, ToExpr}] => ToExpr[Option[T]]:
  def apply(opt: Option[T])(using Quotes): Expr[Option[T]] =
    opt match
      case Some(x) => '{ Some[T](${ Expr(x) }) }
      case None    => '{ None }
```

### Extracting values from quotes

```scala
def optimize(n: Expr[Int])(using Quotes): Expr[Int] =
  n match
    case Expr(0) => '{ 0 }        // n is a known constant 0
    case Expr(v) => Expr(v * 2)   // n is a known constant, double it
    case _       => '{ $n * 2 }   // runtime -- generate multiplication
```

### Quote pattern matching (analytical macros)

```scala
def fusedPowCode(x: Expr[Double], n: Expr[Int])(using Quotes): Expr[Double] =
  x match
    case '{ power($y, $m) } =>             // structural decomposition
      fusedPowCode(y, '{ $n * $m })        // fuse: (y^m)^n => y^(n*m)
    case _ =>
      '{ power($x, $n) }
```

### Type variables in patterns

```scala
def fuseMapCode(x: Expr[List[Int]])(using Quotes): Expr[List[Int]] =
  x match
    case '{ ($ls: List[t]).map[u]($f).map[Int]($g) } =>
      '{ $ls.map($g.compose($f)) }   // fuse consecutive maps
    case _ => x
```

### Working with types

```scala
def emptyOf[T: Type](using Quotes): Expr[Option[T]] =
  Type.of[T] match
    case '[String]  => '{ Some("") }
    case '[Int]     => '{ Some(0) }
    case '[List[t]] => '{ Some(List.empty[t]) }
    case _          => '{ None }
```

### Summoning implicits in macros

```scala
inline def setFor[T]: Set[T] =
  ${ setForExpr[T] }

def setForExpr[T: Type](using Quotes): Expr[Set[T]] =
  Expr.summon[Ordering[T]] match
    case Some(ord) => '{ new TreeSet[T]()($ord) }
    case _         => '{ new HashSet[T] }
```

## Interaction with Other Features

| Feature | Interaction |
|---|---|
| **`inline`** | Macros are defined as `inline def` with a body containing `${ ... }`. The inline mechanism is the user-facing entry point; splicing is hidden from end users. |
| **`transparent inline`** | A transparent inline macro can specialize its return type based on the generated code, enabling whitebox-style macros. |
| **`Type[T]`** | Required whenever a generic type `T` is used across staging levels. The compiler performs "type healing" to insert `Type` witnesses automatically. `Type[T <: AnyKind]` supports higher-kinded types. |
| **`Quotes`** | Every quote requires a `Quotes` context. Each splice provides a fresh `Quotes` to its body. `Quotes` also provides the entry point to the reflection API. |
| **Reflection API** | `quotes.reflect` exposes the full typed AST, enabling low-level tree inspection and construction beyond what quote patterns support. |
| **`ExprMap`** | A trait for transforming all sub-expressions of an `Expr`, useful for bottom-up or top-down rewrites of generated code. |
| **Compile-time ops** | `compiletime.error` can be called from macro implementations to produce custom compile errors. `constValue` / `erasedValue` complement macros for simpler type-level computations. |
| **Staging (`scala.quoted.staging`)** | The same `Expr`/`Type`/`Quotes` abstractions support runtime multi-stage programming via `staging.run`, using a `staging.Compiler` backed by the real Scala 3 compiler. |
| **Separate compilation** | The macro implementation method must be compiled before the call site. When defined in the same project, the compiler automatically detects and defers compilation of files that use macros not yet compiled. |

## Gotchas and Limitations

- **Separate compilation requirement.** The method called in a top-level splice must be already compiled. Cyclic dependencies between macro definition and use cause compilation failures.
- **Level consistency.** Local variables can only be used at the same staging level as their definition. A variable defined at level 0 cannot appear inside a quote (level 1) without being lifted, and a variable at level 1 cannot appear in a splice (level 0).
- **No cross-stage persistence of locals.** You cannot reference a local runtime variable directly inside a quote. Use `Expr(value)` to lift it or `'{ localVal }` if it is defined at the right level.
- **Scope extrusion.** Storing an `Expr` via mutable state and using it outside its defining splice scope causes a runtime error (checked with `-Xcheck-macros`). Each `Expr` tracks its scope.
- **`isInstanceOf[Expr[T]]` is unsound.** Due to erasure, runtime type checks on `Expr` ignore the type parameter. Use `isExprOf[T]` and `asExprOf[T]` instead.
- **Top-level splice restrictions.** A top-level splice must contain a single call to a compiled static method with arguments that are literals, quoted expressions, `Type.of` calls, or `Quotes` references. No nested splices in top-level splices.
- **Quote pattern closedness.** A `${ }` in a quote pattern only matches if the extracted expression is closed (does not refer to variables bound in the pattern). Use HOAS patterns `$f(y)` to capture expressions that reference pattern-bound variables.
- **Type variable convention.** In quote patterns, lowercase type names are automatically treated as type variables. Use backticks to refer to an existing type with a lowercase name.
- **`Expr` is covariant.** `Expr[B]` is a subtype of `Expr[A]` if `B <: A`. This is sound but means the static type may be less precise than the actual expression type.

## Use-Case Cross-References

- `[-> UC-01](../usecases/01-preventing-invalid-states.md)` Compile-time code generation for boilerplate elimination (serializers, codecs, lenses).
- `[-> UC-05](../usecases/05-compile-time-programming.md)` Optimizing DSLs by fusing operations at compile time via quote pattern matching.
- `[-> UC-08](../usecases/08-equality-comparison.md)` Conditional implicit summoning in macros with `Expr.summon`.
- `[-> UC-11](../usecases/11-type-level-arithmetic.md)` Staged computation for performance-critical numeric code (power, polynomial evaluation).
- `[-> UC-05](../usecases/05-compile-time-programming.md)` Custom compile-time error messages for domain-specific validation.
- `[-> UC-05](../usecases/05-compile-time-programming.md)` Entry point: `inline def` + `${ ... }` connects inline (doc 17) to macros.
- `[-> UC-05](../usecases/05-compile-time-programming.md)` Runtime multi-stage programming with `scala.quoted.staging`.
