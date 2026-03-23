# Callable Typing — First-Class and Dependent Functions

> **Since:** Lean 4 (stable)

## What it is

Functions in Lean are first-class values. Every function has a type, and function types are expressions in the language. The basic function type `α → β` is sugar for the dependent function type `(x : α) → β` where `β` does not mention `x`. When the return type *does* mention the argument, you get a **dependent function type** (Pi type): `(n : Nat) → Vector α n → α`.

Key properties:

- **Currying is automatic.** A function `f : Nat → Nat → Nat` takes one argument and returns a function. `f 3` is a partial application of type `Nat → Nat`.
- **Higher-order functions are pervasive.** `List.map`, `List.filter`, and all combinators take function arguments.
- **No mutation concerns.** Unlike Rust's `Fn`/`FnMut`/`FnOnce` distinction, Lean functions are pure — there is no notion of "captures mutable state." All functions are freely copyable and callable.
- **Closures are values.** `fun x => x + 1` creates an anonymous function (lambda) that captures variables from the enclosing scope immutably.

## What constraint it enforces

**Every function has a precise type that the compiler checks at every call site; dependent function types let the return type vary with the argument value.**

More specifically:

- **Argument-return consistency.** The compiler checks that arguments match the declared parameter types and the return value matches the declared return type.
- **Dependent typing.** A function `(n : Nat) → Fin n → α` ensures the second argument is bounded by the first — this is checked at every call site.
- **No runtime type errors.** There is no way to call a function with the wrong argument types. Every call is verified at compile time.

## Minimal snippet

```lean
-- Simple higher-order function
def applyTwice (f : Nat → Nat) (x : Nat) : Nat :=
  f (f x)

#eval applyTwice (· + 1) 5   -- 7

-- Dependent function type
def replicate (n : Nat) (x : α) : Vector α n :=
  match n with
  | 0     => .nil
  | n + 1 => .cons x (replicate n x)
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dependent Types** [→ catalog/T09](T09-dependent-types.md) | Dependent function types are Pi types — the return type can depend on the argument value. This is the foundation of dependent type theory. |
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | Type class constraints `[Ord α]` are implicit function arguments. A generic function is a function taking instance arguments. |
| **Effect Tracking** [→ catalog/T12](T12-effect-tracking.md) | `IO α` in a return type marks a function as effectful. Pure functions simply return `α`. |
| **Implicits** [→ catalog/T38](T38-implicits-auto-bound.md) | Implicit arguments `{α : Type}` are function parameters filled in by the compiler. They are part of the function's type. |
| **Termination** [→ catalog/T28](T28-termination.md) | Recursive functions must prove termination. Higher-order functions that take callbacks do not impose additional termination obligations on the callback. |

## Gotchas and limitations

1. **No subtyping on functions.** Functions do not have variance. `Nat → Int` is not a subtype of `Nat → Nat`, even though `Nat` coerces to `Int`. You may need explicit coercion.

2. **Partial application gotcha.** All functions are curried, so `f a b` is `(f a) b`. This means you can accidentally partially apply a function and get a function value instead of a result — the error messages can be confusing.

3. **No `Fn`-like traits.** There is no mechanism to constrain "callable things" generically (like Rust's `Fn` trait). You simply use function types directly.

4. **Eta expansion.** Two functions that compute the same results are not necessarily definitionally equal unless they are syntactically eta-equal. This matters in proofs but rarely in programs.

## Beginner mental model

Think of every function as a **typed pipe**. The pipe's label says what goes in and what comes out. You can connect pipes (compose functions), store pipes in variables, pass pipes to other pipes. With dependent function types, the output label changes based on what you put in — the pipe adapts.

Coming from Rust: Lean functions are like `Fn` closures that are always `Copy` and never capture mutable state. There is no `FnMut` or `FnOnce` because there is no mutation. Currying works like Haskell.

## Example A — Function composition

```lean
def compose (g : β → γ) (f : α → β) : α → γ :=
  fun x => g (f x)

def double (n : Nat) : Nat := n * 2
def addOne (n : Nat) : Nat := n + 1

#eval compose addOne double 5   -- 11
#eval (addOne ∘ double) 5        -- 11 (using built-in ∘)
```

## Example B — Dependent function enforcing bounds

```lean
def safeGet (xs : Array α) (i : Fin xs.size) : α :=
  xs[i]

#eval safeGet #[10, 20, 30] ⟨1, by omega⟩   -- 20
-- safeGet #[10, 20, 30] ⟨5, by omega⟩
-- error: omega fails (5 < 3 is false)
```

The dependent type `Fin xs.size` ties the index bound to the actual array, checked at compile time.

## Use-case cross-references

- [→ UC-04](../usecases/UC04-generic-constraints.md) — Function types with type class constraints model generic callable abstractions.
- [→ UC-01](../usecases/UC01-invalid-states.md) — Dependent function types prevent calling functions with invalid arguments.

## Source anchors

- *Functional Programming in Lean* — "Functions and Definitions"
- *Theorem Proving in Lean 4* — Ch. 2 "Dependent Type Theory" (Pi types)
- Lean 4 source: `Lean.Expr` (forallE constructor for Pi types)
