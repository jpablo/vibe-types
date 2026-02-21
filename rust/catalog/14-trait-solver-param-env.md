# Trait Solver and Parameter Environments

## What it is

The compiler solves trait obligations in a parameter environment derived from in-scope bounds.

## What constraint it enforces

**Code type-checks only when all trait obligations are provable in the current environment.**

## Minimal snippet

```rust
fn use_clone<T: Clone>(x: T) -> T {
    x.clone()
}
```

## Interaction with other features

- Underpins generic checks in `[-> catalog/05]` and `[-> catalog/06]`.
- Relevant for diagnosis in `[-> UC-07]`.

## Gotchas and limitations

- Internal solver behavior can evolve across compiler versions.

## Use-case cross-references

- `[-> UC-07]`
