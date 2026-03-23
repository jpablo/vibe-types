# Use-Case Index — Navigation Guide

## Purpose

Part II of this guide is the **Use-Case Index**: one document per compile-time constraint category. Each document answers:

> *I want the compiler to enforce X; which Rust features help, and how?*

## Document Structure Convention

Every use-case document follows this template:

1. **The constraint** — precise statement of what must be enforced.
2. **Feature toolkit** — relevant catalog features with links.
3. **Patterns** — 2-4 minimal snippets showing common approaches.
4. **Tradeoffs** — where each pattern is strong or weak.
5. **When to use which feature** — practical selection guidance.

## How to Navigate

- By constraint: start in this directory and pick the closest `UC-nn`.
- By feature: jump from catalog docs via use-case links.
- By matrix: use the shared feature matrix once Rust rows are added.

## Numbering

Use-case documents:

- `UC01-invalid-states.md`
- `UC02-domain-modeling.md`
- `UC03-exhaustiveness.md`
- `UC04-generic-constraints.md`
- `UC08-error-handling.md`
- `UC09-builder-config.md`
- `UC10-encapsulation.md`
- `UC11-effect-tracking.md`
- `UC12-compile-time.md`
- `UC13-state-machines.md`
- `UC14-extensibility.md`
- `UC18-type-arithmetic.md`
- `UC20-ownership-apis.md`
- `UC21-concurrency.md`
- `UC22-conversions.md`
- `UC23-diagnostics.md`

## Snippet Style

- Patterns should be short and constraint-focused.
- Prefer one enforcement point per snippet.
- Keep syntax current and explicit where it improves clarity.
