# Coherence & Instance Resolution (via Scoping Rules)

> **Since:** Lean 4 (stable)

## What it is

Lean's type class system does **not enforce orphan rules** — unlike Rust, whose coherence check rejects an `impl` unless the trait or the type is local to the crate. (Haskell is not the comparison to reach for: GHC permits orphan instances too, warning about them only under `-Worphans`. What GHC *does* enforce, and Lean does not, is a duplicate-instance check at declaration time.) In Lean you can define an instance for any type and any class in any module. Instead of preventing conflicts at the language level, Lean provides tools to manage them:

- **`scoped instance`** — An instance visible only when the enclosing namespace is opened. This is the primary mechanism for avoiding global instance conflicts.
- **`instance (priority := n)`** — Numeric priority controls which instance is preferred when multiple candidates exist. Higher priority wins.
- **`@[default_instance]`** — Marks an instance as the fallback when no other instance matches.
- **`local instance`** — An instance visible only in the current section/file.
- **Instance resolution** — The compiler searches for instances using a backtracking algorithm with depth and heartbeat limits.

Lean's philosophy: coherence is a *convention*, not a hard rule. Libraries should provide canonical instances and use scoping to limit experimental ones.

## What constraint it enforces

**Instance resolution must find *an* instance for each type class constraint — not a unique one. Overlapping instances coexist silently; scoping and priority control which one is picked.**

More specifically:

- **Synthesis must succeed, not be unambiguous.** If no instance is found, the compiler emits "failed to synthesize instance." If *several* instances match, there is no error and no warning of any kind: search picks one and moves on. Lean has no "ambiguous instance" diagnostic.
- **Priority ordering, then recency.** When multiple instances match, the highest-priority one wins; at equal priority, the **most recently declared** one wins. Default priority is 1000. `#synth C α` prints the instance actually selected — it is the only reliable way to find out.
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
#eval Greet.greet (42 : Nat)          -- "#42" (scoped overrides)
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

1. **No orphan rules, and no conflict report.** Any module can define an instance for any type/class pair, so two libraries can define conflicting instances for the same type. Unlike Rust, there is no compile-time error — and, importantly, the conflict does **not** surface at use sites either. The code type-checks, compiles, and runs; it just runs with whichever instance won (highest priority, then most recently declared). The practical hazard follows directly: *adding an import can silently change which instance your existing code gets*, changing behavior with no diagnostic anywhere. If an instance choice matters, pin it — `#synth` to see what you are actually getting, and pass the instance explicitly (`@f _ myInst …`) where it counts.

2. **Diamond problem.** When class C extends both A and B, which both extend D, the compiler may find multiple paths to a D instance. Lean handles this via instance priority, but complex hierarchies (especially in Mathlib) can cause slow resolution.

3. **`scoped` is not `private`.** A `scoped instance` is visible in any file that opens the namespace. It is not restricted to the defining module — only to the namespace scope.

4. **Instance search timeout.** Complex instance searches can hit the heartbeat limit. Use `set_option synthInstance.maxHeartbeats` to increase the limit or simplify the instance graph.

5. **Priority is fragile.** Relying on numeric priorities for correctness is brittle. Prefer scoped instances and explicit instance arguments (`@function instance ...`) over priority tuning.

## Beginner mental model

Think of instance resolution as a **job search with no interview panel**. When the compiler needs a `Greet Nat` instance, it posts a listing. All visible instances apply. It hires the highest-priority applicant, breaking ties in favour of whoever applied last, and never tells you there were other candidates. If none match, the compiler gives up — that is the *only* case you hear about. `scoped instance` is like a recruiter who only works in one department: invisible outside that scope.

Coming from Rust: Lean is more permissive. Rust's orphan rules prevent you from implementing a foreign trait for a foreign type precisely so that "which impl?" always has one answer. Lean allows it and hands you `scoped instance` and priority to manage the consequences — but the failure mode is silent selection, not a conflict error. Coming from Haskell: GHC also allows orphans (it only warns under `-Worphans`), but it rejects duplicate instance heads at declaration time and reports genuine overlap at the use site. Lean does neither; the closest analogue is Haskell's `{-# OVERLAPPING #-}` world, with numeric priorities instead of pragmas and no ambiguity error to fall back on.

## Example A — Priority-based disambiguation (and silent selection without it)

```lean
class Render (α : Type) where
  render : α → String

instance (priority := 500) : Render Nat where
  render n := s!"{n}"

instance (priority := 1000) : Render Nat where
  render n := s!"Nat({n})"

#eval Render.render (42 : Nat)   -- "Nat(42)" (higher priority wins — no error, no warning)

-- Drop the priorities and the overlap is still not an error. The most recently
-- declared instance simply wins, quietly:
instance : Render Bool where
  render _ := "first"

instance : Render Bool where
  render _ := "second"

#eval Render.render true   -- "second"
#synth Render Bool         -- instRenderBool_1 — the second instance
```

Nothing above is diagnosed. If the second `Render Bool` had arrived from an `import` rather than from this file, the `#eval` would have changed answer with no visible cause.

## Example B — Explicit instance to bypass resolution

```lean
class Format (α : Type) where
  fmt : α → String

instance fmtA : Format Nat where
  fmt n := s!"decimal: {n}"

instance fmtB : Format Nat where
  fmt n := s!"hex: 0x{n}" -- simplified

-- Left to synthesis, `fmtB` wins silently (same priority, declared later):
#eval Format.fmt (42 : Nat)      -- "hex: 0x42"

-- Explicitly choose the instance and the answer stops depending on
-- declaration order — or on what some other module happened to import:
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
