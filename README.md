# Vibe Types

A multi-language guide to type system features — mapping each language's type system capabilities to the constraints and properties they can enforce at compile time.

**Approach:** For each language, a *Technique Catalog* documents what each type feature enables, and a *Use-Case Index* shows which features solve which problem. A shared *Taxonomy* provides cross-language coverage matrices.

---

## Languages

| Language | Status | Guide |
|----------|--------|-------|
| [Scala 3](plugin/skills/scala3/README.md) | In Progress | 47 technique catalog entries, 20 use-case documents |
| [Rust](plugin/skills/rust/README.md) | In Progress | 45 technique catalog entries, 21 use-case documents |
| [Lean 4](plugin/skills/lean/README.md) | In Progress | 48 technique catalog entries, 18 use-case documents |
| [TypeScript](plugin/skills/typescript/README.md) | In Progress | 35 technique catalog entries, 17 use-case documents |
| [Python](plugin/skills/python/README.md) | In Progress | 32 technique catalog entries, 18 use-case documents |
| [Java](plugin/skills/java/README.md) | Planned | — |
| [Haskell](plugin/skills/haskell/README.md) | Planned | — |
| [OCaml](plugin/skills/ocaml/README.md) | Planned | — |
| [Agda](plugin/skills/agda/README.md) | Planned | — |
| [TLA+](plugin/skills/tlaplus/README.md) | Planned | — |

---

## Shared Resources

| Document | Contents |
|----------|----------|
| [Techniques](taxonomy/techniques.md) | 64 techniques × 5 languages — cross-language coverage matrix |
| [Use Cases](taxonomy/usecases.md) | 22 use cases × 5 languages — cross-language coverage matrix |
| [Sources](taxonomy/sources.md) | References and primary sources per language |
| [Changelog](CHANGELOG.md) | Version history and update log |

---

## Structure

```
vibe-types/
├── plugin/                  # Claude Code plugin (installable)
│   ├── .claude-plugin/
│   │   └── plugin.json
│   └── skills/
│       ├── scala3/          # One skill per language
│       │   ├── SKILL.md
│       │   ├── catalog/     # T01-algebraic-data-types.md, T02-..., etc.
│       │   └── usecases/    # UC01-invalid-states.md, UC02-..., etc.
│       ├── python/
│       ├── rust/
│       ├── lean/
│       └── typescript/
├── taxonomy/                # Cross-language coverage matrices
│   ├── techniques.md
│   ├── usecases.md
│   └── sources.md
├── .claude-plugin/
│   └── marketplace.json     # For sharing via marketplace
└── docs/                    # Supplementary documentation
```

Technique files use stable IDs (`T01-algebraic-data-types.md`) shared across languages. The same filename = the same concept. Gaps are visible by comparing directory listings.

---

## Claude Code Integration

### Plugin install (recommended)

```
/plugin marketplace add jpablo/vibe-types
/plugin install vibe-types@vibe-types-marketplace
```

This registers one skill per language (Python, Rust, Scala 3, Lean 4, TypeScript). Claude auto-loads the relevant skill when it detects a matching topic — no manual setup needed.

### Install always-on context

Use the built-in command to add a quick index to your CLAUDE.md:

```
/vibe-types:install-context
```

It asks which language and where to install, then appends the snippet. Or do it manually — paste one or more of the quick indexes below into your `~/.claude/CLAUDE.md` (or project-level `CLAUDE.md`).

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
- Parse, don't validate: return refined types instead of checking and discarding → `UC01-invalid-states`
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
- Error handling: Result<T,E> + ? operator for type-tracked error paths → `UC08-error-handling`
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
- Opaque types: distinct types that prevent value mix-ups; no boxing in monomorphic use (boxes when used as a type argument, like any type, with no overhead beyond the underlying type) → `T03-newtypes-opaque`
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

<details>
<summary><strong>TypeScript quick index</strong></summary>

```markdown
- Discriminated unions & ADTs: closed tagged unions; exhaustive `switch`; invalid states unrepresentable → `T01-algebraic-data-types`
- Branded/opaque types: `string & { __brand: "UserId" }`; prevent value mix-ups at zero runtime cost → `T03-newtypes-opaque`
- Union & intersection types: `A | B`, `A & B`; alternatives without class hierarchies → `T02-union-intersection`
- Structural typing: shape conformance without inheritance; excess-property (freshness) checks on literals → `T07-structural-typing`
- Null safety: `strictNullChecks`, `T | null | undefined`, optional chaining; not null by default → `T13-null-safety`
- Narrowing & exhaustiveness: type guards, `in`, `instanceof`, discriminants; `never` for exhaustive checks → `T14-type-narrowing`, `T34-never-bottom`
- Conditional & mapped types: `T extends U ? X : Y`, `infer`, `{ [K in keyof T]: ... }` → `T41-match-types`, `T62-mapped-types`
- Template literal types: restrict string types to computed patterns; invalid strings are compile errors → `T63-template-literal-types`
- Generics & bounds: `<T extends U>`; generic code only compiles when constraints hold → `T04-generics-bounds`
- Preventing invalid states: discriminated unions, branded types, phantom types → `UC01-invalid-states`
```

</details>
