# Structural Contracts

## The Constraint

Accept values based on the members they expose, not the class hierarchy they belong to. Structural types and refinements let you express duck-typed contracts that the compiler still verifies statically.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Structural types | Accept any value with matching members; no shared supertype needed | [-> T07](T07-structural-typing.md)(../catalog/T07-structural-typing.md) |
| Refinement types | Narrow a type by adding member requirements | [-> T26](T26-refinement-types.md)(../catalog/T26-refinement-types.md) |
| Selectable / Dynamic | Provide typed access to structurally-defined fields via `selectDynamic` | [-> T07](T07-structural-typing.md)(../catalog/T07-structural-typing.md) |
| Union types | Combine unrelated structural types into a single parameter | [-> T02](T02-union-intersection.md)(../catalog/T02-union-intersection.md) |

## Patterns

### 1 — Structural type as a parameter

Accept any object that has a `close(): Unit` method, regardless of its class hierarchy.

```scala
import reflect.Selectable.reflectiveSelectable

type Closeable = { def close(): Unit }

def safeUse[A](resource: Closeable)(f: Closeable => A): A =
  try f(resource)
  finally resource.close()

// Works with any class exposing close():
class MyConn:
  def close(): Unit = println("closed")
  def query(sql: String): String = s"result of $sql"

safeUse(MyConn())(r => println("using resource"))
```

### 2 — Refinement types to narrow a base type

Refine a base type to require additional members. The compiler checks that the provided value satisfies both the base type and the refinement.

```scala
import reflect.Selectable.reflectiveSelectable

type Named    = { val name: String }
type HasAge   = { val age: Int }
type Person   = Named & HasAge

def greet(p: Person): String =
  s"Hello, ${p.name}, age ${p.age}"

// Any class (or anonymous instance) matching the shape works:
val p = new { val name = "Alice"; val age = 30 }
greet(p)   // "Hello, Alice, age 30"
```

### 3 — Selectable trait for typed dynamic fields

Implement `Selectable` to provide compile-time-checked field access on structurally-typed records.

```scala
class Record(fields: Map[String, Any]) extends Selectable:
  def selectDynamic(name: String): Any = fields(name)

type UserRec = Record { val name: String; val email: String }

val user: UserRec =
  Record(Map("name" -> "Alice", "email" -> "a@b.com")).asInstanceOf[UserRec]

// Typed access — the compiler knows these fields exist:
val n: String = user.name
val e: String = user.email
// user.age  // compile error — age not in the refinement
```

### 4 — Structural bounds on type parameters

Constrain a generic parameter to any type exposing specific members.

```scala
import reflect.Selectable.reflectiveSelectable

def size[T <: { def length: Int }](t: T): Int = t.length

size("hello")           // 5 — String has length
size(List(1, 2, 3))    // 3 — List has length
// size(42)             // compile error — Int has no length
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Structural types | Supported but required `import language.reflectiveCalls`; runtime reflection | Same import; `Selectable` trait gives a hook to customise dispatch |
| Refinement types | Worked as type members on compound types; verbose | Same concept; cleaner syntax with `&` intersection |
| Typed records | Not expressible without macros or Shapeless HLists | `Selectable` + refinement types provide a built-in path |
| Performance | Always reflective invocation — slow | `Selectable` implementations can use maps or code generation instead of reflection |

## When to Use Which Feature

**Use structural types** when integrating code from different libraries that coincidentally expose the same API surface but share no common trait.

**Use refinement types** when you want to narrow a base type to require specific additional members — e.g., requiring both `name` and `age` on any value.

**Use Selectable** when building record-like abstractions (e.g., database rows, config objects) where field names are known at compile time but the backing storage is a map or similar structure.

**Prefer nominal types** (traits, type classes) when you control the code and can define a shared interface. Structural types add indirection and reflection overhead; use them at integration boundaries.
