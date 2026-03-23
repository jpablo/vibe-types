# Recursive Types

> **Since:** Lean 4 (stable)

## What it is

In Lean, recursive types are defined via **inductive types** -- the same mechanism that defines all algebraic data types. An inductive type is recursive when one or more of its constructors takes an argument of the type being defined. `inductive List (α : Type) | nil | cons : α → List α → List α` defines a list where `cons` contains another `List α`.

Lean's kernel includes a **termination checker** that ensures all functions over recursive types terminate. Structural recursion (recursing on a strict subterm of the input) is accepted automatically. More complex recursion patterns require explicit `termination_by` annotations or well-founded recursion proofs.

Because Lean is a theorem prover, recursive types also serve as the foundation for **inductive proofs**: a proof by induction on `Nat` or `List` follows the same recursive structure as the type definition.

## What constraint it enforces

**Inductive types must satisfy the strict positivity condition: the type being defined can only appear in strictly positive positions in constructor arguments. Functions over inductive types must be proven terminating.**

- **Strict positivity** prevents unsound recursive types (e.g., `inductive Bad | mk : (Bad → Bool) → Bad` is rejected because `Bad` appears in a negative position).
- **Termination checking** ensures all recursive functions over inductive types produce a result or a valid proof. Non-terminating functions are rejected unless marked `partial`.
- **Universe constraints** ensure recursive types do not violate the type hierarchy.

## Minimal snippet

```lean
inductive Tree (α : Type) where
  | leaf : α → Tree α
  | branch : Tree α → Tree α → Tree α

def Tree.depth : Tree α → Nat
  | .leaf _       => 0
  | .branch l r   => 1 + max l.depth r.depth

def example := Tree.branch (Tree.leaf 1) (Tree.branch (Tree.leaf 2) (Tree.leaf 3))
#eval example.depth   -- 2
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **ADTs / Inductive types** [-> catalog/T01](T01-algebraic-data-types.md) | Recursive types ARE inductive types. Every inductive type in Lean is potentially recursive; non-recursive types are the degenerate case. |
| **Dependent types** [-> catalog/T09](T09-dependent-types.md) | Indexed inductive families combine recursion with dependent typing: `inductive Vec (α : Type) : Nat → Type` tracks the length in the type while being recursively defined. |
| **Termination checking** [-> catalog/T28](T28-termination.md) | The termination checker ensures recursive functions over inductive types always halt. Structural recursion is automatic; complex patterns need `termination_by` or `decreasing_by`. |
| **Propositions as types** [-> catalog/T29](T29-propositions-as-types.md) | Induction on recursive types IS proof by induction. Proving a property for all `List α` means handling `nil` and showing the property transfers through `cons`. |
| **Pattern matching** [-> catalog/T14](T14-type-narrowing.md) | Lean's equation compiler generates match expressions for recursive function definitions, ensuring completeness and enabling the termination checker. |

## Gotchas and limitations

1. **Strict positivity is strict.** `inductive T | mk : (T → Bool) → T` is rejected. This prevents defining types that would make the logic inconsistent. Workarounds include using an index or restructuring the type.

2. **Termination proofs can be tedious.** While structural recursion is automatic, functions like `mergeSort` require proving that recursive calls operate on smaller inputs. `termination_by` with `omega` or custom measures helps, but complex cases require manual proofs.

3. **No coinductive types (natively).** Lean does not have built-in coinductive types for infinite structures. Corecursive definitions (infinite streams, infinite trees) must be encoded using `partial` functions, `IO` monad, or external libraries. The `Lean.Elab.Deriving` module provides some support.

4. **Large inductive types.** Types with many constructors or deeply nested recursion can slow down the kernel. The equation compiler generates match/recursor applications that grow with the number of cases.

5. **Nested recursion requires auxiliary types.** `inductive RoseTree | node : List RoseTree → RoseTree` involves nested recursion through `List`. Lean handles this but generates auxiliary types internally, and pattern matching on nested recursive types can require extra lemmas.

## Beginner mental model

Think of an inductive type as a set of **building instructions**. `List` says: "You can build a list by starting with `nil` (empty), or by taking an existing list and prepending a value with `cons`." Every list is built from these two instructions, applied a finite number of times. The termination checker ensures your functions follow the building instructions in reverse -- peeling off one layer at a time until reaching `nil`.

Coming from Rust: Lean's inductive types are like Rust's enums, but you never need `Box` because Lean manages memory automatically. The tradeoff is that Lean additionally requires your functions to terminate.

## Example A -- Natural number arithmetic as structural recursion

```lean
-- Nat is itself a recursive type: inductive Nat | zero | succ : Nat → Nat
def add : Nat → Nat → Nat
  | n, .zero   => n
  | n, .succ m => .succ (add n m)

-- Lean verifies termination: the second argument decreases structurally
#eval add 3 4   -- 7

-- Proof by induction follows the same recursive structure
theorem add_zero (n : Nat) : add n 0 = n := by
  rfl   -- follows directly from the first equation
```

## Example B -- Mutually recursive types

```lean
mutual
  inductive Expr where
    | num  : Int → Expr
    | add  : Expr → Expr → Expr
    | block : List Stmt → Expr → Expr

  inductive Stmt where
    | assign : String → Expr → Stmt
    | print  : Expr → Stmt
end

mutual
  def Expr.eval (env : List (String × Int)) : Expr → Int
    | .num n     => n
    | .add a b   => a.eval env + b.eval env
    | .block stmts body =>
      let env' := stmts.foldl (fun e s => s.exec e) env
      body.eval env'

  def Stmt.exec (env : List (String × Int)) : Stmt → List (String × Int)
    | .assign name expr => (name, expr.eval env) :: env
    | .print expr => dbg_trace s!"{expr.eval env}"; env
end
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Inductive types with strict positivity ensure only well-formed recursive structures can be constructed.
- [-> UC-02](../usecases/UC02-domain-modeling.md) -- Recursive domain models (trees, expressions, nested configurations) are naturally expressed as inductive types.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Inductive types with type parameters propagate constraints recursively, ensuring every node in a `Tree α` satisfies the constraint on `α`.

## Source anchors

- *Theorem Proving in Lean 4* -- Ch. 7 "Inductive Types"
- *Functional Programming in Lean* -- "Inductive Types" and "Recursive Functions"
- Lean 4 source: `Lean.Elab.Inductive` -- inductive type elaboration
- Lean 4 source: `Lean.Elab.PreDefinition.Structural` -- structural recursion checker
