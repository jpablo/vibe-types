---
name: vibe-types:python
description: Python type-checking constraint techniques — annotations, Union, Literal, TypedDict, Protocol, generics, TypeGuard, Final, dataclasses. Use this skill whenever the user writes Python with type hints, mentions mypy or pyright, asks about typing module features, discusses Protocol, TypedDict, NewType, dataclasses, Literal, overload, ParamSpec, or any type annotation. Also use when adding types to untyped code or debugging type checker errors.
version: 0.2.0
---

# Python — Type-Checking Constraint Techniques

> **Base path:** `${CLAUDE_PLUGIN_ROOT}/skills/python`

## Core tenets

Let the type checker carry as much of correctness as it can. The idea is to move guarantees out of runtime checks, tests, and discipline and into the types, so that holding a value is itself evidence that its invariants hold. Wherever you can, make a bad state impossible to express instead of checking for it later. Treat these as defaults to apply with judgment, not as absolute rules.

- **Make illegal states unrepresentable.** Model the data so that an invalid combination of values does not typecheck. → `usecases/UC01-invalid-states.md`
- **Parse, don't validate.** At the boundary, turn a check into a value of a refined type that proves the check ran, rather than returning a boolean and discarding what you learned. → `catalog/T26-refinement-types.md`
- **Keep a functional core and an imperative shell.** Put the decisions and computation in pure functions that take values and return values, and push the effects (input and output, network calls, database access, the clock, randomness) out to a thin outer layer that calls into that core. The core stays deterministic and easy to test and reason about, and the shell is the only part that talks to the outside world. → `usecases/UC11-effect-tracking.md`
- **Upgrade information at the edges; never re-acquire it in the core.** Every parse, check, or branch gains information. Capture it in a type at the boundary and pass it inward, so that the core relies on the evidence it already has instead of re-deriving it by checking or parsing again. This is the second half of parse-don't-validate, applied to every decision point and not just to input. → `catalog/T14-type-narrowing.md`
- **Prefer a more precise type over a less precise one.** A type is more precise when its inhabitants (the distinct values it can hold, so `Bool` has two and a three-case enum has three) match the values that are legal for the job, holding every value that should occur and as few as possible that should not. A practical rule: among the types that can represent every legal value, choose the one with the fewest inhabitants, since the extra inhabitants are exactly the values that should never occur and that you would otherwise have to check for. For a yes or no choice, `Bool` is more precise than `Int`; a closed enum is more precise than a `String`; `NonEmptyList` is more precise than `List`. A newtype covers a second case: `UserId` and `OrderId` may have the same number of inhabitants as the integer underneath, but as distinct types they can no longer be passed in place of one another. The limiting case, a type with no illegal inhabitants at all, is just make illegal states unrepresentable. → `catalog/T03-newtypes-opaque.md`
- **Add precision where a wrong value would do real harm, and leave low-stakes values plain.** A precise type costs some friction to introduce and use, so add it where that cost is worth it. Reach for one when a wrong value would pass unnoticed (nothing fails to signal it), when it would be expensive (money, access, lost data), when the value crosses a boundary (untrusted input, a public API, anything stored or sent), or when the same fact is relied on in many places or far from where it was first established. Leave a value plain when it is used once, locally, never branched on, and a wrong value would be obvious and harmless, such as a string you only display, a log message, or a one-off script. Before introducing a new type, ask which never-legal value it rules out and what it would cost if that value occurred; if it rules nothing out, keep the plain type.
- **Prefer types over tests to capture invariants.** If the compiler can enforce a property, do not write a test for it. Keep tests for the behavior that types cannot express.
- **Make functions total, and let the compiler force every case.** A total function is defined for every input its parameter types allow: no input makes it throw, hang, or return a meaningless result. There are two ways to get there. Widen the output, returning `Option` or `Result` so that "no answer" becomes a case the caller has to handle. Or narrow the input, for example taking a `NonEmptyList` so that `head` always has an answer. When you match, cover every constructor and avoid a catch-all case unless the set of cases is genuinely open, so that adding a variant later becomes a compile error instead of a silent fall-through. For a branch that genuinely cannot occur, close it with a value of an empty type (the uninhabited type, written `Nothing`, `Never`, `!`, or `Empty` depending on the language), which has no inhabitants and so proves the branch unreachable, rather than throwing a "can't happen" error that a later change can turn into a real crash. Finally, prefer a definition that provably terminates over one you only expect to terminate. → `usecases/UC03-exhaustiveness.md`, `catalog/T34-never-bottom.md`
- **Make immutability the default, and mark mutation as the exception.** A value that cannot change after it is constructed cannot quietly become invalid behind the check that vouched for it. Require an explicit, visible marker to opt into mutation or shared aliasing, so that the type records which values are allowed to change. → `catalog/T32-immutability-markers.md`
- **Use state machines when appropriate.** When an object has a lifecycle or a protocol, encode its states as types so that an invalid transition does not compile. These are the invariants that hold across time, between calls, rather than inside a single value. → `usecases/UC13-state-machines.md`
- **Pass authority as a typed value instead of reaching for ambient power.** The right to do something powerful or effectful is itself a value, and a function should receive it as an argument rather than reach for it on its own. Treat as authority the ability to use the filesystem, make a network call, read the clock or a source of randomness, read an environment variable or a secret, start a subprocess, or move money. A function that needs one of these should take it as a parameter (a `Clock`, an `HttpClient`, a `PaymentGateway`, and so on) instead of calling a global or a singleton. A function whose type does not name a given authority then cannot use it, the caller decides what to pass down, and the code becomes easy to test by passing a different value. → `catalog/T12-effect-tracking.md`

## Full catalog (type system features → constraints they enforce)

- **Basic annotations, Optional, None** — variables/params/returns match declared types; None must be handled explicitly → `catalog/T13-null-safety.md`
- **Union and Literal types** — value must be one of declared types or literal values → `catalog/T02-union-intersection.md`
- **TypedDict** — dict keys, value types, and required/optional presence enforced statically → `catalog/T31-record-types.md`
- **NewType** — distinct type prevents interchanging semantically different values → `catalog/T03-newtypes-opaque.md`
- **Enums with static typing** — values restricted to closed named set; exhaustiveness on match/case → `catalog/T01-algebraic-data-types.md`
- **Dataclasses and typed data modeling** — field types enforced; @dataclass_transform extends to third-party decorators → `catalog/T06-derivation.md`
- **Generics, TypeVar, bounded types** — generic code preserves type relationships; bounds restrict acceptable types → `catalog/T04-generics-bounds.md`
- **ParamSpec and TypeVarTuple** — preserve callable signatures through decorators; variadic generics → `catalog/T45-paramspec-variadic.md`
- **Protocol (structural subtyping)** — class satisfies Protocol if it has required methods/attrs — no inheritance needed → `catalog/T07-structural-typing.md`
- **Abstract base classes** — subclasses must implement all abstract methods; cannot instantiate ABC directly → `catalog/T05-type-classes.md`
- **Callable types and @overload** — constrain function signatures as arguments; different return types per arg pattern → `catalog/T22-callable-typing.md`
- **Final and ClassVar** — prevent reassignment/override; distinguish class-level from instance-level attrs → `catalog/T32-immutability-markers.md`
- **TypeGuard, TypeIs, and type narrowing** — user-defined narrowing functions the checker trusts; exhaustive branch analysis → `catalog/T14-type-narrowing.md`
- **Never and NoReturn** — mark functions that never return; bottom type for exhaustiveness proofs → `catalog/T34-never-bottom.md`
- **Annotated and type metadata** — attach metadata for runtime validators (Pydantic, beartype) while keeping base type visible → `catalog/T26-refinement-types.md`
- **Self type** — methods return same type as the class they're called on; fluent/builder APIs → `catalog/T33-self-type.md`
- **TypeAlias and the `type` statement** — explicit alias declarations; lazy evaluation and forward references → `catalog/T23-type-aliases.md`
- **Generic classes and variance** — user-defined generics preserve type-parameter relationships; variance prevents unsound substitutions → `catalog/T08-variance-subtyping.md`
- **Unpack and **kwargs typing** — constrain individual keyword argument types via TypedDict → `catalog/T46-kwargs-typing.md`
- **Type inference, gradual typing, Any** — checker infers types; Any disables checks; --strict controls enforcement → `catalog/T47-gradual-typing.md`
- **Literal types** — restrict parameters to specific values (`Literal["a", "b"]`); discriminate without enums → `catalog/T52-literal-types.md`
- **Effect tracking** *(via Result patterns)* — `T | Error` unions, context managers, exception groups → `catalog/T12-effect-tracking.md`
- **Metaprogramming** *(via decorators)* — decorators, metaclasses, `__init_subclass__`, `dataclass_transform` → `catalog/T17-macros-metaprogramming.md`
- **Type conversions** *(via dunder methods)* — `__int__`, `__float__`, `__str__`; no implicit conversions → `catalog/T18-conversions-coercions.md`
- **Equality safety** *(via __eq__)* — opt-in equality, `@dataclass(eq=True)`, Protocol for comparison → `catalog/T20-equality-safety.md`
- **Encapsulation** *(convention-based)* — `_private`, `__mangling`, `__all__`, `@property` → `catalog/T21-encapsulation.md`
- **Phantom types** *(via TYPE_CHECKING)* — `if TYPE_CHECKING:` guards, NewType for type-level tracking → `catalog/T27-erased-phantom.md`
- **Runtime polymorphism** *(via ABC/Protocol)* — ABC and Protocol as trait-object analogs → `catalog/T36-trait-objects.md`
- **Associated types** *(via Protocol members)* — Protocol type annotations, ClassVar, Generic output types → `catalog/T49-associated-types.md`

- **Typestate pattern** *(via Literal + overload)* — Generic state parameter, checker-enforced → `catalog/T57-typestate.md`
- **Existential types** *(via Protocol)* — interface without knowing concrete type → `catalog/T59-existential-types.md`
- **Recursive types** *(via forward references)* — recursive type aliases, annotations → `catalog/T61-recursive-types.md`
## Use cases (problem → which features help)

- **Preventing invalid states** — only valid domain states are representable; invalid combinations are type errors (enums, Literal, NewType, Union) → `usecases/UC01-invalid-states.md`
- **Domain modeling** — domain primitives carry semantic meaning that prevents mix-ups (NewType, dataclasses, TypedDict, Annotated) → `usecases/UC02-domain-modeling.md`
- **Type narrowing and exhaustiveness** — after a check, the type is narrowed; all cases must be handled (isinstance, TypeGuard, TypeIs, assert_never) → `usecases/UC03-exhaustiveness.md`
- **Generic constraints** — generic functions accept only types satisfying declared bounds (TypeVar, Protocol, ABC) → `usecases/UC04-generic-constraints.md`
- **Structural contracts** — duck typing gets static verification (Protocol) → `usecases/UC05-structural-contracts.md`
- **Immutability and finality** — values, attrs, and hierarchies cannot be modified after declaration (frozen dataclass, Final) → `usecases/UC06-immutability.md`
- **API contracts and callable typing** — callback/decorator signatures preserve parameter and return types (Callable, ParamSpec, @overload) → `usecases/UC07-callable-contracts.md`
- **Error handling with types** — error paths tracked in the type system rather than try/except convention (Optional, Union results, NoReturn) → `usecases/UC08-error-handling.md`
- **Configuration and builder patterns** — required fields must be provided; config objects have validated shapes (TypedDict, dataclasses, Unpack) → `usecases/UC09-builder-config.md`
