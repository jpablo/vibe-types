# Given/Implicit Resolution (Scala's Trait Solver)

> **Since:** Scala 3.0 | **Latest changes:** Scala 3.6 (new given syntax, simplified priority rules)

## What it is

Given resolution is the compiler algorithm that finds and selects **given instances** (Scala 3's replacement for Scala 2 implicits) when a `using` parameter needs to be filled. It is analogous to Rust's trait solver or Haskell's instance resolution: the compiler searches a well-defined set of scopes, ranks candidates by specificity, and either supplies the unique best match or reports an error. In Scala 3, the rules were redesigned to be simpler and more predictable than Scala 2's implicit search, with clearer priority ordering and better ambiguity reporting.

The resolution algorithm determines where type-class instances come from, how capability injection works, and whether two competing given definitions cause an ambiguity error or resolve by specificity. Understanding this algorithm is essential for debugging "no given instance found" and "ambiguous given instances" errors.

## What constraint it enforces

**Given resolution guarantees that for each `using` parameter, there is at most one unambiguous given instance in scope. The compiler either finds exactly one best candidate or rejects the program, preventing silent selection of an unintended instance.**

## Minimal snippet

```scala
trait Show[T]:
  extension (t: T) def show: String

// Companion object — always in implicit scope for Show[Int]
object Show:
  given Show[Int]:
    extension (t: Int) def show = t.toString

// Local scope — higher priority than companion
object CustomInstances:
  given Show[Int]:
    extension (t: Int) def show = s"int($t)"

def printIt[T: Show](x: T): Unit = println(x.show)

// Without import: uses companion object instance
printIt(42)  // "42"

// With import: local import wins over companion
import CustomInstances.given
printIt(42)  // "int(42)"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type classes / givens** [-> catalog/T05](T05-type-classes.md) | Given resolution is the *engine* behind type-class dispatch. Every `[T: Ord]` context bound triggers the resolution algorithm to find an `Ord[T]` instance. |
| **Context functions** [-> catalog/T42](T42-context-functions.md) | Context function application `T ?=> U` triggers resolution for the `T` parameter. The search follows the same scope and priority rules. |
| **Conversions / coercions** [-> catalog/T18](T18-conversions-coercions.md) | Implicit conversions (`given Conversion[A, B]`) are found by the same resolution mechanism but are only applied when a type mismatch would otherwise occur. |

## Where the compiler looks (search scopes)

The compiler searches for given instances in the following order:

1. **Local scope.** Givens defined or imported in the enclosing block, method, or class.
2. **Explicit imports.** `import M.given`, `import M.{given Show[?]}`, or `import M.specificInstance`.
3. **Wildcard imports.** `import M.given` (wildcard given import) — but *not* `import M.*`, which excludes givens.
4. **Implicit scope (companion objects).** The companion objects of all types involved in the target type. For `Show[List[Int]]`, the compiler searches `Show`, `List`, and `Int` companions.
5. **Package objects and toplevel givens.** Givens defined at the top level of the package containing the call site.

## Priority rules

When multiple candidates are found, the compiler applies **specificity** to choose:

- A given defined in a **subclass** wins over one in a **superclass**.
- A given with a **more specific** type parameter wins (e.g., `given Show[Int]` beats `given [T] => Show[T]`).
- A **local or imported** given wins over one found via **implicit scope** (companion objects).
- A **named** import wins over a **wildcard** given import.

If two candidates have the same specificity, the compiler reports an **ambiguity error**.

## Scala 3 changes from Scala 2

- **`given` replaces `implicit val/def/object`.** The new keyword makes intent explicit.
- **Given imports are separate.** `import M.*` does NOT import givens. Use `import M.given`.
- **Simpler priority.** Scala 2 had complex implicit priority based on inheritance and "not-inherited" rules. Scala 3 uses a cleaner specificity ordering.
- **Ambiguity propagation.** In Scala 2, an ambiguity deep in the search could silently cause a "not found" error at the top level. Scala 3 propagates the ambiguity upward, producing a better error message.
- **`-explain` flag.** Compile with `-explain` to see the compiler's search trace, showing which scopes were checked and why candidates were accepted or rejected.

## Gotchas and limitations

1. **`import M.*` does not import givens.** This is the most common surprise for Scala 2 migrants. You must write `import M.given` or `import M.{given, *}`.

2. **Companion scope is searched last.** A given in a companion object is a fallback, not the default. Any local or imported given of the same type will shadow it.

3. **Divergence detection.** If resolution triggers itself recursively (e.g., `given [T: Show] => Show[List[T]]` with no base case), the compiler detects the cycle and reports an error rather than looping.

4. **By-name context parameters.** `using` parameters declared as `=> T` (by-name) allow the compiler to break cycles in recursive given search by deferring evaluation. This is essential for mutually recursive type-class instances.

5. **Anonymous given collisions.** Two anonymous givens with structurally similar types may receive the same compiler-generated name, causing binary-compatibility issues. Name your public givens explicitly.

6. **`summon` vs direct access.** `summon[T]` triggers resolution at the call site. If you already have the instance via a `using` parameter, access it directly to avoid redundant search.

## Beginner mental model

Think of the compiler as a **librarian** looking for a book (a given instance). It first checks your desk (local scope), then your personal shelf (imports), then walks to the reference section (companion objects). If it finds exactly one matching book, it hands it to you. If it finds two equally good matches, it asks you to be more specific (ambiguity error). If it finds nothing, it tells you the book is missing ("no given instance found").

## Example A — Debugging with `-explain`

```scala
trait Codec[T]:
  def encode(t: T): String

object Codec:
  given Codec[String]:
    def encode(t: String) = s"\"$t\""

object JsonCodecs:
  given Codec[String]:
    def encode(t: String) = s"""{"value":"$t"}"""

import JsonCodecs.given

// Compile with: scalac -explain MyFile.scala
// The compiler shows:
//   - Found given Codec[String] in JsonCodecs (via import)
//   - Found given Codec[String] in Codec companion (via implicit scope)
//   - Selected: JsonCodecs instance (import wins over companion)
def test = summon[Codec[String]].encode("hi")  // {"value":"hi"}
```

## Use-case cross-references

- [-> UC-14](../usecases/UC14-extensibility.md) Given resolution determines how third-party type-class instances are discovered and prioritized.
- [-> UC-12](../usecases/UC12-compile-time.md) Resolution happens entirely at compile time; understanding the search algorithm helps diagnose compile-time errors.

## Source anchors

- [Scala 3 Reference -- Given Instances](https://docs.scala-lang.org/scala3/reference/contextual/givens.html)
- [Scala 3 Reference -- Given Imports](https://docs.scala-lang.org/scala3/reference/contextual/given-imports.html)
- [Scala 3 Reference -- Implicit Resolution](https://docs.scala-lang.org/scala3/reference/changed-features/implicit-resolution.html)
- [Scala 3 Migration Guide -- Implicit Resolution Changes](https://docs.scala-lang.org/scala3/guides/migration/incompat-other-changes.html)
