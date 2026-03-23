# Equality and Comparison Safety

Since: Rust 1.0

## What it is

In Rust, equality comparison (`==`, `!=`) and ordering (`<`, `>`, `<=`, `>=`) are **opt-in**. A type cannot be compared for equality unless it implements `PartialEq`, and cannot be ordered unless it implements `PartialOrd`. The stronger variants `Eq` (full equivalence) and `Ord` (total ordering) further refine the contract. There is no universal `==` that works on any two values -- and crucially, **you cannot compare values of unrelated types** unless an explicit cross-type `PartialEq` implementation exists.

`#[derive(PartialEq)]` generates field-by-field comparison. `#[derive(Eq)]` is a marker asserting that the equality is reflexive (i.e., `x == x` is always `true`), which is not the case for `f64` (`NaN != NaN`). Similarly, `#[derive(PartialOrd)]` generates lexicographic ordering by field declaration order, and `Ord` asserts total ordering.

## What constraint it enforces

**Types must explicitly opt into comparison, and the compiler rejects comparisons between types that lack the appropriate trait implementation.**

- `a == b` requires `PartialEq<RHS>` to be implemented. Without it, the code does not compile.
- `HashMap` keys require `Eq + Hash`; `BTreeMap` keys require `Ord`. The compiler enforces these bounds.
- No implicit coercion for comparison: `42_u32 == 42_u64` does not compile because `u32` and `u64` are different types.

## Minimal snippet

```rust
#[derive(PartialEq, Eq)]
struct UserId(u64);

#[derive(PartialEq, Eq)]
struct OrderId(u64);

fn main() {
    let u = UserId(1);
    let o = OrderId(1);
    // u == o;    // error[E0308]: mismatched types
    assert_eq!(u, UserId(1));  // OK -- same type
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Derive macros** [-> catalog/T06](T06-derivation.md) | `#[derive(PartialEq, Eq, PartialOrd, Ord)]` is the standard way to opt into comparison. The compiler generates field-by-field logic. |
| **Newtypes** [-> catalog/T03](T03-newtypes-opaque.md) | Two newtypes wrapping the same inner type are not comparable unless you explicitly implement cross-type `PartialEq` -- which you almost never should. |
| **Traits** [-> catalog/T05](T05-type-classes.md) | `PartialEq`, `Eq`, `PartialOrd`, `Ord` are traits. Generic bounds like `T: Eq + Hash` gate collection membership. |
| **Generics** [-> catalog/T04](T04-generics-bounds.md) | Generic code that needs `==` must declare `T: PartialEq`. This makes comparison requirements explicit in the API. |

## Gotchas and limitations

1. **`f32`/`f64` implement `PartialEq` but not `Eq`.** Because `NaN != NaN`, floats cannot satisfy the reflexivity requirement of `Eq`. A struct containing a float cannot derive `Eq` or be used as a `HashMap` key.

2. **Derived `PartialOrd` uses field declaration order.** If the first field is a name and the second is a priority, derived ordering sorts alphabetically by name. Reorder fields or implement manually.

3. **`PartialEq` and `Hash` must agree.** If `a == b`, then `hash(a)` must equal `hash(b)`. Deriving both from the same set of fields guarantees this, but a manual impl that skips a field in one but not the other breaks `HashMap`.

4. **No cross-type equality by default.** `String == &str` works only because the standard library provides `impl PartialEq<&str> for String`. Your own types have no such magic.

5. **`assert_eq!` requires `Debug + PartialEq`.** If you want to use `assert_eq!` in tests, both traits must be implemented. Missing `Debug` produces a confusing error about `PartialEq`.

## Beginner mental model

Think of equality as a **permission slip**. In many languages every object can be compared with `==`, even when the comparison is meaningless. In Rust, you must sign the permission slip (`#[derive(PartialEq)]`) before the compiler lets you compare. If two types are different -- even if they contain the same data -- the compiler refuses to compare them unless you explicitly allow it.

## Example A -- Using Eq + Hash for HashMap keys

```rust
use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct CacheKey {
    endpoint: String,
    version: u32,
}

fn main() {
    let mut cache = HashMap::new();
    let key = CacheKey { endpoint: "/api".into(), version: 2 };
    cache.insert(key.clone(), "response body");
    println!("{:?}", cache.get(&key));  // Some("response body")
}
```

## Example B -- Manual PartialEq for custom logic

```rust
struct CaseInsensitive(String);

impl PartialEq for CaseInsensitive {
    fn eq(&self, other: &Self) -> bool {
        self.0.eq_ignore_ascii_case(&other.0)
    }
}
impl Eq for CaseInsensitive {}

fn main() {
    let a = CaseInsensitive("Hello".into());
    let b = CaseInsensitive("hello".into());
    assert_eq!(a, b);  // passes -- case insensitive
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Opt-in equality prevents accidental comparison between semantically unrelated types.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Generic APIs declare comparison bounds explicitly, making requirements clear.

## Source anchors

- `book/src/appendix-03-derivable-traits.md`
- `rust-reference/src/expressions/operator-expr.md` -- comparison operators
- `std::cmp` module documentation
- `api-guidelines/src/interoperability.md` -- C-COMMON-TRAITS
