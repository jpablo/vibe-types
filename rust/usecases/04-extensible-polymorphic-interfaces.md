# Extensible Polymorphic Interfaces

## The constraint

Allow extension points while preserving compile-time guarantees on behavior.

## Feature toolkit

- `[-> catalog/06]`
- `[-> catalog/08]`

## Patterns

- Pattern A: static dispatch via generics.
- Pattern B: runtime extension with `dyn Trait`.

## Tradeoffs

- Static dispatch is faster and stricter; dynamic dispatch is more flexible.

## When to use which feature

- Prefer generics in closed, performance-critical paths.
- Prefer trait objects for plugin-like open sets.
