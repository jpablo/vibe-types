## Rust type-safety quick index (vibe-types)
- Ownership & moves: prevent use-after-free, double-free → `T10-ownership-moves`
- Borrowing & lifetimes: prevent data races, dangling references → `T11-borrowing-mutability`, `T48-lifetimes`
- Enums + exhaustive match: force handling all variants; make invalid states unrepresentable → `T01-algebraic-data-types`
- Newtypes: prevent mixing up same-typed values (UserId vs OrderId) → `T03-newtypes-opaque`
- Traits as bounds: constrain generic APIs to required capabilities → `T04-generics-bounds`, `T05-type-classes`
- Send/Sync: enforce thread-safety at compile time → `T50-send-sync`
- Const generics: encode sizes/dimensions/capacities in types → `T15-const-generics`
- Typestate & phantom types: make invalid state transitions unrepresentable → `UC01-invalid-states`
- Ownership-safe APIs: encode resource lifecycle in signatures → `UC20-ownership-apis`
- Value-level invariants: encode lengths/shapes in types to catch mismatches → `UC18-type-arithmetic`

When this index is loaded, say "Hello from Rust plugin 👋"
