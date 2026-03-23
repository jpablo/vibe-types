# Dependent Types (via Path-Dependent and Match Types)

> **Since:** Scala 2 (path-dependent types); Scala 3.0 (match types, singleton types, dependent function types)

## What it is

Scala 3 does not have **full dependent types** in the sense of Lean, Idris, or Agda — there is no way to index types by arbitrary runtime values or write type-level proofs about integers. However, Scala 3 provides a powerful combination of features that **approximates** many dependent-type patterns:

- **Path-dependent types** (`x.T`) — a type that depends on which object `x` refers to.
- **Match types** — type-level pattern matching that computes result types from input types.
- **Singleton types** — literal values (`42`, `"hello"`) promoted to the type level.
- **Dependent function types** — `(x: A) => x.T`, where the return type depends on the argument's path.
- **Inline + compiletime ops** — `constValue`, `constValueTuple`, `erasedValue`, and arithmetic on singleton types enable limited value-level computation at the type level.

Together, these features let you express "the type of the output depends on the value (or type) of the input" — the core idea of dependent typing — within the constraints of JVM erasure.

## What constraint it enforces

**Scala's dependent-type approximation lets you tie output types to input values (via paths) or input types (via match types), so the compiler can verify relationships that would require a full dependent type system in other languages — within the limits of what the JVM can erase at runtime.**

## Minimal snippet

```scala
// Path-dependent: return type depends on the argument
trait Key:
  type Value

val age: Key { type Value = Int } = new Key { type Value = Int }
val name: Key { type Value = String } = new Key { type Value = String }

def get(k: Key): k.Value = ??? // dependent method type

// Match type: output type computed from input type
type Unpacked[T] = T match
  case Option[t] => t
  case List[t]   => t
  case _         => T

val x: Unpacked[Option[Int]] = 42      // Int
val y: Unpacked[String]      = "hello" // String

// Singleton types + compiletime: type-level arithmetic
import scala.compiletime.ops.int.*

type Three = 3
type Four  = 4
type Seven = Three + Four  // type-level 7

val seven: Seven = 7  // only 7 is accepted
```

## What you CAN do vs. what you CANNOT

| Pattern | Scala 3 support | Lean / Idris comparison |
|---------|-----------------|------------------------|
| Return type depends on argument's type member | Path-dependent types — full support | N/A (different mechanism) |
| Type chosen by pattern matching on a type | Match types — full support | Analogous to type families |
| Fixed-length vectors `Vec[N, A]` | Singleton types + match types — partial (no induction on values, must use type-level Nats or literal ints) | Nat-indexed vectors with full proofs |
| Proofs about arithmetic (e.g., `n + m == m + n`) | Not supported — no proof terms, no dependent elimination | Core capability |
| Refinement predicates (e.g., `{x: Int \| x > 0}`) | No built-in refinement types (use opaque types + smart constructors as a workaround) | Supported via propositions-as-types |
| Type-safe printf | Match types on singleton string types — possible but fragile | Straightforward with dependent types |

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Path-dependent types** [-> catalog/T53](T53-path-dependent-types.md) | The primary mechanism for value-dependent typing. A method `def f(k: Key): k.Value` is a dependent method — its return type depends on the argument. |
| **Match types** [-> catalog/T41](T41-match-types.md) | Provide type-level computation: given a type, compute another type. This is the closest Scala gets to type families or type-level functions. |
| **Literal / singleton types** [-> catalog/T52](T52-literal-types.md) | Promote values to types (`42` becomes type `42`). Essential for type-level arithmetic and const-generic-style patterns. |
| **Compile-time operations** [-> catalog/T15](T15-const-generics.md) | `scala.compiletime.ops` provides type-level arithmetic on singletons: `+`, `*`, `<`, etc. This is Scala's analogue to const generics with arithmetic. |

## Gotchas and limitations

1. **No value-indexed types.** You cannot write `Vec(n, A)` where `n` is a runtime `Int`. You must use a singleton type (`val n: 3 = 3`) or an opaque encoding. True runtime-dependent types are beyond Scala's type system.

2. **Match types can get stuck.** When the scrutinee is abstract, the compiler cannot reduce the match type. This limits the composability of type-level computations across generic boundaries.

3. **No proof terms.** Scala has no equivalent of Lean's `Prop` or Idris's `=` type. You cannot construct or pattern-match on proofs of type equalities or arithmetic properties.

4. **Erasure.** All these type-level tricks are erased at runtime. A `Vec[3, Int]` and a `Vec[5, Int]` are the same type at the JVM level. Runtime checks require explicit evidence (e.g., `TypeTest`).

5. **Path stability.** Only stable paths (`val`, `object`, `this`) can appear in dependent types. A `def` or `var` result is not a stable path, so `def getKey: Key` does not enable dependent typing on its result.

6. **Limited type-level recursion.** Recursive match types can diverge. The compiler has a recursion limit and cannot prove termination in general.

## Beginner mental model

Imagine a vending machine with typed slots. In most languages, every slot dispenses the same type: "snack." With dependent types, each slot can dispense a *different* type — slot A gives chips, slot B gives a drink — and the compiler knows which type you get based on which button you press. Scala 3 lets you build this machine using path-dependent types (each button is an object with its own `type Output`) and match types (the compiler looks at which button type you pressed and computes the output type).

## Example A — Type-safe heterogeneous map

```scala
trait TypedKey:
  type Value

object Name extends TypedKey:
  type Value = String

object Age extends TypedKey:
  type Value = Int

class TypedMap(private val underlying: Map[TypedKey, Any]):
  def get(k: TypedKey): Option[k.Value] =
    underlying.get(k).map(_.asInstanceOf[k.Value])

  def put(k: TypedKey)(v: k.Value): TypedMap =
    TypedMap(underlying.updated(k, v))

val m = TypedMap(Map.empty)
  .put(Name)("Alice")
  .put(Age)(30)

val n: Option[String] = m.get(Name)  // compiler knows it's String
val a: Option[Int]    = m.get(Age)   // compiler knows it's Int
// m.put(Age)("thirty")              // compile error
```

## Example B — Type-level list operations with match types

```scala
import scala.compiletime.ops.int.*

// Type-level length of a tuple
type Length[T <: Tuple] <: Int = T match
  case EmptyTuple => 0
  case _ *: rest  => 1 + Length[rest]

// Compile-time verified
summon[Length[(Int, String, Boolean)] =:= 3]

// Type-level append
type Append[Xs <: Tuple, Y] <: Tuple = Xs match
  case EmptyTuple => Y *: EmptyTuple
  case x *: rest  => x *: Append[rest, Y]

summon[Append[(Int, String), Boolean] =:= (Int, String, Boolean)]
```

## Sigma types

In Lean, a Sigma type `(a : α) × β a` packages a value with a type that depends on it — an 'existential with path.' Scala approximates this with path-dependent types: a trait with an abstract type member `type T` and a value `val t: T` packages a value whose type is instance-dependent. This is the encoding behind type-safe heterogeneous maps (`Key { type Value = Int }`).

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) Path-dependent types and singleton types prevent invalid key-value combinations at compile time.
- [-> UC-12](../usecases/UC12-compile-time.md) Match types and compiletime ops move computation to compile time, catching errors before runtime.

## Source anchors

- [Scala 3 Reference -- Match Types](https://docs.scala-lang.org/scala3/reference/new-types/match-types.html)
- [Scala 3 Reference -- Dependent Function Types](https://docs.scala-lang.org/scala3/reference/new-types/dependent-function-types.html)
- [Scala 3 Reference -- Literal Types](https://docs.scala-lang.org/scala3/reference/new-types/literal-types.html)
- [Scala 3 Reference -- compiletime Operations](https://docs.scala-lang.org/scala3/reference/metaprogramming/compiletime-ops.html)
