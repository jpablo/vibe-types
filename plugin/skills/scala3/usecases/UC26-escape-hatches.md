# Escape Hatches (Controlled Unsafety)

## The Constraint

Bypass the type system when necessary — FFI boundaries, performance-critical casts, legacy interop — while keeping unsafe operations visible, contained, and auditable. Scala 3 provides several escape hatches, each with a different risk profile.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Null safety | Explicit nulls mode separates `T` from `T | Null`; platform types bridge Java interop | [-> T13](T13-null-safety.md)(../catalog/T13-null-safety.md) |
| Type casts | `asInstanceOf` performs unchecked casts; `isInstanceOf` for runtime checks | [-> T14](T14-type-narrowing.md)(../catalog/T14-type-narrowing.md) |
| @unchecked | Suppress exhaustiveness warnings on deliberate partial matches | [-> T39](T39-notation-attributes.md)(../catalog/T39-notation-attributes.md) |
| Variance overrides | `@uncheckedVariance` suppresses variance errors at use site | [-> T08](T08-variance-subtyping.md)(../catalog/T08-variance-subtyping.md) |

## Patterns

### 1 — asInstanceOf for unchecked casts

The most direct escape hatch. Use only when you have external proof the cast is safe (e.g., after a runtime check, serialisation boundary, or JNI call).

```scala
def unsafeGet[A](raw: Any): A =
  raw.asInstanceOf[A]   // no runtime check on A if erased

// Safe pattern — guard with isInstanceOf first:
def safeCast[A](raw: Any)(using ct: reflect.ClassTag[A]): Option[A] =
  if ct.runtimeClass.isInstance(raw) then Some(raw.asInstanceOf[A])
  else None

safeCast[String]("hello")   // Some("hello")
safeCast[String](42)        // None
```

### 2 — Platform types under explicit nulls

With `-Yexplicit-nulls`, Java return types become `T | Null`. Use `.nn` to assert non-null, converting to `T`.

```scala
// With -Yexplicit-nulls enabled:
import java.util.HashMap

val map = HashMap[String, String]()
map.put("key", "value")

val v: String | Null = map.get("key")   // Java returns nullable
val safe: String = v.nn                  // asserts non-null; throws if null

// Idiomatic: convert to Option immediately at the boundary
val opt: Option[String] = Option(map.get("key"))
```

### 3 — @unchecked for deliberate partial matches

When you know a match is safe but the compiler cannot prove exhaustiveness, use `@unchecked` to suppress the warning.

```scala
sealed trait Shape
case class Circle(r: Double) extends Shape
case class Rect(w: Double, h: Double) extends Shape
case class Triangle(a: Double, b: Double, c: Double) extends Shape

// We know from context that shapes here are never Triangles:
def areaNoTriangle(s: Shape): Double = (s: @unchecked) match
  case Circle(r)   => math.Pi * r * r
  case Rect(w, h)  => w * h
  // Triangle is intentionally unhandled — will throw MatchError if violated
```

### 4 — null as an escape hatch

In standard Scala 3 (without explicit nulls), `null` inhabits all reference types. Treat it as an escape hatch, not a design tool.

```scala
// Interop with Java APIs that return null:
val result: String | Null = javaMethod()

// Defensive conversion:
val safe: Option[String] = Option(result)

// Or assert non-null with a meaningful error:
val assured: String = result match
  case null => throw IllegalStateException("unexpected null from javaMethod")
  case s    => s
```

### 5 — @uncheckedVariance for variance escape

Suppress variance errors when you know the use site is safe (e.g., internal mutable buffer in an otherwise covariant API).

```scala
import scala.annotation.uncheckedVariance

trait Producer[+A]:
  // Internal mutable state needs contravariant A, but the API is covariant:
  private var cache: A @uncheckedVariance = _

  def produce: A

// Without @uncheckedVariance, the compiler rejects `var cache: A`
// because A appears in a contravariant (write) position.
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| asInstanceOf | Same — unchecked cast | Same — use with ClassTag guard for safety |
| null | All reference types are nullable; no opt-in nullability | `-Yexplicit-nulls` separates `T` from `T \| Null`; `.nn` for boundary assertions |
| @unchecked | Same annotation | Same; more relevant now that exhaustiveness checking is stricter |
| @uncheckedVariance | Same | Same |
| Platform types | No concept — Java types just nullable | Under explicit nulls, Java types become `T \| Null` ("platform types") |

## When to Use Which Feature

**Use `asInstanceOf`** only behind a runtime guard (`isInstanceOf`, `ClassTag`, pattern match) or at a serialisation/FFI boundary where you have external proof. Never scatter casts through business logic.

**Enable `-Yexplicit-nulls`** in new projects to push null handling to the boundary. Convert Java returns to `Option` immediately.

**Use `@unchecked`** when a partial match is intentional and documented — e.g., you filter a collection before matching. Add a comment explaining why the missing cases cannot occur.

**Treat every escape hatch as a code smell.** Wrap them in dedicated boundary modules, name them `unsafe*` or `unchecked*`, and keep them out of core domain logic.
