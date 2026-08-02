# Immutability by Default

> **Since:** Lean 4 (stable)

## What it is

Lean is a **purely functional language** — all values are immutable by default. There are no mutable variables, mutable fields, or in-place mutation outside of controlled monadic contexts. Variable bindings created with `let` cannot be reassigned. Structure fields cannot be mutated. Lists, arrays, and all data structures are persistent (immutable).

Mutation is available only through explicit monadic mechanisms:

- **`IO.Ref`** — A mutable reference inside `IO`. Read with `IO.Ref.get`, write with `IO.Ref.set`.
- **`StateM σ`** / **`StateT σ m`** — Monadic state threading. The state is logically immutable but the monad provides a mutation-like API.
- **`ST` monad** — Region-based mutable state that is safe to run purely (via `ST.Ref`).
- **`do` mutation syntax** — Inside *any* `do` block — `IO`, `Option`, or the pure `Id` — `let mut x := ...` and `x := ...` provide imperative-looking syntax. The do-elaborator rewrites each reassignment into a fresh, shadowed immutable binding in whatever monad the block already runs in; no `StateM` is introduced.

## What constraint it enforces

**All values are immutable by default; mutation is only possible inside monadic contexts (`IO`, `StateM`, `ST`) and is tracked in the type.**

More specifically:

- **No mutable variables.** Reassignment is not a type error — it never gets that far. Outside a `do` block, `let x := 5; x := 6` is a *parse* error (`unexpected token ':='; expected command`), because `:=` is not a term-level statement at all. Inside a `do` block, the elaborator has a dedicated diagnostic: ``  `x` cannot be mutated, only variables declared using `let mut` can be mutated``.
- **No mutable fields.** Structure fields cannot be updated in place. Use `{ record with field := newVal }` to create a new copy.
- **Effect tracking.** Functions that mutate state have monadic return types (`IO α`, `StateM σ α`). A function returning a plain `α` is *logically* pure — the kernel can substitute equals for equals — but that is not the same as being observably silent: `dbg_trace` writes to stderr from an ordinary pure function, and `panic!` aborts. The guarantee is about equational reasoning, not about behaviour you can see.
- **Functional updates.** The `{ record with field := newVal }` syntax creates a new structure with one field changed — the original is unchanged.

## Minimal snippet

```lean
structure Point where
  x : Nat
  y : Nat

def moveRight (p : Point) : Point :=
  { p with x := p.x + 1 }   -- new Point; p is unchanged

-- p.x := p.x + 1  -- error: no mutable field assignment

-- Mutable state inside IO
def counter : IO Nat := do
  let ref ← IO.mkRef 0
  for _ in List.range 10 do
    let n ← ref.get
    ref.set (n + 1)
  ref.get

#eval counter   -- 10
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Effect Tracking** [→ catalog/T12](T12-effect-tracking.md) | Mutation is tracked in the type via monads. A function returning `IO α` may mutate; a function returning `α` cannot. |
| **Structures** [→ catalog/T31](T31-record-types.md) | Functional update syntax `{ s with field := val }` is the idiomatic way to "change" a structure field. |
| **Inductive Types** [→ catalog/T01](T01-algebraic-data-types.md) | All inductive values are immutable. Recursive structures use persistent data structures. |
| **Termination** [→ catalog/T28](T28-termination.md) | Immutability simplifies termination checking — no aliasing or mutation side channels. |

## Gotchas and limitations

1. **`let mut` is syntactic sugar — but not for `StateM`.** Inside a `do` block, `let mut x := 0; x := x + 1` is rewritten by the do-elaborator into shadowed immutable bindings in the block's *own* monad. Nothing is lifted into `StateM`, and no state monad transformer appears. Genuine state threading shows up only where control flow forces it — a loop accumulator, for instance, becomes an argument of the `ForIn` fold. It works in any monad at all:

   ```lean
   -- Option, not IO and not StateM
   def optDemo : Option Nat := do
     let mut acc := 0
     acc := acc + 1
     let x ← some 41
     acc := acc + x
     return acc

   #eval optDemo   -- some 42
   ```

   The one thing you cannot do is reassign a binding that was not declared `mut`:

   ```lean
   def wrong : Id Nat := do
     let y := 5
     -- error: `y` cannot be mutated, only variables declared using `let mut` can be mutated
     y := 6
     return y
   ```

2. **Array uniqueness optimization.** Lean's runtime performs in-place mutation on arrays when the reference count is 1. This is transparent to the programmer — the semantics remain purely functional, but performance is competitive with mutable arrays.

3. **No `var` keyword — but `let mut` is available in pure code.** There is no top-level mutable binder. What there *is* is `let mut` inside a `do` block, and a `do` block does not require an effectful monad: `Id.run do` (Example A) gives you mutable-looking locals inside an ordinary pure function like `sumList : List Nat → Nat`. The restriction is syntactic (you must be in a `do` block), not a purity boundary.

4. **IO.Ref is not thread-safe by default.** `IO.Ref` provides single-threaded mutable state. For concurrent mutation, use `Std.Mutex` (`import Std.Sync.Mutex`, then `Std.Mutex.atomically`) or atomic operations. There is no `IO.Mutex` — referring to it gives ``Unknown constant `IO.Mutex` ``.

5. **"Pure" means equationally pure, not observably silent.** A type `Nat → Nat` promises that the result depends only on the argument and that the kernel may substitute equals for equals. It does not promise the function stays quiet: `dbg_trace` performs real I/O from a pure-typed function, and `panic!` aborts. Both are deliberate escape hatches for debugging, and neither shows up in the type.

   ```lean
   def pureTrace (n : Nat) : Nat :=
     dbg_trace "computing {n}"    -- writes to stderr from a pure function
     n + 1

   #eval pureTrace 3   -- prints "computing 3", then 4
   ```

## Beginner mental model

Think of Lean values as **photographs**. You can look at a photograph, copy it, pass it around — but you cannot change the photograph itself. If you want a "modified" version, you take a new photograph. The `IO` monad is like a **darkroom** — inside it, you can develop and modify photos, but from outside, the darkroom is a sealed box that produces a result.

Coming from Rust: the `let` vs `let mut` distinction looks familiar, and Lean's `let mut` is available in pure code too — inside `Id.run do`. What differs is the meaning. Rust's `mut` grants a real write to a real memory cell, governed by the borrow checker. Lean's `let mut` is a source-level convenience that the do-elaborator compiles away into shadowed immutable bindings, so there is no aliasing to reason about and nothing escapes the block. Where Lean is genuinely stricter is *effects*: anything that touches the outside world has to say so in its type (`IO α`).

## Example A — do-notation with mutable syntax

```lean
def sumList (xs : List Nat) : Nat := Id.run do
  let mut total := 0
  for x in xs do
    total := total + x
  return total

#eval sumList [1, 2, 3, 4, 5]   -- 15
```

`sumList` is an ordinary pure function — its type is `List Nat → Nat`, with no monad in sight. `Id.run` discharges the `Id` monad that the `do` block runs in. The `let mut` is rewritten into shadowed immutable bindings; the only place a value is genuinely threaded is the `for` loop, where `total` becomes the accumulator of the `ForIn` fold. No `StateM` is involved and no actual mutation occurs.

## Example B — Functional update on nested structures

```lean
structure Address where
  city : String
  zip : String
deriving Repr
structure Person where
  name : String
  addr : Address
deriving Repr

def relocate (p : Person) (newCity : String) : Person :=
  { p with addr := { p.addr with city := newCity } }

#eval relocate { name := "Alice", addr := { city := "NY", zip := "10001" } } "LA"
-- { name := "Alice", addr := { city := "LA", zip := "10001" } }
```

## Use-case cross-references

- [→ UC-11](../usecases/UC11-effect-tracking.md) — Immutability ensures pure functions are side-effect-free.
- [→ UC-01](../usecases/UC01-invalid-states.md) — Immutable data structures prevent accidental state corruption.

## Source anchors

- *Functional Programming in Lean* — "Do-Notation" and "Mutable State"
- *Functional Programming in Lean* — "Arrays and Indexing" (uniqueness optimization)
- Lean 4 source: `Lean.Elab.Do` (the do-elaborator's rewriting of `let mut`)
- Lean 4 source: `Std.Sync.Mutex` (`Std.Mutex`, for concurrent mutable state)
