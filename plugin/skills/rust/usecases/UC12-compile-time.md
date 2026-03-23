# Compile-Time Programming

## The constraint

Move computation, validation, and code generation to compile time so that invariants are checked before the program runs and runtime cost is eliminated.

## Feature toolkit

- `[-> T16](../catalog/T16-compile-time-ops.md)` — const fn, const blocks
- `[-> T15](../catalog/T15-const-generics.md)` — const generics
- `[-> T17](../catalog/T17-macros-metaprogramming.md)` — macros and proc macros

## Patterns

- Pattern A: `const fn` for compile-time evaluation.
```rust
const fn factorial(n: u64) -> u64 {
    match n {
        0 | 1 => 1,
        _ => n * factorial(n - 1),
    }
}

const FACT_10: u64 = factorial(10); // evaluated at compile time
```

- Pattern B: const generics for size-parameterized types.
```rust
struct Matrix<const ROWS: usize, const COLS: usize> {
    data: [[f64; COLS]; ROWS],
}

impl<const ROWS: usize, const COLS: usize> Matrix<ROWS, COLS> {
    fn transpose(self) -> Matrix<COLS, ROWS> {
        let mut out = [[0.0; ROWS]; COLS];
        for r in 0..ROWS {
            for c in 0..COLS {
                out[c][r] = self.data[r][c];
            }
        }
        Matrix { data: out }
    }
}

let m: Matrix<2, 3> = Matrix { data: [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]] };
let t: Matrix<3, 2> = m.transpose(); // dimensions checked at compile time
```

- Pattern C: `build.rs` for build-time code generation.
```rust
// build.rs
fn main() {
    let out_dir = std::env::var("OUT_DIR").unwrap();
    let dest = std::path::Path::new(&out_dir).join("generated.rs");
    std::fs::write(&dest, r#"const BUILD_TIME: &str = "2025-01-01";"#).unwrap();
    println!("cargo::rerun-if-changed=build.rs");
}

// src/main.rs
include!(concat!(env!("OUT_DIR"), "/generated.rs"));
fn main() { println!("built at {BUILD_TIME}"); }
```

- Pattern D: `macro_rules!` for repetitive pattern generation.
```rust
macro_rules! impl_from_int {
    ($($ty:ty),+) => {
        $(
            impl From<$ty> for MyNum {
                fn from(v: $ty) -> Self { MyNum(v as i64) }
            }
        )+
    };
}

struct MyNum(i64);
impl_from_int!(i8, i16, i32, i64, u8, u16, u32);
```

## Tradeoffs

| Approach | Strength | Weakness |
|----------|----------|----------|
| `const fn` | Zero runtime cost, type-safe | Limited subset of Rust (no heap, no traits) |
| Const generics | Dimensions/sizes checked at compile time | Only primitive scalar types allowed |
| `build.rs` | Full Rust available, can read files/env | Opaque to IDE, harder to debug |
| Macros | Eliminate boilerplate, enforce patterns | Harder to read, debug, and maintain |

## When to use which feature

- Use `const fn` for pure computations that benefit from compile-time evaluation.
- Use const generics when types should be parameterized by values (array sizes, buffer lengths).
- Use `build.rs` for embedding resources, generating lookup tables, or conditional compilation.
- Use macros when a pattern repeats across many types and cannot be expressed with generics.

## Source anchors

- `book/src/ch19-06-macros.md`
- `rust-reference/src/const_eval.md`
- `rust-reference/src/items/generics.md` — const generics
- `cargo-book/src/reference/build-scripts.md`
