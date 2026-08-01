# `open` Modifier, Export Clauses, Transparent Traits

> **Since:** Scala 3.0 | **Status:** the ad-hoc-extension warning is still opt-in as of Scala 3.8.4 (`-source:future`)

## What It Is

Scala 3 provides three complementary features for controlling how classes and traits compose and surface in the type system. The **`open` modifier** explicitly declares that a class is designed for extension by subclasses outside its source file. **Export clauses** create forwarding aliases that expose selected members of a composed object, enabling delegation without inheritance. **Transparent traits** are marked with the `transparent` modifier so that the compiler suppresses them from inferred types, keeping implementation-detail mixins invisible to callers.

## What Constraint It Lets You Express

**`open` controls _who may extend_ a class; `export` controls _which members are surfaced_ through delegation; `transparent` controls _which supertypes appear_ in inferred types.** Together they let library authors express an extensibility contract (open/final/default), replace inheritance-based reuse with composition that is just as concise, and prevent implementation mixins from leaking into public APIs.

## Minimal Snippets

### `open` modifier

```scala
// Library code
open class Writer[T]:
  def send(x: T): Unit = println(x)
  def sendAll(xs: T*): Unit = xs.foreach(send)

// Client code -- OK because Writer is open
class EncryptedWriter[T] extends Writer[T]:
  private def encrypt(x: T): T = x  // stand-in for real encryption
  override def send(x: T): Unit = super.send(encrypt(x))
```

Without `open`, extending `Writer` from another file is still permitted, and as of Scala 3.8.4 it is completely silent by default. The ad-hoc-extension feature warning only appears under `-source:future`; when it does appear, either `import scala.language.adhocExtensions` in the client file or the compiler option `-language:adhocExtensions` silences it. The Scala reference describes the warning as something that *will* become the default, not something that already is -- so today `open` documents an extensibility contract rather than enforcing one.

### Export clauses

```scala
type BitMap = Array[Byte]

class Printer:
  def print(bits: BitMap): Unit = ???
  def status: List[String] = ???

class Scanner:
  def scan(): BitMap = ???
  def status: List[String] = ???

class Copier:
  private val printUnit = new Printer
  private val scanUnit  = new Scanner

  export scanUnit.scan          // alias: def scan(): BitMap = scanUnit.scan()
  export printUnit.{status as _, *}  // all of printUnit except status

  def status: List[String] = printUnit.status ++ scanUnit.status
```

Exported aliases are `final`, can implement abstract members, and copy type/value parameters faithfully.

### Transparent traits

```scala
transparent trait Impl           // implementation-only mixin

trait Kind
object Var extends Kind, Impl
object Val extends Kind, Impl

val cond = true
val x = Set(if cond then Val else Var)
// inferred type: Set[Kind]   (Impl is dropped)
```

Without `transparent`, the inferred type would be `Set[Kind & Impl]`.

## Interaction with Other Features

| Feature | Interaction |
|---|---|
| **`sealed` / `final`** | `open` is incompatible with both. `final` forbids all extension and `sealed` confines it to the same file, and both are enforced. A non-open, non-sealed class is *not* comparably closed: ad-hoc extension from another file is allowed, and under default flags in 3.8.4 it is not even warned about. Treat the absence of `open` as documentation of intent; reach for `final` or `sealed` when you need the compiler to enforce it. |
| **`abstract` / traits** | Traits and abstract classes are always open; adding `open` is redundant. |
| **Opaque types** | Export clauses can forward opaque type companions, enabling facade patterns at the top level. |
| **Extension methods** | Export clauses may appear inside `extension` blocks, creating extension method aliases from a helper class. |
| **Union types** | When all supertypes widened from a union are transparent, the union is kept un-widened (e.g., `Val \| Var` instead of `Any`). |
| **Given instances** | Exports use a `given` selector to alias given instances specifically, mirroring import syntax. |
| **Type inference** | `transparent` on root classes (`Any`, `AnyVal`, `Matchable`, `Product`, `Serializable`) is built in, so `if c then 1 else "hi"` infers `Int \| String` rather than `Any`. |

## Gotchas and Limitations

- **Export aliases are final.** They cannot be overridden, and they cannot override concrete members in base classes (they lack an `override` modifier). They _can_ implement abstract members.
- **Wildcard exports from packages are forbidden.** The qualifier path of a wildcard or given selector must not be a package (incremental compilation cannot track it).
- **Export elaboration order.** All export qualifier paths are typed before any aliases are entered as members. This means one export clause cannot refer to an alias introduced by another export clause in the same class.
- **Transparent trait single-instance rule.** A single transparent trait appearing alone is _not_ widened to `Any`. Transparent traits are dropped only when they appear in conjunction with some other non-transparent type in an intersection.
- **Ad-hoc extension warnings are not on by default.** As of Scala 3.8.4, extending a non-open class from a different file compiles silently; the feature warning is only produced under `-source:future`. The Scala reference says it is planned to become the default, so `open` is a documented contract today rather than an enforced one -- if you want the warning, turn it on explicitly.
- **Export in blocks.** Export clauses can appear in classes and at the top level, but not as statements inside a block.

## Use-Case Cross-References

- `[-> UC-01](../usecases/UC01-invalid-states.md)` Defining an extensible plugin API with `open` classes and documented extension contracts.
- `[-> UC-04](../usecases/UC11-effect-tracking.md)` Using export clauses for composition-over-inheritance in aggregate services.
- `[-> UC-09](../usecases/UC16-nullability.md)` Keeping `Product` / `Serializable` out of public ADT types with transparent traits.
- `[-> UC-12](../usecases/UC19-serialization.md)` Facade modules that re-export selected definitions at the package top level.
