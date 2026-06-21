# Vibe Types

A multi-language guide to type system features — mapping each language's type system capabilities to the constraints and properties they can enforce at compile time.

**Approach:** For each language, a *Technique Catalog* documents what each type feature enables, and a *Use-Case Index* shows which features solve which problem. A shared *Taxonomy* provides cross-language coverage matrices.

---

## Core tenets

Let the type checker carry as much of correctness as it can — move guarantees out of runtime checks, tests, and discipline and into the types, so that holding a value is itself evidence its invariants hold. Apply these with judgment, not as absolute rules. Each language skill embeds an adapted copy; the canonical wording lives in **[docs/core-tenets.md](docs/core-tenets.md)**.

- **Make illegal states unrepresentable** — model the data so an invalid combination of values doesn't typecheck.
- **Parse, don't validate** — at the boundary, turn a check into a value of a refined type that proves the check ran, instead of returning a boolean and discarding it.
- **Keep a functional core and an imperative shell** — pure decisions in the center; push the effects (I/O, network, database, the clock, randomness) out to a thin outer layer.
- **Upgrade information at the edges; never re-acquire it in the core** — capture what each parse or check proves in a type and pass it inward, rather than re-deriving it.
- **Prefer a more precise type over a less precise one** — among the types that can hold every legal value, choose the one with the fewest illegal ones.
- **Add precision where a wrong value would do real harm, and leave low-stakes values plain** — spend the friction of a precise type where a wrong value is costly, crosses a boundary, or is relied on far and wide.
- **Prefer types over tests to capture invariants** — if the compiler can enforce a property, don't write a test for it.
- **Make functions total, and let the compiler force every case** — defined for every input; widen the output (`Option`/`Result`) or narrow the input, and handle every case.
- **Make immutability the default, and mark mutation as the exception** — a value that can't change can't quietly become invalid behind the check that vouched for it.
- **Use state machines when appropriate** — encode an object's lifecycle states as types so an invalid transition doesn't compile.
- **Pass authority as a typed value instead of reaching for ambient power** — take effects and capabilities (`Clock`, `HttpClient`, `PaymentGateway`) as parameters, not globals.

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

### Plugin install

```
/plugin marketplace add jpablo/vibe-types
/plugin install vibe-types@vibe-types-marketplace
```

This registers one skill per language (Python, Rust, Scala 3, Lean 4, TypeScript). Claude auto-loads the relevant skill when it detects a matching topic — no manual setup needed.
