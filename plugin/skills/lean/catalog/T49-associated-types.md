# Associated Types (via Structure Fields)

> **Since:** Lean 4 (stable)

## What it is

Lean does not have a dedicated "associated type" syntax like Rust's `type Item;` inside a trait. Instead, the same pattern is achieved through **type-valued fields in structures and type classes**, combined with `outParam` for type inference:

- **Type-valued fields.** A structure or class can have a field of type `Type`: `class Container (c : Type) where Elem : Type`. Here `Elem` plays the role of an associated type.
- **`outParam`** — Marks a type class parameter as an output, meaning instance resolution determines its value from the input parameters. `class Container (c : Type) (elem : outParam Type)` lets the compiler infer `elem` from `c`.
- **A search hint, not a guarantee.** `outParam` tells `SynthInstance` not to use that argument as a search key: the goal `Container (List Nat) ?e` is solved from `List Nat` alone and `?e` is filled in from whichever instance is found. It does **not** check that the association is single-valued — keeping it so is the author's responsibility (see gotcha 2).

The `outParam` approach is the most common pattern in Lean 4 for what Rust calls associated types. A type-valued *field* serves the same purpose: inside a `class` it is again one type per instance, while inside a plain `structure` it is one type per *value*.

## What constraint it enforces

**Type-valued fields and `outParam` parameters create type-level associations that the compiler resolves automatically; the associated type is determined by the primary type.**

More specifically:

- **Directed resolution.** `outParam` makes the output argument invisible to the search: the goal is matched on the input parameters only, and the output is read off the instance that matched.
- **Automatic inference.** The caller does not need to specify the associated type — instance resolution computes it from the input type.
- **No coherence checking.** Lean does *not* verify that the association is a function. Declaring two instances with the same input and conflicting `outParam` outputs is accepted with no error and no warning; the solver silently commits to whichever one its search reaches first. Uniqueness is a discipline you maintain, not an invariant the compiler enforces.

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

1. **`outParam` vs type-valued field.** `outParam` on a class parameter makes the associated type a *class-level* association (one per type). A type-valued field of a plain `structure` makes it a *value-level* association — `s1.Row` and `s2.Row` can differ for two values of the same structure type. A type-valued field of a **`class`** is not value-level: `Container.Elem` takes the instance as an argument (`Container.Elem : (c : Type) → [Container c] → Type`), so it is still resolved per instance, i.e. per type, exactly like `outParam`.

2. **Uniqueness is your job.** Nothing stops you from writing two instances that give the same input type different `outParam` outputs — the file compiles clean and one of them silently wins (Example C). If a type genuinely needs several element types, use a regular (non-`outParam`) parameter and let the caller pin it down.

3. **Inference failures.** If the compiler cannot determine the `outParam` from context, you get "failed to synthesize." Provide a type annotation to help inference.

4. **No type member syntax.** Unlike Scala's `type Member = ...` inside a class body, Lean has no dedicated syntax for type members. The pattern is always "parameter with `outParam`" or "field of type `Type`."

5. **Where core actually uses `outParam`.** Not in class hierarchies — those are built with `extends`. `outParam` shows up in *heterogeneous* and *relational* classes, where one argument must be derived rather than searched for: `Membership (γ : outParam Type) (α : Type)`, `HAdd`/`HMul α β (γ : outParam Type)`, `GetElem coll idx (elem : outParam Type) (valid : outParam _)`, and `MonadState (σ : outParam Type) m`. `MonadLift` uses the weaker `semiOutParam`. Note `SMul α β` has no `outParam` at all — reach for it only when you really want the argument excluded from the search key.

## Beginner mental model

Think of `outParam` as a **lookup function**: given a container type, it looks up the element type. `Container (List Nat)` → `elem = Nat`. The lookup is automatic — you provide the container type, and the compiler finds the element type from the instance database. Type-valued fields are simpler: they are just fields that happen to hold a type instead of a value.

Coming from Rust: `outParam Type` ≈ `type Item;` in a trait. `Container (c : Type) (elem : outParam Type)` ≈ `trait Container { type Elem; }`. The syntactic difference (trait member vs. extra class parameter) is the cosmetic one. The difference that matters is **coherence**: Rust's orphan and overlap rules make `<Vec<u32> as Container>::Elem` a *provably* unique type, so `rustc` can reject any second impl. Lean has no such check — `outParam` only steers the search, so `Container.Elem` is unique exactly as far as you keep it unique.

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

## Example C — `outParam` does not enforce uniqueness

```lean
class Elem (c : Type) (e : outParam Type) where
  first : c → Option e

instance instNat : Elem (List Nat) Nat where
  first xs := xs.head?

-- Same input type, a different output type. Lean accepts this: no error,
-- no warning, no "ambiguous instance" diagnostic — the association is
-- simply no longer a function, and the solver commits to one of the two.
instance instStr : Elem (List Nat) String where
  first xs := xs.head?.map toString

#synth Elem (List Nat) _      -- reports the winner; the loser is never mentioned

def firstOf [Elem c e] (coll : c) : Option e := Elem.first coll

#check firstOf [1, 2, 3]      -- the element type comes from whichever instance won
```

The lesson: a passing build is not evidence that your `outParam` association is
single-valued. If you need that guarantee, you have to impose it yourself —
by convention, by keeping the instances in one place, or by not making the
parameter an `outParam` at all.

## Use-case cross-references

- [→ UC-04](../usecases/UC04-generic-constraints.md) — Associated types via `outParam` enable generic programming over containers with determined element types.
- [→ UC-02](../usecases/UC02-domain-modeling.md) — Type-valued fields model domain schemas where each entity has an associated data type.

## Source anchors

- *Functional Programming in Lean* — "Type Classes" (outParam)
- *Theorem Proving in Lean 4* — Ch. 10 "Type Classes" (multi-parameter classes)
- Lean 4 source: `Lean.Meta.SynthInstance` (outParam handling)
