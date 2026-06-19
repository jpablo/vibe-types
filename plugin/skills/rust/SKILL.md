---
name: vibe-types:rust
description: Rust compile-time safety techniques — ownership, borrowing, lifetimes, traits, generics, Send/Sync, const generics. Use this skill whenever the user writes Rust code, mentions ownership or borrowing, asks about lifetime errors, discusses trait bounds, Send/Sync, derive macros, PhantomData, newtype patterns, or any Rust type system feature. Also use when debugging borrow checker errors or porting type patterns from Scala, Python, or Haskell to Rust.
version: 0.2.0
---

# Rust — Compile-Time Safety Techniques

> **Base path:** `${CLAUDE_PLUGIN_ROOT}/skills/rust`

## Core tenets

Let the type checker carry as much of correctness as it can. The idea is to move guarantees out of runtime checks, tests, and discipline and into the types, so that holding a value is itself evidence that its invariants hold. Wherever you can, make a bad state impossible to express instead of checking for it later. Treat these as defaults to apply with judgment, not as absolute rules.

- **Make illegal states unrepresentable.** Model the data so that an invalid combination of values does not typecheck. → `usecases/UC01-invalid-states.md`
- **Parse, don't validate.** At the boundary, turn a check into a value of a refined type that proves the check ran, rather than returning a boolean and discarding what you learned. → `catalog/T26-refinement-types.md`
- **Keep a functional core and an imperative shell.** Put the decisions and computation in pure functions that take values and return values, and push the effects (input and output, network calls, database access, the clock, randomness) out to a thin outer layer that calls into that core. The core stays deterministic and easy to test and reason about, and the shell is the only part that talks to the outside world. → `usecases/UC11-effect-tracking.md`
- **Upgrade information at the edges; never re-acquire it in the core.** Every parse, check, or branch gains information. Capture it in a type at the boundary and pass it inward, so that the core relies on the evidence it already has instead of re-deriving it by checking or parsing again. This is the second half of parse-don't-validate, applied to every decision point and not just to input. → `catalog/T58-witness-evidence.md`
- **Prefer a more precise type over a less precise one.** A type is more precise when its inhabitants (the distinct values it can hold, so `Bool` has two and a three-case enum has three) match the values that are legal for the job, holding every value that should occur and as few as possible that should not. A practical rule: among the types that can represent every legal value, choose the one with the fewest inhabitants, since the extra inhabitants are exactly the values that should never occur and that you would otherwise have to check for. For a yes or no choice, `Bool` is more precise than `Int`; a closed enum is more precise than a `String`; `NonEmptyList` is more precise than `List`. A newtype covers a second case: `UserId` and `OrderId` may have the same number of inhabitants as the integer underneath, but as distinct types they can no longer be passed in place of one another. The limiting case, a type with no illegal inhabitants at all, is just make illegal states unrepresentable. → `catalog/T03-newtypes-opaque.md`
- **Add precision where a wrong value would do real harm, and leave low-stakes values plain.** A precise type costs some friction to introduce and use, so add it where that cost is worth it. Reach for one when a wrong value would pass unnoticed (nothing fails to signal it), when it would be expensive (money, access, lost data), when the value crosses a boundary (untrusted input, a public API, anything stored or sent), or when the same fact is relied on in many places or far from where it was first established. Leave a value plain when it is used once, locally, never branched on, and a wrong value would be obvious and harmless, such as a string you only display, a log message, or a one-off script. Before introducing a new type, ask which never-legal value it rules out and what it would cost if that value occurred; if it rules nothing out, keep the plain type.
- **Prefer types over tests to capture invariants.** If the compiler can enforce a property, do not write a test for it. Keep tests for the behavior that types cannot express.
- **Make functions total, and let the compiler force every case.** A total function is defined for every input its parameter types allow: no input makes it throw, hang, or return a meaningless result. There are two ways to get there. Widen the output, returning `Option` or `Result` so that "no answer" becomes a case the caller has to handle. Or narrow the input, for example taking a `NonEmptyList` so that `head` always has an answer. When you match, cover every constructor and avoid a catch-all case unless the set of cases is genuinely open, so that adding a variant later becomes a compile error instead of a silent fall-through. For a branch that genuinely cannot occur, close it with a value of an empty type (the uninhabited type, written `Nothing`, `Never`, `!`, or `Empty` depending on the language), which has no inhabitants and so proves the branch unreachable, rather than throwing a "can't happen" error that a later change can turn into a real crash. Finally, prefer a definition that provably terminates over one you only expect to terminate. → `usecases/UC03-exhaustiveness.md`, `catalog/T34-never-bottom.md`
- **Make immutability the default, and mark mutation as the exception.** A value that cannot change after it is constructed cannot quietly become invalid behind the check that vouched for it. Require an explicit, visible marker to opt into mutation or shared aliasing, so that the type records which values are allowed to change. → `catalog/T32-immutability-markers.md`
- **Use state machines when appropriate.** When an object has a lifecycle or a protocol, encode its states as types so that an invalid transition does not compile. These are the invariants that hold across time, between calls, rather than inside a single value. → `usecases/UC13-state-machines.md`
- **Pass authority as a typed value instead of reaching for ambient power.** The right to do something powerful or effectful is itself a value, and a function should receive it as an argument rather than reach for it on its own. Treat as authority the ability to use the filesystem, make a network call, read the clock or a source of randomness, read an environment variable or a secret, start a subprocess, or move money. A function that needs one of these should take it as a parameter (a `Clock`, an `HttpClient`, a `PaymentGateway`, and so on) instead of calling a global or a singleton. A function whose type does not name a given authority then cannot use it, the caller decides what to pass down, and the code becomes easy to test by passing a different value. → `catalog/T12-effect-tracking.md`

## Full catalog (type system features → constraints they enforce)

- **Ownership & moves** — prevent use-after-free and double-free; ensure deterministic cleanup → `catalog/T10-ownership-moves.md`
- **Borrowing & mutability** — eliminate data races and iterator invalidation via aliasing rules (`&T` xor `&mut T`) → `catalog/T11-borrowing-mutability.md`
- **Lifetimes** — prevent dangling references; prove every reference valid for its usage → `catalog/T48-lifetimes.md`
- **Structs, enums, newtypes** — make invalid states unrepresentable; exhaustive match forces handling all variants → `catalog/T01-algebraic-data-types.md`
- **Generics & where clauses** — generic code compiles only when operations are justified by declared bounds → `catalog/T04-generics-bounds.md`
- **Traits & impls** — enforce contracts on types; one impl per trait-type pair globally → `catalog/T05-type-classes.md`
- **Associated types & advanced traits** — lock output types per implementor; reduce caller confusion → `catalog/T49-associated-types.md`
- **Trait objects (`dyn`)** — runtime polymorphism when concrete types are unknown; only object-safe traits qualify → `catalog/T36-trait-objects.md`
- **Inference, aliases, conversions** — maintain type safety while permitting local inference; no silent conversions → `catalog/T18-conversions-coercions.md`
- **Smart pointers & interior mutability** — flexible ownership (shared, interior-mutable) while preserving memory safety → `catalog/T24-smart-pointers.md`
- **Send & Sync** — prevent data races at compile time by controlling what crosses thread boundaries → `catalog/T50-send-sync.md`
- **Const generics** — encode sizes, dimensions, capacities in types; distinct values = distinct types → `catalog/T15-const-generics.md`
- **Coherence & orphan rules** — prevent conflicting impls across crates; ensure independent publishing → `catalog/T25-coherence-orphan.md`
- **Trait solver & param env** — deterministic zero-cost trait resolution; guides correct bounds → `catalog/T37-trait-solver.md`
- **Refinement types** — newtype + smart constructor pattern; validated values with private fields; nutype derive macro → `catalog/T26-refinement-types.md`
- **Literal types** — Rust lacks first-class literal types; const generics, enums, and `typenum` serve as alternatives → `catalog/T52-literal-types.md`
- **Path-dependent types** — associated types as path-dependent analogs; GATs for higher-kinded path dependence → `catalog/T53-path-dependent-types.md`
- **Newtypes** — zero-cost wrapper types with private fields; prevent value mix-ups → `catalog/T03-newtypes-opaque.md`
- **Derive macros** — `#[derive(Debug, Clone, Serialize)]`; auto-generate trait impls from structure → `catalog/T06-derivation.md`
- **Null safety** — no null in Rust; `Option<T>` enforces handling of absent values → `catalog/T13-null-safety.md`
- **Type narrowing** — `if let`, `match`, `let-else`; exhaustive pattern matching → `catalog/T14-type-narrowing.md`
- **Compile-time computation** — `const fn`, `const` blocks, compile-time evaluation → `catalog/T16-compile-time-ops.md`
- **Macros** — `macro_rules!`, proc macros, `syn`/`quote` for code generation → `catalog/T17-macros-metaprogramming.md`
- **Equality safety** — `PartialEq`/`Eq` are opt-in; no accidental cross-type equality → `catalog/T20-equality-safety.md`
- **Encapsulation** — `pub`/`pub(crate)`/private-by-default module system → `catalog/T21-encapsulation.md`
- **Callable typing** — `Fn`/`FnMut`/`FnOnce` trait hierarchy; closures and function pointers → `catalog/T22-callable-typing.md`
- **Type aliases** — `type Alias = ConcreteType`; transparent aliases vs newtypes → `catalog/T23-type-aliases.md`
- **Phantom types** — `PhantomData<T>` for variance control, typestate, lifetime markers → `catalog/T27-erased-phantom.md`
- **Record types** — named-field structs; struct update syntax; destructuring → `catalog/T31-record-types.md`
- **Immutability** — immutable by default; `mut` is opt-in; `const` for compile-time constants → `catalog/T32-immutability-markers.md`
- **Self type** — `Self` refers to the implementing type; builders, `From`/`Into` → `catalog/T33-self-type.md`
- **Never type** — `!` bottom type; `Infallible`; empty enums; coerces to any type → `catalog/T34-never-bottom.md`
- **Union types** *(via enums)* — enums as sum types; trait bounds as intersection → `catalog/T02-union-intersection.md`
- **Structural typing** *(via traits)* — nominal typing with trait-based contracts → `catalog/T07-structural-typing.md`
- **Variance** *(implicit rules)* — compiler-inferred variance; `PhantomData` for control → `catalog/T08-variance-subtyping.md`
- **Effect tracking** *(via Result)* — `Result<T,E>` + `?`; `async`/`await`; `unsafe` boundaries → `catalog/T12-effect-tracking.md`
- **Extension methods** *(via traits)* — extension trait pattern; orphan rules → `catalog/T19-extension-methods.md`

- **Functor / Monad** *(via Iterator/Option/Result)* — map, and_then, ? operator → `catalog/T54-functor-applicative-monad.md`
- **Monad transformers** *(via middleware)* — tower layers, async middleware → `catalog/T55-monad-transformers.md`
- **Tagless final** *(via trait DI)* — trait-based dependency injection → `catalog/T56-tagless-final.md`
- **Typestate pattern** — PhantomData for zero-cost state encoding; canonical Rust pattern → `catalog/T57-typestate.md`
- **Witness types** *(via PhantomData markers)* — compile-time evidence of preconditions → `catalog/T58-witness-evidence.md`
- **Existential types** — dyn Trait, impl Trait; type erasure with contracts → `catalog/T59-existential-types.md`
- **Linear / affine types** — ownership IS affine typing; each value used at most once (linear would require exactly once) → `catalog/T60-linear-affine.md`
- **Recursive types** — enum + Box for indirection; compiler requires known size → `catalog/T61-recursive-types.md`
## Use cases (problem → which features help)

- **Preventing invalid states** — represent only valid domain states so invalid combinations won't compile (enums, newtypes, phantom types) → `usecases/UC01-invalid-states.md`
- **Ownership-safe APIs** — encode ownership transfer, borrowing, and lifetimes in signatures to prevent use-after-free in caller code → `usecases/UC20-ownership-apis.md`
- **Generic capability constraints** — accept only types satisfying required traits; reject unsuitable types with clear errors → `usecases/UC04-generic-constraints.md`
- **Extensible polymorphic interfaces** — allow plugins/alternative implementations without losing compile-time safety → `usecases/UC14-extensibility.md`
- **Compile-time concurrency** — threaded code compiles only when transfer and sharing are safe (`Send`/`Sync`) → `usecases/UC21-concurrency.md`
- **Value-level invariants with types** — encode lengths, dimensions, shapes in types so mismatches are caught at compile time → `usecases/UC18-type-arithmetic.md`
