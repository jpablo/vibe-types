# Ownership-Safe APIs

## The constraint

APIs must encode ownership transfer, borrowing, and lifetime relationships explicitly.

## Feature toolkit

- `[-> catalog/01]`
- `[-> catalog/02]`
- `[-> catalog/03]`
- `[-> catalog/10]`

## Patterns

- Pattern A: move-based constructors and builders.
- Pattern B: borrow-based read APIs with explicit lifetimes.

## Tradeoffs

- Signatures become more explicit but safer.

## When to use which feature

- Prefer borrowing for non-owning access.
- Prefer ownership transfer for resource handoff.
