# Existential Types

> **Since:** Lean 4 (stable)

## What it is

An existential type asserts "there exists a value of some type satisfying a property." In Lean, existential quantification is built into the logic via `∃ (x : α), P x` (notation for `Exists (fun x => P x)`) and into data via **Sigma types** (`Σ (x : α), β x` or `(x : α) × β x`).

`∃` lives in `Prop` (the universe of propositions) and is used for logical statements -- you can prove `∃ n : Nat, n > 5` by exhibiting a witness (e.g., `⟨6, by omega⟩`). Sigma types (`Σ`) live in `Type` and carry computationally-relevant data -- a `Σ (n : Nat), Fin n` pairs a natural number with a value bounded by it, and both components are accessible at runtime.

Structures with type-valued fields provide a third encoding: `structure DynValue where { T : Type; val : T }` packages a type and a value of that type, hiding the concrete `T` behind the structure.

## What constraint it enforces

**An existential type hides the witness type from consumers. The type checker ensures you can only use the existential value through its declared interface or by eliminating the existential with pattern matching.**

- `∃ x, P x` hides `x` -- you can only eliminate it in `Prop` (proof-irrelevant) context, not extract the witness into computational code.
- Sigma types allow extracting both the witness and the dependent value, but the consumer must handle all possible witness types.
- Structure-based existentials hide the type field unless the consumer explicitly pattern-matches.

## Minimal snippet

```lean
-- Existential in Prop: "there exists an even natural number > 10"
theorem exists_large_even : ∃ n : Nat, n > 10 ∧ n % 2 = 0 :=
  ⟨12, by omega, by omega⟩

-- Sigma type in Type: a number paired with a proof it is positive
def positivePair : (n : Nat) × (n > 0) :=
  ⟨42, by omega⟩

#eval positivePair.1   -- 42 (accessible at runtime)
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dependent types** [-> catalog/T09](T09-dependent-types.md) | Sigma types are dependent pairs -- the type of the second component depends on the value of the first. `(n : Nat) × Fin n` is a dependent existential. |
| **Propositions as types** [-> catalog/T29](T29-propositions-as-types.md) | `∃ x, P x` is a proposition; its proof is a pair of a witness and evidence. The Curry-Howard correspondence makes existential quantification a type. |
| **Refinement types** [-> catalog/T26](T26-refinement-types.md) | `{ x : α // P x }` is a Sigma type restricted to `Prop` predicates -- a value bundled with a proof, which is the most common existential pattern in practice. |
| **Inductive types** [-> catalog/T01](T01-algebraic-data-types.md) | `Exists` and `Sigma` are themselves inductive types with a single constructor `⟨witness, proof⟩`. Custom inductive types can encode domain-specific existentials. |
| **Universes** [-> catalog/T35](T35-universes-kinds.md) | `Exists` lives in `Prop` (large elimination restricted). `Sigma` lives in `Type` (full elimination allowed). Choosing between them depends on whether the witness must be computationally accessible. |

## Gotchas and limitations

1. **No large elimination from `Prop`.** Given `h : ∃ n, P n`, you cannot extract the `n` into a `Type`-level computation. Use `Sigma` instead if you need the witness at runtime. This is the most common surprise for beginners.

   ```lean
   -- This FAILS:
   -- def getWitness (h : ∃ n : Nat, n > 5) : Nat := h.1  -- error
   -- Use Sigma instead:
   def getWitness (h : (n : Nat) × (n > 5)) : Nat := h.1  -- OK
   ```

2. **Exists vs Sigma naming.** `∃` is `Exists` (in `Prop`), `Σ` is `Sigma` (in `Type`). The notation is similar but the universes differ. Confusing them leads to universe errors.

3. **Proof irrelevance for Exists.** Two proofs of `∃ n, P n` are considered equal in `Prop`, even if they use different witnesses. You cannot distinguish which witness was used.

4. **Anonymous constructor ambiguity.** `⟨a, b⟩` syntax works for both Sigma types and structures, but the expected type must be unambiguous. When multiple structures match, use named constructors.

5. **Existentials in structures complicate instance search.** A structure with `(T : Type)` field creates an existential that type class synthesis cannot automatically resolve. You may need to provide the type explicitly.

## Beginner mental model

Think of `∃ x, P x` as a **locked exhibit with a label**. The label says "inside this case is a number greater than 10 that is even." You can read the label (use the proposition in proofs) but you cannot open the case and take the number out for computation. A Sigma type `(n : Nat) × (n > 10)` is the same exhibit with a glass case -- you can see and use the number.

## Example A -- Existential proof in theorem proving

```lean
-- Prove there exists a prime greater than 100
-- (simplified: we just exhibit one)
theorem exists_large_prime : ∃ p : Nat, p > 100 ∧ Nat.Prime p :=
  ⟨101, by omega, by decide⟩

-- Use the existential in another proof
theorem not_all_small_primes : ¬ (∀ p : Nat, Nat.Prime p → p ≤ 100) := by
  intro h
  obtain ⟨p, hp_large, hp_prime⟩ := exists_large_prime
  have := h p hp_prime
  omega
```

## Example B -- Sigma type for heterogeneous data

```lean
structure DynValue where
  T : Type
  val : T
  show : T → String

def mkDyn [ToString α] (v : α) : DynValue :=
  { T := α, val := v, show := toString }

def display (d : DynValue) : String :=
  d.show d.val   -- works without knowing the concrete type

#eval display (mkDyn 42)       -- "42"
#eval display (mkDyn "hello")  -- "hello"

-- Heterogeneous list
def dynList : List DynValue := [mkDyn 42, mkDyn "hello", mkDyn true]
#eval dynList.map display      -- ["42", "hello", "true"]
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Existential types hide internal representations, ensuring clients cannot construct invalid values.
- [-> UC-02](../usecases/UC02-domain-modeling.md) -- Sigma types pair domain values with their invariant proofs, encoding "a valid X" as a type.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Existential constraints let generic code require "some type exists with property P" without fixing the type.

## Source anchors

- *Theorem Proving in Lean 4* -- Ch. 4 "Quantifiers and Equality" (existential quantifier)
- *Theorem Proving in Lean 4* -- Ch. 2 "Dependent Type Theory" (Sigma types)
- *Functional Programming in Lean* -- "Structures" (type-valued fields)
- Lean 4 source: `Init.Prelude` (`Exists`, `Sigma`, `PSigma`)
