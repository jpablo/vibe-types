# Domain Modeling with Dependent Types

## The constraint

Model domain invariants as type-level constraints that the compiler enforces. Domain rules (e.g., "a matrix has consistent dimensions," "a currency amount is non-negative") become part of the type, not runtime assertions.

## Feature toolkit

- [→ T09-dependent-types](../catalog/T09-dependent-types.md) — Dependent types let types depend on values.
- [→ T01-algebraic-data-types](../catalog/T01-algebraic-data-types.md) — Indexed inductive families model structured data with invariants.
- [→ T31-record-types](../catalog/T31-record-types.md) — Structures with proof fields bundle data and invariants.
- [→ T26-refinement-types](../catalog/T26-refinement-types.md) — Subtypes attach predicates to existing types.
- [→ T18-conversions-coercions](../catalog/T18-conversions-coercions.md) — Coercions provide smooth conversions between domain types.

## Patterns

### Pattern A — Structures with proof fields

```lean
structure Money where
  amount : Int
  currency : String
  nonneg : amount ≥ 0   -- domain invariant as proof field

def usd (n : Nat) : Money :=
  { amount := n, currency := "USD", nonneg := Int.ofNat_nonneg n }
```

### Pattern B — Indexed families for dimensional constraints

```lean
inductive Matrix (α : Type) : Nat → Nat → Type where
  | mk : (data : Array (Array α)) →
         (hrows : data.size = m) →
         (hcols : ∀ row ∈ data.toList, row.size = n) →
         Matrix α m n

-- Multiplication requires inner dimensions to match:
-- Matrix α m n → Matrix α n p → Matrix α m p
-- The compiler rejects m×n * p×q when n ≠ p
```

### Pattern C — Subtypes for domain-constrained primitives

```lean
def Percentage := { n : Float // 0.0 ≤ n ∧ n ≤ 100.0 }
def Email := { s : String // s.containsSubstr "@" }  -- simplified

-- Construction requires proof:
-- ⟨150.0, by ...⟩ : Percentage  -- proof fails: 150 > 100
```

### Pattern D — Coercions for smooth domain usage

```lean
structure UserId where val : Nat
structure OrderId where val : Nat

-- No coercion between UserId and OrderId — they are distinct types
-- def lookupOrder (uid : UserId) : ... -- error if passed OrderId

-- But coerce to Nat when needed:
instance : Coe UserId Nat where coe u := u.val
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Proof fields | Invariant is part of the data; always carried | Must prove invariant at every construction site |
| Indexed families | Strongest guarantees; compiler tracks dimensions | Complex type signatures; heavy proof burden |
| Subtypes | Lightweight; zero runtime cost | Predicate must be provable at each use |
| Distinct structures | Simple; prevents mixing (UserId vs OrderId) | No compile-time domain logic — just nominal separation |

## When to use which feature

- **Domain entities with rules** (money, dates, coordinates) → structures with proof fields.
- **Dimensional/structural constraints** (matrices, vectors, graphs) → indexed inductive families.
- **Constrained primitives** (percentages, bounded numbers) → subtypes.
- **Nominal separation** (user IDs vs order IDs) → distinct structures without coercions.

## Source anchors

- *Functional Programming in Lean* — "Structures", "Dependent Types"
- *Theorem Proving in Lean 4* — Ch. 7 "Inductive Types"
