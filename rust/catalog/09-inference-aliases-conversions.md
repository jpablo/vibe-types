# Inference, Aliases, and Conversion Traits

## What it is

Type inference, aliases, and conversion traits shape how types are inferred and converted safely.

## What constraint it enforces

**Inferred and converted types must satisfy declared signatures and trait contracts.**

## Minimal snippet

```rust
let mut v = Vec::new();
v.push(5_u8); // infers Vec<u8>
```

## Interaction with other features

- Complements modeling in `[-> catalog/04]`.
- Composes with generic bounds in `[-> catalog/05]`.
- Used in `[-> UC-01]` and `[-> UC-06]`.

## Gotchas and limitations

- Type aliases are synonyms, not new distinct types; they do not enforce domain separation by themselves.
- Primitive conversions are explicit; there is no general implicit numeric conversion.

### Beginner mental model

The compiler often fills in type gaps for you. Think of inference as your friend guessing the missing ingredient based on how you use the value, aliases as kitchen notes that rename a type for readability, and conversion traits as the recipes that safely turn one type into another.

### Example A

```rust
type Kms = u32;

fn print_distance(d: Kms) {
    println!("{} km", d);
}

let value = 42;
print_distance(value); // inference sees `Kms` alias = `u32`
```

### Example B

```rust
struct Feet(f64);

impl From<f64> for Feet {
    fn from(meters: f64) -> Feet {
        Feet(meters * 3.28084)
    }
}

let meters = 2.0;
let distance: Feet = meters.into();
```

### Common compiler errors and how to read them

- `error[E0282]: type annotations needed` means inference could not guess the expected type; add a type annotation or specify the generic parameters (`let feet: Feet = meters.into();`).
- `error[E0308]: mismatched types` often shows the two types the compiler compared—read the `expected` vs `found` lines to determine which part of the expression should change or which conversion trait to implement.

## Use-case cross-references

- `[-> UC-01]`
- `[-> UC-06]`

## Source anchors

- `rust-by-example/src/types/inference.md`
- `rust-by-example/src/types/alias.md`
- `rust-by-example/src/types/cast.md`
- `rust-by-example/src/conversion/from_into.md`
- `rust-by-example/src/conversion/try_from_try_into.md`
- `book/src/ch20-03-advanced-types.md`
