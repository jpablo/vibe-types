# Rust Book Findings

## Scope

- Source: `/Users/jpablo/GitHub/book`
- Snapshot: `05d114287b7d` (2026-02-03)

## Priority Files

- `src/ch03-01-variables-and-mutability.md`
- `src/ch03-02-data-types.md`
- `src/ch04-01-what-is-ownership.md`
- `src/ch04-02-references-and-borrowing.md`
- `src/ch04-03-slices.md`
- `src/ch10-00-generics.md`
- `src/ch10-01-syntax.md`
- `src/ch10-02-traits.md`
- `src/ch10-03-lifetime-syntax.md`
- `src/ch15-00-smart-pointers.md`
- `src/ch15-03-drop.md`
- `src/ch15-05-interior-mutability.md`
- `src/ch16-04-extensible-concurrency-sync-and-send.md`
- `src/ch17-05-traits-for-async.md`
- `src/ch18-02-trait-objects.md`
- `src/ch20-02-advanced-traits.md`
- `src/ch20-03-advanced-types.md`
- `src/appendix-03-derivable-traits.md`

## Extraction Order

1. Ch03/Ch04 foundations: ownership, borrowing, data shape.
2. Ch10 generics/traits/lifetimes: main type-system constraints.
3. Ch15 memory abstractions: smart pointers and drop behavior.
4. Ch16/Ch17 concurrency traits and async type constraints.
5. Ch18/Ch20 advanced traits and advanced type constructs.

## Candidate Feature Buckets

- Ownership and borrowing invariants.
- Generic type parameters and trait bounds.
- Lifetime annotations and elision.
- Trait objects and associated types.
- Smart pointers and interior mutability.
- Marker traits (`Send`, `Sync`) and async trait interactions.
- Advanced type forms (aliases, newtypes, never type, DST notes).

## Candidate Use-Case Buckets

- API design with compile-time capability constraints.
- Safe shared/mutable access patterns enforced by types.
- Thread-safe abstractions with marker traits.
- Dynamic extensibility through trait objects.
- Ergonomic, type-safe wrappers and aliases.

## Gaps and Risks

- Some newer language features are not covered in depth.
- Compiler-internal semantics are intentionally abstracted.
- Async/pinning sections are practical, not fully formal.
