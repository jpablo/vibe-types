# Type Aliases — Abbrev, Def, and Reducibility

> **Since:** Lean 4 (stable)

## What it is

Lean provides a spectrum of definition transparency that controls how far the **elaborator** will unfold a name while unifying types, running `simp`, or searching for instances. Note what this is *not*: reducibility is not a kernel setting. The kernel ignores `@[reducible]` and `@[irreducible]` and unfolds any `def` it needs to. Only `opaque` is a barrier the kernel respects.

- **`abbrev`** — Fully reducible (`def` + `@[reducible]`). Unfolded at every elaborator transparency, including the `reducible`-only setting used by instance search. It is a true alias: `abbrev Ints := List Int` means `Ints` and `List Int` are interchangeable everywhere.
- **`def`** — Semireducible (default). Unfolded at `default` transparency, so `example : Score = Nat := rfl` succeeds — but *not* at `reducible` transparency, so instance search does not see through it, and bare `simp` will not unfold it.
- **`@[irreducible] def`** — Not unfolded by the elaborator even at `default` transparency, so `rfl` stops working. `unfold`, `delta`, `simp [f]`, and `with_unfolding_all` still open it, and the kernel disregards the attribute entirely.
- **`opaque`** — Never unfolded, by tactic or by kernel: the body is not handed to either, even when you wrote one. It is not an axiom, though — `#print axioms` on an `opaque` declaration reports none.

Attributes `@[reducible]` and `@[irreducible]` can override the default reducibility of `def` declarations.

## What constraint it enforces

**Reducibility annotations control how deeply the elaborator can see through definitions; `abbrev` is transparent, `opaque` is fully abstract. The kernel sees through everything except `opaque`.**

More specifically:

- **`abbrev` is invisible.** The elaborator unfolds it at every transparency — `abbrev X := T` adds no type-level distinction. `X` and `T` unify without effort, everywhere, including during instance search.
- **`def` is conditionally visible.** It unfolds during ordinary type checking (`rfl` proves `Score = Nat`), but not at `reducible` transparency, and bare `simp` leaves it alone.
- **`opaque` is a wall.** No tactic and no kernel reduction can see through it. Changing the body never breaks downstream code.
- **Instance resolution sensitivity.** Instance search runs at **`reducible`** transparency, so the only alias it sees through is `abbrev` (or a `@[reducible] def`). A plain `def` alias blocks instance synthesis exactly as hard as an `@[irreducible]` one: an instance for `List Int` applies to `abbrev Ints := List Int`, but `#synth Append Scores` fails identically for `def Scores := List Nat` and for `@[irreducible] def Scores := List Nat`.

## Minimal snippet

```lean
abbrev UserId := Nat          -- transparent: UserId = Nat everywhere
def Score := Nat               -- semireducible: unfolds at `default` transparency
@[irreducible] def Secret := Nat  -- not unfolded by the elaborator

example : UserId = Nat := rfl     -- OK: abbrev unfolds immediately
example : Score = Nat := rfl      -- OK: def unfolds during checking
example : Secret = Nat := rfl     -- error: type mismatch, Secret and Nat are not definitionally equal

-- ...but the *kernel* never cared about the attribute. Tell the elaborator to
-- drop transparency limits and the same `rfl` term goes through, axiom-free:
theorem secretIsNat : Secret = Nat := by with_unfolding_all rfl
#print axioms secretIsNat          -- does not depend on any axioms
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Newtypes** [→ catalog/T03](T03-newtypes-opaque.md) | `abbrev` is the transparent extreme; single-field structures are the nominal extreme. Choose based on how much type safety you want. |
| **Encapsulation** [→ catalog/T21](T21-encapsulation.md) | `opaque` and `@[irreducible]` support API abstraction by hiding implementation details from the type checker. |
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | Instance search runs at `reducible` transparency: it unfolds `abbrev` and nothing else. Instances for the underlying type apply to an `abbrev` alias, and to neither a plain `def` nor an `@[irreducible] def`. |
| **Universes** [→ catalog/T35](T35-universes-kinds.md) | `abbrev` preserves universe levels transparently. A `def` in a universe-polymorphic context may need explicit universe annotations. |

## Gotchas and limitations

1. **`abbrev` provides zero type safety.** `abbrev UserId := Nat` and `abbrev OrderId := Nat` are both just `Nat`. Functions accepting `UserId` will happily accept `OrderId`. Use structures for nominal distinction.

2. **Instance leakage.** Because `abbrev` unfolds, all instances for the underlying type apply to the alias. This is convenient but can cause surprising behavior if you want the alias to have *different* instances.

3. **`@[irreducible]` is softer than `opaque`.** An `@[irreducible]` definition can still be unfolded by `unfold`, `delta`, `simp [f]`, or `with_unfolding_all`, and the kernel unfolds it without being asked. `opaque` cannot be unfolded at all, by anything.

4. **Reducibility in tactics.** Bare `simp` unfolds `@[simp]`-tagged definitions and `abbrev`s — it does **not** unfold a plain `def` (`example (n : Nat) : plainDef n = n + 1 := by simp` reports "`simp` made no progress"). Naming the definition changes that: `simp [f]` unfolds a plain `def` *and* an `@[irreducible]` one. The only definition `simp [f]` cannot open is an `opaque` one.

## Beginner mental model

Think of reducibility as a **window tint** on a definition — a tint the elaborator looks through, and the kernel walks straight past:
- `abbrev` = clear glass (everyone sees through it, instance search included)
- `def` = lightly tinted (ordinary type checking sees through; instance search and bare `simp` do not)
- `@[irreducible]` = dark tint (you have to explicitly ask to see through)
- `opaque` = brick wall (nobody sees through, ever — not even the kernel)

Coming from Rust: `abbrev` ≈ `type Alias = T`. It is **Rust** that lacks the intermediate levels — it has transparent `type` aliases and nominal `struct` newtypes and nothing in between (its nearest opaque construct is `impl Trait` in return position). Lean gives you all four points on the spectrum.

## Example A — Reducibility affects type class resolution

The line that matters is `abbrev` vs *everything else* — not `def` vs `@[irreducible]`.

```lean
abbrev Ints := List Int

-- Instance for List applies automatically: `abbrev` is @[reducible], and
-- instance search runs at reducible transparency.
#check (inferInstance : Append Ints)   -- OK: Ints unfolds to List Int

def Scores := List Nat                 -- a *plain* def, no attribute

-- Instance search does not unfold it, so synthesis fails:
example : Append Scores := inferInstance  -- error: failed to synthesize Append Scores
```

An `@[irreducible] def Points := List Nat` behaves identically here — `example : Append Points := inferInstance` fails with the same message. If you want the underlying instances, you need `abbrev`; if you want them blocked, a plain `def` already blocks them.

## Example B — Controlling API surface

```lean
-- Internal implementation
@[irreducible] def Cache := Array (String × Nat)

-- Public API — clients cannot assume Cache is an Array.
-- Because Cache is irreducible, even the implementation must `unfold` it
-- explicitly to see the underlying Array (see gotcha #3).
def Cache.empty : Cache := by
  unfold Cache; exact #[]
def Cache.insert (c : Cache) (k : String) (v : Nat) : Cache := by
  unfold Cache at c ⊢      -- internally we know it's an Array
  exact c.push (k, v)
```

The `unfold`s are the price of `@[irreducible]`, and they are what a plain `def` saves you: with `def Cache := Array (String × Nat)`, `def Cache.empty : Cache := #[]` type-checks directly, because ordinary elaboration runs at `default` transparency. Clients get the same instance-search opacity either way.

## Use-case cross-references

- [→ UC-10](../usecases/UC10-encapsulation.md) — Reducibility controls how much of the implementation is visible.
- [→ UC-02](../usecases/UC02-domain-modeling.md) — Choose `abbrev` for convenience aliases, structures for domain safety.

## Source anchors

- *Functional Programming in Lean* — "Structures" (abbrev discussion)
- *Theorem Proving in Lean 4* — Ch. 6 "Interacting with Lean" (reducibility)
- Lean 4 source: `Lean.Meta.TransparencyMode`
