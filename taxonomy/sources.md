# Source Material

References and primary sources used to build the catalog and use-case documents.

## Cross-language

- [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/) — Alexis King, 2019. Core principle: validation discards information, parsing preserves it in the type system. Applies to UC01-invalid-states and T03-newtypes-opaque across all languages.
- [Lean for Scala programmers](https://typista.org/lean-for-scala-programmers/) — Typista.org, 4-part series. Rosetta Stone between Scala 3 and Lean 4 type systems: ADTs ↔ inductives, GADTs ↔ indexed families, givens ↔ type classes, match types ↔ dependent functions, Sigma types. Enriches T01, T05, T09, T35, T53.

## Scala 3

- [Dotty / Scala 3 Compiler](https://github.com/scala/scala3) — https://docs.scala-lang.org/scala3/
- [Iron](https://github.com/Iltotore/iron) — Scala 3-native refinement types via opaque types + inline. T26-refinement-types.
- [refined](https://github.com/fthomas/refined) — Refinement types for Scala 2 & 3 with broad ecosystem integrations. T26-refinement-types.

## Python

- [Python `typing` documentation](https://docs.python.org/3/library/typing.html) — canonical reference for `TypedDict`, `AsyncIterator`, `AsyncGenerator`, `Annotated`, `NewType`, `Literal`, `TypeGuard`, `TypeIs`, `assert_never`, and related typing constructs.
- [Python `collections.abc` documentation](https://docs.python.org/3/library/collections.abc.html) — runtime ABCs and generic protocols for `AsyncIterable`, `AsyncIterator`, `Awaitable`, `Coroutine`, and stream-like APIs. T64-async-iteration and UC21-concurrency.
- [Python `json` documentation](https://docs.python.org/3/library/json.html) — standard JSON boundary where untyped decoded data must be parsed into typed wire/domain models. UC19-serialization.
- [PEP 492 — Coroutines with async and await syntax](https://peps.python.org/pep-0492/) — introduces native coroutine syntax and asynchronous iteration protocol. T64-async-iteration and UC21-concurrency.
- [PEP 525 — Asynchronous Generators](https://peps.python.org/pep-0525/) — introduces `async def` generators and async generator protocol. T64-async-iteration.
- [PEP 589 — TypedDict](https://peps.python.org/pep-0589/) — fixed-key dictionary shapes for JSON-like objects. T31-record-types and UC19-serialization.
- [PEP 655 — Required / NotRequired TypedDict items](https://peps.python.org/pep-0655/) — per-key requiredness for TypedDict payloads. T31-record-types and UC09-builder-config.
- [PEP 705 — ReadOnly TypedDict items](https://peps.python.org/pep-0705/) — read-only fields for TypedDict wire shapes. T31-record-types and UC19-serialization.
- [PEP 681 — Data Class Transforms](https://peps.python.org/pep-0681/) — lets dataclass-like libraries expose generated fields and constructors to static checkers. T06-derivation and UC19-serialization.
- [Pydantic serialization docs](https://docs.pydantic.dev/latest/concepts/serialization/) — schema/model serialization patterns for runtime-validated Python models. UC19-serialization.
- [mypy TypedDict docs](https://mypy.readthedocs.io/en/stable/typed_dict.html) — checker behavior for TypedDict shape validation, required keys, and structural compatibility. T31-record-types and UC19-serialization.

## Rust

- [The Rust Programming Language (The Book)](https://github.com/rust-lang/book) — https://doc.rust-lang.org/book/
- [Rust by Example](https://github.com/rust-lang/rust-by-example) — https://doc.rust-lang.org/rust-by-example/
- [Rust Reference / Standard Library / Compiler](https://github.com/rust-lang/rust) — https://doc.rust-lang.org/reference/
- [nutype](https://github.com/greyblake/nutype) — Derive macro for validated newtypes with serde support. T26-refinement-types.

## Lean 4

- [Functional Programming in Lean](https://github.com/leanprover/fp-lean) — https://lean-lang.org/functional_programming_in_lean/
- [Simulating Subtyping and OO Polymorphism in Lean](https://typista.org/subtyping-and-polymorphism-in-lean/) — Typista.org. Coercions + type classes for runtime polymorphism. T36-trait-objects.
- [Theorem Proving in Lean 4](https://github.com/leanprover/theorem_proving_in_lean4) — https://lean-lang.org/theorem_proving_in_lean4/
- [Lean 4 Documentation](https://github.com/leanprover/lean4) — https://lean-lang.org/doc/reference/latest/
- [Lean 4 Metaprogramming Book](https://github.com/leanprover-community/lean4-metaprogramming-book) — https://leanprover-community.github.io/lean4-metaprogramming-book/
- [Mathlib4](https://github.com/leanprover-community/mathlib4) — https://leanprover-community.github.io/mathlib4_docs/
