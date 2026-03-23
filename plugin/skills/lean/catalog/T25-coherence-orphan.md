# Coherence & Instance Resolution (via Scoping Rules)

> **Since:** Lean 4 (stable)

## What it is

Lean's type class system does **not enforce strict orphan rules** like Rust or Haskell. You can define an instance for any type and any class in any module. Instead of preventing conflicts at the language level, Lean provides tools to manage them:

- **`scoped instance`** — An instance visible only when the enclosing namespace is opened. This is the primary mechanism for avoiding global instance conflicts.
- **`instance (priority := n)`** — Numeric priority controls which instance is preferred when multiple candidates exist. Higher priority wins.
- **`@[default_instance]`** — Marks an instance as the fallback when no other instance matches.
- **`local instance`** — An instance visible only in the current section/file.
- **Instance resolution** — The compiler searches for instances using a backtracking algorithm with depth and heartbeat limits.

Lean's philosophy: coherence is a *convention*, not a hard rule. Libraries should provide canonical instances and use scoping to limit experimental ones.

## What constraint it enforces

**Instance resolution finds a unique instance for each type class constraint; ambiguous instances cause compile errors. Scoping and priority control which instances are visible.**

More specifically:

- **Synthesis must succeed.** If no instance is found, the compiler emits "failed to synthesize instance." If multiple instances match with equal priority, it emits "ambiguous."
- **Priority ordering.** When multiple instances match, the highest-priority one wins. Default priority is 1000.
- **Scoped visibility.** `scoped instance` limits an instance to the namespace, preventing it from polluting the global instance database.
- **Backtracking search.** Instance resolution tries candidates in priority order and backtracks on failure. This is more flexible than Rust's deterministic resolution but can be slower.

## Minimal snippet

```lean
class Greet (α : Type) where
  greet : α → String

-- Global instance
instance : Greet Nat where
  greet n := s!"Hello, number {n}!"

-- Scoped instance: only visible when MyModule is opened
namespace MyModule
  scoped instance : Greet Nat where
    greet n := s!"#{n}"
end MyModule

#eval Greet.greet (42 : Nat)          -- "Hello, number 42!"

open MyModule in
#eval Greet.greet (42 : Nat)          -- "#{42}" (scoped overrides)
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | Instance resolution is the mechanism that finds and applies type class instances. Priority and scoping control the search. |
| **Encapsulation** [→ catalog/T21](T21-encapsulation.md) | `scoped instance` and `local instance` use the module system to limit instance visibility. |
| **Extension Methods** [→ catalog/T19](T19-extension-methods.md) | Scoped instances serve as locally-available extension methods — new behavior visible only in specific scopes. |
| **Generics** [→ catalog/T04](T04-generics-bounds.md) | Instance resolution is invoked at every call site of a generic function with type class constraints. |
| **Trait Solver** [→ catalog/T37](T37-trait-solver.md) | This entry covers the *rules* for instances; T37 covers the *algorithm* of instance search. |

## Gotchas and limitations

1. **No orphan rules.** Any module can define an instance for any type/class pair. This is powerful but means two libraries can define conflicting instances. Unlike Rust, there is no compile-time error — the conflict surfaces as ambiguity at use sites.

2. **Diamond problem.** When class C extends both A and B, which both extend D, the compiler may find multiple paths to a D instance. Lean handles this via instance priority, but complex hierarchies (especially in Mathlib) can cause slow resolution.

3. **`scoped` is not `private`.** A `scoped instance` is visible in any file that opens the namespace. It is not restricted to the defining module — only to the namespace scope.

4. **Instance search timeout.** Complex instance searches can hit the heartbeat limit. Use `set_option synthInstance.maxHeartbeats` to increase the limit or simplify the instance graph.

5. **Priority is fragile.** Relying on numeric priorities for correctness is brittle. Prefer scoped instances and explicit instance arguments (`@function instance ...`) over priority tuning.

## Beginner mental model

Think of instance resolution as a **job search**. When the compiler needs a `Greet Nat` instance, it posts a job listing. All visible instances submit applications. If exactly one matches, it gets the job. If multiple match, the one with the highest priority wins. If none match, the compiler gives up. `scoped instance` is like a recruiter who only works in one department — invisible outside that scope.

Coming from Rust: Lean is more permissive. Rust's orphan rules prevent you from implementing a foreign trait for a foreign type. Lean allows it but provides `scoped instance` and priority to manage the consequences. Coming from Haskell: similar to Haskell's overlapping instances but with explicit priority numbers.

## Example A — Priority-based disambiguation

```lean
class Render (α : Type) where
  render : α → String

instance (priority := 500) : Render Nat where
  render n := s!"{n}"

instance (priority := 1000) : Render Nat where
  render n := s!"Nat({n})"

#eval Render.render (42 : Nat)   -- "Nat(42)" (higher priority wins)
```

## Example B — Explicit instance to bypass resolution

```lean
class Format (α : Type) where
  fmt : α → String

instance fmtA : Format Nat where
  fmt n := s!"decimal: {n}"

instance fmtB : Format Nat where
  fmt n := s!"hex: 0x{n}" -- simplified

-- Explicitly choose the instance:
#eval @Format.fmt Nat fmtA 42    -- "decimal: 42"
#eval @Format.fmt Nat fmtB 42    -- "hex: 0x42"
```

## Use-case cross-references

- [→ UC-04](../usecases/UC04-generic-constraints.md) — Instance resolution determines which implementations are used in generic code.
- [→ UC-10](../usecases/UC10-encapsulation.md) — Scoped instances control the visibility boundary of type class implementations.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 10 "Type Classes" (instance resolution, priority)
- *Functional Programming in Lean* — "Type Classes" (scoped instances)
- Lean 4 source: `Lean.Meta.SynthInstance`
