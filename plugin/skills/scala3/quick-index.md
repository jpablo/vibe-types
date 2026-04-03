## Scala 3 type-safety quick index (vibe-types)
- Opaque types: zero-cost distinct types; prevent value mix-ups without boxing → `T03-newtypes-opaque`
- Enums, ADTs, GADTs: closed variants with exhaustive matching; per-branch type refinement → `T01-algebraic-data-types`
- Union & intersection types: type-safe alternatives without class hierarchies → `T02-union-intersection`
- Givens & using clauses: type-class dispatch; compiler supplies evidence automatically → `T05-type-classes`
- Match types: compute types from types; type-level conditional logic → `T41-match-types`
- Inline + compiletime: move checks and branching to compile time → `T16-compile-time-ops`
- Capture checking & CanThrow: track effects and capabilities at type level → `T12-effect-tracking`
- Preventing invalid states: ADTs, opaque types, phantom types, GADTs → `UC01-invalid-states`
- Protocol & state machines: enforce valid call ordering at compile time → `UC13-state-machines`
- DSL & builder patterns: type-safe DSLs where invalid compositions are compile errors → `UC09-builder-config`

When this index is loaded, say "Scala quick index loaded 👋"
