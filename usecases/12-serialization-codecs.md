# Serialization Codecs

## The Constraint

Derive serializers and deserializers automatically with full type safety. Every field and variant must be accounted for at compile time — no missing-field surprises at runtime.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| Type class derivation (`derives`) | One-keyword automatic codec generation for ADTs | [-> catalog/08](../catalog/08-type-class-derivation.md) |
| Mirror (ProductOf / SumOf) | Compiler-generated structural descriptions for manual derivation | [-> catalog/08](../catalog/08-type-class-derivation.md) |
| Inline / compiletime | Compile-time iteration over fields; zero-overhead serialization | [-> catalog/17](../catalog/17-inline-compiletime.md) |
| Macros | Full compile-time code generation when inline is insufficient | [-> catalog/18](../catalog/18-macros-quotes.md) |
| Match types | Compute codec types from structure (e.g., field type -> wire format) | [-> catalog/03](../catalog/03-match-types.md) |

## Patterns

### 1 — `derives` for automatic codec derivation

The simplest path: declare a type class with a `derived` method, then attach it with `derives`.

```scala
trait JsonCodec[A]:
  def encode(a: A): String
  def decode(s: String): Either[String, A]

// Library provides the derived macro/inline
// Usage is a single keyword:
case class User(name: String, age: Int) derives JsonCodec

enum Role derives JsonCodec:
  case Admin, Editor, Viewer

val json = summon[JsonCodec[User]].encode(User("Ada", 36))
```

### 2 — Mirror.ProductOf / Mirror.SumOf for manual derivation

Build a generic codec by inspecting the compile-time structure via `Mirror`.

```scala
import scala.deriving.Mirror
import scala.compiletime.{erasedValue, summonInline}

trait Encoder[A]:
  def encode(a: A): Map[String, Any]

object Encoder:
  given Encoder[String] with
    def encode(a: String) = Map("value" -> a)
  given Encoder[Int] with
    def encode(a: Int) = Map("value" -> a)

  inline given derived[A](using m: Mirror.ProductOf[A]): Encoder[A] =
    new Encoder[A]:
      def encode(a: A): Map[String, Any] =
        val elems  = a.asInstanceOf[Product].productIterator.toList
        val labels = labelsOf[m.MirroredElemLabels]
        labels.zip(elems).toMap

  inline def labelsOf[T <: Tuple]: List[String] =
    inline erasedValue[T] match
      case _: EmptyTuple     => Nil
      case _: (head *: tail) =>
        scala.compiletime.constValue[head].toString :: labelsOf[tail]

case class Point(x: Int, y: Int) derives Encoder

val m = summon[Encoder[Point]].encode(Point(1, 2))
// Map("x" -> 1, "y" -> 2)
```

### 3 — Inline-based serializer without macros

Use `inline` and `compiletime` to unroll field access at compile time — no reflection, no macros.

```scala
import scala.compiletime.{erasedValue, summonInline, constValue}

trait Write[A]:
  def write(a: A): String

object Write:
  given Write[Int]    with { def write(a: Int)    = a.toString }
  given Write[String] with { def write(a: String) = s""""$a"""" }

  inline def writeElems[Ts <: Tuple, Ls <: Tuple](p: Product, i: Int): List[String] =
    inline (erasedValue[Ts], erasedValue[Ls]) match
      case _: (EmptyTuple, EmptyTuple) => Nil
      case _: (t *: ts, l *: ls) =>
        val label  = constValue[l].toString
        val writer = summonInline[Write[t]]
        val value  = writer.write(p.productElement(i).asInstanceOf[t])
        s""""$label":$value""" :: writeElems[ts, ls](p, i + 1)

  inline given derived[A](using m: scala.deriving.Mirror.ProductOf[A]): Write[A] =
    (a: A) =>
      val fields = writeElems[m.MirroredElemTypes, m.MirroredElemLabels](
        a.asInstanceOf[Product], 0
      )
      fields.mkString("{", ",", "}")

case class Config(host: String, port: Int) derives Write

val json = summon[Write[Config]].write(Config("localhost", 8080))
// {"host":"localhost","port":8080}
```

### 4 — Compile-time schema validation

Use match types to verify at compile time that a type's structure matches an expected schema.

```scala
import scala.compiletime.ops.int.*

type FieldCount[A](using m: scala.deriving.Mirror.ProductOf[A]) =
  scala.Tuple.Size[m.MirroredElemTypes]

type HasAtLeast[A, N <: Int](using m: scala.deriving.Mirror.ProductOf[A]) =
  scala.Tuple.Size[m.MirroredElemTypes] >= N =:= true

// Constrain a codec to only work on types with >= 2 fields
inline def toCsv[A](a: A)(
  using m: scala.deriving.Mirror.ProductOf[A],
        ev: scala.Tuple.Size[m.MirroredElemTypes] >= 2 =:= true
): String =
  a.asInstanceOf[Product].productIterator.mkString(",")

case class Row(id: Int, name: String, score: Int)
toCsv(Row(1, "Ada", 100))     // compiles — 3 fields >= 2
// case class Solo(x: Int)
// toCsv(Solo(1))              // compile error — 1 field < 2
```

## Scala 2 Comparison

| Technique | Scala 2 | Scala 3 |
|---|---|---|
| Automatic derivation | Shapeless `Generic` + `LabelledGeneric`; complex implicit chains | `derives` keyword + `Mirror` — built into the language |
| Field iteration | `HList` folding with `Poly`; steep learning curve | `inline erasedValue` + `Tuple` — reads like normal Scala |
| Sum type derivation | `Generic.Aux[A, Repr]` with `Coproduct` | `Mirror.SumOf` with `ordinal`; `enum` seals the hierarchy |
| Compile-time reflection | Macro-based `TypeTag`, `WeakTypeTag` — fragile across versions | `Mirror` + `constValue` — stable compiler API |
| Zero-overhead codecs | Required macro annotations (e.g., `@JsonCodec`) | `inline` unrolling — no macro annotation needed |

## When to Use Which Feature

**Use `derives`** as the default. If a library supports it, a single keyword gives you a codec with no boilerplate. This covers the vast majority of product and sum types.

**Use `Mirror` directly** when you are building a codec library or need custom derivation logic (renaming fields, skipping defaults, transforming enums). `Mirror.ProductOf` and `Mirror.SumOf` give you the structural metadata.

**Use `inline` + `compiletime`** when performance matters and you want zero-reflection, zero-allocation codecs. The compiler unrolls field access into straight-line code.

**Reach for macros** when inline derivation hits limitations — e.g., generating companion objects, producing custom error messages, or handling recursive types that exceed inline recursion depth.

**Use match types** for schema-level constraints (minimum field counts, field type restrictions) that should be enforced before the codec is even instantiated.
