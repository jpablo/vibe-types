# Generics & Bounded Polymorphism (via Type Classes and Universes)

> **Since:** Lean 4 (stable)

## What it is

Lean achieves generic programming through two complementary mechanisms:

- **Universe polymorphism** — Definitions can be parameterized over universe levels, making them work across all type levels. `def id {α : Sort u} (a : α) : α := a` works for types in any universe.
- **Type class instance arguments** — Written `[Ord α]`, these constrain generic type parameters to types that provide specific capabilities. This is Lean's equivalent of Rust's trait bounds or Scala's context bounds.

There is no separate "generics" syntax. A polymorphic function is simply a function with implicit type parameters: `def length {α : Type} (xs : List α) : Nat`. Adding type class constraints bounds the polymorphism: `def sort [Ord α] (xs : List α) : List α` requires `α` to have an ordering.

## What constraint it enforces

**Generic functions can only use operations available through their type class constraints; the compiler rejects calls where required instances are missing.**

More specifically:

- **Parametric polymorphism.** A function with an unconstrained `{α : Type}` parameter can only use operations that work for *all* types (e.g., identity, pairing). It cannot inspect the type.
- **Bounded polymorphism.** Adding `[Ord α]` allows the function to use ordering operations. The compiler checks at each call site that the concrete type provides the required instance.
- **Universe generality.** Universe-polymorphic definitions work across `Type 0`, `Type 1`, etc. The compiler infers universe levels in most cases.

## Minimal snippet

```lean
-- Parametric polymorphism: works for any type
def swap {α β : Type} (p : α × β) : β × α :=
  (p.2, p.1)

-- Bounded polymorphism: requires Ord instance
def maximum [Ord α] [Inhabited α] (xs : List α) : α :=
  xs.foldl (fun acc x => if compare x acc == .gt then x else acc) default

#eval maximum [3, 1, 4, 1, 5]   -- 5
-- #eval maximum [fun x => x]   -- error: failed to synthesize Ord (Nat → Nat)
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | Type class constraints are the primary bounding mechanism. `[Ord α]` is an instance-implicit argument resolved at each call site. |
| **Universes** [→ catalog/T35](T35-universes-kinds.md) | Universe polymorphism (`Sort u`) provides parametric generality across type levels. |
| **Implicits** [→ catalog/T38](T38-implicits-auto-bound.md) | `{α : Type}` is an implicit argument. Auto-bound implicits let you omit the `{α}` when the compiler can infer it. |
| **Dependent Types** [→ catalog/T09](T09-dependent-types.md) | Generics are a special case of dependent types. `{α : Type} → List α → Nat` is a Pi type where the return type doesn't depend on `α`. |
| **Derivation** [→ catalog/T06](T06-derivation.md) | `deriving Ord, BEq` generates instances that enable types to participate in bounded-polymorphic functions. |

## Gotchas and limitations

1. **No variance annotations.** Lean does not have Scala-style `+T`/`-T` variance. Type constructors are invariant. Covariance and contravariance must be established through explicit coercions or proofs.

2. **Instance resolution, not syntactic bounds.** Unlike Rust's `T: Ord + Clone`, Lean's constraints are instance-implicit arguments: `[Ord α] [Clone α]`. They look different but serve the same purpose.

3. **Universe unification can fail.** Mixing types from different universes (e.g., `Prop` and `Type`) requires care. The error "universe level mismatch" usually means you need explicit universe annotations.

4. **Implicit argument ordering.** When a function has both implicit type parameters and instance parameters, the order matters for partial application. Lean convention: implicit types first, then instances.

5. **No wildcard bounds.** There is no `? extends T` (Java) or `_ <: T` (Scala). Lean's constraints are always named type variables with specific class requirements.

## Beginner mental model

Think of type class constraints as **requirements on a job posting**. The function says "I need a type that can do X and Y" (the constraints). When you call the function with a specific type, the compiler checks your type's resume (instances) against the requirements. If something is missing, you get a compile error — not a runtime failure.

Coming from Rust: `[Ord α]` ≈ `T: Ord`. `{α : Type}` ≈ `<T>`. The main differences: Lean has no explicit `where` clause syntax (constraints go inline), and no associated types (use `outParam` or structure fields instead).

## Example A — Constrained generic with multiple bounds

```lean
def dedup [BEq α] [Hashable α] (xs : List α) : List α :=
  let seen := xs.foldl (fun (s : Std.HashSet α) x => s.insert x) {}
  seen.toList

#eval dedup [1, 2, 3, 2, 1]   -- [1, 2, 3] (order may vary)
```

## Example B — Universe-polymorphic definition

```lean
universe u

def pair {α : Type u} (a b : α) : List α :=
  [a, b]

-- Works for Type 0 (data types)
#check pair 1 2                   -- List Nat

-- Works for Type 1 (type-level)
#check pair Nat Int               -- List Type
```

## Use-case cross-references

- [→ UC-04](../usecases/UC04-generic-constraints.md) — Type class constraints ensure generic code only uses available capabilities.
- [→ UC-02](../usecases/UC02-domain-modeling.md) — Bounded polymorphism models domain abstractions with required operations.

## Source anchors

- *Functional Programming in Lean* — "Polymorphism" and "Type Classes"
- *Theorem Proving in Lean 4* — Ch. 2 "Dependent Type Theory" (implicit arguments)
- Lean 4 source: `Lean.Elab.Term` (implicit argument elaboration)
