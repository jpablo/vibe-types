# Universes and Universe Polymorphism

> **Since:** Lean 4 (stable)

## What it is

In Lean, types themselves have types, organized into a hierarchy of *universes*. `Prop` (logical propositions) is `Sort 0`. `Type` (computational types) is `Sort 1`, also written `Type 0`. `Type 1` is `Sort 2`, and so on. This hierarchy prevents the "type-in-type" paradox (Girard's paradox), which would make the logic inconsistent.

Universe polymorphism lets definitions work across multiple universe levels. Instead of writing separate versions for `Type 0`, `Type 1`, etc., you introduce a *universe variable* and write `Type u` in the signature; Lean instantiates the definition at each required level. Most standard library definitions (`List`, `Option`, `Prod`) are universe-polymorphic.

Universe variables are introduced in one of three ways — there is **no `{u : Level}` binder syntax**:

- `universe u` as a standalone command, after which `u` may be used in following declarations;
- the explicit level-binder suffix on the declaration name, `def f.{u} ... : Type u := ...`;
- implicitly, by simply mentioning an undeclared level name in a signature (`def f (α : Type u) := α`), which auto-bound implicits turn into a level parameter.

`Level` is `Lean.Level`, the *metaprogramming* datatype that represents levels inside the compiler; it needs `import Lean` and is not a type you bind over. Written literally in a signature, `{u : Level}` silently becomes two ordinary auto-bound **term** implicits and the `u` in `Type u` becomes a third, unrelated auto-bound **level**:

```lean
def foo {u : Level} (α : Type u) : Type u := α

set_option pp.universes true in
#check @foo
-- @foo.{u_1, u_2} : {Level : Sort u_2} → {u : Level} → Type u_1 → Type u_1
--                    ^^^^^ auto-bound term  ^^^^^ auto-bound term   ^^^ the actual level
```

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
| **Propositions as Types** [→ T29](T29-propositions-as-types.md) | `Prop` = `Sort 0` is the bottom universe with special properties (impredicativity, proof irrelevance). |
| **Dependent Types** [→ T09](T09-dependent-types.md) | Pi types quantifying over types must respect universe levels: `(α : Type u) → α → α` lives in `Type (u + 1)`. |
| **Type Classes** [→ T05](T05-type-classes.md) | Type classes are universe-polymorphic. `outParam` helps when multi-parameter classes span different universes. |
| **Inductive Types** [→ T01](T01-algebraic-data-types.md) | Inductive types are assigned a universe level based on their constructors' argument types. |

## Gotchas and limitations

1. **Universe errors are confusing.** Messages like `failed to solve universe constraint`, its sibling `stuck at solving universe constraint`, and ``Invalid universe level in constructor `C` `` are opaque. They usually mean you need to add a universe variable, align levels, or raise the target universe of an inductive.

2. **`Prop` elimination restriction.** You cannot in general extract computational data from a `Prop` proof (large elimination). This means `Exists` in `Prop` doesn't give you a computable witness — use `Σ` (Sigma) in `Type` for that.

3. **Explicit universe variables.** When auto-inference fails, declare universe variables with `universe u v` at the top of a file, or bind them on the declaration itself with `def f.{u} ...`. Levels can also be supplied at a use site: `f.{0}` instantiates the first level parameter with `0`.

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

### `failed to solve universe constraint`

```lean
universe u

example : Sort (max u 1) := ULift.{u} Nat
-- error: failed to solve universe constraint
--   max 1 u =?= max (u + 1) 1
```

```
failed to solve universe constraint
  max 1 u =?= max (u + 1) 1
while trying to unify
  Sort (max u 1) : Type (max u 1)
with
  Type u : Type (u + 1)
```

**Meaning:** Two level expressions had to be made equal and no assignment to the level variables does it. Read the `=?=` line: it is the unsolvable equation. Fix by aligning the levels (often with `max`/`+ 1` in the right places) or by inserting a `ULift`. The sibling message `stuck at solving universe constraint` reports the same kind of equation when it still contains unassigned level metavariables at the end of elaboration. There is no `universe level mismatch` message in Lean 4.

### ``Invalid universe level in constructor `C` ``

```lean
inductive Bad : Type where
  | mk : Type → Bad
-- error: Invalid universe level in constructor `Bad.mk`: Parameter has type Type
--        at universe level 2 which is not less than or equal to the inductive
--        type's resulting universe level 1
```

```
Invalid universe level in constructor `Bad.mk`: Parameter has type
  Type
at universe level
  2
which is not less than or equal to the inductive type's resulting universe level
  1
```

**Meaning:** An inductive must live at least as high as everything its constructors store. Storing a `Type` (which lives in `Type 1`) forces the inductive up to `Type 1`. Fix by raising the declared universe (`inductive Bad : Type 1`) or by making the definition universe-polymorphic (`inductive Bad : Type (u + 1) where | mk : Type u → Bad`).

### `type expected, got`

```lean
def z : (5 : Nat) := 0
-- error: type expected, got (5 : Nat)
```

```
type expected, got
  (5 : Nat)
```

**Meaning:** The expression in type position is not a type at all. The payload is always rendered as `(term : type)`, so it can never be a `Sort` — a `Sort` *is* a type, and would be accepted. This error has nothing to do with missing level annotations; you wrote a value (or a term of the wrong shape) where a type belongs.

### ``recursor `Exists.casesOn` can only eliminate into `Prop` ``

```lean
def witness (h : ∃ n : Nat, n = n) : Nat :=
  match h with
  | ⟨n, _⟩ => n
-- error: recursor `Exists.casesOn` can only eliminate into `Prop`
```

```
error(nested.lean.propRecLargeElim): Tactic `cases` failed with a nested error:
Tactic `induction` failed: recursor `Exists.casesOn` can only eliminate into `Prop`
```

**Meaning:** You tried to pattern match on a `Prop` value to extract computational data (*large elimination*). `Exists` lives in `Prop`, so its recursor may only build proofs, not data. Use `Decidable`, `Classical.choice`, or restructure to use `Sigma`/`Subtype` in `Type`. The error code is `propRecLargeElim`.

## Proof perspective (brief)

The universe hierarchy is the foundation of Lean's consistency as a logical system. Without it, Lean would be subject to Girard's paradox (the type-theoretic analog of Russell's paradox). `Prop` being impredicative means you can define propositions that quantify over all propositions (∀ P : Prop, ...) without ascending the universe hierarchy — this is essential for classical logic. The Calculus of Inductive Constructions (Lean's core theory) derives its power from the interaction between `Prop`, the predicative `Type` hierarchy, and inductive types.

## Coming from Scala

Lean's universe hierarchy (`Prop`, `Type 0`, `Type 1`, ...) has no direct Scala equivalent. Scala's `AnyKind` allows abstracting over kinds (`*`, `* → *`, etc.) but doesn't stratify types into levels. Lean's universes prevent logical paradoxes (Russell's paradox via `Type : Type`); Scala avoids this differently — it doesn't have type-in-type because its type system is less expressive at the meta level.

## Use-case cross-references

- [→ UC-06](../usecases/UC04-generic-constraints.md) — Universe polymorphism enables generic definitions that work across all type levels.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 2 "Dependent Type Theory" (Universes section)
- Lean 4 source: `Lean.Level`, `Init.Prelude` (`Sort`, `Type`, `Prop`)
