# Compile-Time Invariants

## The constraint

Attach invariants to data so that the compiler verifies them via proofs. Invalid data cannot be constructed because the required proof cannot be produced.

## Feature toolkit

- [→ catalog/06](../catalog/T29-propositions-as-types.md) — Propositions as types encode invariants as `Prop`; construction requires proof terms.
- [→ catalog/02](../catalog/T09-dependent-types.md) — Dependent types let types carry value-level constraints.
- [→ catalog/14](../catalog/T26-refinement-types.md) — Subtypes bundle values with proofs of predicates.
- [→ catalog/13](../catalog/T30-proof-automation.md) — Tactics (`omega`, `simp`, `decide`) discharge proof obligations automatically.

## Patterns

### Pattern A — Subtype with arithmetic invariant

```lean
def EvenNat := { n : Nat // n % 2 = 0 }

def mkEven (n : Nat) (h : n % 2 = 0) : EvenNat := ⟨n, h⟩

def four : EvenNat := ⟨4, by decide⟩       -- OK
-- def three : EvenNat := ⟨3, by decide⟩   -- error: 3 % 2 = 0 is false
```

### Pattern B — Structure with proof field

```lean
structure SortedList (α : Type) [Ord α] where
  data : List α
  sorted : data.Pairwise (fun a b => Ord.compare a b |>.isLT)

-- Construction requires proof that the list is sorted
-- Operations that maintain sortedness carry the proof forward
```

### Pattern C — Dependent function precondition

```lean
def unsafeGet (xs : Array α) (i : Nat) (h : i < xs.size) : α :=
  xs[i]  -- OK: the bound check is a compile-time proof, not a runtime check

-- Callers must prove the index is in bounds:
def firstElement (xs : Array α) (h : xs.size > 0) : α :=
  unsafeGet xs 0 (by omega)
```

### Pattern D — Proof automation at scale

```lean
def Fin.addWrap (a b : Fin n) : Fin n :=
  ⟨(a.val + b.val) % n, by omega⟩  -- omega proves (a+b) % n < n

def Fin.double (a : Fin n) (h : n > 0) : Fin n :=
  ⟨(a.val * 2) % n, Nat.mod_lt _ h⟩
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Subtypes | Lightweight; compose naturally | Every construction site needs a proof |
| Proof fields | Invariant travels with the data | Must maintain proof through transformations |
| Dependent preconditions | Shifts checks to compile time | Caller burden increases |
| Proof automation | Reduces manual proof burden | Tactics have scope limits (linear arithmetic, etc.) |

## When to use which feature

- **Numeric bounds** (index < size, value > 0) → subtypes + `omega`.
- **Structural properties** (sorted, balanced, acyclic) → structures with proof fields.
- **Function preconditions** (non-null, valid state) → Prop arguments.
- **Complex invariants** → combine subtypes with custom `simp` lemmas.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 3 "Propositions and Proofs", Ch. 7 "Inductive Types"
- *Functional Programming in Lean* — "Propositions, Proofs, and Indexing"
