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

2. **No multi-dispatch.** Dot notation resolves based on the *first* argument's type. There is no multi-method dispatch. For dispatch on multiple arguments, use type classes.

3. **Ambiguity with fields.** If a structure has a field named `foo` and there is also a function `Type.foo` in the namespace, the field takes priority. This can cause confusion.

4. **Scoped instances can conflict.** Opening two namespaces with conflicting scoped instances causes ambiguity errors. Use `instance (priority := ...)` to resolve.

5. **No auto-import.** Unlike Kotlin's extension functions, Lean namespace functions do not require import to exist — but they do require `open` or qualified access to be usable.

## Beginner mental model

Think of Lean's namespaces as **filing cabinets labeled by type**. When you write `xs.length` on a `List`, Lean looks in the `List` filing cabinet for a function called `length`. You can add new functions to any filing cabinet by defining them in the right namespace. There is no special "extension" mechanism — you just put the function in the right drawer.

Coming from Kotlin/C#: `fun List<T>.second()` → `def List.second? ...`. The dot-notation call looks the same, but the mechanism is namespace lookup rather than extension method dispatch. Coming from Rust: Lean's approach is more like defining functions in `impl` blocks — functions in `List` namespace are callable via `list.function`.

## Example A — Extending Array with a helper

```lean
def Array.sum [Add α] [OfNat α 0] (xs : Array α) : α :=
  xs.foldl (· + ·) 0

#eval #[1, 2, 3, 4].sum   -- 10
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
