# Glossary

Key terminology used throughout this guide, with brief definitions and cross-references.

---

**ADT (Algebraic Data Type)** — A type defined as a fixed set of alternatives (sum type) or a combination of fields (product type). In Scala 3, expressed with `enum`. [-> catalog/11]

**AnyKind** — The top type for all kinds, enabling kind polymorphism. A type parameter bounded by `AnyKind` accepts types, type constructors, and higher-kinded types. [-> catalog/16]

**Capability** — In capture checking, an object or reference whose use constitutes a side effect (e.g., `IO`, file handles). Tracked in capture sets. [-> catalog/21]

**Capture Checking** — An experimental type system extension that tracks which capabilities a function may use, enabling compile-time effect tracking. [-> catalog/21]

**Capture Set** — The set of capabilities that a type may capture, written as `{c1, c2}` in capture-checked code. [-> catalog/21]

**CanEqual** — A type class that governs which pairs of types can be compared with `==` and `!=` under `strictEquality`. [-> catalog/09]

**CanThrow** — A capability type used to encode checked exceptions via the type system. A function requiring `CanThrow[E]` may throw `E`. [-> catalog/21]

**Compiletime Ops** — Type-level operations in `scala.compiletime.ops` for arithmetic, boolean, and string computation on singleton types. [-> catalog/17]

**Context Bound** — Syntactic sugar `[A: F]` meaning an implicit `F[A]` is required. In Scala 3, desugars to a `using` parameter. [-> catalog/06]

**Context Function** — A function type with implicit parameters, written `T ?=> U`. The compiler automatically provides the context argument. [-> catalog/06]

**Dependent Function Type** — A function type where the result type depends on the argument value: `(x: A) => x.Out`. [-> catalog/04]

**Derives** — A clause on a class/enum that requests automatic type class instance generation using `Mirror`. [-> catalog/08]

**Erased** — A modifier marking parameters or values that exist only at compile time and are removed by erasure. Zero runtime cost. [-> catalog/20]

**Exhaustive Checking** — The compiler's ability to verify that a pattern match covers all possible cases of a sealed type or enum. [-> catalog/11]

**Export Clause** — A declaration that makes selected members of an object or class available as members of the enclosing scope. [-> catalog/13]

**Extension Method** — A method added to a type after its definition, declared with `extension (x: T) def ...`. [-> catalog/07]

**GADT (Generalized ADT)** — An ADT where different constructors can refine the type parameter, enabling type-safe pattern matching that narrows types. [-> catalog/11]

**Given Instance** — A value declared with `given` that the compiler can supply automatically to `using` parameters. Replaces Scala 2's `implicit val/def`. [-> catalog/05]

**Higher-Kinded Type (HKT)** — A type that takes type constructors as parameters (e.g., `F[_]` where `F` is `List`, `Option`, etc.). [-> catalog/02]

**Inline** — A modifier guaranteeing that a definition is expanded at the call site at compile time. Enables compile-time computation. [-> catalog/17]

**Intersection Type** — A type `A & B` whose values must satisfy both `A` and `B`. Replaces Scala 2's compound types (`A with B`). Commutative. [-> catalog/01]

**Kind** — The "type of a type." Proper types have kind `*`, type constructors like `List` have kind `* -> *`. Kind polymorphism abstracts over kinds. [-> catalog/16]

**Match Type** — A type-level `match` expression that selects a result type based on a scrutinee type. Enables type-level computation. [-> catalog/03]

**Matchable** — A trait that marks types which can be the scrutinee of a pattern match. Used to prevent matching on opaque or erased types. [-> catalog/14]

**Mirror** — A compiler-generated type class instance (`Mirror.ProductOf`, `Mirror.SumOf`) that describes the structure of ADTs for derivation. [-> catalog/08]

**Multiversal Equality** — Scala 3's system for type-safe equality, where `==` is only allowed between types with a `CanEqual` instance. [-> catalog/09]

**Named Tuple** — A tuple with named elements: `(name: String, age: Int)`. Provides typed field access without defining a class. [-> catalog/15]

**Opaque Type** — A type alias visible only within its defining scope. Outside, it appears as a distinct type with no subtyping relationship to its representation. [-> catalog/12]

**Open Class** — A class marked `open`, explicitly allowing extension outside its defining package. Without `open`, extending requires an explicit import. [-> catalog/13]

**Phantom Type** — A type parameter used only for compile-time tracking, with no runtime representation. Can be implemented via opaque types or erased definitions. [-> catalog/12] [-> catalog/20]

**Polymorphic Function Type** — A function value with a type parameter: `[A] => A => A`. Allows universal quantification in first-class values. [-> catalog/04]

**Product Type** — A type whose values are tuples of fields (e.g., case classes). The "and" side of algebraic data types. [-> catalog/11]

**Refined Type** — A type narrowed with additional member declarations: `T { def name: String }`. [-> catalog/15]

**Selectable** — A marker trait enabling dynamic member selection on structural types, with compile-time checking. [-> catalog/15]

**Singleton Type** — A type with exactly one value, e.g., `42` (type `42`), `"hello"` (type `"hello"`). Foundation for type-level computation. [-> catalog/17]

**Structural Type** — A type defined by the methods it has rather than its class hierarchy. Uses `Selectable` or reflection for dispatch. [-> catalog/15]

**Sum Type** — A type whose values are one of several alternatives (e.g., `enum Color { case Red, Green, Blue }`). The "or" side of algebraic data types. [-> catalog/11]

**Transparent Trait** — A trait marked `transparent`, excluded from inferred types. Useful for implementation mixins that shouldn't appear in APIs. [-> catalog/13]

**Type Class** — A pattern encoding ad-hoc polymorphism: a trait `F[A]` with given instances for specific types. Core to Scala 3's contextual abstractions. [-> catalog/05] [-> catalog/07] [-> catalog/08]

**Type Class Derivation** — Automatic generation of type class instances for ADTs based on their product/sum structure, using `derives` and `Mirror`. [-> catalog/08]

**Type Lambda** — An anonymous type function: `[X] =>> F[X]`. Used where a type constructor is needed but no named alias exists. [-> catalog/02]

**TypeTest** — A type class enabling safe type tests in pattern matching, replacing `ClassTag` for this purpose. [-> catalog/14]

**Union Type** — A type `A | B` whose values may be either `A` or `B`. No common supertype required. Commutative. [-> catalog/01]

**Using Clause** — A parameter clause marked `using`, requesting the compiler to fill in the argument from given instances in scope. Replaces `implicit` parameters. [-> catalog/05]
