# Runtime Polymorphism (via Coercions and Type Classes)

> **Since:** Lean 4 (stable)

## What it is

Lean does not have trait objects or vtable-based dynamic dispatch in the Rust/Java sense. However, OOP-style runtime polymorphism — heterogeneous collections, dynamic dispatch over different concrete types — can be achieved through a combination of:

- **A common structure** (sum type or wrapper) that erases the concrete type
- **Coercions** (`Coe` type class) for automatic upcasting from concrete to abstract types
- **Type classes** for ad-hoc polymorphism (different behavior per type)

The pattern separates *data* (individual structures for each variant) from *behavior* (a type class defining operations), then uses coercions to unify them into a common type for heterogeneous use.

## What constraint it enforces

**All operations on the polymorphic value must go through the unified interface. The concrete type is erased — you can only use operations defined on the common type or type class, not concrete-type-specific methods.**

## Minimal snippet

```lean
-- Data types
structure Circle where radius : Float
structure Rectangle where width : Float; height : Float

-- Common "base type" (sum or structure)
inductive Shape where
  | circle    : Circle → Shape
  | rectangle : Rectangle → Shape

-- Automatic upcasting via Coe
instance : Coe Circle Shape := ⟨Shape.circle⟩
instance : Coe Rectangle Shape := ⟨Shape.rectangle⟩

-- Behavior as a type class
class HasArea (α : Type) where
  area : α → Float

instance : HasArea Circle where
  area c := Float.pi * c.radius * c.radius

instance : HasArea Rectangle where
  area r := r.width * r.height

instance : HasArea Shape where
  area s := match s with
    | .circle c    => HasArea.area c
    | .rectangle r => HasArea.area r

-- Heterogeneous collection with dynamic dispatch
def shapes : List Shape := [Circle.mk 3.0, Rectangle.mk 4.0 5.0]
#eval shapes.map HasArea.area  -- [28.27, 20.0]
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type classes** [-> catalog/T05](T05-type-classes.md) | Type classes define the polymorphic interface. Each concrete type provides its own instance — this is ad-hoc polymorphism. |
| **Coercions** [-> catalog/T18](T18-conversions-coercions.md) | `Coe` instances enable automatic conversion from concrete types to the common wrapper, making heterogeneous lists feel natural. |
| **Inductive types** [-> catalog/T01](T01-algebraic-data-types.md) | The common `Shape` type is an inductive — a closed sum. To support open extension, use a type class + existential encoding instead. |
| **Encapsulation** [-> catalog/T21](T21-encapsulation.md) | The concrete type can be hidden behind `opaque` or module boundaries, exposing only the polymorphic interface. |

## Gotchas and limitations

1. **Closed vs open.** An `inductive Shape` is closed — adding a new variant requires modifying the definition. For open extension (plugin-style), use a type class with an existential wrapper or a function record.

2. **No implicit vtable.** Lean doesn't generate vtables. The "dispatch" is an explicit `match` on the sum type or a type class instance lookup at the call site. For the inductive approach, adding a variant means updating every `match`.

3. **No inheritance hierarchy.** Lean's `extends` on structures is single-inheritance for *data layout*, not for polymorphic dispatch. Combining multiple "interfaces" uses multiple type class constraints, not multiple inheritance.

4. **Existential encoding for open dispatch.** For truly open runtime dispatch (like Rust's `dyn Trait`), use:
   ```lean
   structure DynShape where
     impl : Type
     val  : impl
     ops  : HasArea impl
   ```
   This packages a value with its type class instance, erasing the concrete type.

5. **Performance.** Inductive-based dispatch compiles to efficient match/branch. Existential encoding involves an extra indirection but avoids recompilation when adding types.

## Beginner mental model

In OOP, you write `class Circle extends Shape` and the runtime dispatches `area()` calls via a vtable. In Lean, you write the same pattern in three steps: (1) define each shape as its own structure, (2) define a `Shape` inductive or existential that wraps them all, (3) define behavior via a type class. The `Coe` instance makes step 2 automatic — `Circle.mk 3.0` can appear anywhere a `Shape` is expected.

## Example — Open extension with existential encoding

```lean
-- Type class for the interface
class Drawable (α : Type) where
  draw : α → String

-- Existential wrapper — erases the concrete type
structure AnyDrawable where
  {Impl : Type}
  val : Impl
  [inst : Drawable Impl]

instance : Drawable AnyDrawable where
  draw d := @Drawable.draw d.Impl d.inst d.val

-- Concrete types
structure Line where p1 : Nat; p2 : Nat
structure Dot where x : Nat; y : Nat

instance : Drawable Line where draw l := s!"Line({l.p1}, {l.p2})"
instance : Drawable Dot  where draw d := s!"Dot({d.x}, {d.y})"

-- Heterogeneous list — no need to modify AnyDrawable to add types
def canvas : List AnyDrawable := [
  ⟨Line.mk 0 10⟩,
  ⟨Dot.mk 5 5⟩
]

#eval canvas.map Drawable.draw  -- ["Line(0, 10)", "Dot(5, 5)"]
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Closed inductives prevent invalid shape combinations.
- [-> UC-04](../usecases/UC04-generic-constraints.md) — Type class constraints ensure only types with the required interface are used.

## Source anchors

- [Simulating Subtyping and OO Polymorphism in Lean](https://typista.org/subtyping-and-polymorphism-in-lean/) — Typista.org
- [Type Classes — Functional Programming in Lean](https://leanprover.github.io/functional_programming_in_lean/type-classes/polymorphism.html)
- [Coercions — Lean 4 Reference](https://lean-lang.org/lean4/doc/coe.html)
