# Preventing Invalid States

## The Constraint

Make illegal states unrepresentable at compile time. If a value exists, it is valid — no runtime checks needed, no invalid combinations possible.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Enums / ADTs / GADTs | Closed hierarchies; compiler-enforced exhaustive matching | [-> catalog/11](../catalog/T01-algebraic-data-types.md) |
| Opaque types | Distinct types over the same representation; prevents mixing | [-> catalog/12](../catalog/T03-newtypes-opaque.md) |
| Union types | Express "one of these" without a common supertype | [-> catalog/01](../catalog/T02-union-intersection.md) |
| Match types | Compute types from types; refine at the type level | [-> catalog/03](../catalog/T41-match-types.md) |
| Erased definitions | Phantom values with zero runtime cost | [-> catalog/20](../catalog/T27-erased-phantom.md) |
| Inline | Compile-time evaluation and branching | [-> catalog/17](../catalog/T16-compile-time-ops.md) |

## Patterns

### 1 — ADT with exhaustive matching

Close off the state space with an `enum`. The compiler rejects incomplete matches.

```scala
enum PaymentStatus:
  case Pending
  case Charged(receiptId: String)
  case Refunded(reason: String)
  case Failed(error: String)

def nextAction(s: PaymentStatus): String = s match
  case PaymentStatus.Pending        => "charge the card"
  case PaymentStatus.Charged(id)    => s"send receipt $id"
  case PaymentStatus.Refunded(_)    => "close ticket"
  case PaymentStatus.Failed(err)    => s"alert ops: $err"
  // removing any branch is a compile error
```

### 2 — Phantom types to track state

Encode a protocol's state machine in the type system so transitions that skip steps do not compile.

```scala
sealed trait DoorState
sealed trait Open   extends DoorState
sealed trait Closed extends DoorState
sealed trait Locked extends DoorState

class Door[S <: DoorState] private ():
  def close(using S =:= Open):   Door[Closed] = Door()
  def lock(using S =:= Closed):  Door[Locked] = Door()
  def unlock(using S =:= Locked): Door[Closed] = Door()
  def open(using S =:= Closed):  Door[Open]   = Door()

object Door:
  def apply(): Door[Closed] = new Door()

val d = Door()
// d.lock          // compile error — door is Closed, not yet lockable?
                    // Actually: lock requires Closed, so this compiles.
// d.open.lock     // compile error — cannot lock an Open door
val ok = d.lock    // Closed -> Locked
```

### 3 — Opaque types to prevent value mix-ups

Two IDs share the same runtime representation but are incompatible at compile time.

```scala
object ids:
  opaque type UserId  = Long
  opaque type OrderId = Long

  object UserId:
    def apply(v: Long): UserId = v
  object OrderId:
    def apply(v: Long): OrderId = v

  extension (id: UserId)  def value: Long = id
  extension (id: OrderId) def value: Long = id

import ids.*

def lookupOrder(uid: UserId, oid: OrderId): String = ???

val u = UserId(1)
val o = OrderId(2)
lookupOrder(u, o)   // compiles
// lookupOrder(o, u) // compile error — OrderId ≠ UserId
```

### 4 — GADTs to refine types in pattern match branches

The compiler narrows the type parameter inside each branch, eliminating impossible cases.

```scala
enum Expr[A]:
  case IntLit(value: Int)          extends Expr[Int]
  case BoolLit(value: Boolean)     extends Expr[Boolean]
  case Add(a: Expr[Int], b: Expr[Int]) extends Expr[Int]
  case IfThenElse[T](
    cond: Expr[Boolean], thenE: Expr[T], elseE: Expr[T]
  ) extends Expr[T]

def eval[A](e: Expr[A]): A = e match
  case Expr.IntLit(v)              => v          // A =:= Int here
  case Expr.BoolLit(v)             => v          // A =:= Boolean here
  case Expr.Add(a, b)              => eval(a) + eval(b)
  case Expr.IfThenElse(c, t, f)    => if eval(c) then eval(t) else eval(f)
```

### 5 — Parse, don't validate

Instead of checking a condition and discarding the proof, return a refined type that carries the guarantee. A parser is a function from less-structured input to more-structured output — not just string parsing.

```scala
// Validation: checks and throws away the proof
def validateNonEmpty[A](xs: List[A]): Unit =
  if xs.isEmpty then throw IllegalArgumentException("empty list")

// Parsing: checks and preserves the proof in the return type
import scala.collection.immutable.NonEmptyList // e.g., cats.data.NonEmptyList

def parseNonEmpty[A](xs: List[A]): Either[String, NonEmptyList[A]] =
  NonEmptyList.fromList(xs).toRight("list cannot be empty")

// With opaque types — a smart constructor that parses
object domain:
  opaque type PortNumber = Int
  object PortNumber:
    def parse(n: Int): Either[String, PortNumber] =
      if n > 0 && n < 65536 then Right(n)
      else Left(s"invalid port: $n")

    extension (p: PortNumber) def value: Int = p

// Downstream code never needs to re-validate
import domain.*

def connect(port: PortNumber): Unit =
  println(s"Connecting to port ${port.value}")  // always valid
```

**Key insight:** functions returning `Unit` or throwing exceptions after checks are validation — they discard the information. Functions returning a refined type (`Either[E, A]`, `Option[A]`, an opaque type) are parsing — they preserve it. Prefer parsing.

See: [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Sealed hierarchies | `sealed trait` + `case class/object` — same idea, more boilerplate | `enum` — single construct, derives `ordinal`, `values` |
| Phantom types | Worked, but required `sealed trait` trees and dummy implicit evidence | Same encoding, but `erased` definitions ([-> catalog/20](../catalog/T27-erased-phantom.md)) eliminate runtime overhead entirely |
| Preventing value mix-ups | Value classes (`extends AnyVal`) — limited, boxing pitfalls, no multi-field | Opaque types — true zero-cost, composable, no boxing ever |
| GADTs | Supported but pattern matching often required casts; limited type inference | First-class GADT support in match; compiler refines types without casts |
| Exhaustiveness | Worked with `sealed`, but non-exhaustive match was a warning by default | `-Wnonunit-statement` and stricter defaults; `@nowarn` required to silence |

## When to Use Which Feature

**Start with an `enum` / ADT** when the set of states is small and fixed. This is the default tool — simple, exhaustive, well-understood.

**Reach for phantom types** when you need to enforce a *protocol* or *state machine* across method calls, not just pattern matching on a single value.

**Use opaque types** whenever two values share an underlying type but must not be interchanged (IDs, units of measure, domain primitives). They cost nothing at runtime.

**Use GADTs** when different branches of a data structure carry different type information and you want the compiler to propagate that information into match arms.

**Reserve match types and inline** for cases where the decision must happen entirely at compile time — e.g., selecting a return type based on an input type.
