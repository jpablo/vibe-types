# Witness and Evidence Types

> **Since:** Lean 4 (stable)

## What it is

In Lean, propositions ARE types and proofs ARE values. A "witness" or "evidence" is simply a term that inhabits a proposition type. If `h : n > 0`, then `h` is a witness (proof) that `n` is positive. This is the Curry-Howard correspondence taken literally -- there is no separate proof language; the same term language that builds data also builds proofs.

The `Decidable` type class bridges the gap between compile-time propositions and runtime decisions: `Decidable (P)` provides either a proof of `P` or a proof of `Not P`, enabling runtime branching on propositions. Tactics like `by decide` and `by omega` construct witnesses automatically when the proposition falls within a decidable fragment.

## What constraint it enforces

**A function requiring a witness of type `P` cannot be called unless the caller provides a term of type `P`. The kernel verifies the proof term, making it impossible to bypass the obligation.**

- A parameter `(h : n > 0)` forces the caller to prove positivity.
- `Decidable` instances let `if` expressions branch on propositions with automatic proof extraction.
- `Fact` and `have` introduce local witnesses that subsequent code can use.

## Minimal snippet

```lean
def safeDiv (a : Nat) (b : Nat) (h : b ≠ 0) : Nat :=
  a / b    -- OK: the proof h guarantees no division by zero

#eval safeDiv 10 3 (by decide)   -- 3
-- safeDiv 10 0 (by decide)      -- error: failed to prove 0 ≠ 0
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Propositions as types** [-> catalog/T29](T29-propositions-as-types.md) | Witness/evidence IS propositions-as-types. Every proof obligation is a type, every proof is a value inhabiting it. |
| **Dependent types** [-> catalog/T09](T09-dependent-types.md) | Evidence parameters are dependent types -- the type of later arguments can depend on earlier proof values. `(n : Nat) -> n > 0 -> Fin n` uses evidence dependently. |
| **Refinement types** [-> catalog/T26](T26-refinement-types.md) | `{ x : Nat // x > 0 }` bundles a value with its evidence into a subtype. This is syntactic sugar for a Sigma type with a `Prop`-valued second component. |
| **Proof automation** [-> catalog/T30](T30-proof-automation.md) | `by decide`, `by omega`, `by simp` construct witnesses automatically. The programmer states the obligation; tactics find the proof. |
| **Type classes** [-> catalog/T05](T05-type-classes.md) | `Decidable` is a type class. Instance synthesis finds decision procedures automatically, so `if n > 0 then ...` works without manual proof when `Decidable (n > 0)` is in scope. |

## Gotchas and limitations

1. **Proof obligations can be hard to discharge.** While `by decide` handles concrete values and `by omega` handles linear arithmetic, complex propositions may require manual proof construction or custom tactics.

2. **Prop vs Type universe.** Witnesses in `Prop` are computationally irrelevant -- the compiler can erase them. But you cannot extract data from a `Prop` witness into a `Type` computation (no large elimination from `Prop`) unless the target type has at most one constructor.

3. **Decidable is not always available.** Not all propositions are decidable. Checking `Decidable (∃ x, P x)` for infinite domains requires custom instances or is simply impossible. Missing `Decidable` instances cause "failed to synthesize" errors on `if` expressions.

4. **Proof terms can bloat.** Kernel-checked proofs are terms in the environment. Very large proofs (e.g., from brute-force `decide` on large finite cases) can slow down the kernel and increase memory usage.

5. **`sorry` escapes the system.** `sorry` provides a fake witness for any proposition. It silences errors but marks the declaration as unverified. Production code should never contain `sorry`.

## Beginner mental model

Think of evidence as a **ticket** that proves you are allowed to do something. Calling `safeDiv 10 b h` requires a ticket `h` proving `b` is not zero. The Lean kernel is the ticket inspector -- it verifies every ticket is genuine. Tactics like `by omega` are ticket-printing machines for common cases. If no machine can print the ticket, you must construct it by hand (write the proof yourself).

## Example A -- Fin as evidence of bounded index

```lean
-- Fin n is a natural number with evidence that it is < n
def safeIndex (xs : Array α) (i : Fin xs.size) : α :=
  xs[i]    -- no bounds check needed; Fin carries the proof

def example : Nat :=
  let arr := #[10, 20, 30]
  safeIndex arr ⟨1, by omega⟩   -- 20
  -- safeIndex arr ⟨5, by omega⟩ -- error: omega cannot prove 5 < 3
```

## Example B -- Decidable for runtime evidence

```lean
def describeSign (n : Int) : String :=
  if h : n > 0 then
    -- h : n > 0 is available as evidence here
    s!"{n} is positive (proof: {repr h})"
  else if h2 : n < 0 then
    s!"{n} is negative"
  else
    -- we know n = 0 from exhaustion
    "zero"

#eval describeSign 42     -- "42 is positive ..."
#eval describeSign (-3)   -- "-3 is negative"
#eval describeSign 0      -- "zero"
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Evidence parameters make invalid calls unrepresentable: you cannot call `safeDiv` with a zero divisor.
- [-> UC-02](../usecases/UC02-domain-modeling.md) -- Domain invariants (positive balance, sorted list, valid index) are encoded as evidence types.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Generic functions carry evidence constraints that callers must satisfy, ensuring correctness across all instantiations.

## Source anchors

- *Theorem Proving in Lean 4* -- Ch. 4 "Propositions and Proofs"
- *Theorem Proving in Lean 4* -- Ch. 8 "Type Classes" (Decidable)
- *Functional Programming in Lean* -- "Propositions, Decisions, and Proofs"
- Lean 4 source: `Init.Prelude` (`Decidable`, `Fact`)
