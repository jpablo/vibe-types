# Const Generics

## What it is

Const generics allow types and functions to be parameterized by *values* — not just types. Where ordinary generics let you write `Vec<T>` and substitute any type for `T`, const generics let you write `[T; N]` and substitute any compile-time constant for `N`. The most immediately visible application is **array lengths**: a function can accept `[T; N]` for *any* `N`, rather than being hardcoded for a single size.

Before const generics landed (stabilized in Rust 1.51), the standard library resorted to implementing traits for arrays of each length individually — `impl<T> Default for [T; 0]`, `impl<T> Default for [T; 1]`, all the way up to 32. This was tedious, error-prone, and meant that arrays of length 33 or above simply lacked trait implementations. Const generics eliminated this ceiling by letting a single `impl<T, const N: usize>` cover every possible length at once.

The types allowed as const parameters are restricted to *primitive scalars*: all integer types (`u8` through `u128`, `i8` through `i128`, `usize`, `isize`), `bool`, and `char`. Floating-point numbers, strings, structs, and enums are not permitted because the compiler must be able to compare const values for type equality, and those types lack a straightforward notion of structural equality. This restriction is narrower than C++ non-type template parameters (which now accept class types in C++20) and far narrower than dependent types in languages like Idris or Agda, where any value can appear at the type level.

## What constraint it enforces

**Const-generic parameters embed compile-time scalar values into type signatures, so size, dimension, and capacity invariants are checked before any code runs.**

More specifically:

- **Distinct values produce distinct types.** `Buffer<3>` and `Buffer<4>` are entirely separate types. You cannot assign one to the other, and functions expecting one will reject the other — the compiler treats the const value as part of the type identity.
- **Values must be known at compile time.** A const parameter must resolve to a concrete value during monomorphization. You cannot pass a runtime variable where a const generic is expected.
- **Array generality.** `[T; N]` is now fully generic. You can write a single function, trait impl, or struct that works for arrays of *any* length, eliminating the old length-32 ceiling.
- **Shape-level safety.** By encoding dimensions, capacities, or protocol constants in the type, mismatches surface as type errors rather than runtime panics or silent corruption.

## Minimal snippet

```rust
fn sum<const N: usize>(arr: [i32; N]) -> i32 {
    arr.iter().sum()
}

fn main() {
    let total = sum([10, 20, 30]); // N inferred as 3
    println!("{total}");           // 60
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Generics and Traits** [-> catalog/05] | Const generics extend the generic system. A type can mix type and const parameters: `struct Matrix<T, const R: usize, const C: usize>`. Trait impls can be written over const params just like type params. |
| **Ownership and Moves** [-> catalog/01] | Arrays `[T; N]` are value types; moving a const-generic array transfers ownership of the entire fixed-size block. No heap allocation is involved unless `T` itself allocates. |
| **Lifetimes** [-> catalog/03] | Const generics and lifetimes are orthogonal. A type can carry both: `struct Window<'a, const SIZE: usize>(&'a [u8; SIZE])`. |
| **Smart Pointers** [-> catalog/10] | `Box<[T; N]>` places a const-generic array on the heap. This is useful for large `N` values that would overflow the stack. |
| **Zero-Sized Types** [-> catalog/09] | When `N = 0`, `[T; 0]` is a ZST. Const generics let you write code that gracefully handles this edge case generically. |

## Gotchas and limitations

1. **Only primitive scalar types are allowed as const parameters.** You cannot use `f32`, `&str`, tuples, or user-defined structs as const params. If you need richer compile-time values, you must encode them as integers or use marker types instead.

2. **Const expressions involving generic const params are severely limited.** Writing `[u8; N + 1]` or `[u8; N * M]` in a type position requires the unstable `generic_const_exprs` feature. On stable Rust, you are mostly limited to using a bare const param `N` without arithmetic.

   ```rust
   // Requires nightly + #![feature(generic_const_exprs)]
   fn extend<const N: usize>(arr: [u8; N]) -> [u8; N + 1] {
       todo!()
   }
   ```

3. **Each distinct const value creates a distinct type.** `Buffer<3>` and `Buffer<4>` cannot be used interchangeably. This is type-safe but means you cannot store mixed-size buffers in a homogeneous collection without trait objects or an enum wrapper.

4. **Default values for const params.** You can write `struct Buf<const N: usize = 1024>`, which allows `Buf` to mean `Buf<1024>`. However, defaults must appear after non-defaulted params, and not all contexts infer the default automatically — you may still need to spell it out.

5. **Trait objects and const generics do not mix easily.** A trait that has a const-generic method or is implemented on a const-generic type usually cannot be made into `dyn Trait` because the vtable needs a single concrete implementation, not one per const value.

6. **Const evaluation failures produce cryptic errors.** If a const expression panics or overflows during compilation, the error message points at the type alias or struct definition, not at the arithmetic that failed. This can be confusing when the expression is complex.

7. **`where` clauses for constraining const values are still evolving.** You might want to write `where N > 0` or `where R == C`, but Rust does not yet support general const predicates on stable. Workarounds involve `Assert` helper traits or nightly features.

8. **Binary bloat from monomorphization.** Just like type generics, each distinct const value monomorphizes a separate copy of the function or type. Calling `sum::<3>`, `sum::<4>`, and `sum::<5>` produces three separate compiled functions. For hot paths with many sizes, this can inflate binary size.

## Beginner mental model

Think of const generics as **compile-time knobs on your types**. When you write `Buffer<const N: usize>`, the `N` is a number baked into the type itself — like choosing the size of a container before the factory builds it. The compiler stamps out a custom version for each size you use, verifies that sizes match where they should, and rejects mismatches as type errors.

The key insight: **a const generic parameter is part of the type, not a runtime value.** `[u8; 3]` and `[u8; 4]` are as different to Rust as `String` and `Vec<u8>`. This means the compiler can guarantee that a function receiving `[u8; 3]` never accidentally gets a four-element array — there is no off-by-one at runtime because the size is checked at compile time.

## Example A — Basic const-generic function for arrays

```rust
fn first_and_last<T: Copy, const N: usize>(arr: [T; N]) -> (T, T) {
    (arr[0], arr[N - 1])
}

fn main() {
    let pair = first_and_last([10, 20, 30, 40]);
    println!("{:?}", pair); // (10, 40)
}
```

The compiler infers `N = 4` from the array literal. If you tried passing an empty array (`N = 0`), the subtraction `N - 1` would underflow during const evaluation and the build would fail.

## Example B — Const-generic struct: fixed-size buffer

```rust
struct RingBuffer<T, const CAP: usize> {
    data: [Option<T>; CAP],
    head: usize,
}

impl<T, const CAP: usize> RingBuffer<T, CAP> {
    fn new() -> Self
    where
        T: Copy,
    {
        RingBuffer {
            data: [None; CAP],
            head: 0,
        }
    }

    fn push(&mut self, value: T) {
        self.data[self.head % CAP] = Some(value);
        self.head += 1;
    }
}

fn main() {
    let mut buf = RingBuffer::<u32, 4>::new();
    buf.push(1);
    buf.push(2);
}
```

The capacity `CAP` is part of the type. Two ring buffers with different capacities are different types and cannot be accidentally swapped.

## Example C — Implementing traits for const-generic types

```rust
use std::fmt;

struct Vector<const N: usize>([f64; N]);

impl<const N: usize> fmt::Display for Vector<N> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[")?;
        for (i, val) in self.0.iter().enumerate() {
            if i > 0 { write!(f, ", ")?; }
            write!(f, "{val:.2}")?;
        }
        write!(f, "]")
    }
}

fn main() {
    let v = Vector([1.0, 2.5, 3.7]);
    println!("{v}"); // [1.00, 2.50, 3.70]
}
```

A single `impl<const N: usize>` covers vectors of every size — no need to repeat the implementation per length.

## Example D — Default const parameter values

```rust
struct Pool<const SIZE: usize = 64> {
    slots: [Option<String>; SIZE],
}

impl<const SIZE: usize> Pool<SIZE> {
    fn new() -> Self {
        Pool {
            slots: std::array::from_fn(|_| None),
        }
    }
}

fn main() {
    let default_pool = Pool::new();           // SIZE = 64
    let small_pool = Pool::<8>::new();        // SIZE = 8
    println!("default slots: {}", default_pool.slots.len()); // 64
    println!("small slots: {}", small_pool.slots.len());     // 8
}
```

Default const values work the same way as default type parameters — they provide a sensible fallback while still allowing callers to override.

## Example E — Generic array operations: flatten

```rust
fn flatten<T: Copy + Default, const R: usize, const C: usize>(
    grid: [[T; C]; R],
) -> [T; R * C] {
    // Note: `R * C` in return position requires nightly generic_const_exprs.
    // On stable, you would return a Vec<T> instead.
    let mut out = [T::default(); R * C];
    for (i, row) in grid.iter().enumerate() {
        for (j, val) in row.iter().enumerate() {
            out[i * C + j] = *val;
        }
    }
    out
}
```

This function flattens a 2D array into a 1D array whose length is statically guaranteed to be `R * C`. The compiler enforces that the output has exactly the right number of elements.

## Example F — Enforcing dimension compatibility: matrix multiply

```rust
struct Matrix<const R: usize, const C: usize>([[f64; C]; R]);

impl<const R: usize, const C: usize> Matrix<R, C> {
    fn multiply<const C2: usize>(
        &self,
        rhs: &Matrix<C, C2>,
    ) -> Matrix<R, C2> {
        let mut result = [[0.0f64; C2]; R];
        for i in 0..R {
            for j in 0..C2 {
                for k in 0..C {
                    result[i][j] += self.0[i][k] * rhs.0[k][j];
                }
            }
        }
        Matrix(result)
    }
}

fn main() {
    let a = Matrix([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]); // 3x2
    let b = Matrix([[7.0, 8.0, 9.0], [10.0, 11.0, 12.0]]); // 2x3
    let c = a.multiply(&b);                                   // 3x3

    // let bad = Matrix([[1.0, 2.0]]);                         // 1x2
    // a.multiply(&bad);  // error: expected Matrix<2, _>, found Matrix<1, 2>
}
```

The inner dimension `C` of the left matrix must equal the row count of the right matrix. This constraint is encoded in the type signatures — a dimension mismatch is a compile-time error, not a runtime panic.

## Common compiler errors and how to read them

### `error[E0277]: the trait bound ... is not satisfied` (wrong const value)

```
error[E0277]: the trait bound `[i32; 4]: From<[i32; 3]>` is not satisfied
 --> src/main.rs:5:26
  |
5 |     let big: [i32; 4] = small.into();
  |                          ^^^^ the trait `From<[i32; 3]>` is not
  |                               implemented for `[i32; 4]`
```

**How to fix:** Arrays of different lengths are different types. There is no automatic conversion between `[T; 3]` and `[T; 4]`. Copy elements manually, use `try_into()` for slices, or redesign to work generically over `const N: usize`.

### `error[E0658]: generic parameters may not be used in const operations`

```
error[E0658]: generic parameters may not be used in const operations
 --> src/main.rs:3:35
  |
3 | fn extend<const N: usize>(a: [u8; N]) -> [u8; N + 1] {
  |                                                ^^^^^ cannot perform
  |                  const operations on generic parameter `N`
  = note: see issue #76560 for more information
```

**How to fix:** On stable Rust, you cannot use arithmetic on const generic params in type positions. Either return a `Vec` instead, restructure to avoid the arithmetic, or switch to nightly and enable `#![feature(generic_const_exprs)]`.

### `error[E0308]: mismatched types` (different const values)

```
error[E0308]: mismatched types
 --> src/main.rs:8:18
  |
8 |     let b: Buffer<4> = a;
  |            ---------   ^ expected `Buffer<4>`, found `Buffer<3>`
  |            |
  |            expected due to this
```

**How to fix:** `Buffer<3>` and `Buffer<4>` are distinct types. You cannot assign one to the other. If you need runtime-variable sizing, use a `Vec` or a trait object. If the sizes should match, fix the const argument at the call site.

### `error[E0770]: the type of const parameters must not depend on other generic parameters`

```
error[E0770]: the type of const parameters must not depend on other
              generic parameters
 --> src/main.rs:1:28
  |
1 | fn foo<T, const N: T>(arr: [T; N]) {}
  |                    ^ the type must not depend on the parameter `T`
```

**How to fix:** Const parameter types must be concrete primitive scalars. Write `const N: usize` (or `bool`, `char`, etc.) rather than parameterizing the const type itself. The type of the const param is fixed at definition time.

## Use-case cross-references

- [-> UC-08](../usecases/08-value-level-type-constraints.md) — Encoding value-level invariants (lengths, capacities, dimensions) into types so the compiler can enforce them.
- [-> UC-04](../usecases/04-zero-cost-abstraction.md) — Const generics are monomorphized, producing specialized code with no runtime overhead for each const value.

## Source anchors

- `rust/src/doc/reference/src/items/generics.md`
- `rust/src/doc/reference/src/type-system.md`
- `rust/src/doc/rustc-dev-guide/src/const-generics.md`
- `book/src/ch20-03-advanced-types.md`
- `rust-by-example/src/generics/const_generics.md`
