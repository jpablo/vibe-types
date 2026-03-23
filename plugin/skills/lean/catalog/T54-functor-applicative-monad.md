# Functor, Applicative, and Monad

> **Since:** Lean 4 (stable)

## What it is

Lean provides `Functor`, `Applicative`, and `Monad` as built-in type classes in the standard library. **Functor** declares `map : (α → β) → f α → f β` for transforming values inside a context. **Applicative** extends `Functor` with `pure : α → f α` and `seq : f (α → β) → (Unit → f α) → f β` for lifting values and applying functions within a context. **Monad** extends `Applicative` with `bind : f α → (α → f β) → f β` for sequencing dependent computations.

Lean's `do`-notation desugars directly to `bind` (monadic bind), making imperative-looking code work over any Monad instance. The standard library provides instances for `Option`, `Except`, `IO`, `StateM`, `ReaderM`, and `List`. Mathlib extends these with lawful versions (`LawfulFunctor`, `LawfulMonad`) that carry proof obligations for the functor and monad laws.

## What constraint it enforces

**A function constrained by `[Monad m]` can only use `pure`, `bind`, `map`, and `seq` — it cannot access implementation details of the concrete monad, and the compiler rejects calls where no instance exists. Lawful variants additionally guarantee that identity, composition, and associativity laws hold.**

## Minimal snippet

```lean
def addOpt [Monad m] (mx : m Nat) (my : m Nat) : m Nat := do
  let x ← mx
  let y ← my
  pure (x + y)

#eval addOpt (some 3) (some 4)           -- some 7
#eval addOpt (some 3) (none : Option Nat) -- none
#eval addOpt [1, 2] [10, 20]             -- [11, 21, 12, 22]
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type classes** [-> T05](T05-type-classes.md) | `Functor`, `Applicative`, `Monad` are type classes. `[Monad m]` is an instance-implicit argument resolved automatically. |
| **Do-notation** | `do` blocks desugar to `bind`. `let x ← mx` becomes `bind mx (fun x => ...)`. `return` is `pure`. |
| **Monad transformers** [-> T55](T55-monad-transformers.md) | `StateT`, `ReaderT`, `ExceptT` compose monadic effects. `MonadLift` lifts operations between layers. |
| **Dependent types** [-> T09](T09-dependent-types.md) | Monadic computations can carry dependent types — `do` blocks can produce terms whose types depend on intermediate results. |
| **Tactics and metaprogramming** | Lean's tactic framework (`TacticM`) is itself a monad. `MetaM`, `TermElabM`, and `CommandElabM` form a monad transformer stack. |
| **Lawful type classes** | `LawfulFunctor`, `LawfulMonad` require proofs of the functor/monad laws. Mathlib uses these to reason about monadic code in proofs. |

## Gotchas and limitations

1. **`Applicative` uses thunked `seq`.** Lean's `Applicative.seq` takes `f (α → β) → (Unit → f α) → f β` — the second argument is thunked to enable short-circuiting. This differs from Haskell's `<*> : f (α → β) → f α → f β`.

2. **`do`-notation is Monad, not Applicative.** Unlike Haskell's `ApplicativeDo`, Lean's `do` always desugars to `bind`. Independent computations in a `do` block are still sequenced, not parallelized.

3. **No automatic Applicative accumulation.** `do`-notation short-circuits on the first failure. For error accumulation, you need explicit Applicative combinators or a `Validated`-style type (not in stdlib).

4. **Universe polymorphism.** `Monad` is universe-polymorphic. When defining your own monadic type, you may need to annotate universe levels explicitly to avoid unification errors.

5. **Instance search depth.** Complex monad transformer stacks can hit the instance resolution depth limit. Use `set_option synthInstance.maxHeartbeats` to increase it, or provide instances explicitly.

## Beginner mental model

Think of `m α` as a **recipe that produces an `α`**. `Functor.map` changes what the recipe produces without changing how it runs. `Applicative.pure` creates a trivial recipe that just returns a value. `Monad.bind` chains recipes: "run this recipe, then use its result to pick the next recipe." `do`-notation is syntactic sugar that makes recipe-chaining read like step-by-step instructions.

Coming from Scala: `do` = for-comprehension, `bind` = `flatMap`, `pure` = wrapping in the context (e.g., `Some`, `Right`). Coming from Rust: `bind` is like `and_then`, and `do`-notation is like the `?` operator but generalized to any monad.

## Example A -- Custom monad instance

```lean
inductive Validated (ε α : Type) where
  | ok  : α → Validated ε α
  | err : ε → Validated ε α

instance : Monad (Validated ε) where
  pure := Validated.ok
  bind
    | .ok a,  f => f a
    | .err e, _ => .err e

def safeDivide (x y : Int) : Validated String Int :=
  if y == 0 then .err "division by zero"
  else .ok (x / y)

#eval do                                  -- do-notation works
  let a ← safeDivide 10 2
  let b ← safeDivide a 0                  -- short-circuits here
  pure (a + b)                            -- Validated.err "division by zero"
```

## Example B -- Generic monadic pipeline

```lean
def pipeline [Monad m] (step1 : α → m β) (step2 : β → m γ) (x : α) : m γ := do
  let b ← step1 x
  step2 b

def parseNat (s : String) : Option Nat := s.toNat?
def halve (n : Nat) : Option Nat := if n % 2 == 0 then some (n / 2) else none

#eval pipeline parseNat halve "42"   -- some 21
#eval pipeline parseNat halve "7"    -- none (odd)
#eval pipeline parseNat halve "abc"  -- none (parse failure)
```

## Do-notation

Lean's `do`-notation desugars `let x ← mx` into `bind mx (fun x => ...)`. It makes monadic code read like imperative statements while preserving the pure functional semantics underneath.

```lean
-- This do block:
def example : IO Unit := do
  let name ← IO.getLine
  let greeting := s!"Hello, {name.trim}!"
  IO.println greeting

-- Desugars to:
def example' : IO Unit :=
  IO.getLine >>= fun name =>
    let greeting := s!"Hello, {name.trim}!"
    IO.println greeting
```

**Key desugaring rules:**
- `let x ← mx` → `bind mx (fun x => ...)` (monadic bind)
- `let x := e` → plain let-binding (no monadic effect)
- `return e` → `pure e`
- `if` / `match` inside `do` → standard control flow, each branch returns `m α`
- Statements without `let` → `bind stmt (fun () => ...)` (sequencing for side effects)

`do`-notation works with **any type that has a `Monad` instance** — `IO`, `Option`, `Except`, `StateM`, custom monads. The same syntax adapts to different computational contexts:

```lean
-- Option monad: short-circuits on none
def safeDivide (a b : Nat) : Option Nat := do
  guard (b ≠ 0)    -- fails with none if b = 0
  pure (a / b)

-- Except monad: short-circuits on error
def parseAge (s : String) : Except String Nat := do
  let n ← s.toNat?.toExcept s!"not a number: {s}"
  if n > 150 then throw s!"unrealistic age: {n}"
  pure n
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Monadic chaining in `Option`/`Except` prevents operating on absent or invalid values.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- `[Monad m]` constraints express that a function works for any monadic context.
- [-> UC-11](../usecases/UC11-effect-tracking.md) -- Monad constraints track which effects a computation requires at the type level.

## Source anchors

- *Functional Programming in Lean* -- "Monads" chapter
- Lean 4 source: `Init.Prelude` (Functor, Applicative, Monad definitions)
- Lean 4 source: `Init.Control.Basic` (MonadLift, MonadControl)
- *Theorem Proving in Lean 4* -- Ch. 10 "Type Classes"
