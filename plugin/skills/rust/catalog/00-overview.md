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
6. **Beginner mental model** — intuitive framing for first-time learners.
7. **Example A / Example B** — practical snippets that show real usage shape.
8. **Common compiler errors and how to read them** — map common error messages to fixes.
9. **Use-case cross-references** — links to relevant `UC-nn` documents.
10. **Source anchors** — where the guidance comes from.

## How to Read

- If you already know the feature: read sections 2 and 6 first.
- If you are exploring: read sections 1 and 3 first.
- If you are combining features: focus on section 4.

## Beginner Reading Guidance

- **Start with a single theme:** pick one catalog entry (e.g., ownership, lifetimes) and read sections 1–3 together before branching out; this builds an early mental model.
- **Pair with a practical example:** after the minimal snippet, try running a tiny playground version or modifying it slightly—experimenting reinforces how the compile-time constraint feels.
- **Use cross-references as study links:** when one feature links to another (`[-> catalog/06]`, `[-> UC-05]`), treat them as "learned next" targets rather than reading the whole catalog in order.
- **Track common compiler messages:** before diving into advanced chapters, skim the "Common compiler errors" sections to see how diagnostics describe each feature; `catalog/02` and `catalog/05` are good starting points.

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
