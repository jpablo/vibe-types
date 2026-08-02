# Auto-Bound Implicit and Instance Arguments

> **Since:** Lean 4 (stable)

## What it is

Lean supports three kinds of implicit arguments that the compiler fills in automatically:

1. **Implicit arguments** (`{α : Type}`) — inferred from usage context via unification. You write `{α : Type}` in the signature, and the compiler figures out `α` from how you use it.
2. **Strict implicit arguments** (`⦃α : Type⦄`) — like implicit, but only filled in when a later explicit argument is provided.
3. **Instance arguments** (`[inst : Add α]`) — resolved via type class instance search [→ T05](T05-type-classes.md). The compiler finds a matching `instance` declaration.

Additionally, **auto-bound implicit** is a convenience: if a declaration's signature mentions an identifier that is not bound anywhere, Lean automatically binds it as an implicit argument. Casing is irrelevant — with `relaxedAutoImplicit` (on by default) *any* unbound identifier qualifies, so `def f (xs : List Foo) := xs.length` auto-binds `{Foo : Type u_1}` exactly the way `α` would. This removes boilerplate `{α : Type}` declarations; turn the whole mechanism off per file or per declaration with `set_option autoImplicit false`.

## What constraint it enforces

**The compiler must be able to infer implicit arguments and resolve instance arguments; failure to do so is a compile error.**

More specifically:

- **Implicit inference.** If the compiler can't determine an implicit argument from context, it reports an error. You must provide enough information for unification.
- **Instance resolution.** Instance arguments require a matching type class instance. Missing instances are compile errors, not runtime failures.
- **Auto-binding is scoped.** Auto-bound implicits only apply when a variable is otherwise undeclared. If you declare it explicitly, auto-binding doesn't fire.

## Minimal snippet

```lean
-- Auto-bound implicit: `α` is not declared, so Lean binds it — and generalizes
-- the universe as well, adding a level parameter alongside `{α : Type u_1}`.
def head? (xs : List α) : Option α :=
  xs.head?

set_option pp.universes true in
#check @head?
-- @head?.{u_1} : {α : Type u_1} → List.{u_1} α → Option.{u_1} α

-- NOT equivalent: writing `{α : Type}` pins the definition to `Type 0`.
def headMono {α : Type} (xs : List α) : Option α :=
  xs.head?

set_option pp.universes true in
#check @headMono
-- @headMono : {α : Type} → List.{0} α → Option.{0} α

-- The actual equivalent spells the level out with a `.{u}` binder:
def headPoly.{u} {α : Type u} (xs : List α) : Option α :=
  xs.head?

set_option pp.universes true in
#check @headPoly
-- @headPoly.{u_1} : {α : Type u_1} → List.{u_1} α → Option.{u_1} α

-- Instance argument: [BEq α] required
def contains [BEq α] (xs : List α) (x : α) : Bool :=
  xs.any (· == x)

#eval contains [1, 2, 3] 2  -- OK: BEq Nat instance found
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type Classes** [→ T05](T05-type-classes.md) | Instance arguments are the mechanism for passing type class evidence. `[Monad m]` ≈ Rust's `M: Monad`. |
| **Dependent Types** [→ T09](T09-dependent-types.md) | Implicit arguments can be values, not just types — e.g., `{n : Nat}` can be inferred from a `Vector α n` argument. |
| **Universes** [→ T35](T35-universes-kinds.md) | Universe levels are implicit, but they are *not* term binders — there is no `{u : Level}` syntax. Levels come from `universe u`, from the `def f.{u}` suffix, or from auto-bound implicits; supply one explicitly at a use site with `f.{0}`. |
| **Coercions** [→ T18](T18-conversions-coercions.md) | The compiler tries coercions when filling implicit arguments, expanding the search space. |

## Gotchas and limitations

1. **Auto-bound implicits can over-generalize.** Writing `def f (x : α) := ...` makes `α` implicit. If you wanted a concrete type, you accidentally made the function polymorphic. Use explicit annotations when you want a specific type.

2. **`@` disables all implicits.** Prefixing a function with `@` turns off implicit argument insertion, letting you pass everything explicitly. Useful for debugging inference failures.

3. **Instance argument placement.** The rule "`[BEq α]` must appear after `α` is bound" only holds with auto-binding switched off:

   ```lean
   set_option autoImplicit false in
   def bad [Ord α] (x : α) : List α := [x]
   -- error: Unknown identifier `α`
   --   Note: It is not possible to treat `α` as an implicitly bound variable here
   --   because the `autoImplicit` option is set to `false`.
   ```

   With `autoImplicit` on (the default, and what Example A below relies on) `[Ord α]` may be the *first* binder: Lean auto-binds `α` and hoists it in front of the instance argument, yielding `{α : Type u_1} → [Ord α] → …`.

4. **`variable` vs auto-bound.** `variable {α : Type} [BEq α]` at the section level declares implicits for all subsequent definitions. This is cleaner than repeating them.

5. **Named instance arguments.** `[inst : BEq α]` gives the instance a name `inst` you can reference. Without a name, you can still access it via the class methods.

## Beginner mental model

Think of implicit arguments as **things the compiler figures out for you**. When you write `List α` in a function signature without declaring `α`, the compiler says "okay, `α` must be a type — I'll add `{α : Type}` for you." When you write `[BEq α]`, the compiler says "I need a `BEq` implementation for `α` — I'll look it up." If either search fails, you get a clear error.

Coming from Rust: `{α : Type}` ≈ `<T>` (inferred generic), `[BEq α]` ≈ `T: Eq` (trait bound). The difference is Lean's inference is more aggressive — it auto-binds variables you didn't explicitly declare.

## Example A — Multiple implicit and instance arguments

```lean
def sortedInsert [Ord α] (x : α) : List α → List α
  | []      => [x]
  | y :: ys =>
    if Ord.compare x y |>.isLT then x :: y :: ys
    else y :: sortedInsert x ys
-- α is auto-bound implicit; [Ord α] is an instance argument
```

## Example B — Explicit override with @

```lean
def myId {α : Type} (x : α) : α := x

-- Normal call: α inferred
#eval myId 42  -- α = Nat, inferred

-- Explicit call: provide α manually
#eval @myId Nat 42  -- same result, but α given explicitly
```

## Common compiler errors and how to read them

### `don't know how to synthesize placeholder`

```
don't know how to synthesize placeholder
context:
  ⊢ Type ?u
```

**Meaning:** The compiler can't infer an implicit argument. Provide more type annotations at the call site, or use `@` to pass it explicitly.

### `failed to synthesize instance of type class`

```lean
structure MyCustomType where
  x : Nat

#eval (MyCustomType.mk 1) == (MyCustomType.mk 2)
-- error: failed to synthesize instance of type class BEq MyCustomType
```

```
error(lean.synthInstanceFailed): failed to synthesize instance of type class
  BEq MyCustomType

Hint: Adding the command `deriving instance BEq for MyCustomType` may allow Lean to derive the missing instance.
```

**Meaning:** An instance argument requires an instance that doesn't exist. Take the hint (`deriving instance BEq for MyCustomType`, or `deriving BEq` on the declaration), write the instance by hand, or pass one explicitly with `@`.

### ``Variable name `α` is not explicitly referenced`` — a *warning*, not an error

```
Variable name `α` is not explicitly referenced.

The binding can be removed (if unused) or named `_` (if used implicitly).

Note: This linter can be disabled with `set_option linter.unusedVariables false`
```

**Meaning:** You bound `{α : Type}` (or any other binder) and never mentioned it by name. The `unusedVariables` linter emits this as a **warning** — the declaration still compiles. Remove the binder, rename it to `_`, or disable the linter. There is no `unused variable 'α'` error in Lean 4.

## Proof perspective (brief)

Instance arguments are the mechanism behind Lean's automation. When a tactic like `simp` needs to know that a type has decidable equality, it searches for `[DecidableEq α]` via instance resolution — that part really is the same machinery that powers `[Add α]`. Simp lemmas are *not*: there is no `SimpLemmas` class, and `@[simp]` does not register an instance. The attribute writes into an environment extension (`Lean.Meta.simpExtension`) whose payload is a plain `SimpTheorems` structure holding discrimination trees, and the simplifier queries that tree directly. Two distinct mechanisms — instance synthesis for evidence, environment extensions for lemma databases — sit side by side in the automation stack.

## Use-case cross-references

- [→ UC-06](../usecases/UC04-generic-constraints.md) — Instance arguments constrain generic code to types with required capabilities.

## Source anchors

- *Functional Programming in Lean* — "Implicit Arguments"
- *Theorem Proving in Lean 4* — Ch. 2 "Dependent Type Theory" (implicit arguments)
- Lean 4 source: `Lean.Elab.Term` (implicit argument elaboration)
