---
name: vibe-types:python
description: Python type-checking constraint techniques — annotations, Union, Literal, TypedDict, Protocol, generics, TypeGuard, Final, dataclasses. Use this skill whenever the user writes Python with type hints, mentions mypy or pyright, asks about typing module features, discusses Protocol, TypedDict, NewType, dataclasses, Literal, overload, ParamSpec, or any type annotation. Also use when adding types to untyped code or debugging type checker errors.
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
- **Effect tracking** *(via Result patterns)* — `T | Error` unions, context managers, exception groups → `catalog/T12-effect-tracking.md`
- **Metaprogramming** *(via decorators)* — decorators, metaclasses, `__init_subclass__`, `dataclass_transform` → `catalog/T17-macros-metaprogramming.md`
- **Type conversions** *(via dunder methods)* — `__int__`, `__float__`, `__str__`; no implicit conversions → `catalog/T18-conversions-coercions.md`
- **Equality safety** *(via __eq__)* — opt-in equality, `@dataclass(eq=True)`, Protocol for comparison → `catalog/T20-equality-safety.md`
- **Encapsulation** *(convention-based)* — `_private`, `__mangling`, `__all__`, `@property` → `catalog/T21-encapsulation.md`
- **Phantom types** *(via TYPE_CHECKING)* — `if TYPE_CHECKING:` guards, NewType for type-level tracking → `catalog/T27-erased-phantom.md`
- **Runtime polymorphism** *(via ABC/Protocol)* — ABC and Protocol as trait-object analogs → `catalog/T36-trait-objects.md`
- **Associated types** *(via Protocol members)* — Protocol type annotations, ClassVar, Generic output types → `catalog/T49-associated-types.md`

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
