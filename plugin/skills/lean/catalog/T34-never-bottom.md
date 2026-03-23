# Never / Bottom — Empty, False, and Absurd

> **Since:** Lean 4 (stable)

## What it is

Lean has two types with no constructors, serving the role of "bottom" or "never" types:

- **`Empty`** — An inductive type in `Type` with zero constructors. It represents an impossible *value*. A function returning `Empty` can never return normally.
- **`False`** — A proposition in `Prop` with zero constructors. It represents logical absurdity. A proof of `False` means the assumptions are contradictory.

The key functions for working with these types:

- **`absurd : α → ¬α → β`** — Given a value and a proof of its negation, produce anything (ex falso quodlibet).
- **`Empty.elim : Empty → α`** — Given a value of `Empty`, produce anything. Since `Empty` has no constructors, this function is total but can never be called.
- **`False.elim : False → α`** — The `Prop` analog of `Empty.elim`.
- **`nomatch`** — A keyword for writing functions on empty types without needing to provide any cases.

## What constraint it enforces

**Types with no constructors cannot be instantiated; functions receiving them can produce any return type, enabling exhaustive case analysis and impossible-case elimination.**

More specifically:

- **Uninhabitability.** No value of type `Empty` or proof of `False` can be constructed (without `sorry` or axioms). The compiler guarantees this.
- **Ex falso.** Given an impossible value, any conclusion follows. This is logically sound and used pervasively in proofs.
- **Exhaustive elimination.** Pattern matching on `Empty` or `False` requires zero cases — the match is trivially exhaustive.

## Minimal snippet

```lean
-- A function that can never be called (no value of Empty exists)
def impossible : Empty → Nat := nomatch ·

-- Using absurd to handle contradictory branches
def safeHead (xs : List α) (h : xs ≠ []) : α :=
  match xs with
  | x :: _ => x
  | []     => absurd rfl h   -- h : xs ≠ [], but xs = [] here — contradiction
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Propositions as Types** [→ catalog/T29](T29-propositions-as-types.md) | `False` is the empty proposition. `¬P` is defined as `P → False`. Proof by contradiction uses `False.elim`. |
| **Inductive Types** [→ catalog/T01](T01-algebraic-data-types.md) | `Empty` is simply an inductive type with no constructors. Pattern matching on it requires zero branches. |
| **Type Narrowing** [→ catalog/T14](T14-type-narrowing.md) | Impossible branches in a `match` can be eliminated using `absurd` or `nomatch`, proving that the branch is unreachable. |
| **Dependent Types** [→ catalog/T09](T09-dependent-types.md) | Dependent pattern matching can produce `False` branches when index constraints are contradictory — the compiler knows these are unreachable. |
| **Erased Proofs** [→ catalog/T27](T27-erased-phantom.md) | `False` is in `Prop`, so its elimination is erased at runtime. Using `absurd` in a proof branch adds no runtime cost. |

## Gotchas and limitations

1. **`Empty` vs `False`.** `Empty : Type` is for values; `False : Prop` is for propositions. Use `Empty` when you need an impossible *data* type (e.g., a type parameter for a generic container). Use `False` in logical contexts.

2. **`sorry` inhabits everything.** The `sorry` axiom can produce a value of `Empty` or a proof of `False`. It is a debugging tool, not a sound proof. Lean marks any definition using `sorry` with a warning.

3. **`panic!` is not bottom.** `panic!` returns a default value (via `Inhabited`) rather than diverging. It is not the same as Rust's `!` type or Haskell's `undefined`.

4. **No `Never` keyword.** Unlike Rust's `!` or TypeScript's `never`, Lean uses the standard inductive types `Empty` and `False`. They serve the same purpose with more explicit semantics.

## Beginner mental model

Think of `Empty` as a **door that cannot be opened** — it has no handle (no constructors). If someone hands you the key (a value of `Empty`), you know something impossible happened, so you can conclude anything. `False` is the logical version: it is a statement that is never true. If you prove `False`, your assumptions must be wrong.

Coming from Rust: `Empty` ≈ `enum Void {}` or the `!` never type. `absurd` ≈ unreachable code justified by contradictory conditions.

## Example A — Exhaustive match with impossible cases

```lean
inductive Parity where
  | even | odd

def parityOf (n : Nat) : Parity :=
  if n % 2 == 0 then .even else .odd

def describe : Parity → String
  | .even => "divisible by 2"
  | .odd  => "not divisible by 2"
  -- exhaustive: both constructors covered

-- An empty inductive needs zero cases:
inductive Void : Type where

def fromVoid : Void → α := nomatch ·
```

## Example B — Negation as implication to False

```lean
-- ¬P is defined as P → False
example : ¬(0 = 1) := by
  intro h        -- assume 0 = 1
  exact absurd h (by decide)  -- derive contradiction

-- Using Empty in a type-level context
def noElements : List Empty → Nat :=
  fun xs => xs.length   -- always 0, since no Empty values exist
```

## Use-case cross-references

- [→ UC-01](../usecases/UC01-invalid-states.md) — Empty types make impossible states truly unrepresentable.
- [→ UC-03](../usecases/UC03-exhaustiveness.md) — Impossible cases are eliminated by `nomatch` or `absurd`.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 3 "Propositions and Proofs" (False, negation)
- Lean 4 core: `Init.Prelude` (definition of `Empty`, `False`)
- *Theorem Proving in Lean 4* — Ch. 7 "Inductive Types"
