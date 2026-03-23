# Type-Class Derivation (Limited Built-in Support)

> **Since:** Lean 4 (stable)

## What it is

Lean supports automatic generation of type class instances via the `deriving` keyword. When you write `deriving Repr, BEq` after an inductive or structure declaration, the compiler generates instances for those type classes based on the type's structure.

Built-in derivable classes include:

- **`Repr`** — Pretty-printing representation (used by `#eval`).
- **`BEq`** — Boolean equality.
- **`DecidableEq`** — Decision procedure for propositional equality.
- **`Hashable`** — Hash function.
- **`Inhabited`** — Default value.
- **`Ord`** — Ordering comparison.
- **`Nonempty`** — Evidence that the type has at least one value.

Lean's built-in derivation is more limited than Rust's `#[derive(...)]` or Haskell's `deriving`. Complex classes like `Monad`, `Functor`, or domain-specific classes cannot be derived without writing a custom derive handler. **Mathlib** extends the set of derivable classes significantly.

## What constraint it enforces

**`deriving` generates type class instances automatically for supported classes; the compiler rejects `deriving` for unsupported classes.**

More specifically:

- **Structural generation.** Derived instances work by recursing over the type's structure. For `BEq`, it compares each field; for `Repr`, it prints each field.
- **Field constraints.** Derivation requires that all field types already have instances of the derived class. `deriving BEq` on a structure with a `Float → Float` field fails because functions do not have `BEq`.
- **No magic.** Derived instances are regular instances — they can be overridden by explicit `instance` declarations.

## Minimal snippet

```lean
structure Point where
  x : Int
  y : Int
  deriving Repr, BEq, Hashable, Inhabited

#eval (⟨1, 2⟩ : Point)            -- { x := 1, y := 2 }
#eval (⟨1, 2⟩ : Point) == ⟨1, 3⟩  -- false
#eval (default : Point)            -- { x := 0, y := 0 }
```

```lean
inductive Color where | red | green | blue
  deriving Repr, BEq, DecidableEq, Ord

-- deriving Monad on Color would fail:
-- error: default handlers have not been implemented yet
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | `deriving` generates `instance` declarations. The resulting instances participate in instance resolution like any other. |
| **Structures** [→ catalog/T31](T31-record-types.md) | Structures support `deriving` at the end of the declaration. Derived instances access fields via projections. |
| **Inductive Types** [→ catalog/T01](T01-algebraic-data-types.md) | Inductive types support `deriving` for enum-like and data-carrying constructors. |
| **Equality Safety** [→ catalog/T20](T20-equality-safety.md) | `deriving BEq` and `deriving DecidableEq` are the primary ways to opt into equality comparison. |
| **Macros** [→ catalog/T17](T17-macros-metaprogramming.md) | Custom derive handlers are written using Lean's metaprogramming framework. Mathlib uses this extensively. |

## Gotchas and limitations

1. **Limited built-in set.** Only a handful of classes support `deriving` out of the box. Attempting to derive an unsupported class gives "default handlers have not been implemented yet."

2. **All fields must have instances.** `deriving BEq` requires every field type to have a `BEq` instance. A structure containing a function type (`α → β`) will fail to derive `BEq` because functions do not support equality.

3. **No `deriving via`.** Unlike Haskell's `DerivingVia` or Rust's newtype deriving, Lean has no built-in mechanism to derive instances by delegating to an underlying type.

4. **Mutual inductives.** Derivation for mutually recursive inductive types can fail or produce incorrect instances. Write instances manually in these cases.

5. **Order matters.** `deriving` is processed in order. If class B depends on class A, derive A first. In practice, this rarely matters for built-in classes.

## Beginner mental model

Think of `deriving` as a **code generator**. You tell the compiler "please write the `BEq` instance for me based on the structure's fields." The compiler generates structural comparison code automatically. If it does not know how to generate code for a particular class, it refuses.

Coming from Rust: `deriving Repr, BEq` ≈ `#[derive(Debug, PartialEq)]`. The mechanism is similar, but Lean's set of derivable traits is smaller. Custom derive macros require metaprogramming.

## Example A — Deriving for an enum

```lean
inductive Suit where
  | hearts | diamonds | clubs | spades
  deriving Repr, BEq, Ord, DecidableEq

#eval Suit.hearts < Suit.spades   -- depends on constructor order
#eval Suit.hearts == Suit.hearts  -- true
```

## Example B — When derivation fails

```lean
structure Callback where
  name : String
  action : IO Unit

-- deriving BEq  -- would fail: IO Unit does not have BEq

-- Manual instance instead:
instance : BEq Callback where
  beq a b := a.name == b.name
```

## Use-case cross-references

- [→ UC-02](../usecases/UC02-domain-modeling.md) — Derive common instances for domain types to reduce boilerplate.
- [→ UC-04](../usecases/UC04-generic-constraints.md) — Derived instances satisfy type class constraints in generic code.

## Source anchors

- *Functional Programming in Lean* — "Type Classes" (deriving section)
- Lean 4 source: `Lean.Elab.Deriving`
- Mathlib: `Mathlib.Tactic.DeriveFintype` (example of custom derive handler)
