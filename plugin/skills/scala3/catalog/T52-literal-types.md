# Literal Types (Singleton Types)

> **Since:** Scala 3.0 (first-class literal types) | Scala 2.13 had `-Yliteral-types` behind a flag

## What it is

In Scala 3, every literal value has a **singleton type** — a type inhabited by exactly that one value. The integer `42` has type `42`, the string `"hello"` has type `"hello"`, and `true` has type `true`. These singleton types are proper subtypes of their widened form: `42 <: Int`, `"hello" <: String`, `true <: Boolean`.

Singleton types are the foundation that makes const generics ([-> catalog/T15](T15-const-generics.md)), compile-time operations ([-> catalog/T16](T16-compile-time-ops.md)), and match types ([-> catalog/T41](T41-match-types.md)) possible in Scala 3. Where other languages bolt on a separate "literal type" feature, Scala 3 integrates it directly into the subtyping lattice.

## What constraint it enforces

**A singleton type restricts a value to exactly one literal. The compiler rejects any other value at that position, and distinct literals produce distinct, incompatible types.**

- `val x: 42 = 42` is accepted; `val x: 42 = 43` is rejected.
- A function parameter typed `"GET" | "POST"` only accepts those two string values.
- Type parameters bounded by singletons (`N <: Int & Singleton`) preserve the literal through generic code.

## Minimal snippet

```scala
val theAnswer: 42 = 42          // OK — 42 has type 42
// val wrong: 42 = 43           // error: Found (43 : Int), Required (42 : Int)

val greeting: "hello" = "hello" // OK
val flag: true = true           // OK

// Singleton types are subtypes of their widened form
val n: Int = theAnswer           // OK — 42 <: Int (widening)
// val back: 42 = n              // error — Int is not <: 42
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Const generics** [-> catalog/T15](T15-const-generics.md) | Singleton types are the mechanism behind `Vec[3]` and `Matrix[2, 3]` — type parameters bounded by `<: Int` carry literal types. T15 builds directly on this feature. |
| **Match types** [-> catalog/T41](T41-match-types.md) | Match types pattern-match on singleton types for type-level conditionals: `type IsZero[N <: Int] = N match { case 0 => true; case _ => false }`. |
| **Compile-time ops** [-> catalog/T16](T16-compile-time-ops.md) | `compiletime.ops.int.*` performs arithmetic on singleton `Int` types. `constValue[T]` extracts a singleton type's value at runtime. |
| **Union types** [-> catalog/T02](T02-union-intersection.md) | Unions of singletons create closed value sets: `type Color = "red" \| "green" \| "blue"`, similar to Python's `Literal`. |
| **Opaque types** [-> catalog/T03](T03-newtypes-opaque.md) | Combine singleton types with opaque types for zero-cost wrappers that carry compile-time information. |

## Gotchas and limitations

1. **Inference widens by default.** `val x = 42` infers `x: Int`, not `x: 42`. To preserve the singleton type, annotate explicitly (`val x: 42 = 42`) or use a `Singleton` bound in generic contexts.

2. **The `Singleton` upper bound.** To prevent widening in generic code, bound the type parameter: `def f[N <: Int & Singleton](n: N)`. Without `Singleton`, the compiler may widen `N` to `Int` and lose the literal.

3. **No singleton types for `Float` or `Double`.** Singleton types exist for `Int`, `Long`, `String`, `Boolean`, `Char`, and `Symbol`. Floating-point literals do not get singleton types.

4. **`constValue` fails on widened types.** If a type parameter has been inferred as `Int` rather than a specific literal, `constValue[N]` will not compile. Ensure callers provide literal types.

5. **Runtime values cannot become singletons.** There is no way to take a runtime `Int` and lift it to a singleton type. The value must be a literal or computed from other compile-time constants.

6. **Pattern matching does not narrow to singletons automatically.** Matching on `case 42 =>` narrows to `Int`, not to the singleton `42`, unless the scrutinee was already singleton-typed.

## Beginner mental model

Think of every literal as having a **name tag that IS the value itself**. The number `42` carries a tag that says "I am exactly 42, and nothing else." This tag is a type, and it fits inside the bigger category `Int` — but it is more specific. When you tell the compiler "this variable holds `42`", it can reject `43` without running your code.

## Example A — Union of singletons as a closed value set

```scala
type Direction = "north" | "south" | "east" | "west"

def move(dir: Direction): (Int, Int) = dir match
  case "north" => (0, 1)
  case "south" => (0, -1)
  case "east"  => (1, 0)
  case "west"  => (-1, 0)

move("north")   // OK — returns (0, 1)
// move("up")   // error: Found "up", Required "north" | "south" | "east" | "west"
```

## Example B — Preserving singletons with the Singleton bound

```scala
import scala.compiletime.constValue

def sizeOf[N <: Int & Singleton]: Int = constValue[N]

val s = sizeOf[10]    // OK — returns 10 at runtime
// sizeOf[Int]         // error — Int is not a singleton type

// Without Singleton bound, inference may widen:
def unsafe[N <: Int](n: N): Int = n  // N can be Int — singleton lost
def safe[N <: Int & Singleton](n: N): N = n  // N must be a literal
```

## Example C — Singleton types with match types

```scala
type Parity[N <: Int] = N match
  case 0 => "even"
  case 1 => "odd"

// The result type is itself a singleton string type
val check0: "even" = compiletime.constValueOf[Parity[0]]
val check1: "odd"  = compiletime.constValueOf[Parity[1]]
```

## Common type-checker errors and how to read them

### `Found: (43 : Int), Required: (42 : Int)`

**Meaning:** You assigned a different literal to a singleton-typed binding. The compiler shows both the found and required literal types.
**Fix:** Use the correct literal, or widen the annotation to `Int` if you don't need the singleton constraint.

### `Cannot reduce constValue[Int]`

**Meaning:** `constValue` requires a concrete singleton type, but received a widened type like `Int`. Ensure the type parameter carries a literal type by adding `& Singleton` to its bound.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Restrict values to a known set at compile time.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Model domain-specific value constraints as types.
- [-> UC-12](../usecases/UC12-compile-time.md) — Compile-time computation on type-level literals.
- [-> UC-18](../usecases/UC18-type-arithmetic.md) — Type-level arithmetic builds on singleton Int types.

## Source anchors

- [Scala 3 Reference — Literal Types](https://docs.scala-lang.org/scala3/reference/new-types/literal-types.html)
- [Scala 3 Reference — Singleton Types](https://docs.scala-lang.org/scala3/reference/new-types/literal-types.html#singleton-types)
- [Scala 3 Reference — Match Types](https://docs.scala-lang.org/scala3/reference/new-types/match-types.html)
- [scala.compiletime API](https://scala-lang.org/api/3.x/scala/compiletime.html)
- [SIP-23 — Literal-based singleton types](https://docs.scala-lang.org/sips/42.type.html)
