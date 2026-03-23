# Totality and Exhaustiveness

## The constraint

Every function handles all possible inputs — no unmatched cases and no infinite loops. The compiler ensures that pattern matches cover all constructors and that recursive functions terminate.

## Feature toolkit

- [→ T01-algebraic-data-types](../catalog/T01-algebraic-data-types.md) — Inductive types define the set of constructors; the compiler enforces exhaustive matching.
- [→ T28-termination](../catalog/T28-termination.md) — The termination checker rejects functions that might not return.
- [→ T51-totality](../catalog/T51-totality.md) — `partial` explicitly opts out of termination with known consequences.

## Patterns

### Pattern A — Exhaustive pattern matching

```lean
inductive Shape where
  | circle (radius : Float)
  | rect (width : Float) (height : Float)
  | triangle (a : Float) (b : Float) (c : Float)

def area : Shape → Float
  | .circle r     => Float.pi * r * r
  | .rect w h     => w * h
  | .triangle a b c =>
    let s := (a + b + c) / 2.0
    Float.sqrt (s * (s - a) * (s - b) * (s - c))
-- OK: all three constructors handled
-- Removing any branch → "missing cases" error
```

### Pattern B — Structural recursion for automatic termination

```lean
def flatten : List (List α) → List α
  | []        => []
  | xs :: xss => xs ++ flatten xss
-- OK: structural recursion on the outer list
```

### Pattern C — Well-founded recursion with proof

```lean
def mergeSort [Ord α] (xs : List α) : List α :=
  if h : xs.length ≤ 1 then xs
  else
    let mid := xs.length / 2
    let left := mergeSort (xs.take mid)
    let right := mergeSort (xs.drop mid)
    merge left right
termination_by xs.length
decreasing_by all_goals simp [List.length_take, List.length_drop]; omega
```

### Pattern D — Opting out with partial

```lean
partial def gameLoop (state : GameState) : IO GameState := do
  let input ← readInput
  let newState := update state input
  if newState.isGameOver then return newState
  gameLoop newState
-- partial: intentionally non-terminating (game runs until quit)
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Exhaustive matching | Zero effort if all cases listed; compiler catches missing branches | Adding a constructor breaks all existing matches |
| Structural recursion | Automatic; no proofs needed | Only works when argument visibly shrinks |
| Well-founded recursion | Handles complex recursion patterns | Requires termination proof (can be tedious) |
| `partial` | No proof burden | Cannot use in proofs; taints the result |

## When to use which feature

- **Enumerations and ADTs** → exhaustive matching (always).
- **Simple recursive data** (lists, trees, Nat) → structural recursion (compiler handles it).
- **Complex recursion** (divide-and-conquer, worklist algorithms) → `termination_by` + `omega`/`simp`.
- **Genuinely infinite processes** (servers, REPLs, games) → `partial`.

## Source anchors

- *Functional Programming in Lean* — "Pattern Matching", "Proving Termination"
- *Theorem Proving in Lean 4* — Ch. 8 "Recursion"
