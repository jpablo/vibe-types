# Const Generics

## What it is

Const generics allow values (such as array lengths) to parameterize types and APIs.

## What constraint it enforces

**Const-generic parameters expose compile-time scalar values in type signatures, so shape-level constraints are enforced before runtime.**

## Minimal snippet

```rust
struct FixedGrid<const ROWS: usize, const COLS: usize>([[u8; COLS]; ROWS]);

impl<const ROWS: usize, const COLS: usize> FixedGrid<ROWS, COLS> {
    fn new() -> Self {
        FixedGrid([[0; COLS]; ROWS])
    }
}
```

## Interaction with other features

- Extends generic patterns from `[-> catalog/05]`.
- Used for value-level invariants in `[-> UC-08]`.

## Gotchas and limitations

- Const parameters only accept scalar types (`u8`/`u16`/`u32`/`u64`/`u128`/`usize`/`i8`/`i16`/`i32`/`i64`/`i128`/`isize`/`bool`/`char`), so richer value constraints need wrappers or runtime checks.
- Anonymous const expressions used for array lengths or const arguments cannot capture generic parameters, which is why `const_evaluatable_unchecked` or explicit wrapper consts are needed before the compiler can stabilize more flexible const expressions.
- Const parameters model shape-level invariants well, but not every value-level rule can be encoded directly.

### Beginner mental model

Const generics let you bake fixed numbers into your types (lengths, capacities, alignments) so the compiler enforces them. Think of `const N: usize` as a knob that configures the type layout at compile time rather than passing a value at runtime.

### Example A

```rust
struct Buffer<const LEN: usize>([u8; LEN]);

impl<const LEN: usize> Buffer<LEN> {
    fn new() -> Self {
        Buffer([0; LEN]) // length must be known at compile time, so the compiler guarantees the array size.
    }
}
```

### Example B

```rust
fn print_array<const N: usize>(arr: [i32; N]) {
    println!("array has {} elements", N);
}

fn main() {
    print_array([1, 2, 3]); // N = 3 is captured in the type, so only arrays of fixed lengths can call this function.
}
```

### Common compiler errors and how to read them

- `error[E0271]: expected an `usize` constant` – the compiler needs a literal const expression; make sure the value can be evaluated at compile time (no non-const variables).
- `error[E0277]: the trait bound `[T; N]: Sized` is not satisfied` – likely `N` is a type parameter, not a const; check that `const N: usize` is declared instead of `N: usize` in type parameters.
- `error[E0391]: the trait bound `Foo<{SOME_CONST}>: Bar` is not satisfied` – const parameters appear in trait bounds; ensure the trait implementation exists for that specific const value or add an appropriate `where` clause/`const` constraint.

## Use-case cross-references

- `[-> UC-08]`

## Source anchors

- `rust/src/doc/reference/src/items/generics.md`
- `rust/src/doc/reference/src/type-system.md`
- `rust/src/doc/rustc-dev-guide/src/const-generics.md`
- `book/src/ch20-03-advanced-types.md`
