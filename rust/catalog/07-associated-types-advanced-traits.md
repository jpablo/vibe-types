# Associated Types and Advanced Traits

## What it is

Associated types and advanced trait features encode related type relationships in trait definitions.

## What constraint it enforces

**Implementations must provide consistent associated type choices per trait impl.**

## Minimal snippet

```rust
trait Parser {
    type Output;
    fn parse(&self, s: &str) -> Self::Output;
}
```

## Interaction with other features

- Refines generic constraints from `[-> catalog/05]`.
- Builds on base trait model in `[-> catalog/06]`.
- Supports `[-> UC-03]`.

## Gotchas and limitations

- Choosing associated types versus generic params affects API flexibility.

## Use-case cross-references

- `[-> UC-03]`
