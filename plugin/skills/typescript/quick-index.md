## TypeScript type-safety quick index (vibe-types)
- Discriminated unions & ADTs: closed tagged unions; exhaustive `switch`; invalid states unrepresentable → `T01-algebraic-data-types`
- Branded/opaque types: `string & { __brand: "UserId" }`; prevent value mix-ups at zero runtime cost → `T03-newtypes-opaque`
- Union & intersection types: `A | B`, `A & B`; alternatives without class hierarchies → `T02-union-intersection`
- Structural typing: shape conformance without inheritance; excess-property (freshness) checks on literals → `T07-structural-typing`
- Null safety: `strictNullChecks`, `T | null | undefined`, optional chaining; not null by default → `T13-null-safety`
- Narrowing & exhaustiveness: type guards, `in`, `instanceof`, discriminants; `never` for exhaustive checks → `T14-type-narrowing`, `T34-never-bottom`
- Conditional & mapped types: `T extends U ? X : Y`, `infer`, `{ [K in keyof T]: ... }`; type-level computation → `T41-match-types`, `T62-mapped-types`
- Template literal types: restrict string types to computed patterns; invalid strings are compile errors → `T63-template-literal-types`
- Generics & bounds: `<T extends U>`; generic code only compiles when constraints hold → `T04-generics-bounds`
- Immutability: `readonly`, `as const`, `Readonly<T>` (shallow, erased at runtime) → `T32-immutability-markers`
- Preventing invalid states: discriminated unions, branded types, phantom types → `UC01-invalid-states`
- Typestate & state machines: phantom brands track state; invalid transitions don't compile → `UC13-state-machines`

When this index is loaded, say "TypeScript quick index loaded 👋"
