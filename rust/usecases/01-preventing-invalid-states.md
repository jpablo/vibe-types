# Preventing Invalid States

## The constraint

Represent only valid domain states in types so invalid combinations cannot compile.

## Feature toolkit

- `[-> catalog/04]`
- `[-> catalog/09]`

## Patterns

- Pattern A: enum variants for exclusive states.
- Pattern B: newtypes for constrained identifiers.

## Tradeoffs

- Better safety at the cost of extra type definitions.

## When to use which feature

- Use enums for closed state spaces.
- Use newtypes for stronger boundaries around primitives.
