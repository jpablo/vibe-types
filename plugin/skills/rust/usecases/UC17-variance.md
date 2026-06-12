# Variance (Implicit Rules + PhantomData)

## The constraint

Variance determines whether a subtype can stand in for a supertype through a type constructor. Rust subtyping is essentially lifetime-only — `&'static str` is a subtype of `&'a str` because `'static` outlives `'a` — so variance governs when `Container<&'static str>` can be used where `Container<&'a str>` is expected. The compiler infers variance from how type and lifetime parameters are used in fields. `PhantomData` lets authors control variance for parameters that do not appear in physical fields.

## Feature toolkit

- `[-> T08](../catalog/T08-variance-subtyping.md)`
- `[-> T27](../catalog/T27-erased-phantom.md)`
- `[-> T48](../catalog/T48-lifetimes.md)`

## Patterns

- Pattern A: covariance — inferred from immutable usage.
```rust
// Vec<T> is covariant over T; &'a T is covariant over 'a and T.
fn print_items<'a>(items: &Vec<&'a str>) {
    for item in items {
        println!("{item}");
    }
}

let static_items: Vec<&'static str> = vec!["hello", "world"];
// Vec<&'static str> can be used where Vec<&'a str> is expected (covariance)
print_items(&static_items);
```

- Pattern B: invariance — inferred from mutable usage.
```rust
// &'a mut T is invariant over T.
fn fill<'a>(buf: &mut Vec<&'a str>, item: &'a str) {
    buf.push(item);
}
// Cannot pass &mut Vec<&'static str> where &mut Vec<&'a str> is expected —
// &mut T is invariant in T. If it were allowed, `fill` could push a
// short-lived &'a str into a Vec<&'static str>, leaving a dangling reference.
```

- Pattern C: `PhantomData` to mark unused type parameters.
```rust
use std::marker::PhantomData;

struct Deserializer<T> {
    data: Vec<u8>,
    _marker: PhantomData<fn() -> T>, // covariant over T, like PhantomData<T>,
                                     // but without pretending to own a T
                                     // (no dropck or Send/Sync baggage)
}
```

- Pattern D: `PhantomData` for lifetime-dependent types.
```rust
use std::marker::PhantomData;

struct BorrowedSlice<'a, T> {
    ptr: *const T,
    len: usize,
    _lifetime: PhantomData<&'a T>, // ties the raw pointer to lifetime 'a
}
```

- Pattern E: `PhantomData<fn(T) -> T>` for invariance.
```rust
use std::marker::PhantomData;

struct InvariantId<T> {
    id: u64,
    _marker: PhantomData<fn(T) -> T>, // invariant over T
}
// InvariantId<&'static str> cannot be used where InvariantId<&'a str> is expected
```

## Tradeoffs

- Compiler-inferred variance is correct by construction but invisible — developers must reason about it from field types.
- `PhantomData` has zero runtime cost but adds a field that exists only to guide the type system.
- Incorrect variance (e.g., forcing covariance on a mutable container) can lead to unsoundness in `unsafe` code.

## When to use which feature

- Let the compiler infer variance from field types in most cases — this is the default and correct path.
- Use `PhantomData` when a struct has a type parameter that does not appear in any field (e.g., type-state patterns, raw-pointer wrappers); for producer-only parameters prefer `PhantomData<fn() -> T>` over `PhantomData<T>` — same covariance, no owns-`T` drop-check or auto-trait implications.
- Use `PhantomData<fn(T) -> T>` when the type parameter must be invariant.
- Use `PhantomData<&'a T>` to tie a raw pointer to a borrowed lifetime.

## Source anchors

- `reference/src/subtyping.md`
- `nomicon/src/subtyping.md`
- `nomicon/src/phantom-data.md`
- `std::marker::PhantomData` API docs
