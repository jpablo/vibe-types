# Structures, Inheritance, and Anonymous Constructors

> **Since:** Lean 4 (stable)

## What it is

A `structure` in Lean is a named-field product type with exactly one constructor. It is syntactic sugar for a single-constructor inductive type, but with significant ergonomic benefits: named fields, dot notation for field access, automatic projection functions, a `{ field := value }` construction syntax, and inheritance via `extends`. Structures are the primary way to define record types, configuration objects, and mathematical bundles in Lean.

The `extends` keyword allows a structure to inherit fields from one or more parent structures, creating a flattened record — not a subtyping hierarchy. There is no runtime dispatch; `extends` simply copies fields from the parent and adds a coercion [→ T18](T18-conversions-coercions.md).

## What constraint it enforces

**A structure has exactly one constructor; all fields must be provided at construction. `extends` creates compile-time field inheritance with automatic coercions.**

More specifically:

- **All fields required.** Every field must be supplied when constructing a structure instance (unless a default value is declared). The compiler rejects construction with missing fields.
- **Single constructor.** Unlike inductive types with multiple variants, a structure always has exactly one shape. Pattern matching is trivially exhaustive.
- **Inheritance is flattening.** `extends` copies parent fields into the child. The compiler generates coercions from child to parent automatically.
- **Field access is type-safe.** Dot notation (`s.field`) resolves to the correct projection function, and the compiler rejects access to nonexistent fields.

## Minimal snippet

```lean
structure Point where
  x : Float
  y : Float

def origin : Point := { x := 0.0, y := 0.0 }  -- OK: all fields provided
-- def bad : Point := { x := 0.0 }              -- error: missing field 'y'

def dist (p : Point) : Float :=
  Float.sqrt (p.x * p.x + p.y * p.y)  -- OK: dot notation
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Inductive Types** [→ T01](T01-algebraic-data-types.md) | A structure is a single-constructor inductive type. Multi-variant data requires `inductive` instead. |
| **Type Classes** [→ T05](T05-type-classes.md) | Type classes are structures with the `class` keyword. Instance resolution is built on structure inheritance. |
| **Coercions** [→ T18](T18-conversions-coercions.md) | `extends` generates coercions automatically. You can also declare custom `Coe` instances on structures. |
| **Auto-Bound Implicits** [→ T38](T38-implicits-auto-bound.md) | Structure fields can use auto-bound implicit syntax for polymorphic fields. |
| **Opaque Definitions** [→ T21](T21-encapsulation.md) | Making a structure `opaque` prevents field access from outside the module. |

## Gotchas and limitations

1. **No inheritance polymorphism.** `extends` is field copying, not subtyping. A function taking `Point` does not accept `Point3D extends Point` directly — but the auto-generated coercion makes it *look* like it does. The coercion inserts a field extraction, not an identity cast.

2. **Default field values.** Fields can have defaults: `field : Type := defaultValue`. Omitting a field with a default is fine; omitting one without a default is an error.

3. **Anonymous constructor syntax.** `⟨val1, val2⟩` works for structures with positional fields, but is fragile if fields are reordered. Prefer `{ field := value }` for clarity.

4. **Diamond inheritance.** When extending multiple structures that share a common ancestor, Lean flattens the fields but may create duplicates. You may need to disambiguate with `toParent` accessors.

5. **`deriving` support.** Structures can derive instances (`deriving Repr, BEq, Hashable`), but not all derivation handlers support structures with `extends`.

## Beginner mental model

Think of a structure as a **named bag of fields** — like a Rust `struct` with named fields. Construction requires filling every slot. `extends` works like copy-pasting the parent's fields into the child, plus adding an automatic conversion back to the parent type.

Coming from Rust: `structure` ≈ `struct` with named fields. There's no `enum`-like variant support — use `inductive` for that. `extends` has no Rust equivalent; it's closer to Go's struct embedding.

## Example A — Configuration with defaults

```lean
structure Config where
  host : String := "localhost"
  port : Nat := 8080
  verbose : Bool := false

def myConfig : Config := { port := 3000 }  -- OK: host and verbose use defaults
```

## Example B — Inheritance via extends

```lean
structure Animal where
  name : String
  legs : Nat

structure Dog extends Animal where
  breed : String

def rex : Dog := { name := "Rex", legs := 4, breed := "Labrador" }

-- Auto-generated coercion: Dog → Animal
def greet (a : Animal) : String := s!"Hello, {a.name}!"
#eval greet rex  -- OK: coercion from Dog to Animal applied automatically
```

## Common compiler errors and how to read them

### `missing field`

```
missing field 'y'
```

**Meaning:** You constructed a structure without providing a required field. Add the missing field or declare a default in the structure definition.

### `unknown field`

```
unknown field 'z' for structure 'Point'
```

**Meaning:** You tried to set a field that doesn't exist. Check the structure definition for the correct field names.

### `type mismatch` on construction

```
type mismatch
  "hello"
has type
  String : Type
but is expected to have type
  Nat : Type
```

**Meaning:** A field value has the wrong type. Check the structure definition for the expected type of each field.

## Proof perspective (brief)

Structures are single-constructor inductive types, which in type theory are *product types* (Σ-types where no component depends on the others, or simple record types). In Mathlib, structures are the backbone of the algebraic hierarchy: `Group`, `Ring`, `TopologicalSpace` are all structures that extend each other. The `extends` mechanism creates a clean inheritance chain with automatic coercions, making it natural to say "every ring is a group."

## Use-case cross-references

- [→ UC-02](../usecases/UC02-domain-modeling.md) — Structures model domain entities with named fields and compile-time field requirements.
- [→ UC-08](../usecases/UC10-encapsulation.md) — Private fields and opaque structures control what leaks across module boundaries.

## Source anchors

- *Functional Programming in Lean* — "Structures"
- *Theorem Proving in Lean 4* — Ch. 7 "Inductive Types" (Structures section)
- Lean 4 source: `Lean.Elab.Structure`
