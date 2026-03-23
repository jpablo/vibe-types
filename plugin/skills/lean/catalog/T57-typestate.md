# Typestate

> **Since:** Lean 4 (stable); indexed inductive types since Lean 4.0

## What it is

Typestate in Lean is encoded using **indexed inductive types** — types whose constructors produce values at specific indices, making the state part of the type itself. A `Connection : ConnState -> Type` is a family of types indexed by state, where each constructor produces a value at a specific state index. Methods constrained to a particular index are only callable on values in that state.

Unlike Scala or Rust where phantom type parameters tag an otherwise uniform struct, Lean's dependent type system lets the state index **directly govern what data the type carries and what operations are available**. This is strictly more powerful: constructors can carry different fields in different states, and the type checker proves that transitions are valid by construction.

Lean's approach is closer to indexed monads or graded monads in theory — the state is not just a tag but a first-class part of the type's definition.

## What constraint it enforces

**Functions that accept `Connection .connected` can only be called with values whose type index is `.connected`. Constructors that produce `Connection .disconnected` cannot be passed where `.connected` is expected. The type checker ensures that the sequence of state transitions is valid by construction.**

## Minimal snippet

```lean
inductive ConnState where
  | disconnected
  | connected
  | authenticated

inductive Connection : ConnState → Type where
  | create : String → Connection .disconnected
  | connect : Connection .disconnected → Connection .connected
  | auth : Connection .connected → String → Connection .authenticated

def query (conn : Connection .authenticated) (sql : String) : String :=
  s!"Executing: {sql}"

def example : String :=
  let c := Connection.create "db.example.com"
  let c := Connection.connect c
  let c := Connection.auth c "secret"
  query c "SELECT 1"
  -- query (Connection.create "x") "SELECT 1"  -- type error!
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dependent types** [-> T09](T09-dependent-types.md) | Indexed inductive types are dependent types. The state index is a term-level value that appears in the type, enabling the compiler to reason about state transitions. |
| **Type classes** [-> T05](T05-type-classes.md) | Type-class instances can be defined for specific state indices: `instance : ToString (Connection .connected)`. Different states can have different capabilities. |
| **Pattern matching** [-> T01](T01-algebraic-data-types.md) | Matching on a `Connection s` refines the state index `s`, enabling the type checker to know which constructors are possible in each branch. |
| **Propositions and proofs** | State invariants can be encoded as propositions. A function can require proof that a state satisfies a predicate, e.g., `(h : s ≠ .disconnected)`. |
| **Inductive families** | Typestate types are a special case of inductive families. More complex state machines can use multiple indices (e.g., `Protocol : ClientState → ServerState → Type`). |

## Gotchas and limitations

1. **Indexed types are not phantom types.** Unlike Rust's `PhantomData` approach where the struct layout is identical across states, Lean's indexed inductive types can have genuinely different constructors (and data) per state. This is more expressive but means different states may have different representations.

2. **No linear types.** Lean does not enforce that a value is used exactly once. After calling `Connection.connect c`, the old `c : Connection .disconnected` is still in scope and could be reused. Discipline or careful API design (e.g., making the old value unavailable via shadowing) is needed.

3. **State transitions require new constructors.** Each transition is a constructor or function that produces a value at the new state index. You cannot "mutate" the state — you must construct a new value. This is natural in a pure language but can feel verbose.

4. **Complex state spaces.** For state machines with many states and transitions, the inductive type definition can become large. Consider breaking the machine into smaller indexed types or using a type-class-based approach for more modularity.

5. **Proof obligations.** When functions require specific states, callers must provide values at exactly the right index. In complex programs, this can require explicit type annotations or intermediate `let` bindings to help the elaborator.

## Beginner mental model

Think of an indexed inductive type as a **coloring system** for values. `Connection .disconnected` is a red value, `Connection .connected` is a yellow value, `Connection .authenticated` is a green value. The `query` function has a sign saying "green values only." The `connect` function takes a red value and hands back a yellow one. The `auth` function takes a yellow value and hands back a green one. You must follow the color sequence — the compiler checks your colors at every step.

Coming from Rust: Lean's indexed inductives are strictly more powerful than `PhantomData` typestate because different states can carry different data, not just different type tags. The tradeoff is that Lean has no ownership to prevent reuse of old-state values.

## Example A -- File handle with state tracking

```lean
inductive FileState where
  | closed
  | openRead
  | openWrite

inductive FileHandle : FileState → Type where
  | create : String → FileHandle .closed
  | openForRead : FileHandle .closed → FileHandle .openRead
  | openForWrite : FileHandle .closed → FileHandle .openWrite
  | closeRead : FileHandle .openRead → FileHandle .closed
  | closeWrite : FileHandle .openWrite → FileHandle .closed

def readLine (h : FileHandle .openRead) : String :=
  "line contents"   -- simplified

def writeLine (h : FileHandle .openWrite) (line : String) : FileHandle .openWrite :=
  h  -- simplified; in practice would produce a new handle

def example2 : String :=
  let f := FileHandle.create "data.txt"
  let f := FileHandle.openForRead f
  let content := readLine f
  let _ := FileHandle.closeRead f
  content
```

## Example B -- Protocol with proof of valid transition

```lean
inductive Phase where
  | init | ready | running | done

def Phase.canStart : Phase → Prop
  | .ready => True
  | _ => False

inductive Process : Phase → Type where
  | create : Process .init
  | prepare : Process .init → Process .ready
  | start : (p : Process .ready) → Process .running
  | finish : Process .running → Process .done

def getResult (p : Process .done) : String :=
  "computation result"

-- Valid sequence:
def workflow : String :=
  let p := Process.create
  let p := Process.prepare p
  let p := Process.start p
  let p := Process.finish p
  getResult p

-- Invalid: Process.start Process.create  -- type error: expected Process .ready, got Process .init
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Indexed types make invalid state transitions a type error by construction.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- State indices act as type-level constraints that restrict which operations are available.
- [-> UC-11](../usecases/UC11-effect-tracking.md) -- State-indexed types track resource lifecycle (open/closed, connected/disconnected) at the type level.

## Source anchors

- *Theorem Proving in Lean 4* -- Ch. 7 "Inductive Types" (indexed families)
- *Functional Programming in Lean* -- "Indexed Families"
- Lean 4 source: `Init.Prelude` (indexed inductive definitions)
