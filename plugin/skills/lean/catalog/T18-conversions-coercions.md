# Coercions and Coe

> **Since:** Lean 4 (stable)

## What it is

Coercions in Lean are automatic type conversions inserted by the compiler when a value of type `α` appears where type `β` is expected, provided a `Coe α β` instance exists. Unlike implicit conversions in C++ or Scala 2 (which can be surprising and hard to track), Lean coercions are explicitly declared via type class instances and are visible in the elaborated term.

Lean provides several coercion classes: `Coe α β` for basic coercions, `CoeSort α β` for coercing to a `Sort` (type), `CoeFun α β` for coercing to a function type, and `CoeHTCDep` for dependent coercions. The most common is `Coe`, which handles cases like subtype-to-base-type, structure-to-parent, and numeric widening.

## What constraint it enforces

**Automatic coercions only fire when a `Coe` instance is declared; the compiler rejects implicit conversions between types without an explicit coercion path.**

More specifically:

- **Declared, not implicit.** You must define a `Coe` instance for the conversion to happen. There are no built-in silent conversions.
- **Type-safe insertion.** The compiler inserts the coercion function call, so the resulting code is fully type-checked.
- **Transitive chaining.** Lean can chain multiple coercions (A → B → C), but the chain must resolve within a bounded search depth.
- **Visible in output.** `set_option pp.coercions true` shows where coercions are inserted, aiding debugging.

## Minimal snippet

```lean
instance : Coe Nat Int where
  coe := Int.ofNat

def addInt (a b : Int) : Int := a + b

#eval addInt 3 5  -- OK: Nat 3 and 5 are coerced to Int automatically
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Structures & extends** [→ catalog/03] | `extends` generates `Coe` instances automatically from child to parent. |
| **Subtypes** [→ catalog/14] | A default coercion from `{ x : α // P x }` to `α` is provided (extracting `.val`). |
| **Type Classes** [→ catalog/04] | `Coe` is a type class. Declaring instances follows the same pattern as any other type class. |
| **Auto-Bound Implicits** [→ catalog/11] | Coercions interact with implicit argument resolution — the compiler tries coercions before reporting a type mismatch. |

## Gotchas and limitations

1. **Coercion chains can be surprising.** When multiple coercions compose (e.g., `PosNat → Nat → Int`), the code does two conversions silently. Use `set_option pp.coercions true` to see what's happening.

2. **No coercion in pattern matching.** Coercions apply in expressions, not in patterns. You cannot match on a coerced value directly — match on the actual type and convert explicitly.

3. **Ambiguous coercions.** If multiple `Coe` instances could apply, the compiler reports an ambiguity. Use explicit conversion to disambiguate.

4. **Performance.** Coercions insert real function calls. For numeric types in tight loops, this could matter. Check the generated code if performance is critical.

5. **`CoeSort` and `CoeFun` are special.** `CoeSort` coerces a value to a type (used for "a set S can be used as a type"), and `CoeFun` coerces a value to a function (used for callable objects). These are less common but powerful.

## Beginner mental model

Think of coercions as **automatic adapter plugs**. If you have a `Coe Nat Int` adapter declared, any time you plug a `Nat` into an `Int` socket, the compiler inserts the adapter for you. No adapter declared? The compiler rejects the connection. You can always see which adapters are being used by turning on coercion printing.

Coming from Rust: Lean coercions are similar to Rust's `Deref` coercions — `String` auto-coerces to `&str` because `Deref<Target = str>` is implemented. In Lean, `Coe A B` plays the same role but is more general.

## Example A — Subtype coercion

```lean
def PosNat := { n : Nat // n > 0 }

def double (n : Nat) : Nat := n * 2

def doublePosNat (p : PosNat) : Nat :=
  double p  -- OK: Coe PosNat Nat is automatic (extracts p.val)
```

## Example B — CoeFun for callable structures

```lean
structure Transform where
  f : Float → Float

instance : CoeFun Transform (fun _ => Float → Float) where
  coe t := t.f

def scale2 : Transform := { f := (· * 2.0) }

#eval scale2 3.14  -- OK: CoeFun makes Transform callable; prints 6.28
```

## Common compiler errors and how to read them

### `type mismatch` (no coercion)

```
type mismatch
  x
has type
  MyType : Type
but is expected to have type
  OtherType : Type
```

**Meaning:** No `Coe MyType OtherType` instance exists. Either define one or convert explicitly.

### `maximum coercion depth reached`

```
maximum coercion depth reached
```

**Meaning:** The compiler tried chaining coercions but hit the depth limit. Simplify the coercion chain or provide a direct `Coe` instance.

## Proof perspective (brief)

In the proof world, coercions enable smooth mathematical notation. Mathlib uses `CoeSort` extensively: a `Subgroup G` can be used as a type (the carrier set). `Coe ℕ ℤ` lets you write natural number literals in integer contexts without explicit casts. These coercions mirror mathematical conventions where embeddings (like ℕ ↪ ℤ) are applied silently. The `simp` tactic understands coercions and can simplify expressions involving them.

## Use-case cross-references

- [→ UC-02](../usecases/UC02-domain-modeling.md) — Coercions provide smooth conversions between domain types and their underlying representations.
- [→ UC-06](../usecases/UC04-generic-constraints.md) — Coercions participate in type class resolution, enabling flexible generic code.

## Source anchors

- *Functional Programming in Lean* — "Coercions"
- Lean 4 source: `Init.Coe` (`Coe`, `CoeSort`, `CoeFun`)
