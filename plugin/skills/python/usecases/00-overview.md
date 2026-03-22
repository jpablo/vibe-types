# Use-Case Index — Navigation Guide

## Purpose

Part II of this guide is the **Use-Case Index**: one document per type-checking constraint category. Each document answers:

> *I want my type checker to enforce X; which Python features help, and how?*

## Document Structure Convention

Every use-case document follows this template:

1. **The constraint** — precise statement of what must be enforced.
2. **Feature toolkit** — relevant catalog features with links.
3. **Patterns** — 2-4 minimal snippets showing common approaches.
4. **Tradeoffs** — where each pattern is strong or weak.
5. **When to use which feature** — practical selection guidance.
6. **Source anchors** — where the guidance comes from.

## How to Navigate

- By constraint: start in this directory and pick the closest `UC-nn`.
- By feature: jump from catalog docs via use-case links.
- By matrix: use the shared [feature matrix](../../../../appendix/feature-matrix.md).

## Numbering

Use-case documents are numbered `01` through `12`:

- `UC01-invalid-states.md`
- `UC02-domain-modeling.md`
- `UC03-exhaustiveness.md`
- `UC04-generic-constraints.md`
- `UC05-structural-contracts.md`
- `UC06-immutability.md`
- `UC07-callable-contracts.md`
- `UC08-error-handling.md`
- `UC09-builder-config.md`
- `UC29-typed-records.md`
- `UC28-decorator-typing.md`
- `UC27-gradual-adoption.md`

## Snippet Style

- Patterns should be short and constraint-focused.
- Prefer one enforcement point per snippet.
- Include "untyped Python comparison" where it illustrates runtime failures types would catch.
