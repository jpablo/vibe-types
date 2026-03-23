# Immutability

## The constraint

Everything in Lean 4 is immutable by default. There is no mutable variable binding, no in-place field update, and no mutable collection. Controlled mutation is available only through `IO.Ref` and `StateM` inside monadic contexts, making mutability an explicit, trackable effect.

## Feature toolkit

- [-> T32-immutability-markers](../catalog/T32-immutability-markers.md) -- All `let` bindings and structure fields are immutable; no `var` keyword exists.
- [-> T31-record-types](../catalog/T31-record-types.md) -- Structures support functional update syntax (`{ s with field := newVal }`).
- [-> T01-algebraic-data-types](../catalog/T01-algebraic-data-types.md) -- Inductive types are immutable by construction.
- [-> T12-effect-tracking](../catalog/T12-effect-tracking.md) -- `IO.Ref` and `ST.Ref` confine mutation inside monadic effects.

## Patterns

### Pattern A -- Immutable bindings everywhere

All `let` and `def` bindings are immutable. There is no reassignment.

```lean
def example : Nat :=
  let x := 10
  -- x := 20       -- error: cannot reassign a let binding
  x + 1

-- Function parameters are also immutable:
def double (n : Nat) : Nat :=
  -- n := n * 2    -- error: cannot assign to a parameter
  n * 2
```

### Pattern B -- Functional updates on structures

Use `{ s with field := newVal }` to produce a new structure with one or more fields changed. The original is untouched.

```lean
structure Config where
  host : String
  port : Nat
  ssl  : Bool

def devConfig : Config :=
  { host := "localhost", port := 8080, ssl := false }

def prodConfig : Config :=
  { devConfig with host := "prod.example.com", ssl := true }

-- devConfig.host is still "localhost"
#eval devConfig.host    -- "localhost"
#eval prodConfig.host   -- "prod.example.com"
```

### Pattern C -- Immutable collections

Lists, arrays, and other data structures are immutable. "Modification" always produces a new value.

```lean
def example : List Nat :=
  let xs := [1, 2, 3]
  let ys := 0 :: xs       -- new list; xs is unchanged
  let zs := xs ++ [4, 5]  -- new list
  zs

#eval example   -- [1, 2, 3, 4, 5]
```

### Pattern D -- IO.Ref for controlled mutation

When mutation is genuinely needed (counters, caches), use `IO.Ref`. The mutation is confined to the `IO` monad.

```lean
def counter : IO Unit := do
  let ref ← IO.mkRef (0 : Nat)
  ref.modify (· + 1)
  ref.modify (· + 1)
  let val ← ref.get
  IO.println s!"count = {val}"   -- "count = 2"

-- Outside IO, there is no way to create or use a Ref:
-- def pureCounter : Nat := ...  -- no Ref available in pure code
```

### Pattern E -- StateM for pure stateful computation

`StateM` threads mutable-looking state through a pure computation without actual mutation.

```lean
def sumList (xs : List Nat) : Nat :=
  let go : StateM Nat Unit := do
    for x in xs do
      modify (· + x)
  (go 0).snd

#eval sumList [1, 2, 3, 4]   -- 10
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Immutable bindings | Zero surprise; equational reasoning | Cannot express in-place accumulation directly |
| Functional updates | Readable; preserves originals | Deep nesting requires manual threading or lenses |
| Immutable collections | Safe sharing; no aliasing bugs | Naive code may copy unnecessarily (compiler optimises with RC) |
| `IO.Ref` | Familiar mutable semantics when needed | Confined to `IO`; cannot use in pure proofs |
| `StateM` | Pure; testable; no `IO` required | Monadic style adds syntactic overhead |

## When to use which feature

- **Default**: just use immutable `let` bindings and functional updates. This covers the vast majority of Lean code.
- **Pure stateful algorithms** (accumulators, running totals) -> `StateM` or tail-recursive helpers with an accumulator parameter.
- **Genuine mutation** (caches, counters in long-running processes) -> `IO.Ref`, keeping the mutable surface minimal.
- **Performance-critical code** -> Lean's reference-counting runtime can update unique references in place, so idiomatic immutable code is often already efficient.

## Source anchors

- *Functional Programming in Lean* -- "Structures", "Monads" (IO, StateM)
- Lean 4 source: `Init.Data.Array`, `Init.System.IO`
