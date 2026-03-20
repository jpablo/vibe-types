# Python Type System Constraint Guide

> Status: **In Progress**

This section maps Python's type system features — type hints, the `typing` module, and static checkers (mypy/pyright) — to the constraints they enforce at check time.

Python's key difference from compiled languages: constraints are enforced by **static type checkers** rather than a compiler. The `typing` module has evolved from 3.5 → 3.13, with backports via `typing_extensions`.

---

## Part I: Feature Catalog

One document per type system feature. Each answers: *Given this feature, what constraints can my type checker enforce?*

| # | Document | Feature | Key constraint | Since |
|---|----------|---------|----------------|-------|
| 00 | [Reading Guide](catalog/00-overview.md) | — | — | — |
| 01 | [Basic Annotations, Optional, None](catalog/01-basic-annotations-none.md) | Type annotations and None handling | Variables/params/returns match declared types; `None` must be handled explicitly | 3.5; `X \| Y` 3.10 |
| 02 | [Union and Literal Types](catalog/02-union-literal-types.md) | Union and Literal | Value must be one of declared types or literal values | 3.5; `Literal` 3.8; `X \| Y` 3.10 |
| 03 | [TypedDict](catalog/03-typeddict.md) | TypedDict | Dict keys, value types, and required/optional presence enforced | 3.8; `Required`/`NotRequired` 3.11 |
| 04 | [NewType](catalog/04-newtype.md) | NewType | Distinct type prevents interchanging semantically different values | 3.5.2 |
| 05 | [Enums with Static Typing](catalog/05-enums-typing.md) | Enums | Values restricted to closed named set; exhaustiveness on match/case | 3.4; `StrEnum` 3.11 |
| 06 | [Dataclasses and Typed Data Modeling](catalog/06-dataclasses-typing.md) | Dataclasses | Field types enforced; `@dataclass_transform` extends to third-party | 3.7; `dataclass_transform` 3.12 |
| 07 | [Generics, TypeVar, Bounded Types](catalog/07-generics-typevar.md) | Generics and TypeVar | Generic code preserves type relationships; bounds restrict types | 3.5; new syntax 3.12 |
| 08 | [ParamSpec and TypeVarTuple](catalog/08-paramspec-typevar-tuple.md) | ParamSpec, TypeVarTuple | Preserve callable signatures through decorators; variadic generics | `ParamSpec` 3.10; `TypeVarTuple` 3.11 |
| 09 | [Protocol (Structural Subtyping)](catalog/09-protocol-structural-subtyping.md) | Protocol | Class satisfies Protocol if it has required methods/attrs — no inheritance | 3.8 |
| 10 | [Abstract Base Classes](catalog/10-abc-abstract-classes.md) | ABC | Subclasses must implement all abstract methods; cannot instantiate ABC | 3.0; typing 3.5+ |
| 11 | [Callable Types and @overload](catalog/11-callable-types-overload.md) | Callable, @overload | Constrain function signatures as arguments; per-pattern return types | 3.5; Protocol `__call__` 3.8 |
| 12 | [Final and ClassVar](catalog/12-final-classvar.md) | Final, ClassVar | Prevent reassignment/override; distinguish class vs instance attrs | `Final` 3.8; `ClassVar` 3.5.3 |
| 13 | [TypeGuard, TypeIs, Narrowing](catalog/13-typeguard-typeis-narrowing.md) | TypeGuard, TypeIs | User-defined narrowing the checker trusts; exhaustive branch analysis | `TypeGuard` 3.10; `TypeIs` 3.13 |
| 14 | [Never and NoReturn](catalog/14-never-noreturn.md) | Never, NoReturn | Mark functions that never return; bottom type for exhaustiveness | `NoReturn` 3.5.4; `Never` 3.11 |
| 15 | [Annotated and Type Metadata](catalog/15-annotated-metadata.md) | Annotated | Attach metadata for runtime validators while keeping base type visible | 3.9 |
| 16 | [Self Type](catalog/16-self-type.md) | Self | Methods return same type as the class they're called on | 3.11 |
| 17 | [TypeAlias and the `type` Statement](catalog/17-type-aliases-type-statement.md) | TypeAlias, `type` | Explicit alias declarations; lazy evaluation and forward references | `TypeAlias` 3.10; `type` 3.12 |
| 18 | [Generic Classes and Variance](catalog/18-generic-classes-variance.md) | Variance | User-defined generics preserve type-parameter relationships | 3.5; new syntax 3.12 |
| 19 | [Unpack and **kwargs Typing](catalog/19-unpack-kwargs-typing.md) | Unpack | Constrain individual keyword argument types via TypedDict | 3.12 |
| 20 | [Type Inference, Gradual Typing, Any](catalog/20-type-inference-gradual-typing.md) | Inference, Any | Checker infers types; `Any` disables checks; `--strict` controls enforcement | 3.5+ |

## Part II: Use-Case Index

One document per constraint category. Each answers: *I want my type checker to enforce X; which features help?*

| # | Document | Constraint |
|---|----------|-----------|
| 00 | [Navigation Guide](usecases/00-overview.md) | — |
| 01 | [Preventing Invalid States](usecases/01-preventing-invalid-states.md) | Only valid domain states are representable; invalid combinations are type errors |
| 02 | [Domain Modeling](usecases/02-domain-modeling.md) | Domain primitives carry semantic meaning that prevents mix-ups |
| 03 | [Type Narrowing and Exhaustiveness](usecases/03-type-narrowing-exhaustiveness.md) | After a check, the type is narrowed; all cases must be handled |
| 04 | [Generic Constraints](usecases/04-generic-constraints.md) | Generic functions accept only types satisfying declared bounds |
| 05 | [Structural Contracts](usecases/05-structural-contracts.md) | Duck typing gets static verification via Protocol |
| 06 | [Immutability and Finality](usecases/06-immutability-finality.md) | Values, attrs, and hierarchies cannot be modified after declaration |
| 07 | [API Contracts and Callable Typing](usecases/07-api-contracts-callable.md) | Callback/decorator signatures preserve parameter and return types |
| 08 | [Error Handling with Types](usecases/08-error-handling-types.md) | Error paths tracked in the type system rather than try/except convention |
| 09 | [Configuration and Builder Patterns](usecases/09-configuration-builder.md) | Required fields must be provided; config objects have validated shapes |
| 10 | [Typed Dictionaries and Records](usecases/10-typed-dictionaries-records.md) | Dictionary-shaped data has known keys with typed values |
| 11 | [Decorator Typing](usecases/11-decorator-typing.md) | Decorators preserve or transform function signatures checker-visibly |
| 12 | [Gradual Adoption](usecases/12-gradual-adoption.md) | Incrementally add type safety to an untyped codebase |

---

## Cross-references

- [Feature × Use-Case Matrix](../appendix/feature-matrix.md) — see which features solve which problems
- [Glossary](../appendix/glossary.md) — shared terminology
- [Further Reading](../appendix/further-reading.md) — official docs and community resources

See the [main README](../README.md) for the full project overview.
