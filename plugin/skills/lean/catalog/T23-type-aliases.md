# Type Aliases — Abbrev, Def, and Reducibility

> **Since:** Lean 4 (stable)

## What it is

Lean provides a spectrum of definition transparency that controls how the type checker treats names:

- **`abbrev`** — Fully reducible. The kernel always unfolds the definition. It is a true alias: `abbrev Ints := List Int` means `Ints` and `List Int` are interchangeable everywhere.
- **`def`** — Semireducible (default). The kernel unfolds during type checking when needed but not aggressively. Tactics like `simp` and `unfold` can open it.
- **`@[irreducible] def`** — Not unfolded automatically. The definition is abstract during type checking. `unfold` tactic can still open it explicitly.
- **`opaque`** — Never unfolded, even by tactics. The kernel treats it as an axiom with a known type but unknown body.

Attributes `@[reducible]` and `@[irreducible]` can override the default reducibility of `def` declarations.

## What constraint it enforces

**Reducibility annotations control how deeply the type checker can see through definitions; `abbrev` is transparent, `opaque` is fully abstract.**

More specifically:

- **`abbrev` is invisible.** The kernel unfolds it immediately — `abbrev X := T` adds no type-level distinction. `X` and `T` unify without effort.
- **`def` is conditionally visible.** The kernel unfolds it during type checking but instance resolution treats it as semireducible. `simp` can unfold it.
- **`opaque` is a wall.** No tactic or kernel reduction can see through it. Changing the body never breaks downstream code.
- **Instance resolution sensitivity.** Type class instance search treats `abbrev`, `def`, and `@[irreducible]` differently. An instance for `List Int` applies to `abbrev Ints := List Int` but may not apply if `Ints` were `@[irreducible]`.

## Minimal snippet

```lean
abbrev UserId := Nat          -- transparent: UserId = Nat everywhere
def Score := Nat               -- semireducible: unfolds when needed
@[irreducible] def Secret := Nat  -- not unfolded automatically

example : UserId = Nat := rfl     -- OK: abbrev unfolds immediately
example : Score = Nat := rfl      -- OK: def unfolds during checking
-- example : Secret = Nat := rfl  -- error: not definitionally equal
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Newtypes** [→ catalog/T03](T03-newtypes-opaque.md) | `abbrev` is the transparent extreme; single-field structures are the nominal extreme. Choose based on how much type safety you want. |
| **Encapsulation** [→ catalog/T21](T21-encapsulation.md) | `opaque` and `@[irreducible]` support API abstraction by hiding implementation details from the type checker. |
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | Instance search unfolds `abbrev` but not `@[irreducible]`. This affects whether instances for the underlying type apply to the alias. |
| **Universes** [→ catalog/T35](T35-universes-kinds.md) | `abbrev` preserves universe levels transparently. A `def` in a universe-polymorphic context may need explicit universe annotations. |

## Gotchas and limitations

1. **`abbrev` provides zero type safety.** `abbrev UserId := Nat` and `abbrev OrderId := Nat` are both just `Nat`. Functions accepting `UserId` will happily accept `OrderId`. Use structures for nominal distinction.

2. **Instance leakage.** Because `abbrev` unfolds, all instances for the underlying type apply to the alias. This is convenient but can cause surprising behavior if you want the alias to have *different* instances.

3. **`@[irreducible]` is softer than `opaque`.** An `@[irreducible]` definition can be explicitly unfolded by `unfold` or `delta` tactics. `opaque` cannot be unfolded at all.

4. **Reducibility in tactics.** `simp` unfolds `@[simp]`-tagged definitions and `abbrev`s but not `@[irreducible]` ones. Tactic behavior depends on reducibility settings.

## Beginner mental model

Think of reducibility as a **window tint** on a definition:
- `abbrev` = clear glass (everyone sees through it)
- `def` = lightly tinted (the type checker sees through when it needs to)
- `@[irreducible]` = dark tint (you have to explicitly ask to see through)
- `opaque` = brick wall (nobody sees through, ever)

Coming from Rust: `abbrev` ≈ `type Alias = T`. Lean has no direct equivalent of the other levels — Rust only has `type` aliases (transparent) and `struct` newtypes (opaque).

## Example A — Reducibility affects type class resolution

```lean
abbrev Ints := List Int

-- Instance for List applies automatically:
#check (inferInstance : Append Ints)   -- OK: Ints unfolds to List Int

@[irreducible] def Scores := List Nat

-- Instance search may fail:
-- #check (inferInstance : Append Scores)  -- error: failed to synthesize
```

## Example B — Controlling API surface

```lean
-- Internal implementation
@[irreducible] def Cache := Array (String × Nat)

-- Public API — clients cannot assume Cache is an Array
def Cache.empty : Cache := #[]
def Cache.insert (c : Cache) (k : String) (v : Nat) : Cache :=
  -- internally we know it's an Array
  show Array _ from c |>.push (k, v)
```

## Use-case cross-references

- [→ UC-10](../usecases/UC10-encapsulation.md) — Reducibility controls how much of the implementation is visible.
- [→ UC-02](../usecases/UC02-domain-modeling.md) — Choose `abbrev` for convenience aliases, structures for domain safety.

## Source anchors

- *Functional Programming in Lean* — "Structures" (abbrev discussion)
- *Theorem Proving in Lean 4* — Ch. 6 "Interacting with Lean" (reducibility)
- Lean 4 source: `Lean.Meta.TransparencyMode`
