# Termination and Well-Founded Recursion

> **Since:** Lean 4 (stable)

## What it is

Lean requires every recursive function to terminate. This is not optional — unlike most programming languages, where an infinite loop is valid (if undesirable), Lean's type theory is *inconsistent* if non-terminating functions are allowed. The termination checker verifies that each recursive call operates on a "smaller" argument, ensuring the recursion eventually bottoms out.

By default, the checker looks for **structural recursion**: a recursive call where one argument is a strict sub-term of the input (e.g., the tail of a list, the predecessor of a `Nat`). When structural recursion is not obvious, you provide a `termination_by` clause naming a *measure* that decreases, and a `decreasing_by` clause proving the measure actually decreases — this is **well-founded recursion**.

## What constraint it enforces

**Every recursive function must terminate; the compiler rejects definitions where termination is not proven.**

More specifically:

- **No infinite loops.** Lean's kernel cannot accept a function that might not return — doing so would allow proving `False`.
- **Structural recursion by default.** If Lean detects a parameter that strictly decreases on every recursive call, it accepts the function automatically.
- **Well-founded recursion as fallback.** When structural recursion doesn't apply, `termination_by` specifies a well-founded measure and `decreasing_by` provides the proof.
- **`partial` as escape hatch.** If you genuinely need a possibly-non-terminating function (e.g., a REPL loop, server), mark it `partial` [→ T51](T51-totality.md). The compiler accepts it but taints the result.

## Minimal snippet

```lean
-- Structural recursion: accepted automatically
def factorial : Nat → Nat
  | 0     => 1
  | n + 1 => (n + 1) * factorial n  -- OK: n < n + 1

-- Well-founded recursion: needs termination_by
def gcd (a b : Nat) : Nat :=
  if b = 0 then a
  else gcd b (a % b)
termination_by b
decreasing_by
  omega   -- proves a % b < b when b ≠ 0
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Inductive Types** [→ T01](T01-algebraic-data-types.md) | Structural recursion follows the shape of inductive types — each constructor provides a smaller sub-term. |
| **Totality / partial** [→ T51](T51-totality.md) | `partial` opts out of termination checking; the tradeoff is that the function cannot be used in proofs. |
| **Proof Automation** [→ T30](T30-proof-automation.md) | `omega` and `simp` are commonly used in `decreasing_by` to discharge numeric measure proofs. |
| **Propositions as Types** [→ T29](T29-propositions-as-types.md) | A `termination_by` proof is a `Prop` term proving the measure decreases — it's the same proof system used for logical assertions. |
| **Dependent Types** [→ T09](T09-dependent-types.md) | Functions over indexed families may need explicit termination measures because the index changes shape. |

## Gotchas and limitations

1. **Mutually recursive functions.** Use `mutual ... end` blocks. Each function in the block must independently satisfy termination, and the termination measure must account for calls across functions.

2. **Nested recursion.** When the recursive call appears inside a `List.map` or similar higher-order function, the checker may not see the structural decrease. You may need to inline the map or provide a `termination_by` clause.

3. **`decreasing_by sorry`** lets you skip the proof during development. Like all uses of `sorry`, it marks the definition as unsound and should be replaced before production.

4. **`termination_by` syntax.** The measure expression follows `termination_by` directly (no `:=`). It must be an expression whose type has a `WellFoundedRelation` instance — typically `Nat`, `Prod`, or a custom well-founded order.

5. **Fuel-based recursion.** A common workaround for hard-to-prove termination is to add a "fuel" parameter (`Nat` countdown). This makes the function structurally recursive but changes its semantics (it may return a default when fuel runs out).

## Beginner mental model

Think of the termination checker as asking: **"Show me something that gets smaller every time you recurse."** If you pattern match on a `Nat` or a `List` and recurse on the smaller piece, Lean is happy — it can see the argument shrinking. If the recursion is more complex (like `gcd`), you tell Lean what to measure and prove it decreases.

Coming from Rust: Rust doesn't check termination — you can write `loop {}` freely. Lean is stricter because allowing non-termination would break the proof system. Use `partial` when you genuinely need a loop.

## Example A — Structural recursion on a list

```lean
def sum : List Nat → Nat
  | []      => 0
  | x :: xs => x + sum xs  -- OK: xs is structurally smaller than x :: xs
```

## Example B — Well-founded recursion with a measure

```lean
def collatz (n : Nat) : List Nat :=
  if n ≤ 1 then [n]
  else if n % 2 = 0 then n :: collatz (n / 2)
  else n :: collatz (3 * n + 1)
-- This does NOT pass termination checking (Collatz conjecture is unproven!)
-- You'd need `partial def collatz` to accept it.
```

```lean
-- A function where we CAN prove termination:
def log2 (n : Nat) : Nat :=
  if n ≤ 1 then 0
  else 1 + log2 (n / 2)
termination_by n
decreasing_by
  omega  -- proves n / 2 < n when n > 1
```

## Common compiler errors and how to read them

### `fail to show termination`

```
fail to show termination for
  gcd
with errors
  structural recursion cannot be used
```

**Meaning:** Lean tried structural recursion and it didn't work. Add `termination_by` with an appropriate measure, and `decreasing_by` with a proof that the measure decreases.

### `failed to prove termination, possible solutions`

```
failed to prove termination, possible solutions:
  - Use `have`-expressions to prove the remaining goals
  - Use `termination_by` to specify a well-founded relation
```

**Meaning:** Lean found a plausible measure but couldn't prove it decreases automatically. Add `decreasing_by` and use `omega`, `simp`, or manual proof.

### `cannot use 'partial' ... in a proof`

```
'partial' definition 'f' cannot be used in a proof
```

**Meaning:** You marked `f` as `partial` but then used it in a proof context. `partial` functions are computationally useful but cannot serve as evidence in `Prop` [→ T51](T51-totality.md).

## Proof perspective (brief)

Termination is essential for logical consistency. In Lean's type theory, every well-typed term must *normalize* — evaluate to a value in finite steps. A non-terminating function of type `A → B` could be used to prove anything: given `f : False → α`, a non-terminating `g : Unit → False` would make `f (g ())` a "proof" of any `α`. The termination checker prevents this. Well-founded recursion is justified by the well-ordering principle: any measure that decreases on every call in a well-founded order guarantees termination.

## Use-case cross-references

- [→ UC-03](../usecases/UC03-exhaustiveness.md) — Termination is one half of totality (the other is exhaustiveness).
- [→ UC-07](../usecases/UC24-termination.md) — Patterns for writing recursive functions that pass the checker.

## Source anchors

- *Functional Programming in Lean* — "Proving Termination" section
- *Theorem Proving in Lean 4* — Ch. 8 "Recursion" (well-founded recursion)
- Lean 4 source: `Lean.Elab.PreDefinition.WF`
