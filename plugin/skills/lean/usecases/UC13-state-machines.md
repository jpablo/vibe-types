# Protocol State Machines

## The constraint

Enforce valid state transitions at compile time. The type system encodes which states exist and which transitions are legal, so that code attempting an invalid transition does not type-check.

## Feature toolkit

- [→ T01-algebraic-data-types](../catalog/T01-algebraic-data-types.md) — Indexed inductive types encode states as type indices.
- [→ T09-dependent-types](../catalog/T09-dependent-types.md) — Dependent functions restrict arguments based on the current state.
- [→ T29-propositions-as-types](../catalog/T29-propositions-as-types.md) — Prop-valued preconditions guard transitions with proofs.

## Patterns

### Pattern A — Indexed inductive for protocol states

Encode the protocol as an inductive type indexed by "before" and "after" states. Each constructor represents one valid transition.

```lean
inductive ConnState where
  | disconnected
  | connected
  | authenticated

inductive Step : ConnState → ConnState → Type where
  | connect    : String → Step .disconnected .connected
  | auth       : String → Step .connected .authenticated
  | query      : String → Step .authenticated .authenticated
  | disconnect : Step .authenticated .disconnected

-- Cannot construct: Step.auth token : Step .disconnected .authenticated
-- The indices don't match — this is a type error.
```

### Pattern B — Dependent functions for valid transitions

Use the state index to restrict which operations are available. The return type depends on the current state.

```lean
structure Connection (s : ConnState) where
  host : String

def connect (host : String) : Connection .connected :=
  { host }

def authenticate (c : Connection .connected) (token : String)
    : Connection .authenticated :=
  { host := c.host }

def runQuery (c : Connection .authenticated) (sql : String) : String :=
  s!"result from {c.host}: {sql}"

def disconnect (c : Connection .authenticated) : Connection .disconnected :=
  { host := c.host }

-- Valid sequence:
def session : String :=
  let c := connect "db.example.com"
  let c := authenticate c "secret"
  let r := runQuery c "SELECT 1"
  let _ := disconnect c
  r

-- Invalid: skip authentication
-- def bad :=
--   let c := connect "db.example.com"
--   runQuery c "SELECT 1"  -- error: expected Connection .authenticated,
--                          --        got Connection .connected
```

### Pattern C — Protocol sequences as lists of steps

Chain protocol steps using a type-level guarantee that each step's output state matches the next step's input state.

```lean
inductive Protocol : ConnState → ConnState → Type where
  | done : Protocol s s
  | step : Step s mid → Protocol mid t → Protocol s t

def fullSession : Protocol .disconnected .disconnected :=
  .step (.connect "host")
    (.step (.auth "token")
      (.step (.query "SELECT 1")
        (.step .disconnect
          .done)))

-- Type error if steps don't chain:
-- .step (.auth "token") (.step (.connect "host") .done)
-- error: ConnState mismatch between auth's output and connect's input
```

### Pattern D — Propositions as transition guards

Use Prop-valued arguments to require proof that a transition is valid based on runtime data.

```lean
structure Door where
  isLocked : Bool

def unlock (d : Door) (h : d.isLocked = true) : Door :=
  { isLocked := false }

def open_ (d : Door) (h : d.isLocked = false) : String :=
  "door opened"

-- Must prove the door is locked before unlocking:
def example : String :=
  let d : Door := { isLocked := true }
  let d := unlock d rfl      -- rfl proves d.isLocked = true
  open_ d rfl                -- rfl proves d.isLocked = false
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Indexed inductive | Strongest guarantee; compiler tracks state indices | Verbose type signatures; complex for many states |
| Dependent functions | Lightweight; no protocol GADT needed | States must be tracked manually through the call chain |
| Protocol sequences | Composable; entire protocols type-checked as a unit | Overhead of building the sequence data structure |
| Prop guards | Flexible; works with runtime-computed states | Requires constructing proofs at each call site |

## When to use which feature

- **Fixed protocols** (connect/auth/query/disconnect) → indexed inductive types (Pattern A).
- **Simple state-dependent APIs** → dependent functions (Pattern B).
- **Composable protocol scripts** → protocol sequences (Pattern C).
- **Runtime-dependent state guards** → Prop preconditions (Pattern D).

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 7 "Inductive Types", Ch. 8 "Propositions and Proofs"
- *Functional Programming in Lean* — "Dependent Types"
