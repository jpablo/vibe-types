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
- Basic annotations & None handling: enforce types on params/returns; require None checks → `python/catalog/01`
- Union & Literal types: restrict values to declared alternatives; Literal for exact values → `python/catalog/02`
- TypedDict: enforce dict key names, value types, and required/optional presence → `python/catalog/03`
- Protocol (structural subtyping): static duck typing — verify method/attr presence without inheritance → `python/catalog/09`
- Generics & TypeVar: preserve type relationships; bounds restrict acceptable types → `python/catalog/07`
- ParamSpec: preserve function signatures through decorators → `python/catalog/08`
- TypeGuard & TypeIs: custom narrowing functions; exhaustive branch handling → `python/catalog/13`
- Final & frozen dataclass: prevent reassignment, override, and mutation → `python/catalog/12`, `python/catalog/06`
- Preventing invalid states: enums, Literal, NewType, Union — make invalid states unrepresentable → `python/usecases/01`
- Gradual adoption: add types incrementally; --strict mode; py.typed marker → `python/usecases/12`
<!-- /vibe-types:python -->
```

### Rust
```
<!-- vibe-types:rust -->
## Rust type-safety quick index (vibe-types)
- Ownership & moves: prevent use-after-free, double-free → `rust/catalog/01`
- Borrowing & lifetimes: prevent data races, dangling references → `rust/catalog/02`, `rust/catalog/03`
- Enums + exhaustive match: force handling all variants; make invalid states unrepresentable → `rust/catalog/04`
- Newtypes: prevent mixing up same-typed values (UserId vs OrderId) → `rust/catalog/04`
- Traits as bounds: constrain generic APIs to required capabilities → `rust/catalog/05`, `rust/catalog/06`
- Send/Sync: enforce thread-safety at compile time → `rust/catalog/11`
- Const generics: encode sizes/dimensions/capacities in types → `rust/catalog/12`
- Typestate & phantom types: make invalid state transitions unrepresentable → `rust/usecases/01`
- Ownership-safe APIs: encode resource lifecycle in signatures → `rust/usecases/02`
- Value-level invariants: encode lengths/shapes in types to catch mismatches → `rust/usecases/08`
<!-- /vibe-types:rust -->
```

### Lean 4
```
<!-- vibe-types:lean -->
## Lean 4 type-safety quick index (vibe-types)
- Inductive types & pattern matching: closed variants with exhaustive matching → `lean/catalog/01`
- Dependent types & Pi types: types depend on values; compiler checks index consistency → `lean/catalog/02`
- Propositions as types (Prop): encode invariants; compiler requires proof terms → `lean/catalog/06`
- Subtypes & refinement types: attach predicates to types; construction requires proof → `lean/catalog/14`
- Termination checking: every recursive function must provably terminate → `lean/catalog/07`
- Type classes & instances: constrain generic code to types with required capabilities → `lean/catalog/04`
- Monads & IO: side effects tracked in the type; pure code cannot perform IO → `lean/catalog/09`
- Proof automation (simp, omega, decide): automate proof obligations at construction sites → `lean/catalog/13`
- Preventing invalid states: inductive types, subtypes, dependent types → `lean/usecases/01`
- Domain modeling: model domain invariants as type-level constraints → `lean/usecases/02`
<!-- /vibe-types:lean -->
```

### Scala 3
```
<!-- vibe-types:scala3 -->
## Scala 3 type-safety quick index (vibe-types)
- Opaque types: zero-cost distinct types; prevent value mix-ups without boxing → `scala3/catalog/12`
- Enums, ADTs, GADTs: closed variants with exhaustive matching; per-branch type refinement → `scala3/catalog/11`
- Union & intersection types: type-safe alternatives without class hierarchies → `scala3/catalog/01`
- Givens & using clauses: type-class dispatch; compiler supplies evidence automatically → `scala3/catalog/05`
- Match types: compute types from types; type-level conditional logic → `scala3/catalog/03`
- Inline + compiletime: move checks and branching to compile time → `scala3/catalog/17`
- Capture checking & CanThrow: track effects and capabilities at type level → `scala3/catalog/21`
- Preventing invalid states: ADTs, opaque types, phantom types, GADTs → `scala3/usecases/01`
- Protocol & state machines: enforce valid call ordering at compile time → `scala3/usecases/06`
- DSL & builder patterns: type-safe DSLs where invalid compositions are compile errors → `scala3/usecases/13`
<!-- /vibe-types:scala3 -->
```
