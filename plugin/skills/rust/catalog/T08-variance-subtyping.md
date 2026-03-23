# Variance & Subtyping (Implicit Rules)

Since: Rust 1.0 (rules are implicit and inferred by the compiler)

## What it is

Rust does not have variance annotations (`+T`/`-T` like Scala) or explicit subtyping declarations. Instead, the compiler **infers variance** from the structure of each type. Rust's only form of subtyping is **lifetime subtyping**: `'long: 'short` means a longer lifetime can be used where a shorter one is expected.

Variance describes how a generic type `F<T>` relates to its type parameter when subtyping is involved:

- **Covariant** -- if `'a: 'b`, then `F<'a>` can be used where `F<'b>` is expected. Example: `&'a T` is covariant in `'a`.
- **Contravariant** -- if `'a: 'b`, then `F<'b>` can be used where `F<'a>` is expected. Example: `fn(&'a T)` is contravariant in `'a`.
- **Invariant** -- no substitution is allowed; `'a` and `'b` must be exactly the same. Example: `&'a mut T` is invariant in `T`.

`PhantomData<T>` [-> catalog/T27](T27-erased-phantom.md) is the primary tool for controlling variance when a type parameter is not used directly in a field. `PhantomData<T>` behaves like owning a `T` (covariant in `T`). `PhantomData<fn(T)>` makes the type contravariant in `T`. `PhantomData<fn(T) -> T>` makes it invariant.

## What constraint it enforces

**The compiler prevents lifetime and type substitutions that would create dangling references or unsound aliasing, even when the relationships are implicit.**

- A `&'a mut T` cannot be widened to a `&'b mut T` when `T` contains a lifetime, because doing so could create aliased mutable references.
- Variance errors surface as lifetime mismatch errors, often confusing beginners who do not realize variance is the underlying cause.
- Incorrect variance in unsafe abstractions (e.g., raw pointer wrappers) can lead to unsoundness unless corrected with `PhantomData`.

## Minimal snippet

```rust
use std::marker::PhantomData;

// Covariant in 'a (like &'a T)
struct Ref<'a, T> {
    ptr: *const T,
    _marker: PhantomData<&'a T>,
}

// Invariant in T (like &'a mut T)
struct MutRef<'a, T> {
    ptr: *mut T,
    _marker: PhantomData<&'a mut T>,
}

fn covariant_ok<'long: 'short, 'short>(r: Ref<'long, i32>) -> Ref<'short, i32> {
    r  // OK -- Ref is covariant in 'a, 'long: 'short
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **PhantomData** [-> catalog/T27](T27-erased-phantom.md) | `PhantomData` is the primary mechanism for declaring variance when raw pointers or other opaque representations are used. |
| **Lifetimes** [-> catalog/T48](T48-lifetimes.md) | Lifetime subtyping (`'a: 'b`) is the only form of subtyping in Rust. Variance describes how generic types propagate this relationship. |
| **Borrowing** [-> catalog/T11](T11-borrowing-mutability.md) | `&T` is covariant in both `T` and its lifetime. `&mut T` is covariant in its lifetime but **invariant** in `T` to prevent aliasing. |
| **Trait objects** [-> catalog/T36](T36-trait-objects.md) | `dyn Trait + 'a` is covariant in `'a`. Trait objects interact with variance through their lifetime bounds. |
| **Smart pointers** [-> catalog/T24](T24-smart-pointers.md) | `Box<T>` is covariant in `T`. `Cell<T>` and `UnsafeCell<T>` are invariant in `T` because they allow interior mutation. |

## Gotchas and limitations

1. **Variance errors appear as lifetime errors.** The compiler does not say "variance mismatch." Instead you get messages like "lifetime `'a` does not live long enough." Understanding variance helps decode these errors.

2. **`&mut T` is invariant in `T`.** This means you cannot cast `&mut Vec<&'long str>` to `&mut Vec<&'short str>`, even though `&'long str` outlives `&'short str`. This prevents an aliasing hole where the shorter-lived reference could be inserted into a container expecting longer-lived ones.

3. **`UnsafeCell` forces invariance.** Any type containing `UnsafeCell<T>` (which includes `Cell`, `RefCell`, `Mutex`, etc.) is invariant in `T`. This is necessary because interior mutability could allow writes through shared references.

4. **Raw pointers have no variance by default.** `*const T` and `*mut T` do not carry ownership or borrowing semantics, so the compiler does not infer variance from them alone. You must add `PhantomData` to declare the intended variance.

5. **No explicit variance syntax.** Unlike Scala's `class Foo[+T]` or C#'s `in`/`out`, Rust has no way to annotate variance directly. It is always inferred from fields. This makes it harder to communicate intent; comments and `PhantomData` are the only tools.

## Beginner mental model

Think of variance as **compatibility rules for containers**. A box of `'long`-lived items can be used where a box of `'short`-lived items is expected (covariant), because the items live longer than needed. But a *mutable* box is different: if you could treat a mutable box of long-lived items as a mutable box of short-lived items, someone might put a short-lived item in, violating the original promise. So mutable containers are invariant -- no substitution allowed.

## Example A -- Why &mut T is invariant in T

```rust
fn invariance_example() {
    let mut long_lived = String::from("hello");
    let mut short_ref: &str = &long_lived;

    // If &mut Vec<&str> were covariant in &str, we could do:
    // let mut v: Vec<&'long str> = vec![&long_lived];
    // let r: &mut Vec<&'short str> = &mut v;  // hypothetical covariant cast
    // {
    //     let temp = String::from("temp");
    //     r.push(&temp);  // push short-lived ref into long-lived vec
    // }
    // // v[1] now dangles! The compiler prevents this via invariance.

    println!("{short_ref}");
}

fn main() { invariance_example(); }
```

## Example B -- Controlling variance with PhantomData

```rust
use std::marker::PhantomData;

// Covariant wrapper (like Box<T>)
struct CovariantPtr<T> {
    ptr: *const T,
    _marker: PhantomData<T>,           // owns a T -> covariant
}

// Contravariant wrapper (like a callback taking T)
struct ContravariantPtr<T> {
    ptr: *const T,
    _marker: PhantomData<fn(T)>,       // consumes T -> contravariant
}

// Invariant wrapper (like &mut T)
struct InvariantPtr<T> {
    ptr: *mut T,
    _marker: PhantomData<fn(T) -> T>,  // both produces and consumes -> invariant
}
```

## Use-case cross-references

- [-> UC-20](../usecases/UC20-ownership-apis.md) -- Correct variance ensures that APIs with lifetimes are sound under subtyping.
- [-> UC-23](../usecases/UC23-diagnostics.md) -- Many confusing lifetime errors are actually variance errors; understanding this feature helps decode them.
- [-> UC-21](../usecases/UC21-concurrency.md) -- Interior mutability types are invariant, which prevents unsound aliasing in concurrent code.

## Source anchors

- `nomicon/src/subtyping.md`
- `nomicon/src/phantom-data.md`
- `rust-reference/src/subtyping.md`
- `rust-reference/src/special-types-and-traits.md` -- PhantomData variance
