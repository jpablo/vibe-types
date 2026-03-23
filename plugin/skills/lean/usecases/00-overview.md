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
- By matrix: use the shared [techniques matrix](../../../taxonomy/techniques.md).

## Numbering

Use-case documents are numbered `01` through `10`:

- `UC01-invalid-states.md`
- `UC02-domain-modeling.md`
- `UC03-exhaustiveness.md`
- `UC12-compile-time.md`
- `UC11-effect-tracking.md`
- `UC04-generic-constraints.md`
- `UC24-termination.md`
- `UC10-encapsulation.md`

## Snippet Style

- Patterns should be short and constraint-focused.
- Prefer one enforcement point per snippet.
- Use `-- error` and `-- OK` Lean comment conventions.
