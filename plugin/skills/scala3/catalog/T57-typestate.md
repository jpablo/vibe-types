# Typestate

> **Since:** Scala 3.0 (phantom types since Scala 2; `erased` definitions are Experimental since Scala 3.0, requiring `import scala.language.experimental.erasedDefinitions`)

## What it is

Typestate programming uses **phantom type parameters** to encode an object's state at the type level, so that methods are only available when the object is in the correct state. A `Door[Open]` has an `enter` method; a `Door[Closed]` has an `open` method. Calling `enter` on a `Door[Closed]` is a compile-time error, not a runtime exception.

In Scala 3, typestate is implemented using **phantom type parameters** — type parameters that appear in the type signature but carry no runtime data. State transitions return a new object (or the same object cast to the new state type). The `=:=` type equality evidence can constrain methods to specific states; that evidence is already effectively free, because `=:=.refl` hands back one cached singleton shared by every `=:=` (and every `<:<`) in the program. The experimental **`erased`** definitions feature (`import scala.language.experimental.erasedDefinitions`) removes the evidence *parameter* itself before code generation, but it works only with hand-rolled evidence traits — it cannot be applied to `=:=` (see gotcha 3).

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
| **Erased definitions** [-> T27](T27-erased-phantom.md) | `erased given` and `erased` parameters (experimental, since Scala 3.0, via `erasedDefinitions`) remove the evidence parameter before code generation, so the method takes no argument at all at runtime. This requires *hand-rolled* evidence traits: the synthesized `=:=` witness is a method application, not a pure expression, and is rejected (gotcha 3). |
| **Phantom types** | Typestate is a specific application of phantom types where the phantom parameter encodes a finite state machine. |
| **Union / intersection types** [-> T02](T02-union-intersection.md) | Union states like `Open | HalfOpen` can represent "either state is acceptable" for methods that work in multiple states. |
| **Tagless final** [-> T56](T56-tagless-final.md) | Typestate can be combined with tagless final: algebras whose methods have phantom-state-constrained signatures, interpreted into different effects. |

## Gotchas and limitations

1. **Verbose state transitions.** Each state transition returns a new object (or the same object retyped), requiring the caller to rebind the variable: `val opened = door.open`. This is less ergonomic than mutable state but is the price of compile-time safety.

2. **Linear use required.** After a state transition, the old reference still exists with the old type. Nothing prevents using the stale reference. In Rust, the ownership system prevents this; in Scala, it requires discipline or linting.

3. **`=:=` evidence is a shared singleton, and `erased` cannot strip it.** The `=:=` witness is *not* allocated per call: `=:=.tpEquals` returns one cached instance that is `asInstanceOf`-cast at every use site, and `<:<.refl` is that same object, so `summon[Int =:= Int] eq summon[String =:= String] eq summon[Int <:< Any]` is `true` throughout a program. There is no per-call allocation to optimise away. The experimental `erased` feature does not apply here either: an argument to an `erased` parameter must be a *pure expression*, and the synthesized witness `=:=.refl[A]` is a method application, so `def enter(using erased ev: S =:= Open)` is rejected at every call site with `[E217] implicit argument to an erased parameter fails to be a pure expression`. Erasing the parameter needs a hand-rolled evidence trait whose `erased given` is *non-parameterised* and bound to a pure path — a parameterised `erased given` is rejected outright with `[E218] 'erased' is not allowed for this kind of definition`:

   ```scala
   import scala.language.experimental.erasedDefinitions

   sealed trait DoorState
   sealed trait Open   extends DoorState
   sealed trait Closed extends DoorState

   trait IsOpen[S]
   object OpenEv extends IsOpen[Open]
   erased given eo: IsOpen[Open] = OpenEv       // non-parameterised, pure right-hand side

   trait IsClosed[S]
   object ClosedEv extends IsClosed[Closed]
   erased given ec: IsClosed[Closed] = ClosedEv

   class ErasedDoor[S <: DoorState] private ():
     def open(using erased e: IsClosed[S]): ErasedDoor[Open] = ErasedDoor()
     def enter(using erased e: IsOpen[S]): Unit = println("Entering!")

   object ErasedDoor:
     def closed: ErasedDoor[Closed] = ErasedDoor()

   ErasedDoor.closed.open.enter    // OK — both parameters erased before code generation
   // ErasedDoor.closed.enter      // error: No given instance of type IsOpen[Closed]
   ```

4. **Combinatorial explosion.** If an object has many independent state dimensions (e.g., authenticated + connected + encrypted), the number of phantom type combinations grows multiplicatively. Consider separate phantom parameters or a type-level state product.

5. **Builder pattern duplication.** Typestate builders (e.g., `Builder[HasName, NoAge]`) require a phantom parameter per field, leading to many type parameters. Macro-generated builders [-> T17](T17-macros-metaprogramming.md) can reduce the boilerplate.

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
    new PersonBuilder(n, age)
  def withAge(a: Int)(using A =:= NoAge): PersonBuilder[N, HasAge] =
    new PersonBuilder(name, a)
  def build(using N =:= HasName, A =:= HasAge): (String, Int) =
    (name, age)

object PersonBuilder:
  def apply(): PersonBuilder[NoName, NoAge] = new PersonBuilder("", 0)

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
- [Scala 3 Reference — Erased Definitions](https://docs.scala-lang.org/scala3/reference/experimental/erased-defs.html) — the Scala 3 reference has no "Phantom Types" page: Dotty's separate phantom-types experiment was dropped before 3.0 and explicitly superseded by erased terms.
- [Scala 3 documentation — Opaque Type Aliases](https://docs.scala-lang.org/scala3/reference/other-new-features/opaques.html) (SIP-35)
