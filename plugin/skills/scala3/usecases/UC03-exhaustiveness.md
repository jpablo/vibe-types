# Exhaustiveness

## The Constraint

Ensure every pattern match handles all possible cases. The compiler rejects incomplete matches, and `sealed` / `enum` hierarchies define exactly what "all cases" means. When a case is intentionally unused, `@nowarn` silences the warning with an auditable annotation.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Enums / sealed traits | Closed hierarchies define the full case set; compiler enforces exhaustive matching | [-> T01](T01-algebraic-data-types.md)(../catalog/T01-algebraic-data-types.md) |
| Match types | Type-level pattern matching with exhaustiveness on type cases | [-> T41](T41-match-types.md)(../catalog/T41-match-types.md) |
| Matchable constraint | Limits universal matching to types that opt in; prevents matching on opaque or erased types | [-> T20](T20-equality-safety.md)(../catalog/T20-equality-safety.md) |
| @nowarn annotation | Suppresses specific warnings when non-exhaustive matching is intentional | [-> T16](T16-compile-time-ops.md)(../catalog/T16-compile-time-ops.md) |

## Patterns

### 1 — Sealed trait with exhaustive match

A `sealed` trait restricts its subtypes to the defining file. The compiler knows every possible case.

```scala
sealed trait Result
case class Success(value: String) extends Result
case class Failure(error: String) extends Result
case object Pending               extends Result

def describe(r: Result): String = r match
  case Success(v)  => s"ok: $v"
  case Failure(e)  => s"error: $e"
  case Pending     => "waiting"
  // removing any branch → compile warning: "match may not be exhaustive"
```

### 2 — Enum exhaustiveness

Enums are sealed by definition. Adding a new case breaks all existing non-exhaustive matches at compile time.

```scala
enum Color:
  case Red, Green, Blue

def hex(c: Color): String = c match
  case Color.Red   => "#FF0000"
  case Color.Green => "#00FF00"
  case Color.Blue  => "#0000FF"

// If someone adds `case Yellow`, every match site must be updated.
```

### 3 — @nowarn for intentionally partial matches

When a match is deliberately incomplete, `@nowarn` documents the intent and silences the compiler.

```scala
enum Event:
  case Click(x: Int, y: Int)
  case KeyPress(key: Char)
  case Scroll(delta: Int)
  case Resize(w: Int, h: Int)

// We only care about input events in this handler
@scala.annotation.nowarn("msg=match may not be exhaustive")
def handleInput(e: Event): String = e match
  case Event.Click(x, y)  => s"clicked at ($x, $y)"
  case Event.KeyPress(k)  => s"pressed $k"
  case Event.Scroll(d)    => s"scrolled $d"
  // Resize intentionally not handled — documented by @nowarn
```

### 4 — Matchable constraint

The `Matchable` trait controls which types can be matched on. In strict settings, matching on a non-`Matchable` type is an error, preventing matches that could violate parametricity.

```scala
// Any and AnyRef extend Matchable, but custom abstractions can avoid it.
def process[A <: Matchable](a: A): String = a match
  case i: Int    => s"int: $i"
  case s: String => s"str: $s"
  case other     => other.toString

// With a non-Matchable bound, matching is restricted:
// def unsafe[A](a: A): String = a match  // warning under -source:future
//   case _: Int => "int"                  // A is not <: Matchable
```

### 5 — Exhaustiveness with GADTs

GADT pattern matches refine the type parameter. The compiler tracks which cases are possible for each type and rejects truly impossible branches.

```scala
enum Expr[A]:
  case IntLit(v: Int)       extends Expr[Int]
  case BoolLit(v: Boolean)  extends Expr[Boolean]
  case Not(e: Expr[Boolean]) extends Expr[Boolean]

def eval[A](e: Expr[A]): A = e match
  case Expr.IntLit(v)  => v        // A =:= Int
  case Expr.BoolLit(v) => v        // A =:= Boolean
  case Expr.Not(e)     => !eval(e) // A =:= Boolean
  // exhaustive: all cases for all possible A are covered
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Sealed hierarchies | `sealed trait` + case classes — same idea, exhaustiveness was a warning by default | `enum` — concise syntax; `-Wnonunit-statement` and stricter defaults |
| Suppression | `@unchecked` on the match scrutinee — coarse, hides all warnings | `@nowarn` with message filters — fine-grained, auditable |
| Matchable | Not available; any value could be matched on | `Matchable` constraint restricts matching; enforced under `-source:future` |
| GADT exhaustiveness | Supported but fragile; compiler often could not prove coverage | Improved GADT support; compiler refines types and checks exhaustiveness reliably |

## When to Use Which Feature

**Use `enum`** for any closed set of alternatives. It is the default tool — concise, exhaustive, well-supported by tooling and derivation.

**Use `sealed trait`** when you need class-based features that `enum` does not support (e.g., mixing in traits per case, complex inheritance).

**Use `@nowarn`** sparingly and only when partial matching is intentional. Always include a comment explaining which cases are omitted and why.

**Use `Matchable`** in library APIs where you want to prevent clients from pattern-matching on abstract types, preserving parametricity and future flexibility.
