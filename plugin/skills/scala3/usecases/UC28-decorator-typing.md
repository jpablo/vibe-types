# Decorator Typing (via Higher-Order Functions)

## The Constraint

Wrap, augment, or transform function behaviour — logging, timing, retries, authorisation — while preserving type safety. Scala 3 has no decorator syntax, but higher-order functions and context function composition achieve the same goal with full type checking.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Function types | Higher-order functions wrap and delegate to inner functions | [-> T22](T22-callable-typing.md)(../catalog/T22-callable-typing.md) |
| Context functions | Thread implicit capabilities through decorator chains | [-> T42](T42-context-functions.md)(../catalog/T42-context-functions.md) |
| Extension methods | Add decorator-like methods to existing function types | [-> T19](T19-extension-methods.md)(../catalog/T19-extension-methods.md) |
| Opaque types | Tag decorated functions to distinguish them from raw ones | [-> T03](T03-newtypes-opaque.md)(../catalog/T03-newtypes-opaque.md) |

## Patterns

### 1 — Simple function wrapper for logging

Wrap any function `A => B` with before/after logging. The types flow through.

```scala
def withLogging[A, B](name: String)(f: A => B): A => B =
  a =>
    println(s"[$name] called with $a")
    val result = f(a)
    println(s"[$name] returned $result")
    result

val parse: String => Int = withLogging("parse")(_.toInt)
parse("42")
// [parse] called with 42
// [parse] returned 42
```

### 2 — Composable decorators via andThen

Chain decorators using function composition. Each layer preserves the type signature.

```scala
type Middleware[A, B] = (A => B) => (A => B)

def timed[A, B]: Middleware[A, B] = f => a =>
  val start = System.nanoTime()
  val result = f(a)
  println(s"took ${(System.nanoTime() - start) / 1e6}ms")
  result

def validated[B](f: String => B): String => B = input =>
  require(input.nonEmpty, "input must not be empty")
  f(input)

// Compose decorators:
val process: String => Int =
  (timed[String, Int] compose (validated[Int] _))(_.toInt)

process("42")    // validated, then timed, then parsed
```

### 3 — Context function decorators for capability injection

Use context functions to inject capabilities (transactions, loggers) into decorated blocks.

```scala
trait Logger:
  def info(msg: String): Unit

type Logged[A] = Logger ?=> A

def withLogger[A](f: Logged[A]): A =
  given Logger with
    def info(msg: String): Unit = println(s"[LOG] $msg")
  f

def fetchData: Logged[String] =
  summon[Logger].info("fetching data")
  "result"

val result = withLogger {
  val data = fetchData        // Logger is available implicitly
  summon[Logger].info(s"got: $data")
  data
}
```

### 4 — Retry decorator with type-safe error handling

Wrap effectful operations with retry logic, preserving the return type.

```scala
def withRetry[A](maxAttempts: Int)(f: => A): A =
  var attempts = 0
  var last: Throwable = null
  while attempts < maxAttempts do
    try return f
    catch case e: Exception =>
      last = e
      attempts += 1
      println(s"attempt $attempts failed: ${e.getMessage}")
  throw last

// Type-safe: the decorator returns the same type as the wrapped function
val result: Int = withRetry(3) {
  if math.random() < 0.7 then throw Exception("flaky")
  42
}
```

### 5 — Extension methods as decorator syntax

Add decorator-like methods directly to function types for a fluent API.

```scala
extension [A, B](f: A => B)
  def logged(name: String): A => B = a =>
    println(s"[$name] input: $a")
    val r = f(a)
    println(s"[$name] output: $r")
    r

  def memoized: A => B =
    val cache = scala.collection.mutable.Map.empty[A, B]
    a => cache.getOrElseUpdate(a, f(a))

val fastFib: Int => BigInt =
  ((n: Int) =>
    if n <= 1 then BigInt(n)
    else fastFib(n - 1) + fastFib(n - 2)
  ).memoized.logged("fib")
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Higher-order wrappers | Same pattern; same expressiveness | Same; type inference often better |
| Context function decorators | Not available; required implicit parameter lists at every level | `T ?=> U` — compose decorators that thread capabilities |
| Extension methods on functions | `implicit class` wrappers — allocation overhead | `extension` — zero allocation, cleaner syntax |
| Capability injection | Cake pattern or Reader monad | Context functions provide direct language support |

## When to Use Which Feature

**Use simple wrappers** (`f => a => ...`) for straightforward cross-cutting concerns — logging, timing, validation. They are the most readable and compose with `andThen`/`compose`.

**Use context function decorators** when the decorator injects a capability (logger, transaction, auth context) that downstream code needs implicitly.

**Use extension methods on function types** for a fluent decorator API — `.logged`, `.memoized`, `.retried(3)`. This reads naturally and keeps the pipeline visible.

**Prefer explicit composition over magic.** Unlike annotation-based decorators in other languages, Scala's approach keeps the call chain visible in the source code — each layer is a function you can step into, test, and reason about.
