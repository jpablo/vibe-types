# Structures, Inheritance, and Anonymous Constructors

> **Since:** Lean 4 (stable)

## What it is

A `structure` in Lean is a named-field product type with exactly one constructor. It is syntactic sugar for a single-constructor inductive type, but with significant ergonomic benefits: named fields, dot notation for field access, automatic projection functions, a `{ field := value }` construction syntax, and inheritance via `extends`. Structures are the primary way to define record types, configuration objects, and mathematical bundles in Lean.

The `extends` keyword allows a structure to inherit fields from one or more parent structures, creating a flattened record — not a subtyping hierarchy. There is no runtime dispatch, and — for plain structures — no coercion either: `extends` copies the parent's fields in and generates a *projection* `Child.toParent`. If you want a child to be usable where the parent is expected, you register that projection as a `Coe` instance yourself [→ T18](T18-conversions-coercions.md). (Type *classes* declared with `extends` are the exception: there the parent projection is registered as an instance, which is why instance search finds it automatically.)

## What constraint it enforces

**A structure has exactly one constructor; all fields must be provided at construction. `extends` creates compile-time field inheritance plus a parent projection — but no implicit conversion.**

More specifically:

- **All fields required.** Every field must be supplied when constructing a structure instance (unless a default value is declared). The compiler rejects construction with missing fields.
- **Single constructor.** Unlike inductive types with multiple variants, a structure always has exactly one shape. Pattern matching is trivially exhaustive.
- **Inheritance is flattening.** `extends` copies parent fields into the child and generates the projection `Child.toParent`. It does **not** generate a coercion: passing a `Dog` where an `Animal` is expected is a hard type error until you declare `instance : Coe Dog Animal := ⟨Dog.toAnimal⟩` yourself.
- **Field access is type-safe.** Dot notation (`s.field`) resolves to the correct projection function, and the compiler rejects access to nonexistent fields.

## Minimal snippet

```lean
structure Point where
  x : Float
  y : Float

def origin : Point := { x := 0.0, y := 0.0 }  -- OK: all fields provided

def dist (p : Point) : Float :=
  Float.sqrt (p.x * p.x + p.y * p.y)  -- OK: dot notation

-- error: Fields missing: `y`
def bad : Point := { x := 0.0 }
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Inductive Types** [→ T01](T01-algebraic-data-types.md) | A structure is a single-constructor inductive type. Multi-variant data requires `inductive` instead. |
| **Type Classes** [→ T05](T05-type-classes.md) | Type classes are structures with the `class` keyword. Instance resolution is built on structure inheritance. |
| **Coercions** [→ T18](T18-conversions-coercions.md) | `extends` gives you `Child.toParent`, not a coercion. Declare `instance : Coe Child Parent := ⟨Child.toParent⟩` to make the conversion implicit. |
| **Auto-Bound Implicits** [→ T38](T38-implicits-auto-bound.md) | Structure fields can use auto-bound implicit syntax for polymorphic fields. |
| **Encapsulation** [→ T21](T21-encapsulation.md) | Mark individual fields — or the whole `structure` — `private` to keep projections from escaping the file. |

## Gotchas and limitations

1. **No inheritance polymorphism, and no coercion to paper over it.** `extends` is field copying, not subtyping. A function taking `Animal` does not accept a `Dog`:

   ```lean
   structure Animal where
     name : String
   structure Dog extends Animal where
     breed : String

   def rex : Dog := { name := "Rex", breed := "Labrador" }
   def greet (a : Animal) : String := s!"Hello, {a.name}!"

   -- error: Application type mismatch — rex has type Dog but Animal is expected
   #eval greet rex
   ```

   The fix is either `greet rex.toAnimal` or a one-line `instance : Coe Dog Animal := ⟨Dog.toAnimal⟩` (Example B). Note what the coercion does even then: it *rebuilds* an `Animal` by extracting fields — it is not an identity cast, and the `Dog`'s own fields are gone on the other side.

2. **Default field values.** Fields can have defaults: `field : Type := defaultValue`. Omitting a field with a default is fine; omitting one without a default is an error.

3. **Anonymous constructor syntax.** `⟨val1, val2⟩` works for structures with positional fields, but is fragile if fields are reordered. Prefer `{ field := value }` for clarity.

4. **Diamond inheritance.** When extending multiple structures that share a common ancestor, Lean **merges** the shared ancestor — there are no duplicate fields and no ambiguity to resolve; `d.a` below just works. What is worth knowing is the shape of the generated constructor and the resolution order:

   ```lean
   structure A where
     a : Nat
   structure B extends A where
     b : Nat
   structure C extends A where
     c : Nat
   structure D extends B, C where
     d : Nat

   #print D
   -- fields: A.a, B.b, C.c, D.d   (a appears once)
   -- constructor: D.mk (toB : B) (c d : Nat) : D
   -- field notation resolution order: D, B, C, A

   def dd : D := { a := 1, b := 2, c := 3, d := 4 }
   #eval dd.a   -- 1
   ```

   The flattened constructor bundles the *first* parent as a whole (`toB : B`) and takes the remaining fields individually, so positional `⟨…⟩` construction across an `extends` chain is easy to get wrong — another reason to prefer `{ field := value }`.

5. **`deriving` support.** Structures can derive instances (`deriving Repr, BEq, Hashable`), but not all derivation handlers support structures with `extends`.

## Beginner mental model

Think of a structure as a **named bag of fields** — like a Rust `struct` with named fields. Construction requires filling every slot. `extends` works like copy-pasting the parent's fields into the child, plus a `toParent` function that rebuilds a parent value on demand. Calling that function is your job unless you register it as a coercion.

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

-- `extends` auto-generates the projection `Dog.toAnimal`; register it as a coercion:
instance : Coe Dog Animal := ⟨Dog.toAnimal⟩

def greet (a : Animal) : String := s!"Hello, {a.name}!"
#eval greet rex  -- OK: coercion from Dog to Animal applied automatically
```

## Common compiler errors and how to read them

### ``Fields missing``

```
Fields missing: `y`

Hint: Add missing fields:
  ...
```

**Meaning:** You constructed a structure without providing a required field. Every missing field is listed at once, and 4.31 appends a code-action hint that writes the `y := _` placeholders for you. Add the missing field or declare a default in the structure definition.

### ``is not a field of structure``

```
`z` is not a field of structure `Point`
```

**Meaning:** You tried to set a field that doesn't exist. Check the structure definition for the correct field names — note the message names the *structure*, which is the fastest way to spot that you were building the wrong type.

### `Type mismatch` on construction

```
Type mismatch
  "hello"
has type
  String
but is expected to have type
  Nat
```

**Meaning:** A field value has the wrong type. Check the structure definition for the expected type of each field.

## Proof perspective (brief)

Structures are single-constructor inductive types, which in type theory are *product types* (Σ-types where no component depends on the others, or simple record types). In Mathlib, structures are the backbone of the algebraic hierarchy: `Group`, `Ring`, `TopologicalSpace` are all structures that extend each other. Because these are *classes*, the `extends` chain registers each parent projection as an instance, so "every ring is a group" is discharged by instance search rather than by any coercion — the mechanism that makes the hierarchy usable is the same one that resolves `Ring.toMonoid`.

## Use-case cross-references

- [→ UC-02](../usecases/UC02-domain-modeling.md) — Structures model domain entities with named fields and compile-time field requirements.
- [→ UC-08](../usecases/UC10-encapsulation.md) — `private` fields (and `private structure`) control what leaks across file boundaries; there is no `opaque structure`.

## Source anchors

- *Functional Programming in Lean* — "Structures"
- *Theorem Proving in Lean 4* — Ch. 7 "Inductive Types" (Structures section)
- Lean 4 source: `Lean.Elab.Structure`
