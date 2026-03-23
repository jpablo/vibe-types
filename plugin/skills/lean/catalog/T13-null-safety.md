# Null Safety — Option and the Absence of Null

> **Since:** Lean 4 (stable)

## What it is

Lean has **no null value**. There is no `nil`, `null`, `None`-by-default, or null pointer anywhere in the language. The absence of a value is modeled explicitly via `Option α`, an inductive type with two constructors: `some (val : α)` and `none`. Every use of an optional value requires the programmer to handle both cases — either via pattern matching, monadic combinators, or `Option.get!` (which panics and is discouraged).

This design eliminates null pointer exceptions entirely. If a function returns `α`, a value of type `α` is always present. If it might be absent, the return type is `Option α`, and the caller must deal with `none`.

## What constraint it enforces

**A value of type `α` is always present; absence must be represented explicitly as `Option α`, and the compiler requires handling the `none` case.**

More specifically:

- **No implicit null.** There is no way to have a "null `α`". Every value of type `α` is a genuine `α`.
- **Exhaustive handling.** Pattern matching on `Option α` requires both `some` and `none` branches. The compiler rejects incomplete matches.
- **Type-level visibility.** Whether a value can be absent is visible in the type signature. Callers always know.

## Minimal snippet

```lean
def safeDivide (a b : Nat) : Option Nat :=
  if b == 0 then none else some (a / b)

def report (a b : Nat) : String :=
  match safeDivide a b with
  | some q => s!"Result: {q}"
  | none   => "Cannot divide by zero"
  -- removing either branch → error: missing cases
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Inductive Types** [→ catalog/T01](T01-algebraic-data-types.md) | `Option` is a standard inductive type. The exhaustiveness guarantee comes from pattern matching on inductives. |
| **Monads** [→ catalog/T12](T12-effect-tracking.md) | `Option` is a `Monad`. Use `do`-notation with `←` to chain optional computations: early `none` short-circuits. |
| **Dependent Types** [→ catalog/T09](T09-dependent-types.md) | Subtypes and `Fin n` can eliminate the need for `Option` by proving a value exists at the type level. |
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | `Inhabited α` provides a default value, used by `Option.getD` and `Array.get!`. Distinct from null — it is an explicit default. |

## Gotchas and limitations

1. **`Option.get!` panics.** The `get!` method extracts the value or panics at runtime. It exists for prototyping but defeats null safety. Prefer pattern matching or `Option.getD` (with a default).

2. **`Inhabited` is not null.** The `Inhabited` type class provides a *default value* (e.g., `0` for `Nat`), not a null. It is used for array bounds defaults and `panic!` recovery, but it is always a real value.

3. **Nested optionality.** `Option (Option α)` has three states: `none`, `some none`, `some (some x)`. This can cause confusion — consider a custom type if the domain has more than two states.

4. **Performance.** `Option` introduces a runtime tag. For performance-critical inner loops, consider using sentinel values with proofs, or `Fin`-based indexing to avoid optionality.

## Beginner mental model

Think of `Option α` as a **box that might be empty**. The type system forces you to check whether the box is empty before using its contents. You cannot pretend the box is full — the compiler won't let you. If a function says it returns `α` (no `Option`), the box is always full. Period.

Coming from Rust: `Option α` ≈ `Option<T>`. The semantics are nearly identical. Coming from Java/Python: this replaces `null` entirely — there are zero null pointer exceptions in well-typed Lean code.

## Example A — Monadic chaining with do-notation

```lean
def findUser (id : Nat) : Option String :=
  if id == 42 then some "Alice" else none

def findEmail (name : String) : Option String :=
  if name == "Alice" then some "alice@example.com" else none

def lookupEmail (id : Nat) : Option String := do
  let name ← findUser id
  let email ← findEmail name
  return email
-- If any step returns `none`, the whole computation is `none`.

#eval lookupEmail 42    -- some "alice@example.com"
#eval lookupEmail 99    -- none
```

## Example B — Eliminating Option via proof

```lean
def nonEmpty (xs : List α) (h : xs ≠ []) : α :=
  match xs, h with
  | x :: _, _ => x
  -- no `none` case needed — the proof eliminates it

#eval nonEmpty [1, 2, 3] (by decide)  -- 1
```

## Use-case cross-references

- [→ UC-01](../usecases/UC01-invalid-states.md) — Option makes "absent but unexpected" an unrepresentable state.
- [→ UC-03](../usecases/UC03-exhaustiveness.md) — Exhaustive matching on Option ensures both cases are handled.

## Source anchors

- *Functional Programming in Lean* — "Optional Values"
- Lean 4 core: `Init.Prelude` (definition of `Option`)
- *Theorem Proving in Lean 4* — Ch. 7 "Inductive Types"
