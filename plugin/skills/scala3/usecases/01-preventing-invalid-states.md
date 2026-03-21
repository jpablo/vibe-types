# Preventing Invalid States

## The Constraint

Make illegal states unrepresentable at compile time. If a value exists, it is valid — no runtime checks needed, no invalid combinations possible.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Enums / ADTs / GADTs | Closed hierarchies; compiler-enforced exhaustive matching | [-> catalog/11](../catalog/11-enums-adts-gadts.md) |
| Opaque types | Distinct types over the same representation; prevents mixing | [-> catalog/12](../catalog/12-opaque-types.md) |
| Union types | Express "one of these" without a common supertype | [-> catalog/01](../catalog/01-union-intersection.md) |
| Match types | Compute types from types; refine at the type level | [-> catalog/03](../catalog/03-match-types.md) |
| Erased definitions | Phantom values with zero runtime cost | [-> catalog/20](../catalog/20-erased-definitions.md) |
| Inline | Compile-time evaluation and branching | [-> catalog/17](../catalog/17-inline-compiletime.md) |

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

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Sealed hierarchies | `sealed trait` + `case class/object` — same idea, more boilerplate | `enum` — single construct, derives `ordinal`, `values` |
| Phantom types | Worked, but required `sealed trait` trees and dummy implicit evidence | Same encoding, but `erased` definitions ([-> catalog/20](../catalog/20-erased-definitions.md)) eliminate runtime overhead entirely |
| Preventing value mix-ups | Value classes (`extends AnyVal`) — limited, boxing pitfalls, no multi-field | Opaque types — true zero-cost, composable, no boxing ever |
| GADTs | Supported but pattern matching often required casts; limited type inference | First-class GADT support in match; compiler refines types without casts |
| Exhaustiveness | Worked with `sealed`, but non-exhaustive match was a warning by default | `-Wnonunit-statement` and stricter defaults; `@nowarn` required to silence |

## When to Use Which Feature

**Start with an `enum` / ADT** when the set of states is small and fixed. This is the default tool — simple, exhaustive, well-understood.

**Reach for phantom types** when you need to enforce a *protocol* or *state machine* across method calls, not just pattern matching on a single value.

**Use opaque types** whenever two values share an underlying type but must not be interchanged (IDs, units of measure, domain primitives). They cost nothing at runtime.

**Use GADTs** when different branches of a data structure carry different type information and you want the compiler to propagate that information into match arms.

**Reserve match types and inline** for cases where the decision must happen entirely at compile time — e.g., selecting a return type based on an input type.
