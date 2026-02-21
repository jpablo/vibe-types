# Feature Catalog — Reading Guide

## Purpose

Part I of this guide is the **Feature Catalog**: one document per Rust type-system feature (or feature cluster). Each document answers:

> *Given this feature, what constraints can I express at compile time?*

## Document Structure Convention

Every catalog document follows this template:

1. **What it is** — one-paragraph definition of the feature.
2. **What constraint it enforces** — the key compile-time guarantee in bold.
3. **Minimal snippet** — shortest possible Rust snippet showing the guarantee.
4. **Interaction with other features** — how it composes with other catalog entries.
5. **Gotchas and limitations** — common pitfalls, caveats, unstable edges.
6. **Use-case cross-references** — links to relevant `UC-nn` documents.

## How to Read

- If you already know the feature: read sections 2 and 6 first.
- If you are exploring: read sections 1 and 3 first.
- If you are combining features: focus on section 4.

## Numbering

Catalog documents are numbered `01` through `14` for stable cross-referencing:

- `01-ownership-moves.md`
- `02-borrowing-mutability.md`
- `03-lifetimes.md`
- `04-structs-enums-newtypes.md`
- `05-generics-where-clauses.md`
- `06-traits-impls.md`
- `07-associated-types-advanced-traits.md`
- `08-trait-objects-dyn.md`
- `09-inference-aliases-conversions.md`
- `10-smart-pointers-interior-mutability.md`
- `11-send-sync.md`
- `12-const-generics.md`
- `13-coherence-orphan-rules.md`
- `14-trait-solver-param-env.md`

## Snippet Style

- Keep snippets minimal and focused on one compile-time property.
- Mark rejected lines with `// error`.
- Mark accepted lines with `// OK`.
- Prefer examples that isolate type constraints, not runtime behavior.
