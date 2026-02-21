# Generics and Where Clauses

## What it is

Generic parameters and `where` clauses constrain which types can instantiate APIs.

## What constraint it enforces

**Generic code compiles only when all declared bounds are satisfied.**

## Minimal snippet

```rust
fn stringify<T>(v: T) -> String
where
    T: ToString,
{
    v.to_string()
}
```

## Interaction with other features

- Depends on trait contracts in `[-> catalog/06]`.
- Extended by associated types in `[-> catalog/07]`.
- Drives `[-> UC-03]`, `[-> UC-06]`, `[-> UC-08]`.

## Gotchas and limitations

- Over-constraining bounds can reduce API usability.

## Use-case cross-references

- `[-> UC-03]`
- `[-> UC-06]`
- `[-> UC-08]`
