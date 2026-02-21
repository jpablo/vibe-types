# Send and Sync

## What it is

`Send` and `Sync` are marker traits that express thread-transfer and shared-reference safety.

## What constraint it enforces

**Types that are not `Send`/`Sync` cannot cross thread-safety boundaries in unsafe ways.**

## Minimal snippet

```rust
fn assert_send<T: Send>() {}

assert_send::<String>(); // OK
```

## Interaction with other features

- Built on trait system in `[-> catalog/06]`.
- Common with smart pointers in `[-> catalog/10]`.
- Central to `[-> UC-05]`.

## Gotchas and limitations

- Auto-trait behavior can be surprising with interior mutability types.

## Use-case cross-references

- `[-> UC-05]`
