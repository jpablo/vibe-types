# Schema Derivation & Decorators

> **Since:** TypeScript 5.0 (stage-3 decorators stable); Zod/io-ts always available

## 1. What It Is

TypeScript has no native `derive` keyword, but derivation is achievable through four complementary approaches:

1. **`typeof` / `z.infer<>` — type from value.** The most TypeScript-native form: declare a runtime constant (a schema object, a config object, or a `const` assertion) and let the compiler infer the type from it. The value is the single source of truth; the type is always structurally consistent with it.

2. **Schema libraries** — Zod, valibot, arktype, TypeBox — let you define a runtime schema once and extract the TypeScript type: `type User = z.infer<typeof UserSchema>`. Validation logic and static type cannot drift because they share one definition.

3. **Built-in mapped type utilities** (`Partial<T>`, `Required<T>`, `Readonly<T>`, `Pick<T, K>`, `Omit<T, K>`) derive new object types from existing ones at compile time with zero runtime overhead.

4. **Stage-3 decorators** (stable in TypeScript 5.0) transform class definitions at runtime. Frameworks like Angular, NestJS, and TypeORM use `reflect-metadata` to derive dependency-injection tokens, ORM column metadata, and validation rules from decorated class definitions.

## 2. What Constraint It Lets You Express

**~Achievable — auto-generate validators, serializers, or DI metadata from a single definition; adding or changing a field propagates to all derived types automatically.**

- A Zod schema is both the validator and the type; they cannot drift from each other.
- Changing a property in the schema immediately produces a type error anywhere the old shape was assumed.
- `typeof value` derives a precise type from a runtime constant — useful for config objects, lookup tables, and discriminated union tag sets.
- Decorators generate ORM/DI metadata that mirrors the class structure without manual registration.
- Mapped type utilities (`Partial<T>`, etc.) derive structural variants without copy-pasting field lists.

**Field constraint analog.** Like Rust's `#[derive(Clone)]` failing if a field is not `Clone`, schema derivation has an equivalent: if a field's type cannot be represented in the schema (e.g., a function in Zod), the schema definition fails at the point of the field, not silently at parse time. You must either exclude the field or handle it explicitly.

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

## 4. Beginner Mental Model

Think of schema derivation as a **single mold that stamps out both the validator and the type**. In Rust you write `#[derive(Serialize, PartialEq)]` and the compiler generates implementations from the struct's shape. TypeScript does not have a compiler-level derive keyword, but schema libraries achieve the same outcome from the other direction: you write the schema (which the compiler cannot see through) and then ask the type system to *infer* what shape it produces — `z.infer<typeof Schema>`.

The `typeof` keyword is the other half: for runtime constants (config objects, lookup tables) TypeScript can derive the precise type from the value, which keeps the type structurally in sync automatically.

Coming from Rust: `z.infer<typeof Schema>` ≈ combining `#[derive(Deserialize)]` with the struct definition in one object. Coming from Python: the combination of a Zod schema + `z.infer<>` is the TypeScript equivalent of a Pydantic `BaseModel`.

## 5. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Decorators & DI** [-> T17](T17-macros-metaprogramming.md) | Decorators are the mechanism; `reflect-metadata` derives tokens and column info from class shape |
| **Record types** [-> T31](T31-record-types.md) | Schemas describe record shapes; `z.object()` and TypeScript interfaces share the same mental model |
| **Mapped types** [-> T62](T62-mapped-types.md) | `Partial<T>`, `Required<T>`, and custom mapped types are the built-in derivation mechanism |
| **Conditional types** [-> T41](T41-match-types.md) | Conditional types power the `z.infer<>` helper and similar schema-to-type extractors |
| **Algebraic data types** [-> T01](T01-algebraic-data-types.md) | Schema libraries derive discriminated union types; `z.discriminatedUnion()` maps directly to tagged ADTs |
| **Generics** [-> T04](T04-generics-bounds.md) | Schemas and mapped types are generic; `z.array(z.infer<T>)` and `Partial<T>` compose across any shape |
| **Structural typing** [-> T07](T07-structural-typing.md) | A derived type satisfies any structurally compatible interface — no explicit declaration needed |

## 6. Patterns

### `typeof` derivation — type from runtime value

The `typeof` operator is TypeScript's most direct derivation form. Use it to extract a precise type from a `const` value, eliminating the need to write the type separately.

```typescript
// Derive an event-name union from a runtime map
const EVENTS = {
  USER_CREATED: "user.created",
  USER_DELETED: "user.deleted",
  ORDER_PLACED:  "order.placed",
} as const;

type EventName = typeof EVENTS[keyof typeof EVENTS];
// "user.created" | "user.deleted" | "order.placed"

// Derive a config shape from a defaults object
const defaults = { host: "localhost", port: 5432, ssl: false } as const;
type DbConfig = typeof defaults;
// { readonly host: "localhost"; readonly port: 5432; readonly ssl: false }

// Widen to mutable with a mapped type
type MutableDbConfig = { -readonly [K in keyof DbConfig]: DbConfig[K] };
```

### Template literal types — derive string union shapes

```typescript
type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";
type ApiEndpoint = "/users" | "/orders" | "/products";

// Derive all valid route strings from two unions
type Route = `${HttpMethod} ${ApiEndpoint}`;
// "GET /users" | "GET /orders" | "GET /products" | "POST /users" | …

// Derive getter method names from field names
interface User { id: number; name: string; email: string; }
type Getter = `get${Capitalize<keyof User & string>}`;
// "getId" | "getName" | "getEmail"
```

### Recursive schemas

Schema libraries handle recursive types, but require an explicit type annotation to break the inference cycle:

```typescript
import { z } from "zod";

// Must annotate the type separately — inference cannot resolve the cycle
type Category = {
  name: string;
  subcategories: Category[];
};

const CategorySchema: z.ZodType<Category> = z.lazy(() =>
  z.object({
    name: z.string(),
    subcategories: z.array(CategorySchema),
  })
);

type Category = z.infer<typeof CategorySchema>;
```

### Class decorators — metadata-driven derivation

```typescript
import "reflect-metadata";

function Column(options?: { nullable?: boolean }) {
  return (target: object, key: string) => {
    const type = Reflect.getMetadata("design:type", target, key);
    // Register column metadata keyed by class + field
    Reflect.defineMetadata("column", { type, ...options }, target, key);
  };
}

class UserEntity {
  @Column()
  name!: string;

  @Column({ nullable: true })
  bio!: string | null;
}
```

## 7. Recommended Libraries

| Library | Role | Link |
|---------|------|------|
| **Zod** | Schema validation + type inference | https://zod.dev |
| **valibot** | Modular schema library with smaller bundle size | https://valibot.dev |
| **arktype** | TypeScript-native runtime type validation | https://arktype.io |
| **TypeBox** | JSON Schema + TypeScript type generation | https://github.com/sinclairzx81/typebox |
| **io-ts** | Runtime codecs with Either error reporting | https://github.com/gcanti/io-ts |
| **class-validator** | Decorator-based validation for class instances | https://github.com/typestack/class-validator |
| **class-transformer** | Serialize/deserialize class instances via decorators | https://github.com/typestack/class-transformer |

## 8. When to Use It

- **Runtime validation is required** — API boundaries, file parsing, user input: the schema both validates and defines the type.
- **You want a single source of truth** — field changes propagate automatically to types and validators.
- **Config objects or lookup tables** — derive types from constants with `typeof` to prevent drift.
- **Domain models with shared shapes** — e.g., `Customer` used in DB, API, and validation layers.
- **Generating structural variants** — use `Partial<T>`, `Pick<T, K>`, `Omit<T, K>` instead of duplicating fields.

**Do not** use schema derivation when:
- Working with purely compile-time constraints (no runtime validation needed) — plain interfaces suffice.
- The data structure is transient or used only within a single function scope.
- Performance is critical on hot paths and schema parsing overhead is unacceptable.
- Dealing with unserializable types (functions, class instances, complex circular structures) without clear handling strategy.

---

## 9. Antipatterns

### ❌ Duplicate type definition

```typescript
// BAD — type and schema can drift
interface User {
  id: number;
  name: string;
}

const UserSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string().email(), // added later but interface not updated!
});
```

**Fix:** Always derive types from schemas:
```typescript
const UserSchema = z.object({ id: z.number(), name: z.string(), email: z.string().email() });
type User = z.infer<typeof UserSchema>;
```

### ❌ Ignoring inference in favor of manual types

```typescript
// BAD — defeats the purpose
const ConfigSchema = z.object({ port: z.number(), host: z.string() });
type Config = { port: number; host: string; debug?: boolean }; // drift possible
```

**Fix:** Use inference:
```typescript
type Config = z.infer<typeof ConfigSchema>;
```

### ❌ Over-using derivation for trivial types

```typescript
// BAD — unnecessary complexity
const CounterSchema = z.object({ value: z.number() });
type Counter = z.infer<typeof CounterSchema>;

function increment(c: Counter) { return { ...c, value: c.value + 1 }; }
```

**Fix:** Use plain interfaces for internal-only types:
```typescript
interface Counter { value: number; }
function increment(c: Counter) { return { ...c, value: c.value + 1 }; }
```

### ❌ Deriving from mutable runtime objects

```typescript
// BAD — type widens unexpectedly
const FLAGS = { enabled: true } as const;
type FlagName = keyof typeof FLAGS; // "enabled"

FLAGS.enabled = false; // compiles
// but type is still { readonly enabled: true }
```

**Fix:** Keep source constants immutable or re-declare type after mutations.

---

## 10. Patterns Where Derivation Is Better

### ❌ Mapped type + manual field list

```typescript
interface User { id: number; name: string; email: string; age: number; }

// BAD — must keep field list in sync
type UserDisplay = Pick<User, "name" | "email">;
type UserDb = Omit<User, "age">;

interface UserDisplayV2 { name: string; email: string; phone?: string; }
// forgot to update UserDisplay after adding phone!
```

**Fix with schema derivation:**
```typescript
const UserSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string().email(),
  age: z.number(),
  phone: z.string().optional(),
});

type User = z.infer<typeof UserSchema>;
type UserDisplay = z.infer<typeof UserSchema> extends infer U 
  ? Pick<U, "name" | "email" | "phone"> 
  : never;
```

### ❌ Separate request/response types

```typescript
// BAD — API types diverge from validation
interface CreateUserRequest { name: string; email: string; }
interface CreateUserResponse { id: string; name: string; email: string; createdAt: Date; }

function validateCreate(req: unknown): CreateUserRequest {
  // manual validation with different shape!
  return req as any;
}
```

**Fix with schema derivation:**
```typescript
const CreateUserRequestSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
});

const CreateUserResponseSchema = CreateUserRequestSchema.extend({
  id: z.string().uuid(),
  createdAt: z.date(),
});

type CreateUserRequest = z.infer<typeof CreateUserRequestSchema>;
type CreateUserResponse = z.infer<typeof CreateUserResponseSchema>;
```

### ❌ Config with manual defaults

```typescript
// BAD — defaults not enforced at type level
interface AppConfig {
  port: number;
  host: string;
  timeout: number;
}

const DEFAULT_CONFIG: AppConfig = { port: 3000, host: "localhost", timeout: 5000 };

function loadConfig(env: Record<string, string>): AppConfig {
  return {
    port: parseInt(env.PORT) || DEFAULT_CONFIG.port,
    host: env.HOST || DEFAULT_CONFIG.host,
    timeout: parseInt(env.TIMEOUT), // can be NaN!
  };
}
```

**Fix with schema derivation:**
```typescript
const ConfigSchema = z.object({
  port: z.coerce.number().int().positive(),
  host: z.string().min(1),
  timeout: z.coerce.number().int().positive(),
}).default({ port: 3000, host: "localhost", timeout: 5000 });

type Config = z.infer<typeof ConfigSchema>;

function loadConfig(env: Record<string, string>): Config {
  return ConfigSchema.parse(env); // validates + applies defaults
}
```

---

## 8. Gotchas and Limitations

1. **No native `derive`** — unlike Rust's `#[derive(Serialize)]` or Haskell's `deriving`, TypeScript requires an explicit schema library or decorator setup; the compiler does not auto-generate instances.

2. **Field constraint analog: schemas cannot represent every TypeScript type.** Zod and similar libraries cannot automatically schema-ify function types, class instances, or circular references without explicit handling. A field of type `() => void` or `Map<K, V>` must be modeled with `z.function()` or `z.instanceof(Map)` — or excluded. This is the TypeScript equivalent of Rust's "all fields must implement the trait" rule.

3. **`reflect-metadata` is experimental** — decorator-based derivation depends on `emitDecoratorMetadata` and the `reflect-metadata` polyfill; this is not part of the ECMAScript standard. Stage-3 decorators in TypeScript 5.0 use a new design that does *not* emit type metadata by default; combining the two systems requires care.

4. **Schema and type can still drift if misused** — if you manually write `type User = { ... }` separately from the Zod schema, nothing enforces they stay in sync; the pattern only works if the type is always `z.infer<typeof Schema>`.

5. **Recursive types require explicit annotations.** Zod's `z.lazy()` breaks the inference cycle but forces you to provide a separate `type` or `interface` declaration with the recursive shape. If the type annotation drifts from the schema, the compiler cannot catch it — you must keep them aligned manually.

6. **Runtime cost** — schema parsing adds overhead; for hot paths consider caching parsed results or using compile-only tools like TypeBox's static type extraction.

7. **Decorator order matters** — multiple decorators on the same class member execute bottom-to-top; wrong ordering can produce subtle metadata bugs.

8. **No partial derivation.** Mapped types like `Partial<T>` apply to all fields. To exclude specific fields, use `Omit<T, "field">` before applying the mapped type, or write a custom mapped type with a conditional key filter.

## 9. Example A — Schema-first domain model

```typescript
import { z } from "zod";

const AddressSchema = z.object({
  street: z.string().min(1),
  city: z.string().min(1),
  zip: z.string().regex(/^\d{5}$/),
});

const CustomerSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  email: z.string().email(),
  address: AddressSchema,
  createdAt: z.coerce.date(),
});

// All types derived — adding a field to the schema automatically
// updates the TypeScript type everywhere it is used
type Customer = z.infer<typeof CustomerSchema>;
type Address = z.infer<typeof AddressSchema>;

function validateIncoming(raw: unknown): Customer {
  return CustomerSchema.parse(raw);
}

// Derive a partial "patch" type for PATCH endpoints
const CustomerPatchSchema = CustomerSchema.partial().omit({ id: true, createdAt: true });
type CustomerPatch = z.infer<typeof CustomerPatchSchema>;
// { name?: string; email?: string; address?: Address }
```

## 10. Example B — When field types cannot be derived

```typescript
import { z } from "zod";

// This compiles but cannot be usefully validated at the field level
const HandlerSchema = z.object({
  name: z.string(),
  // Functions have no schema representation — must use z.function() explicitly
  handler: z.function().args(z.string()).returns(z.promise(z.void())),
});

// Alternative: exclude the non-serializable field from the schema
// and handle it separately
const SerializableHandlerSchema = z.object({
  name: z.string(),
  timeout: z.number().int().positive(),
});

type SerializableHandler = z.infer<typeof SerializableHandlerSchema>;

// Extend with the runtime-only field after validation
type Handler = SerializableHandler & {
  fn: (input: string) => Promise<void>;
};
```

## 11. Common Type-Checker Errors

### `Type 'X' is not assignable to type 'z.infer<typeof Schema>'`

The inferred schema type does not match the value you are assigning. Usually caused by a field type mismatch or a missing field.

```
error TS2322: Type '{ id: string; name: string }' is not assignable to type 'Customer'.
  Property 'email' is missing in type '{ id: string; name: string }'.
```

**Fix:** Add the missing field, or make it optional in the schema with `.optional()`.

### `Type 'string' is not assignable to type 'never'` in discriminated unions

Occurs when `z.discriminatedUnion()` or a hand-written tagged union has exhausted all branches.

**Fix:** Check that the discriminant value matches one of the declared variants, or add the missing case.

### `Property 'X' does not exist on type 'Partial<T>'`

`Partial<T>` makes all fields optional — accessing them without a guard produces `T[K] | undefined`, not `T[K]`.

**Fix:** Use a nullish coalescing guard: `config.host ?? "localhost"`, or narrow with an `if` check.

### `z.lazy()` requires an explicit type annotation

When a schema is self-referential, TypeScript cannot infer the return type of `z.lazy()`.

```
error TS7022: 'CategorySchema' implicitly has type 'any' because it does not have a type annotation and is referenced directly or indirectly in its own initializer.
```

**Fix:** Provide `const CategorySchema: z.ZodType<Category> = z.lazy(() => ...)` and declare `type Category` separately.

## 12. Use-Case Cross-References

- [-> UC-02](../usecases/UC02-domain-modeling.md) Single schema drives repository types and runtime validation
- [-> UC-09](../usecases/UC09-builder-config.md) API boundary: schema validates incoming payloads and infers response types

## Source Anchors

- [TypeScript Handbook — `typeof` type operator](https://www.typescriptlang.org/docs/handbook/2/typeof-types.html)
- [TypeScript Handbook — Mapped Types](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)
- [TypeScript Handbook — Template Literal Types](https://www.typescriptlang.org/docs/handbook/2/template-literal-types.html)
- [TypeScript 5.0 release notes — Stage 3 Decorators](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html)
- [Zod documentation — `z.infer`](https://zod.dev/?id=type-inference)
- [TC39 Decorators proposal](https://github.com/tc39/proposal-decorators)
