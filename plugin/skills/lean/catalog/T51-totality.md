# Totality, Partial Functions, and `partial`

> **Since:** Lean 4 (stable)

## What it is

A *total* function in Lean is one that (1) is defined for all possible inputs (exhaustive pattern matching) and (2) terminates on every input (passes the termination checker). By default, every function in Lean must be total. This is a stronger guarantee than most languages offer — not only must you handle all cases, your function must also provably finish executing.

The `partial` keyword lets you opt out of termination checking. A `partial def` can loop forever, use unbounded recursion, or rely on conditions the termination checker cannot verify. The tradeoff is narrower than it sounds: Lean turns the definition into an **`opaque` constant**, so it has no equation lemmas and never unfolds during type checking. You may still mention it in propositions and proof terms — you just cannot *compute* with it. Nothing unsound is introduced; `#print axioms` on a `partial def` reports that it depends on no axioms at all.

## What constraint it enforces

**Every function must handle all inputs and terminate; `partial` explicitly opts out with known consequences.**

More specifically:

- **Exhaustiveness.** Pattern matches must cover all constructors. This is checked regardless of `partial` — even partial functions must match all cases.
- **Termination.** Non-`partial` functions must prove they terminate (structural or well-founded recursion [→ T28](T28-termination.md)).
- **Opaque, not `noncomputable`.** The two are opposites: `noncomputable` means "no executable code is generated", whereas a `partial def` is fully compiled and runs. What it gives up is *definitional* content — it is an `opaque` constant, so it never reduces during type checking, `rfl`, or `simp`.
- **Inhabitation is still required.** `partial` does not let you conjure a value out of nothing. Lean demands `Inhabited`/`Nonempty` evidence for the return type before it will accept the definition, and refuses `partial def loopNo (n : Nat) : NoValue := loopNo (n + 1)` for an empty `NoValue`.
- **No silent non-termination in *recursion*.** Without `partial`, Lean rejects a recursive function it cannot prove terminating. This is about recursion specifically: a `while`/`for` loop inside a monadic `do` block already routes through core's partial fixpoint machinery, so `while true do pure ()` compiles in a plain `def` with no diagnostic at all.

## Minimal snippet

```lean
-- Total function: all cases handled, terminates
def length : List α → Nat
  | []      => 0
  | _ :: xs => 1 + length xs  -- OK

-- Partial function: may not terminate
partial def repl : IO Unit := do
  let line ← IO.getStdin >>= IO.FS.Stream.getLine
  IO.println s!"echo: {line}"
  repl  -- infinite loop: intentional, requires `partial`
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Termination** [→ T28](T28-termination.md) | Totality = exhaustiveness + termination. If you satisfy both, the function is total. |
| **Inductive Types** [→ T01](T01-algebraic-data-types.md) | Exhaustiveness comes from matching all constructors of an inductive type. |
| **Propositions as Types** [→ T29](T29-propositions-as-types.md) | Total functions can serve as proof terms and reduce inside them. A `partial` function may be mentioned freely in a proposition or proof, but it is opaque, so no proof can compute with it. |
| **IO and Monads** [→ T12](T12-effect-tracking.md) | Server loops and REPLs are inherently non-terminating and need `partial`. |

## Gotchas and limitations

1. **Opacity is viral, not mention.** If `f` is `partial` and `g` calls it, then `g` is stuck too: any goal about `g` that needs `f` to unfold is unprovable by computation (`rfl`, `decide`, `simp` on the definition). You can still state and prove facts that only use `f` as an uninterpreted symbol — `congrArg`-style reasoning, `rw` under hypotheses, and so on. And `g` need not be marked `partial` itself if it has no termination issue of its own.

2. **`partial` functions still need exhaustive matches.** `partial` only relaxes termination, not pattern coverage. You still get "missing cases" errors if you skip constructors.

3. **`partial` vs `unsafe`.** `partial` opts out of termination; `unsafe` opts out of type safety entirely (e.g., for FFI). They are independent escape hatches with different consequences [→ UC-10].

4. **Nested `partial` in structures.** A `partial def` returning a structure works fine, but you cannot use the result in a type-level computation — the kernel refuses to unfold it.

5. **Testing partial functions.** You can `#eval` a `partial` function — it runs normally at runtime. The restriction is only at the type-checking level. This makes `partial` perfectly usable for application code that doesn't need proof guarantees.

## Beginner mental model

Think of totality as a **contract with the compiler**: "I promise this function always returns a result, for every possible input, in finite time." Most functions you write satisfy this naturally. When you can't (or don't want to) satisfy the contract — like an event loop that runs forever — you use `partial` to say "I know this might not terminate, and I accept the consequences."

Coming from Rust/Python: almost no mainstream language enforces totality. In Rust, `loop {}` compiles fine. In Lean, it requires `partial` because the proof system needs termination guarantees.

## Example A — A total recursive function

```lean
def map (f : α → β) : List α → List β
  | []      => []
  | x :: xs => f x :: map f xs
-- OK: exhaustive (two cases cover List) + terminating (structural on xs)
```

## Example B — A partial server loop

```lean
structure Request where
  path : String

-- Genuinely recursive and genuinely non-terminating: every handled request is
-- pushed back onto the queue, so no argument decreases. Drop `partial` and Lean
-- answers `fail to show termination for serve`.
partial def serve (port : UInt16) : List Request → IO Unit
  | []        => IO.println s!"port {port}: idle"
  | r :: rest => do
      IO.println s!"port {port}: handling {r.path}"
      serve port (rest ++ [r])

-- Contrast: this one is *not* recursive, so it needs no `partial` at all —
-- `while` inside `do` goes through core's own partial fixpoint, and Lean
-- accepts an unmistakably infinite loop with no diagnostic.
def tick (port : UInt16) : IO Unit := do
  IO.println s!"listening on {port}"
  while true do
    pure ()
```

## Example C — What `partial` actually costs you

```lean
partial def collatzLen (n : Nat) : Nat :=
  if n <= 1 then 0
  else if n % 2 == 0 then 1 + collatzLen (n / 2)
  else 1 + collatzLen (3 * n + 1)

#eval collatzLen 27         -- 111 — fully compiled, runs normally
#print collatzLen           -- opaque collatzLen : Nat → Nat
#print axioms collatzLen    -- 'collatzLen' does not depend on any axioms

-- It may be mentioned freely in propositions and proof terms:
theorem lenCongr (a b : Nat) (h : a = b) : collatzLen a = collatzLen b := by
  rw [h]

#print axioms lenCongr      -- 'lenCongr' does not depend on any axioms
```

What you lose is reduction, not admissibility:

```lean
partial def dbl (n : Nat) : Nat := if n == 0 then 0 else 2 + dbl (n - 1)

#eval dbl 2   -- 4, at runtime

-- The constant is opaque, so `dbl 2` never computes to `4` for the kernel.
-- error: Type mismatch: rfl has type ?m = ?m but is expected to have type dbl 2 = 4
example : dbl 2 = 4 := rfl
```

## Common compiler errors and how to read them

### `fail to show termination`

```
fail to show termination for
  myLoop
```

**Meaning:** You wrote a recursive function without `partial` and Lean can't prove it terminates. Either add `termination_by` with a decreasing measure, or mark it `partial` if non-termination is intentional.

### `Missing cases:`

```
Missing cases:
[]
```

**Meaning:** Even with `partial`, you must match all constructors. Lean prints the uncovered *patterns*, not constructor names — here the empty-list pattern `[]`. Add the missing case.

### `failed to compile 'partial' definition`

```
failed to compile 'partial' definition `loopNo`, could not prove that the type
  Nat → NoValue
is nonempty.
```

**Meaning:** `partial` opts out of termination checking, not out of logic. Lean still has to know the return type has *some* inhabitant before it will introduce the opaque constant. Supply an `Inhabited`/`Nonempty` instance (or `deriving Nonempty`), or add a parameter of the return type.

### `Type mismatch` when a `partial` definition refuses to reduce

```
Type mismatch
  rfl
has type
  ?m.7 = ?m.7
but is expected to have type
  dbl 2 = 4
```

**Meaning:** There is no special "partial in a proof" error — the definition is simply `opaque`, so `dbl 2` never computes to `4` and `rfl` cannot close the goal. Fix: prove the fact about a total version of the function, or restate the goal so it does not depend on unfolding.

## Proof perspective (brief)

Totality is the cornerstone of Lean's logical soundness. In type theory, a total function of type `A → B` is a proof that "given any element of A, there exists an element of B." If the function doesn't terminate, the proof is vacuous — it claims to produce evidence but never does. Lean keeps this airtight without any axiom: a `partial def` adds **no** axiom (`#print axioms` says so), and Lean will only accept it once it has *established* that the return type is inhabited — the opposite of `sorry`, which asserts inhabitation with no evidence. What you get is an `opaque` constant of that type: logically sound and perfectly safe to reason about, but irreducible, so it carries no computational content into proofs.

## Use-case cross-references

- [→ UC-03](../usecases/UC03-exhaustiveness.md) — Totality ensures every function handles all inputs.
- [→ UC-07](../usecases/UC24-termination.md) — Patterns for making recursive functions total.

## Source anchors

- *Functional Programming in Lean* — "Proving Termination" and "Partial Functions"
- *Theorem Proving in Lean 4* — Ch. 8 "Recursion"
- Lean 4 source: `Lean.Elab.PreDefinition.Partial`
