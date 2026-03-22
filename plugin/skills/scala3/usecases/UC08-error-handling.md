# Error Handling

## The Constraint

Handle errors in a type-safe way so the compiler tracks which errors can occur, ensures they are handled, and prevents silent swallowing. Choose between checked exceptions, error ADTs, union-type channels, and capability-based tracking.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| CanThrow capabilities | Lightweight checked exceptions via capability parameters | [-> catalog/21](../catalog/T12-effect-tracking.md) |
| Enums / ADTs | Closed error hierarchies with exhaustive matching | [-> catalog/11](../catalog/T01-algebraic-data-types.md) |
| Union types | Ad-hoc error channels without a common supertype | [-> catalog/01](../catalog/T02-union-intersection.md) |
| Context functions | Propagate error-handling capabilities implicitly through call chains | [-> catalog/06](../catalog/T42-context-functions.md) |
| Capture checking | Track which capabilities a function captures — including error effects | [-> catalog/21](../catalog/T12-effect-tracking.md) |

## Patterns

### 1 — CanThrow for lightweight checked exceptions

Scala 3 experimental feature: methods declare thrown exceptions as capability requirements. Callers must provide the capability or handle the exception.

```scala
import language.experimental.saferExceptions

class ValidationError(msg: String) extends Exception(msg)
class NetworkError(msg: String)    extends Exception(msg)

def validate(input: String)(using CanThrow[ValidationError]): String =
  if input.isEmpty then throw ValidationError("empty input")
  else input.trim

def fetch(url: String)(using CanThrow[NetworkError]): String =
  if !url.startsWith("http") then throw NetworkError(s"bad url: $url")
  else s"content of $url"

def process(url: String)(using CanThrow[ValidationError], CanThrow[NetworkError]): String =
  val clean = validate(url)
  fetch(clean)

// Caller must handle both:
@main def run() =
  try
    val result = process("http://example.com")
    println(result)
  catch
    case e: ValidationError => println(s"Validation: ${e.getMessage}")
    case e: NetworkError    => println(s"Network: ${e.getMessage}")
  // Missing a catch branch does not cause a compile error,
  // but calling process without a surrounding try does.
```

### 2 — Error ADT with exhaustive matching

Model errors as an `enum`. The compiler forces handling of every variant.

```scala
enum AppError:
  case NotFound(id: String)
  case Unauthorized(user: String)
  case RateLimited(retryAfter: Int)

case class Result[+A](value: Either[AppError, A]):
  def map[B](f: A => B): Result[B] = Result(value.map(f))
  def flatMap[B](f: A => Result[B]): Result[B] = Result(value.flatMap(a => f(a).value))

def lookup(id: String): Result[String] =
  if id == "42" then Result(Right("found it"))
  else Result(Left(AppError.NotFound(id)))

def handle(r: Result[String]): String = r.value match
  case Right(v)                        => v
  case Left(AppError.NotFound(id))     => s"$id not found"
  case Left(AppError.Unauthorized(u))  => s"$u denied"
  case Left(AppError.RateLimited(sec)) => s"retry in ${sec}s"
  // removing any branch is a compile error
```

### 3 — Union type error channels

Combine unrelated error types without a common base class using union types.

```scala
case class ParseError(msg: String)
case class IoError(path: String, cause: String)
case class Timeout(ms: Long)

type Fallible[A] = A | ParseError | IoError | Timeout

def readConfig(path: String): Fallible[Map[String, String]] =
  if !path.endsWith(".conf") then ParseError(s"not a .conf file: $path")
  else if path.contains("missing") then IoError(path, "file not found")
  else Map("key" -> "value")

def useConfig(path: String): String =
  readConfig(path) match
    case m: Map[?, ?]    => s"loaded ${m.size} keys"
    case ParseError(msg) => s"parse error: $msg"
    case IoError(p, c)   => s"IO error on $p: $c"
    case Timeout(ms)     => s"timed out after ${ms}ms"
```

### 4 — Capability-based error tracking with capture checking

Track error-handling capabilities in function types so the compiler knows which effects flow through a computation.

```scala
import language.experimental.captureChecking

trait Logger:
  def log(msg: String): Unit

trait ErrorHandler:
  def handle(e: Exception): Unit

// The function type captures its dependencies:
def riskyOp(using l: Logger^, h: ErrorHandler^): String^{l, h} =
  l.log("starting risky operation")
  try
    "success"
  catch
    case e: Exception =>
      h.handle(e)
      "recovered"

// A pure function captures nothing:
def pureCompute(x: Int): Int = x * 2   // no capabilities needed
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Checked exceptions | Not available; Java checked exceptions erased by Scala's type system | `CanThrow` capabilities — opt-in checked exceptions without Java's verbosity |
| Error ADTs | `sealed trait` + `case class`; same pattern, more boilerplate | `enum` — concise, with `ordinal` and `values` for free |
| Union-typed errors | Not expressible; required `Either` nesting or `Coproduct` from Shapeless | `A \| E1 \| E2` — direct, flat, no wrapper types |
| Capability tracking | Not available; manual discipline or effect libraries (ZIO, Cats Effect) | Capture checking tracks capabilities in types; compiler-enforced |
| Exhaustiveness on errors | Worked with `sealed`, but warnings were easy to suppress | Stricter defaults; `enum` + pattern matching gives reliable exhaustiveness |

## When to Use Which Feature

**Use `CanThrow`** when you want lightweight checked exceptions without the ceremony of wrapping everything in `Either`. Best for applications where exceptions are the natural error model but you want the compiler to verify they are caught. Note: this is still experimental.

**Use error ADTs** when errors are a core part of your domain model — each variant carries meaningful data, and callers must handle every case. This is the most common and portable approach.

**Use union types** when errors come from different libraries or domains with no shared base class and you want to avoid wrapper types. Union types compose naturally: just add `| NewError` to the return type.

**Use capture checking** in systems where tracking which side effects a function may perform is as important as tracking its error modes. This is the most advanced option and is experimental.

**Combine approaches**: use ADTs for your domain errors, union types at API boundaries where multiple domains meet, and `CanThrow` for infrastructure exceptions that should not pollute domain types.
