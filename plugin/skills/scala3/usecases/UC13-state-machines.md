# UC-06 -- Protocol State Machines

## 1. The Constraint

**Enforce valid call ordering and protocol compliance at compile time.**
A builder must be called in a prescribed sequence; a network channel must follow a handshake protocol; a resource must be acquired before use and released after.
Violations should be type errors, not runtime exceptions.

## 2. Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| GADTs | Encode protocol steps as type-indexed constructors; the compiler tracks which step you are in. | [-> T01](T01-algebraic-data-types.md)(../catalog/T01-algebraic-data-types.md) |
| Phantom types via Opaque | Lightweight state tags with zero runtime cost; states exist only in the type system. | [-> T03](T03-newtypes-opaque.md)(../catalog/T03-newtypes-opaque.md) |
| Dependent function types | Return types that depend on the current protocol state, threading state through operations. | [-> T53](T53-path-dependent-types.md)(../catalog/T53-path-dependent-types.md) |
| Context functions | Scope a capability (e.g., an open connection) to a block, preventing escape. | [-> T42](T42-context-functions.md)(../catalog/T42-context-functions.md) |
| Erased definitions | Remove state-tag evidence at runtime so protocol enforcement is truly zero-overhead. | [-> T27](T27-erased-phantom.md)(../catalog/T27-erased-phantom.md) |

## 3. Patterns

### Pattern A: Phantom Type State Machine (Builder)

Use opaque types as state tags. The builder type carries its state, and each step returns a builder in the next state. Only a `Complete` builder can call `build`.

```scala
object BuilderState:
  opaque type Empty    = Unit
  opaque type HasName  = Unit
  opaque type HasAge   = Unit
  opaque type Complete = Unit

import BuilderState.*

class PersonBuilder[S]:
  private var name: String = ""
  private var age: Int = 0

  def setName(n: String): PersonBuilder[HasName] =
    name = n
    this.asInstanceOf[PersonBuilder[HasName]]

  def setAge(a: Int)(using S =:= HasName): PersonBuilder[Complete] =
    age = a
    this.asInstanceOf[PersonBuilder[Complete]]

  def build(using S =:= Complete): Person = Person(name, age)

case class Person(name: String, age: Int)

// Usage:
// PersonBuilder[Empty]().setName("Ada").setAge(36).build   // compiles
// PersonBuilder[Empty]().setAge(36)                         // error: Cannot prove S =:= HasName
// PersonBuilder[Empty]().setName("Ada").build                // error: Cannot prove S =:= Complete
```

### Pattern B: GADT Encoding of Protocol Steps

Encode the protocol as a GADT where each constructor represents a step. The type parameter tracks the current state, and sequencing is enforced by matching on the GADT.

```scala
enum State:
  case Disconnected, Connected, Authenticated

enum Protocol[S <: State, Next <: State]:
  case Connect(host: String)
    extends Protocol[State.Disconnected.type, State.Connected.type]
  case Auth(token: String)
    extends Protocol[State.Connected.type, State.Authenticated.type]
  case Query(sql: String)
    extends Protocol[State.Authenticated.type, State.Authenticated.type]
  case Disconnect()
    extends Protocol[State.Authenticated.type, State.Disconnected.type]

def run[S <: State, N <: State](step: Protocol[S, N]): Unit = step match
  case Protocol.Connect(h)    => println(s"connecting to $h")
  case Protocol.Auth(t)       => println("authenticating")
  case Protocol.Query(sql)    => println(s"running: $sql")
  case Protocol.Disconnect()  => println("disconnecting")

// The type parameters prevent: Auth before Connect, Query before Auth, etc.
```

### Pattern C: Dependent Types for Session-Typed Channels

Model send/receive operations whose types depend on the protocol position. A dependent function type lets `next` return a channel in a state determined by the current step.

```scala
trait Channel[S]:
  type Next
  def step: Next

trait Send[A]:
  type After

trait Recv[A]:
  type After

object Session:
  type Step1 = Send[String] { type After = Step2 }
  type Step2 = Recv[Int]    { type After = Done  }
  type Done  = Unit

  def send[A, S <: Send[A]](ch: Channel[S], msg: A): Channel[S#After] = ???
  def recv[A, S <: Recv[A]](ch: Channel[S]): (A, Channel[S#After])    = ???

// The type of the channel after each operation is computed from the protocol,
// preventing out-of-order send/recv at compile time.
```

### Pattern D: Context Functions for Scoped Resource Protocols

A context function confines a capability to a block. The resource is opened before the block and closed after, and the capability token cannot escape.

```scala
import scala.language.experimental.erasedDefinitions

erased class CanUseDb

class DbConnection:
  def query(sql: String)(using CanUseDb): List[String] = List(s"result of $sql")
  def execute(sql: String)(using CanUseDb): Int = 1

def withDb[A](connStr: String)(block: CanUseDb ?=> A): A =
  val conn = openConnection(connStr)
  try
    given CanUseDb = CanUseDb()
    block
  finally
    conn.close()

private def openConnection(s: String): java.io.Closeable = () => ()

// Usage:
withDb("jdbc:...") {
  val rows = DbConnection().query("SELECT 1")
  val n    = DbConnection().execute("INSERT ...")
}

// Outside withDb, no CanUseDb is in scope -- query/execute do not compile.
```

## 4. Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Phantom state tags | Sealed trait hierarchy with `Nothing`-inhabited types; needed a class per state, no guarantee of erasure. | Opaque types: zero-cost, no classes generated. Erased definitions also available. |
| GADT protocols | GADTs worked in Scala 2 `match`, but exhaustiveness checking was weaker and type inference inside GADT branches was fragile. | Full GADT support with sound exhaustiveness. Enum syntax makes protocol ADTs concise. |
| Dependent types | Path-dependent types via `val`/`type` members, requiring object-style encodings. No dependent *function* types. | Dependent function types (`(x: X) => x.T`) are first-class, simplifying session-type encodings. |
| Scoped capabilities | Implicit parameters for capability tokens, but no context-function syntax and no erasure. | Context functions (`T ?=> U`) scope the capability to a block. `erased` removes runtime overhead. |

## 5. When to Use Which Feature

| If you need... | Prefer |
|---|---|
| A linear builder with 3-6 states | **Phantom types via opaque** (Pattern A). Lightest encoding, zero runtime cost. |
| A complex protocol with branching or loops | **GADT** (Pattern B). Each constructor is a step; the compiler checks exhaustiveness. |
| Return types that depend on the current state | **Dependent function types** (Pattern C). Let the protocol compute the next channel type. |
| Ensuring a resource is used only within a scope | **Context functions + erased** (Pattern D). The capability cannot escape the block. |
| Absolute zero-overhead state tracking | Combine **opaque types** with **erased definitions** so tags and evidence exist only at compile time. |
