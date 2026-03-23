# Erased and Phantom Types — Prop, Proof Erasure, and Subsingleton

> **Since:** Lean 4 (stable)

## What it is

Lean has a built-in universe `Prop` for propositions. All values in `Prop` are **erased at runtime** — proofs carry zero runtime cost. This is not an optimization; it is a fundamental design principle. The compiler guarantees that no runtime code depends on *which* proof was provided, only *that* one exists.

Key concepts:

- **`Prop`** — The universe of propositions. Types in `Prop` are logically meaningful but computationally irrelevant.
- **Proof irrelevance.** Any two proofs of the same proposition are considered equal: if `h₁ h₂ : P`, then `h₁ = h₂`. The runtime never distinguishes between them.
- **Subsingleton.** A type with at most one inhabitant. All `Prop` types are subsingletons. `Subsingleton α` is a type class.
- **Universe separation.** A `Prop`-valued match can only produce a `Prop` result (with exceptions for subsingletons). This prevents extracting computational content from proofs.

This means that dependent types carrying proof obligations — `{ x : Nat // x > 0 }`, `Fin n`, proof arguments — add **zero runtime overhead** for the proof component.

## What constraint it enforces

**Proof terms in `Prop` are erased at runtime; the type system tracks them at compile time for safety but they have no runtime cost.**

More specifically:

- **Zero-cost proofs.** Subtype proofs, `Fin` bound proofs, and precondition proofs are all erased. The runtime value of `{ x : Nat // x > 0 }` is just a `Nat`.
- **No proof inspection.** Runtime code cannot branch on which proof was provided. Two values differing only in their proof component are operationally identical.
- **Large elimination restriction.** You cannot pattern-match on a `Prop` to produce data in `Type`. This prevents proofs from affecting computation (with exceptions for subsingletons like `Decidable`).

## Minimal snippet

```lean
-- The proof `h` is erased at runtime; only `n` exists at runtime
def safeDiv (a : Nat) (b : Nat) (h : b ≠ 0) : Nat :=
  a / b

-- Subtype: proof is erased, only the Nat is kept at runtime
def posNat : { n : Nat // n > 0 } := ⟨42, by omega⟩

-- At runtime, posNat is just the number 42
#eval posNat.val   -- 42
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Propositions as Types** [→ catalog/T29](T29-propositions-as-types.md) | `Prop` is the universe where propositions live. Proof erasure means proofs are compile-time only. |
| **Dependent Types** [→ catalog/T09](T09-dependent-types.md) | Dependent types often carry `Prop` proof obligations. Erasure means these add no runtime cost. |
| **Refinement Types** [→ catalog/T26](T26-refinement-types.md) | Subtypes `{ x : α // P x }` carry an erased proof. The runtime representation is just `α`. |
| **Universes** [→ catalog/T35](T35-universes-kinds.md) | `Prop` is at the bottom of the universe hierarchy, below `Type 0`. Universe separation enforces the erasure boundary. |
| **Compile-Time Ops** [→ catalog/T16](T16-compile-time-ops.md) | `decide` produces a `Prop` proof at compile time, which is then erased — zero runtime cost for the verification. |

## Gotchas and limitations

1. **Large elimination restriction.** You cannot match on `Or P Q` (a `Prop`) to produce a `Type` result. Use `Decidable` or `Sum` instead when you need computational content from a disjunction.

2. **`Decidable` is the escape hatch.** `Decidable P` lives in `Type` (not `Prop`) and wraps a proof of `P ∨ ¬P`. This is how `if h : P then ... else ...` works — it extracts computational content from a proposition.

3. **Not the same as Haskell phantom types.** In Haskell, phantom type parameters appear in the type but not in the value. Lean's erased proofs are conceptually different — they are present in the value at the type level but erased during compilation.

4. **`Prop` autocompletion confuses beginners.** Lean's `Prop` is `Sort 0`, while `Type` is `Sort 1`. The universe hierarchy can be confusing. Just remember: `Prop` = proofs (erased), `Type` = data (kept).

## Beginner mental model

Think of proofs as **safety seals on a package**. At the factory (compile time), the seal proves the package was properly assembled. Once shipped (runtime), the seal is removed — the package works without it. The seal costs nothing to ship, but the factory refuses to ship packages without valid seals.

Coming from Rust: There is no direct Rust equivalent. The closest analogy is `PhantomData<T>`, which is zero-sized. But Lean's proof erasure is much more powerful — entire proof *computations* are erased, not just marker types.

## Example A — Proof-carrying function with zero runtime cost

```lean
def checkedIndex (xs : Array α) (i : Nat) (h : i < xs.size) : α :=
  xs[i]  -- h is erased; only xs and i exist at runtime

#eval checkedIndex #["a", "b", "c"] 1 (by omega)  -- "b"
```

## Example B — Subsingleton elimination

```lean
-- Decidable lives in Type, so it can branch computationally
def isEven (n : Nat) : Bool :=
  if n % 2 = 0 then true else false
  -- The `if h : P then ... else ...` syntax uses Decidable,
  -- which provides computational content from a Prop

-- Direct Prop elimination into Prop is always allowed
theorem even_or_odd (n : Nat) : n % 2 = 0 ∨ n % 2 = 1 := by omega
```

## Use-case cross-references

- [→ UC-12](../usecases/UC12-compile-time.md) — Proof erasure enables zero-cost compile-time verification.
- [→ UC-01](../usecases/UC01-invalid-states.md) — Erased proofs enforce invariants with no runtime penalty.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 3 "Propositions and Proofs" (Prop universe)
- *Theorem Proving in Lean 4* — Ch. 7 "Inductive Types" (large elimination)
- Lean 4 source: `Lean.Compiler.CompilerM` (erasure pass)
