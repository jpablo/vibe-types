# Escape Hatches

## The constraint

Rust's safety guarantees can be selectively bypassed with `unsafe` blocks when the type system cannot express a correct invariant. Inside `unsafe`, the programmer takes responsibility for upholding memory safety. Escape hatches include raw pointers, `transmute`, `unsafe impl`, and FFI.

## Feature toolkit

- `[-> T10](../catalog/T10-ownership-moves.md)`
- `[-> T11](../catalog/T11-borrowing-mutability.md)`
- `[-> T24](../catalog/T24-smart-pointers.md)`

## Patterns

- Pattern A: `unsafe` block for dereferencing raw pointers.
```rust
let x = 42;
let ptr: *const i32 = &x;

// Safe wrapper around an unsafe operation
fn read_ptr(p: *const i32) -> i32 {
    unsafe { *p }  // caller guarantees pointer is valid
}

assert_eq!(read_ptr(ptr), 42);
```

- Pattern B: `unsafe impl` for marker traits.
```rust
struct MyBuffer {
    data: Vec<u8>,
}

// Promise the compiler that MyBuffer is safe to send across threads
unsafe impl Send for MyBuffer {}
unsafe impl Sync for MyBuffer {}
```

- Pattern C: `std::mem::transmute` for reinterpreting bit patterns.
```rust
use std::mem;

// Convert between repr(C) types with identical layouts
#[repr(C)]
struct Rgb { r: u8, g: u8, b: u8 }

#[repr(C)]
struct Bgr { b: u8, g: u8, r: u8 }

fn rgb_to_array(c: Rgb) -> [u8; 3] {
    // SAFETY: Rgb is repr(C) with 3 u8 fields — same layout as [u8; 3]
    unsafe { mem::transmute(c) }
}
```

- Pattern D: FFI with `extern "C"` functions.
```rust
extern "C" {
    fn abs(input: i32) -> i32;
    fn strlen(s: *const std::ffi::c_char) -> usize;
}

fn safe_abs(n: i32) -> i32 {
    unsafe { abs(n) }  // C function — safe to call with any i32
}

// Exposing Rust to C:
#[no_mangle]
pub extern "C" fn rust_add(a: i32, b: i32) -> i32 {
    a + b
}
```

- Pattern E: safe abstraction wrapping unsafe internals.
```rust
pub struct FixedBuffer<const N: usize> {
    data: [u8; N],
    len: usize,
}

impl<const N: usize> FixedBuffer<N> {
    pub fn get(&self, index: usize) -> Option<u8> {
        if index < self.len {
            // SAFETY: index is bounds-checked above
            Some(unsafe { *self.data.get_unchecked(index) })
        } else {
            None
        }
    }
}
// Public API is safe; unsafe is encapsulated with a documented invariant.
```

## Tradeoffs

- `unsafe` enables performance optimizations and FFI but shifts correctness responsibility from the compiler to the programmer.
- `transmute` is maximally flexible but maximally dangerous — layout changes silently break it.
- FFI boundaries are inherently unsafe; wrapping them in safe Rust APIs localizes the risk.
- Overuse of `unsafe` defeats Rust's safety guarantees; underuse may lead to unnecessary copies or allocations.

## When to use which feature

- Use `unsafe` blocks only when the compiler cannot verify an invariant you can prove correct.
- Wrap every `unsafe` block in a safe public API with a `// SAFETY:` comment explaining the invariant.
- Prefer `transmute` alternatives (`from_le_bytes`, `as` casts, `bytemuck`) when available.
- Use `extern "C"` and raw pointers for FFI; always wrap the boundary in a safe Rust module.
- Run `miri` and sanitizers in CI to catch undefined behavior in `unsafe` code.

## Source anchors

- `book/src/ch20-01-unsafe-rust.md`
- `nomicon/src/intro.md`
- `nomicon/src/transmutes.md`
- `nomicon/src/ffi.md`
- `rust-by-example/src/unsafe.md`
