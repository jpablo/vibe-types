# Type Narrowing via Dependent Pattern Matching

> **Since:** Lean 4 (stable)

## What it is

When you pattern match on an inductive value in Lean, the type checker *narrows* the types in each branch to reflect what the matched constructor reveals. If you match on a `List α` and land in the `x :: xs` branch, the compiler knows the list is non-empty. With dependent types, this narrowing is even more powerful: matching a length-indexed `Vec α n` on `.nil` tells the compiler that `n` *is* `0` for the rest of that branch, and matching on `.cons` tells it that `n` is `m + 1` for the tail's length `m` — the index in the type is rewritten, not just the value.

This is not a special "narrowing" feature — it is a natural consequence of dependent pattern matching. The match's *motive* (return type) can depend on the matched value, and each branch gets a specialized version of the motive with the constructor's arguments substituted in.

## What constraint it enforces

**Pattern matching on inductive types refines type information per branch; the compiler rejects code that uses pre-narrowing types inside a branch. Exhaustiveness is mandatory — the compiler rejects incomplete matches.**

More specifically:

- **Branch-local type refinement.** In each branch of a `match`, type parameters are specialized to match the constructor. Code that would be ill-typed before the match becomes well-typed inside the correct branch.
- **Exhaustiveness.** Every constructor must be covered. The compiler provides an explicit list of missing cases on failure.
- **Dependent narrowing.** When the scrutinee's type is indexed (e.g., `Vector α n`), matching on constructors refines the index (`n`) in each branch.

## Minimal snippet

```lean
inductive Shape where
  | circle (radius : Float)
  | rect (w h : Float)

def area : Shape → Float
  | .circle r => 3.141592653589793 * r * r   -- r : Float available
  | .rect w h => w * h                        -- w, h : Float available
```

Dependent narrowing with indexed types:

```lean
-- A length-indexed vector: the length lives in the type
inductive Vec (α : Type) : Nat → Type where
  | nil  : Vec α 0
  | cons : α → Vec α n → Vec α (n + 1)

def tail {α : Type} : {n : Nat} → Vec α (n + 1) → Vec α n
  | _, .cons _ xs => xs   -- matching .cons proves the input has ≥ 1 element;
                          -- the .nil case is impossible (its index is 0, not n+1)
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Inductive Types** [→ catalog/T01](T01-algebraic-data-types.md) | Narrowing is driven by the constructor set of an inductive. Each constructor defines what information becomes available in its branch. |
| **Dependent Types** [→ catalog/T09](T09-dependent-types.md) | Indexed families get the most powerful narrowing: matching a `Vec α n` refines the index `n` per branch (`0` under `.nil`, `m + 1` under `.cons`). Note that this needs a genuine *index* — `Fin n` is a single-constructor structure whose `n` is a *parameter*, so matching a `Fin (n+1)` yields one branch and refines nothing. |
| **Null Safety** [→ catalog/T13](T13-null-safety.md) | Matching `Option α` narrows to `some x` (value available) or `none` (no value). |
| **Propositions as Types** [→ catalog/T29](T29-propositions-as-types.md) | Matching on proof terms (e.g., `Or P Q`) narrows which disjunct holds in each branch. |
| **Refinement Types** [→ catalog/T26](T26-refinement-types.md) | Subtypes carry proofs; matching can refine both the value and the proof. |

## Gotchas and limitations

1. **Motive inference.** When the return type depends on the matched value, the compiler must infer a *motive*. Sometimes inference fails with "motive is not type correct." You may need to provide an explicit `(motive := ...)`.

2. **No *implicit* flow typing.** Unlike TypeScript, a plain `if x < 5 then … else …` tells the elaborator nothing: the branches are typed identically and `x < 5` is not usable as a fact. Lean's answer is the **dependent `if`**, `if h : c then … else …` — an ordinary *term*-level construct usable anywhere (not tied to `do`-notation), available whenever `c` has a `Decidable` instance. It binds `h : c` in the `then` branch and `h : ¬c` in the `else` branch — `h` is a proof of the condition itself, not of decidability; the `Decidable` instance is only what makes the term elaborate. So condition-driven refinement does exist outside `match`; what Lean lacks is TypeScript's *implicit* version:

   ```lean
   def firstOrZero (xs : List Nat) : Nat :=
     if h : 0 < xs.length then xs[0]   -- h : 0 < xs.length discharges the bounds proof
     else 0                            -- here h : ¬ (0 < xs.length)

   #eval firstOrZero [7, 8]   -- 7
   #eval firstOrZero []       -- 0
   ```

3. **Inaccessible patterns.** In dependent matches, some patterns are forced by other patterns. These are written as `.(expr)` and cannot be freely chosen.

4. **Generalization.** Sometimes you need to generalize variables before matching to get proper narrowing. The `match` generalization syntax or `intro` / `revert` in tactic mode handles this.

## Beginner mental model

Think of pattern matching as **opening a labeled envelope and learning what is inside**. Each label (constructor) tells you exactly what data you have. The compiler ensures you open every possible label, and inside each branch, you get access to the right data at the right type. With dependent types, the label itself carries information that refines the types of everything else in scope.

Coming from Rust: this works like `match` on an `enum`, where each arm destructures the variant's fields. Lean extends this so that type *parameters* (not just values) can be refined per arm.

## Example A — Narrowing with proof terms

Matching a *proof* refines types too. `Eq` is a `Prop`, but it supports elimination into
`Type`, so matching `h : n = m` against the `rfl` pattern rewrites `n` to `m` throughout
the branch — which is exactly what lets a `Vec α n` be accepted where a `Vec α m` is
wanted:

```lean
inductive Vec (α : Type) : Nat → Type where
  | nil  : Vec α 0
  | cons : α → Vec α n → Vec α (n + 1)

def Vec.castLen {α : Type} {n m : Nat} (h : n = m) (v : Vec α n) : Vec α m :=
  match m, h with
  | _, rfl => v           -- inside this branch the index `m` *is* `n`

def Vec.length {α : Type} : {n : Nat} → Vec α n → Nat
  | 0,     .nil       => 0                -- index narrowed to 0
  | _ + 1, .cons _ xs => 1 + length xs    -- index narrowed to a successor

#eval Vec.length (Vec.cons 1 (Vec.cons 2 Vec.nil))   -- 2
```

## Example B — Exhaustiveness enforcement

```lean
inductive Color where
  | red | green | blue

def toHex : Color → String
  | .red   => "#FF0000"
  | .green => "#00FF00"
  -- error: missing cases: `Color.blue`
```

Adding `.blue` makes it compile. If a new constructor is added to `Color` later, all downstream matches break — the compiler forces you to handle it.

## Use-case cross-references

- [→ UC-01](../usecases/UC01-invalid-states.md) — Narrowing ensures only valid states are reachable in each branch.
- [→ UC-03](../usecases/UC03-exhaustiveness.md) — Exhaustive matching guarantees every case is handled.
- [→ UC-02](../usecases/UC02-domain-modeling.md) — Dependent narrowing refines domain constraints per branch.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 8 "Induction and Recursion" (dependent match)
- *Functional Programming in Lean* — "Pattern Matching"
- Lean 4 source: `Lean.Elab.Match`
