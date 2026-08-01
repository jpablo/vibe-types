# Given Instances, Using Clauses, and Given Imports

> **Since:** Scala 3.0 | **Latest changes:** Scala 3.6 (new given syntax with `[T] => ...`)

## What it is

Givens, using clauses, and given imports form the core of Scala 3's redesigned contextual abstraction system, replacing Scala 2's `implicit` keyword with three distinct, purpose-specific mechanisms. A **given instance** (`given`) defines a canonical value of a type that the compiler can supply automatically. A **using clause** (`using`) declares a parameter that the compiler fills in from available givens. A **given import** (`import A.given`) controls which given instances are brought into scope, separated from regular imports. Together, they provide a principled framework for type-class-based programming, dependency injection, and capability passing.

## What constraint it lets you express

**Givens and using clauses let you require compile-time evidence that a type satisfies a constraint, and have the compiler supply that evidence automatically.** This is the foundation of type-class dispatch in Scala 3: you declare what capabilities a type must have (via using clauses), define how specific types satisfy those capabilities (via given instances), and control which evidence is visible (via given imports).

## Minimal snippet

```scala
// Define a type class
trait Ord[T]:
  def compare(x: T, y: T): Int

// Provide evidence for Int
given intOrd: Ord[Int]:
  def compare(x: Int, y: Int) =
    if x < y then -1 else if x > y then +1 else 0

// Conditional evidence: List[T] is Ord if T is Ord
given listOrd: [T: Ord] => Ord[List[T]]:
  def compare(xs: List[T], ys: List[T]): Int = (xs, ys) match
    case (Nil, Nil) => 0
    case (Nil, _)   => -1
    case (_, Nil)    => +1
    case (x :: xs1, y :: ys1) =>
      val fst = summon[Ord[T]].compare(x, y)
      if fst != 0 then fst else compare(xs1, ys1)

// Require evidence via a using clause
def max[T](x: T, y: T)(using ord: Ord[T]): T =
  if ord.compare(x, y) < 0 then y else x

// Compiler supplies evidence automatically
val m = max(2, 3)  // intOrd supplied by the compiler

// Given imports: selective visibility
object Instances:
  given intOrd: Ordering[Int] = Ordering.Int
  given ec: concurrent.ExecutionContext = ???

import Instances.{given Ordering[?]}  // imports intOrd only
```

## Interaction with other features

- **Context bounds.** A context bound `[T: Ord]` is syntactic sugar for a `using Ord[T]` parameter. Named context bounds (`[T: Ord as ord]`, Scala 3.6+) give the witness a name. [-> UC-06](../usecases/UC13-state-machines.md)
- **Context functions.** Context function types `T ?=> U` abstract over the passing of using parameters, making givens available inside lambda bodies. [-> UC-06](../usecases/UC13-state-machines.md)
- **Union/intersection types.** A given can require combined evidence from several type classes at once via a multi-parameter context bound: `given [T: {Ord, Show}] => Pretty[T] = ...` (Scala 3.6+), or the older repeated form `[T: Ord : Show]`. Writing `[T: Ord & Show]` is a kind error -- `Ord & Show` intersects two *type constructors*, and a context bound needs a type constructor applied to `T`. [-> UC-01](../usecases/UC01-invalid-states.md)
- **Match types.** Given instances can use match types in their result type for conditional type-class derivation. [-> UC-03](../usecases/UC10-encapsulation.md)
- **Type lambdas.** When a type class expects `F[_]` and you have `Either[E, A]`, a type lambda `[A] =>> Either[E, A]` adapts the shape for the given definition. [-> UC-02](../usecases/UC02-domain-modeling.md)
- **Anonymous givens.** Givens can be anonymous; the compiler synthesizes a name based on the type. Publicly available libraries should prefer named instances for binary compatibility.
- **Alias givens.** `given global: ExecutionContext = ForkJoinPool()` defines a given as a lazy, thread-safe value equal to an expression.
- **Initialization.** Unconditional givens without parameters are initialized on demand (lazy). Conditional givens (with type or term parameters) create a fresh instance per use.
- **Summon.** `summon[T]` retrieves the given instance of type `T` in scope. It is defined as `def summon[T](using x: T): x.type = x`.
- **By-type imports.** `import A.given TC` imports only givens conforming to type `TC`, providing fine-grained control.

## Gotchas and limitations

1. **Wildcard `*` does not import givens.** This is intentional: `import A.*` imports everything _except_ givens. You must use `import A.given` or `import A.{given, *}` to include them. Extension methods are *not* affected -- a wildcard import does bring them into scope.
2. **Anonymous given name collisions.** The compiler-synthesized names for anonymous givens can collide when types are "too similar." Use named givens in public APIs to avoid this.
3. **Ambiguity.** If multiple givens of the same type are in scope, the compiler reports an ambiguity error. Specificity rules (more specific given wins) resolve some cases, but complex hierarchies may need explicit `using` arguments.
4. **Given search scope.** The compiler searches for givens in the current scope, imports, and the companion objects of the types involved (the "implicit scope"). Understanding this scope is essential for debugging "no given instance found" errors.
5. **Migration from implicits.** `import A.given` brings old-style Scala 2 `implicit` definitions into scope -- this holds in every Scala 3 version, not just 3.0. A plain `import A.*` also still imports them, and as of 3.8.4 it does so with *no* warning, even under `-Werror`. Deprecating the `*` path is planned, not yet active, so do not rely on the compiler to flag it during migration.
6. **Binary compatibility.** Changing an anonymous given to a named one (or vice versa) is a binary-incompatible change. Libraries should use named givens from the start.

## Recommended libraries

| Library | Role | Link |
|---|---|---|
| **cats** | Standard type classes (Monad, Functor, Applicative, Traverse, etc.) with lawful instances | [typelevel.org/cats](https://typelevel.org/cats/) |
| **shapeless-3** | Generic programming over product/sum shapes; type-class derivation for arbitrary arities | [github.com/typelevel/shapeless-3](https://github.com/typelevel/shapeless-3) |
| **kittens** | Automatic derivation of cats type-class instances (Functor, Show, Eq, etc.) for case classes and enums | [github.com/typelevel/kittens](https://github.com/typelevel/kittens) |

## Coming from Lean

Scala's `given`/`using` corresponds directly to Lean's `class`/`instance`. Where Lean writes `class Ord (α : Type) where le : α → α → Bool` and `instance : Ord Nat where le := Nat.ble`, Scala writes `trait Ord[A]: def le(a: A, b: A): Boolean` and `given Ord[Int] with def le(a: Int, b: Int) = a <= b`. Both use automatic instance resolution. Lean's type classes additionally serve as the mechanism for dependent type dispatch — a role filled by match types and inline in Scala.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) Given instances can be defined for intersection types, combining multiple type-class constraints.
- [-> UC-02](../usecases/UC02-domain-modeling.md) Type lambdas adapt multi-parameter types for use in given definitions targeting unary type classes.
- [-> UC-03](../usecases/UC10-encapsulation.md) Match types enable conditional given derivation based on the scrutinee type.
- [-> UC-04](../usecases/UC11-effect-tracking.md) Polymorphic function types can be provided as given instances for polymorphic capability values.
- [-> UC-06](../usecases/UC13-state-machines.md) Context bounds and context functions build directly on top of givens and using clauses.
