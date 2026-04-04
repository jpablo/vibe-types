# Serialization Safety

## The Constraint

Serialize and deserialize values with compile-time type safety. The runtime schema is the single source of truth — the TypeScript type and the runtime validator are derived from the same definition, so they cannot drift. Passing an unvalidated value where a parsed, typed value is required is a compile error.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Schema derivation** | Infer a TypeScript type from a runtime schema (Zod `z.infer<>`, io-ts `TypeOf<>`) — one definition drives both compile-time and runtime | [-> T06](../catalog/T06-derivation.md) |
| **Record types** | Schemas describe object shapes; record and object types express the serialized and domain representations | [-> T31](../catalog/T31-record-types.md) |
| **Recursive types** | Nested and self-referential schemas; `z.lazy()` in Zod / recursive `io-ts` codecs | [-> T61](../catalog/T61-recursive-types.md) |
| **Mapped types** | Transform between serialized (wire) and domain shapes — e.g., `Date` → `string` for JSON | [-> T62](../catalog/T62-mapped-types.md) |
| **Branded / opaque types** | Mark a value as "already parsed" — the parser is the only way to produce the branded type | [-> T03](../catalog/T03-newtypes-opaque.md) |

## Patterns

### Pattern A — Zod schema + `z.infer<>`

Define the schema once. Zod validates at runtime and `z.infer<>` derives the TypeScript type at compile time. The two cannot drift — if you add a field to the schema it automatically appears in the type, and vice-versa would be a compile error.

```typescript
import { z } from "zod";

// Single source of truth: schema drives both runtime validation and compile-time type
const UserSchema = z.object({
  id:        z.string().uuid(),
  email:     z.string().email(),
  role:      z.enum(["admin", "member", "viewer"]),
  createdAt: z.coerce.date(),           // string on the wire, Date in the domain
  profile: z.object({
    displayName: z.string().min(1).max(100),
    avatarUrl:   z.string().url().optional(),
  }),
});

// Type derived from schema — no manual duplication:
type User = z.infer<typeof UserSchema>;
// {
//   id: string;
//   email: string;
//   role: "admin" | "member" | "viewer";
//   createdAt: Date;
//   profile: { displayName: string; avatarUrl?: string | undefined };
// }

// Parse at the boundary (e.g., API response, request body):
function parseUser(raw: unknown): User {
  return UserSchema.parse(raw); // throws ZodError with field-level messages on failure
}

function safeParseUser(raw: unknown): { success: true; data: User } | { success: false; error: z.ZodError } {
  const result = UserSchema.safeParse(raw);
  return result; // never throws — caller handles the error branch
}

const raw = JSON.parse('{"id":"f47ac10b-58cc-4372-a567-0e02b2c3d479","email":"alice@example.com","role":"admin","createdAt":"2024-01-15T10:00:00Z","profile":{"displayName":"Alice"}}');

const user = parseUser(raw);
console.log(user.createdAt instanceof Date); // true — coerced from string
console.log(user.role);                      // "admin" — narrowed to the enum

// Passing raw unknown where User is required:
function greetUser(u: User): string { return `Hello, ${u.profile.displayName}`; }
greetUser(raw); // error: Argument of type '{}' is not assignable to parameter of type 'User'
greetUser(user); // OK
```

### Pattern B — io-ts codec with `Either<Errors, A>` error reporting

io-ts codecs encode both the runtime decoder and the TypeScript type. Decoding returns `Either<Errors, A>` — callers handle success and failure branches explicitly with no exceptions thrown.

```typescript
import * as t from "io-ts";
import { pipe } from "fp-ts/function";
import * as E from "fp-ts/Either";
import { PathReporter } from "io-ts/PathReporter";

// Codec = runtime decoder + TypeScript type in one definition
const UserCodec = t.type({
  id:    t.string,
  email: t.string,
  role:  t.union([t.literal("admin"), t.literal("member"), t.literal("viewer")]),
  age:   t.number,
});

// Derive the TypeScript type — identical to manual interface:
type User = t.TypeOf<typeof UserCodec>;

// Decode returns Either<Errors, User> — no throwing
const result = UserCodec.decode(JSON.parse('{"id":"1","email":"a@b.com","role":"admin","age":30}'));

pipe(
  result,
  E.fold(
    (errors) => {
      // PathReporter formats errors as human-readable strings:
      console.error(PathReporter.report(E.left(errors)).join("\n"));
    },
    (user: User) => {
      console.log(`Welcome, ${user.email}`); // type-safe — decoded and narrowed
    },
  ),
);

// Compose codecs for nested structures:
const AddressCodec = t.type({
  street: t.string,
  city:   t.string,
});

const OrderCodec = t.type({
  orderId: t.string,
  user:    UserCodec,    // nest — types compose
  address: AddressCodec,
  total:   t.number,
});

type Order = t.TypeOf<typeof OrderCodec>;
// { orderId: string; user: User; address: { street: string; city: string }; total: number }
```

### Pattern C — Mapped type for serialization transform

Use a mapped type to mechanically convert a domain type (with `Date`, `bigint`, etc.) to its wire/JSON-safe equivalent. The transformation is expressed once; adding a new field to the domain type automatically propagates to the serialized type.

```typescript
// Generic serialization transform: convert known non-JSON types to JSON-safe equivalents
type Serialized<T> = {
  [K in keyof T]: T[K] extends Date
    ? string
    : T[K] extends bigint
    ? string
    : T[K] extends (infer U)[]
    ? Serialized<U>[]
    : T[K] extends object
    ? Serialized<T[K]>
    : T[K];
};

type DomainEvent = {
  id:          string;
  occurredAt:  Date;
  amount:      bigint;
  metadata:    { source: string; version: number };
  tags:        string[];
};

// Derived automatically — no manual duplication:
type WireEvent = Serialized<DomainEvent>;
// {
//   id:         string;
//   occurredAt: string;   ← Date → string
//   amount:     string;   ← bigint → string
//   metadata:   { source: string; version: number };
//   tags:       string[];
// }

function toWire(event: DomainEvent): WireEvent {
  return {
    id:         event.id,
    occurredAt: event.occurredAt.toISOString(),
    amount:     event.amount.toString(),
    metadata:   event.metadata,
    tags:       event.tags,
  };
}

function fromWire(wire: WireEvent): DomainEvent {
  return {
    id:         wire.id,
    occurredAt: new Date(wire.occurredAt),
    amount:     BigInt(wire.amount),
    metadata:   wire.metadata,
    tags:       wire.tags,
  };
}

// Type mismatch caught at compile time:
const event: DomainEvent = {
  id: "e1",
  occurredAt: new Date(),
  amount: 999n,
  metadata: { source: "checkout", version: 2 },
  tags: ["urgent"],
};

const wire = toWire(event);
wire.occurredAt.toISOString(); // error: Property 'toISOString' does not exist on type 'string'
```

### Pattern D — Branded deserialized type

Use a branded (opaque) type to distinguish a validated, parsed value from a raw input. The parser function is the only way to produce the branded type — callers who require a parsed value cannot receive an unvalidated one.

```typescript
declare const __parsed: unique symbol;
type Parsed<T> = T & { readonly [__parsed]: unique symbol };

type RawUser = {
  id:    string;
  email: string;
  age:   number;
};

type ParsedUser = Parsed<RawUser>;

import { z } from "zod";

const RawUserSchema = z.object({
  id:    z.string().uuid(),
  email: z.string().email(),
  age:   z.number().int().min(0).max(150),
});

// Only this function produces ParsedUser — the cast is confined to one place:
function parseUserBranded(raw: unknown): ParsedUser {
  const validated = RawUserSchema.parse(raw); // throws on invalid input
  return validated as ParsedUser;             // safe: Zod guarantees the shape
}

// Domain functions require ParsedUser — raw objects are rejected at compile time:
function createAccount(user: ParsedUser): string {
  return `Account created for ${user.email}`;
}

const raw: RawUser = { id: "not-a-uuid", email: "bad", age: -1 };

createAccount(raw);                      // error: Argument of type 'RawUser' is not assignable to parameter of type 'ParsedUser'
createAccount(parseUserBranded(raw));    // throws ZodError at runtime — invalid data caught
createAccount(parseUserBranded(JSON.parse('{"id":"f47ac10b-58cc-4372-a567-0e02b2c3d479","email":"a@b.com","age":30}'))); // OK
```

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Parse API response | `const user = JSON.parse(body)` — any property access; silent `undefined` if shape changes | `UserSchema.parse(body)` returns a typed `User`; accessing missing fields is a compile error |
| Runtime + compile-time contract | Two separate definitions (JSDoc and runtime check) that can drift | Schema-derived types (`z.infer<>`, `t.TypeOf<>`) — single definition, impossible to drift |
| Error reporting | `try/catch (e)` — `e` is `any`; field-level info lost | Zod `ZodError` or io-ts `Either<Errors, A>` — structured, field-path error messages with types |
| Date serialization | Manual `new Date(raw.createdAt)` sprinkled everywhere; easy to forget | `z.coerce.date()` in schema or `Serialized<T>` mapped type — transformation is part of the type contract |
| Validated value vs raw string | Same type — caller may forget to validate | Branded `ParsedUser` vs `RawUser` — compiler rejects unvalidated values in domain functions |

## Recommended Libraries

| Library | Role | Link |
|---|---|---|
| **Zod** | Schema + type inference, tree-shakeable, best-in-class DX | https://zod.dev |
| **io-ts** | Bidirectional codecs with `Either`-based error composition | https://github.com/gcanti/io-ts |
| **arktype** | TypeScript-native runtime types with set-theoretic syntax | https://arktype.io |
| **TypeBox** | JSON Schema + TypeScript codegen, ideal for OpenAPI interop | https://github.com/sinclairzx81/typebox |

## When to Use Which Feature

**Zod** (Pattern A) is the right default for most projects. Its API is ergonomic, it is tree-shakeable, errors are detailed, and `safeParse` removes the need for try/catch. Use it for request body validation, API response parsing, and environment variable validation.

**io-ts** (Pattern B) fits codebases already using fp-ts. The `Either`-based decoding composes cleanly with `pipe` and `chain` across multiple validation steps, and the explicit error type in the `Left` channel integrates naturally with typed error channels (see UC08).

**Mapped types** (Pattern C) are the right tool when you need a reusable, library-free transformation between a domain type and a wire type. Prefer them over manual parallel type definitions — they automatically track domain changes.

**Branded deserialized types** (Pattern D) apply at security-sensitive or domain-critical boundaries where you need the compiler to enforce that every value has been validated before entering the domain layer. Combine with Zod or io-ts for the runtime half; the brand adds the compile-time half.

**TypeBox** is preferred when your project already consumes or produces JSON Schema (e.g., OpenAPI spec), since it generates both the schema and the TypeScript type from a single definition and the JSON Schema output can be shared with non-TypeScript consumers.
