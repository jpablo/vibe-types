# Metaprogramming

## The constraint

Generate or transform code at compile time so repetitive patterns, boilerplate, and conditional compilation are handled before the binary is produced. Rust provides declarative macros (`macro_rules!`), procedural macros (derive, attribute, and function-like), and `build.rs` build scripts.

## Feature toolkit

- `[-> T17](../catalog/T17-macros-metaprogramming.md)`
- `[-> T16](../catalog/T16-compile-time-ops.md)`
- `[-> T06](../catalog/T06-derivation.md)`

## Patterns

- Pattern A: `macro_rules!` for declarative pattern-matching macros.
```rust
macro_rules! vec_of_strings {
    ($($x:expr),* $(,)?) => {
        vec![$($x.to_string()),*]
    };
}

let names = vec_of_strings!["alice", "bob", "carol"];
// Expands to: vec!["alice".to_string(), "bob".to_string(), "carol".to_string()]
```

- Pattern B: derive macros for trait generation.
```rust
// In the proc-macro crate:
// #[proc_macro_derive(Builder)]
// pub fn derive_builder(input: TokenStream) -> TokenStream { ... }

// In user code:
#[derive(Builder)]
struct Config {
    host: String,
    port: u16,
}

// Generated: ConfigBuilder with .host(), .port(), .build() methods.
```

- Pattern C: attribute macros for code transformation.
```rust
// #[proc_macro_attribute]
// pub fn route(attr: TokenStream, item: TokenStream) -> TokenStream { ... }

#[route(GET, "/api/users")]
fn list_users() -> Vec<User> {
    // The macro wraps this in routing registration code
    vec![]
}
```

- Pattern D: `build.rs` for pre-compilation code generation.
```rust
// build.rs
fn main() {
    // Generate bindings, embed assets, or produce Rust code
    let out_dir = std::env::var("OUT_DIR").unwrap();
    std::fs::write(
        format!("{out_dir}/generated.rs"),
        "pub const BUILD_TIME: &str = \"2024-01-01\";"
    ).unwrap();
    println!("cargo::rerun-if-changed=build.rs");
}

// In lib.rs:
include!(concat!(env!("OUT_DIR"), "/generated.rs"));
```

- Pattern E: `cfg` attributes for conditional compilation.
```rust
#[cfg(target_os = "linux")]
fn platform_init() { /* Linux-specific */ }

#[cfg(target_os = "macos")]
fn platform_init() { /* macOS-specific */ }

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() { assert!(true); }
}
```

## Tradeoffs

- `macro_rules!` is zero-cost and hygienic but limited to pattern matching on token trees — no type information available.
- Proc macros have full Rust power but live in a separate crate, increase compile times, and produce opaque errors.
- `build.rs` can generate arbitrary code but runs outside the type system — generated code is only checked after generation.
- Heavy macro use hinders IDE support, code navigation, and debugging.

## When to use which feature

- Use `macro_rules!` for simple repetitive patterns (constructors, match arms, test helpers).
- Use derive macros when a trait implementation follows a predictable pattern from struct fields.
- Use attribute macros for framework-level transformations (routing, serialization, test harnesses).
- Use `build.rs` when code must be generated from external sources (protobuf, FFI bindings, embedded assets).
- Use `cfg` for platform-specific or feature-gated code.

## Source anchors

- `book/src/ch20-06-macros.md`
- `rust-by-example/src/macros.md`
- `reference/src/macros-by-example.md`
- `reference/src/procedural-macros.md`
- `cargo-book/src/reference/build-scripts.md`
