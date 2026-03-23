# Migration from Scala 2

## The Constraint

Migrate Scala 2 implicit-heavy code to idiomatic Scala 3 constructs. Each implicit usage maps to a more specific, narrower Scala 3 feature — making intent explicit and reducing the cognitive load of the `implicit` keyword doing four different things.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Givens / Using | Replace `implicit val`, `implicit def`, and implicit parameter lists | [-> T05](T05-type-classes.md)(../catalog/T05-type-classes.md) |
| Extension methods | Replace `implicit class` for adding methods to existing types | [-> T19](T19-extension-methods.md)(../catalog/T19-extension-methods.md) |
| Conversion type class | Replace `implicit def` conversions with explicit, opt-in `Conversion[A, B]` | [-> T18](T18-conversions-coercions.md)(../catalog/T18-conversions-coercions.md) |
| Context bounds | Cleaner `[A: TC]` syntax, replaces `(implicit ev: TC[A])` | [-> T42](T42-context-functions.md)(../catalog/T42-context-functions.md) |
| Changed features | Cross-cutting migration concerns: syntax, semantics, deprecations | [-> T44](T44-changed-dropped.md)(../catalog/T44-changed-dropped.md) |

## Patterns

### 1 — implicit def / implicit val to given

Scala 2's `implicit val` and `implicit def` for type class instances become `given`.

```scala
// --- Scala 2 ---
trait Ordering[A] { def compare(a: A, b: A): Int }
implicit val intOrd: Ordering[Int] = (a, b) => a - b
implicit def listOrd[A](implicit ev: Ordering[A]): Ordering[List[A]] =
  (a, b) => a.zip(b).map { case (x, y) => ev.compare(x, y) }
    .find(_ != 0).getOrElse(a.length - b.length)

// --- Scala 3 ---
trait Ordering[A]:
  def compare(a: A, b: A): Int

given Ordering[Int] with
  def compare(a: Int, b: Int) = a - b

given [A](using Ordering[A]): Ordering[List[A]] with
  def compare(a: List[A], b: List[A]) =
    a.zip(b).map((x, y) => summon[Ordering[A]].compare(x, y))
      .find(_ != 0).getOrElse(a.length - b.length)
```

Key changes:
- `implicit val` becomes `given ... with` (anonymous or named)
- `implicit def` for derivation becomes `given [A](using ...): TC[A] with`
- Name is optional — the compiler resolves by type, not by name

### 2 — implicit class to extension methods

Enrichment wrappers become zero-cost extension methods.

```scala
// --- Scala 2 ---
implicit class RichString(val s: String) extends AnyVal {
  def words: List[String] = s.split("\\s+").toList
  def initials: String    = words.map(_.head.toUpper).mkString
}

"hello world".words      // List("hello", "world")
"hello world".initials   // "HW"

// --- Scala 3 ---
extension (s: String)
  def words: List[String] = s.split("\\s+").toList
  def initials: String    = words.map(_.head.toUpper).mkString

"hello world".words      // List("hello", "world")
"hello world".initials   // "HW"
```

Key changes:
- No wrapper class, no `extends AnyVal` hack
- Multiple methods grouped in a single `extension` block
- Can be defined at top level, in objects, or scoped to a file

### 3 — implicit conversions to Conversion type class

Implicit conversions become explicit and opt-in.

```scala
// --- Scala 2 ---
implicit def intToDouble(n: Int): Double = n.toDouble
val d: Double = 42   // silent conversion

// Also common: implicit def for "smart" wrappers
case class Meters(value: Double)
implicit def doubleToMeters(d: Double): Meters = Meters(d)
val m: Meters = 3.14   // silent conversion

// --- Scala 3 ---
given Conversion[Int, Double] = _.toDouble
// val d: Double = 42   // only works if Conversion is in scope
//                       // requires: import scala.language.implicitConversions

case class Meters(value: Double)
given Conversion[Double, Meters] = Meters(_)
// val m: Meters = 3.14 // requires explicit import of implicitConversions
```

Key changes:
- `implicit def` conversions become `given Conversion[A, B]`
- User must `import scala.language.implicitConversions` at use site
- Compiler warns on unintended conversions — makes "magic" visible

### 4 — Implicit parameter lists to using clauses

The `implicit` keyword on parameter lists becomes `using`.

```scala
// --- Scala 2 ---
def sorted[A](list: List[A])(implicit ord: Ordering[A]): List[A] =
  list.sorted(ord)

// Context bound version (same in both):
def sorted2[A: Ordering](list: List[A]): List[A] = list.sorted

// Passing explicitly:
sorted(List(3, 1, 2))(Ordering.Int)

// --- Scala 3 ---
def sorted[A](list: List[A])(using ord: Ordering[A]): List[A] =
  list.sorted(using ord)

// Context bound (same syntax, improved semantics):
def sorted2[A: Ordering](list: List[A]): List[A] = list.sorted

// Passing explicitly — note the `using` keyword:
sorted(List(3, 1, 2))(using Ordering.Int)
```

Key changes:
- `implicit` parameter keyword becomes `using`
- Explicit passing requires `using` — prevents accidental position-based passing
- Context bounds `[A: TC]` work the same but integrate better with `summon`

## Scala 2 Comparison

| Scala 2 construct | Scala 3 replacement | Mechanical? |
|---|---|---|
| `implicit val x: T = ...` | `given T with ...` or `given x: T = ...` | Yes |
| `implicit def f[A](implicit e: E): T` | `given [A](using E): T with ...` | Yes |
| `implicit class C(x: T) { def m = ... }` | `extension (x: T) def m = ...` | Yes |
| `implicit def a2b(a: A): B` | `given Conversion[A, B] = ...` | Yes, but opt-in semantics change |
| `def f(implicit x: T)` | `def f(using x: T)` | Yes |
| `implicitly[T]` | `summon[T]` | Yes |
| `implicit object X extends TC[Y]` | `given X: TC[Y] with ...` | Yes |

## When to Use Which Feature

### Gradual migration vs. rewrite

**Gradual migration** is usually the right choice. Scala 3 accepts most Scala 2 syntax under `-source:3.0-migration`, rewriting constructs one at a time:

1. **Phase 1**: compile with Scala 3, `-source:3.0-migration`. Fix hard errors only.
2. **Phase 2**: convert `implicit val/def` for type class instances to `given`. This is the highest-value change — it separates "this is an instance" from "this is a conversion" from "this is a parameter".
3. **Phase 3**: convert `implicit class` to `extension`. Straightforward and improves readability.
4. **Phase 4**: convert `implicit def` conversions to `given Conversion`. This changes semantics (opt-in), so test carefully.
5. **Phase 5**: convert `implicit` parameter lists to `using`. Low risk but touches many call sites if you pass explicitly.

**Full rewrite** makes sense only when the implicit architecture is deeply tangled (orphan instances, import-based implicit scoping tricks, `implicitly`-based type-level programming). In that case, redesigning around `given` / `using` / `extension` often simplifies the code significantly.

### Decision table

| Situation | Recommendation |
|---|---|
| Library with public API | Gradual: keep source compat, migrate internals first |
| Application code | Phase 2-3 first, biggest readability gain |
| Heavy implicit conversions | Phase 4 carefully — semantics change; add tests |
| Type-level implicit programming (Shapeless style) | Consider rewrite using match types / `Mirror` |
| Cross-building Scala 2 / 3 | Use `-Xsource:3` on Scala 2 side; use `given`/`using` syntax where compatible |
