# Type Narrowing via Pattern Matching

Since: Rust 1.0 (`match`, `if let`); Rust 1.65 (`let-else`)

## What it is

Rust narrows types through **pattern matching** rather than runtime type checks. The constructs `match`, `if let`, `let-else`, and `matches!()` destructure enums, structs, and tuples, binding inner values to variables whose types the compiler knows precisely. Because Rust enums are closed (all variants are declared up front), the compiler performs **exhaustiveness checking**: a `match` must handle every variant, or the code will not compile.

Unlike languages with subtype hierarchies where narrowing means "prove this base-class reference is actually a derived class," Rust narrowing is purely structural: you decompose a value into its constituent parts. There are no downcasts, no `instanceof`, no `as?` -- just pattern matching that the compiler verifies statically.

## What constraint it enforces

**Every variant of an enum must be handled, and the compiler guarantees that bindings within each arm have the correct narrowed type.**

- `match` on an enum is exhaustive -- omitting a variant is a compile error.
- `if let` narrows a single variant without requiring exhaustiveness, but the `else` branch implicitly handles everything not matched.
- `let-else` narrows or diverges: the else block must diverge (`return`, `break`, `continue`, `panic!`).
- `matches!()` returns a `bool` without binding, useful in conditions and `filter` closures.

## Minimal snippet

```rust
enum Shape {
    Circle(f64),
    Rect { w: f64, h: f64 },
}

fn area(s: &Shape) -> f64 {
    match s {
        Shape::Circle(r)        => std::f64::consts::PI * r * r,
        Shape::Rect { w, h }    => w * h,
    }
    // Adding a new variant forces updating this match -- exhaustiveness check
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Algebraic data types** [-> catalog/T01](T01-algebraic-data-types.md) | Enums define the variants; pattern matching consumes them. The two features are designed as a pair. |
| **Null safety (Option)** [-> catalog/T13](T13-null-safety.md) | `if let Some(v) = opt` is the idiomatic way to narrow `Option<T>` to `T`. |
| **Effect tracking (Result)** [-> catalog/T12](T12-effect-tracking.md) | `match result { Ok(v) => ..., Err(e) => ... }` narrows `Result` into its success or error type. |
| **Never type** [-> catalog/T34](T34-never-bottom.md) | Match arms that diverge (return `!`) satisfy any expected type, enabling early-return patterns. |
| **Encapsulation** [-> catalog/T21](T21-encapsulation.md) | Structs with private fields cannot be destructured outside their module, limiting where pattern matching works. |

## Gotchas and limitations

1. **Guards weaken exhaustiveness.** `match` arms with `if` guards are not considered by the exhaustiveness checker for coverage purposes. You may still need a wildcard arm even when guards logically cover all cases.

2. **Binding modes and `ref`.** Matching on a reference (`&value`) auto-introduces `ref` bindings. Beginners are often surprised that `match &opt { Some(s) => ... }` gives `s: &T` rather than `s: T`.

3. **Or-patterns share bindings.** `A(x) | B(x) => ...` requires `x` to have the same type in both alternatives. The compiler rejects or-patterns where binding types differ.

4. **`#[non_exhaustive]` enums require wildcards.** External crates matching on a `#[non_exhaustive]` enum must include a `_ =>` arm, even if all current variants are listed.

5. **No type-test narrowing.** There is no `if value is SomeType` construct. Narrowing only works via pattern matching on known enum variants or struct shapes.

## Beginner mental model

Think of `match` as a **sorting machine** on a conveyor belt. Each enum variant has a different shape, and the machine has a slot for every possible shape. If you forget a slot, the machine refuses to turn on (compile error). When a value arrives, it drops into exactly one slot, and inside that slot you have access to the value's inner parts with their precise types -- no guessing needed.

## Example A -- if let for single-variant narrowing

```rust
fn print_if_positive(val: Option<i32>) {
    if let Some(n) = val {
        if n > 0 {
            println!("positive: {n}");
        }
    }
}

fn main() {
    print_if_positive(Some(42));   // positive: 42
    print_if_positive(Some(-1));   // (no output)
    print_if_positive(None);       // (no output)
}
```

## Example B -- let-else for early return

```rust
fn process(input: &str) -> Result<u32, String> {
    let Some(digits) = input.strip_prefix("num:") else {
        return Err("missing 'num:' prefix".into());
    };
    digits.parse::<u32>().map_err(|e| e.to_string())
}

fn main() {
    println!("{:?}", process("num:42"));   // Ok(42)
    println!("{:?}", process("bad"));      // Err("missing 'num:' prefix")
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Exhaustive matching ensures every state is handled, preventing forgotten edge cases.
- [-> UC-23](../usecases/UC23-diagnostics.md) -- "non-exhaustive patterns" is one of the most common and helpful compiler errors.

## Source anchors

- `book/src/ch06-02-match.md`
- `book/src/ch18-01-all-the-places-for-patterns.md`
- `book/src/ch18-03-pattern-syntax.md`
- `rust-reference/src/expressions/match-expr.md`
- `rust-reference/src/expressions/if-expr.md` -- if let
