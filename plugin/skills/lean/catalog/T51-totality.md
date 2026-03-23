# Totality, Partial Functions, and `partial`

> **Since:** Lean 4 (stable)

## What it is

A *total* function in Lean is one that (1) is defined for all possible inputs (exhaustive pattern matching) and (2) terminates on every input (passes the termination checker). By default, every function in Lean must be total. This is a stronger guarantee than most languages offer — not only must you handle all cases, your function must also provably finish executing.

The `partial` keyword lets you opt out of termination checking. A `partial def` can loop forever, use unbounded recursion, or rely on conditions the termination checker cannot verify. The tradeoff: partial functions cannot be used in proofs, and they cannot be unfolded by the kernel during type checking.

## What constraint it enforces

**Every function must handle all inputs and terminate; `partial` explicitly opts out with known consequences.**

More specifically:

- **Exhaustiveness.** Pattern matches must cover all constructors. This is checked regardless of `partial` — even partial functions must match all cases.
- **Termination.** Non-`partial` functions must prove they terminate (structural or well-founded recursion [→ T28](T28-termination.md)).
- **Tainted usage.** `partial` functions are marked with `noncomputable`-like restrictions: they can be `#eval`'d and executed, but cannot appear in proof terms or be reduced during type checking.
- **No silent non-termination.** Without `partial`, Lean rejects functions it cannot prove terminating. There is no middle ground — you cannot silently deploy possibly-infinite computation.

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
| **Propositions as Types** [→ T29](T29-propositions-as-types.md) | Total functions can serve as proof terms; `partial` functions cannot. |
| **IO and Monads** [→ T12](T12-effect-tracking.md) | Server loops and REPLs are inherently non-terminating and need `partial`. |

## Gotchas and limitations

1. **`partial` is viral in proofs.** If function `f` is `partial` and function `g` calls `f`, then `g` cannot be used in proofs either. But `g` does not need to be marked `partial` itself if it doesn't have its own termination issue.

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
partial def serve (port : UInt16) : IO Unit := do
  let socket ← IO.net.listen port
  while true do
    let conn ← socket.accept
    -- handle connection...
    pure ()
  -- `partial` required: infinite loop
```

## Common compiler errors and how to read them

### `fail to show termination`

```
fail to show termination for
  myLoop
```

**Meaning:** You wrote a recursive function without `partial` and Lean can't prove it terminates. Either add `termination_by` with a decreasing measure, or mark it `partial` if non-termination is intentional.

### `missing cases`

```
missing cases:
  List.nil
```

**Meaning:** Even with `partial`, you must match all constructors. Add the missing case.

### `'partial' definition cannot be used to prove`

```
'partial' definition 'myFun' uses 'sorry'-like axiom
```

**Meaning:** You're trying to use a `partial` function in a proof or a type-level computation. Refactor to use a total version, or accept that this proof depends on an axiom.

## Proof perspective (brief)

Totality is the cornerstone of Lean's logical soundness. In type theory, a total function of type `A → B` is a proof that "given any element of A, there exists an element of B." If the function doesn't terminate, the proof is vacuous — it claims to produce evidence but never does. `partial` is an *axiom* that asserts the function's result type is inhabited without constructive evidence, similar to `sorry` but scoped to termination. It is safe for computation but not for reasoning.

## Use-case cross-references

- [→ UC-03](../usecases/UC03-exhaustiveness.md) — Totality ensures every function handles all inputs.
- [→ UC-07](../usecases/UC24-termination.md) — Patterns for making recursive functions total.
- [→ UC-10](../usecases/UC26-escape-hatches.md) — `partial` as an escape hatch alongside `sorry` and `unsafe`.

## Source anchors

- *Functional Programming in Lean* — "Proving Termination" and "Partial Functions"
- *Theorem Proving in Lean 4* — Ch. 8 "Recursion"
- Lean 4 source: `Lean.Elab.PreDefinition.Partial`
