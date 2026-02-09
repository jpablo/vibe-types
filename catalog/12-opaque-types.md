# 12 -- Opaque Type Aliases

> **Since:** Scala 3.0

## 1. What It Is

An opaque type alias introduces a new named type that is identical to its underlying representation *inside* the defining scope but appears as a completely abstract, unrelated type *outside* that scope. This provides the type-safety benefits of a wrapper class (preventing accidental mixing of semantically distinct values that share a representation) with zero runtime overhead -- no boxing, no extra allocations, no indirection. The `opaque` modifier can be applied to type aliases that are members of objects, classes, traits, or top-level definitions.

## 2. What Constraint It Lets You Express

**You can create distinct types that share the same runtime representation, making it a compile-time error to interchange them, while paying no performance cost.** Inside the defining scope, the alias is transparent (you can freely assign between the opaque type and its representation). Outside, the alias is opaque: the compiler treats it as an abstract type with only the declared upper and lower bounds visible. This gives you fine-grained control over *where* the conversion between representation and abstraction is allowed, effectively creating an abstraction barrier enforced by the type system.

## 3. Minimal Snippet

```scala
object Units:
  opaque type Meters = Double
  opaque type Seconds = Double

  object Meters:
    def apply(d: Double): Meters = d     // inside: transparent
  object Seconds:
    def apply(d: Double): Seconds = d

  extension (m: Meters)
    def value: Double = m                // inside: Meters is Double
    def +(other: Meters): Meters = m + other

val d: Units.Meters = Units.Meters(3.0)  // OK
// val bad: Double = d                   // error: found Meters, required Double
// val wrong: Units.Seconds = d          // error: found Meters, required Seconds
```

With bounds (subtype relationships visible outside):

```scala
object Access:
  opaque type Permissions = Int
  opaque type Permission <: Permissions = Int

  val Read: Permission = 1
  val Write: Permission = 2

  extension (p: Permissions)
    def has(required: Permissions): Boolean = (p & required) == required

// Outside:
val r: Access.Permissions = Access.Read  // OK -- Permission <: Permissions
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Extension methods** [-> catalog/07] | Extension methods are the standard way to define the public API of an opaque type, since you cannot add members to a type alias. Defining extensions inside the same scope lets them use the transparent view. |
| **Given instances / type classes** [-> catalog/05] | You can provide type-class instances for opaque types (e.g., `Ordering[Meters]`) inside the defining object, using the transparent alias to delegate to the underlying type's instance. |
| **Implicit conversions** [-> catalog/10] | A `Conversion[Meters, Double]` can be defined to allow controlled, explicit widening outside the scope, while keeping accidental mixing as a compile error. |
| **Multiversal equality** [-> catalog/09] | An opaque type that `derives CanEqual` gets its own equality domain; comparing `Meters == Seconds` would require an explicit `CanEqual[Meters, Seconds]` instance. |
| **Enums** [-> catalog/11] | Enums restrict inhabitants at the value level; opaque types restrict them at the type level. They compose well: an enum case can wrap an opaque type to combine both forms of constraint. |
| **Type-class derivation** [-> catalog/08] | Opaque types do not have `Mirror` instances (they are aliases, not classes), so derivation does not apply directly. You must provide type-class instances manually or delegate to the underlying type's instance. |

## 5. Gotchas and Limitations

- **Scope of transparency.** The alias is transparent in the `private[this]` scope of the enclosing class/object (or the enclosing file for top-level definitions). Nested objects and classes within the same file do *not* see through a top-level opaque type.
- **Class-based opaque types.** When an opaque type is defined inside a class (not an object), instances of different class values produce incompatible types: `log1.Logarithm` and `log2.Logarithm` are distinct types even if both instances are of the same class.
- **No context function RHS.** An opaque type alias cannot have a context function type as its right-hand side.
- **Cannot be `private`.** Opaque type aliases cannot have a `private` access modifier and cannot be overridden in subclasses.
- **Cannot be local.** Opaque types must be members of classes, traits, or objects, or top-level. They cannot appear in local blocks.
- **Equality translation.** Comparing two opaque-type values with `==` is mapped after type-checking to the equality operator of the underlying type (e.g., `Int` equality), avoiding boxing. This is correct but can surprise if you expect reference equality semantics.
- **Transparent inline methods.** If an opaque type is returned from a `transparent inline` method defined inside the opaque scope, the inlined return type may leak the underlying representation as an intersection type (e.g., `Seconds & String`). Explicit type annotations on the return expression are recommended to control this.
- **Type parameters.** Opaque types can have a single type parameter list (`opaque type F[T] = (T, T)` is valid) but cannot combine type parameters with type lambdas on the right-hand side.

## 6. Use-Case Cross-References

- [-> UC-03] Newtypes / zero-cost wrappers for domain primitives
- [-> UC-05] Units-of-measure without runtime overhead
- [-> UC-07] Encapsulation of internal representations in library APIs
- [-> UC-10] Permission systems with subtype-bounded opaque types
