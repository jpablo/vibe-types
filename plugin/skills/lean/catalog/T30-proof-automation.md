# Simp, Decide, Omega — Proof Automation

> **Since:** Lean 4 (stable) | Some `simp` lemmas: **Requires Mathlib**

## What it is

Lean requires proof terms for propositions, but writing them by hand is tedious. Proof automation tactics generate proof terms automatically:

- **`simp`** — the simplifier. Rewrites the goal using a database of lemmas tagged `@[simp]`. Handles equalities, boolean simplifications, list/array operations, and more. Mathlib adds thousands of `simp` lemmas.
- **`decide`** — evaluates decidable propositions by computation. If `P : Prop` has a `Decidable P` instance, `decide` reduces the proposition to `true` or `false` and produces a proof. Works for finite checks (small `Nat` comparisons, `Bool` logic, `Fin` operations).
- **`omega`** — a decision procedure for linear arithmetic over `Nat` and `Int`. Proves goals like `a + b < c`, `a % b > 0`, divisibility constraints, and more — no `simp` lemmas needed.

These tactics are the workhorses of proof obligation discharge in programming contexts (subtype construction, termination proofs, index arithmetic).

## What constraint it enforces

**Proof obligations can be discharged automatically; tactics verify that the stated property holds and reject it if they can't prove it.**

More specifically:

- **`simp` closure.** If the `simp` database contains enough lemmas, the goal simplifies to `True` and is closed. If not, `simp` simplifies as much as it can and leaves the residual goal.
- **`decide` completeness.** For `Decidable` propositions, `decide` always succeeds or fails — there's no ambiguity. Failure means the proposition is false (or not `Decidable`).
- **`omega` scope.** `omega` handles linear arithmetic over integers and naturals. It rejects goals involving multiplication of variables, nonlinear terms, or non-numeric types.

## Minimal snippet

```lean
-- simp: simplify using known lemmas
example : 0 + n = n := by simp  -- OK: Nat.zero_add is @[simp]

-- decide: evaluate decidable propositions
example : 2 + 2 = 4 := by decide  -- OK: Nat equality is Decidable

-- omega: linear arithmetic
example (a b : Nat) (h : a < b) : a + 1 ≤ b := by omega  -- OK
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Subtypes** [→ T26](T26-refinement-types.md) | Subtype construction proofs are the primary consumer of `omega` and `simp` in programming contexts. |
| **Termination** [→ T28](T28-termination.md) | `decreasing_by omega` and `decreasing_by simp` discharge termination obligations. |
| **Propositions as Types** [→ T29](T29-propositions-as-types.md) | These tactics produce `Prop` proof terms that the type checker verifies. |
| **Notation & Attributes** [→ T39](T39-notation-attributes.md) | `@[simp]` registers a lemma in the simplifier database. `@[omega]` is not a thing — `omega` has its own built-in rules. |
| **Macros & Elaboration** [→ T17](T17-macros-metaprogramming.md) | Tactics are elaborators. Custom tactics can combine `simp` and `omega` calls. |

## Gotchas and limitations

1. **`simp` is not magic.** It only uses lemmas tagged `@[simp]`. If the required lemma isn't in the database, `simp` won't close the goal. Use `simp [myLemma]` to add specific lemmas, or `simp?` to discover which lemmas `simp` would use.

2. **`simp` can be slow.** With large `simp` databases (especially Mathlib), `simp` may take seconds. Use `simp only [lemma1, lemma2]` to restrict the search space.

3. **`decide` is exponential.** It evaluates the decision procedure at compile time. For large types (e.g., `Decidable` on `Fin 10000`), this can be extremely slow or blow up memory. Use `native_decide` for better performance on large instances.

4. **`omega` is limited to linear arithmetic.** It cannot handle `a * b < c` (nonlinear) or goals about `Float`. For nonlinear `Nat`/`Int` goals, you need manual proof or `norm_num`.

5. **`norm_num` (Mathlib).** For numeric computations beyond `omega`'s scope, Mathlib provides `norm_num`, which handles concrete numeric evaluation, prime checks, and more.

## Beginner mental model

Think of these tactics as **automatic proof generators**:
- `simp` = "simplify this using known facts" (like a smart algebraic simplifier)
- `decide` = "just compute it and check" (works for small, finite problems)
- `omega` = "this is an arithmetic inequality — figure it out"

When you construct a subtype `⟨value, by omega⟩`, you're saying: "here's the value, and I trust `omega` to prove the predicate." If `omega` can't, you get a compile error.

## Example A — Subtype construction with omega

```lean
def PosNat := { n : Nat // n > 0 }

def five : PosNat := ⟨5, by omega⟩         -- OK
def sum (a b : PosNat) : PosNat :=
  ⟨a.val + b.val, by omega⟩                -- OK: omega proves a.val + b.val > 0
-- def zero : PosNat := ⟨0, by omega⟩      -- error: omega fails (0 > 0 is false)
```

## Example B — Termination proof with omega

```lean
def binarySearch (xs : Array Nat) (target : Nat) (lo hi : Nat) : Option Nat :=
  if h : lo < hi then
    let mid := (lo + hi) / 2
    if xs[mid]! = target then some mid
    else if xs[mid]! < target then binarySearch xs target (mid + 1) hi
    else binarySearch xs target lo mid
  else none
termination_by hi - lo
decreasing_by all_goals omega  -- omega proves both (hi - (mid+1) < hi - lo) and (mid - lo < hi - lo)
```

## Common compiler errors and how to read them

### `simp made no progress`

```
simp made no progress
```

**Meaning:** The `simp` database doesn't contain a lemma that applies to your goal. Try `simp [specificLemma]` or use a different tactic.

### `omega failed to prove the goal`

```
omega failed to prove the goal
  ⊢ a * b > 0
```

**Meaning:** The goal is outside `omega`'s scope (nonlinear) or is actually false. Check the goal and use a different approach.

### `decide timed out`

```
(deterministic) timeout at 'whnf'
```

**Meaning:** `decide` is trying to evaluate a proposition that's too large. Use `native_decide` for better performance, or restructure the proof to avoid brute-force evaluation.

## Proof perspective (brief)

These tactics are the front line of Lean's proof automation. `simp` is a conditional term rewriting engine based on completion — it applies `@[simp]` lemmas in a convergent order. `decide` implements the BHK interpretation for decidable propositions via `Decidable.decide`. `omega` implements a decision procedure for Presburger arithmetic (quantifier-free linear arithmetic over integers). In Mathlib, more powerful tactics exist: `ring` (polynomial identities), `linarith` (linear arithmetic with hypotheses), `norm_num` (numeric normalization), and `aesop` (general-purpose proof search).

## Use-case cross-references

- [→ UC-04](../usecases/UC12-compile-time.md) — Proof automation discharges invariant proofs at construction sites.
- [→ UC-07](../usecases/UC24-termination.md) — `omega` and `simp` are the standard tools for termination proofs.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 5 "Tactics" (simp)
- *Functional Programming in Lean* — "Proof Automation"
- Lean 4 source: `Lean.Elab.Tactic.Simp`, `Lean.Elab.Tactic.Omega`
- Mathlib: `Mathlib.Tactic.NormNum`, `Mathlib.Tactic.Ring`
