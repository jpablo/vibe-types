# Equality

## The constraint

Distinguish between propositional equality (a proof that two terms are identical) and decidable/boolean equality (a computable check). Lean 4 provides `DecidableEq` for compile-time-verified decidable equality, `BEq` for boolean equality, and propositional `=` for theorem proving. Choose the right level for each use case.

## Feature toolkit

- [-> T20-equality-safety](../catalog/T20-equality-safety.md) -- `BEq`, `DecidableEq`, and propositional equality (`=`).
- [-> T06-derivation](../catalog/T06-derivation.md) -- `deriving BEq, DecidableEq` for automatic instance generation.
- [-> T29-propositions-as-types](../catalog/T29-propositions-as-types.md) -- Propositional equality `a = b` as a type; `rfl` as the proof.
- [-> T05-type-classes](../catalog/T05-type-classes.md) -- `BEq` and `DecidableEq` are type classes.

## Patterns

### Pattern A -- BEq for boolean equality

`BEq` provides a `==` operator that returns `Bool`. Derive it for structures and inductive types.

```lean
structure Point where
  x : Int
  y : Int
  deriving BEq

#eval Point.mk 1 2 == Point.mk 1 2   -- true
#eval Point.mk 1 2 == Point.mk 3 4   -- false

-- BEq gives you == and !=, but no proof-level information
```

### Pattern B -- DecidableEq for proof-producing equality

`DecidableEq` decides equality and produces a proof. Use it when downstream code needs to branch on equality with proof evidence.

```lean
inductive Color where
  | red | green | blue
  deriving DecidableEq, BEq

def colorName (c : Color) : String :=
  if c == .red then "red"
  else if c == .green then "green"
  else "blue"

-- DecidableEq lets you use `if h : a = b then ... else ...`:
def sameColor (a b : Color) : String :=
  if h : a = b then s!"same: {a}"
  else s!"different"
```

### Pattern C -- Propositional equality for proofs

Propositional equality `a = b` is a type. The constructor `rfl` proves `a = a`. Use it in theorems and dependent pattern matching.

```lean
-- rfl proves reflexive equality:
example : 2 + 3 = 5 := rfl

-- Substitution: if a = b, use a wherever b appears:
theorem addComm_zero (n : Nat) : n + 0 = n := Nat.add_zero n

-- Equality in hypotheses:
theorem injective_succ (a b : Nat) (h : a + 1 = b + 1) : a = b :=
  Nat.succ.inj h
```

### Pattern D -- Deriving equality for composite types

Use `deriving` to generate `BEq` and `DecidableEq` for structures and inductive types.

```lean
structure Config where
  host : String
  port : Nat
  ssl  : Bool
  deriving BEq, DecidableEq

inductive Result where
  | ok (value : String)
  | err (code : Nat) (msg : String)
  deriving BEq, DecidableEq

#eval Config.mk "a" 80 true == Config.mk "a" 80 true   -- true
#eval Result.ok "x" == Result.err 404 "not found"       -- false
```

### Pattern E -- Custom BEq for domain-specific equality

Override `BEq` when structural equality is not the right notion (e.g., case-insensitive comparison).

```lean
structure CaseInsensitive where
  value : String

instance : BEq CaseInsensitive where
  beq a b := a.value.toLower == b.value.toLower

#eval CaseInsensitive.mk "Hello" == CaseInsensitive.mk "hello"   -- true
#eval CaseInsensitive.mk "Hello" == CaseInsensitive.mk "world"   -- false
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| `BEq` | Simple; familiar `==` syntax; easy to derive | No proof; cannot use result in theorems |
| `DecidableEq` | Proof-producing; works in `if h : a = b` | Slightly heavier; not all types are decidable |
| Propositional `=` | Full proof power; compiler-verified | Not computable at runtime; purely for reasoning |
| Custom `BEq` | Domain-appropriate semantics | Must manually ensure consistency with `Hashable` etc. |

## When to use which feature

- **Runtime equality checks** (filtering, lookup, deduplication) -> `BEq` with `deriving`.
- **Branching with proof evidence** (dependent `if`, index refinement) -> `DecidableEq`.
- **Theorem proving** (mathematical properties, invariant proofs) -> propositional `=` with `rfl`, `simp`, `omega`.
- **Domain-specific equivalence** (case-insensitive strings, approximate floats) -> custom `BEq` instance.

## Source anchors

- *Theorem Proving in Lean 4* -- Ch. 4 "Propositions and Proofs", Ch. 7 "Inductive Types"
- Lean 4 source: `Init.Prelude` (`BEq`, `DecidableEq`), `Init.Core` (`Eq`)
