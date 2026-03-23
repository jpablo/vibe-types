# Generic Programming with Type Classes

## The constraint

Constrain generic code to types with required capabilities. The compiler rejects calls where the type lacks the necessary type class instance.

## Feature toolkit

- [→ T05-type-classes](../catalog/T05-type-classes.md) — Type classes define interfaces; instance resolution enforces them.
- [→ T35-universes-kinds](../catalog/T35-universes-kinds.md) — Universe polymorphism enables generic definitions across all type levels.
- [→ T18-conversions-coercions](../catalog/T18-conversions-coercions.md) — Coercions enable smooth type conversions in generic contexts.
- [→ T38-implicits-auto-bound](../catalog/T38-implicits-auto-bound.md) — Instance arguments declare required capabilities concisely.

## Patterns

### Pattern A — Basic type class constraint

```lean
def deduplicate [BEq α] [Hashable α] (xs : List α) : List α :=
  let seen := xs.foldl (fun s x => s.insert x) (Std.HashSet.empty)
  seen.toList

-- Works for types with BEq and Hashable:
#eval deduplicate [1, 2, 2, 3, 1]  -- OK: Nat has both instances

-- Fails for types without:
-- deduplicate [fun x => x]  -- error: no Hashable instance for (Nat → Nat)
```

### Pattern B — Custom type class for domain operations

```lean
class Serializable (α : Type) where
  serialize : α → ByteArray
  deserialize : ByteArray → Except String α

instance : Serializable Nat where
  serialize n := sorry  -- implementation
  deserialize bs := sorry

def roundtrip [Serializable α] (x : α) : Except String α :=
  Serializable.deserialize (Serializable.serialize x)
```

### Pattern C — Class hierarchy with extends

```lean
class Container (c : Type → Type) where
  empty : c α
  insert : c α → α → c α
  contains : [BEq α] → c α → α → Bool

class OrderedContainer (c : Type → Type) extends Container c where
  toSorted : [Ord α] → c α → List α

-- Functions requiring OrderedContainer automatically get Container methods:
def sortAndCount [OrderedContainer c] [Ord α] [BEq α] (xs : c α) : Nat :=
  (OrderedContainer.toSorted xs).length
```

### Pattern D — Universe-polymorphic generics

```lean
universe u

def identity {α : Sort u} (x : α) : α := x

-- Works for values, types, and propositions:
#check identity 42           -- Nat
#check identity Nat          -- Type
#check identity (1 = 1)      -- Prop
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Single constraint | Simple and clear | Limited to one capability |
| Multiple constraints | Precise requirements | Verbose signatures |
| Class hierarchy | Reuse and composition | Can slow instance resolution |
| Universe polymorphism | Maximum generality | Rarely needed in application code |

## When to use which feature

- **Standard operations** (equality, ordering, hashing) → use built-in classes (`BEq`, `Ord`, `Hashable`).
- **Domain-specific capabilities** → define custom type classes.
- **Algebraic structures** (semigroup, monoid, ring) → class hierarchy with `extends`.
- **Library-level generics** → universe polymorphism for maximum reusability.

## Source anchors

- *Functional Programming in Lean* — "Type Classes"
- *Theorem Proving in Lean 4* — Ch. 10 "Type Classes"
