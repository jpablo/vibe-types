# Use-Case Index — Navigation Guide

## Purpose

Part II of this guide is the **Use-Case Index**: one document per category of compile-time constraint. Each document answers the question:

> *I want the compiler to enforce X — which features help, and how?*

## Document Structure Convention

Every use-case document follows this template:

1. **The constraint** — what property you want the compiler to enforce, stated precisely.
2. **Feature toolkit** — which catalog features apply, with `[-> T##](../catalog/T##-filename.md)` links.
3. **Patterns** — 2–4 minimal code patterns showing the technique.
4. **JavaScript / pre-TypeScript comparison** — how the same constraint was (or wasn't) expressible in plain JavaScript before TypeScript, and what you had to rely on instead (runtime checks, documentation conventions, naming disciplines).
5. **When to use which feature** — decision guidance for choosing among alternatives.

## How to Navigate

- **By constraint:** scan the [Use-Case Index table in the TypeScript README](../README.md#part-ii-use-case-index) for the property you care about.
- **By feature:** each catalog document ends with `[-> UC-##]` links pointing here.
- **By matrix:** the [Techniques matrix](../../../../taxonomy/techniques.md) gives the full cross-language mapping.

## Numbering

Use-case documents are numbered `UC01`–`UC21`, with gaps where certain use cases don't apply to TypeScript: `UC11`, `UC12`, `UC18`, and `UC20` are absent from the TypeScript set. The present documents are: UC01–UC10, UC13–UC17, UC19, UC21.

Cross-references use `[-> UC-##]` notation throughout the guide.

## Snippet Style

- Patterns are minimal: just enough TypeScript to show the technique.
- Each pattern is labeled (e.g., "Pattern A: Branded type approach").
- Comments like `// error` mark compiler-rejected lines; `// OK` marks valid lines.
- The JavaScript comparison section is brief — just enough to show *what changed*, not a full JavaScript tutorial.
- When a technique requires `--strict` or a specific flag, a comment at the top of the snippet notes this.

## A Note on JavaScript Comparison

Many TypeScript type constraints are invisible at runtime — the types are erased during compilation. The "JavaScript / pre-TypeScript comparison" section in each use-case document therefore focuses on two things:

1. What the JavaScript-era convention or workaround was (runtime guards, JSDoc annotations, naming conventions like `_userId` for values that must be treated as opaque).
2. What is *gained* by encoding the constraint in the type system: earlier error detection, IDE feedback, no runtime overhead for type-level distinctions, and refactoring safety.

This framing reflects TypeScript's design goal: to be a superset of JavaScript that adds static verification without changing runtime semantics.
