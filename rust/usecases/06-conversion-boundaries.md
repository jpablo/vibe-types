# Conversion Boundaries

## The constraint

Conversions across domain boundaries should be explicit and type-checked.

## Feature toolkit

- `[-> catalog/09]`
- `[-> catalog/05]`

## Patterns

- Pattern A: `TryFrom` for fallible conversion.
- Pattern B: generic conversion helpers with trait bounds.

## Tradeoffs

- Explicit conversion code is more verbose but safer.

## When to use which feature

- Use `TryFrom` when failure is meaningful.
- Use `From` for guaranteed lossless conversions.
