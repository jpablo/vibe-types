# Erased Definitions (`erased` parameters, `erased` vals, `compiletime.Erased`)

> **Status:** Experimental | **Since:** Scala 3.0

## What it is

Erased definitions are an experimental feature (`import scala.language.experimental.erasedDefinitions`) that allows parameters and `val` definitions to be marked `erased`, meaning they exist only at compile time and are completely removed before code generation. An erased parameter serves as compile-time evidence -- the compiler verifies it can be constructed, but no runtime object is ever allocated or passed. This enables zero-cost type-level programming where evidence types such as type class witnesses, state machine tokens, and capability markers carry no runtime overhead whatsoever.

## What constraint it lets you express

**A function can require compile-time proof (evidence) of an arbitrary type-level property without paying any runtime cost for that proof.** The `erased` modifier guarantees that evidence values are checked during compilation and then stripped entirely, producing bytecode with no trace of the evidence parameters.

## Minimal snippet

```scala
import scala.language.experimental.erasedDefinitions

// State machine: only valid transitions compile
sealed trait State
final class On extends State
final class Off extends State

class IsOff[S <: State]
object IsOff:
  inline given IsOff[Off]()

class IsOn[S <: State]
object IsOn:
  inline given IsOn[On]()

class Machine[S <: State]:
  def turnOn(using erased IsOff[S]): Machine[On] = Machine[On]()
  def turnOff(using erased IsOn[S]): Machine[Off] = Machine[Off]()

@main def test =
  val m = Machine[Off]()
  val m1 = m.turnOn       // ok
  val m2 = m1.turnOff     // ok
  // m1.turnOn             // error: State must be Off
  // m2.turnOff            // error: State must be On
```

At runtime, `turnOn` and `turnOff` take zero arguments -- the `IsOff` / `IsOn` evidence is erased.

## Interaction with other features

- **Given instances and context bounds.** Erased parameters work naturally with `using` clauses. When a type class extends `compiletime.Erased`, its instances are implicitly erased, so context bounds like `[T: CanSerialize]` expand to `(using erased CanSerialize[T])` automatically.
- **Inline and pure expressions.** Arguments to erased parameters must be _pure expressions_ (constants, non-lazy immutable vals, or constructor applications with no initializer). Inline given definitions satisfy this after inlining, which is why erased evidence typically uses `inline given`.
- **`CanThrow` capabilities.** The `CanThrow[E]` class used for safer exceptions extends `Erased`, making exception capabilities zero-cost at runtime. [-> UC-21]
- **`CanEqual` (multiversal equality).** The `CanEqual` evidence for equality checking is a candidate for becoming `Erased`, removing its runtime footprint. [-> UC-05]
- **Function types.** Erased parameters are reflected in function types: `(erased T, U) => R` is a distinct type from `(T, U) => R`, with no subtype relation between them.
- **Overriding.** Erased and non-erased parameters must match exactly in overrides; you cannot change a parameter from erased to non-erased or vice versa.

## Gotchas and limitations

1. **Purity requirement.** Arguments passed to erased parameters must be pure. Side-effecting expressions, non-inline method calls, and lazy vals are rejected. This prevents "faking" evidence via `null.asInstanceOf[Evidence]` or recursive definitions.
2. **Cannot use erased values in computation.** An erased parameter cannot appear in non-erased expressions. It can only be forwarded to another erased parameter or used in the path of a dependent type.
3. **No `lazy val`, `var`, or `object`.** The `erased` modifier cannot appear on lazy vals, mutable variables, or object definitions.
4. **No call-by-name.** Erased parameters cannot be call-by-name (`erased` cannot combine with `=> T`).
5. **Polymorphic function literals.** Polymorphic function literals with erased parameters are not yet supported (implementation restriction).
6. **`erasedValue` vs `unsafeErasedValue`.** `compiletime.erasedValue[T]` is an erased reference that must be eliminated by inlining; it is not a pure expression and cannot persist as erased evidence. The escape hatch `scala.caps.unsafe.unsafeErasedValue[T]` counts as pure but should only be used when safety can be proven by other means.
7. **Overloading after erasure.** Methods whose signatures differ only in erased parameters may collide after erasure, since erased parameters are removed.

## Use-case cross-references

- [-> UC-05] Type class evidence (e.g., `CanEqual`, `Ordering`) can be erased for zero-overhead constraints.
- [-> UC-19] Explicit nulls: erased capabilities compose with null-safe types for comprehensive static checking.
- [-> UC-21] `CanThrow` capabilities for safer exceptions are the flagship use of erased definitions.
- [-> UC-22] Phantom types / state machines use erased evidence to enforce valid state transitions at zero runtime cost.
