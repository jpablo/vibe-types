# Callable Types & Overloading

> **Since:** Scala 3.0

## What it is

Scala 3 has a rich system of callable types that goes well beyond simple function literals. **Function types** (`A => B`) are sugar for instances of `scala.FunctionN` traits. **SAM (Single Abstract Method) types** allow any trait or abstract class with exactly one abstract method to be instantiated with a lambda. **Eta-expansion** automatically converts method references to function values. **Method overloading** permits multiple methods with the same name but different parameter types. **By-name parameters** (`=> T`) delay evaluation of an argument until it is used. **Context function types** (`A ?=> B`) propagate given instances through lambda bodies. Together, these features provide a flexible, type-safe callable abstraction layer.

## What constraint it lets you express

**Callable types let you express precisely what a computation requires (input types, implicit context, evaluation strategy) and what it produces (output type), and the compiler enforces that every call site matches the declared signature.** Function types encode arity and parameter/return types. SAM types let you require a specific interface while accepting lambda syntax. By-name parameters enforce lazy evaluation at the type level. Context functions thread capabilities without explicit passing.

## Minimal snippet

**Function types:**

```scala
val add: (Int, Int) => Int = (a, b) => a + b
val transform: String => Int = _.length

// Function types are traits: Function2[Int, Int, Int]
// with variance: Function2[-A, -B, +R]
```

**SAM (Single Abstract Method) conversion:**

```scala
trait Comparator[A]:
  def compare(x: A, y: A): Int

// Lambda auto-converts to SAM type:
val byLength: Comparator[String] = (x, y) => x.length - y.length
```

**Eta-expansion (automatic method-to-function conversion):**

```scala
def double(x: Int): Int = x * 2

val f: Int => Int = double   // eta-expanded automatically
List(1, 2, 3).map(double)   // also eta-expanded
```

**Method overloading:**

```scala
def show(x: Int): String = x.toString
def show(x: String): String = s"'$x'"
def show(x: Double, precision: Int): String = s"%.${precision}f".format(x)

show(42)        // "42"
show("hello")   // "'hello'"
show(3.14, 2)   // "3.14"
```

**By-name parameters:**

```scala
def logging[A](msg: => String)(body: => A): A =
  println(s"START: $msg")
  val result = body      // evaluated here, not at call site
  println(s"END: $msg")
  result

logging("heavy computation") {
  Thread.sleep(1000)
  42
}
```

**Context function types:**

```scala
import scala.concurrent.ExecutionContext

type Executable[A] = ExecutionContext ?=> A

val task: Executable[Int] =
  summon[ExecutionContext]  // available via ?=>
  42

given ExecutionContext = ExecutionContext.global
val result: Int = task   // context supplied automatically
```

## Interaction with other features

| Feature | How it composes |
|---|---|
| **Generics & bounds** [-> catalog/T04](T04-generics-bounds.md) | Function types compose with generics: `def map[A, B](f: A => B): List[B]`. Polymorphic function types `[A] => A => A` allow universally quantified function values. |
| **Context functions** [-> catalog/T42](T42-context-functions.md) | Context function types `A ?=> B` are a distinct function kind: the compiler supplies the argument from given instances, enabling capability-passing patterns. |
| **Variance** [-> catalog/T08](T08-variance-subtyping.md) | `FunctionN` is contravariant in parameter types and covariant in the return type: `Function1[-A, +B]`. This means a function `Animal => Cat` is a subtype of `Cat => Animal`. |
| **Dependent function types** [-> catalog/T09](T09-dependent-types.md) | `(x: A) => x.T` allows the return type to depend on the argument value, enabling type-safe extractors and interpreters as first-class values. |
| **Given instances** [-> catalog/T05](T05-type-classes.md) | SAM conversion interacts with givens: if a given instance is defined for a SAM type, a lambda literal satisfies the given requirement. |
| **Extension methods** [-> catalog/T19](T19-extension-methods.md) | Extension methods on function types allow adding combinators: `extension [A, B](f: A => B) def andThen[C](g: B => C): A => C`. |

## Gotchas and limitations

1. **SAM conversion requires exactly one abstract method.** If a trait has two abstract methods, lambda syntax does not apply. Default methods and concrete methods do not count against the limit.
2. **Eta-expansion and overloading.** When a method is overloaded, eta-expansion requires an expected type to disambiguate: `val f: Int => Int = show` fails if `show` is overloaded. Provide a type ascription or use `show(_: Int)`.
3. **By-name parameters are not function values.** `=> T` is not the same as `() => T`. You cannot store a by-name parameter in a `val` (it is evaluated immediately). To defer, explicitly wrap: `val thunk: () => T = () => param`.
4. **Overloading resolution priority.** Scala's overloading resolution uses specificity rules that can be surprising. A method taking `String` is more specific than one taking `Any`, but when generics are involved, ambiguities can arise. The compiler reports an "ambiguous overloaded method" error.
5. **Function arity limits.** `FunctionN` is defined for `N` up to 22 in the standard library. Scala 3 auto-generates beyond 22 using tupled representation, but some libraries may not handle high-arity functions.
6. **SAM types and serialization.** Lambda-created SAM instances may not be serializable. If the SAM trait extends `Serializable`, the lambda must capture only serializable values.
7. **No overloading on return type alone.** Scala does not support overloading methods that differ only in their return type. The parameter lists must differ.

## Beginner mental model

Think of Scala's callable types as a spectrum of **precision**:
- `A => B` is the simplest: "give me an A, get a B."
- `=> T` (by-name) says: "I will evaluate this expression only when I need it."
- `A ?=> B` (context function) says: "give me an A implicitly through the given system."
- SAM types say: "I accept a lambda, but I am a full interface with a name and possible other concrete members."

The compiler converts between these forms automatically where safe (eta-expansion, SAM conversion), and rejects conversions where types do not align.

## Common type-checker errors

```
-- [E134] Type Error ---
  val f: Int => String = show
                         ^^^^
  Ambiguous overload. Both method show(x: Int): String
  and method show(x: String): String match expected type Int => String

  Fix: disambiguate with a lambda: val f: Int => String = show(_: Int)
```

```
-- [E007] Type Mismatch Error ---
  def twice(f: => Int): Int = f + f
  twice { () => 42 }
         ^^^^^^^^^
  Found:    () => Int
  Required: Int

  Fix: by-name parameters are not Function0. Remove the () =>:
    twice { 42 }
```

```
-- Error ---
  trait Handler[A]:
    def handle(a: A): Unit
    def reset(): Unit

  val h: Handler[String] = s => println(s)
                           ^^^^^^^^^^^^^^^
  Handler is not a single abstract method type (has 2 abstract methods)

  Fix: provide a full implementation with `new Handler[String] { ... }`
  or add a default implementation for reset().
```

```
-- [E081] Type Error ---
  def process(f: String => Int) = f("hello")
  process(_.length + _.toInt)
                     ^
  Missing parameter type for expanded function.
  Wrong number of parameters: expected 1, found 2.

  Fix: the underscore syntax creates one parameter per _. Use an
  explicit lambda: process(s => s.length + s.toInt)
```

## Use-case cross-references

- [-> UC-02](../usecases/UC02-domain-modeling.md) SAM types for domain-specific callbacks and event handlers
- [-> UC-06](../usecases/UC13-state-machines.md) Context functions for threading capabilities through state machine transitions
- [-> UC-09](../usecases/UC09-builder-config.md) By-name parameters for lazy configuration and builder patterns
- [-> UC-11](../usecases/UC11-effect-tracking.md) Function types in effect-tracking systems that thread capabilities

## Source anchors

- [Scala 3 Reference: Function Types](https://docs.scala-lang.org/scala3/reference/new-types/type-lambdas-spec.html)
- [Scala 3 Reference: Context Functions](https://docs.scala-lang.org/scala3/reference/contextual/context-functions.html)
- [Scala 3 Reference: SAM Conversions](https://docs.scala-lang.org/scala3/reference/changed-features/eta-expansion-spec.html)
- [Scala 3 Reference: Automatic Eta Expansion](https://docs.scala-lang.org/scala3/reference/changed-features/eta-expansion.html)
