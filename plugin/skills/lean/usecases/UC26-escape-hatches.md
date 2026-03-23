# Interop and Escape Hatches

## The constraint

`sorry`, `partial`, `unsafe`, and FFI provide controlled exits from Lean's safety guarantees. Each has a known scope, and the compiler marks where guarantees are weakened.

## Feature toolkit

- [→ T51-totality](../catalog/T51-totality.md) — `partial` opts out of termination checking.

## Patterns

### Pattern A — sorry for development placeholders

```lean
def complexAlgorithm (xs : List Nat) : List Nat :=
  sorry  -- fills any hole; compiler warns "uses 'sorry'"

-- The compiler emits: declaration 'complexAlgorithm' uses 'sorry'
-- This marks the definition as unsound — replace before production
```

### Pattern B — partial for non-terminating computations

```lean
partial def eventLoop (state : AppState) : IO Unit := do
  let event ← waitForEvent
  let newState := handleEvent state event
  eventLoop newState
-- `partial` is correct here: the loop is intentionally infinite
-- Restriction: cannot use eventLoop in proofs
```

### Pattern C — unsafe for raw pointer operations

```lean
unsafe def castPtr (p : @& ByteArray) : UInt64 :=
  unsafeCast p  -- bypasses type safety entirely

-- `unsafe` functions can only be called from other `unsafe` functions
-- or via @[implemented_by] to back an opaque definition
```

### Pattern D — FFI with @[extern]

```lean
@[extern "lean_io_prim_println"]
opaque println : String → IO Unit

-- The implementation is in C/C++. The Lean compiler trusts the
-- type signature. If the C code doesn't match, behavior is undefined.
```

### Pattern E — Combining escape hatches responsibly

```lean
-- Pattern: unsafe C FFI backing an opaque Lean definition
@[extern "my_fast_sort"]
opaque fastSort (xs : @& Array Nat) : Array Nat

-- Client code sees: fastSort : Array Nat → Array Nat
-- The opaque type is safe to use; the unsafe implementation is hidden
-- You can add a theorem about fastSort's behavior (proved via sorry
-- during development, replaced with a proof later)
```

## Tradeoffs

| Escape hatch | What it bypasses | Scope of taint | When to use |
|-------------|-----------------|----------------|-------------|
| `sorry` | Any proof obligation | Definition marked as using sorry | Development placeholders; TDD-style workflow |
| `partial` | Termination checking | Cannot be used in proofs | Servers, REPLs, event loops |
| `unsafe` | Type safety | Callable only from `unsafe` or `@[implemented_by]` | FFI, low-level optimization |
| `@[extern]` / FFI | Lean type checker (trusts C code) | Runtime UB if types don't match | Interop with C/C++ libraries |

## When to use which feature

- **Incremental development** → `sorry` as a placeholder, replace before shipping.
- **Non-terminating processes** → `partial`.
- **Performance-critical code with C interop** → `unsafe` + `@[extern]` behind `opaque`.
- **Never** → `sorry` in production, `unsafe` without `opaque` wrapper.

## Source anchors

- *Functional Programming in Lean* — "Partial Functions", "FFI"
- Lean 4 documentation: "FFI" reference
- Lean 4 source: `Lean.Elab.PreDefinition.Partial`, `Init.Prelude` (`sorry`)
