# Newtypes, Abbrev, and Opaque Wrappers

> **Since:** Lean 4 (stable)

## What it is

Lean provides several mechanisms for creating type-level distinctions over existing types. A **single-field structure** acts as a newtype: it wraps an existing type in a distinct named type, preventing accidental mixing. `abbrev` creates a *transparent* alias that the type checker always unfolds. `opaque` creates a definition whose body is completely hidden outside its module. Private constructors (using `private`) restrict who can construct a value.

Together these tools let you control the boundary between "same representation" and "distinct type" — from fully transparent aliases to fully opaque abstractions.

## What constraint it enforces

**Single-field structures create nominally distinct types that cannot be used interchangeably; the compiler rejects mixing the wrapper with the underlying type.**

More specifically:

- **Nominal separation.** A `structure Meters where val : Float` is a different type from `Float`. Passing a raw `Float` where `Meters` is expected is a compile error.
- **Transparent aliases.** An `abbrev` is always unfolded by the kernel — it provides no type-level distinction, only a shorter name.
- **Opaque hiding.** An `opaque` definition prevents the kernel from seeing the body entirely. Downstream code cannot depend on the implementation.
- **Private constructors.** Marking a structure constructor `private` prevents other modules from constructing values directly, enforcing smart-constructor patterns.

## Minimal snippet

```lean
structure Meters where
  val : Float

structure Seconds where
  val : Float

def speed (d : Meters) (t : Seconds) : Float :=
  d.val / t.val

-- #eval speed ⟨100.0⟩ ⟨100.0⟩   -- error: expected Meters, got anonymous constructor
#eval speed { val := 100.0 : Meters } { val := 10.0 : Seconds }  -- OK
```

Attempting to pass a `Seconds` as `Meters`:

```lean
def wrong (s : Seconds) : Float := speed s s
-- error: type mismatch, expected Meters, got Seconds
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Structures** [→ catalog/T31](T31-record-types.md) | Single-field structures are the primary newtype mechanism. They support `deriving` and dot notation. |
| **Type Classes** [→ catalog/T05](T05-type-classes.md) | Newtypes can derive or implement different type class instances than the wrapped type, enabling distinct behavior. |
| **Encapsulation** [→ catalog/T21](T21-encapsulation.md) | `opaque` and `private` work together with the module system to hide implementation details. |
| **Type Aliases** [→ catalog/T23](T23-type-aliases.md) | `abbrev` is the transparent end of the spectrum; newtypes are the opaque end. |
| **Coercions** [→ catalog/T18](T18-conversions-coercions.md) | A `Coe Meters Float` instance can make unwrapping ergonomic when desired. |

## Gotchas and limitations

1. **No zero-cost guarantee in all cases.** While a single-field structure has the same runtime representation as the wrapped type in most compiled code, the Lean runtime may box structures in some contexts. This is an implementation detail, not a language guarantee.

2. **`abbrev` provides no protection.** An `abbrev UserId := Nat` is completely interchangeable with `Nat`. If you want type safety, use a `structure`.

3. **`opaque` is very strong.** An `opaque` definition cannot be unfolded even by tactics. If you need controlled unfolding, use `@[irreducible]` instead.

4. **Deriving for newtypes.** You must derive or manually provide instances for each newtype. There is no automatic "derive via underlying type" mechanism (unlike Haskell's `GeneralizedNewtypeDeriving`).

## Beginner mental model

Think of a newtype as a **labeled envelope**. The value inside is the same, but the label on the envelope matters — you cannot put a "Meters" envelope where a "Seconds" envelope is expected. `abbrev` is a sticky note that says "this is just another name" — no envelope at all. `opaque` is a sealed, unmarked box — nobody can look inside.

Coming from Rust: `structure Meters where val : Float` ≈ `struct Meters(f64)`. `abbrev` ≈ `type Alias = ...`. `opaque` has no direct Rust analog — it is stronger than `pub struct` with private fields.

## Example A — Smart constructor with private

```lean
structure Percentage where
  private mk ::
  val : Float

def Percentage.new (f : Float) : Option Percentage :=
  if 0.0 ≤ f ∧ f ≤ 100.0 then some ⟨f⟩ else none

-- Outside this module:
-- def bad : Percentage := Percentage.mk 200.0
-- error: 'Percentage.mk' is private
```

## Example B — Abbrev vs structure

```lean
abbrev Name := String    -- transparent alias, no type safety

structure Email where
  raw : String           -- nominally distinct from String

def sendTo (e : Email) : IO Unit :=
  IO.println s!"Sending to {e.raw}"

-- sendTo "alice@example.com"  -- error: expected Email, got String
#eval sendTo { raw := "alice@example.com" }  -- OK
```

## Use-case cross-references

- [→ UC-01](../usecases/UC01-invalid-states.md) — Newtypes prevent mixing semantically different values.
- [→ UC-02](../usecases/UC02-domain-modeling.md) — Domain types wrap primitives for safety.
- [→ UC-10](../usecases/UC10-encapsulation.md) — Opaque definitions hide implementation.

## Source anchors

- *Functional Programming in Lean* — "Structures"
- *Theorem Proving in Lean 4* — Ch. 6 "Structures and Records"
- Lean 4 source: `Lean.Elab.Structure`
