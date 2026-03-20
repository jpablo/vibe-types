# Rust Core Docs Findings

## Scope

- Source: `/Users/jpablo/GitHub/rust`
- Snapshot: `59fd4ef94daa` (2026-02-20)

## Priority Files (Available)

- `src/doc/rustc-dev-guide/src/generic-parameters-summary.md`
- `src/doc/rustc-dev-guide/src/typing-parameter-envs.md`
- `src/doc/rustc-dev-guide/src/type-inference.md`
- `src/doc/rustc-dev-guide/src/coherence.md`
- `src/doc/rustc-dev-guide/src/const-generics.md`
- `src/doc/rustc-dev-guide/src/variance.md`
- `src/doc/rustc-dev-guide/src/borrow-check.md`
- `src/doc/rustc-dev-guide/src/opaque-types-impl-trait-inference.md`
- `src/doc/rustc-dev-guide/src/opaque-types-type-alias-impl-trait.md`
- `src/doc/rustc-dev-guide/src/solve/trait-solving.md`
- `src/doc/rustc-dev-guide/src/solve/canonicalization.md`
- `src/doc/rustc-dev-guide/src/traits/resolution.md`
- `src/doc/rustc-dev-guide/src/traits/implied-bounds.md`
- `src/doc/rustc-dev-guide/src/traits/specialization.md`

## Priority Files (Now Available)

- `src/doc/reference/src/type-system.md`
- `src/doc/reference/src/items/generics.md`
- `src/doc/reference/src/trait-bounds.md`
- `src/doc/reference/src/lifetime-elision.md`
- `src/doc/reference/src/subtyping.md`

`src/doc/reference` is initialized in the local checkout.

## Extraction Order

1. Rust Reference (when available) as canonical surface-language semantics.
2. rustc-dev-guide core typing docs (`type-inference`, `param-env`, `coherence`).
3. Trait solving internals (`traits/*`, `solve/*`).
4. Const generics and advanced opaque/impl-trait behavior.

## Candidate Feature Buckets

- Canonical generic/trait/lifetime semantics.
- Trait solver obligations and coherence.
- Inference and parameter environment machinery.
- Const generics and opaque/impl-trait typing.
- Variance/subtyping and borrow-check relations.

## Candidate Use-Case Buckets

- Explain why specific trait bounds pass/fail at compile time.
- Explain orphan/coherence failures and overlap errors.
- Explain lifetime/borrow diagnosis with param-env context.
- Explain const generic constraints and inference boundaries.

## Gaps and Risks

- rustc-dev-guide includes implementation details that may evolve quickly.
- Some internals do not map 1:1 to user-facing documentation language.
