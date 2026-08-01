# Given/Implicit Resolution (Scala's Trait Solver)

> **Since:** Scala 3.0 | **Latest changes:** Scala 3.6 (new given syntax, simplified priority rules)

## What it is

Given resolution is the compiler algorithm that finds and selects **given instances** (Scala 3's replacement for Scala 2 implicits) when a `using` parameter needs to be filled. The analogy to Rust's trait solver or Haskell's instance resolution holds only at the level of "the compiler finds instances for you instead of making you pass them explicitly." The mechanisms differ fundamentally: Rust and Haskell resolve against a **global, coherent** set of impls/instances — impls are not scoped, an `import` never changes which impl is selected, and overlapping instances are rejected outright by coherence rules rather than ranked. Scala instead searches a set of **lexical** scopes plus the companion objects of the types involved, ranks whatever candidates it finds, and either supplies the unique best match or reports an error. That scope- and import-sensitivity is precisely how Scala differs: the same expression can resolve to different instances in two files depending on what each file imports. Within Scala's own history, the Scala 3 rules were redesigned to be simpler and more predictable than Scala 2's implicit search, with clearer priority ordering and better ambiguity reporting.

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

The search runs in two tiers, and **tier 1 is tried first as a whole**; tier 2 is only consulted if tier 1 produces no candidate.

**Tier 1 — lexical scope.** Everything visible at the call site by simple name, with no prefix:

1. **Local and inherited givens.** Givens defined in (or inherited into) the enclosing block, method, class, or object.
2. **Imported givens.** `import M.given` (all givens of `M`), `import M.{given Show[?]}` (by type), or `import M.specificInstance` (by name). Note that `import M.*` does *not* import givens.
3. **Top-level givens of the enclosing package.** Givens declared at the top level of the package containing the call site (including in a package object) are lexically in scope, so they are tier-1 candidates — they beat companion-object candidates outright rather than being a last resort.

**Tier 2 — implicit scope (companion objects).** The companion objects of all types involved in the target type. For `Show[List[Int]]`, the compiler searches the `Show`, `List`, and `Int` companions.

Scala 3 **removed package prefixes from the implicit scope**. A given sitting at the top level of the *type's* package but not in its companion is not found from another package: `summon[lib.Show[Int]]` in package `app` fails with "No given instance of type lib.Show[Int] was found", and the compiler merely *suggests* `import lib.given_Show_Int`.

## Priority rules

When multiple candidates are found, the compiler ranks them:

- **Nesting depth first.** Among lexically visible candidates, the one defined at greater nesting depth wins — a given in an inner object shadows one in the enclosing object with no ambiguity.
- **Then owner/definition specificity.** A given defined in a **subclass** wins over one in a **superclass**, and a given with a **more specific** type wins (e.g., `given Show[Int]` beats `given [T] => Show[T]`).
- A **lexically visible** given (tier 1) wins over one found via **implicit scope** (tier 2).

Scala 3 **dropped** Scala 2's rule that a named import outranks a wildcard import. Two givens brought into the same scope — one by `import A.given`, one by `import B.narrow` — are at the same nesting depth with no specificity difference between them, so they are simply **ambiguous** (see Example A).

If two candidates cannot be separated by these rules, the compiler reports an **ambiguity error**.

## Scala 3 changes from Scala 2

- **`given` replaces `implicit val/def/object`.** The new keyword makes intent explicit.
- **Given imports are separate.** `import M.*` does NOT import givens. Use `import M.given`.
- **Simpler priority.** Scala 2 had complex implicit priority based on inheritance and "not-inherited" rules. Scala 3 uses a cleaner specificity ordering.
- **Ambiguity propagation.** In Scala 2, an ambiguity deep in the search could silently cause a "not found" error at the top level. Scala 3 propagates the ambiguity upward, producing a better error message.
- **No implicit-search trace.** Scala 2's `-Xlog-implicits` has no successor: `-Xlog-implicits`, `-Xprint-implicits`, `-Vimplicits` and `-Ydebug-implicits` are all rejected by Scala 3.8.4 ("bad option ... was ignored"). `-explain` is *not* a substitute — it only expands the prose of an error that was already reported, printing nothing at all for a successful given search. Debugging resolution means reading the failure message (which already lists the partial term the compiler built) and bisecting imports by hand.

## Gotchas and limitations

1. **`import M.*` does not import givens.** This is the most common surprise for Scala 2 migrants. You must write `import M.given` or `import M.{given, *}`.

2. **Companion scope is searched last.** A given in a companion object is a fallback, not the default. Any local or imported given of the same type will shadow it.

3. **Divergence detection.** Divergence is not "recursion without a base case" — a recursive given whose premise *shrinks* the goal, such as `given [T: Show] => Show[List[T]]`, terminates on its own and just yields an ordinary "no implicit values were found that match type Show[Int]". Divergence happens when a premise **grows** the type, so each step asks a strictly larger question: `given [T] => (ev: Show[List[T]]) => Show[T]` makes `summon[Show[Int]]` ask for `Show[List[Int]]`, then `Show[List[List[Int]]]`, and the compiler cuts the search off with `But given instance given_Show_T produces a diverging implicit search when trying to match type Show[List[List[Int]]]` rather than looping forever.

4. **By-name context parameters.** `using` parameters declared as `=> T` (by-name) allow the compiler to break cycles in recursive given search by deferring evaluation. This is essential for mutually recursive type-class instances.

5. **Anonymous given collisions are a hard compile error.** The synthesized name elides type *arguments*, so `given Show[List[Int]]` and `given Show[List[String]]` are both named `given_Show_List`. Declaring both in the same scope does not merely risk a binary-compatibility problem — it fails outright with `[E161] ... given_Show_List is already defined as object given_Show_List`. Name such givens explicitly (`given showIntList: Show[List[Int]]`). Stable names are also what keeps public givens binary-compatible across releases, since the synthesized name changes whenever the declared type does.

6. **`summon` vs direct access.** `summon[T]` triggers resolution at the call site. If you already have the instance via a `using` parameter, access it directly to avoid redundant search.

## Beginner mental model

Think of the compiler as a **librarian** looking for a book (a given instance). It first checks your desk (local scope), then your personal shelf (imports), then walks to the reference section (companion objects). If it finds exactly one matching book, it hands it to you. If it finds two equally good matches, it asks you to be more specific (ambiguity error). If it finds nothing, it tells you the book is missing ("no given instance found").

## Example A — Reading the two resolution diagnostics

There is no search trace to turn on, so the diagnostics themselves are the debugging tool. First, the case that succeeds: the import is lexical scope (tier 1) and the companion is implicit scope (tier 2), so there is no ambiguity and the import wins.

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

def test = summon[Codec[String]].encode("hi")  // {"value":"hi"}
```

When nothing is found, the message names the type and the parameter it was needed for:

```scala
trait Codec[T]:
  def encode(t: T): String

object Codec:
  given Codec[String]:
    def encode(t: String) = s"\"$t\""

def missing = summon[Codec[Int]]
// error: No given instance of type Codec[Int] was found for parameter x of method summon in object Predef
```

When two lexically visible candidates tie, the message names both — note that the named import does *not* outrank the wildcard given import:

```scala
trait Codec[T]:
  def encode(t: T): String

object A:
  given Codec[String]:
    def encode(t: String) = "a"

object B:
  given narrow: Codec[String]:
    def encode(t: String) = "b"

import A.given
import B.narrow

def clash = summon[Codec[String]]
// error: Ambiguous given instances: both object narrow in object B and object given_Codec_String in object A match type Codec[String] of parameter x of method summon in object Predef
```

## Use-case cross-references

- [-> UC-14](../usecases/UC14-extensibility.md) Given resolution determines how third-party type-class instances are discovered and prioritized.
- [-> UC-12](../usecases/UC12-compile-time.md) Resolution happens entirely at compile time; understanding the search algorithm helps diagnose compile-time errors.

## Source anchors

- [Scala 3 Reference -- Given Instances](https://docs.scala-lang.org/scala3/reference/contextual/givens.html)
- [Scala 3 Reference -- Given Imports](https://docs.scala-lang.org/scala3/reference/contextual/given-imports.html)
- [Scala 3 Reference -- Implicit Resolution](https://docs.scala-lang.org/scala3/reference/changed-features/implicit-resolution.html)
- [Scala 3 Migration Guide -- Implicit Resolution Changes](https://docs.scala-lang.org/scala3/guides/migration/incompat-other-changes.html)
