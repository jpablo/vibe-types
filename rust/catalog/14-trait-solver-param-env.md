# Trait Solver and Parameter Environments

## What it is

The compiler solves trait obligations in a parameter environment derived from in-scope bounds.

## What constraint it enforces

**A trait obligation is accepted only when the solver can prove it in the active `ParamEnv` built from in-scope bounds.**

## Minimal snippet

```rust
trait Alias: Clone {}

fn promote<T: Alias>(value: T) -> T {
    value.clone() // ParamEnv elaborates `Alias: Clone`, so the Clone goal is provable.
}
```

## Interaction with other features

- Underpins generic checks in `[-> catalog/05]` and `[-> catalog/06]`.
- Relevant for diagnosis in `[-> UC-07]`.

## Gotchas and limitations

- `ParamEnv` elaboration can add implied/supertrait assumptions, so diagnostics may mention bounds you did not write directly.
- Proving a goal with the wrong environment can fail even when a matching impl exists.

### Beginner mental model

The parameter environment (`ParamEnv`) is the compiler’s notebook of assumptions: it records the bounds you’ve written plus any implied rules (like supertraits). When you use a trait, the solver checks if it can prove a chain of obligations from that notebook before approving the code.

### Example A

```rust
trait Verbose: std::fmt::Display {}

fn shout<T: Verbose>(value: T) {
    println!("{}", value); // ParamEnv knows Verbose implies Display, so Display formatting is available.
}
```

### Example B

```rust
trait Alias: Clone + Send {}

fn run<T: Alias + 'static>(t: T) {
    std::thread::spawn(move || {
        t.clone(); // Clone goal proven because ParamEnv inherited it from Alias.
    });
}
```

### Common compiler errors and how to read them

- `the trait bound T: Clone is not satisfied` means no proof path is available in the current bounds; add an explicit bound or ensure your alias/supertrait really includes `Clone`.
- `the requirement \`T: Trait\` is not satisfied in the current environment` – the solver can only use bounds in scope; add the missing bound to the function or impl header.
- `impl Trait for Type` conflicts because `ParamEnv` includes enough assumptions to consider another impl – watch for blanket impls or overlapping where clauses that the solver now sees as overlapping.

## Use-case cross-references

- `[-> UC-07]`

## Source anchors

- `rust/src/doc/reference/src/trait-bounds.md`
- `rust/src/doc/reference/src/type-system.md`
- `rust/src/doc/rustc-dev-guide/src/typing-parameter-envs.md`
- `rust/src/doc/rustc-dev-guide/src/solve/trait-solving.md`
