# Type-Level Functions and Universe Polymorphism

> **Since:** Lean 4 (stable)

## What it is

In Lean, types are values. There is no separate "type language" — the same `fun`, `match`, and `def` that work on values work on types. A **type lambda** is simply a function that returns a type:

```lean
def Pair := fun α => α × α

#check Pair   -- Pair.{u_1} (α : Type u_1) : Type u_1
```

Note what Lean did there: it *generalized the universe*, turning an unannotated type lambda into a universe-polymorphic constant with a level parameter `u_1`.

That generalization is what makes type-level functions work across the hierarchy — **not** cumulativity. Lean 4's universes are **not cumulative** (Coq's are). `Type 0 : Type 1 : Type 2 : ...` is a chain of typing judgements about the constants `Type 0`, `Type 1`, …; it is not a subtyping rule, and `α : Type 0` does *not* also give `α : Type 1`:

```lean
def notCumulative : Type 1 := Nat
-- error: Type mismatch: `Nat` has type `Type` of sort `Type 1`,
--        but is expected to have type `Type 1` of sort `Type 2`
```

The hierarchy is strictly *stratified*, and **universe polymorphism** is the mechanism that spans it: a definition is parameterized over universe levels and re-instantiated at whatever level each use site needs.

```lean ignore
def List : Type u → Type u   -- u is a universe variable (signature sketch)
```

When two fixed levels genuinely have to meet, you move a type up explicitly with `ULift`:

```lean
example : Type 1 := ULift.{1, 0} Nat
```

There is no special syntax for type-level programming. Everything that works at the value level works at the type level because the language is uniformly dependently typed.

## What constraint it enforces

**Type-level functions are checked by the same rules as value-level functions; universe polymorphism ensures type constructors work across all universe levels consistently.**

More specifically:

- **Type functions are typed.** `fun α => List α` has type `Type u → Type u`. The compiler checks that type-level functions produce well-formed types.
- **Universe consistency.** Universe levels prevent paradoxes (like `Type : Type`). The compiler infers and checks universe levels automatically.
- **No separate type language.** There is no "kind" system or "type-level Haskell." Type computations are just computations.

## Minimal snippet

```lean
-- A type-level function: takes a type, returns a type
def Wrapper := fun α => Option α

-- `#check` reports the elaborated type, it does not unfold `Wrapper`:
#check Wrapper Nat      -- Wrapper Nat : Type    (definitionally `Option Nat`)
#check Wrapper String   -- Wrapper String : Type (definitionally `Option String`)

-- Universe-polymorphic identity
def id' {α : Sort u} (a : α) : α := a

#check @id' -- {α : Sort u} → α → α
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dependent Types** [→ catalog/T09](T09-dependent-types.md) | Type lambdas are a special case of dependent functions where the return type is a universe. The full Pi type `(x : α) → β x` generalizes this. |
| **Universes** [→ catalog/T35](T35-universes-kinds.md) | Universe polymorphism allows type functions to work across all levels. `List : Type u → Type u` is universe-polymorphic. |
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | Type classes can be parameterized by type constructors: `class Functor (f : Type u → Type v)`. |
| **Type Aliases** [→ catalog/T23](T23-type-aliases.md) | `abbrev` and `def` can define type-level functions. The reducibility determines how the type checker treats them. |
| **Match Types** [→ catalog/T41](T41-match-types.md) | Type-level `match` is just a dependent function with pattern matching — no separate construct needed. |

## Gotchas and limitations

1. **Universe level inference.** Lean usually infers universe levels, but complex type-level functions may require explicit universe annotations: `universe u v` at the top of the file.

2. **Type-level `if` works — but only reduces on a closed condition.** `ite` is `Sort`-polymorphic, so a plain `if` may return types. What it requires is a `Decidable` instance for the condition (automatic for `Bool`, and for any decidable proposition), and reduction only happens once the condition is a closed value:

   ```lean
   def TIf (b : Bool) : Type := if b then Nat else String

   example : TIf true := (3 : Nat)   -- OK: `TIf true` reduces to `Nat`

   example (b : Bool) : TIf b := (3 : Nat)
   -- error: Type mismatch: `3` has type `Nat` but is expected to have type `TIf b`
   ```

3. **Definitional equality matters.** Two type-level computations must reduce to a common form to be interchangeable. This is where transparency bites: `@[irreducible]` stops the *elaborator* — unification and instance search give up on the definition — even though the kernel ignores the attribute and would unfold it. Only `opaque` blocks both.

4. **No higher-kinded types syntax.** Lean does not have a `* -> *` kind syntax. Instead, `Type → Type` serves the same role. The encoding is natural but unfamiliar to Haskell programmers.

## Beginner mental model

Think of Lean's type system as **a programming language that runs at compile time**. You write functions that take types and return types, using the same `fun`, `match`, and `def` you use for values. `List` is a function from types to types. `fun α => α × α` is a function that takes a type and returns the pair type. There is no separate "type algebra" — it is all one language.

Coming from Scala/Haskell: Lean's type lambdas are like Scala 3's `[X] =>> List[X]` or Haskell's `TypeFamilies`, but they require no special syntax because the language is dependently typed from the ground up.

## Example A — Higher-kinded abstraction

```lean
class Container (f : Type → Type) where
  empty : f α
  insert : α → f α → f α

instance : Container List where
  empty := []
  insert := (· :: ·)

instance : Container Array where
  empty := #[]
  insert a xs := xs.push a
```

## Example B — Type-level computation

```lean
-- A function that computes a type based on a boolean
-- (abbrev so the type checker reduces `ChooseType true` to `Nat` for literals)
abbrev ChooseType : Bool → Type
  | true  => Nat
  | false => String

def example1 : ChooseType true := 42
def example2 : ChooseType false := "hello"

-- `example1` is definitionally `Nat` and `example2` definitionally `String`,
-- but `#check` shows the type as declared — `abbrev` reducibility lets the
-- elaborator *accept* `42 : ChooseType true`, it does not make the
-- pretty-printer display the reduct.
#check example1   -- example1 : ChooseType true
#check example2   -- example2 : ChooseType false
```

## Use-case cross-references

- [→ UC-04](../usecases/UC04-generic-constraints.md) — Type-level functions enable higher-kinded abstractions over type constructors.
- [→ UC-12](../usecases/UC12-compile-time.md) — Type-level computation is inherently compile-time.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 2 "Dependent Type Theory" (universes)
- *Functional Programming in Lean* — "Polymorphism" and "Functors, Applicatives, and Monads"
- Lean 4 source: `Lean.Level` (universe level representation)
