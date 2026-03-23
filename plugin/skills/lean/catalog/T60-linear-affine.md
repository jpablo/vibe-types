# Linear and Affine Types (Not Supported -- GC)

> **Since:** N/A; Lean 4 uses reference counting with runtime optimizations

## What it is

Lean does **not** have linear or affine types in its type system. Values can be freely aliased, passed to multiple functions, and stored in multiple data structures. Memory is managed through **reference counting** rather than a garbage collector or ownership system.

However, Lean's runtime performs a key optimization: when the reference count of a value is exactly 1, destructive updates are performed in-place rather than copying. This achieves **linear-like performance** without requiring the programmer to manage ownership at the type level. The compiler and runtime collaborate to make "last use" optimizations automatic.

This means Lean gets many of the performance benefits of linear types (avoiding unnecessary copies, in-place mutation of unique references) while keeping the programming model simple -- values behave as if they are always immutable and freely copyable.

## What constraint it enforces

**Lean does not enforce single-use or linear constraints at the type level. Any value can be used zero or more times without restriction.**

The runtime optimizations provide:
- **Automatic in-place updates** when refcount = 1 (the value has a single owner).
- **Transparent copying** when refcount > 1 (the value is shared).
- **Deterministic deallocation** via reference counting (no GC pauses).

## Minimal snippet

```lean
-- Values can be freely aliased — no move semantics
def example : List Nat :=
  let xs := [1, 2, 3]
  let ys := xs          -- xs is still valid
  let zs := xs          -- xs can be used again
  xs ++ ys ++ zs        -- all three are usable

-- In-place optimization: when xs has refcount 1, append mutates in-place
def buildList (n : Nat) : List Nat :=
  let mut xs : List Nat := []
  for i in [:n] do
    xs := xs ++ [i]     -- optimized to in-place append when xs is unique
  xs
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Inductive types** [-> catalog/T01](T01-algebraic-data-types.md) | Inductive values are reference-counted. Pattern matching on a unique reference can destructure in-place. Shared references cause a copy before pattern matching modifies the structure. |
| **Encapsulation** [-> catalog/T21](T21-encapsulation.md) | Without linear types, encapsulation relies on `private`/`protected` and opaque definitions to control how values are used, not on ownership transfer. |
| **Totality checking** [-> catalog/T51](T51-totality.md) | Totality ensures all functions terminate, but does not track resource usage. A function can use its argument zero times (ignoring it) without type error. |
| **Proof automation** [-> catalog/T30](T30-proof-automation.md) | Proof terms in `Prop` are erased at runtime and have no reference counting overhead. Only `Type`-universe values participate in reference counting. |
| **Dependent types** [-> catalog/T09](T09-dependent-types.md) | Dependent types in Lean are orthogonal to linearity. You can encode "used exactly once" as a proposition, but the runtime does not enforce it -- it is a proof obligation, not a type-system restriction. |

## Gotchas and limitations

1. **No compile-time uniqueness guarantee.** Unlike Rust, Lean cannot prove at compile time that a value has a single reference. The refcount=1 optimization is a runtime property. Code that accidentally aliases a large structure will silently copy instead of updating in-place.

2. **Performance cliffs.** Adding a seemingly innocent `let y := xs` before mutating `xs` bumps the refcount to 2, causing a full copy. Profiling is needed to detect these hidden copies in performance-sensitive code.

3. **No resource management discipline.** File handles, sockets, and other external resources are not tracked by the type system. Lean programs must manually close resources or use wrapper patterns similar to Scala's `Using`.

4. **`@[inline]` and fusion affect uniqueness.** Compiler optimizations can change whether a value is unique at a given point. The performance of in-place updates depends on optimization decisions that are not visible in the source code.

5. **No `Drop`-like protocol.** Lean has no equivalent of Rust's `Drop` trait or Python's `__del__`. When a value's refcount reaches zero, its memory is freed, but there is no user-defined cleanup hook for non-memory resources.

## Beginner mental model

Think of Lean's approach as a **library with smart photocopiers**. When you hand your only copy of a book to the librarian for editing, they edit it directly (in-place update, refcount=1). When you hand a book you have shared with others, the librarian photocopies it first and edits the copy (copy-on-write, refcount>1). You never need to think about this -- the library handles it automatically. The tradeoff is that you cannot *guarantee* in-place editing at the type level; you just trust the library to be efficient.

Coming from Rust: Lean's approach is the dual of ownership. Rust forces you to think about uniqueness and rewards you with guaranteed zero-cost moves. Lean frees you from thinking about uniqueness and relies on runtime refcounting to achieve similar performance when references happen to be unique.

## Example A -- Reference counting optimization in practice

```lean
-- Array update: O(1) when unique, O(n) when shared
def incrementAll (xs : Array Nat) : Array Nat :=
  xs.map (· + 1)

-- Unique path — in-place update (fast)
def fast : Array Nat :=
  let xs := #[1, 2, 3]
  incrementAll xs          -- xs is unique → modified in-place

-- Shared path — copies (slower)
def slow : Array Nat × Array Nat :=
  let xs := #[1, 2, 3]
  let ys := xs             -- refcount bumped to 2
  (incrementAll xs, ys)    -- xs is shared → copy before modifying
```

## Example B -- do-notation with mutable variables

```lean
-- Lean's `do` notation with `let mut` compiles to efficient
-- reference-counted updates, achieving imperative performance
def sumArray (xs : Array Nat) : Nat := do
  let mut total := 0
  for x in xs do
    total := total + x
  return total

-- The `total` variable is not truly mutable — each update creates
-- a new binding. But refcount optimization makes this O(n), not O(n²).
#eval sumArray #[10, 20, 30]   -- 60
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Without linear types, Lean prevents invalid states through dependent types and proof obligations rather than ownership discipline.
- [-> UC-02](../usecases/UC02-domain-modeling.md) -- Domain models in Lean use algebraic types and invariants encoded as proofs, not resource-tracking types.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Generic constraints in Lean use type classes and propositions, not linearity bounds.

## Source anchors

- *Functional Programming in Lean* -- "Arrays and Indexing" (reference counting discussion)
- Ullrich & de Moura, "Counting Immutable Beans" (2019) -- Lean's reference counting semantics
- Lean 4 source: `Lean.Runtime` -- reference counting implementation
- de Moura & Ullrich, "The Lean 4 Theorem Prover and Programming Language" (2021)
