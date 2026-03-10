# Feature Catalog — Reading Guide

## Purpose

Part I of this guide is the **Feature Catalog**: one document per Python type-system feature (or feature cluster). Each document answers:

> *Given this feature, what constraints can my type checker enforce?*

Python's type system is opt-in and gradual: annotations have no runtime enforcement by default, so the constraints described here are enforced by static type checkers — primarily **mypy** and **pyright**. The catalog treats these checkers as the "compiler" for constraint purposes.

## Document Structure Convention

Every catalog document follows this template:

1. **What it is** — one-paragraph definition of the feature.
2. **What constraint it enforces** — the key check-time guarantee in bold.
3. **Minimal snippet** — shortest possible Python snippet showing the guarantee.
4. **Interaction with other features** — how it composes with other catalog entries.
5. **Gotchas and limitations** — common pitfalls, caveats, checker divergences.
6. **Beginner mental model** — intuitive framing for first-time learners.
7. **Example A / Example B** — practical snippets that show real usage shape.
8. **Common type-checker errors and how to read them** — map common mypy/pyright messages to fixes.
9. **Use-case cross-references** — links to relevant `UC-nn` documents.
10. **Source anchors** — PEPs, docs, and typing spec references.

## How to Read

- If you already know the feature: read sections 2 and 6 first.
- If you are exploring: read sections 1 and 3 first.
- If you are combining features: focus on section 4.

## Beginner Reading Guidance

- **Start with basic annotations:** pick [catalog/01](01-basic-annotations-none.md) and read sections 1--3 to see how types constrain code.
- **Pair with a practical example:** run `mypy` or `pyright` on the minimal snippets to see real error messages.
- **Use cross-references as study links:** when one feature links to another (`[-> catalog/06]`, `[-> UC-05]`), treat them as "learn next" targets rather than reading the whole catalog in order.
- **Compare checker behavior:** when "Gotchas" mentions checker differences, try the snippet in both mypy and pyright to build intuition for where they diverge.

## Numbering

Catalog documents are numbered `01` through `20` for stable cross-referencing:

- `01-basic-annotations-none.md`
- `02-union-literal-types.md`
- `03-typeddict.md`
- `04-newtype.md`
- `05-enums-typing.md`
- `06-dataclasses-typing.md`
- `07-generics-typevar.md`
- `08-paramspec-typevar-tuple.md`
- `09-protocol-structural-subtyping.md`
- `10-abc-abstract-classes.md`
- `11-callable-types-overload.md`
- `12-final-classvar.md`
- `13-typeguard-typeis-narrowing.md`
- `14-never-noreturn.md`
- `15-annotated-metadata.md`
- `16-self-type.md`
- `17-type-aliases-type-statement.md`
- `18-generic-classes-variance.md`
- `19-unpack-kwargs-typing.md`
- `20-type-inference-gradual-typing.md`

## Snippet Style

- Keep snippets minimal and focused on one type-checking property.
- Mark rejected lines with `# error`.
- Mark accepted lines with `# OK`.
- Prefer examples that isolate type constraints, not runtime behavior.
- Include the Python version requirement when a feature needs 3.10+.
