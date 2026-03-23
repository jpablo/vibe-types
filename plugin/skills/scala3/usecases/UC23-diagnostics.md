# Diagnostics

## The Constraint

Understand and act on compiler messages efficiently. Scala 3 provides flags for detailed explanations, unused-code warnings, and annotation-based suppression. Knowing the common error patterns and their fixes turns cryptic messages into actionable guidance.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Compiler flags | `-explain`, `-Wunused`, `-Werror` control verbosity and strictness | [-> T39](T39-notation-attributes.md)(../catalog/T39-notation-attributes.md) |
| @nowarn annotation | Suppress specific warnings without losing global strictness | [-> T39](T39-notation-attributes.md)(../catalog/T39-notation-attributes.md) |
| Inline / compiletime | `compiletime.error` for custom compile-time error messages | [-> T16](T16-compile-time-ops.md)(../catalog/T16-compile-time-ops.md) |
| Match types | Type-level diagnostics via `compiletime.error` in unmatched branches | [-> T41](T41-match-types.md)(../catalog/T41-match-types.md) |

## Patterns

### 1 — The -explain flag for detailed errors

When the compiler reports an error or warning, re-compile with `-explain` to get an expanded explanation with context and suggestions.

```scala
// Given this code:
val x: Int = "hello"

// Standard error:
//   Found:    ("hello" : String)
//   Required: Int

// With -explain:
//   Found:    ("hello" : String)
//   Required: Int
//
//   Explanation: ...a detailed paragraph about type mismatch,
//   expected type propagation, and possible fixes...
```

### 2 — -Wunused for dead code detection

Enable unused warnings to catch dead imports, parameters, and local definitions.

```scala
// scalacOptions += "-Wunused:all"
// or selectively:
//   -Wunused:imports    — unused imports
//   -Wunused:privates   — unused private members
//   -Wunused:locals     — unused local definitions
//   -Wunused:params     — unused parameters
//   -Wunused:explicits  — unused explicit parameters

import scala.collection.mutable.ArrayBuffer  // warning: unused import

def compute(x: Int, y: Int): Int = x * 2     // warning: parameter y is never used
```

### 3 — @nowarn for targeted suppression

Suppress specific warnings without turning off the check globally. Use the `value` parameter to match on message text or warning category.

```scala
import scala.annotation.nowarn

// Suppress a specific warning by message pattern:
@nowarn("msg=unused import")
import scala.collection.mutable.ArrayBuffer

// Suppress by category:
@nowarn("cat=deprecation")
def old(): Unit = legacyApi()

// Suppress at method level:
@nowarn("msg=parameter .* is never used")
def handler(ctx: Context, unused: Metadata): Unit =
  ctx.respond("ok")
```

### 4 — Custom compile-time error messages

Use `compiletime.error` to produce clear, domain-specific error messages when invalid types are used.

```scala
import scala.compiletime.error

inline def validate[T](value: T): T =
  inline value match
    case _: Int    => value
    case _: String => value
    case _         => error("validate only supports Int and String")

validate(42)       // OK
validate("hi")     // OK
// validate(3.14)  // error: validate only supports Int and String
```

### 5 — Common error patterns and fixes

| Error message | Likely cause | Fix |
|---|---|---|
| `Found: X, Required: Y` | Type mismatch; wrong return or argument type | Check expected type; add explicit type annotation to narrow the search |
| `No given instance of type T` | Missing implicit / given | Import or define `given T`; use `-explain` to see where the search looked |
| `Value x is not a member of Y` | Typo, missing import, or structural type needs `reflectiveSelectable` | Check spelling; import `reflect.Selectable.reflectiveSelectable` |
| `Match may not be exhaustive` | Non-exhaustive pattern match on a sealed hierarchy | Add missing cases or use a wildcard with `@unchecked` if intentional |
| `Unused import` / `Unused parameter` | Dead code with `-Wunused` enabled | Remove the import/parameter or annotate with `@nowarn` |
| `Implicit conversion requires import` | `Conversion` used without the language import | Add `import scala.language.implicitConversions` |

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Explain mode | Not available; community plugins provided some help | `-explain` built in; detailed explanations for most errors |
| Unused warnings | `-Ywarn-unused` variants; less granular | `-Wunused:imports,privates,locals,params,explicits` — fine-grained |
| Warning suppression | `@SuppressWarnings` (Java-style); limited | `@nowarn` with pattern matching on message text and category |
| Custom compile errors | Macro-based `???` hacks | `compiletime.error` — first-class, no macro overhead |
| Error formatting | Flat text; hard to parse | Coloured output, caret positions, `-explain` expansions |

## When to Use Which Feature

**Enable `-Wunused:all` and `-Werror`** in CI to catch dead code and prevent warning accumulation. This is the single highest-value diagnostics setting.

**Use `-explain`** during development when a type error is unclear. It often reveals the implicit search path or type inference chain that led to the mismatch.

**Use `@nowarn`** to document intentional exceptions — "this import looks unused but is needed for an implicit" — rather than turning off warnings globally.

**Use `compiletime.error`** in library code to give users clear messages when they instantiate a generic with an unsupported type.
