# Const Generics (Subsumed by Dependent Types)

> **Since:** Lean 4 (stable)

## What it is

Many languages have a separate "const generics" or "value-dependent generics" feature that allows types to be parameterized by compile-time constants (e.g., Rust's `[T; N]` where `const N: usize`). In Lean, **dependent types fully subsume const generics** — types can be parameterized by *any* value, not just compile-time integer constants.

A `Vector α n` is parameterized by a natural number `n`. A `Matrix α m n` is parameterized by two dimensions. A `Fin n` is a natural number provably less than `n`. These are not special features — they are ordinary applications of dependent types.

The key advantage: Lean's approach is strictly more powerful. You can parameterize types by any value of any type, not just integers. You can compute with these parameters at the type level. And the compiler verifies all constraints.

## What constraint it enforces

**Types parameterized by values carry those values in the type; the compiler checks that value parameters are consistent across operations.**

More specifically:

- **Value-indexed types.** `Vector α n` tracks its length `n` at the type level. Concatenating `Vector α m` and `Vector α n` produces `Vector α (m + n)`.
- **Static bounds checking.** `Fin n` ensures an index is less than `n`. Accessing `Vector α n` with a `Fin n` index is guaranteed safe.
- **Arithmetic in types.** The compiler evaluates arithmetic expressions (`m + n`, `n + 1`) during type checking to verify type equality.

## Minimal snippet

```lean
-- Vector parameterized by length (a "const generic" in other languages)
inductive Vec (α : Type) : Nat → Type where
  | nil  : Vec α 0
  | cons : α → Vec α n → Vec α (n + 1)

def Vec.append : Vec α m → Vec α n → Vec α (m + n)
  | .nil,       ys => ys
  | .cons x xs, ys => .cons x (xs.append ys)

-- The type tracks lengths:
-- append (cons 1 (cons 2 nil)) (cons 3 nil) : Vec Nat 3
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dependent Types** [→ catalog/T09](T09-dependent-types.md) | Const generics ARE dependent types. `Vec α n` is an inductive family indexed by `n : Nat`. |
| **Compile-Time Ops** [→ catalog/T16](T16-compile-time-ops.md) | The kernel evaluates arithmetic (`m + n`) during type checking. `decide` and `omega` verify numeric constraints. |
| **Erased Proofs** [→ catalog/T27](T27-erased-phantom.md) | Proof obligations (e.g., `i < n` for `Fin n`) are erased at runtime. Only the numeric value remains. |
| **Refinement Types** [→ catalog/T26](T26-refinement-types.md) | `Fin n` is a subtype `{ i : Nat // i < n }`. Subtypes are the mechanism for value-bounded types. |
| **Termination** [→ catalog/T28](T28-termination.md) | Recursive functions over indexed types (like `Vec.append`) must satisfy the termination checker via structural recursion. |

## Gotchas and limitations

1. **Arithmetic unification.** The kernel's definitional equality can handle simple arithmetic (`n + 0 = n`), but complex expressions may not unify automatically. You may need `simp [Nat.add_comm]` or `omega` to help the type checker.

2. **Not just `Nat`.** Unlike Rust's const generics (limited to integer types), Lean allows indexing by any type. You can have `Matrix α (Fin m) (Fin n)` or types indexed by strings, lists, or even other types.

3. **Runtime representation.** Unlike Rust where `[T; N]` has a compile-time-known fixed size, Lean's `Vec α n` is a linked list at runtime. Performance-sensitive code should use `Array` with proof-carrying indices.

4. **Type-level computation can be slow.** When `n` is large, the kernel may take a long time to verify arithmetic equalities. Use `native_decide` or `omega` for complex numeric reasoning.

## Beginner mental model

Think of const generics as **putting numbers (or any values) into type labels**. A box labeled "contains 5 items" (`Vec α 5`) is different from a box labeled "contains 3 items" (`Vec α 3`). You cannot concatenate them and claim the result has 7 items — the compiler does the arithmetic and checks. In Lean, this is not a special feature; it is just how types work.

Coming from Rust: `Vec α n` ≈ `[T; N]` (array with compile-time known length). But Lean goes further: you can parameterize by *any* value, not just `usize` constants. And you can compute with these parameters (`append` produces `Vec α (m + n)`).

## Example A — Safe matrix dimensions

```lean
structure Matrix (α : Type) (m n : Nat) where
  data : Array (Array α)
  -- invariant: m rows, n columns each

def Matrix.mul [Add α] [Mul α] [OfNat α 0]
    (a : Matrix α m n) (b : Matrix α n p) : Matrix α m p :=
  sorry -- implementation omitted; the KEY point is the type:
  -- columns of `a` must equal rows of `b`, enforced by sharing `n`
```

## Example B — Fin as a const-generic index

```lean
def safeGet (xs : Array α) (i : Fin xs.size) : α :=
  xs[i]   -- no bounds check needed; the type guarantees i < xs.size

-- At the call site, the bound is verified:
#eval safeGet #[10, 20, 30] ⟨1, by omega⟩   -- 20
-- safeGet #[10, 20, 30] ⟨5, by omega⟩
-- error: omega fails to prove 5 < 3
```

## Use-case cross-references

- [→ UC-01](../usecases/UC01-invalid-states.md) — Value-indexed types make out-of-bounds access unrepresentable.
- [→ UC-02](../usecases/UC02-domain-modeling.md) — Dimension-parameterized types model physical quantities and matrix algebra.
- [→ UC-12](../usecases/UC12-compile-time.md) — Value constraints are verified entirely at compile time.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 7 "Inductive Types" (indexed families)
- *Functional Programming in Lean* — "Dependent Types"
- Lean 4 core: `Init.Prelude` (definition of `Fin`)
