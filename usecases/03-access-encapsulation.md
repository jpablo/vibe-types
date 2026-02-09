# Access and Encapsulation

## The Constraint

Control visibility and prevent unauthorized access to internals. Module boundaries are enforced by the compiler — clients cannot depend on representations they should not see, and extension points are explicitly declared.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Opaque types | Hide the underlying representation entirely | [-> catalog/12] |
| Export clauses | Selective delegation without inheritance | [-> catalog/13] |
| `open` modifier | Explicitly opt in to cross-module inheritance | [-> catalog/13] |
| Transparent traits | Control whether a trait's identity leaks into inferred types | [-> catalog/13] |
| Context functions | Scope capabilities to a block without exposing them globally | [-> catalog/06] |

## Patterns

### 1 — Opaque types hiding representation

Outside the defining scope, clients cannot access or pattern match on the underlying type. The abstraction is total and zero-cost.

```scala
object money:
  opaque type USD = BigDecimal

  object USD:
    def apply(amount: BigDecimal): USD = amount
    val Zero: USD = BigDecimal(0)

  extension (a: USD)
    def +(b: USD): USD = a + b       // BigDecimal + BigDecimal inside scope
    def *(n: Int): USD = a * n
    def show: String = f"$$${a}%.2f"

// Outside the `money` object:
import money.*

val total = USD(9.99) + USD(4.50)
total.show                     // "$14.49"
// total + BigDecimal(1)       // compile error — USD ≠ BigDecimal outside
// val raw: BigDecimal = total // compile error
```

### 2 — Export for selective delegation

Expose a curated subset of a wrapped object's API without inheritance and without manually forwarding every method.

```scala
class Connection private[db] (host: String):
  def query(sql: String): List[String] = ???
  def execute(sql: String): Int = ???
  def unsafeRawSocket: java.net.Socket = ???   // internal

class SafeConnection(private val conn: Connection):
  export conn.{query, execute}
  // `unsafeRawSocket` is NOT exported — invisible to clients

val safe = SafeConnection(Connection("localhost"))
safe.query("SELECT 1")      // compiles
// safe.unsafeRawSocket      // compile error — not exported
```

### 3 — `open` modifier controlling inheritance across modules

By default (under `-source:future` or the `open` feature warning), classes without `open` are not intended for extension outside their defining file. This makes extension points explicit.

```scala
// library code
open class Template:                     // explicitly extensible
  def header: String = "<head/>"
  def body: String                       // abstract — must override
  def footer: String = "<footer/>"

class InternalHelper:                    // NOT open — extending outside this file
  def run(): Unit = ()                   // triggers a warning or error

// client code (different file / module)
class MyPage extends Template:           // OK — Template is open
  def body: String = "<p>hello</p>"

// class MyHelper extends InternalHelper  // warning: InternalHelper is not open
```

### 4 — Package-private via scope qualifiers

Scala's access modifiers accept scope qualifiers to restrict visibility to a specific enclosing package or class.

```scala
package com.example.app

package db:
  class Schema:
    private[db] def migrate(): Unit = ()        // visible inside `db` package
    private[app] def snapshot(): Unit = ()       // visible inside `app` package
    private def internalOnly(): Unit = ()        // visible only inside Schema

package api:
  import db.Schema

  class Endpoint:
    val s = Schema()
    // s.migrate()       // compile error — private[db]
    s.snapshot()          // compiles — private[app] includes api
    // s.internalOnly()  // compile error — private
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Hiding representation | `private[this]` constructor + companion `apply` — still leaks via pattern matching or `.copy`; value classes have boxing issues | Opaque types — truly opaque outside defining scope, zero cost, no `.copy` leak |
| Selective delegation | Manual forwarder methods — tedious, error-prone | `export` clause — compiler-generated forwarders, selective or wildcard |
| Controlling extension | `sealed` (same file only) or `final` (no extension at all); no middle ground | `open` modifier — cross-file extension requires explicit opt-in; non-open classes warn |
| Transparent traits | Not available — inferred types always included trait identities | `transparent trait` — compiler omits the trait from inferred types, reducing API surface |
| Scope qualifiers | `private[scope]` — same syntax, same semantics | Unchanged in Scala 3 |

## When to Use Which Feature

**Opaque types** are the strongest encapsulation tool for data. Use them whenever the internal representation must be invisible to clients — domain primitives, handles, tokens. They replace value classes and manual wrapper patterns.

**Export clauses** replace inheritance-for-delegation. When you hold a reference to a service and want to expose part of its API, `export` is cleaner than `extends`. Use selective exports (`export x.{a, b}`) to keep the surface small.

**The `open` modifier** is a library design tool. Mark a class `open` when extension is part of the contract (template method, plugin hooks). Leave it off when extension would break invariants. Under `-source:future`, non-open classes produce warnings when extended from other files.

**Transparent traits** are useful for marker traits or implementation-detail mixins (e.g., `Product`, `Serializable`) that should not appear in inferred types. Mark them `transparent` to keep API signatures clean.

**Scope qualifiers** (`private[pkg]`) remain the right tool for package-internal APIs — functionality shared across classes within a module but hidden from external consumers. Combine with opaque types for layered encapsulation.
