# Ownership-Safe APIs

## The constraint

APIs must encode ownership transfer, borrowing, and lifetime relationships explicitly.

## Feature toolkit

- `[-> catalog/01]`
- `[-> catalog/02]`
- `[-> catalog/03]`
- `[-> catalog/10]`

## Patterns

- Pattern A: move ownership into constructors/builders.
```rust
pub struct Job(String);
impl Job {
    pub fn new(payload: String) -> Self { Self(payload) }
}
```
- Pattern B: borrow for read-only views with explicit lifetime ties.
```rust
fn head<'a>(s: &'a str) -> &'a str {
    s.split(':').next().unwrap_or(s)
}
```

## Tradeoffs

- Signatures become more explicit, but call sites gain predictable ownership behavior.
- Borrowing minimizes allocations, while move-based APIs simplify lifecycle ownership.

## When to use which feature

- Prefer borrowing for non-owning access.
- Prefer ownership transfer for resource handoff.

## Source anchors

- `book/src/ch04-01-what-is-ownership.md`
- `book/src/ch04-02-references-and-borrowing.md`
- `book/src/ch10-03-lifetime-syntax.md`
- `rust-by-example/src/scope/move.md`
- `rust-by-example/src/scope/borrow.md`
