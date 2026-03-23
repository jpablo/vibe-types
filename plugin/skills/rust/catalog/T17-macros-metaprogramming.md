# Macros and Metaprogramming

Since: Rust 1.0 (`macro_rules!`); Rust 1.15 (custom derive proc macros); Rust 1.30 (attribute & function-like proc macros)

## What it is

Rust provides two macro systems for compile-time code generation. **Declarative macros** (`macro_rules!`) use pattern matching on token trees to expand invocations into Rust code. They are hygienic -- identifiers introduced by the macro do not leak into the caller's scope, and vice versa, preventing accidental name collisions.

**Procedural macros** (proc macros) are Rust functions that receive a `TokenStream` and return a `TokenStream`, executing arbitrary Rust code at compile time. There are three kinds: **custom derive** (`#[derive(MyTrait)]`), **attribute macros** (`#[my_attr]`), and **function-like macros** (`my_macro!(...)`). Proc macros live in dedicated `proc-macro` crates and typically use the `syn` crate for parsing and `quote` for code generation.

Together these systems eliminate boilerplate, enforce patterns, and generate type-safe code without runtime reflection.

## What constraint it enforces

**Macro-generated code is type-checked and borrow-checked identically to hand-written code. Invalid expansions are caught at compile time.**

- Declarative macros expand before type checking. If the expansion contains a type error, the compiler reports it against the expanded code.
- Proc macros run during compilation. A buggy proc macro can produce a compile error, but it cannot silently generate unsound code that bypasses the type system.
- Hygienic identifiers in `macro_rules!` prevent accidental shadowing or capture.

## Minimal snippet

```rust
macro_rules! make_getter {
    ($field:ident, $ty:ty) => {
        fn $field(&self) -> &$ty {
            &self.$field
        }
    };
}

struct User { name: String, age: u32 }

impl User {
    make_getter!(name, String);
    make_getter!(age, u32);
}

fn main() {
    let u = User { name: "Alice".into(), age: 30 };
    println!("{}, {}", u.name(), u.age());
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Derive macros** [-> catalog/T06](T06-derivation.md) | Custom derive is the most common proc macro kind. `#[derive(Serialize)]` is a proc macro that generates `impl Serialize`. |
| **Traits** [-> catalog/T05](T05-type-classes.md) | Macros often generate trait implementations. The `derive` ecosystem is built on this combination. |
| **Compile-time ops** [-> catalog/T16](T16-compile-time-ops.md) | `macro_rules!` runs at syntax expansion time; `const fn` runs at evaluation time. Both shift work to compile time but at different phases. |
| **Algebraic data types** [-> catalog/T01](T01-algebraic-data-types.md) | Macros frequently generate enum variants or struct fields from a DSL, then hand the result to the type checker. |

## Gotchas and limitations

1. **Declarative macro syntax is its own language.** The `$ident:expr`, `$($x:tt)*` syntax differs from regular Rust and has a steep learning curve. Error messages from malformed macros can be cryptic.

2. **Proc macros slow compilation.** Each proc macro crate adds a dependency and compilation unit. Heavy use of `syn` parsing can significantly increase build times.

3. **Debugging macros is hard.** Use `cargo expand` (from the `cargo-expand` crate) to see the generated code. Without it, compiler errors point to opaque macro invocations.

4. **Hygiene is not perfect in `macro_rules!`.** While identifiers are hygienic, certain constructs (like `$crate`) have edge cases. Proc macros have no built-in hygiene -- the author must manage spans carefully.

5. **Proc macros cannot access type information.** They operate on token streams, not the AST or type system. A proc macro cannot inspect whether a field implements `Clone`; it can only see the tokens.

6. **`macro_rules!` ordering matters.** A declarative macro must be defined before it is used in the same module (or brought into scope with `#[macro_use]` or `#[macro_export]`).

## Beginner mental model

Think of `macro_rules!` as a **text template with smart find-and-replace**. You write a pattern with placeholders, and whenever someone invokes the macro, the compiler swaps in the actual code. The "smart" part is hygiene: the template's internal variable names do not clash with the caller's names. Proc macros are more like **compiler plugins** -- full programs that read your source code as input and produce new source code as output.

## Example A -- Declarative macro generating repetitive impls

```rust
macro_rules! impl_display_for_newtype {
    ($($t:ty),+) => {
        $(
            impl std::fmt::Display for $t {
                fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
                    write!(f, "{}", self.0)
                }
            }
        )+
    };
}

struct Name(String);
struct Age(u32);

impl_display_for_newtype!(Name, Age);

fn main() {
    println!("{}", Name("Alice".into()));  // Alice
    println!("{}", Age(30));               // 30
}
```

## Example B -- Attribute-style proc macro concept (usage)

```rust
// Using a hypothetical proc macro crate:
use my_builder::Builder;

#[derive(Builder)]
struct Config {
    host: String,
    port: u16,
    #[builder(default = 3)]
    retries: u32,
}

fn main() {
    let cfg = Config::builder()
        .host("db.local".into())
        .port(5432)
        .build()
        .unwrap();
    println!("{}:{}", cfg.host, cfg.port);
}
```

The `Builder` derive macro generates a `ConfigBuilder` struct with setter methods and a `build()` method -- all at compile time.

## Use-case cross-references

- [-> UC-14](../usecases/UC14-extensibility.md) -- Macros enable extensible patterns where new variants or impls can be stamped out without modifying core code.
- [-> UC-23](../usecases/UC23-diagnostics.md) -- Macro expansion errors are a frequent source of confusing diagnostics; understanding macros helps decode them.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Macros can generate generic impls with trait bounds, scaling to many types at once.

## Recommended libraries

| Library | Description |
|---------|-------------|
| [syn](https://docs.rs/syn) | Parser for Rust token streams — the foundation for almost all proc macros |
| [quote](https://docs.rs/quote) | Quasi-quoting for generating `TokenStream` output from Rust-like syntax |
| [proc-macro2](https://docs.rs/proc-macro2) | Wrapper around `proc_macro` that works in non-macro contexts (testing, utilities) |
| [darling](https://docs.rs/darling) | Declarative attribute parsing for proc macros — eliminates boilerplate for reading `#[attr(...)]` arguments |

## Source anchors

- `book/src/ch19-06-macros.md`
- `rust-reference/src/macros-by-example.md`
- `rust-reference/src/procedural-macros.md`
- `rust-by-example/src/macros.md`
- `rust-by-example/src/macros/syntax.md`
