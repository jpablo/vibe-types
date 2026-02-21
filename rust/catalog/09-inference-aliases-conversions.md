# Inference, Aliases, and Conversion Traits

## What it is

Type inference, aliases, and conversion traits shape how types are inferred and converted safely.

## What constraint it enforces

**Inferred and converted types must satisfy declared signatures and trait contracts.**

## Minimal snippet

```rust
use std::convert::TryFrom;

let n = i32::try_from(7_i64).unwrap(); // OK
let _x: i32 = n;
```

## Interaction with other features

- Complements modeling in `[-> catalog/04]`.
- Composes with generic bounds in `[-> catalog/05]`.
- Used in `[-> UC-01]` and `[-> UC-06]`.

## Gotchas and limitations

- Implicit conversions are intentionally limited.

## Use-case cross-references

- `[-> UC-01]`
- `[-> UC-06]`
