# Use-Case Index — Navigation Guide

## Purpose

Part II of this guide is the **Use-Case Index**: one document per category of compile-time constraint. Each document answers the question:

> *I want the compiler to enforce X — which features help, and how?*

## Document Structure Convention

Every use-case document follows this template:

1. **The constraint** — what property you want the compiler to enforce, stated precisely.
2. **Feature toolkit** — which catalog features apply, with `[-> catalog/nn]` links.
3. **Patterns** — 2–4 minimal code patterns showing the technique.
4. **Scala 2 comparison** — how the same constraint was (or wasn't) expressible in Scala 2.
5. **When to use which feature** — decision guidance for choosing among alternatives.

## How to Navigate

- **By constraint:** scan the [Use-Case Index table in the Scala 3 README](../README.md) for the property you care about.
- **By feature:** each catalog document ends with `[-> UC-nn]` links pointing here.
- **By matrix:** the [Techniques matrix](../../../../taxonomy/techniques.md) gives the full cross-language mapping.

## Numbering

Use-case documents are numbered `01`–`15`. Cross-references use `[-> UC-nn]` notation throughout the guide.

## Snippet Style

- Patterns are minimal: just enough code to show the technique.
- Each pattern is labeled (e.g., "Pattern A: Phantom type approach").
- The Scala 2 comparison is brief — just enough to show *what changed*, not a full Scala 2 tutorial.
