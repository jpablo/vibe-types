# Experimental & Preview: Named Type Arguments, `into`, Modularity

> **Status:** Mixed -- Named type args: experimental since 3.0 | `into`: preview since 3.8 | Modularity: experimental

## What it is

This document covers three forward-looking Scala 3 features at different maturity stages. **Named type arguments** (experimental) let callers bind type parameters by name rather than position, allowing unneeded parameters to be inferred. **The `into` type** (preview, since Scala 3.8) provides fine-grained control over where implicit conversions using `scala.Conversion` are allowed, removing the need for a blanket `import scala.language.implicitConversions`. **Modularity improvements** (experimental, `-source:future -language:experimental.modularity`) add `tracked` class parameters, applied constructor types, and refined-type parents, making dependent-typing-based module composition in Scala as natural as SML functors -- without the infamous `Aux` pattern.

## What constraint it lets you express

**Named type arguments let you selectively specify only the type parameters the compiler cannot infer; `into` restricts implicit conversions to specific parameter sites instead of enabling them globally; `tracked` parameters preserve dependent type information through class constructors, enabling sound modular composition with abstract type members.**

## Minimal snippet

```scala
// --- Named type arguments ---
def construct[Elem, Coll[_]](xs: Elem*): Coll[Elem] = ???

val xs1 = construct[Coll = List, Elem = Int](1, 2, 3)  // both named, any order
val xs2 = construct[Coll = List](1, 2, 3)               // Elem inferred

// --- into (preview, Scala 3.8+) ---
// As a type constructor: conversions allowed only at marked sites
def ++(elems: into[IterableOnce[Int]]): List[Int] = ???

given Conversion[Array[Int], IterableOnce[Int]] = _.toList
val ys = List(1) ++ Array(2, 3)  // conversion applied, no language import needed

// As a modifier: conversions allowed for any parameter of this type
into trait Modifier
given Conversion[String, Modifier] = ???

def f(m: Modifier) = ()
f("hello")  // ok, Modifier is declared `into`

// --- Tracked parameters (modularity) ---
import scala.language.experimental.modularity

trait Ordering:
  type T
  def compare(t1: T, t2: T): Int

class SetFunctor(tracked val ord: Ordering):
  type Set = List[ord.T]
  def empty: Set = Nil
  extension (s: Set)
    def add(x: ord.T): Set = x :: s

object intOrdering extends Ordering:
  type T = Int
  def compare(t1: Int, t2: Int): Int = t1 - t2

val IntSet = SetFunctor(intOrdering)
val s = IntSet.empty.add(1).add(2)  // element type Int is preserved
```

## Interaction with other features

- **Named type arguments and type inference.** Named type arguments compose with local type inference: unspecified parameters are inferred as usual. All arguments must be either all named or all positional -- no mixing. This is especially useful for methods with many type parameters where only one or two are ambiguous.
- **`into` and `Conversion`.** `into[T]` is defined as `opaque type into[T] >: T = T` in the `Conversion` companion. It interacts with implicit search: only when the expected type is a valid conversion target type (an `into`-wrapped type, an `into`-modified trait, or a type alias thereof) does the compiler insert a `Conversion` without requiring a language import. Vararg parameters with `into` allow different conversions for each element.
- **`into` unwrapping in method bodies.** Inside a method, `into` wrappers on parameter types are erased from the local type, so `elems: into[IterableOnce[A]]` is seen as `elems: IterableOnce[A]` inside the body -- no `.underlying` call needed.
- **`tracked` and dependent types.** A `tracked val` parameter `x: C` in a class `F` refines the constructor return type to `F { val x: x1.type }`, preserving path-dependent type information. This is inferred automatically when the parameter type has abstract type members. [-> UC-04]
- **Applied constructor types.** With modularity enabled, `C(42)` can be used as a type, expanding to `C { val v: 42 }` for `class C(tracked val v: Any)`. This provides concise syntax for refined types.
- **Refined-type parents.** Classes can now extend refined types directly; refinements are lifted into synthetic members. This lets you express module signatures as type aliases with refinements and then implement them as classes.
- **Export relaxation.** Type member exports are no longer `final`, enabling multiple traits to export the same type member and then be mixed together -- essential for aggregating type-class-like givens.

## Gotchas and limitations

1. **Named type arguments: no mixing.** You cannot mix positional and named type arguments in the same application. It is all-named or all-positional.
2. **`into` subclasses.** Subclasses of an `into`-declared type are _not_ automatically valid conversion targets. If `class C extends T` and `T` is `into`, parameters of type `C` still require a language import for conversions.
3. **`into` and type parameter instantiation.** Type parameters that are not explicitly instantiated to an `into` type do not count as valid conversion targets. For example, `List("a", "b")` where the list element type is inferred (not explicitly `into[Keyword]`) will not allow conversions on the elements.
4. **Two `into` schemes are complementary.** `into` as a type constructor gives per-parameter control (library author wraps specific parameters). `into` as a modifier gives per-type control (all parameters of that type accept conversions). Using too many `into` modifiers weakens the protection that the language import was designed to provide.
5. **`tracked` changes inferred types.** Making a case class parameter `tracked` can cause singleton types to be inferred where wider types were expected, potentially breaking assignments to mutable variables (e.g., `var x = Foo(1); x = Foo(2)` fails if `x` is inferred as `Foo { val v: 1 }`).
6. **`tracked` is not default.** For backward compatibility, `tracked` is not assumed for all `val` parameters. It is only inferred when the parameter type has abstract type members.

## Use-case cross-references

- [-> UC-04] Dependent function types: `tracked` parameters bring path-dependent typing to class constructors.
- [-> UC-05] Type class patterns: `tracked` and modularity improvements simplify the `Aux` pattern for type classes with associated types.
- [-> UC-06] Context functions: `into` parameters compose with context function types for ergonomic DSL design.
- [-> UC-22] Module composition: `SetFunctor`-style patterns replace SML functors in Scala.
- [-> UC-23] Migration: `into` provides a smooth path from Scala 2 implicit conversions to Scala 3 `Conversion` instances.
