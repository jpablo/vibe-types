# Type Classes and Instance Resolution

> **Since:** Lean 4 (stable)

## What it is

Type classes in Lean are structures annotated with the `class` keyword. They define an interface — a set of operations and properties — that types can implement by providing `instance` declarations. When a function requires a type class constraint (e.g., `[Add α]`), the compiler searches for a matching instance automatically via *instance resolution*. If no instance exists, the code fails to compile.

This is Lean's mechanism for ad-hoc polymorphism — the same operator (`+`, `*`, `<`) works on different types because each type provides its own instance. Type classes are also the backbone of Lean's mathematical hierarchy (Mathlib builds `Group`, `Ring`, `Field`, etc. as type classes) and are used pervasively for `ToString`, `Repr`, `BEq`, `Hashable`, `Monad`, and more.

## What constraint it enforces

**Generic functions can only use operations for which the compiler can find a type class instance; missing instances are compile errors.**

More specifically:

- **Capability requirements.** A constraint `[Add α]` means "type `α` must support addition." The compiler rejects calls where `α` lacks the required instance.
- **Automatic resolution.** The compiler searches the instance database at each call site. You don't pass instances manually (though you can with `@` for explicit arguments).
- **Coherence by convention.** Lean does not enforce global instance uniqueness (unlike Rust's orphan rules), but convention and `scoped instance` help avoid conflicts.

## Minimal snippet

```lean
class Greet (α : Type) where
  greet : α → String

structure User where name : String

instance : Greet User where
  greet u := s!"Hello, {u.name}!"

def welcome [Greet α] (x : α) : String := Greet.greet x

#eval welcome { name := "Alice" : User }  -- OK: instance found
#eval welcome (42 : Nat)
-- error: failed to synthesize instance of type class `Greet Nat`
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Structures** [→ T31](T31-record-types.md) | Type classes *are* structures with `class`. Instances are structure values. `extends` creates a class hierarchy. |
| **Auto-Bound Implicits** [→ T38](T38-implicits-auto-bound.md) | `[inst : C α]` is an instance-implicit argument. The compiler fills it in via resolution. |
| **Coercions** [→ T18](T18-conversions-coercions.md) | `Coe α β` is a type class. Declaring a `Coe` instance enables automatic coercion. |
| **Monads** [→ T12](T12-effect-tracking.md) | `Monad`, `Functor`, `Applicative` are type classes. Do-notation requires a `Monad` instance. |
| **Universes** [→ T35](T35-universes-kinds.md) | Type classes can be universe-polymorphic: a class declared over `{α : Sort u}` works at every level, and Lean infers the level at each instance site. (`outParam` is unrelated to universes — see gotcha 4.) |

## Gotchas and limitations

1. **Instance search can be slow.** With many instances (especially in Mathlib), resolution can take noticeable time. Use `set_option synthInstance.maxHeartbeats` to control the limit, or provide instances explicitly with `@`.

2. **No orphan rules — and no ambiguity error either.** Unlike Rust, Lean does not prevent defining instances for types you don't own. This is powerful but risky, and the risk is *not* an ambiguity error: overlapping instances happily coexist, and synthesis just picks one — by priority (default `1000`) and, among equal priorities, the **last declared instance wins** — silently. So merely importing a module can change which instance your code uses, with no diagnostic at all. Use `scoped instance` or `local instance` to limit visibility, `instance (priority := ...)` to make the choice deliberate, and `#synth C α` to see which instance was actually selected.

3. **Default methods.** Type classes can have default implementations. If you don't override them in your instance, the default is used. But defaults that call other class methods can create subtle loops if not careful.

4. **`outParam` and functional dependencies.** Multi-parameter type classes often need `outParam` to guide inference. Marking a parameter `outParam` declares it an *output* of instance resolution: synthesis ignores it when matching and lets the chosen instance determine it (functional-dependency style). Without it, the compiler may not be able to determine all type parameters from the call site.

5. **`deriving` is limited.** Not all type classes support `deriving`. For complex classes (like `Monad`), you must write the instance manually.

## Beginner mental model

Think of a type class as a **plug-in interface**. The class declaration says "any type that supports these operations can participate." Each `instance` declaration plugs a specific type into the interface. When you write a generic function with `[Add α]`, you're saying "this function works for any type with an Add plug-in." The compiler checks that the plug-in exists and wires it in automatically.

Coming from Rust: `class` ≈ `trait`, `instance` ≈ `impl`, `[Add α]` ≈ `T: Add`. The key difference: Lean has no orphan rules, and instance resolution is more flexible (but also less predictable).

## Example A — Numeric type class

```lean
class Metric (α : Type) where
  distance : α → α → Float

instance : Metric Float where
  distance a b := Float.abs (a - b)

structure Point2D where
  x : Float
  y : Float

instance : Metric Point2D where
  distance a b :=
    Float.sqrt ((a.x - b.x)^2 + (a.y - b.y)^2)

def isClose [Metric α] (a b : α) (ε : Float) : Bool :=
  Metric.distance a b < ε  -- OK: works for Float and Point2D
```

## Example B — Class hierarchy with extends

```lean
class Semigroup (α : Type) where
  op : α → α → α

class Monoid (α : Type) extends Semigroup α where
  e : α

instance : Monoid Nat where
  op := Nat.add
  e := 0

def fold [Monoid α] (xs : List α) : α :=
  xs.foldl Semigroup.op Monoid.e
```

## Common compiler errors and how to read them

### `failed to synthesize instance of type class`

```
error(lean.synthInstanceFailed): failed to synthesize instance of type class
  Greet Nat

Hint: Type class instance resolution failures can be inspected with the
`set_option trace.Meta.synthInstance true` command.
```

**Meaning:** No instance of `Greet` exists for `Nat`. Either define one or change the type. If the reported goal contains metavariables (`Greet ?m`), the real problem is upstream: the type was never pinned down, so annotate it and re-read the error.

### ``(deterministic) timeout at `typeclass` ``

```
failed to synthesize
  Loopy Nat
(deterministic) timeout at `typeclass`, maximum number of heartbeats (20000) has been reached

Note: Use `set_option synthInstance.maxHeartbeats <num>` to set the limit.
```

**Meaning:** Instance search is looping or too deep. You likely have circular instances (an instance whose own hypothesis re-triggers itself, e.g. `instance [Loopy (α × α)] : Loopy α`) or an excessively deep class hierarchy. Simplify or provide the instance explicitly. Note there is no "maximum class-instance resolution depth reached" error in Lean 4 — that is Lean 3 phrasing; a runaway search shows up as this heartbeat timeout.

### There is no "ambiguous instance" error

Lean never reports an ambiguity from instance synthesis. When two instances match the same goal they simply coexist, and the search silently picks one — the higher priority, or the **last declared** among equals:

```lean
class Greet (α : Type) where
  greet : α → String

structure User where
  name : String

instance instFriendly : Greet User where
  greet u := s!"Hello, {u.name}!"

instance instTerse : Greet User where
  greet u := s!"HI {u.name}"

#eval Greet.greet { name := "Alice" : User }  -- "HI Alice" — the later instance won
#synth Greet User                             -- instTerse
```

**Meaning:** this silent shadowing is the genuine hazard of having no orphan rule (contrast [→ T25](T25-coherence-orphan.md)): an import can change your program's behaviour without a single diagnostic. Diagnose with `#synth C α` or `set_option trace.Meta.synthInstance true`; control it with `instance (priority := ...)`, `scoped`/`local instance`, or by passing the instance explicitly with `@`. If you *have* seen `ambiguous, possible interpretations`, that comes from overloaded identifiers or notation, not from `synthInstance`.

## Proof perspective (brief)

In the proof world, type classes organize mathematical structures. `Group α` is a type class asserting that `α` has a group operation, identity, and inverses satisfying the group axioms. Instance resolution is the mechanism by which Lean automatically infers that, say, `ℤ` is a group when needed in a proof. Mathlib's `Mathlib.Algebra.Group.Basic` is built entirely on type class inheritance: `CommMonoid extends Monoid extends Semigroup`, and so on. This lets proofs compose: a theorem about `Monoid` applies to any `Group` via the inheritance coercion.

## Coming from Scala

Lean's `class`/`instance` corresponds to Scala 3's `given`/`using` and `trait` pattern. Where Scala writes `trait Ord[A]` with `given Ord[Int]`, Lean writes `class Ord (α : Type)` with `instance : Ord Nat`. Key differences: Lean's instance arguments `[Ord α]` are searched automatically (like Scala's `using`), but Lean's type classes can also carry proofs as data — the class `Decidable p` has constructors `isTrue : p → Decidable p` and `isFalse : ¬p → Decidable p`, so an instance *is* a decision procedure that hands back a proof either way. This has no Scala equivalent. (`DecidableEq` is not itself a class: it is the reducible abbreviation `@[reducible] def DecidableEq (α : Sort u) := (a b : α) → Decidable (a = b)`, with no `decEq` field. Writing `[DecidableEq α]` works because it unfolds to a function returning the `Decidable` class.)

## Use-case cross-references

- [→ UC-06](../usecases/UC04-generic-constraints.md) — Constrain generic code to types with required capabilities.

## Source anchors

- *Functional Programming in Lean* — "Type Classes"
- *Theorem Proving in Lean 4* — Ch. 10 "Type Classes"
- Lean 4 source: `Lean.Elab.Instance`
