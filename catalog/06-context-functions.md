# Context Functions (`T ?=> U`) and Context Bounds (`F : Monad`)

> **Since:** Scala 3.0 | **Latest changes:** Scala 3.6 (named context bounds with `as`, aggregate bounds `{Ord, Show}`, context bounds on type members and polymorphic functions)

## What it is

Context functions and context bounds are two closely related mechanisms in Scala 3 for abstracting over contextual dependencies. A **context function type** `T ?=> U` describes a function that takes an implicit (given) parameter of type `T` and produces a `U`; the argument is supplied automatically by the compiler from the enclosing scope. A **context bound** `[T: Ord]` is shorthand for declaring a `using` parameter of a type class applied to a type parameter. Together, they make capability requirements explicit in types while keeping call sites concise: context functions turn "requires a given `T`" into a first-class type, and context bounds turn "requires evidence of `Ord[T]`" into a lightweight annotation on type parameters.

## What constraint it lets you express

**Context functions let you abstract over contextual dependencies as types, so that "needs a `T` in scope" becomes part of the function's type signature rather than invisible plumbing.** **Context bounds let you declare "this type parameter must have an associated type-class instance" directly on the parameter, reducing boilerplate.** The combination encodes capability requirements -- from execution contexts to builder scopes to type-class evidence -- in a composable, zero-overhead way.

## Minimal snippet

```scala
// --- Context functions ---
import scala.concurrent.ExecutionContext

type Executable[T] = ExecutionContext ?=> T

def f(x: Int): Executable[Int] =
  val ec = summon[ExecutionContext]
  x + 1  // ExecutionContext is available implicitly in the body

given ec: ExecutionContext = ExecutionContext.global
val result: Int = f(2)  // ec is supplied automatically

// --- Context bounds ---
trait Ord[T]:
  def compare(x: T, y: T): Int

def maximum[T: Ord](xs: List[T]): T =
  xs.reduceLeft((a, b) =>
    if summon[Ord[T]].compare(a, b) < 0 then b else a)

// Named context bound (Scala 3.6+):
trait Monoid[A]:
  def unit: A
  extension (x: A) def combine(y: A): A

def reduce[A: Monoid as m](xs: List[A]): A =
  xs.foldLeft(m.unit)(_ `combine` _)
```

## Interaction with other features

- **Givens and using clauses.** Context bounds desugar to using clauses, and context function application relies on given instances in scope. They are the demand side; givens are the supply side. [-> UC-05](../usecases/05-compile-time-programming.md)
- **Builder pattern (context functions).** Context functions enable DSL-style builder patterns where the enclosing scope provides a mutable builder as a given. The classic example is an HTML table builder where `table { row { cell("x") } }` compiles via nested context functions that thread `Table` and `Row` instances.
- **Postconditions (context functions).** Combined with opaque type aliases and extension methods, context functions can implement zero-overhead postcondition checking: `List(1,2,3).sum.ensuring(result == 6)` where `result` is resolved from a `WrappedResult[T] ?=> Boolean` context function.
- **Polymorphic function types.** Context bounds can be used on polymorphic function types (Scala 3.6+): `[X: Ord] => (X, X) => Boolean` desugars to `[X] => (X, X) => Ord[X] ?=> Boolean`. [-> UC-04](../usecases/04-effect-tracking.md)
- **Aggregate context bounds.** Multiple bounds are written inside braces: `[X: {Ord, Show}]`. Named variants: `[X: {Ord as ord, Show as show}]`.
- **Abstract type members.** Context bounds on abstract type members (Scala 3.6+) expand to deferred givens: `type Element: Ord` becomes `type Element` plus `given Ord[Element] = deferred`.
- **Automatic wrapping.** If an expression `E` is expected to have a context function type `T ?=> U` but is not already a context function literal, the compiler rewrites it to `(x: T) ?=> E`, making `x` available as a given in `E`.
- **Union/intersection types.** Context function parameters can be intersection types to require multiple capabilities: `(Logging & Tracing) ?=> Result`. [-> UC-01](../usecases/01-preventing-invalid-states.md)

## Gotchas and limitations

1. **Context functions are not regular functions.** A `T ?=> U` is distinct from `T => U`. You cannot use a context function where a plain function is expected, or vice versa, without explicit conversion.
2. **Implicit ambiguity.** If multiple givens of the context function's parameter type are in scope, the compiler reports ambiguity. Use distinct opaque types or newtypes to avoid collisions (as demonstrated in the postconditions example).
3. **Named context bounds require Scala 3.6+.** The `as` syntax for naming the witness (`[T: Ord as ord]`) and aggregate bounds (`[T: {Ord, Show}]`) are not available before Scala 3.6. The older syntax `[T: Ord : Show]` still works but will be deprecated.
4. **Placement of generated parameters.** The using clause generated from context bounds follows specific placement rules: if the bound's name is referenced by a subsequent parameter clause, the using clause is inserted before that clause; otherwise it is appended or merged with an existing using clause.
5. **Context function overhead.** Although conceptually zero-overhead, each context function type creates a distinct `ContextFunctionN` trait instance at the type level. Deeply nested context functions can produce verbose inferred types.
6. **Debugging.** When a context function argument is not found, the error message says "no given instance of type T was found," which can be confusing if you did not realize a context function was involved. Understanding the automatic wrapping rule is key to diagnosing such errors.
7. **Deferred givens.** Context bounds on abstract type members produce `given T = deferred`, which must be implemented in concrete subclasses. Forgetting to provide the implementation results in a compile error at the subclass, not at the abstract definition.

## Use-case cross-references

- [-> UC-01](../usecases/01-preventing-invalid-states.md) Intersection types combine multiple capability requirements in a single context function parameter.
- [-> UC-02](../usecases/02-domain-modeling.md) Type lambdas adapt multi-parameter type constructors for use in context bounds.
- [-> UC-03](../usecases/03-access-encapsulation.md) Match types can serve as the result type of context-bounded methods for conditional returns.
- [-> UC-04](../usecases/04-effect-tracking.md) Polymorphic function types compose with context bounds for polymorphic, context-dependent values.
- [-> UC-05](../usecases/05-compile-time-programming.md) Givens and using clauses are the supply-side counterpart to the demand expressed by context bounds and context functions.
