# Subtypes and Refinement Types

> **Since:** Lean 4 (stable)

## What it is

A subtype in Lean is a value paired with a proof that the value satisfies a predicate. Written `{ x : α // P x }`, it bundles a value `x` of type `α` together with evidence `h : P x` — a `Prop` proof that the predicate `P` holds for `x`. The proof is erased at runtime, so a subtype has the same runtime representation as the underlying type, but at compile time, construction is impossible without proving the predicate.

This is Lean's version of *refinement types* found in languages like Liquid Haskell or F*. Unlike those systems where refinement checking can be automated by SMT solvers, in Lean you construct the proof explicitly (often with the help of tactics like `omega`, `simp`, or `decide` [→ catalog/T30](T30-proof-automation.md)).

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
  ⟨p.val * 2, by have := p.property; omega⟩  -- OK: p.property gives p.val > 0, so omega proves p.val * 2 > 0

-- error: omega could not prove the goal — 0 > 0 is false, so the proof obligation is unmet
def zero : PosNat := ⟨0, by omega⟩
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Propositions as Types** [→ catalog/T29](T29-propositions-as-types.md) | The proof field in a subtype is a `Prop` term. Subtypes are the primary way to attach `Prop` constraints to data. |
| **Dependent Types** [→ catalog/T09](T09-dependent-types.md) | Subtypes are a special case of dependent pairs (Sigma types) where the second component is in `Prop`. |
| **Coercions** [→ catalog/T18](T18-conversions-coercions.md) | Core registers a `CoeOut (Subtype p) α`, so a value whose type is *visibly* a subtype coerces to the base type. Hide the subtype behind a plain `def` and the instance no longer applies — use `abbrev`, or write `.val`. |
| **Proof Automation** [→ catalog/T30](T30-proof-automation.md) | `omega`, `simp`, and `decide` are commonly used to discharge subtype proof obligations. |
| **Inductive Types** [→ catalog/T01](T01-algebraic-data-types.md) | An alternative to subtypes: define an inductive type whose constructors only admit valid values (e.g., `Fin n`). |

## Gotchas and limitations

1. **Proof obligations on every construction.** Every time you create a subtype value, you need a proof. If you're doing arithmetic that preserves the invariant (e.g., adding two positive numbers), you must prove the result still satisfies the predicate. `omega` handles many numeric cases automatically.

2. **Coercion is one-way — and only when Lean can *see* the subtype.** The core instance is `CoeOut (Subtype p) α`; it fires when the term's type reduces to a `Subtype` during instance search. A named alias declared with a plain `def` blocks that, because `def` is only semireducible:

   ```lean
   abbrev PosA := { n : Nat // n > 0 }
   def    PosD := { n : Nat // n > 0 }

   def fiveA : PosA := ⟨5, by omega⟩
   def fiveD : PosD := ⟨5, by omega⟩

   def useNat (n : Nat) : Nat := n + 1

   #eval useNat fiveA        -- 6   — coercion fires through the abbrev
   #eval useNat fiveD.val    -- 6   — must project by hand
   ```

   Going the other way (`Nat` → `PosNat`) always requires a proof; there is no coercion in that direction.

3. **Subtype vs Fin.** `Fin n` is a *structure of its own* (`⟨val, isLt⟩`), not notation for `{ i : Nat // i < n }`. The two are isomorphic but **not** definitionally equal — `example : Fin 3 = { i : Nat // i < 3 } := rfl` is a type mismatch. Prefer `Fin n` for bounded indices anyway: it has far better library support, and convert explicitly (`⟨s.val, s.property⟩`) when you need to cross over.

4. **Equality of subtype values.** Proof irrelevance is *definitional* in Lean 4, so two proofs of the same `Prop` are equal by `rfl`. What `Subtype.ext` does is different: it lifts a *proved* equality of the `.val` fields up to equality of the subtype values.

   ```lean
   example (h₁ h₂ : (2:Nat) > 0) : h₁ = h₂ := rfl          -- definitional proof irrelevance
   example (a b : { n : Nat // n > 0 }) (h : a.val = b.val) : a = b := Subtype.ext h
   ```

5. **Complex predicates.** For predicates involving existentials or non-decidable properties, constructing proofs may require significant manual effort. Keep predicates simple and decidable when possible.

## Beginner mental model

Think of a subtype as a **value with a certificate**. The certificate proves the value meets a requirement. You can always read the value (it's public), and the certificate costs nothing at runtime (it's erased). But you can never create a certified value without actually producing the certificate — the compiler enforces this.

Coming from Rust: imagine a newtype `struct PosU32(u32)` whose constructor is private, so the only way in is a checked `new()`. Lean's subtype is the same idea with a stronger guarantee: the check cannot be *skipped*. It does not always disappear — for a value known at compile time the proof is discharged by a tactic and nothing survives to runtime, but for a value that arrives at runtime you still branch (`if h : n > 0 then ⟨n, h⟩ else …`) exactly as Rust's `new()` does. The difference is that Lean will not let you build the value on the `else` side.

## Example A — Bounded index

```lean
def safeIndex (xs : List α) (i : { n : Nat // n < xs.length }) : α :=
  xs[i.val]'i.property   -- OK: the proof guarantees i is in bounds

def demo : Char :=
  let xs := ['a', 'b', 'c']
  safeIndex xs ⟨1, by decide⟩  -- OK: decide proves 1 < 3
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

### `omega could not prove the goal`

```
omega could not prove the goal:
No usable constraints found. You may need to unfold definitions so `omega` can
see linear arithmetic facts about `Nat` and `Int`, which may also involve
multiplication, division, and modular remainder by constants.
```

**Meaning:** `omega` gave up. The header is always `omega could not prove the goal:`; what follows is a diagnostic. `No usable constraints found` means nothing in the goal or context looked like linear arithmetic — which is what you get from `⟨0, by omega⟩`, since the goal `0 > 0` closes over no hypotheses. When there *are* hypotheses, the diagnostic is instead `a possible counterexample may satisfy the constraints …` followed by the constraint set. Either way: fix the value, or bring the missing facts into scope with `have := p.property`.

### Coercion-related errors

```
Application type mismatch: The argument
  fiveD
has type
  PosD
but is expected to have type
  Nat
in the application
  useNat fiveD
```

**Meaning:** The subtype-to-base coercion did not fire, because the argument's type is a plain `def` alias rather than a visible `Subtype`. Write `fiveD.val`, or declare the alias with `abbrev` so instance search can see through it.

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
