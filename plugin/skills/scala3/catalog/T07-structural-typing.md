# Structural Types, Refined Types, and Named Tuples

> **Since:** Scala 3.0 | **Latest changes:** Scala 3.7 (named tuples)

## What It Is

Scala 3 supports **structural types** -- types defined by their member signatures rather than by a named class hierarchy. A structural type is a refinement on a parent type (often `Selectable`) that declares fields or methods the value must provide. Member access on structural types is dispatched through `selectDynamic` / `applyDynamic`, giving library authors full control over resolution. **Named tuples** (Scala 3.7+) extend tuples with field names, creating lightweight record-like types where elements are accessed by name (e.g., `person.age`). Named tuples integrate with `Selectable` through the `Fields` type member, enabling computed field access patterns such as typed query DSLs.

## What Constraint It Lets You Express

**Structural types provide statically checked duck typing -- you can require that a value has certain members without mandating a common supertype. Named tuples provide record-like types with positional and named access, zero-overhead representation, and seamless interop with case classes via `NamedTuple.From`.**

## Minimal Snippets

### Structural types with Selectable

```scala
class Record(elems: (String, Any)*) extends Selectable:
  private val fields = elems.toMap
  def selectDynamic(name: String): Any = fields(name)

type Person = Record { val name: String; val age: Int }

val p: Person = Record("name" -> "Emma", "age" -> 42).asInstanceOf[Person]
println(p.name)  // "Emma" -- compiled to p.selectDynamic("name").asInstanceOf[String]
```

### Structural types with Java reflection

```scala
import scala.reflect.Selectable.reflectiveSelectable

type Closeable = { def close(): Unit }

def autoClose(f: Closeable)(op: Closeable => Unit): Unit =
  try op(f) finally f.close()
// f.close() dispatches via Java reflection
```

### Local Selectable refinements

```scala
trait Vehicle extends reflect.Selectable:
  val wheels: Int

val i3 = new Vehicle:
  val wheels = 4
  val range = 240     // inferred type: Vehicle { val range: Int }

i3.range  // OK -- structural access via Selectable
```

### Named tuples

```scala
type Person = (name: String, age: Int)
val Bob: Person = (name = "Bob", age = 33)

Bob.name      // "Bob"
Bob.age       // 33

// Pattern matching (named or positional)
Bob match
  case (age = a, name = n) => s"$n is $a"

// Unnamed tuples conform to named tuple types
val Laura: Person = ("Laura", 25)  // OK
```

### Named tuples with Selectable (computed fields)

```scala
trait Q[T] extends Selectable:
  type Fields = NamedTuple.Map[NamedTuple.From[T], Q]
  def selectDynamic(name: String): Any = ???

case class City(zipCode: Int, name: String, population: Int)
val city: Q[City] = ???
city.zipCode   // type: Q[Int]
city.name      // type: Q[String]
```

## Interaction with Other Features

| Feature | Interaction |
|---|---|
| **`Selectable` trait** | The bridge between structural types and their runtime dispatch. Custom `Selectable` subclasses can use maps, reflection, code generation, or any other strategy. |
| **`scala.Dynamic`** | Both use `selectDynamic`/`applyDynamic`, but structural types are statically type-checked while `Dynamic` is not. |
| **Opaque types** | `NamedTuple` is an opaque type alias: `opaque type NamedTuple[N <: Tuple, +V <: Tuple] >: V = V`. Names exist only at compile time and are erased at runtime. |
| **Case classes** | `NamedTuple.From[CaseClass]` extracts the named tuple type corresponding to a case class's first parameter list, bridging nominal and structural worlds. |
| **Pattern matching** | Named tuple patterns support matching on a subset of fields in any order. Named patterns also work on case classes. |
| **Match types** | The `Fields` type member in `Selectable` can be computed via match types or `NamedTuple.Map`, enabling typed query DSLs. |
| **Extension methods** | Operations on named tuples (`head`, `tail`, `map`, `zip`, `++`) are defined as extension methods in the `NamedTuple` object. |
| **Transparent inline** | Can be combined with structural types to generate `Selectable` wrappers at compile time. |

## Gotchas and Limitations

- **Reflective dispatch is slow.** Using `reflectiveSelectable` triggers Java reflection at runtime. The required import serves as a warning. Custom `Selectable` implementations can avoid this.
- **`asInstanceOf` needed for Record construction.** The generic `Record` class is too weakly typed for the compiler to verify the refinement. In practice, a database layer or macro would handle the cast.
- **Non-Selectable anonymous classes lose refinements.** If the parent trait does not extend `Selectable`, anonymous class members beyond those declared in the parent are not visible through the inferred type.
- **Named tuple mixing rules.** It is illegal to mix named and unnamed elements in a single tuple. All elements must be named or all must be unnamed.
- **Named tuple ordering matters.** `(name: String, age: Int)` and `(age: Int, name: String)` are different, incompatible types.
- **Conversion asymmetry.** Unnamed tuples are subtypes of named tuples (by position), but named tuples require an explicit `.toTuple` or compiler-inserted conversion to become unnamed tuples. Inside type constructors (e.g., `List[Person]` to `List[(String, Int)]`), automatic conversion does not apply.
- **Arity-one source incompatibility.** `(age = 1)` is now a named tuple, not a parenthesized assignment, which is a source-level change from Scala 2.

## Use-Case Cross-References

- `[-> UC-02](../usecases/UC02-domain-modeling.md)` Database row access with structural types and custom `Selectable`.
- `[-> UC-05](../usecases/UC12-compile-time.md)` Typed query DSLs using `NamedTuple.From` and computed `Fields`.
- `[-> UC-07](../usecases/UC14-extensibility.md)` Lightweight record types for configuration or API responses without defining case classes.
- `[-> UC-10](../usecases/UC17-variance.md)` Duck-typing interop with Java classes that share method signatures but no common interface.
- `[-> UC-13](../usecases/UC09-builder-config.md)` Named tuple pattern matching for destructuring complex return values.
