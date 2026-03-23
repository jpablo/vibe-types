# Trait Impl Failure Diagnostics

## The constraint

Understand trait-impl failures as two checks: coherence/orphan legality and solver proof obligations in the active `ParamEnv`.

## Feature toolkit

- `[-> T25](T25-coherence-orphan.md)`
- `[-> T37](T37-trait-solver.md)`
- `[-> T05](T05-type-classes.md)`

## Patterns

- Pattern A: add missing bounds explicitly even when they are implied, because the `ParamEnv` elaborates supertraits (e.g., `trait Alias: Clone {}` gives you `Clone` inside the env). Keep the diagnostic text in mind when the solver only mentions the assumption. Example:
```rust
trait Alias: Clone {}
fn clone_alias<T: Alias>(value: T) -> T {
    value.clone()
}
```
- Pattern B: move impl legality into your crate with a newtype/local trait so the coherence/orphan rules see a local type or trait.
```rust
struct MyVec(Vec<i32>); // local type, legal impl target
```

## Tradeoffs

- Diagnostics can reference elaborated obligations not written explicitly, which makes errors harder to map back to source bounds.
- Adding bounds to satisfy solver requirements can overconstrain callers; newtypes/local traits may preserve flexibility.

## When to use which feature

- Use coherence/orphan reasoning when diagnostics mention foreign trait/type impl attempts.
- Use solver/`ParamEnv` reasoning when diagnostics mention unsatisfied obligations in generic code.

## Source anchors

- `rust/src/doc/reference/src/items/implementations.md`
- `rust/src/doc/reference/src/trait-bounds.md`
- `rust/src/doc/rustc-dev-guide/src/coherence.md`
- `rust/src/doc/rustc-dev-guide/src/typing-parameter-envs.md`
- `rust/src/doc/rustc-dev-guide/src/solve/trait-solving.md`
