# Context Functions (via Instance Arguments)

> **Since:** Lean 4 (stable)

## What it is

Lean does not have a separate "context function" syntax like Scala 3's `?=>`. Instead, **instance-implicit arguments** (`[C α]`) provide the same capability natively: they are automatically supplied by the compiler from the ambient context.

The key mechanisms:

- **Instance arguments `[C α]`** — Written in square brackets, these are filled automatically by instance resolution at each call site. The caller does not need to pass them explicitly.
- **`variable` declarations** — `variable [Ord α]` declares an instance argument that is automatically inserted into all subsequent definitions in the scope. This propagates context without repetition.
- **Auto-bound implicits** — When you use a type class method like `compare x y`, the compiler automatically introduces the necessary implicit and instance arguments.
- **`@` for explicit passing** — When needed, `@function explicit_args...` lets you override automatic resolution and pass instances manually.

In Scala 3, `(using ord: Ord[A]) ?=> ...` creates a function that takes a context parameter. In Lean, `[ord : Ord α] → ...` does the same thing — the `[...]` syntax IS the context function mechanism.

## What constraint it enforces

**Instance arguments are automatically resolved from the type class database; missing instances are compile errors. `variable` declarations propagate context requirements without boilerplate.**

More specifically:

- **Automatic supply.** The caller never needs to pass instance arguments explicitly (unless using `@`). The compiler finds and supplies them.
- **Transitive propagation.** If function `f` calls function `g` which needs `[Ord α]`, and `f` also has `[Ord α]`, the instance is automatically threaded through.
- **`variable` reduces boilerplate.** Instead of writing `[Ord α]` on every function, `variable [Ord α]` adds it to all definitions in scope.

## Minimal snippet

```lean
-- Instance argument: automatically supplied at call sites
def sortedPair [Ord α] (a b : α) : α × α :=
  if compare a b == .lt then (a, b) else (b, a)

#eval sortedPair 5 3   -- (3, 5): Ord Nat instance found automatically

-- variable propagates context to all subsequent definitions
variable {α : Type} [Ord α] [ToString α]

def showSorted (a b : α) : String :=
  let (x, y) := sortedPair a b   -- [Ord α] supplied automatically
  s!"({toString x}, {toString y})"
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

1. **Not exactly Scala's context functions.** Scala 3's `?=>` creates a first-class function value that captures context. Lean's instance arguments are resolved at the *call site*, not captured as a value. To pass context as a value, use explicit structure arguments.

2. **`variable` scope.** `variable` declarations apply to the rest of the current `section`, `namespace`, or file. Closing the section ends the scope. This can surprise newcomers when definitions "lose" their constraints.

3. **Anonymous vs named instances.** `[Ord α]` provides an anonymous instance. `[inst : Ord α]` names it `inst` for explicit use in the body. Use named instances when you need to refer to the instance directly.

4. **Performance.** Each `[C α]` constraint triggers instance resolution at every call site. In hot code paths with many constraints, this can slow compilation. Consider providing instances explicitly with `@` if needed.

5. **No reader monad equivalent.** Instance arguments are resolved at compile time, not at runtime. For runtime context (like configuration), use `ReaderT` or explicit parameters.

## Beginner mental model

Think of instance arguments as **electrical outlets in a room**. When you plug in a device (call a function), the outlet (instance resolution) automatically supplies the right current (instance). You don't run extension cords (pass arguments manually) — the building's wiring handles it. `variable` is like wiring an entire floor with a specific outlet type — every room (function) on that floor gets it automatically.

Coming from Scala 3: `[Ord α]` ≈ `(using Ord[A])`. `variable [Ord α]` ≈ `given Ord[A]` at the class level. The main difference: Lean resolves at the call site, Scala can capture context functions as values.

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
end VectorOps
-- Outside the section, sum and avg have explicit [Add α] [OfNat α 0] in their signatures
```

## Use-case cross-references

- [→ UC-04](../usecases/UC04-generic-constraints.md) — Instance arguments are the mechanism for expressing generic constraints.
- [→ UC-11](../usecases/UC11-effect-tracking.md) — Monadic contexts can be threaded via instance arguments for effect-related type classes.

## Source anchors

- *Functional Programming in Lean* — "Type Classes" (instance arguments)
- *Theorem Proving in Lean 4* — Ch. 10 "Type Classes" (variable declarations)
- Lean 4 source: `Lean.Elab.Term` (instance argument elaboration)
