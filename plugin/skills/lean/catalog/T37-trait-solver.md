# Instance Resolution (Lean's Trait Solver)

> **Since:** Lean 4 (stable)

## What it is

Lean's **instance resolution** is the algorithm that automatically finds type class instances at each use site. When you write `[Ord α]` in a function signature, the compiler must find an `Ord` instance for the concrete type `α` at every call site. This process — analogous to Rust's trait solver or Haskell's instance resolution — is a backtracking search through the instance database.

Key mechanisms:

- **Instance synthesis.** The compiler searches for instances by trying registered candidates in priority order. Each candidate may trigger further sub-searches for its own constraints.
- **Backtracking.** If a candidate fails (its sub-constraints cannot be satisfied), the solver backtracks and tries the next candidate.
- **Priority ordering.** `instance (priority := n)` controls search order. Higher priority instances are tried first. Default priority is 1000.
- **`@[default_instance]`** — Plays two roles. It is an ordinary candidate during normal search (it does *not* wait for the others to fail), and it is *additionally* consulted when elaboration gets stuck with the class's type still an unassigned metavariable. That second role is what makes a bare numeric literal default to `Nat`: `instOfNatNat` is a `@[default_instance]`, so `#check 2` elaborates at `Nat` even though `OfNat Int 2`, `OfNat Float 2`, … all match too.
- **Depth and heartbeat limits.** `synthInstance.maxHeartbeats` and `synthInstance.maxSize` prevent infinite loops.
- **`outParam`** — Marks a type class parameter as an output, meaning instance resolution determines its value rather than requiring it from the caller.

## What constraint it enforces

**The compiler must find *an* instance for each type class constraint; failure to find one is a compile error. Overlap is not — when several instances match, the search silently commits to one.**

More specifically:

- **Existence.** An instance must exist in the database (global, scoped, or local) for the concrete types at the call site.
- **No uniqueness check.** Lean never reports instance ambiguity. Overlapping instances coexist, and synthesis returns the first candidate that succeeds — ordering by priority, then by most-recent declaration. Declaring a second instance for a type that already has one silently shadows the first at every later use site.
- **Termination.** The search must complete within the heartbeat budget. Self-referential instances are pruned by cycle detection; genuinely divergent chains hit the `synthInstance` heartbeat limit.

## Minimal snippet

```lean
-- The compiler resolves [Add Nat] automatically
#eval (3 : Nat) + 5   -- 8: compiler finds Add Nat instance

-- outParam tells resolution to determine the output type
class Convert (α : Type) (β : outParam Type) where
  convert : α → β

instance : Convert Nat Int where
  convert n := Int.ofNat n

-- The compiler infers β = Int from α = Nat
#check (Convert.convert (5 : Nat) : Int)
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | Instance resolution is the runtime of the type class system. Every `[C α]` constraint triggers a resolution search. |
| **Coherence** [→ catalog/T25](T25-coherence-orphan.md) | T25 covers instance management (scoping, priority); this entry covers the search algorithm itself. |
| **Generics** [→ catalog/T04](T04-generics-bounds.md) | Instance resolution is invoked at every instantiation of a generic function with type class constraints. |
| **Implicits** [→ catalog/T38](T38-implicits-auto-bound.md) | Instance-implicit arguments `[C α]` are filled by instance resolution. Regular implicits `{α : Type}` are filled by unification. |
| **Associated Types** [→ catalog/T49](T49-associated-types.md) | `outParam` in multi-parameter type classes guides resolution to determine "associated" types from input types. |

## Gotchas and limitations

1. **Performance.** Instance resolution can be a major performance bottleneck, especially in Mathlib where the instance graph is deep. Profile with `set_option trace.Meta.synthInstance true`.

2. **Heartbeat limits.** The default `synthInstance.maxHeartbeats` may be too low for complex hierarchies. Increase with `set_option synthInstance.maxHeartbeats 400000`.

3. **Silent overlap, not ambiguity.** Unlike Rust's coherence check, Lean accepts overlapping instances and never reports an ambiguity error. The winner is whichever candidate succeeds first — priority order, then most-recently-declared:

   ```lean
   class Describe (α : Type) where describe : α → String
   instance instA : Describe Nat where describe _ := "A"
   instance instB : Describe Nat where describe _ := "B"
   #synth Describe Nat                 -- instB — no ambiguity error
   #eval Describe.describe (0 : Nat)   -- "B"

   instance (priority := 2000) instC : Describe Nat where describe _ := "C"
   #eval Describe.describe (0 : Nat)   -- "C" — higher priority now wins
   ```

   Because of this, behavior depends on instance import order and priority assignments — the same search, run in a file with a different `import` list, can silently pick a different implementation.

4. **Circular instances.** A directly self-referential instance (`instance [Loop α] : Loop α`) is *pruned* by the solver's cycle detection, and you just get `failed to synthesize`. A genuinely divergent chain — each step producing a strictly larger goal, e.g. `instance [Chain (List α)] : Chain α` — runs until the budget is exhausted: ``(deterministic) timeout at `typeclass`, maximum number of heartbeats (20000) has been reached``. Lean 3's `maximum class-instance resolution depth reached` does not exist in Lean 4.

5. **`outParam` ambiguity.** If `outParam` is used incorrectly, the solver may find multiple valid output types. Ensure that the input parameters uniquely determine the output.

6. **Differences from Rust.** Rust's trait solver is deterministic and never backtracks — if a candidate fails, it is an error. Lean's solver backtracks, making it more flexible but harder to predict.

## Beginner mental model

Think of instance resolution as a **search engine for implementations** — one that always shows you the top hit and never says "did you mean...?". The compiler has a database of all registered instances. When it needs `Ord Nat`, it queries the database, orders candidates by priority (then by most-recent declaration), and commits to the first that works. If the search fails you get a compile error; if several instances match, you get no warning at all. `outParam` is like telling the search engine "this output field should be determined by the input — find it for me."

Coming from Rust: Lean's instance resolution is more powerful and more unpredictable than Rust's trait solver. Rust never backtracks and has orphan rules for coherence. Lean backtracks and has no orphan rules — but provides priority and scoping to manage complexity.

## Example A — Tracing instance resolution

```lean
set_option trace.Meta.synthInstance true in
#check (inferInstance : Add Nat)
-- Trace output shows the search path:
-- [Meta.synthInstance] ✅ Add Nat
```

## Example B — outParam for type determination

```lean
class Collection (c : Type) (elem : outParam Type) where
  empty : c
  insert : elem → c → c
  toList : c → List elem

instance : Collection (List Nat) Nat where
  empty := []
  insert := (· :: ·)
  toList := id

-- The compiler determines elem = Nat from c = List Nat
def addAll [Collection c α] (xs : List α) (init : c) : c :=
  xs.foldl (fun acc x => Collection.insert x acc) init
```

## Use-case cross-references

- [→ UC-04](../usecases/UC04-generic-constraints.md) — Instance resolution is the mechanism that satisfies generic constraints at call sites.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 10 "Type Classes" (instance synthesis algorithm)
- Lean 4 source: `Lean.Meta.SynthInstance` (core resolution algorithm)
- *Functional Programming in Lean* — "Type Classes" (outParam, default instances)
