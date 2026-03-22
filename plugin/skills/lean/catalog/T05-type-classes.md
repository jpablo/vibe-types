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
-- #eval welcome (42 : Nat)                -- error: failed to synthesize Greet Nat
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Structures** [→ catalog/03] | Type classes *are* structures with `class`. Instances are structure values. `extends` creates a class hierarchy. |
| **Auto-Bound Implicits** [→ catalog/11] | `[inst : C α]` is an instance-implicit argument. The compiler fills it in via resolution. |
| **Coercions** [→ catalog/10] | `Coe α β` is a type class. Declaring a `Coe` instance enables automatic coercion. |
| **Monads** [→ catalog/09] | `Monad`, `Functor`, `Applicative` are type classes. Do-notation requires a `Monad` instance. |
| **Universes** [→ catalog/05] | Type classes can be universe-polymorphic. `outParam` controls universe inference in multi-parameter classes. |

## Gotchas and limitations

1. **Instance search can be slow.** With many instances (especially in Mathlib), resolution can take noticeable time. Use `set_option synthInstance.maxHeartbeats` to control the limit, or provide instances explicitly with `@`.

2. **No orphan rules.** Unlike Rust, Lean does not prevent defining instances for types you don't own. This is powerful but risky — conflicting instances cause ambiguity. Use `scoped instance` to limit an instance's visibility to the current namespace.

3. **Default methods.** Type classes can have default implementations. If you don't override them in your instance, the default is used. But defaults that call other class methods can create subtle loops if not careful.

4. **`outParam` and functional dependencies.** Multi-parameter type classes often need `outParam` to guide inference. Without it, the compiler may not be able to determine all type parameters from the call site.

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

structure Point2D where x : Float; y : Float

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
  xs.foldl Monoid.op Monoid.e
```

## Common compiler errors and how to read them

### `failed to synthesize instance`

```
failed to synthesize instance
  Greet Nat
```

**Meaning:** No instance of `Greet` exists for `Nat`. Either define one or change the type.

### `maximum class-instance resolution depth reached`

```
maximum class-instance resolution depth reached
```

**Meaning:** Instance search is looping or too deep. You likely have circular instances or an excessively deep class hierarchy. Simplify or provide the instance explicitly.

### `ambiguous, possible interpretations`

```
ambiguous, possible interpretations
```

**Meaning:** Multiple instances match and the compiler can't choose. Use `@` to provide the instance explicitly, or use `scoped instance` to limit visibility.

## Proof perspective (brief)

In the proof world, type classes organize mathematical structures. `Group α` is a type class asserting that `α` has a group operation, identity, and inverses satisfying the group axioms. Instance resolution is the mechanism by which Lean automatically infers that, say, `ℤ` is a group when needed in a proof. Mathlib's `Mathlib.Algebra.Group.Basic` is built entirely on type class inheritance: `CommMonoid extends Monoid extends Semigroup`, and so on. This lets proofs compose: a theorem about `Monoid` applies to any `Group` via the inheritance coercion.

## Use-case cross-references

- [→ UC-06](../usecases/UC04-generic-constraints.md) — Constrain generic code to types with required capabilities.

## Source anchors

- *Functional Programming in Lean* — "Type Classes"
- *Theorem Proving in Lean 4* — Ch. 10 "Type Classes"
- Lean 4 source: `Lean.Elab.Instance`
