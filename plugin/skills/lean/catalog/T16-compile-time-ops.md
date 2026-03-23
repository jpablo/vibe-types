# Compile-Time Computation

> **Since:** Lean 4 (stable)

## What it is

In Lean, **everything is compile-time by default**. The type checker is a full computation engine — it evaluates expressions during type checking to determine whether types match. There is no separate "const eval" phase; the same reduction rules that evaluate `2 + 3` at runtime also simplify type-level expressions during compilation.

Key mechanisms:

- **`#eval`** — Evaluate an expression and print the result at elaboration time.
- **`#check`** — Inspect a type at elaboration time.
- **`decide`** — Discharge decidable propositions by computation (the compiler runs the decision procedure).
- **`native_decide`** — Like `decide`, but uses compiled native code for faster evaluation.
- **`simp`** — Simplification tactic that applies rewriting rules at compile time.
- **Definitional reduction** — The kernel unfolds definitions and reduces expressions as needed during type checking.

## What constraint it enforces

**The type checker evaluates expressions at compile time to verify type correctness; decidable propositions can be proved by computation rather than manual proof.**

More specifically:

- **Type-level computation.** Expressions in types are reduced during checking. `Vector α (2 + 3)` is the same type as `Vector α 5` because the kernel computes `2 + 3 = 5`.
- **Decidable proof discharge.** Any proposition with a `Decidable` instance can be proved by `decide` — the compiler evaluates the decision procedure and checks the result.
- **Elaboration-time evaluation.** `#eval` runs arbitrary Lean code during file processing, enabling compile-time checks, code generation, and testing.

## Minimal snippet

```lean
-- The kernel reduces 2 + 3 during type checking
example : Vector Nat (2 + 3) = Vector Nat 5 := rfl  -- OK

-- decide proves decidable propositions by computation
example : 7 < 100 := by decide                        -- OK
example : Nat.Prime 17 := by decide                    -- OK (if Decidable instance exists)

-- #eval runs code at elaboration time
#eval (List.range 10).filter (· % 2 == 0)
-- [0, 2, 4, 6, 8]
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dependent Types** [→ catalog/T09](T09-dependent-types.md) | Type-level computation is essential for dependent types — the kernel must evaluate expressions in types to check equality. |
| **Propositions as Types** [→ catalog/T29](T29-propositions-as-types.md) | `decide` bridges the gap between decidable propositions and proofs, using computation to generate evidence. |
| **Proof Automation** [→ catalog/T30](T30-proof-automation.md) | `simp`, `omega`, and `norm_num` perform compile-time computation to close proof goals. |
| **Macros** [→ catalog/T17](T17-macros-metaprogramming.md) | Macros and elaborators run at compile time. `#eval` in combination with metaprogramming enables compile-time code generation. |
| **Termination** [→ catalog/T28](T28-termination.md) | Compile-time evaluation requires termination. Non-terminating functions cannot be used in types or by `decide`. |

## Gotchas and limitations

1. **`decide` can be slow.** For large inputs, `decide` evaluates the decision procedure in the kernel, which is interpreted. Use `native_decide` for expensive computations — it compiles to native code first.

2. **Kernel reduction vs `#eval`.** The kernel (which checks types) uses a slower interpreter than `#eval` (which uses compiled code). A computation fast under `#eval` can time out during type checking. Increase `set_option maxHeartbeats` if needed.

3. **Not all functions reduce.** `opaque` definitions and functions marked `@[irreducible]` do not reduce during type checking. `partial` functions also do not reduce in the kernel.

4. **`native_decide` is trusted.** It uses compiled code and is not verified by the kernel — it is a trust boundary. For fully verified proofs, use `decide` or explicit proof terms.

5. **No staging.** Lean does not have multi-stage programming. Compile-time evaluation is implicit (via reduction) rather than explicitly staged.

## Beginner mental model

Think of Lean's compiler as a **calculator built into the type checker**. When it sees `Vector α (2 + 3)`, it computes `5` on the spot. When you write `by decide`, it runs the relevant code and checks the answer. There is no wall between "compile time" and "run time" — the same language runs in both. The main distinction is that the kernel's built-in evaluator is slower than compiled code.

Coming from Rust: Lean's compile-time computation is far more powerful than `const fn`. Every pure function automatically works at compile time. `decide` is like a super-powered `const_assert!`.

## Example A — Compile-time validated constant

```lean
def safeIndex : Fin 5 :=
  ⟨3, by decide⟩  -- compiler verifies 3 < 5 at compile time

-- def badIndex : Fin 5 :=
--   ⟨7, by decide⟩  -- error: 'decide' failed, 7 < 5 is false
```

## Example B — Type-level computation with simp

```lean
def append (xs : Vector α n) (ys : Vector α m) : Vector α (n + m) :=
  match xs with
  | .nil       => by simp [Nat.zero_add]; exact ys
  | .cons x xs => by simp [Nat.succ_add]; exact .cons x (append xs ys)
```

The `simp` tactic rewrites the goal at compile time using arithmetic lemmas, enabling the type checker to accept the definition.

## Use-case cross-references

- [→ UC-12](../usecases/UC12-compile-time.md) — Use compile-time computation to validate invariants before runtime.
- [→ UC-01](../usecases/UC01-invalid-states.md) — Decidable checks at compile time reject invalid states statically.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 4 "Tactics" (decide, simp)
- *Functional Programming in Lean* — "Interlude: Tactics, Induction, and Proofs"
- Lean 4 source: `Lean.Meta.Reduce`
