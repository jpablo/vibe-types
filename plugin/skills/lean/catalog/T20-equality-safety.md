# Equality Safety — BEq, DecidableEq, and Propositional Equality

> **Since:** Lean 4 (stable)

## What it is

Lean distinguishes between **propositional equality** (`=`, a `Prop`) and **boolean equality** (`==`, via `BEq`). Propositional equality `a = b` is a type that is inhabited when `a` and `b` are definitionally or provably equal. Boolean equality `a == b` is a function returning `Bool`, defined by a `BEq` instance. Neither is available for free — types must explicitly opt in.

- **`BEq α`** — Provides `(· == ·) : α → α → Bool`. Derived with `deriving BEq`.
- **`DecidableEq α`** — Provides a decision procedure that returns either a proof of `a = b` or a proof of `a ≠ b`. Stronger than `BEq`: it connects boolean comparison with propositional truth.
- **`deriving DecidableEq`** — Generates both the decision procedure and a `BEq` instance.

There is no universal `==` that silently compares arbitrary types. Comparing two unrelated types is a type error.

## What constraint it enforces

**Equality comparison is opt-in via type classes; the compiler rejects comparisons for types without instances. Propositional and boolean equality are distinct.**

More specifically:

- **No default equality.** Unlike Java's `Object.equals`, there is no built-in equality for all types. Using `==` without a `BEq` instance is a compile error.
- **No cross-type comparison.** `BEq` takes a single type parameter: `(· == ·) : α → α → Bool`. You cannot compare a `Nat` with a `String`.
- **Proof-level equality.** `DecidableEq` connects `==` with `=`, meaning boolean results can be lifted into proofs.

## Minimal snippet

```lean
structure UserId where id : Nat
  deriving BEq

#eval (⟨1⟩ : UserId) == ⟨2⟩     -- false (OK: BEq instance exists)

structure RoleId where id : Nat   -- no deriving BEq

-- #eval (⟨1⟩ : RoleId) == ⟨2⟩  -- error: failed to synthesize BEq RoleId
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | `BEq` and `DecidableEq` are type classes. Instances are resolved automatically. |
| **Derivation** [→ catalog/T06](T06-derivation.md) | `deriving BEq` and `deriving DecidableEq` auto-generate instances for inductive types. |
| **Propositions as Types** [→ catalog/T29](T29-propositions-as-types.md) | Propositional equality `a = b` is a type in `Prop`. Proofs of equality enable rewriting in goals. |
| **Compile-Time Ops** [→ catalog/T16](T16-compile-time-ops.md) | `decide` can prove `a = b` or `a ≠ b` at compile time when `DecidableEq` is available. |
| **Hashable** | `Hashable` is a separate type class. Having `BEq` without `Hashable` is allowed; `HashMap` requires both. |

## Gotchas and limitations

1. **`BEq` does not imply `DecidableEq`.** A `BEq` instance is just a boolean function — it may not agree with propositional equality. `DecidableEq` is the stronger, proof-producing version.

2. **Heterogeneous equality.** Lean has `HEq` (heterogeneous equality) for comparing values of different types. It is primarily used in dependent type theory proofs and is rarely needed in application code.

3. **Custom `BEq` can be wrong.** Nothing stops you from writing a `BEq` instance where `x == x` returns `false`. Use `deriving BEq` or `DecidableEq` to avoid this.

4. **Floating-point equality.** `Float` has a `BEq` instance, but `Float.nan == Float.nan` is `false` (IEEE 754 semantics). This cannot satisfy `DecidableEq` because NaN ≠ NaN breaks reflexivity.

## Beginner mental model

Think of `==` as a **permission slip**. You can only compare two values if the type has a `BEq` permission slip. No slip, no comparison — the compiler refuses. `DecidableEq` is a *stronger* slip that also says "the boolean answer matches a mathematical proof of equality."

Coming from Rust: `BEq` ≈ `PartialEq`, `DecidableEq` ≈ `Eq` (but with proof-level guarantees). `deriving BEq` ≈ `#[derive(PartialEq)]`.

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
