# Safe Recursion and Termination

## The constraint

All recursion terminates. Every recursive function must either satisfy structural recursion automatically or provide a well-founded termination proof.

## Feature toolkit

- [→ T28-termination](../catalog/T28-termination.md) — Termination checker verifies structural or well-founded recursion.
- [→ T51-totality](../catalog/T51-totality.md) — `partial` opts out of termination checking for intentionally non-terminating code.
- [→ T30-proof-automation](../catalog/T30-proof-automation.md) — `omega` and `simp` discharge termination measure proofs.

## Patterns

### Pattern A — Structural recursion (automatic)

```lean
def sum : List Nat → Nat
  | []      => 0
  | x :: xs => x + sum xs  -- OK: xs is structurally smaller

def depth : Tree α → Nat
  | .leaf _     => 0
  | .node l _ r => 1 + max (depth l) (depth r)  -- OK: l, r are sub-terms
```

### Pattern B — Well-founded recursion with omega

```lean
def binarySearch (xs : Array Nat) (target lo hi : Nat) : Option Nat :=
  if h : lo < hi then
    let mid := (lo + hi) / 2
    if xs[mid]! = target then some mid
    else if xs[mid]! < target then binarySearch xs target (mid + 1) hi
    else binarySearch xs target lo mid
  else none
termination_by hi - lo
decreasing_by all_goals omega
```

### Pattern C — Fuel-based recursion (workaround)

```lean
def eval (fuel : Nat) (expr : Expr) : Option Value :=
  match fuel with
  | 0     => none  -- ran out of fuel
  | n + 1 =>
    match expr with
    | .lit v     => some v
    | .app f arg => do
        let fv ← eval n f
        let av ← eval n arg
        apply fv av
-- Structural recursion on fuel — always terminates
-- Tradeoff: semantics change (may return none even for valid expressions)
```

### Pattern D — partial for genuinely infinite processes

```lean
partial def repl : IO Unit := do
  let line ← (← IO.getStdin).getLine
  if line.trim = "quit" then return
  IO.println s!"You said: {line.trim}"
  repl
-- Cannot prove termination (depends on user input)
-- partial is the correct choice here
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Structural recursion | Automatic; zero proof effort | Only works with visibly shrinking arguments |
| Well-founded + omega | Handles complex patterns | Requires writing termination_by and decreasing_by |
| Fuel-based | Always structurally recursive | Changes semantics; arbitrary fuel limit |
| `partial` | No proof needed | Cannot be used in proofs; taints the definition |

## When to use which feature

- **Simple list/tree recursion** → let structural recursion handle it (default).
- **Divide-and-conquer, search algorithms** → `termination_by` with a numeric measure + `omega`.
- **Interpreters, evaluators with unknown depth** → fuel parameter or `partial`.
- **Servers, REPLs, event loops** → `partial` (non-termination is the point).

## Source anchors

- *Functional Programming in Lean* — "Proving Termination"
- *Theorem Proving in Lean 4* — Ch. 8 "Recursion"
