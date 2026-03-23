# Preventing Invalid States

## The constraint

Represent only valid domain states in types so that invalid combinations cannot be constructed. The compiler rejects code that attempts to create values violating the state constraints.

## Feature toolkit

- [→ T01-algebraic-data-types](../catalog/T01-algebraic-data-types.md) — Inductive types with closed constructors model valid state spaces.
- [→ T09-dependent-types](../catalog/T09-dependent-types.md) — Dependent types index data by invariants the compiler tracks.
- [→ T29-propositions-as-types](../catalog/T29-propositions-as-types.md) — Prop-based preconditions require proof to construct values.
- [→ T26-refinement-types](../catalog/T26-refinement-types.md) — Subtypes attach predicates to values; construction requires proof.

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

### Pattern E — Parse, don't validate

Instead of checking a condition and discarding the proof, return a refined type that carries the guarantee. In Lean, this is the natural style — subtypes and propositions ARE parsing.

```lean
-- Validation: checks and throws — caller gains no type-level info
def validateNonEmpty (xs : List α) : IO Unit :=
  if xs.isEmpty then throw (IO.userError "empty list") else pure ()

-- Parsing: checks and returns a refined type (the subtype carries the proof)
def NonEmptyList (α : Type) := { xs : List α // xs ≠ [] }

def parseNonEmpty (xs : List α) : Option (NonEmptyList α) :=
  match xs with
  | [] => none
  | _  => some ⟨xs, by simp [List.isEmpty]⟩

-- The head function is total — no partial function needed
def head (nel : NonEmptyList α) : α :=
  match nel.val, nel.property with
  | a :: _, _ => a

-- Downstream code never needs to re-validate
def processFirst (nel : NonEmptyList String) : IO Unit :=
  IO.println s!"Processing: {head nel}"  -- always safe
```

**Key insight:** Lean makes the "parse, don't validate" principle most explicit — a subtype `{ x : T // P x }` literally pairs a value with its proof. Validation (`IO Unit`) discards the evidence; parsing (`Option (Subtype P)`) preserves it. Lean's proof system means the parsed result carries a machine-checked guarantee, not just a type-level hint.

See: [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)

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
