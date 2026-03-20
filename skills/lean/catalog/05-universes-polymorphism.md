# Universes and Universe Polymorphism

> **Since:** Lean 4 (stable)

## What it is

In Lean, types themselves have types, organized into a hierarchy of *universes*. `Prop` (logical propositions) is `Sort 0`. `Type` (computational types) is `Sort 1`, also written `Type 0`. `Type 1` is `Sort 2`, and so on. This hierarchy prevents the "type-in-type" paradox (Girard's paradox), which would make the logic inconsistent.

Universe polymorphism lets definitions work across multiple universe levels. Instead of writing separate versions for `Type 0`, `Type 1`, etc., you write `{u : Level} → ... Type u ...` and Lean instantiates it at each required level. Most standard library definitions (`List`, `Option`, `Prod`) are universe-polymorphic.

## What constraint it enforces

**Types cannot contain themselves; the universe hierarchy prevents circular type definitions that would lead to logical paradoxes.**

More specifically:

- **No type-in-type.** `Type u` has type `Type (u + 1)`, never `Type u` itself. This prevents Girard's paradox.
- **Prop is special.** `Prop` (= `Sort 0`) is *impredicative*: you can quantify over all propositions and still get a `Prop`. `Type u` is *predicative*: quantifying over `Type u` gives `Type (u + 1)`.
- **Automatic level inference.** Lean infers universe levels in most cases. You rarely need to write them explicitly.
- **Consistency.** The universe hierarchy is the first line of defense against logical inconsistency.

## Minimal snippet

```lean
-- Universe-polymorphic identity
def id' {α : Sort u} (x : α) : α := x

-- Works at any universe level:
#check id' (42 : Nat)       -- OK: Nat : Type 0
#check id' (Nat : Type 0)   -- OK: Type 0 : Type 1
#check id' (True : Prop)    -- OK: Prop = Sort 0
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Propositions as Types** [→ catalog/06] | `Prop` = `Sort 0` is the bottom universe with special properties (impredicativity, proof irrelevance). |
| **Dependent Types** [→ catalog/02] | Pi types quantifying over types must respect universe levels: `(α : Type u) → α → α` lives in `Type (u + 1)`. |
| **Type Classes** [→ catalog/04] | Type classes are universe-polymorphic. `outParam` helps when multi-parameter classes span different universes. |
| **Inductive Types** [→ catalog/01] | Inductive types are assigned a universe level based on their constructors' argument types. |

## Gotchas and limitations

1. **Universe errors are confusing.** Messages like `universe level mismatch` or `type expected, got Sort (max u v + 1)` are opaque. They usually mean you need to add a universe variable or align levels.

2. **`Prop` elimination restriction.** You cannot in general extract computational data from a `Prop` proof (large elimination). This means `Exists` in `Prop` doesn't give you a computable witness — use `Σ` (Sigma) in `Type` for that.

3. **Explicit universe variables.** When auto-inference fails, you can declare universe variables with `universe u v` at the top of a file and use them in signatures.

4. **`ULift` for level mismatches.** When you need to lift a type from `Type u` to `Type (max u v)`, use `ULift`. This is rare in application code but common in library code.

5. **`noncomputable` and universes.** `Classical.choice` works across universes but makes definitions noncomputable.

## Beginner mental model

Think of universes as **floors in a building**. Values live on the ground floor. Types of those values live on the first floor. Types of types live on the second floor, and so on. A type cannot live on its own floor — it must be one floor up. Universe polymorphism lets a definition take an elevator to any floor.

Coming from Rust/Python: you never think about this in mainstream languages because they don't have types-of-types as first-class values. In Lean, because types are values, the hierarchy is needed to prevent paradoxes.

## Example A — Universe-polymorphic container

```lean
universe u

structure Box (α : Type u) where
  val : α

#check Box Nat        -- Box Nat : Type      (= Type 0)
#check Box (Type 0)   -- Box (Type 0) : Type 1
```

## Example B — Prop vs Type universes

```lean
-- In Prop: proof irrelevance, impredicative
def allPropsAreEqual (p q : Prop) (hp : p) (hq : p) : hp = hq :=
  rfl  -- OK: proof irrelevance — all proofs of the same Prop are equal

-- In Type: cannot use the same trick
-- def allNatsAreEqual (a b : Nat) : a = b := rfl  -- error: rfl requires a = a
```

## Common compiler errors and how to read them

### `universe level mismatch`

```
universe level mismatch at ...
```

**Meaning:** The universe levels in your definition don't align. Add explicit universe variables or adjust the definition to ensure levels are consistent.

### `type expected, got (Sort ...)`

```
type expected, got
  Sort (max u v + 1)
```

**Meaning:** You used a `Sort` expression where a specific type was expected. This usually means a universe-polymorphic definition needs more level annotations.

### `cannot eliminate from Prop into Type`

```
cannot eliminate 'Exists' into Type
```

**Meaning:** You tried to pattern match on a `Prop` value to extract computational data. Use `Decidable`, `Classical.choice`, or restructure to use `Sigma` in `Type`.

## Proof perspective (brief)

The universe hierarchy is the foundation of Lean's consistency as a logical system. Without it, Lean would be subject to Girard's paradox (the type-theoretic analog of Russell's paradox). `Prop` being impredicative means you can define propositions that quantify over all propositions (∀ P : Prop, ...) without ascending the universe hierarchy — this is essential for classical logic. The Calculus of Inductive Constructions (Lean's core theory) derives its power from the interaction between `Prop`, the predicative `Type` hierarchy, and inductive types.

## Use-case cross-references

- [→ UC-06](../usecases/06-generic-programming-type-classes.md) — Universe polymorphism enables generic definitions that work across all type levels.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 2 "Dependent Type Theory" (Universes section)
- Lean 4 source: `Lean.Level`, `Init.Prelude` (`Sort`, `Type`, `Prop`)
