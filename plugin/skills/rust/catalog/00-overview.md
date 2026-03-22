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

- `T10-ownership-moves.md`
- `T11-borrowing-mutability.md`
- `T48-lifetimes.md`
- `T01-algebraic-data-types.md`
- `T04-generics-bounds.md`
- `T05-type-classes.md`
- `T49-associated-types.md`
- `T36-trait-objects.md`
- `T18-conversions-coercions.md`
- `T24-smart-pointers.md`
- `T50-send-sync.md`
- `T15-const-generics.md`
- `T25-coherence-orphan.md`
- `T37-trait-solver.md`

## Snippet Style

- Keep snippets minimal and focused on one compile-time property.
- Mark rejected lines with `// error`.
- Mark accepted lines with `// OK`.
- Prefer examples that isolate type constraints, not runtime behavior.
