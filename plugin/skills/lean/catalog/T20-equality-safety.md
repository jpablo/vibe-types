# Equality Safety — BEq, DecidableEq, and Propositional Equality

> **Since:** Lean 4 (stable)

## What it is

Lean distinguishes between **propositional equality** (`=`, a `Prop`) and **boolean equality** (`==`, via `BEq`). Propositional equality `a = b` is a type that is inhabited when `a` and `b` are definitionally or provably equal. Boolean equality `a == b` is a function returning `Bool`, defined by a `BEq` instance. The two are not opt-in to the same degree: `a = b` is well-formed for **any** type with no instance whatsoever, and `rfl` proves `a = a`. What requires an instance is *computing* equality — `==` (a `BEq` instance) and *deciding* `=` (a `DecidableEq` instance).

- **`BEq α`** — Provides `(· == ·) : α → α → Bool`. Derived with `deriving BEq`.
- **`DecidableEq α`** — Provides a decision procedure that returns either a proof of `a = b` or a proof of `a ≠ b`. Stronger than `BEq`: it connects boolean comparison with propositional truth.
- **`deriving DecidableEq`** — Generates the decision procedure only. `==` then works anyway, because core ships the generic `instBEqOfDecidableEq : [DecidableEq α] → BEq α` (`#synth BEq α` on such a type reports `instBEqOfDecidableEq`).

There is no universal `==` that silently compares arbitrary types. Comparing two unrelated types is a type error.

## What constraint it enforces

**Computable equality is opt-in via type classes; the compiler rejects `==` for types without instances. Propositional and boolean equality are distinct.**

More specifically:

- **No default *boolean* equality.** Unlike Java's `Object.equals`, there is no built-in `==` for all types. Using `==` without a `BEq` instance is a compile error. (Writing `a = b` is always allowed — it is a proposition, not a computation.)
- **No cross-type comparison.** `BEq` takes a single type parameter: `(· == ·) : α → α → Bool`. You cannot compare a `Nat` with a `String`.
- **Proof-level equality.** `DecidableEq` connects `==` with `=`, meaning boolean results can be lifted into proofs.

## Minimal snippet

```lean
structure UserId where id : Nat
  deriving BEq

#eval (⟨1⟩ : UserId) == ⟨2⟩     -- false (OK: BEq instance exists)

structure RoleId where id : Nat   -- no deriving BEq

-- Propositional equality needs no instance at all:
#check (⟨1⟩ : RoleId) = ⟨2⟩       -- ... = ... : Prop
example : (⟨1⟩ : RoleId) = ⟨1⟩ := rfl

-- Only the *boolean* comparison is opt-in:
example : Bool := (⟨1⟩ : RoleId) == ⟨2⟩  -- error: failed to synthesize BEq RoleId
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | `BEq` and `DecidableEq` are type classes. Instances are resolved automatically. |
| **Derivation** [→ catalog/T06](T06-derivation.md) | `deriving BEq` and `deriving DecidableEq` auto-generate instances for inductive types. |
| **Propositions as Types** [→ catalog/T29](T29-propositions-as-types.md) | Propositional equality `a = b` is a type in `Prop`. Proofs of equality enable rewriting in goals. |
| **Compile-Time Ops** [→ catalog/T16](T16-compile-time-ops.md) | `decide` can prove `a = b` or `a ≠ b` at compile time when `DecidableEq` is available. |
| **Hashable** | `Hashable` is a separate type class. Having `BEq` without `Hashable` is allowed; `HashMap` requires both. |
| **LawfulBEq** | `LawfulBEq α` is the proof-side companion to `BEq α`: it asserts `(a == a) = true` and `(a == b) = true → a = b`. `instBEqOfDecidableEq` is lawful; a hand-written `BEq` is not, until proved. |

## Gotchas and limitations

1. **`BEq` does not imply `DecidableEq`.** A `BEq` instance is just a boolean function — it may not agree with propositional equality. `DecidableEq` is the stronger, proof-producing version.

2. **Heterogeneous equality.** Lean has `HEq` (heterogeneous equality) for comparing values of different types. It is primarily used in dependent type theory proofs and is rarely needed in application code.

3. **Custom `BEq` can be wrong.** Nothing stops you from writing a `BEq` instance where `x == x` returns `false`. The class that rules this out is **`LawfulBEq α`** — it bundles `ReflBEq`'s `(a == a) = true` with `eq_of_beq : (a == b) = true → a = b`. `deriving BEq` on a plain inductive type gives you an instance you can prove lawful; a hand-written `BEq` gives you nothing until you supply `LawfulBEq`. Functions that need `==` to track `=` should ask for `[BEq α] [LawfulBEq α]`.

4. **Floating-point equality.** `Float` has a `BEq` instance, but with NaN — build one as `0.0 / 0.0`, since core 4.31 has no `Float.nan` — `nan == nan` is `false` (IEEE 754 semantics). Note what this does *not* break: `nan = nan` is still provable by `rfl`, because propositional equality is reflexive for every term. What IEEE semantics rules out is **`LawfulBEq Float`**: `(a == a) = true` fails, and `#synth LawfulBEq Float` reports "failed to synthesize". `DecidableEq Float` is missing for an unrelated reason — `Float` wraps an opaque extern type, so there is no decision procedure to run.

## Beginner mental model

Think of `==` as a **permission slip**. You can only *compute* a comparison if the type has a `BEq` permission slip. No slip, no `==` — the compiler refuses. Writing `a = b` needs no slip at all; it is a claim, not a computation. `DecidableEq` is the slip that turns that claim back into something runnable, and `LawfulBEq` is the slip that certifies "the boolean answer matches the claim."

Coming from Rust: `BEq` ≈ `PartialEq` (it supplies the comparison). Rust's `Eq` is a *lawfulness marker* with no methods of its own, so its Lean counterpart is **`LawfulBEq`**, not `DecidableEq`. `DecidableEq` is orthogonal to both — it is about `=` being *decidable*, which Rust's trait system has no analogue for. `deriving BEq` ≈ `#[derive(PartialEq)]`.

## Example A — DecidableEq for proof-carrying comparison

```lean
structure Point where
  x : Int
  y : Int
  deriving DecidableEq

def samePoint (a b : Point) : String :=
  if a = b then "same"      -- uses DecidableEq, result is Prop-level
  else "different"

#eval samePoint ⟨1, 2⟩ ⟨1, 2⟩    -- "same"
```

## Example B — Preventing cross-type comparison

```lean
structure Celsius where val : Float deriving BEq
structure Fahrenheit where val : Float deriving BEq

-- Comparing unrelated types is rejected: `==` needs both sides to share a type.
def compareTemps (c : Celsius) (f : Fahrenheit) := c == f -- error: type mismatch, expected Celsius, got Fahrenheit
```

## Use-case cross-references

- [→ UC-01](../usecases/UC01-invalid-states.md) — Opt-in equality prevents accidentally comparing unrelated domain types.
- [→ UC-02](../usecases/UC02-domain-modeling.md) — Domain types choose their own equality semantics.

## Source anchors

- *Functional Programming in Lean* — "Overloading and Type Classes"
- Lean 4 core: `Init.Prelude` (definition of `BEq`, `DecidableEq`)
- *Theorem Proving in Lean 4* — Ch. 4 "Propositions and Proofs" (propositional equality)
