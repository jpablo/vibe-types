# Macros, Elaboration, and Syntax Extensions

> **Since:** Lean 4 (stable)

## What it is

Lean 4 has a powerful compile-time metaprogramming system that lets you extend the language's syntax and semantics. There are three layers:

1. **Syntax declarations** (`syntax`) — define new grammatical forms that the parser recognizes.
2. **Macro rules** (`macro_rules`) — transform new syntax into existing Lean syntax at parse time. Macros are hygienic and purely syntactic.
3. **Elaboration** (`elab`) — custom elaboration procedures that have full access to the Lean environment during type checking. This is the most powerful layer: elaborators can inspect types, create new definitions, and generate proof obligations.

Together, these let you build domain-specific notations, custom `do`-notation extensions, and even new tactic languages — all type-checked by the same kernel.

## What constraint it enforces

**Syntax extensions are processed at compile time; the generated code is fully type-checked. Macros and elaborators cannot produce ill-typed terms.**

More specifically:

- **Parse-time validation.** `syntax` declarations define what the parser accepts. Invalid syntax is rejected before elaboration begins.
- **Macro hygiene.** Macro-generated identifiers don't capture or shadow user names accidentally. This prevents a class of bugs common in C preprocessor macros.
- **Type-checked output.** Whether from a macro or an elaborator, the generated Lean code passes through the full type checker. A macro that produces nonsense is caught at compile time.
- **Phase separation.** Macros run at parse time (no type information), elaborators run at elaboration time (full type information). Choosing the right layer matters.

## Minimal snippet

```lean
-- Define new syntax
syntax "assert! " term : term

-- Define how it expands
macro_rules
  | `(assert! $cond) => `(if $cond then pure () else panic! "assertion failed")

def check : IO Unit := do
  assert! (2 + 2 == 4)  -- OK: expands to if-then-else, type-checked
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Notation & Attributes** [→ catalog/16] | `notation` is a simple macro. `@[simp]` attributes are processed by elaboration. |
| **Proof Automation** [→ catalog/13] | Tactics like `simp` and `omega` are implemented as elaborators. Custom tactics use the `elab` framework. |
| **Type Classes** [→ catalog/04] | `deriving` handlers are elaborators that auto-generate type class instances. |
| **Monads / IO** [→ catalog/09] | `do`-notation itself is a macro that expands to `bind` calls. Extensions to `do`-notation use the same framework. |

## Gotchas and limitations

1. **Macro vs elaborator choice.** Use macros for simple syntactic transformations (they're faster and simpler). Use elaborators when you need type information, environment access, or to generate definitions.

2. **Error messages from macros.** When a macro-expanded expression fails type checking, the error points to the expanded code, not the original syntax. This can be confusing. Use `trace` in macros for debugging.

3. **Syntax priorities.** When multiple syntax rules overlap, priority determines which parses first. Incorrect priorities cause unexpected parsing.

4. **`macro_rules` are pattern-based.** They match syntax trees, not types. If you need type-directed behavior, you need an elaborator.

5. **Lean metaprogramming API is large.** The `Lean.Elab`, `Lean.Meta`, and `Lean.Syntax` namespaces are extensive. Start with macros and the `macro` convenience command before diving into raw elaboration.

## Beginner mental model

Think of macros as **find-and-replace at the syntax level**. You define a pattern (new syntax) and a replacement (existing Lean code). The compiler expands all macros before type checking, so the generated code must be valid Lean. Elaborators are more powerful — they're like macros that can also *ask the type checker questions* while generating code.

Coming from Rust: `macro_rules!` ≈ Rust's `macro_rules!` (pattern-based syntax transformation). `elab` ≈ Rust's procedural macros (full compile-time code access). Lean's macros are hygienic by default, like Rust's.

## Example A — Custom notation via macro

```lean
syntax term " |> " term : term

macro_rules
  | `($x |> $f) => `($f $x)

#eval 5 |> toString |> String.length  -- OK: desugars to String.length (toString 5)
```

## Example B — Custom tactic via elab

```lean
-- A tactic that closes goals of the form `True`
elab "my_trivial" : tactic => do
  let goal ← Lean.Elab.Tactic.getMainGoal
  goal.apply (Lean.mkConst ``True.intro)

example : True := by my_trivial  -- OK: custom tactic closes the goal
```

## Common compiler errors and how to read them

### `expected token`

```
expected token
```

**Meaning:** Your `syntax` declaration has a parse error or conflicting syntax rule. Check the syntax definition and priorities.

### `macro expansion error`

```
macro expansion produced ill-formed term
```

**Meaning:** Your `macro_rules` expansion generated syntax that Lean can't parse or elaborate. Debug by replacing the macro body with a simpler expression and building up.

### Type error in macro-expanded code

When a macro produces valid syntax but the expanded code doesn't type-check, you get a normal type error — but pointing to the expanded code. Trace the expansion with `set_option trace.Elab.step true`.

## Proof perspective (brief)

Lean's tactic framework is built on the elaboration system. Every tactic (`simp`, `ring`, `omega`, `apply`, `intro`) is an elaborator that manipulates *proof goals* (metavariables of type `Prop`). Writing a custom tactic means writing an elaborator that transforms the goal state. The `Lean.Meta` and `Lean.Elab.Tactic` APIs provide the tools for inspecting hypotheses, unifying terms, and closing goals. Mathlib's extensive tactic library is entirely built on this framework.

## Use-case cross-references

- [→ UC-09](../usecases/09-metaprogramming-syntax-extension.md) — Extend the language safely at compile time.

## Source anchors

- *Functional Programming in Lean* — "Macros" (if covered)
- *Lean 4 Metaprogramming Book* — comprehensive guide to macros and elaboration
- Lean 4 source: `Lean.Elab.Macro`, `Lean.Elab.Tactic`, `Lean.Syntax`
