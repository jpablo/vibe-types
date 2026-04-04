# Feature Catalog — Reading Guide

## Purpose

Part I of this guide is the **Feature Catalog**: one document per TypeScript type system feature (or feature cluster). Each document answers the question:

> *Given this feature, what constraints can I express that I couldn't before?*

## Document Structure Convention

Every catalog document follows this template:

0. **Version annotation** — a blockquote line immediately below the title indicating which TypeScript version introduced the feature and any notable version changes. Format: `> **Since:** TypeScript X.Y` or `> **Since:** TypeScript X.Y | **Latest changes:** TypeScript X.Y (description)`. Features requiring a compiler flag use `> **Status:** Requires \`--strict\` | **Since:** TypeScript X.Y` or the specific flag name (e.g., `--strictNullChecks`, `--noUncheckedIndexedAccess`).
1. **What it is** — a one-paragraph definition of the feature.
2. **What constraint it lets you express** — the key insight, stated up front in bold. This is the most important section: the *reason* you'd reach for this feature.
3. **Minimal snippet** — the shortest TypeScript code that demonstrates the constraint. No imports, no boilerplate beyond what's needed.
4. **Interaction with other features** — how this feature composes with others (with cross-references).
5. **Gotchas and limitations** — common pitfalls, edge cases, compiler limitations.
6. **Use-case cross-references** — a list of `[-> UC-##]` links to Part II documents where this feature appears.

## How to Read

- **If you know the feature:** jump directly to section 2 ("What constraint…") and section 6 (use-case links).
- **If you're exploring:** read section 1 for orientation, then section 3 for the code shape.
- **If you're composing features:** section 4 tells you which features interact well together.

## Numbering

Catalog documents use `T`-prefixed numbers (`T01`–`T63`). The numbers are shared across all language skill directories in this project for stable cross-language referencing. Not every number is used in the TypeScript catalog — only the features that apply to TypeScript are included. The highest numbers (`T62` and `T63`) are TypeScript-specific additions covering mapped types and template literal types, which have no direct analogue in other languages at this level of expressiveness.

Cross-references throughout the guide use the notation `[-> T##](T##-filename.md)`.

## Snippet Style

- Snippets show *only* the relevant type-level constraint, not complete programs.
- Type annotations are explicit where they aid understanding.
- Comments like `// error` mark lines the TypeScript compiler rejects (e.g., with `tsc --strict`).
- Comments like `// OK` mark lines that compile successfully.
- When a snippet depends on a compiler flag, a comment at the top of the block notes this: `// requires --strictNullChecks`.

## A Note on TypeScript's Type System

TypeScript's type system is **structural** and **gradual**. Structural means the compiler checks shape compatibility, not declaration-site identity — two types are assignable if they have the same shape, regardless of their names. Gradual means there is a controlled escape hatch (`any`, `unknown`) that lets you opt out of checking for portions of a codebase.

This dual nature is both a strength and a hazard:

- Structural typing enables duck-typed JavaScript patterns to work naturally.
- Gradual typing enables incremental migration from JavaScript.
- But `any` is contagious and can silently disable checks across module boundaries.

The Feature Catalog documents treat `--strict` mode (which enables `strictNullChecks`, `strictFunctionTypes`, `strictPropertyInitialization`, and others) as the default. Features that only make sense without `--strict` are noted explicitly.
