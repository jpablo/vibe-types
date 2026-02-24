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
| [Python](python/README.md) | Planned | — |
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
