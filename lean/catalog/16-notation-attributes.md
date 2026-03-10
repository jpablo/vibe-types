# Notation, Attributes, and Compiler Options

> **Since:** Lean 4 (stable)

## What it is

Lean provides three orthogonal mechanisms for controlling how the compiler treats definitions:

1. **Notation** — declares syntactic sugar for expressions. `notation "‖" x "‖" => norm x` lets you write `‖v‖` instead of `norm v`. Notations are lightweight macros [→ catalog/12] with precedence control.

2. **Attributes** — metadata tags attached to definitions that affect how the compiler, simplifier, or other tools process them. Common attributes:
   - `@[simp]` — register as a simplifier lemma
   - `@[inline]` — inline the function at call sites
   - `@[reducible]` — always unfold during type checking
   - `@[irreducible]` — block automatic unfolding
   - `@[ext]` — register as an extensionality lemma
   - `@[instance]` — register as a type class instance (usually implicit in `instance` declarations)

3. **Compiler options** — `set_option` commands that control the compiler's behavior, such as `set_option maxHeartbeats 400000` (type checking budget) or `set_option pp.all true` (pretty-printing).

## What constraint it enforces

**Attributes and options control the compiler's treatment of definitions; incorrect attributes cause type-check failures, and options control resource limits and output.**

More specifically:

- **`@[simp]` correctness.** A `@[simp]` lemma must be an equality or iff — the simplifier rejects non-rewriting lemmas.
- **`@[inline]` guarantees.** Marking a function `@[inline]` guarantees it's inlined, affecting performance but not semantics.
- **Option scoping.** `set_option` is scoped — it applies to the current `section`, `namespace`, or command. This prevents global side effects.
- **`@[reducible]`/`@[irreducible]` affect type checking.** They change what the kernel can see, which can make proofs succeed or fail.

## Minimal snippet

```lean
-- Notation
notation "‖" x "‖" => Float.sqrt (x * x)
#eval ‖3.0‖  -- OK: 3.0

-- Attribute
@[simp] theorem Nat.add_zero' (n : Nat) : n + 0 = n := Nat.add_zero n
example : 5 + 0 = 5 := by simp  -- OK: uses the @[simp] lemma

-- Compiler option
set_option maxHeartbeats 200000 in
def expensiveComputation := ...
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Proof Automation** [→ catalog/13] | `@[simp]` populates the simplifier database. `@[ext]` enables `ext` tactic. `@[omega]`-like rules are built into `omega` directly. |
| **Opaque Definitions** [→ catalog/15] | `@[reducible]` and `@[irreducible]` control unfolding on a spectrum from transparent to opaque. |
| **Macros & Elaboration** [→ catalog/12] | `notation` is a macro. Custom attributes can be defined using the elaboration framework. |
| **Type Classes** [→ catalog/04] | `@[instance]` explicitly registers a definition as a type class instance (usually inferred from `instance` syntax). `@[default_instance]` sets priority. |

## Gotchas and limitations

1. **`@[simp]` loops.** If you register a lemma that creates a cycle (e.g., `a = b` and `b = a` both as `@[simp]`), the simplifier loops. Use `@[simp]` only for oriented rewrites (left side is "more complex").

2. **Notation precedence.** Incorrect precedence makes notation parse unexpectedly. Use `notation:65` (with explicit precedence) to control binding strength.

3. **`scoped` attributes.** `@[scoped simp]` makes the attribute active only when the current namespace is opened. This prevents polluting the global `simp` set.

4. **`set_option` scope.** Forgetting that options are scoped means your `set_option maxHeartbeats 1000000` only applies to the next command, not the entire file. Use `set_option ... in` for explicit scoping.

5. **`@[inline]` vs `@[always_inline]`.** `@[inline]` is a hint; the compiler may ignore it. `@[always_inline]` forces inlining.

## Beginner mental model

Think of attributes as **sticky notes on your definitions** that tell the compiler how to treat them. `@[simp]` says "use this in simplification." `@[inline]` says "copy this code into call sites for speed." Notation is **custom syntax sugar** — it lets you write math-like expressions that desugar to Lean code. Options are **knobs on the compiler** — turn them to adjust behavior for a specific section.

Coming from Rust: `@[inline]` ≈ `#[inline]`, `@[simp]` has no direct Rust equivalent (it's a proof-system feature). `notation` ≈ a limited form of `macro_rules!` for operator syntax.

## Example A — Custom notation with precedence

```lean
-- Left-associative, precedence 65 (same as +)
infixl:65 " ⊕ " => fun a b => a + b + 1

#eval 1 ⊕ 2 ⊕ 3  -- (1 ⊕ 2) ⊕ 3 = (1+2+1) + 3 + 1 = 8
```

## Example B — Scoped simp lemma

```lean
namespace MyModule

@[scoped simp] theorem myLemma : ∀ n : Nat, n + 0 = n := Nat.add_zero

example : 5 + 0 = 5 := by simp  -- OK: myLemma is in scope

end MyModule

-- Outside MyModule, myLemma is NOT in the simp set
-- (unless you `open MyModule`)
```

## Common compiler errors and how to read them

### `@[simp] attribute not a valid simp lemma`

```
invalid [simp] attribute, not a valid simp lemma
```

**Meaning:** The theorem you tagged `@[simp]` is not an equality or iff. The simplifier can only use rewriting rules.

### `maximum heartbeats exceeded`

```
(deterministic) timeout at 'whnf', maximum number of heartbeats (200000) has been reached
```

**Meaning:** Type checking exceeded the computation budget. Use `set_option maxHeartbeats 400000` to increase the limit, or simplify the definition. This often indicates a `simp` loop or expensive dependent type computation.

### `unknown attribute`

```
unknown attribute [myattr]
```

**Meaning:** You used an attribute that hasn't been defined. Check the spelling, or import the module that defines it.

## Proof perspective (brief)

Attributes are the primary way to organize proof automation in Lean and Mathlib. `@[simp]` lemmas form a convergent rewriting system — the simplifier applies them in a fixed order to normalize terms. `@[ext]` lemmas enable extensionality proofs ("to prove two functions are equal, prove they agree on all inputs"). `@[instance]` and `@[default_instance]` control type class resolution priority. Mathlib's entire proof automation ecosystem is built on tagged lemmas and tactic-facing attributes.

## Use-case cross-references

- [→ UC-08](../usecases/08-encapsulation-module-boundaries.md) — Attributes control what the simplifier sees across module boundaries.
- [→ UC-09](../usecases/09-metaprogramming-syntax-extension.md) — Notation and custom attributes extend the language.

## Source anchors

- *Theorem Proving in Lean 4* — Ch. 5 "Tactics" (simp attributes)
- Lean 4 source: `Lean.Elab.Attribute`, `Lean.Parser.Command` (notation)
- Lean 4 documentation: "Attributes" reference
