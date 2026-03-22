# Inductive Types and Pattern Matching

> **Since:** Lean 4 (stable)

## What it is

Inductive types are Lean's primary mechanism for defining data. An `inductive` declaration introduces a new type with a fixed set of constructors — each constructor specifies the shape of data it produces. Pattern matching (`match`) destructures values by constructor, and the compiler rejects any match that does not cover all cases. This is analogous to Rust's `enum` with exhaustive `match`, but Lean's inductive types are more powerful: constructors can be recursive, parameterized, and indexed by values (making them the foundation of dependent types [→ catalog/02]).

## What constraint it enforces

**Every pattern match must cover all constructors; the compiler rejects incomplete matches.**

More specifically:

- **Exhaustiveness.** A `match` expression must have a branch for every constructor of the inductive type. Missing a case is a compile error.
- **Closed alternatives.** Unlike open class hierarchies, an inductive type's constructors are fixed at definition time. No code outside the declaration can add new variants.
- **Safe destructuring.** Fields extracted via pattern matching are guaranteed to have the types declared by the constructor.

## Minimal snippet

```lean
inductive Direction where
  | north
  | south
  | east
  | west

def opposite : Direction → Direction
  | .north => .south
  | .south => .north
  | .east  => .west
  -- error: missing cases: `Direction.west`
```

Adding the missing case makes it compile:

```lean
def opposite : Direction → Direction
  | .north => .south
  | .south => .north
  | .east  => .west
  | .west  => .east   -- OK
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dependent Types** [→ catalog/02] | Inductive types can be *indexed* by values (e.g., `Vector α n`), making them dependent types. Constructors carry proofs about indices. |
| **Structures** [→ catalog/03] | A `structure` is syntactic sugar for a single-constructor inductive type with named fields. |
| **Propositions as Types** [→ catalog/06] | Propositions like `And P Q` and `Or P Q` are inductive types in `Prop`. Pattern matching on them is proof by cases. |
| **Termination Checking** [→ catalog/07] | Recursive functions over inductive types must prove termination. The compiler accepts structural recursion on a shrinking argument. |
| **Subtypes** [→ catalog/14] | Subtypes use single-constructor inductive types to attach predicates to values. |

## Gotchas and limitations

1. **No open extension.** Once an inductive type is declared, you cannot add constructors from another module. This is by design (closed world), but it means you cannot model plugin-style extensibility directly — use type classes [→ catalog/04] instead.

2. **Recursive types require termination.** If a constructor refers to the type being defined, any function that pattern-matches recursively must satisfy the termination checker [→ catalog/07]. Mutual recursion requires `mutual ... end` blocks.

3. **Universe constraints.** An inductive type in `Prop` can only eliminate into `Prop` (with exceptions for subtypes and propositions with at most one constructor). This "large elimination" restriction surprises newcomers. See [→ catalog/05] for universe details.

4. **Dot notation requires namespace.** Writing `.north` only works when the expected type is known. In ambiguous contexts, you must write `Direction.north`.

5. **Indices vs parameters.** Parameters are fixed across all constructors; indices can vary. Mixing them up leads to confusing errors about "motive is not type correct."

## Beginner mental model

Think of an inductive type as a **sealed box with labeled compartments**. Each constructor is a compartment with a specific shape. When you `match`, you must open every compartment — the compiler won't let you ignore any. If you add data (fields) to a compartment, the match arms give you typed access to that data.

Coming from Rust: `inductive` ≈ `enum`, `match` ≈ `match`, and the exhaustiveness check works the same way.

## Example A — Option-like type

```lean
inductive Maybe (α : Type) where
  | none : Maybe α
  | some : α → Maybe α

def unwrapOr (m : Maybe Nat) (default : Nat) : Nat :=
  match m with
  | .none   => default
  | .some x => x        -- OK: x has type Nat
```

## Example B — Recursive type (natural numbers)

```lean
inductive MyNat where
  | zero : MyNat
  | succ : MyNat → MyNat

def add : MyNat → MyNat → MyNat
  | .zero,   n => n
  | .succ m, n => .succ (add m n)  -- OK: structural recursion on m
```

The compiler accepts this because each recursive call is on a structurally smaller argument (`m` vs `.succ m`).

## Common compiler errors and how to read them

### `missing cases`

```
missing cases:
  Direction.west
```

**Meaning:** Your `match` does not cover every constructor. Add the missing branch.

### `motive is not type correct`

```
motive is not type correct
```

**Meaning:** Often occurs with indexed families when the match's return type depends on the index. You may need to write an explicit `motive` or use the `match` generalization feature. See [→ catalog/02] for dependent matching.

### `unknown identifier`

```
unknown identifier 'north'
```

**Meaning:** You wrote `north` instead of `.north` or `Direction.north`. Use dot notation when the expected type is clear, or fully qualify the constructor.

## Proof perspective (brief)

In type theory, inductive types are the foundation of *all* data — even logical connectives. `And P Q` is an inductive type with one constructor carrying proofs of both `P` and `Q`. `Or P Q` has two constructors (one for each disjunct). The natural numbers, lists, and trees are all inductive types. The *elimination principle* generated by each `inductive` declaration is what makes pattern matching and recursion work. In the proof world, pattern matching on `Or P Q` is proof by cases; recursion on `Nat` is proof by induction.

## Use-case cross-references

- [→ UC-01](../usecases/UC01-invalid-states.md) — Use inductive types to make invalid states unrepresentable.
- [→ UC-02](../usecases/UC02-domain-modeling.md) — Inductive families model domain invariants as type indices.
- [→ UC-03](../usecases/UC03-exhaustiveness.md) — Exhaustive matching ensures every case is handled.

## Source anchors

- *Functional Programming in Lean* — "Datatypes and Pattern Matching"
- *Theorem Proving in Lean 4* — Ch. 7 "Inductive Types"
- Lean 4 source: `Lean.Elab.Inductive`
