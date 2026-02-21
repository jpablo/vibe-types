# Trait Impl Failure Diagnostics

## The constraint

Understand and resolve compile-time failures from missing/invalid trait implementations.

## Feature toolkit

- `[-> catalog/13]`
- `[-> catalog/14]`
- `[-> catalog/06]`

## Patterns

- Pattern A: add missing bounds to satisfy obligations.
```rust
fn clone_it<T: Clone>(x: T) -> T { x.clone() }
```
- Pattern B: move impl legality into your crate with a newtype.
```rust
struct MyVec(Vec<i32>); // local type, legal impl target
```

## Tradeoffs

- Diagnostics may require understanding compiler-internal terminology.
- The shortest fix (adding a bound) can overconstrain APIs; redesign may be better.

## When to use which feature

- Use coherence rules when impl legality is unclear.
- Use solver/param-env reasoning for complex generic errors.

## Source anchors

- `book/src/ch10-02-traits.md`
- `rust/src/doc/rustc-dev-guide/src/coherence.md`
- `rust/src/doc/rustc-dev-guide/src/type-inference.md`
- `rust/src/doc/rustc-dev-guide/src/typing-parameter-envs.md`
