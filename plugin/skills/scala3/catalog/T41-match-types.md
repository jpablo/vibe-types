# Match Types

> **Since:** Scala 3.0

## What it is

A match type is a type-level construct in Scala 3 that reduces to one of several right-hand-side types depending on the structure of a scrutinee type. Written as `X match { case P1 => T1; ... ; case Pn => Tn }`, it performs type-level pattern matching, analogous to a value-level `match` expression. Match types enable conditional type selection and recursive type computation without macros or implicit resolution tricks.

## What constraint it lets you express

**Match types let you express type-level computation: "given a type as input, select or compute the appropriate output type by pattern matching."** This enables dependently-typed methods whose return type is determined by their argument type, type-level recursion over structures like tuples, and conditional type relationships that were previously impossible without macros.

## Minimal snippet

```scala
// Basic: extract the element type of a container
type Elem[X] = X match
  case String      => Char
  case Array[t]    => t
  case Iterable[t] => t

// Usage:
val c: Elem[String]      = 'a'     // Char
val i: Elem[Array[Int]]  = 42      // Int
val f: Elem[List[Float]] = 3.14f   // Float

// Recursive: drill down to the leaf element type
type LeafElem[X] = X match
  case String      => Char
  case Array[t]    => LeafElem[t]
  case Iterable[t] => LeafElem[t]
  case AnyVal      => X

// Dependently-typed method using a match type as return type
def leafElem[X](x: X): LeafElem[X] = x match
  case x: String      => x.charAt(0)
  case x: Array[t]    => leafElem(x(0))
  case x: Iterable[t] => leafElem(x.head)
  case x: AnyVal      => x
```

## Interaction with other features

- **Dependent methods.** Match types are the primary mechanism for writing methods whose return type depends on the argument type. The compiler verifies that the value-level match mirrors the type-level match under specific conditions (no guards, typed patterns, same number of cases). [-> UC-04](../usecases/UC11-effect-tracking.md)
- **Recursive types.** Match types can reference themselves recursively. An upper bound can be declared (`type Concat[Xs <: Tuple, Ys <: Tuple] <: Tuple = ...`) to help the compiler verify that recursive invocations are well-typed.
- **Tuple operations.** The standard library uses match types extensively for tuple operations (`Concat`, `Zip`, `Map`, `Head`, `Tail`, etc.).
- **Union/intersection types.** Match types can dispatch on union or intersection types, though reduction requires that the scrutinee can be proven disjoint from rejected patterns. [-> UC-01](../usecases/UC01-invalid-states.md)
- **Given instances.** Match types can be used in the result type of given definitions, enabling type-class instances whose behavior varies by type. [-> UC-05](../usecases/UC12-compile-time.md)
- **Subtyping.** A match type and its reduction (when it reduces) are mutual subtypes. A match type also conforms to its declared upper bound even when it cannot reduce.

## Gotchas and limitations

1. **Reduction is not always possible.** A match type remains "stuck" (unreduced) when the compiler cannot prove that the scrutinee matches a case or is disjoint from it. Abstract type parameters frequently cause stuck match types.
2. **Disjointness proofs are limited.** The compiler relies on single inheritance of classes, finality, distinct constant types, and distinct singleton paths. It cannot reason about arbitrary user-defined disjointness.
3. **Invariant positions.** All type positions in a match type (scrutinee, patterns, bodies) are treated as invariant, regardless of the variance of the enclosing type constructor.
4. **No guards.** Match type cases cannot have guards. All dispatch must be structural, based on type patterns alone.
5. **Termination.** Recursive match types can cause infinite reduction loops. The compiler detects these via cycle detection in subtyping and reports a "recursion limit exceeded" error.
6. **Value-level mirror requirements.** For a value-level `match` to be typed using a match type, the patterns must be typed patterns (`case x: T => ...`), there must be no guards, and the case count and order must match exactly.
7. **No constraint narrowing.** Unlike Haskell's type families, match type reduction does not tighten the underlying type constraint. Type variables in the enclosing scope are not unified by pattern matching.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) Union and intersection types can serve as match type scrutinees for conditional dispatch.
- [-> UC-02](../usecases/UC02-domain-modeling.md) Type lambdas can appear in match type bodies, producing computed higher-kinded types.
- [-> UC-04](../usecases/UC11-effect-tracking.md) Dependent function types use match types as return types to achieve type-safe dependent returns.
- [-> UC-05](../usecases/UC12-compile-time.md) Given instances can leverage match types to provide type-class evidence conditionally.
