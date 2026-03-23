# Match Types — Dependent Pattern Matching at the Type Level

> **Since:** Lean 4 (stable)

## What it is

In Lean, there is no separate "match type" construct. Because types are values, the standard `match` expression works at the type level naturally. A function can return different *types* depending on its argument by using dependent pattern matching — the return type varies with the matched value.

This subsumes what other languages call "match types" (Scala 3) or "type families" (Haskell). In Lean, you simply write a function `α → Type` and use pattern matching in its body. The type checker evaluates the function at each call site to determine the resulting type.

## What constraint it enforces

**Dependent pattern matching can compute types from values; the compiler evaluates these type-level matches during type checking and enforces that each branch produces a well-formed type.**

More specifically:

- **Type-level case analysis.** A function from values to types lets each value map to a different type. The compiler evaluates the function at each use site.
- **Exhaustiveness at the type level.** The same exhaustiveness rules apply — every constructor must be covered, even in type-returning functions.
- **Definitional reduction.** The compiler reduces type-level matches during unification. `ChooseType true` reduces to `Nat` automatically.

## Minimal snippet

```lean
-- A "match type": the return type depends on the matched value
def JsonType : String → Type
  | "number" => Float
  | "string" => String
  | "bool"   => Bool
  | _        => Unit

def parse (tag : String) : JsonType tag :=
  match tag with
  | "number" => 3.14
  | "string" => "hello"
  | "bool"   => true
  | _        => ()
```

Each branch of `parse` returns a different type, and the compiler checks that each branch's value matches `JsonType tag` after substitution.

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dependent Types** [→ catalog/T09](T09-dependent-types.md) | Match types are a direct application of dependent types — the return type depends on the argument value. |
| **Type Lambdas** [→ catalog/T40](T40-type-lambdas.md) | Type-level functions and match types are the same mechanism. A `match` in a type-level function computes types from values. |
| **Inductive Types** [→ catalog/T01](T01-algebraic-data-types.md) | Type-level matching destructures inductive values to determine the result type. |
| **Compile-Time Ops** [→ catalog/T16](T16-compile-time-ops.md) | Type-level matches are evaluated at compile time by the kernel's reduction engine. |
| **Universes** [→ catalog/T35](T35-universes-kinds.md) | Type-level functions must respect universe levels. A function `Nat → Type` returns types in `Type 0`; returning higher universes requires `Type u`. |

## Gotchas and limitations

1. **Reduction depends on scrutinee.** `JsonType tag` only reduces when `tag` is a known value (e.g., a literal `"number"`). If `tag` is an opaque variable, the type stays unreduced and the compiler cannot check the branches.

2. **No open matching.** String matching (as above) requires a catch-all `| _` branch. For extensible type-level dispatch, use type classes instead.

3. **Motive inference.** Complex dependent matches may require an explicit `motive` annotation. The error "motive is not type correct" indicates that the compiler could not infer how the return type depends on the matched value.

4. **Overlapping patterns.** Lean evaluates patterns top-to-bottom. If patterns overlap, the first match wins. This can affect type-level computation if patterns are reordered.

## Beginner mental model

Think of a type-level match as a **lookup table where the keys are values and the results are types**. When you look up `"number"`, you get `Float`. When you look up `"bool"`, you get `Bool`. The compiler uses this table during type checking to verify that the data in each branch has the correct type.

Coming from Scala 3: Lean's dependent `match` serves the same role as Scala 3's `Match` types, but it requires no special syntax — `match` on values can naturally return types.

Coming from Haskell: This replaces both type families and GADTs. Lean unifies both into ordinary dependent functions with pattern matching.

## Example A — Type-safe heterogeneous access

```lean
inductive Schema where
  | int | str | pair (l r : Schema)

def Interp : Schema → Type
  | .int      => Int
  | .str      => String
  | .pair l r => Interp l × Interp r

def example1 : Interp (.pair .int .str) := (42, "hello")
-- example1 : Int × String
```

## Example B — Dependent elimination on Nat

```lean
def NTuple (α : Type) : Nat → Type
  | 0     => Unit
  | n + 1 => α × NTuple α n

def zeros : (n : Nat) → NTuple Nat n
  | 0     => ()
  | n + 1 => (0, zeros n)

#check zeros 3   -- Nat × Nat × Nat × Unit
```

## Use-case cross-references

- [→ UC-02](../usecases/UC02-domain-modeling.md) — Type-level matching enables schema-driven domain models.
- [→ UC-12](../usecases/UC12-compile-time.md) — Type-level computation is evaluated entirely at compile time.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 8 "Induction and Recursion" (dependent match)
- *Functional Programming in Lean* — "Dependent Types" section
- Lean 4 source: `Lean.Elab.Match` (dependent match elaboration)
