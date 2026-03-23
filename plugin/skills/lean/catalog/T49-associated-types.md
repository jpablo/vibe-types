# Associated Types (via Structure Fields)

> **Since:** Lean 4 (stable)

## What it is

Lean does not have a dedicated "associated type" syntax like Rust's `type Item;` inside a trait. Instead, the same pattern is achieved through **type-valued fields in structures and type classes**, combined with `outParam` for type inference:

- **Type-valued fields.** A structure or class can have a field of type `Type`: `class Container (c : Type) where Elem : Type`. Here `Elem` plays the role of an associated type.
- **`outParam`** — Marks a type class parameter as an output, meaning instance resolution determines its value from the input parameters. `class Container (c : Type) (elem : outParam Type)` lets the compiler infer `elem` from `c`.
- **Functional dependencies.** `outParam` creates a functional dependency: the input parameters uniquely determine the output. This is how Lean ensures `Container (List Nat)` always resolves `Elem = Nat`.

The `outParam` approach is the most common pattern in Lean 4 for what Rust calls associated types. Alternatively, a type-valued *field* inside a `class` or `structure` can serve the same purpose.

## What constraint it enforces

**Type-valued fields and `outParam` parameters create type-level associations that the compiler resolves automatically; the associated type is determined by the primary type.**

More specifically:

- **Deterministic resolution.** `outParam` ensures that given the input type, the associated type is uniquely determined. Two instances with the same input but different outputs is a coherence violation.
- **Automatic inference.** The caller does not need to specify the associated type — instance resolution computes it from the input type.
- **No ambiguity.** If two instances define different output types for the same input, the compiler reports ambiguity.

## Minimal snippet

```lean
-- outParam approach: elem is determined by c
class Container (c : Type) (elem : outParam Type) where
  empty : c
  insert : elem → c → c
  member : elem → c → Bool

instance : Container (List Nat) Nat where
  empty := []
  insert := (· :: ·)
  member x xs := xs.contains x

-- The compiler infers elem = Nat from c = List Nat
def addAndCheck [Container c α] (x : α) : c → Bool :=
  fun coll => Container.member x (Container.insert x coll)
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | Associated types are implemented via multi-parameter type classes with `outParam`. Instance resolution handles the inference. |
| **Trait Solver** [→ catalog/T37](T37-trait-solver.md) | `outParam` guides the instance resolution algorithm to determine output type parameters from input parameters. |
| **Structures** [→ catalog/T31](T31-record-types.md) | Type-valued fields in structures serve as "associated types" for individual values (not type-class-level). |
| **Dependent Types** [→ catalog/T09](T09-dependent-types.md) | Type-valued fields are possible because Lean is dependently typed — types are values and can appear as structure fields. |
| **Context Functions** [→ catalog/T42](T42-context-functions.md) | Instance arguments with `outParam` are automatically threaded through context, so the associated type propagates without boilerplate. |

## Gotchas and limitations

1. **`outParam` vs type-valued field.** `outParam` on a class parameter makes the associated type a *class-level* association (one per type). A type-valued *field* makes it a *value-level* association (different values can have different associated types). Choose based on your needs.

2. **Uniqueness requirement.** With `outParam`, each input type must map to exactly one output type. If you need the same container type with different element types, use a regular (non-`outParam`) parameter instead.

3. **Inference failures.** If the compiler cannot determine the `outParam` from context, you get "failed to synthesize." Provide a type annotation to help inference.

4. **No type member syntax.** Unlike Scala's `type Member = ...` inside a class body, Lean has no dedicated syntax for type members. The pattern is always "parameter with `outParam`" or "field of type `Type`."

5. **Mathlib conventions.** Mathlib uses `outParam` extensively in its algebraic hierarchy. The convention is that the "carrier type" is the input and algebraic structure types are outputs.

## Beginner mental model

Think of `outParam` as a **lookup function**: given a container type, it looks up the element type. `Container (List Nat)` → `elem = Nat`. The lookup is automatic — you provide the container type, and the compiler finds the element type from the instance database. Type-valued fields are simpler: they are just fields that happen to hold a type instead of a value.

Coming from Rust: `outParam Type` ≈ `type Item;` in a trait. `Container (c : Type) (elem : outParam Type)` ≈ `trait Container { type Elem; }`. The main difference: Rust's associated types are part of the trait definition syntax; Lean uses multi-parameter type classes with `outParam`.

## Example A — Iterator-like pattern

```lean
class Iterable (c : Type) (elem : outParam Type) where
  toList : c → List elem

instance : Iterable (Array Nat) Nat where
  toList := Array.toList

instance : Iterable String Char where
  toList := String.toList

-- elem is inferred from the container type
def count [Iterable c α] [BEq α] (x : α) (coll : c) : Nat :=
  (Iterable.toList coll).filter (· == x) |>.length

#eval count 'l' "hello"       -- 2
#eval count 3 #[1, 2, 3, 3]   -- 2
```

## Example B — Type-valued field in a structure

```lean
structure Schema where
  name : String
  Row : Type            -- "associated type" as a field

def usersSchema : Schema :=
  { name := "users", Row := String × Nat }

def productsSchema : Schema :=
  { name := "products", Row := String × Float × Nat }

-- Each schema has its own Row type
def exampleRow (s : Schema) (r : s.Row) : s.Row := r
```

## Use-case cross-references

- [→ UC-04](../usecases/UC04-generic-constraints.md) — Associated types via `outParam` enable generic programming over containers with determined element types.
- [→ UC-02](../usecases/UC02-domain-modeling.md) — Type-valued fields model domain schemas where each entity has an associated data type.

## Source anchors

- *Functional Programming in Lean* — "Type Classes" (outParam)
- *Theorem Proving in Lean 4* — Ch. 10 "Type Classes" (multi-parameter classes)
- Lean 4 source: `Lean.Meta.SynthInstance` (outParam handling)
