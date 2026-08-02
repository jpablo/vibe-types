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

-- Dependent function type: the return type's length index varies with `n`
inductive Vec (α : Type) : Nat → Type where
  | nil  : Vec α 0
  | cons : α → Vec α n → Vec α (n + 1)

def replicate (n : Nat) (x : α) : Vec α n :=
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

1. **Coercions are not lifted through the arrow.** `Nat` coerces to `Int`, but that does *not* make `Nat → Nat` usable where `Nat → Int` is expected: `def g : Nat → Int := (f : Nat → Nat)` fails with "type mismatch: f has type Nat → Nat but is expected to have type Nat → Int". Function types are invariant and coercion is inserted at the *value* position, so you must eta-expand and coerce the result yourself: `fun n => (f n : Int)`.

2. **Partial application gotcha.** All functions are curried, so `f a b` is `(f a) b`. This means you can accidentally partially apply a function and get a function value instead of a result — the error messages can be confusing.

3. **The `Fn`-trait analogue is `CoeFun`.** Lean's mechanism for "callable things" is the `CoeFun` class [→ catalog/T18](T18-conversions-coercions.md): an instance makes a structure applicable like a function, *and* `[CoeFun F (fun _ => α → β)]` is the constraint you write when a generic function should accept anything callable. Plain function types need no instance — they are already applicable — so core ships no `CoeFun (α → β) …`; a generic function that must also accept bare lambdas should just take `α → β`.

   ```lean
   structure Shift where
     by' : Nat

   instance : CoeFun Shift (fun _ => Nat → Nat) where
     coe s := fun n => n + s.by'

   -- The constraint version: "F is something callable as Nat → Nat".
   def twice {F : Type} [CoeFun F (fun _ => Nat → Nat)] (f : F) (x : Nat) : Nat :=
     f (f x)

   #eval twice (Shift.mk 1) 40   -- 42
   ```

4. **Eta is definitional; extensionality is not.** `f = fun x => f x` is proved by `rfl` in Lean 4 — eta is a definitional rule of the theory, for functions *and* for structures (`p = ⟨p.x, p.y⟩` is also `rfl`). The real gotcha is the other direction: two functions that agree on every input are *not* definitionally equal. Turning `∀ x, f x = g x` into `f = g` requires the `funext` theorem, which is proved from quotient soundness — `#print axioms funext` reports `[Quot.sound]`.

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

#eval safeGet #[10, 20, 30] ⟨1, by decide⟩   -- 20

-- Out of bounds is caught while elaborating the proof argument:
example : Nat := safeGet #[10, 20, 30] ⟨5, by decide⟩  -- error: `decide` proved that the proposition 5 < #[10, 20, 30].size is false
```

Use `decide`, not `omega`, for the bound here: `omega` treats `#[10, 20, 30].size` as an opaque atom rather than evaluating it to `3`, so it fails on the *in*-bounds index too.

The dependent type `Fin xs.size` ties the index bound to the actual array, checked at compile time.

## Use-case cross-references

- [→ UC-04](../usecases/UC04-generic-constraints.md) — Function types with type class constraints model generic callable abstractions.
- [→ UC-01](../usecases/UC01-invalid-states.md) — Dependent function types prevent calling functions with invalid arguments.

## Source anchors

- *Functional Programming in Lean* — "Functions and Definitions"
- *Theorem Proving in Lean 4* — Ch. 2 "Dependent Type Theory" (Pi types)
- Lean 4 source: `Lean.Expr` (forallE constructor for Pi types)
