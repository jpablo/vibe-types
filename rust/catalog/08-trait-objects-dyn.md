# Trait Objects and dyn

## What it is

`dyn Trait` enables runtime polymorphism via vtables when object safety rules are met.

## What constraint it enforces

**Only object-safe trait methods are callable through trait objects.**

## Minimal snippet

```rust
trait Draw {
    fn draw(&self);
}

fn paint(x: &dyn Draw) {
    x.draw();
}
```

## Interaction with other features

- Alternative to static dispatch in `[-> catalog/05]` and `[-> catalog/06]`.
- Used for extensibility in `[-> UC-04]`.

## Gotchas and limitations

- Generic methods are not object-safe by default.

## Use-case cross-references

- `[-> UC-04]`
