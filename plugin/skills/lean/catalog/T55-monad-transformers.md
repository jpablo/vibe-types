# Monad Transformers

> **Since:** Lean 4 (stable); `StateT`, `ReaderT`, `ExceptT` in Init.Control

## What it is

Monad transformers in Lean compose monadic effects by wrapping one monad inside another. The standard library provides **`StateT σ m α`** (stateful computation over monad `m`), **`ReaderT ρ m α`** (read-only environment), **`ExceptT ε m α`** (error handling), and **`WriterT ω m α`** (logging/accumulation). Each transformer takes an existing monad `m` and produces a new monad that combines `m`'s effects with an additional capability.

**`MonadLift`** enables lifting operations from an inner monad to an outer transformer layer. Lean's tactic and metaprogramming stack is itself a monad transformer tower: `TacticM` builds on `TermElabM`, which builds on `MetaM`, which builds on `CoreM`, each adding capabilities (tactic state, elaboration context, metavariables, environment).

## What constraint it enforces

**Monad transformers enforce that composed effects are accessed through a well-typed interface. Operations from an inner monad must be explicitly lifted to the transformer level, and the type signature reveals the full effect stack.**

## Minimal snippet

```lean
def computation : StateT Nat (Except String) Nat := do
  let current ← get
  if current == 0 then
    throw "counter is zero"     -- ExceptT effect
  modify (· + 10)               -- StateT effect
  get

#eval computation.run 5    -- Except.ok (15, 15)
#eval computation.run 0    -- Except.error "counter is zero"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Functor/Applicative/Monad** [-> T54](T54-functor-applicative-monad.md) | Transformers require `[Monad m]` on the base monad and produce a new `Monad` instance for the composed type. |
| **Type classes** [-> T05](T05-type-classes.md) | `MonadState`, `MonadReader`, `MonadExcept` are type classes that abstract over transformer stacks, enabling MTL-style programming. |
| **Do-notation** | `do` blocks work seamlessly with transformer stacks. `let x ← action` desugars to `bind` on the transformer's monad instance. |
| **MonadLift** | `MonadLift m n` provides `monadLift : m α → n α` for lifting operations from inner monad `m` to outer monad `n`. Lean synthesizes lift chains automatically. |
| **Tactics and metaprogramming** | Lean's internal monad stack (`CoreM → MetaM → TermElabM → TacticM`) is built with transformers. Understanding transformers helps when writing custom tactics. |

## Gotchas and limitations

1. **Lift chains can be long.** In a deep stack like `StateT S (ReaderT R (ExceptT E IO))`, lifting an `IO` action requires traversing three layers. `MonadLift` automates this, but instance search can be slow for deep stacks.

2. **Order of transformers matters.** `ExceptT E (StateT S m)` rolls back state on error; `StateT S (ExceptT E m)` preserves state through errors. Choose the order based on desired semantics.

3. **Performance.** Each transformer layer adds closure allocations. For performance-critical code, consider using `IO.Ref` for state or `EStateM` (Lean's efficient combined state+exception monad) instead of stacking transformers.

4. **`MonadState` vs `StateT`.** `MonadState` is the MTL-style type class; `StateT` is the concrete transformer. Prefer constraining functions with `[MonadState σ m]` over requiring `StateT σ m` directly, to keep code polymorphic.

5. **`ExceptT` vs `Except`.** `Except ε α` is `ExceptT ε Id α` — the non-transformer version. Mixing them up causes confusing type errors.

## Beginner mental model

Think of monad transformers as **layers of capabilities**. The base monad `IO` gives you side effects. Wrapping it in `StateT Nat IO` adds a mutable counter. Wrapping further in `ExceptT String (StateT Nat IO)` adds error handling on top. Each `do` block can use any capability from any layer. `MonadLift` is the elevator that carries operations from a lower floor to a higher one.

Coming from Scala: `StateT`/`ReaderT`/`ExceptT` are the same as cats' `StateT`/`Kleisli`/`EitherT`. `MonadLift` is similar to cats' `MonadIO` or `LiftIO`.

## Example A -- ReaderT for dependency injection

```lean
structure Config where
  maxRetries : Nat
  baseUrl : String

def fetchWithRetries : ReaderT Config IO String := do
  let cfg ← read
  IO.println s!"Fetching from {cfg.baseUrl} with {cfg.maxRetries} retries"
  pure "response data"

def processResponse : ReaderT Config IO Unit := do
  let data ← fetchWithRetries
  IO.println s!"Processing: {data}"

#eval processResponse.run { maxRetries := 3, baseUrl := "https://api.example.com" }
```

## Example B -- Combined ExceptT + StateT

```lean
abbrev App := ExceptT String (StateT (List String) IO)

def log (msg : String) : App Unit :=
  modify (· ++ [msg])

def failIf (cond : Bool) (msg : String) : App Unit :=
  if cond then throw msg else pure ()

def program : App Unit := do
  log "starting"
  failIf false "should not fail"
  log "step 2"
  failIf true "intentional failure"
  log "unreachable"

#eval do
  let (result, logs) ← program.run |>.run []
  IO.println s!"Result: {repr result}"
  IO.println s!"Logs: {logs}"
  -- Result: Except.error "intentional failure"
  -- Logs: ["starting", "step 2"]
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- `ExceptT` ensures error handling is threaded through the computation, preventing operations on invalid state.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- MTL-style constraints (`[MonadState σ m]`) express required effects as type-class bounds.
- [-> UC-11](../usecases/UC11-effect-tracking.md) -- The transformer stack in the type signature reveals all effects a computation may perform.

## Source anchors

- Lean 4 source: `Init.Control.StateRef` (StateT)
- Lean 4 source: `Init.Control.Reader` (ReaderT)
- Lean 4 source: `Init.Control.Except` (ExceptT)
- *Functional Programming in Lean* -- "Monad Transformers" chapter
- *Metaprogramming in Lean 4* -- monad stack for tactics
