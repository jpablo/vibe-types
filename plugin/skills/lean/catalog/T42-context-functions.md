# Context Functions (via Instance Arguments)

> **Since:** Lean 4 (stable)

## What it is

Lean does not have a separate "context function" syntax like Scala 3's `?=>`. Instead, **instance-implicit arguments** (`[C α]`) provide the same capability natively: they are automatically supplied by the compiler from the ambient context.

The key mechanisms:

- **Instance arguments `[C α]`** — Written in square brackets, these are filled automatically by instance resolution at each call site. The caller does not need to pass them explicitly.
- **`variable` declarations** — `variable [Ord α]` declares an instance argument that later declarations may pick up. Since the Lean 4.9/4.10 variable-inclusion change it is inserted **only into declarations that actually use it**: a `def` that mentions `α` but calls no `Ord` method gets neither `α`'s instance binder nor the instance. (Theorems are slightly more generous — an instance binder whose type mentions an already-included variable is pulled in even if the proof never uses it, and the `include` / `omit … in` commands override that choice.)
- **Auto-bound implicits** — An unbound type variable in a signature is automatically bound as an implicit `{α : Type _}`. Only the *type* variable is auto-bound: writing `compare a b` without an `[Ord α]` binder in scope is a hard `failed to synthesize instance of type class Ord α` error, not a silently added constraint.
- **`@` for explicit passing** — When needed, `@function explicit_args...` lets you override automatic resolution and pass instances manually.

In Scala 3, `(using ord: Ord[A]) ?=> ...` creates a function that takes a context parameter. In Lean, `[ord : Ord α] → ...` does the same thing — the `[...]` syntax IS the context function mechanism.

## What constraint it enforces

**Instance arguments are automatically resolved from the type class database; missing instances are compile errors. `variable` declarations propagate context requirements without boilerplate.**

More specifically:

- **Automatic supply.** The caller never needs to pass instance arguments explicitly (unless using `@`). The compiler finds and supplies them.
- **Transitive propagation.** If function `f` calls function `g` which needs `[Ord α]`, and `f` also has `[Ord α]`, the instance is automatically threaded through.
- **`variable` reduces boilerplate.** Instead of writing `[Ord α]` on every function, `variable [Ord α]` adds it to the definitions in scope that use it — and only to those.

## Minimal snippet

```lean
-- Instance argument: automatically supplied at call sites
def sortedPair [Ord α] (a b : α) : α × α :=
  if compare a b == .lt then (a, b) else (b, a)

#eval sortedPair 5 3   -- (3, 5): Ord Nat instance found automatically

-- variable propagates context to the later definitions that use it
variable {α : Type} [Ord α] [ToString α]

def showSorted (a b : α) : String :=
  let (x, y) := sortedPair a b   -- [Ord α] supplied automatically
  s!"({toString x}, {toString y})"

#check @showSorted   -- {α : Type} → [Ord α] → [ToString α] → α → α → String

-- ...but a definition that uses neither class gets neither binder
def swap' (a b : α) : α × α := (b, a)

#check @swap'        -- {α : Type} → α → α × α  (no [Ord α], no [ToString α])
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | Instance arguments are the delivery mechanism for type class instances. `[Ord α]` requests an Ord instance from the database. |
| **Trait Solver** [→ catalog/T37](T37-trait-solver.md) | Instance resolution is the algorithm that fills in `[...]` arguments. Priority and backtracking control which instance is chosen. |
| **Generics** [→ catalog/T04](T04-generics-bounds.md) | Instance arguments are how bounded polymorphism is expressed. `[Ord α]` bounds `α` to orderable types. |
| **Implicits** [→ catalog/T38](T38-implicits-auto-bound.md) | Instance arguments `[C α]` are a special case of implicit arguments. Regular implicits `{α : Type}` are filled by unification; instance implicits by resolution. |
| **Coherence** [→ catalog/T25](T25-coherence-orphan.md) | Scoped and local instances control what context is available at different points in the code. |

## Gotchas and limitations

1. **`[C α] → β` really is a first-class context-function type.** `[Ord Nat] → Nat → Nat` is a well-formed type: you can name it, store a value of it, and pass it as a parameter (see Example C). The instance is not baked into the value — it is synthesised where the value is *applied*, exactly like Scala 3's `?=>`. What Lean lacks is Scala's *inference* of context-function types from an expected type; you write the `[…] →` arrow yourself.

2. **`variable` scope and inclusion.** `variable` declarations apply to the rest of the current `section`, `namespace`, or file — closing the section ends the scope. Within the scope, a binder is only attached to a declaration that actually uses it, so definitions can also "lose" a constraint you expected them to have. For theorems, `include x` / `omit [C α] in` force the decision either way; for `def`s the usage analysis is the only rule, so add the binder explicitly if you want it in the signature.

3. **Anonymous vs named instances.** `[Ord α]` provides an anonymous instance. `[inst : Ord α]` names it `inst` for explicit use in the body. Use named instances when you need to refer to the instance directly.

4. **Performance.** Each `[C α]` constraint triggers instance resolution at every call site. In hot code paths with many constraints, this can slow compilation. Consider providing instances explicitly with `@` if needed.

5. **No reader monad equivalent.** Instance arguments are resolved at compile time, not at runtime. For runtime context (like configuration), use `ReaderT` or explicit parameters.

## Beginner mental model

Think of instance arguments as **electrical outlets in a room**. When you plug in a device (call a function), the outlet (instance resolution) automatically supplies the right current (instance). You don't run extension cords (pass arguments manually) — the building's wiring handles it. `variable` is like offering a specific outlet type on an entire floor — but only the rooms (functions) that actually have something to plug in get one wired.

Coming from Scala 3: `[Ord α]` ≈ `(using Ord[A])`, and `variable [Ord α]` is a *hoisted* `using` clause — it declares a **requirement**, not a supply. Scala's `given` is the opposite direction (it *provides* an instance); Lean's counterpart to `given` is `instance`. Context functions carry over directly too: Scala's `(using Ord[A]) ?=> B` is Lean's `[Ord α] → β`, a genuine first-class type whose instance is resolved where the value is applied.

## Example A — Transitive context propagation

```lean
def min' [Ord α] (a b : α) : α :=
  if compare a b == .lt then a else b

def min3 [Ord α] (a b c : α) : α :=
  min' (min' a b) c   -- [Ord α] propagated automatically to both calls

#eval min3 5 2 8   -- 2
```

## Example B — variable in a section

```lean
section VectorOps
  variable {α : Type} [Add α] [OfNat α 0]

  def sum (xs : List α) : α :=
    xs.foldl (· + ·) 0        -- [Add α] and [OfNat α 0] from variable

  def avg (xs : List α) [Div α] (len : α) : α :=
    sum xs / len               -- sum uses the same [Add α] from variable

  -- `pair` mentions α but calls no method of either class, so it gets neither binder
  def pair (a : α) : α × α := (a, a)
end VectorOps

#check @sum    -- {α : Type} → [Add α] → [OfNat α 0] → List α → α
#check @pair   -- {α : Type} → α → α × α

-- live proof that `pair` really picked up no instance arguments:
example : @pair = fun {α : Type} (a : α) => (a, a) := rfl
```

## Example C — Context functions as first-class values

```lean
-- `[Ord Nat] → …` is an ordinary type: it can be named, stored, and passed around
abbrev Cmp := [Ord Nat] → Nat → Nat → Nat

def biggest : Cmp :=
  fun a b => if compare a b == .gt then a else b

-- ...and taken as a parameter, exactly like Scala 3's `(using Ord[Int]) ?=> ...`
def applyTwice (f : Cmp) (a b c : Nat) : Nat := f (f a b) c

#eval applyTwice biggest 3 7 5   -- 7

-- The instance is supplied where the value is applied, not where it was built:
#check (biggest : Nat → Nat → Nat)   -- the [Ord Nat] argument has been discharged
```

## Use-case cross-references

- [→ UC-04](../usecases/UC04-generic-constraints.md) — Instance arguments are the mechanism for expressing generic constraints.
- [→ UC-11](../usecases/UC11-effect-tracking.md) — Monadic contexts can be threaded via instance arguments for effect-related type classes.

## Source anchors

- *Functional Programming in Lean* — "Type Classes" (instance arguments)
- *Theorem Proving in Lean 4* — Ch. 10 "Type Classes" (variable declarations)
- Lean 4 source: `Lean.Elab.Term` (instance argument elaboration)
