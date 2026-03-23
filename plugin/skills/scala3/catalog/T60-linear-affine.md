# Linear and Affine Types (Not Supported -- JVM Limitation)

> **Since:** N/A; Scala 3 experimental capture checking (since 3.3, under `-language:experimental.captureChecking`)

## What it is

Scala 3 does **not** have linear or affine types. The JVM's garbage-collected memory model allows unrestricted aliasing -- any reference can be freely copied, shared, and stored, with the GC handling cleanup. There is no compiler-enforced "use at most once" discipline.

However, Scala 3 introduces **experimental capture checking** (since 3.3), which approximates effect linearity by tracking which capabilities a value captures. A `String^{io}` captures the `io` capability; the compiler ensures captured capabilities are not leaked beyond their scope. This is not affine typing per se, but it addresses a related concern: controlling how resources and effects propagate through a program.

For resource management without linear types, Scala relies on **`Using` / try-with-resources patterns**, scoped resource managers, and discipline-based conventions (e.g., closing streams in `finally` blocks).

## What constraint it enforces

**Scala 3 does not enforce single-use or linear constraints on values. Any value can be freely aliased and used multiple times.**

Experimental capture checking adds a weaker constraint:
- A value's captured capabilities must not escape their declared scope.
- Functions that capture mutable state or I/O capabilities carry that information in their type.
- This prevents capability leaks but does not prevent aliasing.

## Minimal snippet

```scala
// No linear types — values can be freely aliased
val x = List(1, 2, 3)
val y = x       // x is still valid — no move
val z = x       // x can be aliased indefinitely
println(x)      // OK — x is not consumed

// Resource management via Using (not linear types)
import scala.util.Using
import java.io.PrintWriter

Using(PrintWriter("output.txt")) { writer =>
  writer.println("hello")
}   // writer is closed here — by convention, not by the type system
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Experimental capture checking** [-> catalog/T43](T43-experimental-preview.md) | Capture checking tracks which capabilities a closure or value captures, approximating linearity for effects. `() ->{io} Unit` declares an I/O effect. |
| **Encapsulation** [-> catalog/T21](T21-encapsulation.md) | Without linear types, encapsulation relies on access modifiers (`private`, `protected`) and opaque types to prevent misuse, rather than single-use enforcement. |
| **Type classes** [-> catalog/T05](T05-type-classes.md) | A `Closeable` type class with `Using` provides resource management similar to Rust's `Drop` -- but as a library pattern, not a type-system guarantee. |
| **Context functions** [-> catalog/T42](T42-context-functions.md) | Scoped capabilities via context functions (`(using FileSystem) ?=> Unit`) approximate linear resource access by tying capabilities to lexical scope. |
| **Immutability** [-> catalog/T32](T32-immutability-markers.md) | Scala compensates for lack of linear types by encouraging immutability. Immutable values can be safely aliased since aliasing only causes problems with mutation. |

## Gotchas and limitations

1. **Resource leaks are possible.** Without linear types, nothing prevents storing a `BufferedReader` in a long-lived collection and forgetting to close it. Linters and `Using` help but do not provide compile-time guarantees.

2. **Capture checking is experimental.** As of Scala 3.3+, capture checking requires `-language:experimental.captureChecking` and the surface syntax and semantics are still evolving. Do not rely on it for production code yet.

3. **No move semantics.** You cannot express "this function takes ownership and invalidates the caller's reference." APIs that need exclusive access must rely on conventions, documentation, or runtime checks.

4. **Double-use bugs.** Submitting a form token twice, closing a connection twice, or processing a message twice are all possible in Scala. These bugs must be caught by runtime checks or protocol-level idempotency.

5. **JVM identity equality.** The JVM's reference semantics mean `val y = x` creates an alias, not a copy. Both `x` and `y` point to the same object. This is fundamental to the JVM and cannot be changed by Scala's type system.

## Beginner mental model

Think of Scala values as **library books with infinite renewal**. You can check out a book (bind a variable), make copies of the reference card (alias freely), and keep the book as long as you want. The garbage collector is the librarian who eventually notices nobody has a reference card anymore and returns the book to the shelf. There is no rule saying "you must return this book after reading it once" -- that would be linear typing, which the JVM does not support.

## Example A -- Using for scoped resource management

```scala
import scala.util.Using
import java.io.{BufferedReader, FileReader}

val lines: scala.util.Try[List[String]] =
  Using(BufferedReader(FileReader("data.txt"))) { reader =>
    Iterator.continually(reader.readLine())
      .takeWhile(_ != null)
      .toList
  }
// reader is closed when the block exits, regardless of success or failure

// But nothing prevents this mistake (no linear types):
var leakedReader: BufferedReader = null.asInstanceOf[BufferedReader]
Using(BufferedReader(FileReader("data.txt"))) { reader =>
  leakedReader = reader   // aliased — escapes the scope!
}
// leakedReader is now closed but still accessible — potential use-after-close
```

## Example B -- Experimental capture checking (preview)

```scala
// Requires -language:experimental.captureChecking

import language.experimental.captureChecking

class FileSystem:
  def read(path: String): String = ???
  def write(path: String, data: String): Unit = ???

def process(fs: FileSystem^): String^{fs} =
  fs.read("input.txt")

// The type String^{fs} tracks that the result captures the fs capability.
// Returning the result beyond fs's scope is a compile error.
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Without linear types, Scala relies on encapsulation, smart constructors, and runtime checks to prevent invalid resource states.
- [-> UC-10](../usecases/UC10-encapsulation.md) -- Resource safety is achieved through encapsulation patterns (Using, loan pattern) rather than type-level linearity.
- [-> UC-13](../usecases/UC13-state-machines.md) -- State machines in Scala use sealed traits and runtime state fields rather than move-based state transitions.

## Source anchors

- [Scala 3 Reference -- Capture Checking](https://docs.scala-lang.org/scala3/reference/experimental/cc.html)
- [scala.util.Using](https://scala-lang.org/api/3.x/scala/util/Using$.html)
- [SIP-51 -- Capture Checking](https://docs.scala-lang.org/sips/capture-checking.html)
- Odersky et al., "Capturing Types" (2023) -- theoretical foundation for capture checking
