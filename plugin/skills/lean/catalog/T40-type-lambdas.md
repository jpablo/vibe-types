# Type-Level Functions and Universe Polymorphism

> **Since:** Lean 4 (stable)

## What it is

In Lean, types are values. There is no separate "type language" — the same `fun`, `match`, and `def` that work on values work on types. A **type lambda** is simply a function that returns a type:

```lean
def Pair := fun α => α × α   -- Pair : Type → Type
```

This is possible because Lean's universes are cumulative: `Type 0 : Type 1 : Type 2 : ...`, and functions can operate at any universe level. **Universe polymorphism** means definitions can be parameterized over universe levels:

```lean
def List : Type u → Type u   -- u is a universe variable
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

#check Wrapper Nat      -- Option Nat : Type
#check Wrapper String   -- Option String : Type

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

2. **No type-level `if`.** While `match` works at the type level (via dependent elimination), you cannot use `if ... then ... else ...` to choose between types unless you use `Decidable` and dependent `if`.

3. **Definitional equality matters.** Two type-level computations must reduce to the same normal form to be considered equal by the kernel. This can be surprising when functions are `@[irreducible]`.

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
def ChooseType : Bool → Type
  | true  => Nat
  | false => String

def example1 : ChooseType true := 42
def example2 : ChooseType false := "hello"

-- example1 has type Nat, example2 has type String
#check example1   -- Nat
#check example2   -- String
```

## Use-case cross-references

- [→ UC-04](../usecases/UC04-generic-constraints.md) — Type-level functions enable higher-kinded abstractions over type constructors.
- [→ UC-12](../usecases/UC12-compile-time.md) — Type-level computation is inherently compile-time.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 2 "Dependent Type Theory" (universes)
- *Functional Programming in Lean* — "Polymorphism" and "Functors, Applicatives, and Monads"
- Lean 4 source: `Lean.Level` (universe level representation)
