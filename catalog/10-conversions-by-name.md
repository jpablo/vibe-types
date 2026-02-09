# 10 -- Implicit Conversions, By-Name Context Parameters, and Deferred Givens

## 1. What It Is

This document covers three related mechanisms for controlling how the compiler resolves and provides implicit evidence:

- **Implicit conversions** in Scala 3 are given instances of the `scala.Conversion[-T, +U]` abstract class. When the compiler encounters a value of type `T` where a `U` is expected (or where `T` has no member `m` but `U` does), it applies the conversion automatically. Unlike Scala 2's `implicit def`, the `Conversion` type class makes conversions explicit, discoverable, and import-controlled.

- **By-name context parameters** (`=> T` in a `using` clause) let the compiler defer evaluation of a given argument and, crucially, break cycles during implicit search. The synthesized argument is backed by a local `lazy val` only when self-reference would otherwise diverge.

- **Deferred givens** (`given T = deferred`) allow a trait to declare a given whose implementation is filled in automatically by any inheriting class, either by forwarding a constructor-supplied using parameter or by implicit search in the subclass's scope.

## 2. What Constraint It Lets You Express

**You can control implicit widening (which types may silently convert to which), break circular given dependencies with lazy evidence, and propagate type-class requirements through trait hierarchies without boilerplate.**

- `Conversion[T, U]` constrains *which* automatic coercions the compiler may perform: only those backed by an explicit given instance.
- By-name context parameters constrain *when* evidence is materialized, allowing recursive or mutually dependent given structures (e.g., `Codec[Option[T]]` depending on `Codec[T]`) to terminate.
- Deferred givens constrain *where* a given is provided: the trait declares the requirement; the implementing class satisfies it -- either explicitly or via the compiler synthesizing it from the class's own scope.

## 3. Minimal Snippet

**Implicit conversion:**

```scala
case class Token(value: String)

given Conversion[String, Token] = Token(_)

val t: Token = "hello"   // OK -- Conversion[String, Token] applied
```

**By-name context parameter:**

```scala
trait Codec[T]:
  def write(x: T): Unit

given intCodec: Codec[Int] = ???

given optionCodec: [T] => (ev: => Codec[T]) => Codec[Option[T]]:
  def write(xo: Option[T]) = xo match
    case Some(x) => ev.write(x)  // ev evaluated on demand
    case None    =>
```

**Deferred given:**

```scala
trait Sorted:
  type Element : Ord           // desugars to: given Ord[Element] = deferred

class SortedSet[A : Ord] extends Sorted:
  type Element = A
  // compiler auto-fills: override given Ord[Element] = <from using clause>
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Given instances / using clauses** [-> catalog/05] | `Conversion` instances are givens and follow all normal scoping, import, and priority rules. By-name context parameters are a modifier on `using` clauses. |
| **Extension methods** [-> catalog/07] | When `T` has no member `m`, the compiler tries extension methods *and* implicit conversions to a type with `m`. Conversions are tried after extensions fail. |
| **Opaque types** [-> catalog/12] | You can define a `Conversion` from an opaque type's companion to allow controlled widening while keeping the underlying type hidden. |
| **Type-class derivation** [-> catalog/08] | Recursive derivation (e.g., deriving `Eq` for a recursive ADT) relies on by-name context parameters to prevent the implicit search from diverging. |
| **Context bounds in traits** | Context bounds on abstract type members desugar to deferred givens. This lets traits declare type-class requirements that subclasses satisfy through their own constructor parameters. |

## 5. Gotchas and Limitations

### Conversions
- **Import requirement.** Using `Conversion` instances triggers a feature warning unless `scala.language.implicitConversions` is imported (or the `-language:implicitConversions` flag is set).
- **Three trigger points.** Conversions fire on type mismatch, missing member, and inapplicable member. This is the same as Scala 2, but the `Conversion` type class makes the mechanism more visible.
- **Magnet pattern.** Conversions can simulate overloading via a "magnet" enum, useful when normal overloading is impossible (e.g., erased generic parameters).

### By-name context parameters
- **Not immediately available.** The placeholder given created during search is not a candidate for the current level of implicit resolution. It only becomes available in *nested* by-name searches. This is what prevents infinite loops.
- **Lazy val only when needed.** The compiler backs the synthesized argument with a `lazy val` only if the expansion is self-referential; otherwise, the argument is evaluated directly.

### Deferred givens
- **Override modifier required.** Because `deferred` counts as a concrete right-hand side, any explicit implementation in a subclass must use `override`.
- **Replaces abstract givens.** Abstract givens (`given name: T` with no body) are still supported but are considered superseded by deferred givens as of Scala 3.6.
- **Search scope.** The synthesized implementation is searched for in the inheriting class's environment augmented by its parameters, but *not* its own members (to avoid circular resolution).

## 6. Use-Case Cross-References

- [-> UC-03] Controlled coercion between newtypes and underlying representations
- [-> UC-04] Recursive codec derivation with by-name evidence
- [-> UC-08] Trait-level type-class requirements via deferred givens
- [-> UC-11] Magnet-pattern APIs with Conversion instances
