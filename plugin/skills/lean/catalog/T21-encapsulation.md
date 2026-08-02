# Opaque Definitions and Reducibility

> **Since:** Lean 4 (stable)

## What it is

By default, Lean definitions are *transparent* — the elaborator unfolds them while checking types, and the kernel can always unfold them. An `opaque` declaration blocks unfolding **everywhere**, including inside the very file that declares it: only the type signature is ever usable. This provides *definitional encapsulation*: clients can use the value but cannot reason about its internal structure. (`opaque` is the declaration keyword itself — it is `opaque foo : Nat := 5`, never `opaque def foo`.)

Lean also provides a spectrum of reducibility control. Reducibility is an **elaborator** transparency setting: it steers unification, `simp`, and instance search. The kernel ignores it entirely and unfolds any `def` it likes.

- **`@[reducible]`** — unfolded at every elaborator transparency, including the `reducible`-only setting used by instance search. `abbrev` is `def` + `@[reducible]`.
- **`def` (default)** — *semireducible*: unfolded at `default` transparency (so `example : Score = Nat := rfl` works), but **not** during instance search, and bare `simp` will not unfold it either.
- **`@[irreducible]`** — not unfolded at `default` transparency, so `rfl` stops working. `unfold`, `delta`, `simp [f]`, and `with_unfolding_all` all still open it, and the kernel ignores the attribute completely.
- **`opaque`** — a real barrier: no tactic opens it (`simp [f]` reports "`simp` made no progress"), and `with_unfolding_all rfl` fails too, because the kernel is never handed the body in the first place — even when you wrote one. It is *not* an axiom, though: `#print axioms` on an `opaque` declaration reports none.

## What constraint it enforces

**`opaque` declarations cannot be unfolded anywhere — not by tactics, not by the kernel, not even in their own file. Only the type signature is usable.**

More specifically:

- **Definitional encapsulation.** No proof or computation *anywhere*, including in the declaring file, can depend on the implementation of an `opaque` declaration. Only the type signature is visible. (Restricting a *name* to its defining module is a different feature: `private`.)
- **Controlled reduction.** `@[irreducible]` provides a softer, elaborator-only version — the definition is not unfolded automatically at `default` transparency but can be opened on demand with `unfold` or `simp [f]`.
- **API stability.** Changing the implementation of an `opaque` definition doesn't break downstream code, as long as the type signature remains the same.

## Minimal snippet

```lean
opaque secretHash (s : String) : UInt64

-- Nothing unfolds `secretHash` — not `simp`, not the kernel, and not this very
-- file. `#reduce secretHash "hello"` stays stuck at the symbolic term
-- `secretHash "hello"`; only the type signature is usable.

-- Opacity is not the same as "cannot run": a bodyless `opaque` still compiles
-- and evaluates to the `Inhabited` default of its result type.
#eval secretHash "hello"          -- 0

-- And an `opaque` declaration is not an axiom:
#print axioms secretHash          -- 'secretHash' does not depend on any axioms
```

More practically:

```lean
-- In module A. The subtype packages the carrier with a proof that it is
-- nonempty, so `MySet` stays abstract while `Nonempty (MySet α)` remains
-- provable — no bespoke `axiom` needed (see gotcha #3).
private opaque MySetImpl (α : Type) : {β : Type // Nonempty β} := ⟨List α, ⟨[]⟩⟩
def MySet (α : Type) : Type := (MySetImpl α).val
instance : Nonempty (MySet α) := (MySetImpl α).property

noncomputable opaque MySet.empty : MySet α
noncomputable opaque MySet.insert : MySet α → α → MySet α

-- In module B:
noncomputable def client : MySet Nat := MySet.insert MySet.empty 42  -- OK: type checks
#print axioms client   -- [Classical.choice] only — no project-specific axiom

-- The abstraction holds even here, in the file that defines it:
example : MySet Nat = List Nat := rfl  -- error: type mismatch, MySet Nat is not definitionally List Nat
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Structures** [→ T31](T31-record-types.md) | A `private` constructor blocks *construction* from other modules — the projections stay public, so field values remain readable. To hide the fields too you need `private` on them, or an `opaque` carrier, which hides the shape entirely. |
| **Proof Automation** [→ T30](T30-proof-automation.md) | Bare `simp` does not unfold a plain `def` at all. `simp [f]` unfolds a plain or `@[irreducible]` `def`, but *not* an `opaque` one — that is the only case where `simp [f]` reports "made no progress". Provide explicit `@[simp]` lemmas for `opaque` behavior. |
| **Notation & Attributes** [→ T39](T39-notation-attributes.md) | `@[reducible]`, `@[irreducible]` are attributes that control unfolding. `@[implemented_by]` provides runtime code for `opaque` definitions. |
| **Dependent Types** [→ T09](T09-dependent-types.md) | Opaque definitions block dependent type checking that relies on unfolding. This is the point — it forces abstraction. |

## Gotchas and limitations

1. **`opaque` does not block `#eval` — noncomputability does.** An `opaque` *with* a body evaluates normally, and a bodyless one evaluates via the `Inhabited` default of its result type. What actually stops compilation is when Lean has to reach for `Classical.ofNonempty` because only a `Nonempty` instance is available: `error(lean.dependsOnNoncomputable): failed to compile definition, consider marking it as 'noncomputable' because it depends on 'Classical.ofNonempty', which is 'noncomputable'`. Mark the declaration `noncomputable`, or supply an `Inhabited` instance so a computable default exists.

2. **`@[irreducible]` is leaky.** Unlike `opaque`, `@[irreducible]` can be overridden with `unfold`, `delta`, `simp [f]`, or `with_unfolding_all` — and the kernel disregards it entirely. It is an elaborator hint, not a hard barrier.

3. **`opaque` vs `axiom`.** `constant` no longer exists — it was removed from Lean 4; `opaque` replaced it. `axiom` asserts a constant into existence with no justification and shows up forever in `#print axioms` of everything downstream. `opaque` does *not* require a body (a bodyless `opaque` is legal, as in the snippets above) and adds no axiom. Prefer `opaque`; reach for `axiom` only for genuinely axiomatic assertions — note that `axiom T.instNonempty : Nonempty T` is *not* one, and makes every client report `[Classical.choice, T.instNonempty]`.

4. **Opacity is not module-relative.** `opaque` is opaque everywhere, its own file included — you cannot "peek" locally. The feature that *is* module-relative is `private`, which hides the name outside the declaring module.

5. **`private` is orthogonal.** `private def` hides the *name* from other modules. `opaque` hides the *body* from everyone. You can combine them, but mind the syntax: `opaque` is the declaration keyword and takes no `def` — write `private opaque bar : Nat := 5`, not `private opaque def bar`.

## Beginner mental model

Think of `opaque` as a **sealed box with a label on it**. Everyone can read the label ("takes a String, returns a UInt64") and nobody can open the box — not other modules, not other files, not the lines directly underneath the declaration, not the kernel. That is what makes it safe to change the internals later: no proof anywhere could have depended on them. If what you actually want is "hidden from *other modules*", that is `private`, not `opaque`.

Coming from Rust: the question "can the type system see through this definition?" barely arises, because Rust's type system never reasons about function *bodies* at all — only signatures. Rust does have opaque *types*, though: `impl Trait` in return position (and type-alias `impl Trait`) hides a concrete type behind the traits it implements, which is the closest analogue to `opaque MySet : Type`. What Lean adds is that the same knob applies to *values* and to proofs about them.

## Example A — Abstract data type

```lean
-- API module. Pairing the hidden carrier with its `Inhabited` witness keeps the
-- type abstract *and* keeps every declaration computable and axiom-free — the
-- tempting `axiom Counter.instNonempty : Nonempty Counter` would do neither.
private opaque CounterImpl : (β : Type) × Inhabited β := ⟨Nat, ⟨0⟩⟩
def Counter : Type := CounterImpl.1
instance : Inhabited Counter := CounterImpl.2

opaque Counter.new : Counter
opaque Counter.increment : Counter → Counter
opaque Counter.value : Counter → Nat

-- Client code can use the API:
def client : Nat :=
  let c := Counter.new
  let c := Counter.increment c
  let c := Counter.increment c
  Counter.value c  -- OK: type checks

#print axioms client   -- 'client' does not depend on any axioms

-- But you cannot prove anything about the results, because the bodies are hidden:
example : Counter.value (Counter.increment Counter.new) = 1 := rfl  -- error: type mismatch, rfl cannot prove this — the definitions are opaque
```

## Example B — Irreducible for controlled abstraction

```lean
@[irreducible] def myHash (s : String) : Nat :=
  s.foldl (fun acc c => acc * 31 + c.toNat) 0

-- Bare `simp` leaves it alone (it would leave a plain `def` alone too):
--   example : myHash "" = 0 := by simp   -- `simp` made no progress

-- But naming it opens it, and so does `unfold`. `@[irreducible]` buys you
-- "not unfolded *by default*", not "not unfoldable":
example : myHash "" = 0 := by simp [myHash]
example : myHash "" = 0 := by unfold myHash; simp
```

## Common compiler errors and how to read them

### `failed to compile definition … 'noncomputable'`

```
error(lean.dependsOnNoncomputable): failed to compile definition, consider marking it
as 'noncomputable' because it depends on 'Classical.ofNonempty', which is 'noncomputable'
```

**Meaning:** Not an evaluation error — a *code generation* error. You declared a bodyless `opaque` whose result type has only a `Nonempty` instance, so Lean fell back to `Classical.ofNonempty`, which has no runtime meaning. Either mark the declaration `noncomputable`, or provide an `Inhabited` instance so a computable default exists. There is no "cannot evaluate, X is opaque" error in Lean 4: an `opaque` with a body evaluates its body, and a bodyless one evaluates to the `Inhabited` default.

### `failed to synthesize` due to opaque type

When a type class instance depends on the structure of an `opaque` type, resolution may fail because the solver can't see the type's definition. Provide explicit instances or make the type `@[irreducible]` instead.

## Proof perspective (brief)

Opacity is crucial for managing proof complexity. In Mathlib, large definitions are often marked `@[irreducible]` so that unification and `simp` do not blow them up into enormous terms; `@[simp]` lemmas describe the behavior at a high level instead. This is the type-theoretic analog of information hiding: you prove properties about an interface, not an implementation. `opaque` takes this further — no amount of unfolding recovers the body, so *all* reasoning must go through lemmas you explicitly provide. Note that this is a definitional barrier, not a logical one: an `opaque` declaration is not recorded as an axiom, and `#print axioms` on it reports none. `@[irreducible]`, by contrast, is only an elaborator setting — the kernel unfolds such definitions freely, which is why `by with_unfolding_all rfl` can still prove `Secret = Nat` for an `@[irreducible] def Secret := Nat`.

## Use-case cross-references

- [→ UC-08](../usecases/UC10-encapsulation.md) — Control what leaks across module boundaries.

## Source anchors

- Lean 4 source: `Lean.Elab.Declaration` (`opaque`)
- Lean 4 documentation: "Declarations and Definitions"
