# Python — Type-Checking Constraint Techniques

> **Base path:** `/Users/jpablo/GitHub/vibe-types/python`

## Quick index (paste this into CLAUDE.md)

<!-- ~10 high-impact triggers. Prefer static type-checking guarantees over runtime checks.
     When one matches, read the full entry before recommending. -->

- Basic annotations & None handling: enforce types on params/returns; require None checks → `catalog/01`
- Union & Literal types: restrict values to declared alternatives; Literal for exact values → `catalog/02`
- TypedDict: enforce dict key names, value types, and required/optional presence → `catalog/03`
- Protocol (structural subtyping): static duck typing — verify method/attr presence without inheritance → `catalog/09`
- Generics & TypeVar: preserve type relationships; bounds restrict acceptable types → `catalog/07`
- ParamSpec: preserve function signatures through decorators → `catalog/08`
- TypeGuard & TypeIs: custom narrowing functions; exhaustive branch handling → `catalog/13`
- Final & frozen dataclass: prevent reassignment, override, and mutation → `catalog/12`, `catalog/06`
- Preventing invalid states: enums, Literal, NewType, Union — make invalid states unrepresentable → `usecases/01`
- Gradual adoption: add types incrementally; --strict mode; py.typed marker → `usecases/12`

---

## Full catalog (type system features → constraints they enforce)

- **Basic annotations, Optional, None** — variables/params/returns match declared types; None must be handled explicitly → `catalog/01-basic-annotations-none.md`
- **Union and Literal types** — value must be one of declared types or literal values → `catalog/02-union-literal-types.md`
- **TypedDict** — dict keys, value types, and required/optional presence enforced statically → `catalog/03-typeddict.md`
- **NewType** — distinct type prevents interchanging semantically different values → `catalog/04-newtype.md`
- **Enums with static typing** — values restricted to closed named set; exhaustiveness on match/case → `catalog/05-enums-typing.md`
- **Dataclasses and typed data modeling** — field types enforced; @dataclass_transform extends to third-party decorators → `catalog/06-dataclasses-typing.md`
- **Generics, TypeVar, bounded types** — generic code preserves type relationships; bounds restrict acceptable types → `catalog/07-generics-typevar.md`
- **ParamSpec and TypeVarTuple** — preserve callable signatures through decorators; variadic generics → `catalog/08-paramspec-typevar-tuple.md`
- **Protocol (structural subtyping)** — class satisfies Protocol if it has required methods/attrs — no inheritance needed → `catalog/09-protocol-structural-subtyping.md`
- **Abstract base classes** — subclasses must implement all abstract methods; cannot instantiate ABC directly → `catalog/10-abc-abstract-classes.md`
- **Callable types and @overload** — constrain function signatures as arguments; different return types per arg pattern → `catalog/11-callable-types-overload.md`
- **Final and ClassVar** — prevent reassignment/override; distinguish class-level from instance-level attrs → `catalog/12-final-classvar.md`
- **TypeGuard, TypeIs, and type narrowing** — user-defined narrowing functions the checker trusts; exhaustive branch analysis → `catalog/13-typeguard-typeis-narrowing.md`
- **Never and NoReturn** — mark functions that never return; bottom type for exhaustiveness proofs → `catalog/14-never-noreturn.md`
- **Annotated and type metadata** — attach metadata for runtime validators (Pydantic, beartype) while keeping base type visible → `catalog/15-annotated-metadata.md`
- **Self type** — methods return same type as the class they're called on; fluent/builder APIs → `catalog/16-self-type.md`
- **TypeAlias and the `type` statement** — explicit alias declarations; lazy evaluation and forward references → `catalog/17-type-aliases-type-statement.md`
- **Generic classes and variance** — user-defined generics preserve type-parameter relationships; variance prevents unsound substitutions → `catalog/18-generic-classes-variance.md`
- **Unpack and **kwargs typing** — constrain individual keyword argument types via TypedDict → `catalog/19-unpack-kwargs-typing.md`
- **Type inference, gradual typing, Any** — checker infers types; Any disables checks; --strict controls enforcement → `catalog/20-type-inference-gradual-typing.md`

## Use cases (problem → which features help)

- **Preventing invalid states** — only valid domain states are representable; invalid combinations are type errors (enums, Literal, NewType, Union) → `usecases/01-preventing-invalid-states.md`
- **Domain modeling** — domain primitives carry semantic meaning that prevents mix-ups (NewType, dataclasses, TypedDict, Annotated) → `usecases/02-domain-modeling.md`
- **Type narrowing and exhaustiveness** — after a check, the type is narrowed; all cases must be handled (isinstance, TypeGuard, TypeIs, assert_never) → `usecases/03-type-narrowing-exhaustiveness.md`
- **Generic constraints** — generic functions accept only types satisfying declared bounds (TypeVar, Protocol, ABC) → `usecases/04-generic-constraints.md`
- **Structural contracts** — duck typing gets static verification (Protocol) → `usecases/05-structural-contracts.md`
- **Immutability and finality** — values, attrs, and hierarchies cannot be modified after declaration (frozen dataclass, Final) → `usecases/06-immutability-finality.md`
- **API contracts and callable typing** — callback/decorator signatures preserve parameter and return types (Callable, ParamSpec, @overload) → `usecases/07-api-contracts-callable.md`
- **Error handling with types** — error paths tracked in the type system rather than try/except convention (Optional, Union results, NoReturn) → `usecases/08-error-handling-types.md`
- **Configuration and builder patterns** — required fields must be provided; config objects have validated shapes (TypedDict, dataclasses, Unpack) → `usecases/09-configuration-builder.md`
- **Typed dictionaries and records** — dictionary-shaped data has known keys with typed values (TypedDict, Literal, Annotated) → `usecases/10-typed-dictionaries-records.md`
- **Decorator typing** — decorators preserve or transform function signatures checker-visibly (ParamSpec, TypeVarTuple, Callable) → `usecases/11-decorator-typing.md`
- **Gradual adoption** — incrementally add type safety to an untyped codebase (basic annotations, Any, --strict) → `usecases/12-gradual-adoption.md`
