# Trait Solver and Parameter Environments

## What it is

The compiler solves trait obligations in a parameter environment derived from in-scope bounds.

## What constraint it enforces

**A trait obligation is accepted only when the solver can prove it in the active `ParamEnv` built from in-scope bounds.**

## Minimal snippet

```rust
trait Alias: Clone {}

fn promote<T: Alias>(value: T) -> T {
    value.clone() // ParamEnv elaborates `Alias: Clone`, so the Clone goal is provable.
}
```

## Interaction with other features

- Underpins generic checks in `[-> catalog/05]` and `[-> catalog/06]`.
- Relevant for diagnosis in `[-> UC-07]`.

## Gotchas and limitations

- `ParamEnv` elaboration can add implied/supertrait assumptions, so diagnostics may mention bounds you did not write directly.
- Proving a goal with the wrong environment can fail even when a matching impl exists.

## Use-case cross-references

- `[-> UC-07]`

## Source anchors

- `rust/src/doc/reference/src/trait-bounds.md`
- `rust/src/doc/reference/src/type-system.md`
- `rust/src/doc/rustc-dev-guide/src/typing-parameter-envs.md`
- `rust/src/doc/rustc-dev-guide/src/solve/trait-solving.md`
