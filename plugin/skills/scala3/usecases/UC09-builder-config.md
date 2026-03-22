# DSL and Builder Patterns

## The Constraint

Build type-safe DSLs and fluent APIs where the compiler enforces correct usage. Invalid construction sequences, missing required fields, and type-incorrect compositions must be compile errors.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Context functions | Scoped DSL blocks with an implicit receiver | [-> catalog/06](../catalog/T42-context-functions.md) |
| Extension methods | Fluent chaining without inheritance or wrappers | [-> catalog/07](../catalog/T19-extension-methods.md) |
| Dependent function types | Return types that depend on argument values/types | [-> catalog/04](../catalog/T09-dependent-types.md) |
| Opaque types | Lightweight wrapper types for DSL tokens and identifiers | [-> catalog/12](../catalog/T03-newtypes-opaque.md) |
| Inline | Compile-time DSL validation and expansion | [-> catalog/17](../catalog/T16-compile-time-ops.md) |
| GADTs | Typed expression trees with type-safe evaluation | [-> catalog/11](../catalog/T01-algebraic-data-types.md) |

## Patterns

### 1 — Context functions for scoped DSL blocks

Use context function types (`A ?=> B`) to create blocks where a builder is implicitly available.

```scala
import scala.collection.mutable.ListBuffer

class HtmlBuffer:
  private val parts = ListBuffer[String]()
  def addTag(tag: String)(content: String): Unit =
    parts += s"<$tag>$content</$tag>"
  def result: String = parts.mkString("\n")

type Html[A] = HtmlBuffer ?=> A

def html(build: Html[Unit]): String =
  val buf = HtmlBuffer()
  build(using buf)
  buf.result

def div(content: Html[Unit]): Html[Unit] =
  summon[HtmlBuffer].addTag("div")("")
  content

def p(text: String): Html[Unit] =
  summon[HtmlBuffer].addTag("p")(text)

def h1(text: String): Html[Unit] =
  summon[HtmlBuffer].addTag("h1")(text)

val page = html:
  h1("Title")
  div:
    p("Hello")
    p("World")
// p("orphan") — does not compile outside an html block (no HtmlBuffer in scope)
```

### 2 — Phantom type builder enforcing required fields

Track which fields have been set using phantom types. The `build` method is only available when all required fields are present.

```scala
sealed trait Yes
sealed trait No

case class ServerConfig(host: String, port: Int, maxConn: Int)

class ServerBuilder[HasHost <: Yes | No, HasPort <: Yes | No](
  host: String = "", port: Int = 0, maxConn: Int = 100
):
  def withHost(h: String): ServerBuilder[Yes, HasPort] =
    ServerBuilder(h, port, maxConn)

  def withPort(p: Int): ServerBuilder[HasHost, Yes] =
    ServerBuilder(host, p, maxConn)

  def withMaxConn(m: Int): ServerBuilder[HasHost, HasPort] =
    ServerBuilder(host, port, m)

  def build(using HasHost =:= Yes, HasPort =:= Yes): ServerConfig =
    ServerConfig(host, port, maxConn)

object ServerBuilder:
  def apply(): ServerBuilder[No, No] = new ServerBuilder()

val cfg = ServerBuilder()
  .withHost("0.0.0.0")
  .withPort(8080)
  .withMaxConn(500)
  .build                    // compiles — both required fields set

// ServerBuilder()
//   .withPort(8080)
//   .build                 // compile error — host not set
```

### 3 — Extension methods for fluent chaining

Add domain methods to existing types without wrappers for natural-reading pipelines.

```scala
case class Query(table: String, filters: List[String] = Nil, lim: Option[Int] = None)

extension (q: Query)
  def where(predicate: String): Query =
    q.copy(filters = q.filters :+ predicate)

  def limit(n: Int): Query =
    q.copy(lim = Some(n))

  def sql: String =
    val base   = s"SELECT * FROM ${q.table}"
    val wheres = if q.filters.isEmpty then "" else q.filters.mkString(" WHERE ", " AND ", "")
    val lim    = q.lim.fold("")(n => s" LIMIT $n")
    base + wheres + lim

val query = Query("users")
  .where("age > 18")
  .where("active = true")
  .limit(100)
  .sql
// "SELECT * FROM users WHERE age > 18 AND active = true LIMIT 100"
```

### 4 — GADT-based expression DSL with type-safe evaluation

Build a typed expression tree where each node carries its result type. Evaluation is total and type-safe.

```scala
enum Expr[A]:
  case Lit(value: Int)                          extends Expr[Int]
  case Str(value: String)                       extends Expr[String]
  case Gt(lhs: Expr[Int], rhs: Expr[Int])       extends Expr[Boolean]
  case If[T](
    cond: Expr[Boolean], yes: Expr[T], no: Expr[T]
  )                                             extends Expr[T]
  case Concat(a: Expr[String], b: Expr[String]) extends Expr[String]

def eval[A](e: Expr[A]): A = e match
  case Expr.Lit(v)        => v
  case Expr.Str(v)        => v
  case Expr.Gt(l, r)      => eval(l) > eval(r)
  case Expr.If(c, y, n)   => if eval(c) then eval(y) else eval(n)
  case Expr.Concat(a, b)  => eval(a) + eval(b)

val program: Expr[String] =
  Expr.If(
    Expr.Gt(Expr.Lit(10), Expr.Lit(5)),
    Expr.Str("big"),
    Expr.Str("small")
  )

val result: String = eval(program)  // "big"

// Expr.If(Expr.Gt(Expr.Lit(1), Expr.Lit(2)), Expr.Lit(0), Expr.Str("x"))
//   — compile error: Expr[Int] vs Expr[String] in branches
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Scoped DSL blocks | Implicit parameters + by-name args; explicit `implicit` keyword clutters DSL surface | Context functions — the builder is invisible to the user; natural block syntax |
| Phantom builders | Same `=:=` evidence trick; worked but required `implicit` keyword everywhere | `using` clauses — cleaner call sites; union types simplify the phantom encoding |
| Fluent chaining | `implicit class` wrappers — extra allocation, cluttered companion | `extension` — zero-cost, no wrapper object, top-level or scoped |
| Typed expression trees | GADTs via `sealed trait` + `case class`; pattern match inference was weaker | `enum` GADTs — concise declaration; compiler refines types in match branches reliably |

## When to Use Which Feature

**Use context functions** when your DSL has a natural "scope" — HTML builders, configuration blocks, test fixtures. They eliminate explicit parameter passing and enforce that certain operations only happen inside the right block.

**Use phantom type builders** when construction has required fields or a required order. The type parameters track what has been configured, and the `build` method demands evidence of completeness.

**Use extension methods** for read-oriented or chaining-oriented DSLs where the goal is a fluent pipeline over existing types (queries, data transformations, assertions).

**Use GADTs** when your DSL is an expression language that will be interpreted or compiled. The type parameter on each node ensures that ill-typed expressions (like `if int then string else boolean`) cannot be constructed.

**Combine approaches** in larger DSLs: context functions for the outer scope, phantom builders for resource construction, extensions for chaining, and GADTs for the core expression model.
