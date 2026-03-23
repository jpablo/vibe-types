# Immutability by Default

> **Since:** Lean 4 (stable)

## What it is

Lean is a **purely functional language** — all values are immutable by default. There are no mutable variables, mutable fields, or in-place mutation outside of controlled monadic contexts. Variable bindings created with `let` cannot be reassigned. Structure fields cannot be mutated. Lists, arrays, and all data structures are persistent (immutable).

Mutation is available only through explicit monadic mechanisms:

- **`IO.Ref`** — A mutable reference inside `IO`. Read with `IO.Ref.get`, write with `IO.Ref.set`.
- **`StateM σ`** / **`StateT σ m`** — Monadic state threading. The state is logically immutable but the monad provides a mutation-like API.
- **`ST` monad** — Region-based mutable state that is safe to run purely (via `ST.Ref`).
- **`do` mutation syntax** — Inside a `do` block with `StateM` or `IO`, `let mut x := ...` and `x := ...` provide imperative-looking syntax that desugars to state passing.

## What constraint it enforces

**All values are immutable by default; mutation is only possible inside monadic contexts (`IO`, `StateM`, `ST`) and is tracked in the type.**

More specifically:

- **No mutable variables.** `let x := 5; x := 6` is a type error outside a `do`-block with mutable state.
- **No mutable fields.** Structure fields cannot be updated in place. Use `{ record with field := newVal }` to create a new copy.
- **Effect tracking.** Functions that mutate state have monadic return types (`IO α`, `StateM σ α`). Pure functions returning `α` are guaranteed side-effect-free.
- **Functional updates.** The `{ record with field := newVal }` syntax creates a new structure with one field changed — the original is unchanged.

## Minimal snippet

```lean
structure Point where x : Nat; y : Nat

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

1. **`let mut` is syntactic sugar.** Inside a `do` block, `let mut x := 0; x := x + 1` desugars to state-passing. It is not "real" mutation — it is a convenient syntax for `StateM`.

2. **Array uniqueness optimization.** Lean's runtime performs in-place mutation on arrays when the reference count is 1. This is transparent to the programmer — the semantics remain purely functional, but performance is competitive with mutable arrays.

3. **No `var` keyword.** Unlike Swift or Kotlin, there is no way to declare a mutable local variable in pure code. All mutation goes through monads.

4. **IO.Ref is not thread-safe by default.** `IO.Ref` provides single-threaded mutable state. For concurrent mutation, use `IO.Mutex` or atomic operations.

## Beginner mental model

Think of Lean values as **photographs**. You can look at a photograph, copy it, pass it around — but you cannot change the photograph itself. If you want a "modified" version, you take a new photograph. The `IO` monad is like a **darkroom** — inside it, you can develop and modify photos, but from outside, the darkroom is a sealed box that produces a result.

Coming from Rust: Lean takes immutability further than Rust's `let` vs `let mut`. In Lean, there is no `mut` at all in pure code. All "mutation" is explicit state threading via monads, tracked in the type system.

## Example A — do-notation with mutable syntax

```lean
def sumList (xs : List Nat) : Nat := Id.run do
  let mut total := 0
  for x in xs do
    total := total + x
  return total

#eval sumList [1, 2, 3, 4, 5]   -- 15
```

`Id.run` runs the `Id` monad (pure computation with do-notation). The `let mut` desugars to state-passing — no actual mutation occurs.

## Example B — Functional update on nested structures

```lean
structure Address where city : String; zip : String
structure Person where name : String; addr : Address

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
- Lean 4 source: `Lean.Elab.Do` (desugaring of `let mut`)
