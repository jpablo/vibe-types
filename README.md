# Vibe Types

A multi-language guide to type system features — mapping each language's type system capabilities to the constraints and properties they can enforce at compile time.

**Approach:** For each language, a *Feature Catalog* documents what each type feature enables, and a *Use-Case Index* shows which features solve which problem. A shared appendix provides cross-language resources.

---

## Languages

| Language | Status | Guide |
|----------|--------|-------|
| [Scala 3](scala3/README.md) | Complete | 23 feature catalog entries, 15 use-case documents |
| [Java](java/README.md) | Planned | — |
| [TypeScript](typescript/README.md) | Planned | — |
| [Rust](rust/README.md) | In Progress | 14 feature catalog entries, 8 use-case documents |
| [Python](python/README.md) | In Progress | 20 feature catalog entries, 12 use-case documents |
| [Haskell](haskell/README.md) | Planned | — |
| [OCaml](ocaml/README.md) | Planned | — |
| [Lean](lean/README.md) | Planned | — |
| [Agda](agda/README.md) | Planned | — |
| [TLA+](tlaplus/README.md) | Planned | — |

---

## Shared Appendix

| Document | Contents |
|----------|----------|
| [Glossary](appendix/glossary.md) | Key terminology |
| [Feature Matrix](appendix/feature-matrix.md) | Feature × use-case cross-reference (per language) |
| [Further Reading](appendix/further-reading.md) | Official docs, SIPs, talks, libraries |
| [Changelog](CHANGELOG.md) | Version history and update log |

---

## Structure

Each language directory follows a common layout:

```
<language>/
├── README.md       # Landing page with catalog and use-case tables
├── catalog/        # One doc per type system feature
├── usecases/       # One doc per compile-time constraint
└── inputs/         # Source material list for that language
```

The shared `appendix/` at the root contains cross-language resources like the glossary and feature matrix.

---

## Claude Code Integration

### Plugin install (recommended)

```
/plugin marketplace add jpablo/vibe-types
/plugin install vibe-types@vibe-types-marketplace
```

This registers one skill per language (Python, Rust, Scala 3). Claude auto-loads the relevant skill when it detects a matching topic — no manual setup needed.

### Always-on context (optional)

For proactive recognition even before types are mentioned, paste one or more of the quick indexes below into your `~/.claude/CLAUDE.md` (or project-level `CLAUDE.md`). This keeps the index in context at all times so Claude can suggest type-safety techniques unprompted.

<details>
<summary><strong>Python quick index</strong></summary>

```markdown
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
```

</details>

<details>
<summary><strong>Rust quick index</strong></summary>

```markdown
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
```

</details>

<details>
<summary><strong>Scala 3 quick index</strong></summary>

```markdown
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
```

</details>
