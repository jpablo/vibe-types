# Explicit Nulls (`T | Null`, `.nn`, `unsafeNulls`)

## What it is

Explicit nulls is an opt-in feature (enabled with `-Yexplicit-nulls`) that modifies the Scala 3 type hierarchy so that `Null` is no longer a subtype of every reference type. Instead, `Null` becomes a subtype only of `Any` and `Matchable`. To represent a nullable reference you must write `T | Null` explicitly as a union type, and the compiler will reject any attempt to use a nullable value without first proving it is non-null. The feature also provides flow-sensitive type narrowing, Java interop via flexible types, and an escape-hatch import `unsafeNulls` for gradual migration.

## What constraint it lets you express

**A reference type `T` can never hold `null` unless its type explicitly says `T | Null`, forcing every potential null dereference to be handled statically.** This moves null-safety from a runtime concern (NullPointerException) to a compile-time guarantee.

## Minimal snippet

```scala
// Opt in via compiler flag: -Yexplicit-nulls

val x: String = null          // error: found Null, required String
val y: String | Null = null   // ok

// Cannot call methods on nullable types directly
// y.trim                     // error: trim is not a member of String | Null

// Option 1: flow typing via null check
if y != null then
  val len = y.trim.length     // ok, y: String in this branch

// Option 2: assert non-null with .nn
val z: String = y.nn          // compiles; throws NPE at runtime if y is null
```

## Interaction with other features

- **Union types.** Nullability is encoded as `T | Null`, reusing Scala 3's first-class union type mechanism. All union-type rules (pattern matching, subtyping) apply directly. [-> UC-01]
- **Flow typing.** The compiler performs flow-sensitive narrowing: after `if x != null`, `x` is refined to non-nullable within the `then` branch. This extends to `&&`, `||`, `!`, `match` case guards, and `assert`.
- **Java interop / flexible types.** Java-originated reference types are loaded as _flexible types_ (`T?`) with bounds `T | Null <: T? <: T`. This lets them be used as either nullable or non-nullable depending on context, aligning Scala's safety guarantees with Java's. Flexible types are non-denotable (compiler-only). Recognized `@NotNull` annotations (e.g., `@org.jetbrains.annotations.NotNull`) suppress nullification.
- **`unsafeNulls` escape hatch.** Importing `scala.language.unsafeNulls` (or setting `-language:unsafeNulls`) allows `T | Null` to be used as `T` without null checks, enabling gradual migration from Scala 2 or unchecked Scala 3 code.
- **Pattern matching.** Match cases like `case _: String =>` narrow a `String | Null` scrutinee to `String` in the body. [-> UC-03]
- **Mutable variables.** Local mutable variables can be tracked for nullability as long as they are not captured or mutated by closures.

## Gotchas and limitations

1. **Unsoundness from uninitialized fields.** Fields in a class start as `null` before their initializer runs, so a non-nullable field can temporarily hold `null` during construction. The `-Wsafe-init` flag can detect this.
2. **No tracking of mutable-variable prefixes.** If `x` is mutable, the compiler cannot track nullability of paths like `x.a`.
3. **No aliasing inference.** `if s != null && s == s2` will narrow `s` but not `s2`, even though they are equal.
4. **`.nn` on mutable variables.** Using `.nn` directly on a mutable variable may introduce an unknown type into the variable's inferred type; prefer a null check instead.
5. **Flexible types are non-denotable.** You cannot write `T?` in source code; only the compiler constructs flexible types when loading Java definitions. Use `-Yno-flexible-types` to get `T | Null` union types instead.
6. **`unsafeNulls` is not equivalent to regular Scala.** Generic Java methods returning `T | Null` where `T` is a type parameter still require `.nn` even under `unsafeNulls`, because the compiler cannot confirm `T` is a reference type.

## Use-case cross-references

- [-> UC-01] Union types are the foundation: `T | Null` is just `Union[T, Null]`.
- [-> UC-03] Match types and pattern matching integrate with null narrowing.
- [-> UC-19] Java interop patterns: wrapping legacy APIs that return nullable values with safe Scala facades.
- [-> UC-20] Erased definitions: `CanThrow` capabilities combine with explicit nulls for fully safe exception + null checking.
