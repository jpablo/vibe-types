# Capture Checking, `CanThrow`, and Pure Functions

> **Status:** Experimental (research) | **Since:** Scala 3.2

## What it is

Capture checking is an experimental extension to Scala 3's type system (`import language.experimental.captureChecking`) that tracks which _capabilities_ -- references to objects that perform side effects such as I/O, mutation, or exception throwing -- are retained by a value. Every value's type can carry a _capture set_ listing the capabilities it closes over, and the compiler enforces that capabilities do not escape their intended scope. Built on this foundation, `CanThrow[E]` provides checked exceptions as capabilities, and pure function types (`A -> B`) denote functions that capture nothing at all.

## What constraint it lets you express

**A function's type declares exactly which capabilities (I/O handles, loggers, exception tokens) it may use or retain, and the compiler statically prevents capabilities from escaping their owning scope.** This makes effect tracking, resource safety, and purity enforceable at the type level rather than by convention.

## Minimal snippet

```scala
import language.experimental.captureChecking

// Resource safety: prevent a file handle from escaping
def usingLogFile[T](op: FileOutputStream^ => T): T =
  val logFile = FileOutputStream("log")
  val result = op(logFile)
  logFile.close()
  result

// Safe: the capability is used eagerly
val xs = usingLogFile { f =>
  List(1, 2, 3).map { x => f.write(x); x * x }
}

// Unsafe: the capability would escape in a closure -- compile error
// val later = usingLogFile { f => () => f.write(0) }
//   error: capability f cannot be included in outer capture set

// Checked exceptions via CanThrow
import language.experimental.saferExceptions

class LimitExceeded extends Exception

def f(x: Double): Double throws LimitExceeded =
  if x < 1e9 then x * x else throw LimitExceeded()

@main def test(xs: Double*) =
  try println(xs.map(f).sum)
  catch case _: LimitExceeded => println("too large")
```

## Interaction with other features

- **Capturing types and capture sets.** A type `T^{c1, c2}` means "a `T` that may retain capabilities `c1` and `c2`." The universal capability `cap` covers all others, so `T^` (shorthand for `T^{cap}`) means "captures anything." Pure types (no capture set) are subtypes of all capturing types with the same underlying type.
- **Pure vs impure function types.** `A => B` is sugar for `A ->{cap} B` (impure, may capture anything). `A -> B` denotes a pure function that captures nothing. Intermediate forms like `A ->{c} B` capture only `c`. The same applies to context functions (`?=>` vs `?->`).
- **CanThrow and `throws` clauses.** `CanThrow[E]` is an erased capability class. A `throw Exc()` requires a `CanThrow[Exc]` in scope. The `try` block synthesizes the capability for its catch clauses. The `throws` keyword is sugar: `def m(x: T): U throws E` desugars to `def m(x: T)(using CanThrow[E]): U`. This achieves effect-polymorphic checked exceptions without changing `map` or other HOF signatures. [-> UC-14](../usecases/UC08-error-handling.md)
- **Capability classes.** Types extending `caps.SharedCapability` automatically carry a capture set; writing `FileSystem` where `class FileSystem extends SharedCapability` implicitly means `FileSystem^`.
- **Subtyping and subcapturing.** Smaller capture sets produce subtypes: `T^{c} <: T^{c, d} <: T^{cap}`. Pure types are subtypes of any capturing variant. The subcapturing relation is transitive and accounts for nested capabilities.
- **Escape checking and avoidance.** Capabilities follow lexical scoping: a capture set cannot mention a capability not visible at the point where the set is defined. When a local capability would appear in a result type, the compiler _widens_ (avoids) it to the smallest visible superset.
- **Erased definitions.** `CanThrow` extends `compiletime.Erased`, so exception capabilities carry zero runtime cost. [-> UC-04](../usecases/UC11-effect-tracking.md)

## Gotchas and limitations

1. **Highly experimental.** Capture checking evolves rapidly; APIs and semantics may change between Scala versions. Always use the latest nightly.
2. **Capability escape in `try`.** The current `CanThrow` model does not prevent capabilities from escaping a `try` scope in a returned closure. A closure returned from a `try` body can carry the synthesized `CanThrow` capability, causing an uncaught exception at a later call site. Full enforcement awaits ephemeral capability tracking.
3. **`->` and `?->` are soft keywords.** In type position `->` denotes a pure function type, but in term position it remains a regular identifier (e.g., `Map("x" -> 1)` still works).
4. **Methods do not capture directly.** Since methods are not values, they do not carry capture sets themselves. The capabilities they reference are instead tracked in the capture set of their enclosing object.
5. **Lazy val initialization.** Lazy vals behave like parameterless methods for capture-checking purposes: accessing a lazy val charges its enclosing object's capability to the current capture set.
6. **`unsafeExceptions.canThrowAny`.** Importing this given provides `CanThrow[Exception]` globally, disabling exception checking. Useful for migration but defeats the purpose of safer exceptions.
7. **Only simple catch patterns.** The compiler generates `CanThrow` capabilities only for catch clauses of the form `case ex: Ex =>`; constructor patterns and guarded patterns are not supported under `saferExceptions`.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) Union types: `throws E1 | E2` uses union types to express multi-exception capabilities.
- [-> UC-04](../usecases/UC11-effect-tracking.md) Erased definitions: `CanThrow` is the primary consumer of erased capability classes.
- [-> UC-09](../usecases/UC16-nullability.md) Explicit nulls: capture checking and null checking are complementary layers of static safety.
- [-> UC-04](../usecases/UC11-effect-tracking.md) Effect systems: capture checking generalizes beyond exceptions to I/O, mutation, and algebraic effects.
- [-> UC-04](../usecases/UC11-effect-tracking.md) Purity enforcement: `A -> B` function types compose with capture checking to guarantee side-effect freedom.
