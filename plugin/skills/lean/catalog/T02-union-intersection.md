# Union & Intersection Types (via Inductive Types and Type Classes)

> **Since:** Lean 4 (stable)

## What it is

Lean has **no built-in union or intersection type syntax** like TypeScript's `A | B` or `A & B`. Instead, the same goals are achieved through existing mechanisms:

**Union types** — modeled via:
- **`Sum α β`** — A standard library type with constructors `.inl : α → Sum α β` and `.inr : β → Sum α β`. This is the disjoint union (tagged union / coproduct).
- **Custom inductive types** — For domain-specific unions, define an inductive with one constructor per variant (see [→ catalog/T01](T01-algebraic-data-types.md)).
- **`Or P Q`** — The propositional version of `Sum`, used for logical disjunction in `Prop`.

**Intersection types** — modeled via:
- **Multiple type class constraints** — `[Ord α] [BEq α] [Hashable α]` requires `α` to satisfy all three interfaces simultaneously. This serves the role of intersection types for interfaces.
- **Structure extension** — `structure C extends A, B` creates a type that has all fields of both `A` and `B`.
- **Sigma types** — `(x : α) × β x` pairs a value with evidence, serving as a dependent intersection.

## What constraint it enforces

**Sum types require explicit tagging and exhaustive case analysis; type class constraints require all listed interfaces to be satisfied.**

More specifically:

- **Explicit tagging.** `Sum α β` requires wrapping values with `.inl` or `.inr`. There is no implicit "either" — the programmer must choose and the consumer must handle both.
- **Exhaustive handling.** Pattern matching on `Sum` requires both `.inl` and `.inr` branches.
- **Conjunctive constraints.** `[Ord α] [BEq α]` means `α` must have *both* instances. Missing either is a compile error.
- **No structural subtyping.** Lean uses nominal typing. A type does not automatically satisfy an interface just because it has the right fields — it must provide an explicit instance.

## Minimal snippet

```lean
-- Union via Sum
def parseInput (s : String) : Sum Nat String :=
  match s.toNat? with
  | some n => .inl n
  | none   => .inr s

def describe : Sum Nat String → String
  | .inl n => s!"Number: {n}"
  | .inr s => s!"Text: {s}"

-- Intersection via type class constraints
def sortAndShow [Ord α] [ToString α] (xs : List α) : String :=
  toString (xs.mergeSort (compareOfLessAndEq · · |>.isLT))
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Inductive Types** [→ catalog/T01](T01-algebraic-data-types.md) | Custom inductives are the preferred way to model domain-specific unions with meaningful constructor names. |
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | Multiple type class constraints serve as interface intersections. Instance resolution checks each constraint independently. |
| **Structures** [→ catalog/T31](T31-record-types.md) | `extends` combines fields from multiple parent structures, serving as record-level intersection. |
| **Propositions** [→ catalog/T29](T29-propositions-as-types.md) | `Or P Q` is the logical union; `And P Q` is the logical intersection. Both are inductive types in `Prop`. |
| **Generics** [→ catalog/T04](T04-generics-bounds.md) | Bounded polymorphism via type class constraints is how Lean achieves "a type that satisfies multiple interfaces." |

## Gotchas and limitations

1. **No untagged unions.** Unlike TypeScript's `string | number`, Lean's `Sum` always requires explicit tagging. This is intentional — untagged unions can be ambiguous.

2. **`Sum` is not `Either`.** While `Sum` serves a similar role to Haskell's `Either`, Lean convention often prefers custom inductives for domain types rather than using `Sum` directly.

3. **No subtype polymorphism.** There is no `A <: B` subtyping in Lean. If you want "any type that is both Orderable and Printable," you must use type class constraints, not structural subtyping.

4. **Coercions can simulate subtyping.** A `Coe A B` instance enables implicit conversion from `A` to `B`, which can approximate subtype relationships but is not true subtyping.

5. **Instance diamonds.** When combining multiple type class constraints, diamond inheritance can cause ambiguity. Lean handles this via instance priority and `outParam`.

## Beginner mental model

Think of Lean's approach as **explicit labeling**:
- **Union**: Instead of "this value is either a number or a string," you say "this value is a labeled box containing *either* a number (labeled `.inl`) *or* a string (labeled `.inr`)." You must check the label before using the contents.
- **Intersection**: Instead of "this type is both Orderable and Printable," you say "this function requires *both* an `Ord` plug-in *and* a `ToString` plug-in for the type."

Coming from TypeScript: `A | B` → `Sum A B` (but tagged). `A & B` → multiple `[constraints]`. Coming from Rust: `Sum` ≈ `enum Either<A, B>`. Trait bounds `T: Ord + Display` ≈ `[Ord α] [ToString α]`.

## Example A — Domain-specific union via inductive

```lean
inductive JsonValue where
  | null
  | bool (b : Bool)
  | num (n : Float)
  | str (s : String)
  | arr (xs : List JsonValue)
  | obj (fields : List (String × JsonValue))

-- This is more idiomatic than Sum for domain modeling
```

## Example B — Multiple constraints as intersection

```lean
class Serializable (α : Type) where
  serialize : α → String

class Validatable (α : Type) where
  validate : α → Bool

-- "Intersection": α must be both Serializable and Validatable
def processIfValid [Serializable α] [Validatable α] (x : α) : Option String :=
  if Validatable.validate x then
    some (Serializable.serialize x)
  else
    none
```

## Use-case cross-references

- [→ UC-02](../usecases/UC02-domain-modeling.md) — Custom inductives model domain unions; type class constraints model capability intersections.
- [→ UC-03](../usecases/UC03-exhaustiveness.md) — Sum types require exhaustive case handling.
- [→ UC-04](../usecases/UC04-generic-constraints.md) — Multiple type class constraints specify required capabilities.

## Source anchors

- *Functional Programming in Lean* — "Polymorphism" (Sum, type classes)
- *Theorem Proving in Lean 4* — Ch. 7 "Inductive Types" (Or, And)
- Lean 4 core: `Init.Prelude` (definition of `Sum`, `Or`, `And`)
