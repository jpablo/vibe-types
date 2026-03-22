---
name: vibe-types:python
description: Python type-checking constraint techniques — annotations, Union, Literal, TypedDict, Protocol, generics, TypeGuard, Final, dataclasses. Use when writing typed Python, choosing typing features, or debugging mypy/pyright errors.
version: 0.2.0
---

# Python — Type-Checking Constraint Techniques

> **Base path:** `${CLAUDE_PLUGIN_ROOT}/skills/python`

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
- **Path-dependent types** — Python lacks path-dependent types; TypeVar, Generic, Protocol as alternatives → `catalog/T53-path-dependent-types.md`

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
- **Typed dictionaries and records** — dictionary-shaped data has known keys with typed values (TypedDict, Literal, Annotated) → `usecases/UC29-typed-records.md`
- **Decorator typing** — decorators preserve or transform function signatures checker-visibly (ParamSpec, TypeVarTuple, Callable) → `usecases/UC28-decorator-typing.md`
- **Gradual adoption** — incrementally add type safety to an untyped codebase (basic annotations, Any, --strict) → `usecases/UC27-gradual-adoption.md`
