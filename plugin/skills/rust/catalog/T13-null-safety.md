# Null Safety via Option

Since: Rust 1.0

## What it is

Rust has **no null**. There is no `null`, `nil`, `None` pointer, or implicit "absence" value baked into every reference type. Instead, the possibility of absence is represented explicitly through the `Option<T>` enum, which has exactly two variants: `Some(T)` (a value is present) and `None` (no value). Because `Option<T>` is a different type from `T`, the compiler **forces** you to handle the absent case before you can use the inner value. This eliminates null pointer dereferences -- Tony Hoare's "billion-dollar mistake" -- at compile time.

Every API that might not return a value declares that fact in its return type. `HashMap::get` returns `Option<&V>`, not a bare `&V`. `Vec::first` returns `Option<&T>`. If a function returns `T`, you are **guaranteed** a value exists -- no defensive null checks needed.

## What constraint it enforces

**You cannot use the inner value of an `Option<T>` without first proving to the compiler that it is `Some`.**

- Pattern matching (`match`, `if let`, `let-else`) is the primary extraction mechanism. The compiler rejects code that accesses the inner value without handling `None`.
- `unwrap()` and `expect()` exist as escape hatches but panic at runtime on `None`. Production code should prefer combinators (`map`, `and_then`, `unwrap_or`) or the `?` operator.
- A bare `T` in a function signature guarantees a value; `Option<T>` signals potential absence. The type system makes the distinction explicit and inescapable.

## Minimal snippet

```rust
fn find_user(id: u64) -> Option<String> {
    if id == 1 { Some("Alice".into()) } else { None }
}

fn main() {
    // Must handle both cases -- compiler enforces this
    match find_user(1) {
        Some(name) => println!("found: {name}"),
        None       => println!("not found"),
    }
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Pattern matching / type narrowing** [-> catalog/T14](T14-type-narrowing.md) | `if let Some(v) = opt` and `let Some(v) = opt else { return }` are the primary ways to narrow an `Option<T>` to its inner `T`. |
| **Algebraic data types** [-> catalog/T01](T01-algebraic-data-types.md) | `Option<T>` is itself an enum. Nesting enums with `Option` (e.g., `Option<Payment>`) composes cleanly. |
| **Effect tracking (Result)** [-> catalog/T12](T12-effect-tracking.md) | `Option<T>` and `Result<T, E>` share the same combinator API (`map`, `and_then`, `?`). Converting between them is trivial: `opt.ok_or(err)`, `res.ok()`. |
| **Never type** [-> catalog/T34](T34-never-bottom.md) | `Option<!>` can only ever be `None`, which the compiler can use for dead-code analysis. |
| **Derive macros** [-> catalog/T06](T06-derivation.md) | `Option<T>` implements `Default` (defaults to `None`), making it useful in derived `Default` impls for structs with optional fields. |

## Gotchas and limitations

1. **`unwrap()` is a hidden panic.** It compiles but crashes at runtime on `None`. Use `expect("context")` at minimum, or prefer `?`, `unwrap_or`, `unwrap_or_default`, or pattern matching.

2. **Double-wrapping: `Option<Option<T>>`.** APIs that return `Option` composed with other `Option`-returning methods can produce nested options. Use `flatten()` or `and_then()` to collapse them.

3. **`Option<&T>` vs `&Option<T>`.** These are different types with different semantics. `Option<&T>` borrows conditionally; `&Option<T>` always borrows the outer enum. Use `.as_ref()` to convert `&Option<T>` to `Option<&T>`.

4. **Niche optimization.** `Option<Box<T>>`, `Option<&T>`, and `Option<NonZeroU32>` are the same size as the inner type because the compiler uses the null/zero bit pattern to represent `None`. This is invisible in safe code but relevant for FFI and layout guarantees.

5. **No implicit truthiness.** Unlike languages where `null` is falsy, you cannot write `if opt { ... }`. You must use `if let Some(v) = opt` or `if opt.is_some()`.

## Beginner mental model

Think of `Option<T>` as a **box that might be empty**. Before you can use whatever is inside, you must open the box and check. The compiler is the inspector: it will not let you reach into the box without first writing code that handles the "empty" case. This single rule eliminates an entire category of crashes that plague languages with null.

## Example A -- Using combinators instead of matching

```rust
fn parse_port(s: &str) -> Option<u16> {
    s.strip_prefix("port=")
        .and_then(|num| num.parse().ok())
}

fn main() {
    let port = parse_port("port=8080").unwrap_or(3000);
    println!("listening on :{port}");  // :8080

    let fallback = parse_port("invalid").unwrap_or(3000);
    println!("listening on :{fallback}");  // :3000
}
```

## Example B -- let-else for early return on None

```rust
fn greet(name: Option<&str>) {
    let Some(n) = name else {
        println!("no name provided");
        return;
    };
    println!("hello, {n}!");
}

fn main() {
    greet(Some("Alice"));  // hello, Alice!
    greet(None);           // no name provided
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- `Option` eliminates null-related invalid states by making absence explicit in the type.
- [-> UC-23](../usecases/UC23-diagnostics.md) -- "expected `T`, found `Option<T>`" is a common beginner error; understanding `Option` helps read those diagnostics.

## Recommended libraries

No external libraries needed — `Option<T>` is built into `std` and covers all null-safety use cases. The standard combinators (`map`, `and_then`, `unwrap_or`, `ok_or`, `?`) are sufficient for production code.

## Source anchors

- `book/src/ch06-01-defining-an-enum.md` -- Option definition
- `book/src/ch06-02-match.md` -- matching on Option
- `rust-by-example/src/std/option.md`
- `rust-reference/src/types/enum.md`
- `std::option` module documentation
