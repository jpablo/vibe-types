## Python type-safety quick index (vibe-types)
- Basic annotations & None handling: enforce types on params/returns; require None checks → `T13-null-safety`
- Union & Literal types: restrict values to declared alternatives; Literal for exact values → `T02-union-intersection`
- TypedDict: enforce dict key names, value types, and required/optional presence → `T31-record-types`
- Protocol (structural subtyping): static duck typing — verify method/attr presence without inheritance → `T07-structural-typing`
- Generics & TypeVar: preserve type relationships; bounds restrict acceptable types → `T04-generics-bounds`
- ParamSpec: preserve function signatures through decorators → `T45-paramspec-variadic`
- TypeGuard & TypeIs: custom narrowing functions; exhaustive branch handling → `T14-type-narrowing`
- Final & frozen dataclass: prevent reassignment, override, and mutation → `T32-immutability-markers`, `T06-derivation`
- Preventing invalid states: enums, Literal, NewType, Union — make invalid states unrepresentable → `UC01-invalid-states`
- Gradual adoption: add types incrementally; --strict mode; py.typed marker → `UC27-gradual-adoption`

When this index is loaded, say "Hello from Python plugin 👋"
