# Monads, Do-Notation, and the IO Type

> **Since:** Lean 4 (stable)

## What it is

Lean is a pure functional language — functions have no side effects by default. Side effects (reading files, printing, networking, mutable state) are tracked by the type system through *monadic types*. The `IO` type marks computations that interact with the outside world. `StateM σ` tracks mutable state of type `σ`. `ExceptT ε m` tracks the possibility of errors.

Monads are formalized via the `Monad` type class [→ T05](T05-type-classes.md), which provides `pure` (wrap a value) and `bind` (sequence computations). Lean's `do`-notation provides imperative-looking syntax that desugars to monadic `bind` calls, making effectful code readable without losing type-level effect tracking.

## What constraint it enforces

**Side effects are tracked in the type; pure functions cannot perform IO or other effects. The type signature declares exactly which effects a function may use.**

More specifically:

- **IO containment.** A function returning `IO α` can perform side effects; a function returning `α` cannot. Pure code may still *build* and pass around `IO` actions — `def actions : List (IO Unit) := [...]` type-checks fine, because an `IO Unit` is just a value. What pure code cannot do is *run* one: there is no pure function of type `IO α → α`.
- **Effect composition.** Monads compose via monad transformers (`StateT`, `ExceptT`, `ReaderT`). The resulting type reflects all effects in play.
- **do-notation type checking.** The compiler checks that every `←` binding inside a `do` block has the correct monadic type. Mismatched monads are compile errors.
- **Main must be IO.** The entry point `def main : IO Unit` declares that the program performs IO.

## Minimal snippet

```lean
def greet : IO Unit := do
  IO.println "What is your name?"
  let name ← IO.getStdin >>= IO.FS.Stream.getLine
  IO.println s!"Hello, {name.trim}!"  -- OK: IO actions in IO context

-- Pure code may hold IO actions as data; only *running* them needs an IO context.
def actions : List (IO Unit) := [IO.println "a", IO.println "b"]
def howMany : Nat := actions.length        -- pure: evaluates to 2, prints nothing
def runAll : IO Unit := actions.forM id    -- running them is itself an IO action

def pureGreet : String := IO.println "hi"  -- error: type mismatch, IO Unit is not String
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type Classes** [→ T05](T05-type-classes.md) | `Monad`, `Functor`, `Applicative` are type classes. Custom monads need instances. |
| **Totality / partial** [→ T51](T51-totality.md) | Infinite IO loops (servers, REPLs) require `partial` since they don't terminate. |
| **Coercions** [→ T18](T18-conversions-coercions.md) | Monad transformers use `MonadLift` (a type class with coercion-like behavior) to lift inner monad actions. |
| **Dependent Types** [→ T09](T09-dependent-types.md) | Monadic return types can depend on values, enabling indexed monads (advanced). |

## Gotchas and limitations

1. **IO is not just a marker.** `IO α` is by definition `EIO IO.Error α` — an exception-handling monad. IO actions can throw, so you handle them with `try`/`catch`, or capture the failure as data with `EIO.toBaseIO : EIO ε α → BaseIO (Except ε α)`. Do not reach for `EIO.toIO` here: its job is the opposite direction, mapping a *custom* error type into `IO.Error` (`(ε → IO.Error) → EIO ε α → IO α`).

2. **Monad transformer stacking order matters.** `StateT σ (ExceptT ε IO)` and `ExceptT ε (StateT σ IO)` behave differently on errors (the first loses state on error, the second preserves it).

3. **`do`-notation pitfalls.** Forgetting `←` before a monadic value gives you `IO α` instead of `α`. Lean's error message ("type mismatch: expected α, got IO α") makes this clear, but it's a common stumble.

4. **No implicit IO promotion.** There is no ordinary function `IO α → α`. Lean's counterpart to Haskell's `unsafePerformIO` is `unsafeIO : IO α → Except IO.Error α` (and `unsafeBaseIO`), and both are `unsafe`, so calling them infects your definition. The one sanctioned exception is `dbg_trace` (gotcha 5).

5. **Debugging in pure code.** Use `dbg_trace` for printf-debugging in pure functions. It bypasses *purity*, not the type system: the term is fully type-checked, needs no `unsafe`, and keeps the pure return type — it just prints as a side effect while the expression is evaluated. `def f (n : Nat) : Nat := dbg_trace "n = {n}"; n + 1` compiles as written. Remove it for production code.

## Beginner mental model

Think of `IO` as a **permission tag**. A function tagged with `IO` is allowed to talk to the outside world. A function without the tag is *pure* — it can only compute from its arguments. The `do` block is imperative syntax: `let x ← action` runs `action` and binds the result to `x`. The compiler ensures you only use `←` with actions that have the right tag.

Coming from Rust: `IO` is somewhat like `async` — it changes the function's type to mark that something special happens. But `IO` tracks *all* side effects, not just asynchrony.

## Example A — File reading with error handling

```lean
def readConfig (path : String) : IO String := do
  let contents ← IO.FS.readFile path  -- may throw if file doesn't exist
  return contents.trim

def main : IO Unit := do
  try
    let config ← readConfig "config.txt"
    IO.println s!"Config: {config}"
  catch e =>
    IO.eprintln s!"Error: {e}"
```

## Example B — Custom monad with StateT

```lean
abbrev Counter := StateT Nat IO

def increment : Counter Unit :=
  modify (· + 1)

def logCount : Counter Unit := do
  let n ← get
  IO.println s!"Count: {n}"  -- IO action lifted into Counter automatically

def main : IO Unit := do
  let ((), finalCount) ← (do increment; increment; logCount; increment).run 0
  IO.println s!"Final: {finalCount}"  -- prints "Count: 2" then "Final: 3"
```

## Common compiler errors and how to read them

### `type mismatch: expected α, got IO α`

```
type mismatch
  IO.println "hi"
has type
  IO Unit : Type
but is expected to have type
  Unit : Type
```

**Meaning:** You forgot `←` or you're in a pure context. Either add `←` in a `do` block, or restructure to work within `IO`.

### `failed to synthesize instance of type class Monad`

```
failed to synthesize instance of type class
  Monad MyType
```

**Meaning:** You used a monad-generic function (`twice [Monad m] : m Nat → m Nat`, `forM`, `mapM`, …) at a type with no `Monad` instance. Define one, or use a known monad. A bare `do` block at a non-monadic expected type reports something different — `invalid 'do' notation, expected type is not a monad application` — with a hint to write `Id.run do` for pure code.

### `type mismatch` between different monads

```
type mismatch ... StateT Nat IO Unit ... IO Unit
```

**Meaning:** You mixed two different monad stacks. Use `MonadLift` or ensure consistent monad types within the `do` block.

## Proof perspective (brief)

From the proof perspective, monads are algebraic structures with laws (left identity, right identity, associativity). Lean's `LawfulMonad` class states these laws as propositions. In Mathlib, monads appear in the formalization of probability (the `Giry` monad) and computation theory. The `IO` monad itself is *not* axiomatized: `IO` is a `@[reducible] def` for `EIO IO.Error`, it unfolds by `rfl`, and `#print axioms IO` reports that it depends on no axioms. What resists unfolding is the layer beneath it — the runtime primitives such as `IO.getStdout`, declared `opaque` with an `@[extern]` implementation. Those have no Lean body to reduce, which is what makes reasoning about actual IO effects impractical.

## Use-case cross-references

- [→ UC-05](../usecases/UC11-effect-tracking.md) — Track side effects via IO and monads; prevent untracked mutation.

## Source anchors

- *Functional Programming in Lean* — "Monads" and "IO"
- Lean 4 source: `Init.Control.Basic` (`Monad`, `MonadLift`), `Init.System.IO`
