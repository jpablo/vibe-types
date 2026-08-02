# Coercions and Coe

> **Since:** Lean 4 (stable)

## What it is

Coercions in Lean are automatic type conversions inserted by the compiler when a value of type `α` appears where type `β` is expected, provided a `Coe α β` instance exists. Unlike implicit conversions in C++ or Scala 2 (which can be surprising and hard to track), Lean coercions are explicitly declared via type class instances and are visible in the elaborated term.

Lean provides several coercion classes: `Coe α β` for basic coercions, `CoeSort α β` for coercing to a `Sort` (type), `CoeFun α β` for coercing to a function type, and `CoeDep α (a : α) β` for coercions that may depend on the *value* being coerced (there is no `CoeHTCDep`). Around these sit the search-order classes `CoeHead`, `CoeOut`, `CoeTail`, and the driver `CoeT` that instance search actually goes through. The most common one to declare yourself is `Coe`.

## What constraint it enforces

**Automatic coercions only fire when a `Coe` instance is declared; the compiler rejects implicit conversions between types without an explicit coercion path.**

More specifically:

- **Declared, not implicit — for *your* types.** No conversion between two of your own types happens until you declare an instance. But core ships plenty of built-in silent conversions that need no user declaration: `Nat → Int` (via the `NatCast` class, inserting `Nat.cast`), `{ x : α // p x } → α` (via the `CoeOut` instance `subtypeCoe`, inserting `.val`), and a decidable `Prop` used where a `Bool` is expected (via `decPropToBool`, inserting `decide`).
- **Type-safe insertion.** The compiler inserts the coercion function call, so the resulting code is fully type-checked.
- **Transitive chaining.** Lean can chain multiple coercions (A → B → C), but the chain must resolve within a bounded search depth.
- **Hidden in output by default.** `pp.coercions` is **on** by default, and what it does is *hide* the coercion: you see `↑x`, not the function. Set `set_option pp.coercions false` to reveal which function was actually inserted.

## Minimal snippet

```lean
-- A *user-declared* coercion. This one really fires:
structure Meters where
  val : Float

instance : Coe Meters Float where
  coe m := m.val

def scale (x : Float) : Float := x * 2.0

def m : Meters := ⟨3.0⟩
#eval scale m                 -- 6.000000

-- `pp.coercions` defaults to true and HIDES the coercion (printing `↑m`).
-- Set it false to see the function that was actually inserted:
set_option pp.coercions false in
#check scale m                -- scale m.val : Float

-- Contrast: no coercion fires here at all.
def addInt (a b : Int) : Int := a + b
#eval addInt 3 5              -- 8
set_option pp.coercions false in
#check addInt 3 5             -- addInt (OfNat.ofNat 3) (OfNat.ofNat 5) : Int
```

The literals in `addInt 3 5` are *not* coerced `Nat`s — with `Int` as the expected
type they elaborate directly at `Int` via `OfNat Int`. (You can prove this to
yourself by declaring a deliberately wrong `Coe Nat Int`: the answer is still `8`.)
A real `Nat → Int` conversion, from a bound variable, goes through core's
`NatCast`, not through any `Coe` instance you write:

```lean
-- Core's built-in silent conversions — no user declaration anywhere:
def n : Nat := 3
def addInt (a b : Int) : Int := a + b
#eval addInt n n              -- 6   -- Nat → Int via `NatCast` (`Nat.cast`)

def p : { k : Nat // k > 0 } := ⟨5, by decide⟩
def dbl (k : Nat) : Nat := k * 2
#eval dbl p                   -- 10  -- Subtype → base via `CoeOut` instance `subtypeCoe`

def flag : Bool := 3 < 5      -- decidable Prop → Bool via `decPropToBool`
#eval flag                    -- true

set_option pp.coercions false in
#check (addInt n n, dbl p, (3 < 5 : Bool))
-- (addInt n.cast n.cast, dbl p.val, decide (3 < 5)) : Int × Nat × Bool
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Structures & extends** [→ T31](T31-record-types.md) | For **structures**, `extends` generates only the `toParent` projection — *no* `Coe` instance — so a child value is rejected where the parent is expected (see gotcha 6). For **type classes**, `extends` does register the parent as an instance (via the `toParent` projection, again not via `Coe`), which is why `[Derived α]` satisfies a `[Base α]` constraint. |
| **Subtypes** [→ T26](T26-refinement-types.md) | A default coercion from `{ x : α // P x }` to `α` is provided (extracting `.val`). |
| **Type Classes** [→ T05](T05-type-classes.md) | `Coe` is a type class. Declaring instances follows the same pattern as any other type class. |
| **Auto-Bound Implicits** [→ T38](T38-implicits-auto-bound.md) | Coercions interact with implicit argument resolution — the compiler tries coercions before reporting a type mismatch. |

## Gotchas and limitations

1. **Coercion chains can be surprising.** When multiple coercions compose (e.g., `PosNat → Nat → Int`), the code does two conversions silently. Use `set_option pp.coercions false` to see what's happening — the default (`true`) collapses the whole chain into a single `↑`.

2. **No coercion in pattern matching.** Coercions apply in expressions, not in patterns. You cannot match on a coerced value directly — match on the actual type and convert explicitly.

3. **Overlapping coercions resolve silently — there is no ambiguity error.** If two `Coe` instances could apply, Lean does **not** report a conflict; instance search simply takes the most recently declared one and moves on.

```lean
structure Wrap where
  v : Nat

instance : Coe Wrap Nat where coe w := w.v      -- the "obvious" one
instance : Coe Wrap Nat where coe _ := 999      -- declared later

def use (n : Nat) : Nat := n
#eval use (Wrap.mk 7)   -- 999, with no warning
```

This is easy to miss, and it is a pattern worth internalizing across this whole
catalog: where the docs would like to promise an ambiguity error, Lean usually
just picks a winner quietly (the same is true of overlapping scoped instances,
[→ T19](T19-extension-methods.md)). If you suspect it, print the elaborated term
with `set_option pp.coercions false` rather than expecting the compiler to warn you.

4. **Performance.** Coercions insert real function calls. For numeric types in tight loops, this could matter. Check the generated code if performance is critical.

5. **`CoeSort` and `CoeFun` are special.** `CoeSort` coerces a value to a type (used for "a set S can be used as a type"), and `CoeFun` coerces a value to a function (used for callable objects). These are less common but powerful.

6. **Structure `extends` gives you a projection, not a coercion.** `structure Dog extends Animal` generates `Dog.toAnimal` and lets dot notation reach parent fields — but it declares no `Coe Dog Animal`, so passing a `Dog` where an `Animal` is expected is a type error. Write `.toAnimal`, or declare the `Coe` instance yourself.

```lean
structure Animal where
  name : String
structure Dog extends Animal where
  breed : String

def speak (a : Animal) : String := a.name
def rex : Dog := { name := "Rex", breed := "lab" }

#eval speak rex.toAnimal   -- "Rex" -- the generated projection, used explicitly
#eval rex.name             -- "Rex" -- dot notation does walk the parent chain

-- but the child is not accepted where the parent is expected:
#eval speak rex
-- error: Application type mismatch: the argument rex has type Dog but is expected to have type Animal
```

## Beginner mental model

Think of coercions as **automatic adapter plugs**. If you have a `Coe Meters Float` adapter declared, any time you plug a `Meters` into a `Float` socket, the compiler inserts the adapter for you. No adapter declared — and none shipped by core for that pair — and the compiler rejects the connection. By default Lean *hides* the adapter when printing (you just see `↑`); `set_option pp.coercions false` takes the cover off and shows the actual function.

Coming from Rust: Lean coercions are similar to Rust's `Deref` coercions — `String` auto-coerces to `&str` because `Deref<Target = str>` is implemented. In Lean, `Coe A B` plays the same role but is more general.

## Example A — Subtype coercion

```lean
def PosNat := { n : Nat // n > 0 }

-- A subtype wrapped in a `def` is not coerced for free; declare the coercion.
instance : Coe PosNat Nat where
  coe p := p.val

def double (n : Nat) : Nat := n * 2

def doublePosNat (p : PosNat) : Nat :=
  double p  -- OK: the Coe PosNat Nat instance extracts p.val
```

## Example B — CoeFun for callable structures

```lean
structure Transform where
  f : Float → Float

instance : CoeFun Transform (fun _ => Float → Float) where
  coe t := t.f

def scale2 : Transform := { f := (· * 2.0) }

#eval scale2 3.14  -- OK: CoeFun makes Transform callable; prints 6.280000
```

(`Float`'s `Repr` instance always prints six decimal places, so the output is
`6.280000`, not `6.28`.)

## Common compiler errors and how to read them

### `Type mismatch` / `Application type mismatch` (no coercion)

```
Application type mismatch: The argument
  x
has type
  MyType
but is expected to have type
  OtherType
in the application
  f x
```

**Meaning:** No coercion path from `MyType` to `OtherType` exists. Either define a `Coe` instance or convert explicitly. In an ascription or a `def` body rather than an application, the same situation is reported as plain `Type mismatch`.

**There is no special "coercion failed" error.** A failed coercion is not announced as such — it degrades into an ordinary type mismatch, and messages like `maximum coercion depth reached` do not exist in Lean 4. Writing `↑x` explicitly does not change this either: you still get the same mismatch, not a `CoeT` synthesis complaint. If you expected a coercion and got a type mismatch, check that the instance exists (`#synth CoeT MyType x OtherType`) rather than looking for a dedicated diagnostic.

## Proof perspective (brief)

In the proof world, coercions enable smooth mathematical notation. Mathlib uses `CoeSort` extensively: a `Subgroup G` can be used as a type (the carrier set). `Coe ℕ ℤ` lets you write natural number literals in integer contexts without explicit casts. These coercions mirror mathematical conventions where embeddings (like ℕ ↪ ℤ) are applied silently. The `simp` tactic understands coercions and can simplify expressions involving them.

## Use-case cross-references

- [→ UC-02](../usecases/UC02-domain-modeling.md) — Coercions provide smooth conversions between domain types and their underlying representations.
- [→ UC-06](../usecases/UC04-generic-constraints.md) — Coercions participate in type class resolution, enabling flexible generic code.

## Source anchors

- *Functional Programming in Lean* — "Coercions"
- Lean 4 source: `Init.Coe` (`Coe`, `CoeSort`, `CoeFun`)
