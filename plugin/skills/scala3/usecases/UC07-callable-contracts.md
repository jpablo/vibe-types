# Callable Contracts

## The Constraint

Express contracts on callable values — function types, SAM conversions, by-name parameters, and eta-expansion — so the compiler verifies arity, parameter types, and evaluation strategy at every call site.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Function types | First-class `FunctionN` / `ContextFunctionN` types | [-> T22](T22-callable-typing.md)(../catalog/T22-callable-typing.md) |
| SAM types | Single-abstract-method traits usable as function literals | [-> T22](T22-callable-typing.md)(../catalog/T22-callable-typing.md) |
| Context functions | Functions with implicit parameters baked into the type | [-> T42](T42-context-functions.md)(../catalog/T42-context-functions.md) |
| By-name parameters | Delay evaluation; callee controls when (and whether) the argument is computed | [-> T22](T22-callable-typing.md)(../catalog/T22-callable-typing.md) |

## Patterns

### 1 — First-class function types

Functions are values with a precise type. The compiler checks arity and parameter types.

```scala
val add: (Int, Int) => Int = (a, b) => a + b
val greet: String => String = name => s"Hello, $name"

def applyTwice[A](f: A => A, x: A): A = f(f(x))
applyTwice(_ + 1, 0)   // 2
applyTwice(greet, "world")  // "Hello, Hello, world"
```

### 2 — SAM (Single Abstract Method) conversion

Any trait or abstract class with exactly one abstract method can be used as a function literal target.

```scala
trait Comparator[A]:
  def compare(a: A, b: A): Int

def sort[A](xs: List[A], cmp: Comparator[A]): List[A] =
  xs.sortWith((a, b) => cmp.compare(a, b) < 0)

// SAM conversion: a lambda fills in the single abstract method
val byLength: Comparator[String] = (a, b) => a.length - b.length

sort(List("hello", "hi", "hey"), byLength)
```

### 3 — Eta-expansion: methods as functions

Scala 3 automatically converts methods to function values where a function type is expected (no trailing `_` needed as in Scala 2).

```scala
def double(x: Int): Int = x * 2

val xs = List(1, 2, 3)
xs.map(double)       // List(2, 4, 6) — automatic eta-expansion

// Also works with overloaded methods when the expected type is unambiguous:
def format(n: Int): String = n.toString
def format(s: String): String = s.toUpperCase

val ints: List[Int] = List(1, 2)
ints.map(format)     // compiler picks format(Int) based on expected type
```

### 4 — By-name parameters for lazy evaluation

A by-name parameter (`=> T`) delays evaluation until the callee accesses it. Useful for logging, assertions, and short-circuit combinators.

```scala
def unless(cond: Boolean)(body: => Unit): Unit =
  if !cond then body

var count = 0
unless(true) { count += 1 }   // body never evaluated
assert(count == 0)

// By-name enables infinite structures:
def repeat[A](a: => A): LazyList[A] = a #:: repeat(a)
```

### 5 — Context functions for implicit-carrying callables

A context function `T ?=> U` threads a `given` value automatically, turning capability propagation into a first-class type.

```scala
import scala.concurrent.ExecutionContext

type Executable[A] = ExecutionContext ?=> A

def runOnPool[A](f: Executable[A]): A =
  given ec: ExecutionContext = ExecutionContext.global
  f   // ExecutionContext is supplied automatically

val task: Executable[String] = summon[ExecutionContext].toString
runOnPool(task)
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Function types | `FunctionN` up to `Function22` | Same, plus `ContextFunctionN` for implicit parameters |
| SAM conversion | Added in 2.12 with `-Xexperimental`, then default | Always on; works with traits and abstract classes |
| Eta-expansion | Required trailing `_` for methods with no argument list | Automatic — the `_` is no longer needed |
| By-name parameters | `=> T` — same semantics | Same semantics |
| Context functions | Not available; required implicit parameter lists on each method | `T ?=> U` — first-class; composable; no boilerplate |

## When to Use Which Feature

**Use plain function types** (`A => B`) for callbacks, transformations, and any higher-order API. They are the bread and butter of functional Scala.

**Use SAM conversion** when interoperating with Java APIs or when a trait carries semantic meaning beyond a bare function (e.g., `Comparator`, `Runnable`).

**Use by-name parameters** for control abstractions — `unless`, `attempt`, `logIf` — where the argument should not be evaluated eagerly.

**Use context functions** when you want to propagate capabilities (execution contexts, loggers, transaction handles) through a chain of calls without repeating `using` at every step.
