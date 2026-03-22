# Subtypes and Refinement Types

> **Since:** Lean 4 (stable)

## What it is

A subtype in Lean is a value paired with a proof that the value satisfies a predicate. Written `{ x : α // P x }`, it bundles a value `x` of type `α` together with evidence `h : P x` — a `Prop` proof that the predicate `P` holds for `x`. The proof is erased at runtime, so a subtype has the same runtime representation as the underlying type, but at compile time, construction is impossible without proving the predicate.

This is Lean's version of *refinement types* found in languages like Liquid Haskell or F*. Unlike those systems where refinement checking can be automated by SMT solvers, in Lean you construct the proof explicitly (often with the help of tactics like `omega`, `simp`, or `decide` [→ catalog/13]).

## What constraint it enforces

**A subtype value can only be constructed by providing a proof that the predicate holds; the compiler rejects construction without evidence.**

More specifically:

- **Proof-guarded construction.** You cannot create `{ x : Nat // x > 0 }` without supplying a proof that `x > 0`. This turns runtime assertions into compile-time guarantees.
- **Transparent access.** The underlying value is accessible via `.val` (or `.1`), and the proof via `.property` (or `.2`). No runtime overhead — the proof is erased.
- **Composable predicates.** You can nest subtypes or combine predicates to model complex invariants.

## Minimal snippet

```lean
def PosNat := { n : Nat // n > 0 }

def mkPosNat (n : Nat) (h : n > 0) : PosNat := ⟨n, h⟩

def double (p : PosNat) : PosNat :=
  ⟨p.val * 2, by omega⟩  -- OK: omega proves p.val * 2 > 0

-- ⟨0, by omega⟩ : PosNat  -- error: omega cannot prove 0 > 0
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Propositions as Types** [→ catalog/06] | The proof field in a subtype is a `Prop` term. Subtypes are the primary way to attach `Prop` constraints to data. |
| **Dependent Types** [→ catalog/02] | Subtypes are a special case of dependent pairs (Sigma types) where the second component is in `Prop`. |
| **Coercions** [→ catalog/10] | Lean provides a default coercion from subtypes to their base type, so `PosNat` can be used where `Nat` is expected. |
| **Proof Automation** [→ catalog/13] | `omega`, `simp`, and `decide` are commonly used to discharge subtype proof obligations. |
| **Inductive Types** [→ catalog/01] | An alternative to subtypes: define an inductive type whose constructors only admit valid values (e.g., `Fin n`). |

## Gotchas and limitations

1. **Proof obligations on every construction.** Every time you create a subtype value, you need a proof. If you're doing arithmetic that preserves the invariant (e.g., adding two positive numbers), you must prove the result still satisfies the predicate. `omega` handles many numeric cases automatically.

2. **Coercion is one-way.** Lean coerces `PosNat` to `Nat` automatically, but going the other way requires a proof. This means you can pass a `PosNat` to a function expecting `Nat`, but not vice versa.

3. **Subtype vs Fin.** `Fin n` (the type of natural numbers less than `n`) is already defined in the standard library as a structure. For bounded indices, prefer `Fin n` over `{ i : Nat // i < n }` — they are definitionally equal but `Fin` has better library support.

4. **Runtime equality.** Two subtype values with the same `.val` are propositionally equal (proof irrelevance), but this might not be definitionally equal. Use `Subtype.ext` to prove equality from `.val` equality.

5. **Complex predicates.** For predicates involving existentials or non-decidable properties, constructing proofs may require significant manual effort. Keep predicates simple and decidable when possible.

## Beginner mental model

Think of a subtype as a **value with a certificate**. The certificate proves the value meets a requirement. You can always read the value (it's public), and the certificate costs nothing at runtime (it's erased). But you can never create a certified value without actually producing the certificate — the compiler enforces this.

Coming from Rust: imagine a newtype `struct PosU32(u32)` where the constructor is private and the `new()` function panics on invalid input. Lean's subtype does the same, except instead of panicking at runtime, the check happens at compile time.

## Example A — Bounded index

```lean
def safeIndex (xs : List α) (i : { n : Nat // n < xs.length }) : α :=
  xs[i.val]'i.property   -- OK: the proof guarantees i is in bounds

def example : Char :=
  let xs := ['a', 'b', 'c']
  safeIndex xs ⟨1, by simp⟩  -- OK: simp proves 1 < 3
```

## Example B — Non-empty list

```lean
def NonEmptyList (α : Type) := { xs : List α // xs ≠ [] }

def head (nel : NonEmptyList α) : α :=
  match nel.val, nel.property with
  | x :: _, _ => x

def singleton (x : α) : NonEmptyList α :=
  ⟨[x], by simp⟩  -- OK: simp proves [x] ≠ []
```

## Common compiler errors and how to read them

### `type mismatch ... expected ... Prop`

```
type mismatch
  ...
has type
  ...
but is expected to have type
  n > 0 : Prop
```

**Meaning:** You tried to construct a subtype without providing the correct proof. The second component of the anonymous constructor `⟨val, proof⟩` must be a proof of the predicate.

### `omega failed to prove`

```
omega failed to prove the goal
  ⊢ 0 > 0
```

**Meaning:** The numeric invariant doesn't hold. Your value doesn't satisfy the subtype predicate. Fix the value or the predicate.

### Coercion-related errors

```
application type mismatch
  f x
argument
  x
has type
  { n : Nat // n > 0 } : Type
but is expected to have type
  Nat : Type
```

**Meaning:** Automatic coercion didn't fire (rare — usually it does). Explicitly write `x.val` to extract the underlying value.

## Proof perspective (brief)

Subtypes correspond to *subset types* in type theory — `{ x : α // P x }` is the type-theoretic analog of the set `{ x ∈ α | P(x) }`. Because the proof component lives in `Prop`, it is proof-irrelevant and erased: two elements with the same `.val` are equal regardless of how the proofs were constructed. This makes subtypes the standard way to formalize "the naturals greater than 0" or "the sorted lists" in Lean's mathematical library (Mathlib).

## Use-case cross-references

- [→ UC-01](../usecases/UC01-invalid-states.md) — Subtypes make invalid values unconstructable by requiring proof.
- [→ UC-02](../usecases/UC02-domain-modeling.md) — Model domain constraints (positive, bounded, non-empty) as subtype predicates.
- [→ UC-04](../usecases/UC12-compile-time.md) — Attach compile-time invariants directly to data.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 7 "Inductive Types" (Subtypes section)
- *Functional Programming in Lean* — "Subtypes" section
- Lean 4 source: `Init.Prelude` (`Subtype`)
