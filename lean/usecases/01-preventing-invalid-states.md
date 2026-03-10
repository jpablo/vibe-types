# Preventing Invalid States

## The constraint

Represent only valid domain states in types so that invalid combinations cannot be constructed. The compiler rejects code that attempts to create values violating the state constraints.

## Feature toolkit

- [→ catalog/01](../catalog/01-inductive-types.md) — Inductive types with closed constructors model valid state spaces.
- [→ catalog/02](../catalog/02-dependent-types.md) — Dependent types index data by invariants the compiler tracks.
- [→ catalog/06](../catalog/06-propositions-as-types.md) — Prop-based preconditions require proof to construct values.
- [→ catalog/14](../catalog/14-subtypes-refinements.md) — Subtypes attach predicates to values; construction requires proof.

## Patterns

### Pattern A — Inductive types for closed state spaces

```lean
inductive ConnectionState where
  | disconnected
  | connecting (host : String)
  | connected (host : String) (socket : IO.FS.Handle)

-- Cannot represent "connected without a socket" — the type forbids it
def send (s : ConnectionState) (msg : String) : IO Unit :=
  match s with
  | .connected _ sock => sock.putStr msg
  | _ => throw (IO.userError "not connected")
```

### Pattern B — Subtypes for constrained values

```lean
def Port := { n : Nat // n > 0 ∧ n < 65536 }

def mkPort (n : Nat) (h : n > 0 ∧ n < 65536) : Port := ⟨n, h⟩

def http : Port := ⟨80, by omega⟩       -- OK
-- def bad : Port := ⟨0, by omega⟩      -- error: omega can't prove 0 > 0
```

### Pattern C — Dependent types for indexed invariants

```lean
inductive Vec (α : Type) : Nat → Type where
  | nil  : Vec α 0
  | cons : α → Vec α n → Vec α (n + 1)

def zipWith (f : α → β → γ) : Vec α n → Vec β n → Vec γ n
  | .nil,       .nil       => .nil
  | .cons a as, .cons b bs => .cons (f a b) (zipWith f as bs)
-- Cannot zip vectors of different lengths — the types prevent it
```

### Pattern D — Propositions as preconditions

```lean
def safeDiv (a b : Nat) (h : b ≠ 0) : Nat := a / b

-- Callers must provide proof:
#eval safeDiv 10 3 (by decide)  -- OK
-- safeDiv 10 0 ???              -- cannot construct proof that 0 ≠ 0
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Inductive types | Easy to read; exhaustive matching forced | Cannot express numeric/arithmetic constraints |
| Subtypes | Flexible predicates; zero runtime cost | Proof obligations at every construction site |
| Dependent types (indexed) | Strongest invariants; compiler tracks indices | Steep learning curve; verbose type errors |
| Prop preconditions | Lightweight; one proof per call | Only guards function entry, not data shape |

## When to use which feature

- **Finite, named states** (auth states, connection lifecycle) → inductive types.
- **Numeric constraints** (positive, bounded, non-zero) → subtypes with `omega`.
- **Structural invariants** (length-indexed data, balanced trees) → dependent types (indexed families).
- **Function preconditions** (non-zero divisor, valid index) → Prop arguments.

## Source anchors

- *Functional Programming in Lean* — "Datatypes and Pattern Matching", "Subtypes"
- *Theorem Proving in Lean 4* — Ch. 7 "Inductive Types"
