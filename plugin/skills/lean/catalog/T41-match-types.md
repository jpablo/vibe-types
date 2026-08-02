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
- **Definitional reduction.** The compiler reduces type-level matches during unification. `ChooseType true` reduces to `Nat` automatically — subject to the transparency of the step doing the reducing (see Gotchas #1).

## Minimal snippet

```lean
-- A "match type": the return type depends on the matched value
def JsonType : String → Type
  | "number" => Float
  | "string" => String
  | "bool"   => Bool
  | _        => Unit

-- `JsonType "number"` really is definitionally `Float` — at default transparency:
example : JsonType "number" = Float := rfl

-- NOTE: shown for illustration; this definition does NOT compile. A
-- `String`-keyed match type cannot be consumed by a total function over
-- arbitrary strings, and it fails in two separate places.
def parse (tag : String) : JsonType tag :=
  match tag with
  | "number" => 3.14
  -- error: failed to synthesize instance of type class OfScientific (JsonType "number")
  | "string" => "hello"
  | "bool"   => true
  | _        => ()
  -- error: Type mismatch: `()` has type `Unit` but is expected to have type `JsonType x✝`
```

Each branch of `parse` returns a different type, and the compiler checks that each branch's value matches `JsonType tag` after substitution — but the *literal* branch fails first, before the catch-all is ever reached. Elaborating `3.14` needs an `OfScientific (JsonType "number")` instance, and instance synthesis runs at `instances` (reducible-only) transparency, where the `String.decEq` comparison of the two string literals is stuck; the `example` above succeeds only because `rfl` gets default transparency. The catch-all then fails for a genuinely different reason: `JsonType x✝` cannot reduce for an opaque variable at any transparency. For a version that type-checks, key the match type on an inductive tag — constructor patterns reduce even at reducible transparency — see Example A.

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dependent Types** [→ catalog/T09](T09-dependent-types.md) | Match types are a direct application of dependent types — the return type depends on the argument value. |
| **Type Lambdas** [→ catalog/T40](T40-type-lambdas.md) | Type-level functions and match types are the same mechanism. A `match` in a type-level function computes types from values. |
| **Inductive Types** [→ catalog/T01](T01-algebraic-data-types.md) | Type-level matching destructures inductive values to determine the result type. |
| **Compile-Time Ops** [→ catalog/T16](T16-compile-time-ops.md) | Type-level matches are evaluated at compile time by the kernel's reduction engine. |
| **Universes** [→ catalog/T35](T35-universes-kinds.md) | Type-level functions must respect universe levels. A function `Nat → Type` returns types in `Type 0`; returning higher universes requires `Type u`. |

## Gotchas and limitations

1. **Two distinct reduction problems — transparency, then scrutinee.** The obvious one: for an opaque variable `tag`, `JsonType tag` cannot reduce at any transparency, so the compiler cannot check that branch. The subtler and usually *first* one: even with a literal scrutinee, reduction depends on the transparency of the current elaboration step. `JsonType "number"` reduces to `Float` at *default* transparency (`rfl` proves it), but instance synthesis runs at `instances` — reducible-only — transparency, where the `String.decEq` comparison of two string literals is stuck. So anything needing an instance at that type (a numeric literal needing `OfScientific`, a `BEq`, …) fails even though the branch's type is "obviously" right. Keying the match type on an `inductive` tag avoids both: constructor patterns reduce at reducible transparency.

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

-- abbrev so the type checker reduces `Interp .int` to `Int` for the literal 42
abbrev Interp : Schema → Type
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

-- `NTuple` is a `def`, so the pretty-printer leaves it folded — but the two
-- types below are definitionally equal.
#check zeros 3   -- zeros 3 : NTuple Nat 3
example : NTuple Nat 3 = (Nat × Nat × Nat × Unit) := rfl
```

## Use-case cross-references

- [→ UC-02](../usecases/UC02-domain-modeling.md) — Type-level matching enables schema-driven domain models.
- [→ UC-12](../usecases/UC12-compile-time.md) — Type-level computation is evaluated entirely at compile time.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 8 "Induction and Recursion" (dependent match)
- *Functional Programming in Lean* — "Dependent Types" section
- Lean 4 source: `Lean.Elab.Match` (dependent match elaboration)
