# Variance (Implicit Rules + PhantomData)

## The constraint

Variance determines whether `Container<Sub>` can be used where `Container<Super>` is expected (and vice versa). In Rust, the compiler infers variance from how type parameters are used in fields. `PhantomData<T>` lets authors control variance for type parameters that do not appear in physical fields.

## Feature toolkit

- `[-> T08](../catalog/T08-variance-subtyping.md)`
- `[-> T27](../catalog/T27-erased-phantom.md)`
- `[-> T48](../catalog/T48-lifetimes.md)`

## Patterns

- Pattern A: covariance — inferred from immutable usage.
```rust
// Vec<T> is covariant over T.
// &'a T is covariant over 'a and T.
fn print_items(items: &[&str]) {
    for item in items {
        println!("{item}");
    }
}

let owned: &str = "hello";
// &'static str can be used where &'a str is expected (covariant over lifetime)
```

- Pattern B: invariance — inferred from mutable usage.
```rust
// &'a mut T is invariant over T.
fn fill(buf: &mut Vec<String>, item: String) {
    buf.push(item);
}
// Cannot pass &mut Vec<&str> where &mut Vec<String> is expected — invariant.
```

- Pattern C: `PhantomData` to mark unused type parameters.
```rust
use std::marker::PhantomData;

struct Deserializer<T> {
    data: Vec<u8>,
    _marker: PhantomData<T>, // makes Deserializer<T> covariant over T
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
// InvariantId<Sub> cannot be used where InvariantId<Super> is expected
```

## Tradeoffs

- Compiler-inferred variance is correct by construction but invisible — developers must reason about it from field types.
- `PhantomData` has zero runtime cost but adds a field that exists only to guide the type system.
- Incorrect variance (e.g., forcing covariance on a mutable container) can lead to unsoundness in `unsafe` code.

## When to use which feature

- Let the compiler infer variance from field types in most cases — this is the default and correct path.
- Use `PhantomData<T>` when a struct has a type parameter that does not appear in any field (e.g., type-state patterns, raw-pointer wrappers).
- Use `PhantomData<fn(T) -> T>` when the type parameter must be invariant.
- Use `PhantomData<&'a T>` to tie a raw pointer to a borrowed lifetime.

## Source anchors

- `reference/src/subtyping.md`
- `nomicon/src/subtyping.md`
- `nomicon/src/phantom-data.md`
- `std::marker::PhantomData` API docs
