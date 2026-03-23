# Annotations & Compiler Directives

> **Since:** Scala 2 (most annotations); Scala 3.0 adds `@targetName`, `@experimental`; Scala 3.3 stabilizes `@experimental`

## What it is

Scala annotations are metadata markers attached to definitions that influence compiler behavior, runtime semantics, or tooling. Unlike Rust attributes (`#[inline]`, `#[must_use]`) which are a core part of the language grammar, Scala annotations are syntactically uniform (`@name` or `@name(args)`) and may be processed at compile time, retained in bytecode, or both. They serve as **compiler directives** — instructions that modify how the compiler optimizes, checks, or names the generated code.

Scala 3 inherits most annotations from Scala 2 and adds several new ones. The annotation system also interoperates with Java annotations, making JVM interop straightforward.

## What constraint it enforces

**Annotations constrain or direct the compiler's behavior for a specific definition: requiring tail-call optimization, forcing inlining, renaming in bytecode, marking as deprecated, or gating behind experimental flags. The compiler either enforces the constraint at compile time (e.g., `@tailrec` fails if recursion is not in tail position) or emits modified bytecode/metadata.**

## Minimal snippet

```scala
import scala.annotation.*

// @tailrec — compiler verifies tail recursion
@tailrec
def factorial(n: Long, acc: Long = 1): Long =
  if n <= 1 then acc else factorial(n - 1, n * acc)

// @inline — hint to inline the method body at call sites
@inline def square(x: Int): Int = x * x

// @targetName — set the JVM bytecode name (for operator interop)
extension (x: Int)
  @targetName("plus_mod")
  def +%(y: Int): Int = (x + y) % 100

// @deprecated — warn callers with a message and since-version
@deprecated("use newMethod instead", since = "2.0")
def oldMethod(): Unit = ()

// @main — mark an entry point (Scala 3)
@main def run(): Unit = println("Hello!")
```

## Key annotations reference

| Annotation | Effect | Compile-time check? |
|------------|--------|---------------------|
| `@tailrec` | Verifies the annotated method is tail-recursive; compiler error if not | Yes |
| `@inline` | Requests the compiler/JIT to inline the method body at call sites | Hint only |
| `@targetName(name)` | Sets the JVM-level name of a definition; enables symbolic operator names with readable bytecode names | Yes (name collision check) |
| `@deprecated(msg, since)` | Emits a deprecation warning when the definition is referenced | Yes (warning) |
| `@experimental` | Marks a definition as experimental; using it requires `-language:experimental` or `@experimental` on the call site | Yes |
| `@main` | Generates a program entry point with argument parsing | Yes |
| `@throws(classOf[E])` | Declares checked exceptions for Java interop | Metadata only |
| `@unchecked` | Suppresses exhaustivity warnings in pattern matches | Yes (suppresses) |
| `@switch` | Verifies that a match compiles to a JVM `tableswitch`/`lookupswitch`; error if not | Yes |

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Compile-time operations** [-> catalog/T16](T16-compile-time-ops.md) | `@inline` and `@tailrec` complement `inline def` (which guarantees inlining). An `inline def` is always inlined; `@inline` is a best-effort hint for non-inline methods. |
| **Macros / metaprogramming** [-> catalog/T17](T17-macros-metaprogramming.md) | Macro annotations (experimental in Scala 3) process custom annotations at compile time to generate code. `@experimental` gates access to such unstable APIs. |
| **Changed / dropped features** [-> catalog/T44](T44-changed-dropped.md) | `@deprecated` is the standard migration tool when features change between Scala versions. `@targetName` helps maintain binary compatibility across renames. |
| **Extension methods** [-> catalog/T19](T19-extension-methods.md) | `@targetName` is especially useful for extension methods that define symbolic operators, ensuring readable names in bytecode and Java interop. |

## Gotchas and limitations

1. **`@tailrec` only checks self-recursion.** Mutual recursion between two methods is not verified by `@tailrec`. Only direct tail calls to the same method qualify.

2. **`@inline` is not guaranteed.** Unlike `inline def` (which the Scala 3 compiler always inlines), `@inline` is merely a hint. The JIT may ignore it. Use `inline def` when inlining must happen.

3. **`@switch` limitations.** The match must use only literal constants, enums, or `final val` constants. Guards, extractors, and type patterns prevent tableswitch generation.

4. **`@experimental` propagation.** Using an `@experimental` definition requires that the call site is also marked `@experimental`, or the entire compilation unit opts in via `-language:experimental`. This can cascade through a codebase.

5. **Java annotation interop.** Not all Java annotation retention policies are supported. `SOURCE`-retained annotations are discarded before reaching Scala's compiler phases. `RUNTIME`-retained annotations are preserved in bytecode and accessible via reflection.

6. **`@unchecked` hides real bugs.** Suppressing exhaustivity warnings with `(expr: @unchecked) match { ... }` can mask genuine missing cases. Use sparingly and document why the match is believed to be complete.

## Beginner mental model

Think of annotations as **sticky notes** attached to your code. Each note is an instruction to the compiler: "Check that this is tail-recursive," "Try to inline this," "Warn anyone who uses this." The compiler reads the sticky notes during compilation and either follows the instruction or complains if it cannot.

## Example A — Safe operator naming with `@targetName`

```scala
case class Vec2(x: Double, y: Double):
  @targetName("add")
  def +(other: Vec2): Vec2 = Vec2(x + other.x, y + other.y)

  @targetName("scalarMultiply")
  def *(scalar: Double): Vec2 = Vec2(x * scalar, y * scalar)

// Scala sees: Vec2(1, 2) + Vec2(3, 4)
// Java sees:  vec.add(other)  — readable interop name
```

## Example B — `@switch` for performance-critical matching

```scala
import scala.annotation.switch

def category(c: Char): String = (c: @switch) match
  case 'a' | 'e' | 'i' | 'o' | 'u' => "vowel"
  case ' ' | '\t' | '\n'             => "whitespace"
  case _                              => "other"
// Compiles to a JVM lookupswitch — O(1) dispatch
```

## Use-case cross-references

- [-> UC-12](../usecases/UC12-compile-time.md) Annotations like `@tailrec`, `@switch`, and `@inline` enforce compile-time guarantees about generated code quality.

## Source anchors

- [Scala 3 Reference -- @targetName](https://docs.scala-lang.org/scala3/reference/other-new-features/targetName.html)
- [Scala 3 Reference -- @main Methods](https://docs.scala-lang.org/scala3/reference/changed-features/main-functions.html)
- [Scala 3 Reference -- @experimental](https://docs.scala-lang.org/scala3/reference/other-new-features/experimental-defs.html)
- [Scala Standard Library -- scala.annotation](https://www.scala-lang.org/api/3.x/scala/annotation.html)
