# Vibe Types

A multi-language guide to type system features — mapping each language's type system capabilities to the constraints and properties they can enforce at compile time.

**Approach:** For each language, a *Feature Catalog* documents what each type feature enables, and a *Use-Case Index* shows which features solve which problem. A shared appendix provides cross-language resources.

---

## Languages

| Language | Status | Guide |
|----------|--------|-------|
| [Scala 3](plugin/skills/scala3/README.md) | Complete | 23 feature catalog entries, 15 use-case documents |
| [Java](plugin/skills/java/README.md) | Planned | — |
| [TypeScript](plugin/skills/typescript/README.md) | Planned | — |
| [Rust](plugin/skills/rust/README.md) | In Progress | 14 feature catalog entries, 8 use-case documents |
| [Python](plugin/skills/python/README.md) | In Progress | 20 feature catalog entries, 12 use-case documents |
| [Haskell](plugin/skills/haskell/README.md) | Planned | — |
| [OCaml](plugin/skills/ocaml/README.md) | Planned | — |
| [Lean](plugin/skills/lean/README.md) | In Progress | 16 feature catalog entries, 10 use-case documents |
| [Agda](plugin/skills/agda/README.md) | Planned | — |
| [TLA+](plugin/skills/tlaplus/README.md) | Planned | — |

---

## Shared Resources

| Document | Contents |
|----------|----------|
| [Techniques](taxonomy/techniques.md) | Cross-language technique coverage matrix |
| [Use Cases](taxonomy/usecases.md) | Cross-language use-case coverage matrix |
| [Further Reading](docs/scala-further-reading.md) | Official docs, SIPs, talks, libraries |
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

The `docs/` directory contains supplementary documentation. The `taxonomy/` directory has cross-language coverage matrices.

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
```

</details>

<details>
<summary><strong>Rust quick index</strong></summary>

```markdown
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
```

</details>

<details>
<summary><strong>Lean 4 quick index</strong></summary>

```markdown
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
```

</details>

<details>
<summary><strong>Scala 3 quick index</strong></summary>

```markdown
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
```

</details>
