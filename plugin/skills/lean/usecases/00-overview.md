# Use-Case Index — Navigation Guide

## Purpose

Part II of this guide is the **Use-Case Index**: one document per compile-time constraint category. Each document answers:

> *I want the Lean compiler to enforce X; which features help, and how?*

## Document Structure Convention

Every use-case document follows this template:

1. **The constraint** — precise statement of what must be enforced.
2. **Feature toolkit** — relevant catalog features with links.
3. **Patterns** — 2–4 minimal snippets showing common approaches.
4. **Tradeoffs** — where each pattern is strong or weak.
5. **When to use which feature** — practical selection guidance.
6. **Source anchors** — where the guidance comes from.

## How to Navigate

- By constraint: start in this directory and pick the closest `UC-nn`.
- By feature: jump from catalog docs via use-case links.
- By matrix: use the shared [feature matrix](../../../../appendix/feature-matrix.md) (Lean section).

## Numbering

Use-case documents are numbered `01` through `10`:

- `01-preventing-invalid-states.md`
- `02-domain-modeling-dependent-types.md`
- `03-totality-exhaustiveness.md`
- `04-compile-time-invariants.md`
- `05-safe-effectful-programming.md`
- `06-generic-programming-type-classes.md`
- `07-safe-recursion-termination.md`
- `08-encapsulation-module-boundaries.md`
- `09-metaprogramming-syntax-extension.md`
- `10-interop-escape-hatches.md`

## Snippet Style

- Patterns should be short and constraint-focused.
- Prefer one enforcement point per snippet.
- Use `-- error` and `-- OK` Lean comment conventions.
