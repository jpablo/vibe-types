# Feature Catalog — Reading Guide

## Purpose

Part I of this guide is the **Feature Catalog**: one document per Scala 3 type system feature (or feature cluster). Each document answers the question:

> *Given this feature, what constraints can I express that I couldn't before?*

## Document Structure Convention

Every catalog document follows this template:

0. **Version annotation** — a blockquote line immediately below the title indicating which Scala version introduced the feature and any notable version changes. Format: `> **Since:** Scala X.Y` or `> **Since:** Scala X.Y | **Latest changes:** Scala X.Y (description)`. Experimental features use `> **Status:** Experimental | **Since:** Scala X.Y`.
1. **What it is** — a one-paragraph definition of the feature.
2. **What constraint it lets you express** — the key insight, stated up front in bold. This is the most important section: the *reason* you'd reach for this feature.
3. **Minimal snippet** — the shortest code that demonstrates the constraint. No imports, no `@main`, no boilerplate beyond what's needed.
4. **Interaction with other features** — how this feature composes with others (with cross-references).
5. **Gotchas and limitations** — common pitfalls, edge cases, compiler limitations.
6. **Use-case cross-references** — a list of `[-> UC-nn]` links to Part II documents where this feature appears.

## How to Read

- **If you know the feature:** jump directly to section 2 ("What constraint…") and section 6 (use-case links).
- **If you're exploring:** read section 1 for orientation, then section 3 for the code shape.
- **If you're composing features:** section 4 tells you which features interact well together.

## Numbering

Catalog documents are numbered `01`–`23`. The numbering is for stable cross-referencing, not an ordering of importance. Cross-references throughout the guide use the notation `[-> catalog/nn]`.

## Snippet Style

- Snippets show *only* the relevant type-level constraint, not complete programs.
- Type annotations are explicit where they aid understanding.
- Comments like `// error` mark lines the compiler rejects.
- Comments like `// OK` mark lines that compile.
