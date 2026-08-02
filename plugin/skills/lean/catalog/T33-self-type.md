# Self Type (via Dependent Types)

> **Since:** Lean 4 (stable)

## What it is

Lean has **no `Self` keyword** like Rust or Swift. However, dependent types and Lean's design make it unnecessary:

- **Generic type parameters** serve as `Self`. A function `def clone {α : Type} (x : α) : α` returns the exact input type — `α` plays the role of `Self`.
- **Structure methods** — Functions defined in a structure's namespace naturally take the structure type as a parameter. `def Point.scale (p : Point) (f : Float) : Point` returns `Point` explicitly.
- **Type class methods** — Type class methods use the class's type parameter. `class Clone (α : Type) where clone : α → α` — here `α` is `Self`.
- **Dependent return types** — With dependent types, methods can return types that depend on the input value, going beyond what `Self` provides in other languages.

The key insight: in a dependently typed language, the "current type" is always available as a type parameter. There is no need for a special keyword.

## What constraint it enforces

**Functions and type class methods use explicit type parameters to refer to the implementing type; the compiler checks that return types match the declared type parameter.**

More specifically:

- **Exact type preservation.** `def id {α : Type} (x : α) : α` guarantees the output type equals the input type. The compiler enforces this — no widening.
- **No type-level `Self` indirection.** Unlike Rust where `Self` refers to the implementing type and can cause ambiguity with associated types, Lean's type parameters are always explicit and unambiguous.
- **Dependent precision.** Return types can depend on input *values*, not just types — more powerful than `Self`.

## Minimal snippet

```lean
-- Type class with "Self" semantics (α plays the role of Self)
class Clone (α : Type) where
  clone : α → α

structure Point where
  x : Float
  y : Float

instance : Clone Point where
  clone p := { p with }    -- returns Point (same type)

-- Generic function: α is "Self"
def duplicate [Clone α] (x : α) : α × α :=
  (Clone.clone x, Clone.clone x)
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | Type class type parameters serve as `Self`. `class Monoid (α : Type)` — `α` is the "self type" in every method. |
| **Dependent Types** [→ catalog/T09](T09-dependent-types.md) | Dependent return types go beyond `Self` — the return type can depend on the argument value, not just its type. |
| **Structures** [→ catalog/T31](T31-record-types.md) | Structure namespace functions take the structure type as a regular parameter — no `self` keyword needed. |
| **Generics** [→ catalog/T04](T04-generics-bounds.md) | Generic type parameters `{α : Type}` naturally play the role of `Self` in polymorphic functions. |
| **Associated Types** [→ catalog/T49](T49-associated-types.md) | Where Rust uses `Self::Item`, Lean uses `outParam` or structure fields. The "self type" and associated types are both explicit parameters. |

## Gotchas and limitations

1. **No implicit `self` parameter.** Unlike Rust's `&self` or Python's `self`, Lean methods do not have an implicit self parameter. You write `def Point.move (p : Point) ...` explicitly. Dot notation (`point.move`) provides the ergonomic equivalent.

2. **Factory methods.** A "factory" pattern (`Self::new()` in Rust) is simply a function returning the type: `def Point.origin : Point := ⟨0.0, 0.0⟩`. There is no `Self` to refer to.

3. **Type class inheritance.** In a class hierarchy `class B extends A`, methods in `B` use `B`'s type parameter, and `A`'s constraints are satisfied because `extends` generates the parent projection `B.toA` and **registers it as an instance** — `@B.toA : {α : Type} → [self : B α] → A α`. It is instance resolution that closes the gap, not a coercion.

   ```lean
   class Named (α : Type) where
     name : α → String
   class Greeter (α : Type) extends Named α where
     greeting : α → String

   -- Named.name is reachable from a Greeter constraint alone, via Greeter.toNamed
   def label [Greeter α] (x : α) : String := s!"{Greeter.greeting x}, {Named.name x}"
   ```

4. **`Self`-returning methods behind an existential.** Rust's `dyn Trait` struggles with `Self`-returning methods, and Lean has no `dyn` — but it is not the case that Lean lacks dynamic dispatch or that type parameters are always concrete. Type parameters are routinely *universally quantified* (`def duplicate [Clone α] (x : α) : α × α` works for every `α` at once), and existential packaging is expressible directly: bundle the carrier type, its instance, and the value into a structure, then dispatch through the stored instance.

   ```lean
   class Shape (α : Type) where
     area : α → Float

   structure Circle where r : Float
   structure Square where s : Float

   instance : Shape Circle := ⟨fun c => 3.14159 * c.r * c.r⟩
   instance : Shape Square := ⟨fun q => q.s * q.s⟩

   -- the existential package: carrier type + its instance + a value
   structure AnyShape where
     carrier : Type
     inst    : Shape carrier
     value   : carrier

   def AnyShape.area (s : AnyShape) : Float := s.inst.area s.value

   def shapes : List AnyShape :=
     [ { carrier := Circle, inst := inferInstance, value := ⟨1.0⟩ },
       { carrier := Square, inst := inferInstance, value := ⟨2.0⟩ } ]

   #eval shapes.map AnyShape.area   -- [3.141590, 4.000000]
   ```

   The dispatch really is dynamic: `AnyShape.area` picks the method out of a value at runtime. What you give up is exactly what Rust gives up — once packed, the carrier type is hidden, so a `Self`-returning method can only hand you back another `AnyShape`, never a statically known `Circle`.

## Beginner mental model

Think of Lean's approach as **always naming the type explicitly**. Instead of a magic `Self` word that changes meaning based on context, you use a type variable `α` that stands for "whatever type this is." Every function explicitly declares what type it works on and what type it returns. There is no hidden indirection.

Coming from Rust: Where Rust writes `fn clone(&self) -> Self`, Lean writes `def clone (x : α) : α`. The `α` in a type class serves exactly the role of `Self`. Coming from TypeScript: Where TypeScript uses `this` type, Lean uses an explicit type parameter.

## Example A — Builder pattern without Self

```lean
structure Config where
  host : String := "localhost"
  port : Nat := 8080
  debug : Bool := false

def Config.withHost (c : Config) (h : String) : Config :=
  { c with host := h }

def Config.withPort (c : Config) (p : Nat) : Config :=
  { c with port := p }

def Config.withDebug (c : Config) : Config :=
  { c with debug := true }

-- Chaining returns Config at every step
#eval ({} : Config) |>.withHost "example.com" |>.withPort 443 |>.withDebug
```

## Example B — Dependent "Self" — more powerful than Self keyword

```lean
-- Baseline: NOT value-dependent. Its type is `{α} → Nat → α → List α`;
-- the result type `List α` mentions no argument value.
def replicate (n : Nat) (x : α) : List α :=
  match n with
  | 0     => []
  | n + 1 => x :: replicate n x

-- THIS is the value-dependent one: the return type mentions `n`, so it
-- depends on the input VALUE, not just its type. Nothing `Self` can express.
def replicateV (n : Nat) (x : α) : { xs : List α // xs.length = n } :=
  ⟨List.replicate n x, by simp⟩

#eval (replicateV 3 'a').val   -- ['a', 'a', 'a']
```

## Use-case cross-references

- [→ UC-02](../usecases/UC02-domain-modeling.md) — Type parameters model domain types precisely without Self indirection.
- [→ UC-04](../usecases/UC04-generic-constraints.md) — Type class type parameters serve as Self in generic interfaces.

## Source anchors

- *Functional Programming in Lean* — "Structures" and "Type Classes"
- *Theorem Proving in Lean 4* — Ch. 10 "Type Classes"
- Lean 4 source: `Lean.Elab.App` (dot notation and method resolution)
