# Callable Contracts

## The constraint

Express precise contracts on callable values -- dependent function types, higher-order functions, and automatic currying. Lean 4's type system tracks the relationship between a function's input and output types, so the compiler verifies contracts that go far beyond simple arity and type checks.

## Feature toolkit

- [-> T22-callable-typing](../catalog/T22-callable-typing.md) -- Function types, dependent function types, and automatic currying.
- [-> T09-dependent-types](../catalog/T09-dependent-types.md) -- Return types that depend on argument values.
- [-> T05-type-classes](../catalog/T05-type-classes.md) -- Type-class-constrained higher-order functions.
- [-> T04-generics-bounds](../catalog/T04-generics-bounds.md) -- Universe-polymorphic function types.

## Patterns

### Pattern A -- Higher-order functions

Functions are first-class values. Pass them, return them, and store them in data structures.

```lean
def applyTwice (f : Nat → Nat) (x : Nat) : Nat :=
  f (f x)

#eval applyTwice (· + 1) 0      -- 2
#eval applyTwice (· * 2) 3      -- 12

-- Functions as return values:
def adder (n : Nat) : Nat → Nat :=
  (· + n)

#eval (adder 10) 5               -- 15
```

### Pattern B -- Automatic currying

All multi-parameter functions are automatically curried. Partial application requires no special syntax.

```lean
def add (a b : Nat) : Nat := a + b

-- Partial application:
def add5 : Nat → Nat := add 5

#eval add5 3            -- 8
#eval List.map (add 10) [1, 2, 3]   -- [11, 12, 13]
```

### Pattern C -- Dependent function types

The return type can depend on the argument value. This is the core power of Lean's type system applied to callables.

```lean
-- The return type depends on the Bool argument:
def choose (b : Bool) : if b then Nat else String :=
  if b then 42 else "hello"

#eval choose true    -- 42 : Nat
#eval choose false   -- "hello" : String

-- Dependent function over Fin:
def index (xs : Array α) (i : Fin xs.size) : α :=
  xs[i]
-- The index is statically bounded — no out-of-bounds possible
```

### Pattern D -- Type-class-constrained callables

Constrain higher-order function parameters with type-class bounds.

```lean
def sortBy [Ord β] (f : α → β) (xs : List α) : List α :=
  xs.mergeSort (fun a b => compare (f a) (f b) == .lt)

-- The caller must provide a type with an Ord instance:
#eval sortBy (·.length) ["hello", "hi", "hey"]   -- ["hi", "hey", "hello"]

-- Works with any Ord:
#eval sortBy (fun p : Nat × Nat => p.1) [(3, 1), (1, 2), (2, 3)]
```

### Pattern E -- Anonymous function syntax

Lean supports multiple anonymous function styles for concise callable expressions.

```lean
-- Lambda with fun:
#eval List.map (fun x => x * 2) [1, 2, 3]   -- [2, 4, 6]

-- Placeholder syntax:
#eval List.map (· * 2) [1, 2, 3]             -- [2, 4, 6]

-- Pattern-matching lambda:
#eval List.map (fun | 0 => "zero" | _ => "nonzero") [0, 1, 2]
-- ["zero", "nonzero", "nonzero"]
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Higher-order functions | Universally applicable; composable | No special optimisation hints (but Lean's compiler is good) |
| Automatic currying | Seamless partial application | Every function is unary under the hood; can confuse newcomers |
| Dependent function types | Return type precision unmatched by any mainstream language | Type errors can be harder to read; requires more annotation |
| Type-class constraints | Reusable; caller chooses implementation | Instance resolution can fail with opaque error messages |

## When to use which feature

- **Simple callbacks and transformations** -> plain function types (`α -> β`) with higher-order combinators.
- **Partial application** -> just apply fewer arguments; currying is automatic.
- **Contracts that depend on values** (safe indexing, protocol states) -> dependent function types.
- **Polymorphic algorithms** (sort, compare, serialise) -> type-class-constrained parameters.

## Source anchors

- *Functional Programming in Lean* -- "Functions and Definitions", "Type Classes"
- *Theorem Proving in Lean 4* -- Ch. 2 "Dependent Type Theory"
