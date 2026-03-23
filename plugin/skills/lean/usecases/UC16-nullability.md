# Nullability

## The constraint

Lean 4 has no `null` value. Absence is represented by `Option α`, which forces every consumer to handle the "nothing here" case explicitly. The compiler rejects code that uses an `Option` value without matching on it or unwrapping it through a combinator.

## Feature toolkit

- [-> T13-null-safety](../catalog/T13-null-safety.md) -- `Option α` as the sole mechanism for optional values; no null pointer.
- [-> T01-algebraic-data-types](../catalog/T01-algebraic-data-types.md) -- `Option` is an inductive type with `none` and `some`; exhaustive matching enforced.
- [-> T05-type-classes](../catalog/T05-type-classes.md) -- `Option` has `Monad`, `Alternative`, `BEq`, and other instances.

## Patterns

### Pattern A -- Option for explicit absence

Use `Option α` wherever a value might not exist. The type system makes absence visible.

```lean
def findUser (id : Nat) : Option String :=
  if id == 42 then some "Alice" else none

-- Caller must handle both cases:
def greet (id : Nat) : String :=
  match findUser id with
  | some name => s!"Hello, {name}!"
  | none      => "User not found"

#eval greet 42    -- "Hello, Alice!"
#eval greet 99    -- "User not found"
```

### Pattern B -- Pattern matching for safe unwrapping

Pattern matching is the primary way to work with `Option`. The compiler rejects incomplete matches.

```lean
def firstPositive (xs : List Int) : Option Int :=
  xs.find? (· > 0)

def report (xs : List Int) : String :=
  match firstPositive xs with
  | some n => s!"found: {n}"
  | none   => "no positive numbers"
  -- removing either branch is a compile error

#eval report [(-1), (-2), 3, 4]   -- "found: 3"
#eval report [(-1), (-2)]         -- "no positive numbers"
```

### Pattern C -- Monadic combinators with do notation

`Option` is a `Monad`. Use `do` notation to chain optional computations; any `none` short-circuits the entire block.

```lean
def parseInt (s : String) : Option Int :=
  s.toInt?

def addStrings (a b : String) : Option Int := do
  let x ← parseInt a
  let y ← parseInt b
  return x + y

#eval addStrings "10" "20"    -- some 30
#eval addStrings "10" "abc"   -- none (short-circuits at parseInt b)
```

### Pattern D -- getD and map for concise defaults

Use `.getD` for a default value and `.map` for transforming the inner value without unwrapping.

```lean
def lookup (key : String) (store : List (String × Nat)) : Option Nat :=
  store.lookup key

-- Default value:
#eval (lookup "a" [("a", 1), ("b", 2)]).getD 0   -- 1
#eval (lookup "c" [("a", 1), ("b", 2)]).getD 0   -- 0

-- Map over the contents:
#eval (some 5).map (· * 2)    -- some 10
#eval (none : Option Nat).map (· * 2)   -- none
```

### Pattern E -- Option.guard and filtering

Use `Option.guard` and `.filter` to conditionally produce or keep values.

```lean
-- guard: produce some () if condition holds, else none
def validateAge (age : Nat) : Option Nat := do
  Option.guard (age >= 18)
  return age

#eval validateAge 20   -- some 20
#eval validateAge 15   -- none

-- filter: keep the value only if a predicate holds
#eval (some 10).filter (· > 5)    -- some 10
#eval (some 3).filter (· > 5)     -- none
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Pattern matching | Most explicit; compiler-enforced exhaustiveness | Verbose for simple cases |
| Monadic `do` notation | Concise chaining; short-circuits on `none` | Less visible where the `none` originates |
| `.getD` / `.map` | One-liners for common patterns | Default may hide a bug if absence is unexpected |
| `.guard` / `.filter` | Clean conditional construction | Loses information about why the condition failed |

## When to use which feature

- **Always start with `Option`** for any value that might be absent. There is no alternative in Lean.
- **Pattern matching** when you need to handle presence and absence differently with non-trivial logic.
- **Monadic `do`** when chaining multiple optional steps -- parsing pipelines, multi-step lookups.
- **`.getD`** when a sensible default exists and absence is not an error.
- **`Except` instead of `Option`** when the caller needs to know *why* the value is missing ([-> UC08-error-handling](UC08-error-handling.md)).

## Source anchors

- *Functional Programming in Lean* -- "Polymorphism", "Monads"
- Lean 4 source: `Init.Prelude` (`Option`), `Init.Data.Option.Basic`
