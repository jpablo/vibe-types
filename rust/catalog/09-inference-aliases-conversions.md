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
