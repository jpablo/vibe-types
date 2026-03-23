# UC-09 -- Nullability and Optionality

## 1. The Constraint

**Eliminate null pointer exceptions through the type system.**
Every reference is non-nullable by default. Nullability must be declared explicitly in the type, and every nullable value must be checked before use. The compiler rejects code that dereferences a potentially-null reference without proof of non-nullness.

## 2. Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Explicit nulls | Under `-Yexplicit-nulls`, `Null` is no longer a subtype of reference types; nullable values must be typed `T \| Null`. | [-> T13](T13-null-safety.md)(../catalog/T13-null-safety.md) |
| Union types | `T \| Null` is the standard encoding of "nullable T," reusing first-class union types. | [-> T02](T02-union-intersection.md)(../catalog/T02-union-intersection.md) |
| Opaque types | Wrap nullable representations with a safe API that hides the `null` from callers. | [-> T03](T03-newtypes-opaque.md)(../catalog/T03-newtypes-opaque.md) |
| Match types | Compute at the type level whether a type is nullable, or strip nullability generically. | [-> T41](T41-match-types.md)(../catalog/T41-match-types.md) |

## 3. Patterns

### Pattern A: Enabling Explicit Nulls

Enable `-Yexplicit-nulls` in the compiler options. Every reference type `T` becomes non-nullable. To express nullability, use `T | Null`.

```scala
// scalacOptions += "-Yexplicit-nulls"

val name: String = "Ada"
// val bad: String = null      // error: found Null, required String

val nullable: String | Null = null  // ok

// Cannot call methods directly on nullable types:
// nullable.length  // error: length is not a member of String | Null

// Flow-sensitive narrowing after a null check:
if nullable != null then
  println(nullable.length)  // ok: nullable is refined to String here

// Assert non-null with .nn (throws NPE if null):
val forced: String = nullable.nn
```

### Pattern B: `T | Null` for Nullable Values and `.nn` for Assertion

Model nullable data explicitly. Use pattern matching, `Option` conversion, or `.nn` to safely extract values.

```scala
def findUser(id: Long): User | Null =
  if id > 0 then User(id, "found") else null

case class User(id: Long, name: String)

// Pattern match to handle both cases:
findUser(42) match
  case u: User => println(u.name)
  case null    => println("not found")

// Convert to Option for idiomatic Scala:
val maybeUser: Option[User] = Option(findUser(42))  // None if null

// Chain with .nn when you are certain it is non-null:
val user: User = findUser(42).nn  // throws NPE if null
```

### Pattern C: Java Interop with Nullability Annotations

Java methods return flexible types by default. Recognized `@NonNull` / `@Nullable` annotations refine the types at the Scala boundary.

```scala
// Given Java code:
//   public class Repository {
//     @Nullable public User findById(long id) { ... }
//     @NonNull  public List<User> findAll() { ... }
//   }

// In Scala 3 with explicit nulls:
val repo = Repository()

val user: User | Null = repo.findById(1)  // @Nullable => T | Null
val all: java.util.List[User] = repo.findAll()  // @NonNull => T (non-nullable)

// Without annotations, Java types are flexible (T?) --
// assignable to either T or T | Null depending on context.
// Use -Yno-flexible-types to force everything to T | Null for maximum safety.

// Escape hatch for gradual migration:
import scala.language.unsafeNulls
val unsafeUser: User = repo.findById(1)  // compiles, but may NPE
```

### Pattern D: Match Type to Strip Nullability

Define a match type that removes `| Null` from a type, useful in generic code that must handle both nullable and non-nullable type parameters.

```scala
type StripNull[T] = T match
  case t | Null => t
  case t        => t

// StripNull[String | Null]  =  String
// StripNull[String]         =  String

def unwrap[T](value: T)(using ev: T =:= (StripNull[T] | Null)): Option[StripNull[T]] =
  val v = ev(value)
  if v != null then Some(v.asInstanceOf[StripNull[T]]) else None

// Useful in generic APIs that abstract over nullable/non-nullable parameters.
```

## 4. Scala 2 Comparison

| Aspect | Scala 2 | Scala 3 with explicit nulls |
|---|---|---|
| Null subtyping | `Null <: AnyRef`. Every reference variable can hold `null`. | `Null <: Any` only. `String` does not accept `null`. |
| Expressing nullability | Convention: use `Option[T]`. But nothing prevents `val s: String = null`. | Type system: `T \| Null` for nullable, `T` for non-nullable. The compiler enforces it. |
| Java interop | All Java reference types implicitly nullable; no compile-time check. | Flexible types (`T?`) bridge the gap. `@Nullable` / `@NonNull` annotations are recognized. |
| Flow typing | Not available. Null checks did not narrow the type. | After `if x != null`, `x` is refined to non-nullable in the branch body. |
| Gradual migration | No migration path -- `null` was always valid. | `unsafeNulls` import allows treating `T \| Null` as `T` during migration. |

## 5. When to Use Which Feature

| If you need... | Prefer |
|---|---|
| Project-wide null safety | Enable **`-Yexplicit-nulls`** (Pattern A). Let the compiler find every unhandled null. |
| Idiomatic nullable return values | Use **`T \| Null`** at API boundaries and convert to **`Option`** immediately (Pattern B). |
| Safe Java interop | Annotate Java code with **`@NonNull`** / **`@Nullable`** (Pattern C). Use `-Yno-flexible-types` for strictest checking. |
| Generic null stripping | Use a **match type** (Pattern D) to compute the non-nullable version of a type parameter. |
| Gradual migration from Scala 2 | Start with **`unsafeNulls`** import in files that are not yet migrated; remove it file by file. |
| A safe wrapper over a nullable representation | Use an **opaque type** whose companion provides a smart constructor that rejects `null`, hiding the representation from callers. |
