# Schema Derivation & Decorators

> **Since:** TypeScript 5.0 (stage-3 decorators stable); Zod/io-ts always available

## 1. What It Is

TypeScript has no native `derive` keyword, but derivation is achievable through three complementary approaches. First, stage-3 decorators (stable in TypeScript 5.0) transform class definitions at runtime; frameworks like Angular, NestJS, and TypeORM use `reflect-metadata` to derive dependency-injection tokens, ORM column metadata, and validation rules from decorated class definitions. Second, schema libraries — Zod, io-ts, arktype, TypeBox — let you define a runtime schema once and infer the TypeScript type from it: the schema becomes the single source of truth for both runtime validation and compile-time types. Third, TypeScript's built-in mapped type utilities (`Partial<T>`, `Required<T>`, `Readonly<T>`, `Pick<T, K>`, `Omit<T, K>`) derive new object types from existing ones without any runtime overhead.

## 2. What Constraint It Lets You Express

**~Achievable — auto-generate validators, serializers, or DI metadata from a single definition; adding or changing a field propagates to all derived types automatically.**

- A Zod schema is both the validator and the type; they cannot drift from each other.
- Changing a property in the schema immediately produces a type error anywhere the old shape was assumed.
- Decorators generate ORM/DI metadata that mirrors the class structure without manual registration.
- Mapped type utilities (`Partial<T>`, etc.) derive structural variants without copy-pasting field lists.

## 3. Minimal Snippet

```typescript
import { z } from "zod";

// Schema is the single source of truth
const UserSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string().email(),
});

// Type derived from schema — cannot drift
type User = z.infer<typeof UserSchema>;
// { id: number; name: string; email: string }

// Runtime validation uses the same definition
function parseUser(raw: unknown): User {
  return UserSchema.parse(raw); // throws ZodError on failure
}

// OK — all fields present and valid
const u: User = parseUser({ id: 1, name: "Alice", email: "a@example.com" });

// error — missing 'email' is caught at runtime AND statically if you pass a literal
// parseUser({ id: 2, name: "Bob" });

// Built-in mapped type derivation (no library needed)
interface Config {
  host: string;
  port: number;
  debug: boolean;
}

type PartialConfig = Partial<Config>;
// { host?: string; port?: number; debug?: boolean }

function applyOverrides(base: Config, overrides: PartialConfig): Config {
  return { ...base, ...overrides }; // OK
}
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Decorators & DI** [-> T17](T17-macros-metaprogramming.md) | Decorators are the mechanism; `reflect-metadata` derives tokens and column info from class shape |
| **Record types** [-> T31](T31-record-types.md) | Schemas describe record shapes; `z.object()` and TypeScript interfaces share the same mental model |
| **Mapped types** [-> T62](T62-mapped-types.md) | `Partial<T>`, `Required<T>`, and custom mapped types are the built-in derivation mechanism |
| **Conditional types** [-> T41](T41-match-types.md) | Conditional types power the `z.infer<>` helper and similar schema-to-type extractors |

## 5. Recommended Libraries

| Library | Role | Link |
|---------|------|------|
| **Zod** | Schema validation + type inference | https://zod.dev |
| **io-ts** | Runtime codecs with Either error reporting | https://github.com/gcanti/io-ts |
| **arktype** | TypeScript-native runtime type validation | https://arktype.io |
| **TypeBox** | JSON Schema + TypeScript type generation | https://github.com/sinclairzx81/typebox |

## 6. Gotchas and Limitations

1. **No native `derive`** — unlike Rust's `#[derive(Serialize)]` or Haskell's `deriving`, TypeScript requires an explicit schema library or decorator setup; the compiler does not auto-generate instances.
2. **`reflect-metadata` is experimental** — decorator-based derivation depends on `emitDecoratorMetadata` and the `reflect-metadata` polyfill; this is not part of the ECMAScript standard.
3. **Schema and type can still drift if misused** — if you manually write `type User = { ... }` separately from the Zod schema, nothing enforces they stay in sync; the pattern only works if the type is always `z.infer<typeof Schema>`.
4. **Runtime cost** — schema parsing adds overhead; for hot paths consider caching parsed results or using compile-only tools like TypeBox's static type extraction.
5. **Decorator order matters** — multiple decorators on the same class member execute bottom-to-top; wrong ordering can produce subtle metadata bugs.

## 7. Use-Case Cross-References

- [-> UC-19](../usecases/UC19-generic-repository.md) Single schema drives repository types and runtime validation
- [-> UC-09](../usecases/UC09-api-boundary.md) API boundary: schema validates incoming payloads and infers response types
