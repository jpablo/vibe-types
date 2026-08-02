# Extension Methods (Not a First-Class Feature)

> **Since:** Lean 4 (stable)

## What it is

Lean does not have a dedicated `extension` keyword or extension method syntax like Scala 3 or Kotlin. Instead, similar functionality is achieved through several mechanisms:

- **Namespace dot notation.** If a function is defined in a type's namespace (e.g., `Nat.isEven`), it can be called with dot notation: `n.isEven`. This works for any type — you simply define the function in the appropriate namespace.
- **Type class instances.** Defining a new type class instance for an existing type adds new capabilities that can be used via type class dispatch.
- **`open ... in`** — Brings names from a namespace into scope, enabling unqualified access.
- **Scoped instances.** `scoped instance` defines a type class instance visible only within the current namespace, simulating locally-available extension methods.

The key insight: Lean's dot notation is based on **namespace lookup**, not method tables. If `List.myHelper` exists and `xs : List α`, then `xs.myHelper` works automatically.

## What constraint it enforces

**Dot notation resolves by namespace lookup; functions must be in the correct namespace to be callable with dot syntax. Scoped instances limit the visibility of new capabilities.**

More specifically:

- **Namespace-based dispatch.** `x.foo` looks up `TypeOfX.foo`. If the function exists in that namespace, the call succeeds. No registration or annotation is needed.
- **No implicit extension.** Unlike Scala 3, there is no implicit conversion to an "extension carrier." The function must literally be in the type's namespace.
- **Scoped visibility.** `scoped instance` and `open ... in` control when extended capabilities are visible, preventing global namespace pollution.

## Minimal snippet

```lean
-- "Extension method" via namespace
def List.second? (xs : List α) : Option α :=
  xs.drop 1 |>.head?

#eval [1, 2, 3].second?   -- some 2
#eval ([] : List Nat).second?  -- none
```

```lean
-- Adding capabilities via scoped instance
namespace MyModule
  scoped instance : ToString Nat where
    toString n := s!"#{n}"
end MyModule

open MyModule in
#eval toString (42 : Nat)   -- "#42" (scoped instance active)
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | New type class instances add method-like capabilities. Scoped instances limit their reach. |
| **Structures** [→ catalog/T31](T31-record-types.md) | Dot notation on structures accesses fields and namespace functions uniformly. |
| **Coercions** [→ catalog/T18](T18-conversions-coercions.md) | `Coe` instances enable implicit conversion, which can simulate extension-method-like ergonomics. |
| **Encapsulation** [→ catalog/T21](T21-encapsulation.md) | `open` controls what names are in scope. `protected` definitions require full qualification. |
| **Macros** [→ catalog/T17](T17-macros-metaprogramming.md) | Custom notation and macros can simulate extension-like syntax for domain-specific operations. |

## Gotchas and limitations

1. **Namespace must match.** `def List.foo ...` puts `foo` in the `List` namespace. If you accidentally define it at the wrong level, dot notation won't find it.

2. **No multi-dispatch — and the receiver is not necessarily the first parameter.** `x.foo` looks up `T.foo` where `T` is the head of `x`'s type, then passes `x` as the first *explicit* argument whose type also has head `T`. Earlier parameters of other types are left to be given at the call site. There is no multi-method dispatch; for dispatch on several arguments, use type classes.

```lean
-- the `List String` parameter is second, but it is still the receiver
def List.tagAll (sep : String) (xs : List String) : String :=
  sep.intercalate xs

#eval ["a", "b", "c"].tagAll "-"   -- "a-b-c" -- the receiver filled `xs`, not `sep`
```

3. **Fields and namespace functions cannot collide.** The situation "a field `foo` and also a function `S.foo`" cannot arise: the field projection *is* the declaration `S.foo`, so a later `def S.foo` is rejected outright rather than shadowed.

```lean
structure S where
  foo : Nat

def S.foo (s : S) : Nat := 99
-- error: invalid declaration name `foo`, structure `S` has field `foo`
```

4. **Scoped instances conflict silently.** Opening two namespaces with competing scoped instances produces **no** ambiguity error — the most recently opened (or highest-priority) one quietly wins, and swapping the order in `open` swaps the result. Use `instance (priority := ...)` to make the winner deliberate rather than incidental. This mirrors the same "silently picks, never complains" behaviour that overlapping `Coe` instances have [→ T18](T18-conversions-coercions.md).

```lean
namespace Hash
  scoped instance : ToString Nat where toString n := s!"#{n}"
end Hash
namespace Star
  scoped instance : ToString Nat where toString n := s!"*{n}"
end Star

open Hash Star in
#eval toString (42 : Nat)   -- "*42" -- Star opened last, Star wins

open Star Hash in
#eval toString (42 : Nat)   -- "#42" -- order reversed, so is the answer
```

5. **You *do* need the import — but not `open`.** Unlike Kotlin, where an extension function must be imported *by name* to be callable, in Lean the requirement runs the other way round: you must `import` the module that defines the function (nothing is visible without it), but once imported, dot notation needs neither `open` nor qualification. `xs.myHelper` resolves through the namespace of `xs`'s type on its own.

```lean
import Std.Data.HashMap

-- `Std.HashMap.size` is reachable by dot notation with no `open Std` and
-- no qualification. Without the import, even `Std.HashMap` is an unknown identifier.
def m : Std.HashMap Nat String := (∅ : Std.HashMap Nat String).insert 1 "one"
#eval m.size   -- 1
```

## Beginner mental model

Think of Lean's namespaces as **filing cabinets labeled by type**. When you write `xs.length` on a `List`, Lean looks in the `List` filing cabinet for a function called `length`. You can add new functions to any filing cabinet by defining them in the right namespace. There is no special "extension" mechanism — you just put the function in the right drawer.

Coming from Kotlin/C#: `fun List<T>.second()` → `def List.second? ...`. The dot-notation call looks the same, but the mechanism is namespace lookup rather than extension method dispatch. Coming from Rust: Lean's approach is more like defining functions in `impl` blocks — functions in `List` namespace are callable via `list.function`.

## Example A — Extending Array with a helper

```lean
-- `Array.sum` already ships in core, so add a distinct method name.
def Array.total [Add α] [OfNat α 0] (xs : Array α) : α :=
  xs.foldl (· + ·) 0

#eval #[1, 2, 3, 4].total   -- 10
```

## Example B — Scoped type class extension

```lean
namespace Scientific
  scoped instance : Repr Float where
    reprPrec f _ := s!"{f}f"
end Scientific

-- Outside Scientific: default Repr for Float
-- Inside Scientific: custom representation
open Scientific in
#eval repr (3.14 : Float)   -- uses scoped instance
```

## Use-case cross-references

- [→ UC-04](../usecases/UC04-generic-constraints.md) — Type class instances extend types with new capabilities for generic functions.
- [→ UC-10](../usecases/UC10-encapsulation.md) — Scoped instances control the visibility of extended functionality.

## Source anchors

- *Functional Programming in Lean* — "Structures" (dot notation)
- *Theorem Proving in Lean 4* — Ch. 6 "Interacting with Lean" (namespaces, open)
- Lean 4 source: `Lean.Elab.App` (dot notation resolution)
