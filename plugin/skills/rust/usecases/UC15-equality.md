# Equality Opt-In

## The constraint

Types are not comparable by default. Equality requires explicitly deriving or implementing `PartialEq` (and optionally `Eq`). The compiler rejects `==` on types that lack these traits, preventing accidental comparisons between unrelated types.

## Feature toolkit

- `[-> T20](../catalog/T20-equality-safety.md)`
- `[-> T06](../catalog/T06-derivation.md)`
- `[-> T05](../catalog/T05-type-classes.md)`

## Patterns

- Pattern A: `derive(PartialEq)` for structural equality.
```rust
#[derive(PartialEq, Debug)]
struct Point {
    x: f64,
    y: f64,
}

assert_eq!(Point { x: 1.0, y: 2.0 }, Point { x: 1.0, y: 2.0 }); // OK
// Point { x: 0.0, y: 0.0 } == 42;  // error: mismatched types
```

- Pattern B: `Eq` for total equality (excludes `NaN`-like values).
```rust
#[derive(PartialEq, Eq, Hash)]
struct UserId(u64);

// Eq enables use as HashMap key
use std::collections::HashMap;
let mut users: HashMap<UserId, String> = HashMap::new();
users.insert(UserId(1), "Alice".into());
```

- Pattern C: custom `PartialEq` for domain-specific comparison.
```rust
struct CaseInsensitive(String);

impl PartialEq for CaseInsensitive {
    fn eq(&self, other: &Self) -> bool {
        self.0.eq_ignore_ascii_case(&other.0)
    }
}

assert!(CaseInsensitive("Hello".into()) == CaseInsensitive("hello".into()));
```

- Pattern D: no cross-type comparison by default.
```rust
#[derive(PartialEq)]
struct Meters(f64);

#[derive(PartialEq)]
struct Feet(f64);

// Meters(1.0) == Feet(3.28);  // error: mismatched types
// Must implement PartialEq<Feet> for Meters explicitly if desired
```

## Tradeoffs

- Opt-in equality prevents accidental cross-type comparisons but requires boilerplate (`derive` or manual `impl`).
- `PartialEq` without `Eq` supports floating-point semantics (`NaN != NaN`) but excludes the type from `HashMap` keys.
- Custom equality impls must maintain reflexivity, symmetry, and transitivity manually.

## When to use which feature

- Derive `PartialEq` on most data types for structural comparison.
- Add `Eq` when the type has total equality (no `NaN`) and may be used as a hash key.
- Implement `PartialEq` manually when comparison needs domain logic (case-insensitive strings, epsilon-based floats).
- Keep types incomparable when cross-comparison would be a logic error (different units, different ID domains).

## Source anchors

- `book/src/ch05-02-example-structs.md` (deriving traits)
- `book/src/appendix-03-derivable-traits.md`
- `rust-by-example/src/trait/derive.md`
- `std::cmp::PartialEq` / `std::cmp::Eq` API docs
