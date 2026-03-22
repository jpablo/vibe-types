# Dependent Function Types and Polymorphic Function Types

> **Since:** Scala 3.0

## What it is

Dependent function types and polymorphic function types are two new function type forms in Scala 3 that promote capabilities previously available only in methods to first-class function values. A **dependent function type** `(x: A) => x.B` is a function type whose result type depends on the _value_ of its argument (via path-dependent types). A **polymorphic function type** `[A] => List[A] => List[A]` is a function type that is universally quantified over a type parameter. In Scala 2, dependent methods and polymorphic methods existed but could not be turned into values; these two features close that gap.

## What constraint it lets you express

**Dependent function types let you express "the return type is determined by the argument value" as a first-class value that can be stored, passed, and returned.** **Polymorphic function types let you express "this function works for all types" as a first-class value, enabling universal quantification in the value world.** Together, they allow callbacks, strategies, and higher-order functions that preserve precise type relationships.

## Minimal snippet

```scala
// --- Dependent function types ---
trait Entry:
  type Key
  val key: Key

def extractKey(e: Entry): e.Key = e.key  // dependent method

// Now as a first-class function value:
val extractor: (e: Entry) => e.Key = extractKey
//             ^^^^^^^^^^^^^^^^^^^^
//             dependent function type

// --- Polymorphic function types ---
def foo[A](xs: List[A]): List[A] = xs.reverse  // polymorphic method

// Now as a first-class function value:
val bar: [A] => List[A] => List[A] =
  [A] => (xs: List[A]) => xs.reverse
//^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
// polymorphic function type
```

## Interaction with other features

- **Match types.** Dependent methods commonly use match types as their return type, and the resulting method can be eta-expanded into a dependent function value. [-> UC-03](../usecases/UC10-encapsulation.md)
- **Given instances / using clauses.** Polymorphic function values can be required as given instances, allowing type-class-like dispatch through function values rather than trait implementations. [-> UC-05](../usecases/UC12-compile-time.md)
- **Context functions.** Polymorphic function types compose with context function types. You can write `[A] => Ord[A] ?=> (A, A) => A` to express a polymorphic, context-dependent function. [-> UC-06](../usecases/UC13-state-machines.md)
- **Type lambdas.** Type lambdas are applied in type expressions (`F[Int]`), while polymorphic functions are applied in term expressions (`bar[Int]`). They are complementary: one operates at the type level, the other at the value level. [-> UC-02](../usecases/UC02-domain-modeling.md)
- **Higher-order functions.** Polymorphic function types enable higher-order functions that demand polymorphic callbacks. For example, a function `mapSubexpressions` can require its callback to work for any subexpression type, not just a fixed one.
- **Representation.** Dependent function types are syntactic sugar for refined `FunctionN` traits with a more precise `apply` method. Polymorphic function types use a similar encoding with type parameters on `apply`.

## Gotchas and limitations

1. **Path-dependent scope.** In a dependent function type `(x: A) => x.B`, the name `x` is only in scope in the result type. You cannot reference it elsewhere or chain multiple dependent arguments easily.
2. **No dependent function literals directly.** You write a dependent function by eta-expanding a dependent method or via an explicit lambda. The compiler needs a dependent method as the bridge.
3. **Polymorphic function values are verbose.** Unlike `val f = (x: Int) => x + 1`, polymorphic function values require repeating the type parameter: `[A] => (x: A) => x`. There is no inference shorthand.
4. **No polymorphic currying.** You cannot partially apply a polymorphic function's type parameter and get back a monomorphic function value in a single step; you must apply the type argument explicitly.
5. **Cannot combine type parameters and dependent parameters in one function type.** You cannot write `[A] => (x: A) => x.T` in a single type; you would need to nest or use a method.
6. **Erasure.** Type parameters in polymorphic function types are erased at runtime. The polymorphism is purely a compile-time guarantee.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) Intersection types can be returned from dependent functions to combine capabilities based on argument values.
- [-> UC-02](../usecases/UC02-domain-modeling.md) Type lambdas are the type-level counterpart to polymorphic function types.
- [-> UC-03](../usecases/UC10-encapsulation.md) Match types serve as the return type of dependent methods/functions for type-level computation.
- [-> UC-05](../usecases/UC12-compile-time.md) Given instances of polymorphic function types encode type-class-like evidence as values.
- [-> UC-06](../usecases/UC13-state-machines.md) Context functions compose with polymorphic function types for polymorphic + contextual abstractions.
