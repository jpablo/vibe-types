# Simp, Decide, Omega — Proof Automation

> **Since:** Lean 4 (stable) | Some `simp` lemmas: **Requires Mathlib**

## What it is

Lean requires proof terms for propositions, but writing them by hand is tedious. Proof automation tactics generate proof terms automatically:

- **`simp`** — the simplifier. Rewrites the goal using a database of lemmas tagged `@[simp]`. Handles equalities, boolean simplifications, list/array operations, and more. Mathlib adds thousands of `simp` lemmas.
- **`decide`** — evaluates decidable propositions by computation. If `P : Prop` has a `Decidable P` instance, `decide` reduces the proposition to `true` or `false` and produces a proof. Works for finite checks (small `Nat` comparisons, `Bool` logic, `Fin` operations).
- **`omega`** — a decision procedure for linear arithmetic over `Nat` and `Int`. Proves goals like `a + b < c` — no `simp` lemmas needed. It also understands `%`, `/` and `∣`, but **only with numeral operands** (`a % 2 < 2`, `3 ∣ n → n % 3 = 0`). With a *variable* divisor, `a % b` is just an opaque atom to `omega` and even a true goal like `0 < b → a % b < b` is out of reach.

These tactics are the workhorses of proof obligation discharge in programming contexts (subtype construction, termination proofs, index arithmetic).

## What constraint it enforces

**Proof obligations can be discharged automatically; tactics verify that the stated property holds and reject it if they can't prove it.**

More specifically:

- **`simp` closure.** If the `simp` database contains enough lemmas, the goal simplifies to `True` and is closed. If not, `simp` simplifies as much as it can and leaves the residual goal.
- **`decide` reduces, it does not reason.** `decide` synthesises the `Decidable` instance and asks the kernel to *evaluate* it. It succeeds only when that evaluation reaches `isTrue`. Failure carries **no** information about the truth of the goal: a perfectly true, perfectly decidable proposition fails whenever the instance gets stuck — on an `opaque` constant, on `Classical.propDecidable`, or on an instance defined by well-founded recursion. And a goal mentioning a free variable is refused outright, before any evaluation happens.
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

3. **`decide` is exponential — and fails silently on true goals.** It evaluates the decision procedure in the kernel. For large types this is slow or blows up memory. Worse, a failure is not evidence that the goal is false; the instance may simply be stuck:

   ```lean
   opaque secret : Nat

   -- error: Tactic `decide` failed — the Decidable instance did not reduce to isTrue/isFalse
   example : secret = secret := by decide
   ```

   `native_decide` sidesteps the slowness, but see the next point before reaching for it.

4. **`native_decide` moves the check outside the kernel and adds an axiom.** It compiles the decision procedure to native code and trusts the result. The kernel never rechecks it, and the theorem's trust base grows: `#print axioms` reports a generated `native_decide` axiom. That means a compiler or FFI bug becomes a soundness bug. It is a legitimate tool for large finite checks, but it is not a free speedup — never use it in a proof whose whole point is kernel-verified trust.

   ```lean
   theorem nd : (List.range 100).length = 100 := by native_decide
   #print axioms nd   -- 'nd' depends on axioms: [nd._native.native_decide.ax_1_1]
   ```

5. **`omega` is limited to linear arithmetic.** It cannot handle `a * b < c` (nonlinear) or goals about `Float`. For nonlinear `Nat`/`Int` goals over variables you need a manual proof — `norm_num` is *not* the answer, and is not available here anyway (see below).

6. **The famous tactics are Mathlib, not core.** `ring`, `linarith` and `norm_num` all ship with Mathlib; on a core-only toolchain `by norm_num` is simply `unknown tactic`. `aesop` is a separate package again (Mathlib depends on it, but it is not part of Mathlib proper). And even with Mathlib available, `norm_num` *normalises numeric expressions* — concrete arithmetic, primality, casts. It does not prove nonlinear facts about variables; that is `nlinarith`/`polyrith` territory.

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
  -- bring the positivity proofs into scope so omega can see a.val, b.val > 0
  ⟨a.val + b.val, by have := a.property; have := b.property; omega⟩

-- error: omega could not prove the goal — 0 > 0 is false
def zero : PosNat := ⟨0, by omega⟩
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

### `omega could not prove the goal`

For `example (a b : Nat) (h : a > 0) : a * b > 0 := by omega`:

```
omega could not prove the goal:
a possible counterexample may satisfy the constraints
  c ≥ 1
where
 c := ↑a
```

**Meaning:** The goal is outside `omega`'s scope (here `a * b` is nonlinear, so it becomes an atom) or is actually false. The header is always `omega could not prove the goal:`; the body tells you which case you are in. `a possible counterexample may satisfy the constraints …` lists the linear facts `omega` *did* extract — read it as "these are all I had, and they don't force the goal". If instead the body says `No usable constraints found. You may need to unfold definitions …`, `omega` found nothing arithmetical at all, usually because the relevant facts are hidden behind a definition or were never brought into context.

### `decide timed out`

```
(deterministic) timeout at 'whnf'
```

**Meaning:** `decide` is trying to evaluate a proposition that's too large. Restructure the proof to avoid brute-force evaluation, or fall back to `native_decide` — accepting that it moves the check out of the kernel and adds an axiom to the result (gotcha 4).

## Proof perspective (brief)

These tactics are the front line of Lean's proof automation. `simp` is a conditional term rewriting engine based on completion — it applies `@[simp]` lemmas in a convergent order. `decide` implements the BHK interpretation for decidable propositions via `Decidable.decide`. `omega` implements a decision procedure for Presburger arithmetic (quantifier-free linear arithmetic over integers). Beyond core, more powerful tactics exist — but they are *not* part of this toolchain: `ring` (polynomial identities), `linarith` (linear arithmetic with hypotheses) and `norm_num` (numeric normalization) come from Mathlib, and `aesop` (general-purpose proof search) is its own package that Mathlib depends on. On a core-only setup, invoking any of them is an `unknown tactic` error.

## Use-case cross-references

- [→ UC-04](../usecases/UC12-compile-time.md) — Proof automation discharges invariant proofs at construction sites.
- [→ UC-07](../usecases/UC24-termination.md) — `omega` and `simp` are the standard tools for termination proofs.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 5 "Tactics" (simp)
- *Functional Programming in Lean* — "Proof Automation"
- Lean 4 source: `Lean.Elab.Tactic.Simp`, `Lean.Elab.Tactic.Omega`
- Mathlib: `Mathlib.Tactic.NormNum`, `Mathlib.Tactic.Ring`
