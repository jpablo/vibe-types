# Typestate

> **Since:** Scala 3.0 (phantom types since Scala 2; erased definitions since Scala 3.3)

## What it is

Typestate programming uses **phantom type parameters** to encode an object's state at the type level, so that methods are only available when the object is in the correct state. A `Door[Open]` has an `enter` method; a `Door[Closed]` has an `open` method. Calling `enter` on a `Door[Closed]` is a compile-time error, not a runtime exception.

In Scala 3, typestate is implemented using **phantom type parameters** — type parameters that appear in the type signature but carry no runtime data. State transitions return a new object (or the same object cast to the new state type). The `=:=` type equality evidence can constrain methods to specific states. With Scala 3.3's **`erased`** definitions, the phantom evidence parameters are guaranteed to have zero runtime cost.

Typestate is particularly useful for builder patterns, protocol enforcement (e.g., "must authenticate before querying"), and resource lifecycle management (e.g., "must open before reading, must close after use").

## What constraint it enforces

**Methods are only callable when the phantom type parameter matches the required state. The compiler rejects calls in the wrong state, turning protocol violations into type errors. State transitions produce new types, making the valid sequence of operations visible in the type signature.**

## Minimal snippet

```scala
sealed trait DoorState
sealed trait Open  extends DoorState
sealed trait Closed extends DoorState

class Door[S <: DoorState] private ():
  def open(using S =:= Closed): Door[Open] = Door()
  def close(using S =:= Open): Door[Closed] = Door()
  def enter(using S =:= Open): Unit = println("Entering!")

object Door:
  def closed: Door[Closed] = Door()

val d = Door.closed
// d.enter           // error: Cannot prove that Closed =:= Open
val opened = d.open
opened.enter         // OK
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type classes / givens** [-> T05](T05-type-classes.md) | `=:=` evidence is provided as a given. `using S =:= Open` is a context parameter the compiler supplies when the types match. |
| **Opaque types** [-> T03](T03-newtypes-opaque.md) | State tags can be opaque types, preventing external code from forging state evidence. |
| **Erased definitions** | `erased given` and `erased` parameters (Scala 3.3+) ensure phantom evidence has zero runtime cost — no object allocation for the `=:=` witness. |
| **Phantom types** | Typestate is a specific application of phantom types where the phantom parameter encodes a finite state machine. |
| **Union / intersection types** [-> T02](T02-union-intersection.md) | Union states like `Open | HalfOpen` can represent "either state is acceptable" for methods that work in multiple states. |
| **Tagless final** [-> T56](T56-tagless-final.md) | Typestate can be combined with tagless final: algebras whose methods have phantom-state-constrained signatures, interpreted into different effects. |

## Gotchas and limitations

1. **Verbose state transitions.** Each state transition returns a new object (or the same object retyped), requiring the caller to rebind the variable: `val opened = door.open`. This is less ergonomic than mutable state but is the price of compile-time safety.

2. **Linear use required.** After a state transition, the old reference still exists with the old type. Nothing prevents using the stale reference. In Rust, the ownership system prevents this; in Scala, it requires discipline or linting.

3. **`=:=` evidence is not erased by default.** Before Scala 3.3's `erased`, the `=:=` witness is a real object allocated at each call. Use `erased` to eliminate this cost, but note that `erased` is still experimental in some Scala 3.x versions.

4. **Combinatorial explosion.** If an object has many independent state dimensions (e.g., authenticated + connected + encrypted), the number of phantom type combinations grows multiplicatively. Consider separate phantom parameters or a type-level state product.

5. **Builder pattern duplication.** Typestate builders (e.g., `Builder[HasName, NoAge]`) require a phantom parameter per field, leading to many type parameters. Libraries like `scala-newtype` or macro-based builders can reduce boilerplate.

## Beginner mental model

Think of typestate as a **boarding pass system**. Your `Door[Closed]` is like a boarding pass for the waiting area — it lets you wait but not board the plane. Calling `open` upgrades your pass to `Door[Open]`, which lets you board. The gate agent (compiler) checks your pass type before letting you through. You cannot forge a boarding pass — the only way to get `Door[Open]` is through the `open` method on `Door[Closed]`. This ensures everyone follows the correct sequence.

## Example A -- Builder pattern with typestate

```scala
sealed trait HasName
sealed trait NoName
sealed trait HasAge
sealed trait NoAge

class PersonBuilder[N, A] private (name: String, age: Int):
  def withName(n: String)(using N =:= NoName): PersonBuilder[HasName, A] =
    PersonBuilder(n, age)
  def withAge(a: Int)(using A =:= NoAge): PersonBuilder[N, HasAge] =
    PersonBuilder(name, a)
  def build(using N =:= HasName, A =:= HasAge): (String, Int) =
    (name, age)

object PersonBuilder:
  def apply(): PersonBuilder[NoName, NoAge] = PersonBuilder("", 0)

val person = PersonBuilder()
  .withName("Alice")
  .withAge(30)
  .build                // OK: ("Alice", 30)

// PersonBuilder().withAge(30).build  // error: Cannot prove NoName =:= HasName
```

## Example B -- Connection protocol enforcement

```scala
sealed trait Disconnected
sealed trait Connected
sealed trait Authenticated

class Connection[S] private (host: String):
  def connect(using S =:= Disconnected): Connection[Connected] =
    println(s"Connecting to $host")
    Connection(host)
  def authenticate(token: String)(using S =:= Connected): Connection[Authenticated] =
    println(s"Authenticating with $token")
    Connection(host)
  def query(sql: String)(using S =:= Authenticated): String =
    s"Result from $host: [$sql]"
  def disconnect(using S =:= Connected | S =:= Authenticated): Connection[Disconnected] =
    println("Disconnecting")
    Connection(host)

object Connection:
  def create(host: String): Connection[Disconnected] = Connection(host)

val result = Connection.create("db.example.com")
  .connect
  .authenticate("secret")
  .query("SELECT 1")
// Cannot query without connecting and authenticating first
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Typestate makes invalid state transitions unrepresentable at the type level.
- [-> UC-09](../usecases/UC09-builder-config.md) -- Typestate builders enforce that all required fields are set before construction.
- [-> UC-11](../usecases/UC11-effect-tracking.md) -- Phantom state parameters track resource lifecycle (open/closed, authenticated/unauthenticated) at the type level.
- [-> UC-13](../usecases/UC13-state-machines.md) -- Typestate is the canonical encoding of state machines in the type system.

## Source anchors

- Scala 3 reference: "Type Equality — `=:=`"
- Scala 3 reference: "Erased Definitions"
- Scala 3 reference: "Phantom Types" (SIP-35)
- [Scala 3 documentation — Opaque Type Aliases](https://docs.scala-lang.org/scala3/reference/other-new-features/opaques.html)
