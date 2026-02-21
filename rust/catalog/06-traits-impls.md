# Traits and Implementations

## What it is

Traits define behavior contracts; implementations provide concrete behavior per type.

## What constraint it enforces

**Types must satisfy trait contracts before using trait-constrained APIs.**

## Minimal snippet

```rust
trait Render {
    fn render(&self) -> String;
}

fn draw<T: Render>(x: &T) -> String {
    x.render()
}
```

## Interaction with other features

- Used by generics in `[-> catalog/05]`.
- Advanced forms in `[-> catalog/07]` and `[-> catalog/08]`.
- Core to `[-> UC-03]`, `[-> UC-04]`, `[-> UC-07]`.

## Gotchas and limitations

- Coherence/orphan restrictions are covered in `[-> catalog/13]`.

## Use-case cross-references

- `[-> UC-03]`
- `[-> UC-04]`
- `[-> UC-05]`
- `[-> UC-07]`
