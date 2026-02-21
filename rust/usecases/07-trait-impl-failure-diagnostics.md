# Trait Impl Failure Diagnostics

## The constraint

Understand and resolve compile-time failures from missing/invalid trait implementations.

## Feature toolkit

- `[-> catalog/13]`
- `[-> catalog/14]`
- `[-> catalog/06]`

## Patterns

- Pattern A: adding missing bounds to satisfy obligations.
- Pattern B: redesigning impl placement to satisfy orphan/coherence rules.

## Tradeoffs

- Diagnostics may require understanding compiler-internal terminology.

## When to use which feature

- Use coherence rules when impl legality is unclear.
- Use solver/param-env reasoning for complex generic errors.
