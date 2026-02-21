# Generic Capability Constraints

## The constraint

Generic APIs should accept only types that satisfy required capabilities.

## Feature toolkit

- `[-> catalog/05]`
- `[-> catalog/06]`
- `[-> catalog/07]`

## Patterns

- Pattern A: trait bounds in function signatures.
- Pattern B: associated types to tie related outputs.

## Tradeoffs

- Stronger guarantees versus steeper API complexity.

## When to use which feature

- Start with simple trait bounds.
- Use associated types when relationships must stay coherent.
