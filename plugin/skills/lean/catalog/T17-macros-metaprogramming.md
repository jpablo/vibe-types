# Macros, Elaboration, and Syntax Extensions

> **Since:** Lean 4 (stable)

## What it is

Lean 4 has a powerful compile-time metaprogramming system that lets you extend the language's syntax and semantics. There are three layers:

1. **Syntax declarations** (`syntax`) — define new grammatical forms that the parser recognizes.
2. **Macro rules** (`macro_rules`) — transform new syntax into existing Lean syntax. Macros are hygienic and purely syntactic. They do **not** run at parse time: the parser only builds a `Syntax` tree, and macro expansion happens during elaboration, interleaved with type checking.
3. **Elaboration** (`elab`) — custom elaboration procedures that have full access to the Lean environment during type checking. This is the most powerful layer: elaborators can inspect types, create new definitions, and generate proof obligations.

Together, these let you build domain-specific notations, custom `do`-notation extensions, and even new tactic languages — all type-checked by the same kernel.

## What constraint it enforces

**Syntax extensions are processed at compile time; whatever they generate still goes through the full type checker. A macro or elaborator can absolutely *produce* an ill-typed term — the guarantee is that such a term is *rejected*, ultimately by the kernel.**

More specifically:

- **Parse-time validation.** `syntax` declarations define what the parser accepts. Invalid syntax is rejected before elaboration begins.
- **Macro hygiene.** Macro-generated identifiers don't capture or shadow user names accidentally. This prevents a class of bugs common in C preprocessor macros.
- **Type-checked output.** Whether from a macro or an elaborator, the generated Lean code passes through the full type checker. A macro that produces nonsense is caught at compile time. An `elab` that hands back a hand-built ill-typed `Expr` gets past elaboration but is stopped by the kernel with `(kernel) application type mismatch` — see the errors section below.
- **Phase separation.** Both macros and elaborators run during elaboration; the difference is what they see. A macro is handed only `Syntax` — no expected type, no environment queries — while an `elab` runs in `TermElabM` with the expected type and the full environment. Choosing the right layer matters.

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
| **Notation & Attributes** [→ T39](T39-notation-attributes.md) | `notation` is a simple macro. `@[simp]` attributes are processed by elaboration. |
| **Proof Automation** [→ T30](T30-proof-automation.md) | Tactics like `simp` and `omega` are implemented as elaborators. Custom tactics use the `elab` framework. |
| **Type Classes** [→ T05](T05-type-classes.md) | `deriving` handlers are elaborators that auto-generate type class instances. |
| **Monads / IO** [→ T12](T12-effect-tracking.md) | `do`-notation itself is a macro that expands to `bind` calls. Extensions to `do`-notation use the same framework. |

## Gotchas and limitations

1. **Macro vs elaborator choice.** Use macros for simple syntactic transformations (they're faster and simpler). Use elaborators when you need type information, environment access, or to generate definitions.

2. **Error messages from macros.** When a macro-expanded expression fails type checking, the error points to the expanded code, not the original syntax. This can be confusing. Use `trace` in macros for debugging.

3. **Syntax priorities.** When multiple syntax rules overlap, priority determines which parses first. Incorrect priorities cause unexpected parsing.

4. **`macro_rules` are pattern-based.** They match syntax trees, not types. If you need type-directed behavior, you need an elaborator.

5. **Lean metaprogramming API is large.** The `Lean.Elab`, `Lean.Meta`, and `Lean.Syntax` namespaces are extensive. Start with macros and the `macro` convenience command before diving into raw elaboration.

## Beginner mental model

Think of macros as **find-and-replace at the syntax level**. You define a pattern (new syntax) and a replacement (existing Lean code). Expansion happens as the elaborator walks the syntax tree — the parser has already finished by then and knows nothing about your `macro_rules` — and the expanded code is then type-checked as ordinary Lean. Elaborators are more powerful: they're like macros that can also *ask the type checker questions* while generating code.

Coming from Rust: `macro_rules!` ≈ Rust's `macro_rules!` (pattern-based syntax transformation). `elab` ≈ Rust's procedural macros (full compile-time code access). Both languages call their pattern macros "hygienic", but do not equate the two: Lean's hygiene is complete, whereas Rust's `macro_rules!` is only *partially* hygienic — it protects local variables and loop labels, but items, types, paths, and lifetimes are resolved at the use site and can capture.

## Example A — Custom notation via macro

```lean
-- A custom left-associative "pipe-forward" operator (`|>` is already built in,
-- so we pick a fresh symbol). The precedences make it left-associative.
syntax:55 term:55 " ~> " term:56 : term

macro_rules
  | `($x ~> $f) => `($f $x)

#eval 5 ~> toString ~> String.length  -- OK: desugars to String.length (toString 5)
```

## Example B — Custom tactic via elab

```lean
import Lean
open Lean Elab Tactic

-- A tactic that closes goals of the form `True`
elab "my_trivial" : tactic => do
  let goal ← getMainGoal
  let newGoals ← goal.apply (mkConst ``True.intro)
  replaceMainGoal newGoals          -- True.intro takes no args, so newGoals = []

example : True := by my_trivial  -- OK: custom tactic closes the goal
```

## Common compiler errors and how to read them

### `unexpected token '...'; expected ...` / `unexpected end of input`

```
unexpected token 'then'; expected term
unexpected end of input
```

**Meaning:** A use site did not match your `syntax` declaration — a missing operand, a stray keyword, or a competing rule with a higher priority winning the parse. These are the *real* parser messages; the bare string `expected token` is not one Lean emits at top level (it only shows up inside syntax quotations). Check the declared arity and precedences of the rule.

### `elaboration function for 'termFoo_' has not been implemented`

```
elaboration function for `termGimme_` has not been implemented
  gimme 5
```

**Meaning:** You declared `syntax` but no `macro_rules` or `elab` for it. Note what this error proves: the parser accepted `gimme 5` happily and produced a `Syntax` node — the failure comes later, at elaboration. That is the phase at which macros expand.

### `invalid macro_rules alternative, multiple interpretations for pattern`

```
invalid macro_rules alternative, multiple interpretations for pattern
(solution: specify node kind using `macro_rules (kind := ...) ...`)
```

**Meaning:** Two `syntax` declarations produce overlapping shapes, so Lean cannot tell which node kind your `macro_rules` pattern is meant to match. Give the kind explicitly, or make the syntaxes distinguishable.

### `(kernel) application type mismatch` — an elaborator produced an ill-typed term

```lean
import Lean
open Lean Elab Term

-- An `elab` is free to *build* an ill-typed `Expr`; nothing in the
-- elaborator stops it. The kernel is what refuses the declaration.
elab "bogus" : term => return mkApp (mkConst ``Nat.succ) (mkConst ``Bool.true)

def oops : Nat := bogus
-- error: (kernel) application type mismatch: Nat.succ true — argument has type Bool but function has type Nat → Nat
```

**Meaning:** The `(kernel)` prefix tells you elaboration finished and the *kernel* rejected the result. This is the safety net behind "metaprogramming cannot break type safety": bad output is possible, but unaccepted.

### Type error in macro-expanded code

When a macro produces valid syntax but the expanded code doesn't type-check, you get a normal type error — but pointing to the expanded code. Trace the expansion with `set_option trace.Elab.step true`.

## Proof perspective (brief)

Lean's tactic framework is built on the elaboration system. Every tactic (`simp`, `ring`, `omega`, `apply`, `intro`) is an elaborator that manipulates *proof goals* (metavariables of type `Prop`). Writing a custom tactic means writing an elaborator that transforms the goal state. The `Lean.Meta` and `Lean.Elab.Tactic` APIs provide the tools for inspecting hypotheses, unifying terms, and closing goals. Mathlib's extensive tactic library is entirely built on this framework.

## Use-case cross-references


## Source anchors

- *Functional Programming in Lean* — "Macros" (if covered)
- *Lean 4 Metaprogramming Book* — comprehensive guide to macros and elaboration
- Lean 4 source: `Lean.Elab.Macro`, `Lean.Elab.Tactic`, `Lean.Syntax`
