# Opaque Definitions and Reducibility

> **Since:** Lean 4 (stable)

## What it is

By default, Lean definitions are *transparent* — the kernel can unfold them during type checking. An `opaque def` prevents the kernel from unfolding the definition outside the module where it's defined. This provides *definitional encapsulation*: clients can use the value but cannot reason about its internal structure.

Lean also provides a spectrum of reducibility control:

- **`@[reducible]`** — always unfold (treated like an alias).
- **`def` (default)** — unfold during type checking and `simp`.
- **`@[irreducible]`** — don't unfold during type checking, but allow `unfold` tactic to open it.
- **`opaque`** — never unfold, even with tactics. The kernel treats it as an axiom with a known type but unknown body.

## What constraint it enforces

**`opaque` definitions cannot be unfolded outside their defining module; the kernel treats them as abstract constants with known types.**

More specifically:

- **Definitional encapsulation.** Proofs and computations outside the module cannot depend on the implementation of an `opaque` definition. Only the type signature is visible.
- **Controlled reduction.** `@[irreducible]` provides a softer version — the definition can be explicitly unfolded when needed but isn't unfolded automatically.
- **API stability.** Changing the implementation of an `opaque` definition doesn't break downstream code, as long as the type signature remains the same.

## Minimal snippet

```lean
opaque secretHash (s : String) : UInt64

-- #eval secretHash "hello"
-- error: 'secretHash' is opaque and cannot be evaluated

-- In the defining module, the implementation would use `@[implemented_by]`
-- to provide a runtime implementation.
```

More practically:

```lean
-- In module A:
opaque MySet (α : Type) : Type
opaque MySet.empty : MySet α
opaque MySet.insert : MySet α → α → MySet α

-- In module B:
def example : MySet Nat := MySet.insert MySet.empty 42  -- OK: type checks
-- But you cannot prove anything about MySet's internals
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Structures** [→ T31](T31-record-types.md) | Fields of a structure can be hidden by making the structure constructor `private`. `opaque` goes further — the structure's shape is completely hidden. |
| **Proof Automation** [→ T30](T30-proof-automation.md) | `simp` cannot unfold `opaque` or `@[irreducible]` definitions. You must provide explicit `@[simp]` lemmas about their behavior. |
| **Notation & Attributes** [→ T39](T39-notation-attributes.md) | `@[reducible]`, `@[irreducible]` are attributes that control unfolding. `@[implemented_by]` provides runtime code for `opaque` definitions. |
| **Dependent Types** [→ T09](T09-dependent-types.md) | Opaque definitions block dependent type checking that relies on unfolding. This is the point — it forces abstraction. |

## Gotchas and limitations

1. **`opaque` blocks `#eval`.** An `opaque` definition cannot be evaluated unless it has an `@[implemented_by]` attribute pointing to a concrete implementation. This is intentional — the runtime needs code, but the type checker doesn't need to see it.

2. **`@[irreducible]` is leaky.** Unlike `opaque`, `@[irreducible]` can be overridden with `unfold` or `delta` tactics. It's a hint, not a hard barrier.

3. **`opaque` vs `constant`.** `constant` (or `axiom`) declares a value without any implementation. `opaque` has an implementation but hides it. Prefer `opaque` when you have code; use `axiom` only for truly axiomatic assertions.

4. **Module boundaries.** `opaque` is most useful at module boundaries. Within a single file, you can still see everything. For true encapsulation, split code into separate modules.

5. **`private` is orthogonal.** `private def` hides the *name* from other modules. `opaque def` hides the *body*. You can combine them: `private opaque def` hides both.

## Beginner mental model

Think of `opaque` as a **one-way mirror on your definition**. Outside code can see the type ("this function takes a String and returns a UInt64") but cannot look inside to see the implementation. This prevents outside code from depending on implementation details, making it safe to change the internals later.

Coming from Rust: `opaque` is like putting a function behind a `pub` API but making its body equivalent to a black box — similar to trait objects where you only know the interface. In Rust, all function bodies are transparent to the compiler; Lean's `opaque` is a feature that Rust lacks.

## Example A — Abstract data type

```lean
-- API module
opaque Counter : Type
opaque Counter.new : Counter
opaque Counter.increment : Counter → Counter
opaque Counter.value : Counter → Nat

-- Client code can use the API:
def example : Nat :=
  let c := Counter.new
  let c := Counter.increment c
  let c := Counter.increment c
  Counter.value c  -- OK: type checks

-- But cannot prove Counter.value (Counter.increment Counter.new) = 1
-- because the definitions are opaque
```

## Example B — Irreducible for controlled abstraction

```lean
@[irreducible] def myHash (s : String) : Nat :=
  s.foldl (fun acc c => acc * 31 + c.toNat) 0

-- simp won't unfold myHash in proofs
-- But: `unfold myHash` in a tactic proof will work
```

## Common compiler errors and how to read them

### `cannot evaluate opaque definition`

```
cannot evaluate, 'secretHash' is opaque
```

**Meaning:** You tried to `#eval` or `#reduce` an `opaque` definition. Provide `@[implemented_by]` for runtime evaluation, or use a non-opaque definition.

### `failed to synthesize` due to opaque type

When a type class instance depends on the structure of an `opaque` type, resolution may fail because the solver can't see the type's definition. Provide explicit instances or make the type `@[irreducible]` instead.

## Proof perspective (brief)

Opacity is crucial for managing proof complexity. In Mathlib, large definitions are often marked `@[irreducible]` to prevent `simp` from unfolding them into enormous terms. Instead, `@[simp]` lemmas describe the definition's behavior at a high level. This is the type-theoretic analog of information hiding: you prove properties about an interface, not an implementation. `opaque` takes this further — the definition is an axiom with a known type, and any reasoning about it must go through lemmas you explicitly provide.

## Use-case cross-references

- [→ UC-08](../usecases/UC10-encapsulation.md) — Control what leaks across module boundaries.

## Source anchors

- Lean 4 source: `Lean.Elab.Declaration` (`opaque`)
- Lean 4 documentation: "Declarations and Definitions"
