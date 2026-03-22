# Propositions as Types (Prop and Proof Terms)

> **Since:** Lean 4 (stable)

## What it is

In Lean, propositions (logical statements) are types, and proofs are values inhabiting those types. The universe `Prop` contains types that represent logical facts — `2 + 2 = 4` is a type, and a proof of it is a term of that type. When you write a function that requires a proof argument (e.g., `h : n > 0`), the compiler demands *evidence* — you must construct a term that proves the proposition. This is the Curry-Howard correspondence made practical: the same type checker that validates your data types also validates your logical assertions.

From a programming perspective, `Prop` types act as compile-time assertions. They are erased at runtime (they have no computational content), but the compiler guarantees that the assertion was verified during type checking.

## What constraint it enforces

**Logical invariants encoded as `Prop` types must be accompanied by proof terms; the compiler rejects code that lacks evidence.**

More specifically:

- **Proof obligations.** If a function signature includes a `Prop` argument (e.g., `n ≠ 0`), callers must supply a proof. The compiler won't let you skip it.
- **Proof irrelevance.** Two proofs of the same `Prop` are considered equal — the *content* of the proof doesn't matter, only its existence. This means `Prop` types carry zero runtime cost.
- **Elimination restriction.** You generally cannot extract computational data from a `Prop` (large elimination is restricted). A proof that "there exists an `n`" doesn't let you compute with that `n` unless you use `Decidable` or work in `Type`.

## Minimal snippet

```lean
def safeDiv (a b : Nat) (h : b ≠ 0) : Nat :=
  a / b  -- OK: the proof h guarantees b is nonzero

-- safeDiv 10 0 ???  -- error: you must provide a proof that 0 ≠ 0 (which is impossible)
#eval safeDiv 10 3 (by decide)  -- OK: `decide` proves 3 ≠ 0
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dependent Types** [→ catalog/02] | Propositions-as-types is a dependent typing pattern — the proof argument's type depends on the value arguments. |
| **Inductive Types** [→ catalog/01] | Core propositions (`And`, `Or`, `Exists`, `Eq`) are inductive types in `Prop`. |
| **Subtypes** [→ catalog/14] | `{ x : α // P x }` bundles a value with a `Prop` proof — the main programming interface for proof-carrying data. |
| **Proof Automation** [→ catalog/13] | Tactics like `simp`, `decide`, and `omega` automate constructing proof terms. |
| **Universes** [→ catalog/05] | `Prop` is `Sort 0`, the bottom of the universe hierarchy. Its special properties (proof irrelevance, restricted elimination) distinguish it from `Type`. |
| **Termination** [→ catalog/07] | Termination proofs are `Prop` terms — you prove that a measure decreases on each recursive call. |

## Gotchas and limitations

1. **Proof irrelevance means no pattern matching into `Type`.** You cannot `match` on a proof of `∃ x, P x` to extract `x` into a computation. Use `Decidable` instances or `Classical.choice` (noncomputable) to bridge the gap.

2. **`decide` only works for `Decidable` propositions.** The `decide` tactic evaluates the proposition and produces a proof, but only if the proposition has a `Decidable` instance. For `Nat` comparisons, `Bool` operations, and finite types, this works. For arbitrary propositions over infinite domains, it doesn't.

3. **`sorry` is the escape hatch.** Writing `sorry` fills in any proof obligation, but it marks the definition as unsound. The compiler emits a warning. Use it during development, never in production [→ UC-10].

4. **`Prop` vs `Bool`.** `Prop` is a logical assertion checked at compile time; `Bool` is a runtime boolean. They are connected via `Decidable`: if `P : Prop` has a `Decidable P` instance, you can use `if P then ... else ...` in code, and the compiler inserts the decision procedure.

5. **Classical vs constructive.** By default, Lean is constructive — you must produce evidence. Importing `Classical` gives you the law of excluded middle and `choice`, making all propositions decidable but potentially noncomputable.

## Beginner mental model

Think of `Prop` as a **compile-time assertion that requires proof**. When a function asks for `h : n > 0`, it's like a function precondition, except the compiler *enforces* it — you can't call the function without proving the precondition holds. The proof is erased at runtime, so there's no cost; it's purely a compile-time check.

Coming from Rust: imagine if `assert!(n > 0)` were checked at compile time instead of panicking at runtime. That's what `Prop` gives you.

## Example A — Proof-carrying preconditions

```lean
structure PosNat where
  val : Nat
  pos : val > 0   -- Prop field: proof that val is positive

def mkPosNat (n : Nat) (h : n > 0) : PosNat :=
  ⟨n, h⟩

#eval (mkPosNat 5 (by omega)).val  -- OK: omega proves 5 > 0

-- mkPosNat 0 (by omega)
-- error: omega fails to prove 0 > 0
```

## Example B — Using Decidable for runtime decisions

```lean
def classify (n : Nat) : String :=
  if n % 2 = 0 then    -- OK: Nat equality is Decidable
    "even"
  else
    "odd"

-- The `if` desugars to `if h : n % 2 = 0 then ... else ...`
-- where h is a proof term automatically managed by the Decidable instance
```

## Common compiler errors and how to read them

### `type mismatch ... expected ... Prop`

```
type mismatch
  true
has type
  Bool : Type
but is expected to have type
  ... : Prop
```

**Meaning:** You used a `Bool` value (`true`/`false`) where a `Prop` proof was expected. Use `decide`, `by simp`, or construct a proof term instead.

### `failed to synthesize instance Decidable`

```
failed to synthesize instance
  Decidable (P x)
```

**Meaning:** You used `if P x then ... else ...` but `P x` has no `Decidable` instance. Either provide one, use a `Bool`-valued function instead, or restructure to avoid runtime branching on the proposition.

### `declaration uses 'sorry'`

```
declaration 'myDef' uses 'sorry'
```

**Meaning:** Your definition depends on an unproven proposition. Replace `sorry` with an actual proof before the code is considered sound.

## Proof perspective (brief)

Propositions-as-types *is* the proof perspective. In Lean, `p : P` means "p is a proof of proposition P." Function types are universal quantifiers: `(n : Nat) → n > 0 → Q n` means "for all natural numbers n, if n > 0 then Q(n)." Applying a function is *modus ponens*; constructing a lambda is introducing a universal quantifier. The entire logical framework is the type system — there is no separate proof language.

## Use-case cross-references

- [→ UC-01](../usecases/UC01-invalid-states.md) — Prop-based preconditions make invalid states unconstructable.
- [→ UC-04](../usecases/UC12-compile-time.md) — Compile-time invariants are propositions that must be proved at construction.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 3 "Propositions and Proofs"
- *Functional Programming in Lean* — "Propositions, Proofs, and Indexing"
- Lean 4 source: `Init.Prelude` (`Prop`, `Decidable`)
