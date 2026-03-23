---
description: Add a vibe-types quick index to a CLAUDE.md file for always-on type safety guidance
disable-model-invocation: true
argument-hint: "[language]"
---

# Install vibe-types context

This command adds a language-specific quick index snippet to a CLAUDE.md file so that type-safety guidance is always available in context.

## Steps

1. **Choose the language.** If `$ARGUMENTS` specifies a language, use it. Otherwise:
   - First, detect the project language by checking for signature files: `*.py` or `pyproject.toml` → Python, `Cargo.toml` or `*.rs` → Rust, `lakefile.lean` or `*.lean` → Lean 4, `build.sbt` or `build.sc` or `*.scala` → Scala 3.
   - Present the numbered menu below. If a language was detected, mark it as `(detected)` and make it the default. Accept just the number or Enter for the default.

```
Which language? [default: 2 — detected Rust project]
  1. Python
  2. Rust  (detected)
  3. Lean 4
  4. Scala 3
  5. All
```

2. **Choose the target file.** Present this numbered menu and accept just the number:

```
Where should the snippet go?
  1. ~/.claude/CLAUDE.md        (personal, all projects)
  2. .claude/CLAUDE.md          (project, version-controlled)
  3. .claude/CLAUDE.local.md    (project, gitignored)
  4. Custom path
```

If the user picks 4, ask for the path.

3. **Read the target file** (if it exists) to check whether the snippet is already present. Look for the marker `<!-- vibe-types:<lang> -->`. If found, tell the user it's already installed and ask whether to replace it.

4. **Append the snippet** to the end of the file (create it if it doesn't exist). Use the exact content below for each language, wrapped in the marker comments. Include a blank line before the marker.

5. **Confirm** what was added and where.

## Snippets

### Python
```
<!-- vibe-types:python -->
## Python type-safety quick index (vibe-types)
- Basic annotations & None handling: enforce types on params/returns; require None checks → `T13-null-safety`
- Union & Literal types: restrict values to declared alternatives; Literal for exact values → `T02-union-intersection`
- TypedDict: enforce dict key names, value types, and required/optional presence → `T31-record-types`
- Protocol (structural subtyping): static duck typing — verify method/attr presence without inheritance → `T07-structural-typing`
- Generics & TypeVar: preserve type relationships; bounds restrict acceptable types → `T04-generics-bounds`
- ParamSpec: preserve function signatures through decorators → `T45-paramspec-variadic`
- TypeGuard & TypeIs: custom narrowing functions; exhaustive branch handling → `T14-type-narrowing`
- Final & frozen dataclass: prevent reassignment, override, and mutation → `T32-immutability-markers`, `T06-derivation`
- Preventing invalid states: enums, Literal, NewType, Union — make invalid states unrepresentable → `UC01-invalid-states`
- Gradual adoption: add types incrementally; --strict mode; py.typed marker → `UC27-gradual-adoption`
<!-- /vibe-types:python -->
```

### Rust
```
<!-- vibe-types:rust -->
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
<!-- /vibe-types:rust -->
```

### Lean 4
```
<!-- vibe-types:lean -->
## Lean 4 type-safety quick index (vibe-types)
- Inductive types & pattern matching: closed variants with exhaustive matching → `T01-algebraic-data-types`
- Dependent types & Pi types: types depend on values; compiler checks index consistency → `T09-dependent-types`
- Propositions as types (Prop): encode invariants; compiler requires proof terms → `T29-propositions-as-types`
- Subtypes & refinement types: attach predicates to types; construction requires proof → `T26-refinement-types`
- Termination checking: every recursive function must provably terminate → `T28-termination`
- Type classes & instances: constrain generic code to types with required capabilities → `T05-type-classes`
- Monads & IO: side effects tracked in the type; pure code cannot perform IO → `T12-effect-tracking`
- Proof automation (simp, omega, decide): automate proof obligations at construction sites → `T30-proof-automation`
- Preventing invalid states: inductive types, subtypes, dependent types → `UC01-invalid-states`
- Domain modeling: model domain invariants as type-level constraints → `UC02-domain-modeling`
<!-- /vibe-types:lean -->
```

### Scala 3
```
<!-- vibe-types:scala3 -->
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
<!-- /vibe-types:scala3 -->
```
