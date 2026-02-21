# Value-Level Invariants with Types

## The constraint

Encode numeric/value invariants in types so invalid values are rejected early.

## Feature toolkit

- `[-> catalog/12]`
- `[-> catalog/05]`

## Patterns

- Pattern A: const-generic array sizes.
- Pattern B: const-parameterized wrappers for bounded shapes.

## Tradeoffs

- Strong guarantees with potentially more complex type signatures.

## When to use which feature

- Use const generics when invariant values are part of the type identity.
- Keep bounds minimal to preserve API ergonomics.
