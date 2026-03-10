# Safe Effectful Programming

## The constraint

Track side effects via IO and monads; prevent untracked mutation. Pure functions cannot perform IO or modify state — the type signature declares exactly which effects a function uses.

## Feature toolkit

- [→ catalog/09](../catalog/09-monads-do-io.md) — `IO`, `StateM`, `ExceptT`, and `do`-notation track and compose effects.

## Patterns

### Pattern A — IO containment

```lean
-- Pure function: no effects
def square (n : Nat) : Nat := n * n

-- Effectful function: IO in the type
def askAndSquare : IO Nat := do
  IO.println "Enter a number:"
  let line ← (← IO.getStdin).getLine
  match line.trim.toNat? with
  | some n => return square n
  | none   => throw (IO.userError "not a number")

-- Cannot call askAndSquare from pure code:
-- def bad : Nat := askAndSquare  -- error: type mismatch IO Nat vs Nat
```

### Pattern B — State tracking via StateT

```lean
abbrev Logged := StateT (List String) IO

def logMsg (msg : String) : Logged Unit :=
  modify (· ++ [msg])

def process : Logged Nat := do
  logMsg "starting"
  let result := 42
  logMsg s!"result: {result}"
  return result

def main : IO Unit := do
  let (result, logs) ← process.run []
  for log in logs do
    IO.println log
```

### Pattern C — Error handling via ExceptT

```lean
inductive AppError where
  | notFound (key : String)
  | invalid (msg : String)

abbrev App := ExceptT AppError IO

def lookupConfig (key : String) : App String := do
  -- ...
  throw (.notFound key)

def main : IO Unit := do
  match ← lookupConfig "db_url" |>.run with
  | .ok url    => IO.println s!"URL: {url}"
  | .error err => IO.eprintln s!"Error: {repr err}"
```

### Pattern D — Monad transformer stack

```lean
abbrev AppM := ReaderT Config (StateT AppState (ExceptT AppError IO))

-- The type declares: this function reads config, modifies state,
-- may fail with AppError, and performs IO.
-- Pure code cannot call AppM functions.
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Plain IO | Simple; sufficient for scripts | No distinction between "reads" and "writes" |
| StateT | Explicit state threading; testable | Transformer stacking adds complexity |
| ExceptT | Typed error handling; no exceptions | Must handle errors at every boundary |
| Full stack | Maximum precision in effect tracking | Verbose types; `MonadLift` ceremony |

## When to use which feature

- **Simple scripts and CLI tools** → plain `IO`.
- **Stateful computations** (accumulators, counters) → `StateT`.
- **Operations that can fail** → `ExceptT` with a domain error type.
- **Large applications with multiple effects** → monad transformer stack with `abbrev`.

## Source anchors

- *Functional Programming in Lean* — "Monads" and "Monad Transformers"
- Lean 4 source: `Init.Control.Basic`, `Init.System.IO`
