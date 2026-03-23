# Effect Tracking

## The Constraint

Track side effects — IO, exceptions, mutation, capabilities — at the type level. A function's signature declares what it can do; the compiler rejects code that performs undeclared effects.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Capture checking | Track which capabilities a value captures; experimental effect system | [-> T12](T12-effect-tracking.md)(../catalog/T12-effect-tracking.md) |
| Context functions | Thread implicit capabilities through call chains | [-> T42](T42-context-functions.md)(../catalog/T42-context-functions.md) |
| Givens / Using | Provide and require capabilities via implicit resolution | [-> T05](T05-type-classes.md)(../catalog/T05-type-classes.md) |
| Opaque types | Wrap effect evidence at zero cost | [-> T03](T03-newtypes-opaque.md)(../catalog/T03-newtypes-opaque.md) |
| CanThrow | Checked exceptions via capabilities | [-> T12](T12-effect-tracking.md)(../catalog/T12-effect-tracking.md) |

## Patterns

### 1 — CanThrow for checked exceptions

Scala 3's `CanThrow` mechanism turns exceptions into capabilities. A function that throws must declare the capability; callers must provide it.

```scala
import language.experimental.saferExceptions

class ValidationError(msg: String) extends Exception(msg)
class IOError(msg: String) extends Exception(msg)

// Declares that it may throw ValidationError
def parseAge(s: String)(using CanThrow[ValidationError]): Int =
  val n = s.toIntOption.getOrElse:
    throw ValidationError(s"Not a number: $s")
  if n < 0 then throw ValidationError("Age cannot be negative")
  n

// Declares both possible exceptions
def readAndParseAge(path: String)(
    using CanThrow[IOError], CanThrow[ValidationError]
): Int =
  val content = // ... read file, may throw IOError
    "25"
  parseAge(content)

// At the boundary — convert to Either
val result: Either[ValidationError, Int] =
  try Right(parseAge("42"))
  catch case e: ValidationError => Left(e)
  // CanThrow[ValidationError] is provided by the `try`
```

### 2 — Capability-based IO tracking

Model IO as an explicit capability. Functions that perform IO require the capability; pure functions do not mention it.

```scala
trait IO:
  def println(msg: String): Unit
  def readLine(): String

// Pure — no IO capability required
def validate(name: String): Either[String, String] =
  if name.nonEmpty then Right(name) else Left("empty")

// Effectful — requires IO
def greet(using io: IO): Unit =
  io.println("What is your name?")
  val name = io.readLine()
  validate(name) match
    case Right(n) => io.println(s"Hello, $n!")
    case Left(e)  => io.println(s"Error: $e")

// Provide the capability at the program edge
@main def run() =
  given IO with
    def println(msg: String) = scala.Predef.println(msg)
    def readLine() = scala.io.StdIn.readLine()

  greet  // IO capability resolved here
```

### 3 — Context functions encoding Reader/Writer effects

Context functions let you thread a dependency through a computation without passing it explicitly at every call site.

```scala
type Config = Map[String, String]
type Configured[A] = Config ?=> A

def dbUrl: Configured[String] =
  summon[Config].getOrElse("db.url", "jdbc:h2:mem:")

def poolSize: Configured[Int] =
  summon[Config].getOrElse("db.pool", "10").toInt

def connectInfo: Configured[String] =
  s"${dbUrl} (pool=${poolSize})"

// Provide the context at the boundary
val info = connectInfo(using Map("db.url" -> "jdbc:postgresql://localhost/mydb"))
// "jdbc:postgresql://localhost/mydb (pool=10)"
```

### 4 — Tagless final with givens

Encode effects as type constructors and provide interpreters via `given`. The business logic is polymorphic in the effect type.

```scala
trait Store[F[_]]:
  def get(key: String): F[Option[String]]
  def put(key: String, value: String): F[Unit]

trait Logger[F[_]]:
  def info(msg: String): F[Unit]

def program[F[_]](using store: Store[F], logger: Logger[F], m: cats.Monad[F]): F[Unit] =
  import cats.syntax.flatMap.*
  import cats.syntax.functor.*
  for
    _ <- logger.info("Starting")
    v <- store.get("counter")
    _ <- store.put("counter", v.fold("1")(n => (n.toInt + 1).toString))
    _ <- logger.info("Done")
  yield ()

// Wire up interpreters at the edge:
// given Store[IO]   = ...
// given Logger[IO]  = ...
// program[IO].unsafeRunSync()
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Checked exceptions | Not available — all exceptions unchecked; third-party `Either`-based patterns | `CanThrow` capability — exceptions tracked in types; `try` provides the capability |
| Capability passing | Implicit parameters (`implicit io: IO`) — same idea, more ceremony | `using` / `given` + context functions — lighter syntax, context function types `IO ?=> A` |
| Reader/Writer effects | Monad transformers or `Reader[Config, A]` — runtime overhead, complex stacks | Context functions (`Config ?=> A`) — compiler-desugared, no wrapper types at runtime |
| Tagless final | Worked well with `implicit` — unchanged in principle | `given` / `using` syntax is lighter; `transparent inline given` can eliminate abstraction cost |
| Capture checking | Not available | Experimental in Scala 3 — compiler tracks captured references in types |

## When to Use Which Feature

**CanThrow** is the right starting point for tracking exceptions without abandoning `throw`/`catch`. It adds type safety incrementally — you do not have to rewrite your error handling to `Either` everywhere. Use it when integrating with Java libraries that throw.

**Capability traits** (like the `IO` pattern above) are appropriate when you want to mark effectful code explicitly and test it by substituting implementations. They are simple, require no framework, and work with any effect type.

**Context functions** replace the Reader monad for dependency injection. Use them when a value must be available "in scope" throughout a call chain but you do not want to pass it manually. They compose naturally and have no runtime wrapper.

**Tagless final** remains the tool for abstracting over the effect system itself — when the same business logic must run against different runtimes (e.g., `IO`, `Future`, `Id` for testing). It requires a monad library.

**Capture checking** (experimental) is the most rigorous approach: the compiler tracks *which* capabilities a closure captures, preventing capability leaks. Consider it for safety-critical code once the feature stabilizes.
