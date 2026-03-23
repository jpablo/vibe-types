# Dependent Types and Pi Types

> **Since:** Lean 4 (stable)

## What it is

A dependent type is a type that can refer to a *value*. In most languages, types and values live in separate worlds — `List<Int>` is parameterized by a type, not a number. In Lean, a type can depend on a runtime value: `Vector α n` is a list of `α` values whose length is `n : Nat`. The compiler tracks `n` at the type level and rejects operations that would violate length constraints.

The underlying mechanism is the **Pi type** (written `(x : α) → β x`), which is a function type where the return type `β` can mention the argument `x`. Every function in Lean is a Pi type — ordinary functions `α → β` are the special case where `β` doesn't mention `x`.

## What constraint it enforces

**Return types, field types, and function signatures can depend on values; the compiler checks that value-dependent constraints are consistent.**

More specifically:

- **Index consistency.** When a type is indexed by a value (e.g., `Fin n`), the compiler ensures all operations respect that index. You cannot silently mix a `Fin 5` with a `Fin 10`.
- **Proof obligations at construction.** Creating a dependently-typed value may require providing evidence (a proof) that the index constraint holds. The compiler rejects construction without that proof.
- **Propagation through computation.** The compiler simplifies type-level expressions (definitional equality) to check that types match after computation. For example, `Vector α (1 + n)` and `Vector α (n + 1)` are equal because `Nat.add` is definitionally commutative on successors.

## Minimal snippet

```lean
def Vector (α : Type) : Nat → Type
  | 0     => Unit
  | n + 1 => α × Vector α n

def head (v : Vector α (n + 1)) : α :=
  v.1    -- OK: the type guarantees at least one element

-- head (() : Vector Nat 0)  -- error: type mismatch, expected Vector Nat (n + 1)
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Inductive Types** [→ T01](T01-algebraic-data-types.md) | Indexed inductive families are the standard way to define dependent types. Each constructor specifies its index value. |
| **Propositions as Types** [→ T29](T29-propositions-as-types.md) | Dependent types encode logical statements — a function `(n : Nat) → n > 0 → Fin n` requires a proof of `n > 0`. |
| **Subtypes** [→ T26](T26-refinement-types.md) | `{ x : α // P x }` is a lightweight dependent pair — a value bundled with a proof of a predicate. |
| **Termination** [→ T28](T28-termination.md) | Functions over indexed families often need `termination_by` since structural recursion may not be obvious to the checker. |
| **Universes** [→ T35](T35-universes-kinds.md) | Dependent types can quantify over types themselves: `(α : Type u) → α → α` is universe-polymorphic. |

## Gotchas and limitations

1. **Definitional vs propositional equality.** The compiler automatically handles *definitional* equality (computation rules). But if two expressions are equal only *propositionally* (you need a proof), you must explicitly rewrite or cast. This is the most common source of "type mismatch" frustration.

2. **Type-level computation can be slow.** Complex dependent types make the kernel do more work during type checking. Deeply nested index arithmetic can cause noticeable slowdowns.

3. **Not all functions reduce.** `opaque` definitions [→ T21](T21-encapsulation.md) and some `partial` functions [→ T51](T51-totality.md) do not reduce at the type level, which can block dependent type checking.

4. **Universe restrictions.** A function that returns a `Type` lives in a higher universe. Mixing `Prop` and `Type` in dependent positions has restrictions [→ T35](T35-universes-kinds.md).

5. **Error messages can be cryptic.** When dependent types don't match, the error message shows the full normalized types, which can be large. Learning to read "expected X, got Y" with type-level computations takes practice.

## Beginner mental model

Think of dependent types as **types with a variable slot that gets filled in by a value**. `Vector α n` has a slot for the length `n`. When you write a function, the compiler tracks what's in that slot and rejects operations that don't fit — like trying to take the `head` of an empty vector.

Coming from Rust: imagine `[T; N]` where `N` is checked at compile time, but far more general — any value, not just array sizes, can appear in the type.

## Example A — Fixed-length vectors with Fin indexing

```lean
inductive Vec (α : Type) : Nat → Type where
  | nil  : Vec α 0
  | cons : α → Vec α n → Vec α (n + 1)

def Vec.get : Vec α n → Fin n → α
  | .cons x _,  ⟨0, _⟩     => x
  | .cons _ xs, ⟨i + 1, h⟩ => xs.get ⟨i, Nat.lt_of_succ_lt_succ h⟩
  -- OK: Fin n guarantees the index is in bounds
```

## Example B — Type-safe printf format

```lean
inductive Fmt where
  | lit  : String → Fmt
  | str  : Fmt
  | int  : Fmt
  | seq  : Fmt → Fmt → Fmt

def Fmt.Args : Fmt → Type
  | .lit _   => Unit
  | .str     => String
  | .int     => Int
  | .seq a b => Args a × Args b

def Fmt.render : (f : Fmt) → f.Args → String
  | .lit s,   ()       => s
  | .str,     s        => s
  | .int,     i        => toString i
  | .seq a b, (x, y)   => a.render x ++ b.render y

-- The format determines the argument types at compile time:
-- Fmt.render (.seq .str .int) ("age: ", 42)  -- OK
-- Fmt.render (.seq .str .int) (42, "age: ")  -- error: type mismatch
```

## Common compiler errors and how to read them

### `type mismatch`

```
type mismatch
  h
has type
  n = m
but is expected to have type
  n = m + 0
```

**Meaning:** The compiler cannot see that `m` and `m + 0` are definitionally equal (they are only propositionally equal). Use `simp` or `omega` [→ T30](T30-proof-automation.md) to close the gap, or `rw` to rewrite one side.

### `application type mismatch`

```
application type mismatch
  Vec.cons x xs
argument
  xs
has type
  Vec α m : Type
but is expected to have type
  Vec α n : Type
```

**Meaning:** You're trying to use a vector of length `m` where length `n` is expected. Ensure the indices match, possibly by adding an equality proof and rewriting.

### `failed to synthesize instance`

When working with dependent types and type classes together, you may see this when the compiler can't find an instance for a type involving a dependent index. Provide the instance explicitly or simplify the index expression.

## Proof perspective (brief)

Dependent types are the core of the Curry-Howard correspondence in Lean. A Pi type `(x : α) → β x` is both a function type and a universal quantifier (∀ x : α, β x). A dependent pair `Σ x : α, β x` (Sigma type) is both a data structure and an existential quantifier (∃ x : α, β x). Every theorem in Lean is a dependent type, and every proof is a term inhabiting that type.

## Sigma types (dependent pairs)

```lean
-- Sigma type: a value paired with a type that depends on it
def example : (n : Nat) × Fin n := ⟨3, ⟨2, by omega⟩⟩

-- Practical use: heterogeneous list where each element knows its type
structure DynValue where
  {T : Type}
  val : T

def hetList : List DynValue := [⟨42⟩, ⟨"hello"⟩, ⟨true⟩]
```

Coming from Scala: Sigma types are what Scala encodes with path-dependent types and abstract type members. Where Scala writes `trait Entry { type Value; val value: Value }`, Lean writes `(e : Entry) × e.Value` or uses a structure with a type-valued field directly.

## Use-case cross-references

- [→ UC-01](../usecases/UC01-invalid-states.md) — Dependent types enforce invariants (e.g., non-empty vectors) at the type level.
- [→ UC-02](../usecases/UC02-domain-modeling.md) — Model domain constraints as type indices.
- [→ UC-04](../usecases/UC12-compile-time.md) — Attach proof obligations to data construction.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 2 "Dependent Type Theory"
- *Functional Programming in Lean* — "Dependent Types" section
- Lean 4 source: `Lean.Expr` (Pi, Lambda, App)
