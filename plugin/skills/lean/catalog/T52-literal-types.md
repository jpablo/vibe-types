# Literal Types (Subsumed by Dependent Types)

> **Since:** Lean 4 — no separate feature; dependent types have always provided this capability

## What it is

Lean 4 does not have a distinct "literal type" feature because its **dependent type system** already allows any value to appear in a type. Where Scala 3 has singleton types (`42: 42`) and Python has `Literal["GET"]`, Lean simply lets you write types that mention values directly: `Fin 3` (natural numbers less than 3), `Vector α 5` (a vector of exactly 5 elements), or `{ n : Nat // n = 42 }` (the subtype containing only 42).

In a dependently-typed language, the boundary between "value" and "type" is fluid. A function's return type can depend on its argument's value, and propositions about values (like `n < 10`) can be required as proof obligations. Singleton types are just the trivial case of this: `{ n : Nat // n = 42 }` is a type with exactly one natural number inhabitant.

## What constraint it enforces

**Any value-level constraint can be encoded in the type. The type checker (which is also a proof checker) verifies that the constraint holds, either by computation or by requiring an explicit proof term.**

- `Fin n` enforces that a value is in `{0, ..., n-1}` — the bound is part of the type.
- `Vector α n` enforces that the collection has exactly `n` elements.
- Subtypes `{ x : T // P x }` enforce any predicate `P` on values of type `T` — decidable or not; what you must supply is a proof for the particular element.
- Equality types `a = b` can serve as singleton witnesses.

## Minimal snippet

```lean
-- A natural number that is exactly 42 (singleton type, Lean style)
def theAnswer : { n : Nat // n = 42 } := ⟨42, rfl⟩

-- Fin n: naturals less than n (value-indexed type)
def two : Fin 5 := ⟨2, by omega⟩
-- def bad : Fin 5 := ⟨7, by omega⟩  -- fails: 7 < 5 is false

-- Vector with length in the type
def triple : Vector String 3 := #v["a", "b", "c"]
-- def bad : Vector String 3 := #v["a", "b"]  -- error: expected length 3
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dependent types** [-> catalog/T09](T09-dependent-types.md) | Literal types are a trivial instance of dependent types. `Fin 3` is a dependent pair `(n : Nat, n < 3)`. Everything in this entry is a special case of T09. |
| **Refinement types** [-> catalog/T26](T26-refinement-types.md) | `{ x : T // P x }` subtype notation is Lean's refinement types. Singleton types are refinements where `P x` is `x = v` for a specific value `v`. |
| **Type classes** [-> catalog/T05](T05-type-classes.md) | Instances can be parameterized by values: `instance : ToString (Fin n)` works for any `n`. Type class resolution interacts with value-indexed types. |
| **Termination checking** [-> catalog/T28](T28-termination.md) | Functions over `Fin n` or `Vector α n` often use structural recursion on the index, which the termination checker verifies. |
| **Proof automation** [-> catalog/T30](T30-proof-automation.md) | Tactics like `omega`, `decide`, and `simp` discharge numeric obligations (e.g., `2 < 5`) automatically. |

## Gotchas and limitations

1. **No special syntax for singletons.** Unlike TypeScript's `42` type or Scala 3's `val x: 42 = 42`, Lean requires you to spell out the constraint: `{ n : Nat // n = 42 }`. This is more verbose but strictly more general.

2. **Proof obligations can be heavy.** When you create a `Fin n` or a refined subtype, Lean requires a proof that the constraint holds. For literals, `by omega` or `by decide` usually suffices, but complex constraints may require manual proofs.

3. **Nat literals are polymorphic.** The literal `42` in Lean has type `Nat` by default, not a singleton type. To get a constrained type, you must explicitly use `Fin`, a subtype, or a proof-carrying construction.

4. **The coercion runs downhill only.** `Fin n → Nat` *is* automatic — core provides the coercion and Lean inserts it for you, so `double x` elaborates for `x : Fin 100` and `#check (x : Nat)` prints `↑x`. Writing `.val` is optional. The direction that does not exist is `Nat → Fin n`: a bare `Nat` carries no bound, so `(n : Fin 5)` for `n : Nat` is a plain `Type mismatch`. Build it with a proof (`⟨n, h⟩`) or a total wrapping operation (`Fin.ofNat n : Fin k`, which reduces mod `k` and needs `[NeZero k]`).

5. **Decidability is about tactics, not about subtypes.** `{ x : T // P x }` imposes no decidability requirement on `P` whatsoever. You need a proof for the one element you are constructing, and that proof can be an ordinary constructive term even when `P` has no `Decidable` instance at all — `⟨fun n => n + 1, fun n => Nat.le_succ n⟩ : { f : Nat → Nat // ∀ n, n ≤ f n }` type-checks fine. Decidability only matters if you want `by decide` to *find* the proof for you; ask for it here and you get `failed to synthesize Decidable (…)`.

6. **Dependent pattern matching requires care.** When you pattern-match on a value that appears in a type, Lean must track how the type changes in each branch. This "motive" inference sometimes needs hints.

## Beginner mental model

Think of Lean's type system as a language where **types can ask questions about values, and you must answer those questions to compile**. In Python, `Literal[42]` says "this value is 42" and the checker believes you. In Lean, `{ n : Nat // n = 42 }` says "this value is 42, and here is a proof." The proof is checked by the compiler — there is no trust involved.

Singleton types in other languages are a limited version of what Lean does everywhere. Where TypeScript can say "this string is `GET`", Lean can say "this list has exactly 5 elements, all of which are prime, and they are sorted" — and enforce every part of that at compile time.

## Example A — Fin as a bounded natural (the practical singleton)

```lean
-- Fin n is { val : Nat, isLt : val < n }
-- It replaces Literal[0, 1, 2] for indexing into fixed-size structures

def safeIndex (xs : Vector α n) (i : Fin n) : α :=
  xs[i]

def colors : Vector String 3 := #v["red", "green", "blue"]

#eval safeIndex colors ⟨0, by omega⟩  -- "red"
#eval safeIndex colors ⟨2, by omega⟩  -- "blue"
-- safeIndex colors ⟨3, by omega⟩     -- fails: 3 < 3 is false

-- Fin n → Nat is a coercion core supplies and Lean inserts for you:
def double (n : Nat) : Nat := n * 2
def idx : Fin 100 := ⟨7, by omega⟩

#eval double idx     -- 14 — no `.val` written anywhere
#check (idx : Nat)   -- ↑idx : Nat

-- The reverse direction is the one that does not exist. Either carry the proof...
def mkFin (n : Nat) (h : n < 5) : Fin 5 := ⟨n, h⟩
-- ...or use a total operation that makes the value fit:
#eval Fin.ofNat 5 12  -- 2 : Fin 5 (reduces mod 5; needs [NeZero 5])
```

## Example B — Subtype as a singleton type

```lean
-- Exact equivalent of TypeScript's `type FortyTwo = 42`
def FortyTwo := { n : Nat // n = 42 }

def mk42 : FortyTwo := ⟨42, rfl⟩
-- def bad : FortyTwo := ⟨43, rfl⟩  -- error: 43 = 42 is false

-- Extract the value
#eval mk42.val  -- 42

-- The predicate need not be decidable: `Expanding` quantifies over all of Nat and
-- has no `Decidable` instance, yet the subtype is still perfectly constructible —
-- you just write the proof yourself instead of asking `by decide` for it.
def Expanding (f : Nat → Nat) : Prop := ∀ n, n ≤ f n

def succF : { f : Nat → Nat // Expanding f } :=
  ⟨fun n => n + 1, fun n => Nat.le_succ n⟩

#check succF.property   -- Expanding succF.val
```

## Example C — Dependent function: return type depends on input value

```lean
-- The return type varies with the argument — impossible with mere literal types
def describe (n : Nat) : if n == 0 then String else Nat :=
  match n with
  | 0 => "zero"
  | k + 1 => (k + 1) * 2

#eval describe 0    -- "zero" : String
#eval describe 5    -- 10 : Nat
```

## Common type-checker errors and how to read them

### `omega` cannot prove the goal

```
omega could not prove the goal:
No usable constraints found. You may need to unfold definitions so `omega` can see linear
arithmetic facts about `Nat` and `Int`, which may also involve multiplication, division,
and modular remainder by constants.
```

**Meaning:** From `def bad : Fin 5 := ⟨7, by omega⟩`. Note what `omega` does *not* say: it never reports "7 < 5 is false". It is a decision procedure for linear arithmetic over hypotheses, and with no hypotheses in context it simply reports that it found nothing to work with — the same message you get for a goal it merely cannot see through.
**Fix:** Use a value within the valid range, or widen the bound. To get a diagnosis that actually names the falsehood, use `by decide`, which refutes the goal outright: ``Tactic `decide` proved that the proposition 7 < 5 is false``.

### `Application type mismatch` on a subtype

```
Application type mismatch: The argument
  rfl
has type
  ?m.6 = ?m.6
but is expected to have type
  43 = 42
in the application
  ⟨43, ⋯⟩
```

**Meaning:** From `def bad : { n : Nat // n = 42 } := ⟨43, rfl⟩`. Lean does not infer a subtype `{ n // n = 43 }` for the anonymous constructor and then compare it against the expected one — it pushes the expected type inward, takes `43` as the value, and checks the second component against the resulting proposition `43 = 42`. `rfl` can only prove `?a = ?a`, so it fails there.
**Fix:** Use the correct value that matches the type's constraint.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Value-indexed types make invalid indices unrepresentable.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Encode domain invariants (bounds, sizes) directly in types.
- [-> UC-12](../usecases/UC12-compile-time.md) — Compile-time proof obligations replace runtime checks.
- [-> UC-24](../usecases/UC24-termination.md) — Decreasing Fin indices prove termination of recursive functions.

## Source anchors

- [Lean 4 — Dependent Types](https://lean-lang.org/doc/reference/latest/)
- [Lean 4 — Fin](https://leanprover-community.github.io/mathlib4_docs/Init/Prelude.html#Fin)
- [Lean 4 — Subtypes](https://lean-lang.org/doc/reference/latest/)
- [Theorem Proving in Lean 4 — Dependent Type Theory](https://lean-lang.org/theorem_proving_in_lean4/dependent_type_theory.html)
- [Functional Programming in Lean — Polymorphism](https://lean-lang.org/functional_programming_in_lean/)
