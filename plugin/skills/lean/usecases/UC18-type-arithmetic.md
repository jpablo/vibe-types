# Type Arithmetic

## The constraint

Encode numeric and dimensional constraints directly in types so the compiler checks arithmetic invariants at compile time. Lean 4's dependent types let you index data by natural numbers, bound values with `Fin n`, and prove arithmetic relationships as part of type checking.

## Feature toolkit

- [-> T09-dependent-types](../catalog/T09-dependent-types.md) -- Types indexed by values; the core mechanism for type-level arithmetic.
- [-> T26-refinement-types](../catalog/T26-refinement-types.md) -- Subtypes with arithmetic predicates verified by `omega`.
- [-> T29-propositions-as-types](../catalog/T29-propositions-as-types.md) -- Arithmetic propositions as types; proofs as values.
- [-> T15-const-generics](../catalog/T15-const-generics.md) -- `Fin n` and natural number indices as "const generics."

## Patterns

### Pattern A -- Vec indexed by length

A length-indexed vector makes it impossible to zip vectors of different sizes or access out-of-bounds indices.

```lean
inductive Vec (α : Type) : Nat → Type where
  | nil  : Vec α 0
  | cons : α → Vec α n → Vec α (n + 1)

def zipWith (f : α → β → γ) : Vec α n → Vec β n → Vec γ n
  | .nil,       .nil       => .nil
  | .cons a as, .cons b bs => .cons (f a b) (zipWith f as bs)
-- Cannot zip Vec α 2 with Vec β 3 — the types prevent it

def head : Vec α (n + 1) → α
  | .cons a _ => a
-- Cannot call head on Vec α 0 — the type (n + 1) excludes it
```

### Pattern B -- Fin n for bounded indices

`Fin n` is a natural number guaranteed to be less than `n`. Use it for safe indexing.

```lean
-- Fin n = { val : Nat, isLt : val < n }
def safeIndex (xs : Array α) (i : Fin xs.size) : α :=
  xs[i]

-- Construction:
def firstThree : List (Fin 5) :=
  [⟨0, by omega⟩, ⟨1, by omega⟩, ⟨2, by omega⟩]

-- Arithmetic on Fin:
def next (i : Fin n) (h : i.val + 1 < n) : Fin n :=
  ⟨i.val + 1, h⟩

-- Out-of-bounds is a type error:
-- def bad : Fin 3 := ⟨5, by omega⟩   -- error: omega can't prove 5 < 3
```

### Pattern C -- Arithmetic constraints via subtypes

Use subtypes with arithmetic predicates, proved automatically by `omega`.

```lean
def Positive := { n : Nat // n > 0 }

def safeDiv (a : Nat) (b : Positive) : Nat :=
  a / b.val

#eval safeDiv 10 ⟨3, by omega⟩     -- 3
-- safeDiv 10 ⟨0, by omega⟩        -- error: omega can't prove 0 > 0

def BoundedPort := { n : Nat // n > 0 ∧ n < 65536 }

def mkPort (n : Nat) (h : n > 0 ∧ n < 65536) : BoundedPort := ⟨n, h⟩

#eval (mkPort 80 (by omega)).val    -- 80
```

### Pattern D -- Matrix dimensions in types

Track matrix dimensions to prevent incompatible operations.

```lean
structure Matrix (m n : Nat) where
  data : Array (Array Float)
  -- In production, add proofs: data.size = m, ∀ row, row.size = n

def multiply (a : Matrix m k) (b : Matrix k n) : Matrix m n :=
  sorry  -- implementation omitted; the key point is the types

-- The shared dimension k must match:
-- multiply (Matrix 2 3) (Matrix 4 5) — type error: k=3 ≠ k=4

def transpose (a : Matrix m n) : Matrix n m :=
  sorry  -- dimensions are swapped in the return type
```

### Pattern E -- Compile-time arithmetic proofs

Prove arithmetic relationships to satisfy type constraints.

```lean
-- Append preserves length:
theorem Vec.append_length :
    (as : Vec α m) → (bs : Vec α n) → Vec α (m + n)
  | .nil,       bs => bs
  | .cons a as, bs => .cons a (Vec.append_length as bs)

-- The compiler needs to know m + n = n + m for some operations:
theorem addComm (m n : Nat) : m + n = n + m := Nat.add_comm m n

-- omega handles linear arithmetic automatically:
example (a b : Nat) (h : a < b) : a + 1 ≤ b := by omega
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Length-indexed types (`Vec`) | Strongest guarantees; impossible to misuse | Verbose; harder to build incrementally |
| `Fin n` | Safe indexing; composable | Proof obligations at every construction site |
| Subtypes with `omega` | Automated proofs for linear arithmetic | `omega` limited to linear constraints; non-linear needs manual proof |
| Dimensional types (`Matrix m n`) | Catches dimension mismatches at compile time | Carrying dimensions in types adds annotation overhead |

## When to use which feature

- **Safe indexing** -> `Fin n` for array/vector access; eliminates bounds checks.
- **Numeric invariants** (positive, bounded, non-zero) -> subtypes with `omega`.
- **Length-preserving operations** (zip, split, chunk) -> length-indexed types like `Vec α n`.
- **Dimensional analysis** (matrices, physical units) -> phantom or index parameters tracking dimensions.
- **Complex arithmetic** -> write explicit `theorem` lemmas; use `omega` for the linear parts and `simp` for the rest.

## Source anchors

- *Theorem Proving in Lean 4* -- Ch. 7 "Inductive Types", Ch. 8 "Tactics"
- Lean 4 source: `Init.Data.Fin`, `Init.Data.Array`, `Mathlib.Data.Matrix`
