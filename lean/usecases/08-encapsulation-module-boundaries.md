# Encapsulation and Module Boundaries

## The constraint

Control what leaks across module boundaries. Internal implementation details should not be accessible to client code, while the public API remains typed and verifiable.

## Feature toolkit

- [→ catalog/15](../catalog/15-opaque-definitions.md) — `opaque` hides definition bodies from the kernel.
- [→ catalog/03](../catalog/03-structures-inheritance.md) — `private` constructors and fields restrict access.
- [→ catalog/16](../catalog/16-notation-attributes.md) — `@[irreducible]` controls unfolding; `scoped` limits attribute visibility.

## Patterns

### Pattern A — Private constructors via structure

```lean
structure Token where
  private mk ::
  value : String

namespace Token

def create (s : String) : Option Token :=
  if s.length > 0 then some (Token.mk s) else none

end Token

-- Outside the namespace:
-- Token.mk "hello"  -- error: 'Token.mk' is private
def t := Token.create "hello"  -- OK: goes through validation
```

### Pattern B — Opaque abstract types

```lean
-- In module `Internal`:
opaque Handle : Type
opaque Handle.open : String → IO Handle
opaque Handle.close : Handle → IO Unit

-- Client code can use Handle but cannot inspect its internals.
-- Changing the implementation doesn't break client code.
```

### Pattern C — @[irreducible] for controlled unfolding

```lean
@[irreducible] def hashPassword (pw : String) : UInt64 :=
  -- implementation hidden from simp and automatic unfolding
  pw.foldl (fun acc c => acc * 31 + c.toNat.toUInt64) 0

-- Proofs about hashPassword require explicit `unfold hashPassword`
-- or lemmas you provide — the implementation doesn't leak into client proofs
```

### Pattern D — Scoped instances and attributes

```lean
namespace MyLib

@[scoped simp] theorem internal_lemma : ∀ n, n + 0 = n := Nat.add_zero

scoped instance : ToString MyType where
  toString _ := "MyType"

end MyLib

-- Outside `open MyLib`, these don't pollute the global scope
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| `private` constructors | Simple; familiar access control | Only hides names, not structure shape |
| `opaque` | Complete abstraction; kernel can't unfold | Cannot `#eval` without `@[implemented_by]` |
| `@[irreducible]` | Softer barrier; can be overridden when needed | Not a hard boundary — `unfold` can pierce it |
| `scoped` | Prevents namespace pollution | Only effective with disciplined `open` usage |

## When to use which feature

- **Validated smart constructors** → `private` constructor + validation function.
- **True abstract data types** → `opaque` (strongest barrier).
- **Library internals that shouldn't leak into proofs** → `@[irreducible]`.
- **Module-local instances and simp lemmas** → `scoped`.

## Source anchors

- Lean 4 documentation: "Declarations" (private, protected)
- Lean 4 source: `Lean.Elab.Declaration` (opaque, private)
