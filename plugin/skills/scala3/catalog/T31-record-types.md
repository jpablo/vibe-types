# Record Types & Data Modeling

> **Since:** Scala 3.0 | **Latest changes:** Scala 3.7 (named tuples)

## What it is

Scala 3's primary record type is the **case class**: a nominal product type that automatically derives `equals`, `hashCode`, `toString`, `copy`, and an `unapply` extractor for pattern matching. For lightweight, anonymous records, Scala 3.7 introduces **named tuples** (`(name: String, age: Int)`) -- structural product types where fields are accessed by name with zero overhead (names exist only at compile time). Plain **tuples** (`(A, B, C)`) provide positional product types of arbitrary arity. Together, these three mechanisms cover the full spectrum of data modeling: from named, schema-enforced domain objects (case classes) to ad-hoc data bundles (named tuples) to anonymous positional groupings (tuples).

## What constraint it lets you express

**Record types let you declare the exact shape of data -- which fields exist, what types they have, and what operations are automatically available -- so that the compiler rejects any code that misuses, omits, or confuses fields.** Case classes enforce a named schema with nominal identity; named tuples enforce a named schema with structural identity; plain tuples enforce only positional arity and types.

## Minimal snippet

**Case class (the standard record type):**

```scala
case class User(name: String, age: Int, email: String)

val alice = User("Alice", 30, "alice@example.com")

// Auto-derived members:
alice.toString    // "User(Alice,30,alice@example.com)"
alice == User("Alice", 30, "alice@example.com")  // true (structural equality)
alice.hashCode    // consistent with equals

// Copy with named modifications:
val older = alice.copy(age = 31)

// Pattern matching via auto-generated unapply:
alice match
  case User(name, age, _) => s"$name is $age"
```

**Named tuples (Scala 3.7+):**

```scala
type Point = (x: Double, y: Double)

val origin: Point = (x = 0.0, y = 0.0)
origin.x    // 0.0
origin.y    // 0.0

// Named tuple pattern matching:
origin match
  case (x = a, y = b) => s"($a, $b)"

// Unnamed tuple conforms by position:
val p: Point = (1.0, 2.0)  // OK
```

**Plain tuples:**

```scala
val pair: (String, Int) = ("Alice", 30)
pair._1   // "Alice"
pair._2   // 30

// Arbitrary arity (not limited to 22 in Scala 3):
val big: (Int, Int, Int, Int, Int) = (1, 2, 3, 4, 5)
```

**Case class vs. named tuple -- key differences:**

```scala
case class Coord(x: Double, y: Double)
type CoordT = (x: Double, y: Double)

val a = Coord(1.0, 2.0)
val b: CoordT = (x = 1.0, y = 2.0)

// Case class: nominal -- Coord is a distinct type
// Named tuple: structural -- CoordT is (x: Double, y: Double)

// a == b  // does not compile: different types
```

## Interaction with other features

| Feature | How it composes |
|---|---|
| **ADTs / enums** [-> catalog/T01](T01-algebraic-data-types.md) | Case classes are the product cases of algebraic data types. An `enum` with parameterized cases creates a sum of case-class products. |
| **Type-class derivation** [-> catalog/T06](T06-derivation.md) | `case class User(...) derives Eq, Show, JsonCodec` triggers automatic derivation via `Mirror.Product`. Named tuples do not have `Mirror` instances. |
| **Opaque types** [-> catalog/T03](T03-newtypes-opaque.md) | Named tuples are implemented as opaque types internally: `opaque type NamedTuple[N <: Tuple, +V <: Tuple] >: V = V`. Names are erased at runtime. |
| **Structural types** [-> catalog/T07](T07-structural-typing.md) | Named tuples bridge nominal and structural typing: `NamedTuple.From[User]` extracts the named tuple type corresponding to a case class, enabling typed query DSLs. |
| **Pattern matching** [-> catalog/T14](T14-type-narrowing.md) | Case classes auto-generate `unapply` for destructuring. Named tuples support both named and positional pattern matching. |
| **Multiversal equality** [-> catalog/T20](T20-equality-safety.md) | `case class Foo(...) derives CanEqual` restricts `==` to same-type comparisons, preventing accidental equality between unrelated case classes. |

## Gotchas and limitations

1. **Case class equality is structural, not referential.** Two case class instances with the same field values are `==`. This is usually desired but can surprise when used as map keys with mutable fields (don't put mutable fields in case classes).
2. **`copy` and default arguments.** The `copy` method uses named arguments. Adding a field to a case class does not break existing `copy` calls that use named parameters, but adding a field *before* existing positional parameters does.
3. **Case class inheritance is restricted.** A case class cannot extend another case class. This is intentional: inheritance + auto-generated equality is unsound (the "equals-hashCode contract" problem).
4. **Named tuple field ordering matters.** `(name: String, age: Int)` and `(age: Int, name: String)` are different, incompatible types. Unlike Python's `TypedDict`, field order is significant.
5. **Named tuples cannot mix named and unnamed.** All elements must be named or all must be unnamed. `(name: String, Int)` is illegal.
6. **No custom methods on named tuples.** Named tuples are structural -- you cannot add methods or implement traits. For behavior, use case classes.
7. **Pattern matching exhaustiveness.** Case classes in sealed hierarchies get exhaustiveness checking. Named tuples and plain tuples do not participate in sealed hierarchies.

## Beginner mental model

Think of Scala's record types as three levels of formality:

- **Case class**: a formal, named data type. Like a database table with a schema -- it has a name, typed fields, equality, pattern matching, and can implement traits. Use this for domain models.
- **Named tuple**: a quick, ad-hoc labeled bundle. Like a Python `namedtuple` or TypeScript `{ name: string, age: number }` -- lightweight, structural, no ceremony. Use this for return values and intermediate data.
- **Plain tuple**: a positional grab-bag. Like returning `(Int, String)` -- fast and minimal, but fields have no names. Use this for trivial multi-return.

For comparison with other languages:
- Python's `@dataclass` is closest to Scala's `case class` (named, with auto-generated methods).
- Python's `TypedDict` is closest to named tuples (structural, dict-like).
- TypeScript's `interface`/`type` objects are structural like named tuples, but with methods.

## Common type-checker errors

```
-- [E007] Type Mismatch Error ---
  case class Celsius(value: Double)
  case class Fahrenheit(value: Double)

  val temp: Celsius = Fahrenheit(72.0)
                      ^^^^^^^^^^^^^^^^
  Found:    Fahrenheit
  Required: Celsius

  Note: case classes are nominal -- same fields does not mean same type.
```

```
-- Error ---
  case class A(x: Int)
  case class B(x: Int) extends A(x)
                                ^
  case class B may not extend another case class

  Fix: use a common trait instead:
    sealed trait HasX { def x: Int }
    case class A(x: Int) extends HasX
    case class B(x: Int) extends HasX
```

```
-- Error ---
  type Rec = (name: String, 42)
                            ^^
  Illegal combination of named and unnamed tuple elements

  Fix: all elements must be named or all must be unnamed:
    type Rec = (name: String, id: Int)
```

## Use-case cross-references

- [-> UC-02](../usecases/UC02-domain-modeling.md) Domain modeling with case classes as the primary record type
- [-> UC-01](../usecases/UC01-invalid-states.md) Making invalid states unrepresentable with sealed case class hierarchies
- [-> UC-09](../usecases/UC09-builder-config.md) Named tuples for lightweight configuration records
- [-> UC-19](../usecases/UC19-serialization.md) Deriving JSON codecs for case classes via type-class derivation
- [-> UC-12](../usecases/UC12-compile-time.md) `NamedTuple.From` for compile-time schema extraction

## Source anchors

- [Scala 3 Reference: Case Classes](https://docs.scala-lang.org/scala3/book/domain-modeling-tools.html#case-classes)
- [Scala 3 Reference: Named Tuples](https://docs.scala-lang.org/scala3/reference/experimental/named-tuples.html)
- [Scala 3 Reference: Tuples](https://docs.scala-lang.org/scala3/reference/new-types/tuple-types.html)
- [Scala 3 Reference: Enums / ADTs](https://docs.scala-lang.org/scala3/reference/enums/adts.html)
