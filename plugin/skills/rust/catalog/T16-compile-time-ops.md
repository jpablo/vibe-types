# Compile-Time Computation

Since: Rust 1.31 (`const fn` basics); Rust 1.51 (const generics MVP); Rust 1.79 (expanded `const` blocks)

## What it is

Rust provides several mechanisms for moving computation from runtime to compile time. **`const fn`** declares a function that the compiler *may* evaluate during compilation -- when called in a `const` or `static` context, it *must* evaluate at compile time. **`const` generics** (`struct Array<const N: usize>`) let types and functions be parameterized by compile-time values, not just types. **`const` blocks** (`const { ... }`) force evaluation of an expression at compile time even inside runtime code. Beyond the language itself, **`build.rs`** scripts run at build time and can generate code, embed resources, or compute lookup tables.

The `static_assertions` crate provides declarative compile-time checks: `const_assert!(size_of::<Foo>() == 8)` fails compilation if the assertion is false.

## What constraint it enforces

**Expressions evaluated at compile time are guaranteed to produce the same result on every execution, and compile-time assertions reject invalid configurations before any code runs.**

- `const fn` results used in `const` or `static` positions are computed once during compilation, incurring zero runtime cost.
- `const` generics let the compiler monomorphize for each value, enabling fixed-size arrays, bounded buffers, and compile-time dimension checks.
- Compile-time panics (`panic!` inside `const fn` or `const` blocks) become compiler errors, catching logic bugs before tests even run.

## Minimal snippet

```rust
const fn factorial(n: u64) -> u64 {
    match n {
        0 | 1 => 1,
        _ => n * factorial(n - 1),
    }
}

const FACT_10: u64 = factorial(10);  // computed at compile time

fn fixed_buffer<const N: usize>() -> [u8; N] {
    [0u8; N]
}

fn main() {
    println!("{FACT_10}");                    // 3628800
    let buf = fixed_buffer::<1024>();
    println!("buffer len = {}", buf.len());   // 1024
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Generics** [-> catalog/T04](T04-generics-bounds.md) | Const generics extend the generics system from types to values. `fn zeros<const N: usize>() -> [f64; N]` is generic over a compile-time integer. |
| **Macros** [-> catalog/T17](T17-macros-metaprogramming.md) | `macro_rules!` and proc macros generate code at compile time; `const fn` evaluates values at compile time. They complement each other. |
| **PhantomData** [-> catalog/T27](T27-erased-phantom.md) | Const generics can replace some `PhantomData` patterns where a type was previously tagged with a type-level number. |
| **Newtypes** [-> catalog/T03](T03-newtypes-opaque.md) | A newtype combined with `const fn` validation can reject invalid values at compile time: `const fn valid_port(p: u16) -> Port { ... }`. |

## Gotchas and limitations

1. **`const fn` is restricted.** Not all Rust features are available in `const fn`. Heap allocation, trait objects, and most `std` functions are not (yet) const-evaluable. The set of allowed operations expands with each Rust edition.

2. **Const generics are limited to primitive types.** As of stable Rust, const generic parameters can be integers, `bool`, and `char`. Strings, floats, and custom types are not yet supported (nightly has `adt_const_params`).

3. **`build.rs` is a blunt instrument.** Build scripts run for every compilation and can slow incremental builds. They also make cross-compilation harder since they execute on the host.

4. **Compile-time panics are hard to debug.** A `panic!` inside a `const fn` becomes a compiler error with the panic message, but there is no stack trace or debugger -- you must reason about the failure from the message alone.

5. **`const` blocks evaluated at monomorphization time.** A `const { ... }` inside a generic function is evaluated once per monomorphized instantiation, which can inflate compile times.

## Beginner mental model

Think of `const fn` as a **calculator built into the compiler**. Instead of shipping a calculation to your users' machines, you do the math once at build time and bake the answer directly into the binary. Const generics are like **ruler markings on a template** -- they let you stamp out structures of different sizes from the same blueprint, with the size fixed at compile time.

## Example A -- Compile-time assertion with const block

```rust
struct Packet {
    header: [u8; 4],
    payload: [u8; 60],
}

const _: () = {
    assert!(
        std::mem::size_of::<Packet>() == 64,
        "Packet must be exactly 64 bytes"
    );
};

fn main() {
    println!("Packet size OK");
}
```

## Example B -- Const generics for fixed-capacity stack buffer

```rust
struct StackVec<T, const CAP: usize> {
    buf: [Option<T>; CAP],
    len: usize,
}

impl<T, const CAP: usize> StackVec<T, CAP> {
    fn new() -> Self where T: Copy {
        StackVec { buf: [None; CAP], len: 0 }
    }

    fn push(&mut self, val: T) {
        assert!(self.len < CAP, "capacity exceeded");
        self.buf[self.len] = Some(val);
        self.len += 1;
    }
}

fn main() {
    let mut v = StackVec::<i32, 8>::new();
    v.push(42);
    println!("len = {}", v.len);  // 1
}
```

## Use-case cross-references

- [-> UC-18](../usecases/UC18-type-arithmetic.md) -- Const generics enable type-level arithmetic and dimension checking.
- [-> UC-01](../usecases/UC01-invalid-states.md) -- Compile-time assertions reject invalid configurations before the program even runs.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Const generic bounds constrain acceptable values at the type level.

## Source anchors

- `book/src/ch10-01-syntax.md` -- const generics
- `rust-reference/src/const_eval.md`
- `rust-reference/src/items/constant-items.md`
- `rust-reference/src/items/functions.md` -- const fn
- `rust-blog/const-generics-mvp.md`
