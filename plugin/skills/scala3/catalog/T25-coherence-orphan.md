# Coherence & Instance Scoping (via Given Import Rules)

> **Since:** Scala 3.0 | **Latest changes:** Scala 3.6 (new given syntax), Scala 3.7 (re-prioritised given resolution)

## What it is

Scala 3 has **no orphan rule**. Unlike Rust, which forbids defining a trait implementation for a type unless you own the trait or the type, Scala allows you to define a `given` instance for any type-class/type combination anywhere. Coherence — the guarantee that there is at most one applicable instance for each type — is instead maintained through **scoping and import rules**: given instances are not globally visible; they must be explicitly imported or discovered through the companion-object implicit scope.

This design is a deliberate trade-off. Rust's orphan rule provides *global* coherence (there is exactly one `impl Trait for Type` across the entire program). Scala provides *local* coherence (at each use site, there is at most one unambiguous given in scope). This gives Scala more flexibility — you can define alternative instances in different scopes — but requires discipline to avoid conflicting instances.

## What constraint it enforces

**Scala's given scoping rules ensure that at any use site, the compiler finds at most one given instance of each type. If two *named* instances of the same type are in scope with equal priority, the compiler rejects the program with an ambiguity error rather than silently choosing one.**

The "named" qualifier is load-bearing. An anonymous `given Show[Int]` is compiled under a *synthesised* name derived from its type (`given_Show_Int`), so two anonymous givens of the same type in different objects collide as ordinary names: importing both is plain name shadowing, the later import wins, and no diagnostic is issued. Give a given an explicit name whenever a competing instance could plausibly exist elsewhere — see gotcha 1.

## Minimal snippet

```scala
trait Ordering[T]:
  def compare(x: T, y: T): Int

// Instance in companion object — always in implicit scope
object Ordering:
  given intAsc: Ordering[Int]:      // name it: anonymous givens shadow silently
    def compare(x: Int, y: Int) = x - y

// Alternative instance in a separate object — must be imported
object ReverseOrdering:
  given intDesc: Ordering[Int]:
    def compare(x: Int, y: Int) = y - x

def sorted[T: Ordering](xs: List[T]): List[T] =
  xs.sortWith((a, b) => summon[Ordering[T]].compare(a, b) < 0)

// Default: uses companion instance
sorted(List(3, 1, 2))  // List(1, 2, 3)

// Override: import the alternative
{
  import ReverseOrdering.given
  sorted(List(3, 1, 2))  // List(3, 2, 1)
}
// Outside the block, the default is back in effect
```

## How Scala avoids conflicting instances without an orphan rule

### 1. Import-based visibility

Given instances are **not** imported by `import M.*`. They require explicit `import M.given` or `import M.{given Ordering[?]}`. This means conflicting instances in different modules do not interfere unless explicitly brought together.

### 2. Companion scope as the default

The compiler automatically searches companion objects of the types involved in the target type. For `Ordering[MyClass]`, it searches both `Ordering` and `MyClass` companions. Placing the "canonical" instance in one of these companions makes it the default without any import.

### 3. Priority ordering

When multiple instances are found, specificity rules resolve the conflict:
- **Local/imported (lexical scope)** beats **companion / implicit scope** — unconditionally, not just on a tie.
- **More specific type** beats **less specific** (`given Ordering[Int]` beats `given [T] => Ordering[T]`).
- Within the same scope, **nesting depth** comes first, then **owner specificity**: a given defined in a subclass of the class/object that defines the competing given wins.
- Everything else in the same scope is **ambiguous**, not ranked.

Two Scala 2 intuitions do *not* carry over:

- **A named (or by-type) given import does not beat a wildcard given import.** Scala 3 dropped that rule. `import M1.m1` (or `import M1.{given Show[Int]}`) alongside `import M2.given` puts two equally-ranked candidates in lexical scope, and the use site fails with an `[E172]` ambiguity error. To pick a winner, import only one of them.
- **A given whose *type* is a subtype does not beat one whose type is a supertype.** Given `trait Sub[T] extends Base[T]`, with both `given b: Base[Int]` and `given s: Sub[Int]` in scope, Scala 3.7's re-prioritisation makes `summon[Base[Int]]` select `b`, the supertype-typed one. Subtyping wins only under the *owner* reading in the bullet above (where the given is defined), not the instance-type reading.

### 4. Export for controlled re-exposure

The `export` clause lets a module selectively re-expose given instances from another module, creating curated "instance bundles" without pulling in everything.

```scala
trait Ordering[T]:
  def compare(x: T, y: T): Int

trait Show[T]:
  def show(t: T): String

object Ordering:
  given intAsc: Ordering[Int] = (x, y) => x - y  // companion given to re-export

object MyCustomInstances:
  given showInt: Show[Int] = _.toString
  given showBoolean: Show[Boolean] = if _ then "yes" else "no"

object Defaults:
  export Ordering.given         // re-export companion givens
  export MyCustomInstances.{given Show[?]}  // only Show instances
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type classes / givens** [-> catalog/T05](T05-type-classes.md) | Coherence rules determine which given instance the compiler selects for each `using` parameter. The scoping rules ARE the coherence mechanism. |
| **Context functions** [-> catalog/T42](T42-context-functions.md) | Context functions (`T ?=> U`) trigger given resolution for `T`. The same scoping and priority rules apply. |
| **Given resolution** [-> catalog/T37](T37-trait-solver.md) | T37 describes the resolution algorithm in detail. This file focuses on the coherence properties that emerge from those rules. |
| **Encapsulation** [-> catalog/T21](T21-encapsulation.md) | Access modifiers and `export` clauses control which given instances are visible, providing module-level encapsulation of type-class instances. |

## Comparison with Rust's orphan rule

| Aspect | Rust | Scala 3 |
|--------|------|---------|
| **Rule** | Cannot implement a foreign trait for a foreign type | No restriction — any given anywhere |
| **Coherence scope** | Global (whole program) | Local (per use site) |
| **Conflicting instances** | Compilation error at the impl definition | Ambiguity error at the use site (if both are in scope *and named*; anonymous givens shadow silently) |
| **Newtype workaround** | Required for alternative instances | Not needed — just define in a different scope |
| **Trade-off** | Safety at the cost of flexibility | Flexibility at the cost of discipline |

## Gotchas and limitations

1. **No global uniqueness guarantee — and with anonymous givens the clash is silent.** Two libraries can each define a `Show[Int]` in an ordinary object, and a user can import both. (This cannot happen via *companion* objects: the implicit scope of `Ordering[Int]` is only the `Ordering` and `Int` companions, so a third party has nowhere to inject a competing given — and companion givens are never *imported* anyway, they are always in implicit scope.) What happens next depends entirely on whether the givens are named. Anonymous ones are compiled under the same synthesised name, so the second import just shadows the first:

   ```scala
   trait Show[T]:
     def show(t: T): String

   object M1:
     given Show[Int] = _ => "M1"   // synthesised name: given_Show_Int

   object M2:
     given Show[Int] = _ => "M2"   // same synthesised name

   import M1.given
   import M2.given                 // shadows M1's — no ambiguity, no warning

   @main def demo(): Unit =
     println(summon[Show[Int]].show(1))  // prints "M2"
   ```

   Naming the givens is what turns the clash into the error you actually want:

   ```scala
   trait Show[T]:
     def show(t: T): String

   object M1:
     given m1: Show[Int] = _ => "M1"

   object M2:
     given m2: Show[Int] = _ => "M2"

   import M1.given
   import M2.given

   @main def demo(): Unit =
     // error: Ambiguous given instances: both given instance m2 in object M2 and given instance m1 in object M1 match type Show[Int]
     println(summon[Show[Int]].show(1))
   ```

   So: **name every given you publish.** Scala relies on convention (canonical instances in companions, explicit names elsewhere) rather than enforcement, and the anonymous-given default quietly opts you out of the one check the compiler does offer.

2. **Diamond imports.** Importing givens from two modules that transitively include the same instance can cause unexpected ambiguities. Use by-type imports (`import M.{given Ordering[?]}`) to be precise.

3. **Companion scope is always searched.** You cannot "opt out" of companion-object instances. If the companion provides a given and you import an alternative, the compiler finds both — but the import always wins, because lexical scope strictly outranks implicit scope. Equal specificity is exactly the case where the import wins; it does not produce an ambiguity.

4. **Migration from Scala 2.** Scala 2's `implicit` definitions are found by `import M.*`, but Scala 3's `given` definitions are not. This discrepancy can cause confusing breakage during migration.

5. **No coherence checker.** Unlike Rust's compiler, which rejects incoherent programs at definition time, Scala only detects conflicts at use sites. A conflicting instance in an unimported module causes no error until someone imports it.

6. **Sealed type classes.** A pattern for stronger coherence: make the type-class trait `sealed` or place it in a package with controlled exports, so only authorized modules can define instances.

## Beginner mental model

Think of given instances as **business cards** in filing cabinets. Every type class has a "default" cabinet (its companion object) with one card. Other modules can print their own cards (alternative instances), but those cards stay in their own cabinets until someone explicitly takes them out (imports them). At any moment, you can only hold one card of each type. If you accidentally grab two, the compiler asks you to put one back (ambiguity error) — but only if the cards carry names. Two unnamed cards look identical to the filing system, so the second one silently replaces the first. Rust, by contrast, only allows one card to be printed in the first place.

## Example A — Scoped alternative instances

```scala
trait JsonFormat[T]:
  def write(t: T): String

object JsonFormat:
  given defaultDate: JsonFormat[java.time.LocalDate]:
    def write(d: java.time.LocalDate) = s""""${d.toString}""""

object IsoFormat:
  given isoDate: JsonFormat[java.time.LocalDate]:
    def write(d: java.time.LocalDate) =
      s""""${d.format(java.time.format.DateTimeFormatter.ISO_DATE)}""""

object AmericanFormat:
  given usDate: JsonFormat[java.time.LocalDate]:
    def write(d: java.time.LocalDate) =
      s""""${d.format(java.time.format.DateTimeFormatter.ofPattern("MM/dd/yyyy"))}""""

// Each module imports exactly the format it needs — no conflict
object EuropeanService:
  import IsoFormat.given
  def serialize(d: java.time.LocalDate) = summon[JsonFormat[java.time.LocalDate]].write(d)

object AmericanService:
  import AmericanFormat.given
  def serialize(d: java.time.LocalDate) = summon[JsonFormat[java.time.LocalDate]].write(d)
```

## Use-case cross-references

- [-> UC-14](../usecases/UC14-extensibility.md) Scoped instances allow third-party extensibility without orphan-rule friction.

## Source anchors

- [Scala 3 Reference -- Given Imports](https://docs.scala-lang.org/scala3/reference/contextual/given-imports.html)
- [Scala 3 Reference -- Implicit Resolution](https://docs.scala-lang.org/scala3/reference/changed-features/implicit-resolution.html)
- [Scala 3 Reference -- Givens](https://docs.scala-lang.org/scala3/reference/contextual/givens.html)
- [Scala 3 Reference -- Export Clauses](https://docs.scala-lang.org/scala3/reference/other-new-features/export.html)
