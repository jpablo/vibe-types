# Compile-Time Concurrency Constraints

## The constraint

Threaded code should only compile when transfer and sharing are safe.

## Feature toolkit

- `[-> catalog/11]`
- `[-> catalog/06]`
- `[-> catalog/10]`

## Patterns

- Pattern A: `Send`-bounded worker APIs.
- Pattern B: shared ownership wrappers with explicit synchronization.

## Tradeoffs

- Safety constraints may require additional wrapper types.

## When to use which feature

- Use `Send`/`Sync` bounds at API boundaries.
- Choose pointer/wrapper types based on sharing semantics.
