# Error Handling

## The constraint

Handle errors in a type-safe way so the compiler tracks which operations can fail and how. Choose between `Except` for typed error channels, `Option` for simple absence, and `MonadExcept` for polymorphic error propagation in `do` blocks.

## Feature toolkit

- [→ T05-type-classes](../catalog/T05-type-classes.md) — `MonadExcept` and `MonadExceptOf` define error handling as a type-class interface.
- [→ T01-algebraic-data-types](../catalog/T01-algebraic-data-types.md) — Inductive error types with exhaustive matching on error variants.
- [→ T31-record-types](../catalog/T31-record-types.md) — Structures carry error context alongside failure reasons.

## Patterns

### Pattern A — Except for typed error channels

`Except` is the standard pure error monad: `Except ε α` is either `.ok a` or `.error e`.

```lean
inductive AppError where
  | notFound (key : String)
  | unauthorized (user : String)
  | rateLimited (retryMs : Nat)

def lookupUser (id : String) : Except AppError String :=
  if id == "42" then .ok "Alice"
  else .error (.notFound id)

def requireAdmin (user : String) : Except AppError Unit :=
  if user == "Alice" then .ok ()
  else .error (.unauthorized user)

-- Compose with do notation — errors short-circuit:
def adminLookup (id : String) : Except AppError String := do
  let user ← lookupUser id
  requireAdmin user
  return s!"admin:{user}"
```

### Pattern B — Option vs Except

Use `Option` when the only failure mode is "absent." Use `Except` when the caller needs to know *why* something failed.

```lean
-- Option: simple absence
def findFirst (xs : List Nat) (p : Nat → Bool) : Option Nat :=
  xs.find? p

-- Except: informative failure
def parsePort (s : String) : Except String Nat := do
  let n ← s.toNat?.toExcept s!"not a number: {s}"
  if n > 0 && n < 65536 then return n
  else throw s!"port out of range: {n}"

-- Convert between them:
def optionToExcept (msg : String) : Option α → Except String α
  | some a => .ok a
  | none   => .error msg
```

### Pattern C — MonadExcept for polymorphic error handling

`MonadExcept` abstracts over the error-handling monad, letting functions work with `IO`, `Except`, `EStateM`, or any monad that supports `throw`/`tryCatch`.

```lean
def fetchOrDefault [MonadExcept String m] [Monad m]
    (fetch : String → m Nat) (key : String) (default : Nat) : m Nat := do
  try
    fetch key
  catch
    | _ => return default

-- Works with IO:
def ioFetch (key : String) : IO Nat :=
  if key == "a" then return 42
  else throw (IO.userError s!"missing: {key}")

-- Works with Except:
def pureFetch (key : String) : Except String Nat :=
  if key == "a" then .ok 42
  else .error s!"missing: {key}"
```

### Pattern D — try/catch in do blocks

`do` blocks support `try`/`catch` for monads with `MonadExcept`. The catch branch handles specific error patterns.

```lean
def processFile (path : String) : IO String := do
  try
    let contents ← IO.FS.readFile path
    return s!"read {contents.length} bytes"
  catch
    | e => return s!"failed: {e}"

-- Multiple operations with early exit on error:
def pipeline (input : String) : IO String := do
  let validated ← validate input   -- throws on bad input
  let fetched ← fetch validated    -- throws on network error
  let result ← transform fetched   -- throws on parse error
  return result
-- Each step's error propagates automatically via MonadExcept
```

### Pattern E — Custom error hierarchies

Combine inductive error types with `Except` for domain-specific error handling with exhaustive matching.

```lean
inductive DbError where
  | connectionFailed (host : String)
  | queryFailed (sql : String) (reason : String)
  | timeout (ms : Nat)

def handleDbError (e : DbError) : String :=
  match e with
  | .connectionFailed h  => s!"cannot connect to {h}"
  | .queryFailed sql r   => s!"query failed: {sql} ({r})"
  | .timeout ms          => s!"timed out after {ms}ms"
  -- removing any branch → "missing cases" error
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| `Except` | Pure; typed error channel; composable | Must thread through all callers |
| `Option` | Simplest; no error details | No information on why it failed |
| `MonadExcept` | Polymorphic; works across monads | Extra type-class constraints in signatures |
| `try`/`catch` in `do` | Familiar syntax; concise | Only in monads supporting `MonadExcept` |

## When to use which feature

- **Simple absence** (lookup, find) → `Option`.
- **Typed error channels in pure code** → `Except ε α` with an inductive error type.
- **IO operations** → `IO` with `try`/`catch` (IO has `MonadExcept` for `IO.Error`).
- **Polymorphic libraries** → abstract over `MonadExcept` so callers choose the monad.
- **Exhaustive error handling** → inductive error type + pattern match.

## Source anchors

- *Functional Programming in Lean* — "Error Handling", "do Notation"
- Lean 4 source: `Init.Control.Except`, `Init.Control.ExceptCps`
