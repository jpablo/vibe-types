# Changed & Dropped Features: Type Inference, Implicit Resolution, Existential Types, Type Projection

> **Since:** Scala 3.0 | **Latest changes:** Scala 3.5 (given disambiguation rule 9), Scala 3.6 (recursive given avoidance rule 10)

## What it is

Scala 3 deliberately changes several type-system behaviors inherited from Scala 2 and drops features that proved unsound or overly complex. **Type inference** is improved with better GADT support and a new algorithm. **Implicit resolution** uses a new search algorithm with refined disambiguation, proper ambiguity propagation, and prevention of recursive givens. **Existential types** (`forSome`) are removed entirely. **General type projection** (`T#A` on abstract types) is restricted to concrete prefixes only. Together these changes make the type system more predictable, sound, and amenable to tooling.

## What constraint it lets you express

**By tightening inference rules, fixing implicit resolution anomalies, and removing unsound features, Scala 3 ensures that the types the compiler infers and the implicits it selects are consistent, unambiguous, and free from the soundness holes that plagued Scala 2.** The constraints you lose (existential types, abstract type projection) are replaced by safer alternatives (path-dependent types, wildcard refinements).

## Minimal snippet

```scala
// --- Implicit resolution: nesting now matters ---
def f(implicit i: C) =
  def g(implicit j: C) =
    implicitly[C]   // resolves to j (more deeply nested), not ambiguity error

// --- Implicit resolution: ambiguity propagates ---
class A; class B extends C; class C
implicit def a1: A = ???
implicit def a2: A = ???
implicit def b(implicit a: A): B = ???
implicit def c: C = ???

// implicitly[C] is ambiguous: b(a1) and b(a2) are both better than c,
// but neither is better than the other. Scala 2 would have picked c.

// --- NotGiven replaces negation-by-ambiguity hack ---
import scala.util.NotGiven
def onlyIfNoOrdering[T](x: T)(using NotGiven[Ordering[T]]): String =
  "no ordering available"

// --- Dropped: existential types ---
// Scala 2:  List[T] forSome { type T }   // no longer compiles
// Scala 3:  List[?]                       // wildcard, treated as refined type

// --- Dropped: general type projection on abstract types ---
// Scala 2:  T#A where T is abstract       // unsound, no longer compiles
// Scala 3:  only concrete prefix allowed
class Outer { class Inner }
type Valid = Outer#Inner       // ok: Outer is concrete
// type Invalid = T#Inner      // error if T is abstract
```

## Interaction with other features

- **Explicit given types (rule 1).** Implicit vals and defs at class or object level must have an explicitly declared result type. This improves compilation speed (no need to infer the type before indexing) and prevents accidental implicit widening. Local implicits inside blocks are exempt.
- **Nesting-based priority (rule 2).** When two implicits of the same type are in scope and one is more deeply nested, the inner one wins. Scala 2 treated this as ambiguous. This eliminates the old "shadowing" failure mode.
- **Package prefixes excluded (rule 3).** Package-level givens are no longer in the implicit scope of types defined in sub-packages. Only companion objects and explicit imports contribute. This makes implicit scope more predictable.
- **Ambiguity propagation (rule 4).** An ambiguity found during a recursive step of implicit search now propagates to the caller rather than being silently discarded. This prevents Scala 2's surprising behavior where an ambiguity in a sub-query caused fallback to a less-specific alternative.
- **`NotGiven[Q]` (rule 4 corollary).** The `scala.util.NotGiven` type replaces the Scala 2 hack of exploiting ambiguity for negated implicit search. `NotGiven[Q]` succeeds if and only if no implicit of type `Q` is found.
- **Divergence as soft failure (rule 5).** A divergent implicit search is treated as a normal failure, allowing other candidates to be tried, rather than aborting the entire search.
- **Given disambiguation (rule 9).** From Scala 3.5, when multiple givens match an expected type, the _most general_ one is preferred (not the most specific, as in overloading resolution). Compile with `-source:3.5-migration` to see warnings where behavior changes.
- **Recursive given avoidance (rule 10).** Under `-source:future`, implicit resolution discards search results that lead back to the given definition currently being checked, preventing infinite-loop givens like `given Ordering[Price] = summon[Ordering[BigDecimal]]` in an opaque type companion.
- **Path-dependent types replace existentials.** Any use case previously requiring `forSome` can be expressed with path-dependent types, wildcards (refined types), or match types. [-> UC-04](../usecases/UC11-effect-tracking.md)
- **Concrete type projection.** `T#A` is allowed only when `T` is a concrete class. For abstract types, use path-dependent types (`x.A` for some value `x: T`). [-> UC-04](../usecases/UC11-effect-tracking.md)

## Gotchas and limitations

1. **Migration of negated implicits.** Scala 2 code that relied on ambiguity-based negation patterns must be rewritten to use `NotGiven`. The `-source:3.0-migration` flag helps identify these.
2. **Implicit scope narrowing.** Removing package prefixes from implicit scope means that some Scala 2 code relying on package-level implicits will stop compiling. Move such implicits into companion objects or import them explicitly.
3. **Call-by-name priority dropped (rule 6).** Scala 2 gave lower priority to implicit conversions with call-by-name parameters. Scala 3 treats them equally, so previously working code with both `conv(x: Int)` and `conv(x: => Int)` may become ambiguous.
4. **Existential type approximation.** When reading Scala 2 classfiles containing existential types, Scala 3 performs a best-effort approximation and issues a warning. Some types may not round-trip precisely.
5. **Type projection restriction.** Dropping `T#A` for abstract `T` breaks type-level encoding tricks (e.g., the SKI combinator calculus encoding). The recommended alternative is path-dependent types, which require a value-level witness.
6. **Given preference reversal.** The shift from "most specific" to "most general" in given disambiguation (rule 9) can silently change which instance is selected. Always compile with migration warnings when upgrading to Scala 3.5+.

## Use-case cross-references

- [-> UC-04](../usecases/UC11-effect-tracking.md) Path-dependent types: the primary replacement for existential types and abstract type projections.
- [-> UC-05](../usecases/UC12-compile-time.md) Given instances: all implicit resolution changes directly affect type class derivation and given search.
- [-> UC-06](../usecases/UC13-state-machines.md) Context functions: changes to implicit resolution apply equally to `?=>` parameter synthesis.
- [-> UC-07](../usecases/UC14-extensibility.md) Modularity: `tracked` parameters reduce the need for `Aux`-pattern workarounds that were partly motivated by type projection limitations.
