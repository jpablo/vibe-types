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

### Pattern E — Discriminated union (tagged variant) serialization

Zod's `z.discriminatedUnion()` validates and narrows a union based on a literal discriminant field. This is the TypeScript equivalent of Rust's `#[serde(tag = "type")]` — the tag field drives which variant's schema is applied.

```typescript
import { z } from "zod";

// Each variant has a literal "kind" field — the discriminant
const ClickEventSchema = z.object({
  kind: z.literal("click"),
  x:    z.number(),
  y:    z.number(),
});

const KeyPressEventSchema = z.object({
  kind: z.literal("keypress"),
  key:  z.string(),
  ctrl: z.boolean().default(false),
});

const ScrollEventSchema = z.object({
  kind:  z.literal("scroll"),
  delta: z.number(),
});

// Discriminated union — Zod uses "kind" to pick the right schema:
const UIEventSchema = z.discriminatedUnion("kind", [
  ClickEventSchema,
  KeyPressEventSchema,
  ScrollEventSchema,
]);

type UIEvent = z.infer<typeof UIEventSchema>;
// { kind: "click"; x: number; y: number }
// | { kind: "keypress"; key: string; ctrl: boolean }
// | { kind: "scroll"; delta: number }

// Parse incoming events — the tag selects the branch:
const raw = JSON.parse('{"kind":"click","x":10,"y":20}');
const event = UIEventSchema.parse(raw);

// TypeScript narrows the discriminated union after a switch:
switch (event.kind) {
  case "click":    console.log(event.x, event.y); break;  // x, y available
  case "keypress": console.log(event.key);         break;  // key available
  case "scroll":   console.log(event.delta);       break;  // delta available
}

// Serialize back to JSON — the discriminant field is part of the type:
function toWireEvent(e: UIEvent): string {
  return JSON.stringify(e); // kind field is present; round-trips cleanly
}

// Unrecognized tag produces a ZodError — not silent undefined:
UIEventSchema.parse({ kind: "drag", dx: 5, dy: 5 });
// ZodError: Invalid discriminator value. Expected 'click' | 'keypress' | 'scroll'
```

### Pattern F — Field-level control: rename, defaults, omit null

Use Zod transforms and schema combinators to control how fields are named and shaped on the wire vs in the domain, and to omit null/undefined values before serializing.

```typescript
import { z } from "zod";

// Field renaming: wire uses snake_case, domain uses camelCase
const ApiUserSchema = z
  .object({
    user_name:    z.string(),        // wire field name
    display_name: z.string(),
    created_at:   z.coerce.date(),
    avatar_url:   z.string().url().nullable().optional(),
  })
  .transform((raw) => ({
    userName:    raw.user_name,      // camelCase in the domain
    displayName: raw.display_name,
    createdAt:   raw.created_at,
    avatarUrl:   raw.avatar_url ?? undefined,  // null → undefined
  }));

type ApiUser = z.infer<typeof ApiUserSchema>;
// { userName: string; displayName: string; createdAt: Date; avatarUrl?: string }

// Default values: missing fields get a fallback without extra code
const ConfigSchema = z.object({
  host:    z.string().default("localhost"),
  port:    z.number().int().default(8080),
  debug:   z.boolean().default(false),
  timeout: z.number().default(30_000),
});

type Config = z.infer<typeof ConfigSchema>;

const cfg = ConfigSchema.parse({});  // {} — all fields missing
// { host: "localhost", port: 8080, debug: false, timeout: 30000 }

// Partial update schema — every field optional for PATCH payloads
const PartialConfigSchema = ConfigSchema.partial();
type PartialConfig = z.infer<typeof PartialConfigSchema>;
// { host?: string; port?: number; debug?: boolean; timeout?: number }

// Strip unknown fields before persisting (avoids storing arbitrary client data)
const StrippedSchema = z.object({ id: z.string(), name: z.string() }).strip();
StrippedSchema.parse({ id: "1", name: "Alice", extra: "x" });
// { id: "1", name: "Alice" } — unknown keys silently removed
```

### Pattern G — Custom per-type serializer (transform and toJSON)

For domain types that cannot be expressed directly in JSON (e.g., `URL`, `Temporal.Instant`, custom value objects), use Zod's `.transform()` for parsing and override `toJSON()` on the class for serialization. This is the TypeScript analogue of Rust's custom `Serialize`/`Deserialize` impl.

```typescript
import { z } from "zod";

// Value object with a custom wire representation
class Money {
  constructor(
    readonly amount:   bigint,
    readonly currency: string,
  ) {}

  // Called automatically by JSON.stringify
  toJSON(): { amount: string; currency: string } {
    return { amount: this.amount.toString(), currency: this.currency };
  }

  static fromWire(raw: { amount: string; currency: string }): Money {
    return new Money(BigInt(raw.amount), raw.currency);
  }
}

// Zod schema for the wire format, transformed to the domain type:
const MoneySchema = z
  .object({
    amount:   z.string().regex(/^\d+$/),
    currency: z.string().length(3),
  })
  .transform((raw) => Money.fromWire(raw));

type MoneyInput = z.input<typeof MoneySchema>;   // { amount: string; currency: string }
type MoneyOutput = z.output<typeof MoneySchema>; // Money

// Parse from wire:
const price = MoneySchema.parse({ amount: "1099", currency: "USD" });
price instanceof Money; // true

// Serialize back — toJSON handles it:
JSON.stringify({ price }); // '{"price":{"amount":"1099","currency":"USD"}}'

// JSON.parse reviver pattern for in-place coercion (useful when Zod is not involved):
const reviver = (key: string, value: unknown): unknown => {
  if (typeof value === "object" && value !== null &&
      "amount" in value && "currency" in value) {
    return Money.fromWire(value as { amount: string; currency: string });
  }
  return value;
};

const recovered = JSON.parse(
  '{"price":{"amount":"1099","currency":"USD"}}',
  reviver,
) as { price: Money };

recovered.price instanceof Money; // true
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

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| **Zod** (Pattern A) | Ergonomic API; detailed field-level errors; `safeParse` avoids try/catch; tree-shakeable | Runtime overhead; not zero-cost; not format-agnostic |
| **io-ts** (Pattern B) | Bidirectional codecs; `Either`-typed errors compose with fp-ts pipelines | Verbose; steep learning curve; slower parse than Zod |
| **Mapped types** (Pattern C) | Library-free; compile-time only; tracks domain changes automatically | No runtime enforcement — must pair with a runtime validator |
| **Discriminated union** (Pattern E) | Exhaustive, compile-time exhaustiveness checking; tag-driven narrowing | Requires a literal discriminant field in every variant |
| **`toJSON` / reviver** (Pattern G) | Uses built-in JSON primitives; no library needed | No compile-time validation; easy to forget `toJSON` when adding fields |
| **TypeBox** | Generates JSON Schema alongside TS types; ideal for OpenAPI | Heavier setup; JSON Schema vocabulary limits expressiveness |
| **Binary (protobuf / msgpack)** | Compact wire size; strongly-typed schemas; schema evolution built-in | Requires proto compilation or codec library; not human-readable |

### A note on binary serialization

TypeScript projects that need compact wire formats or explicit schema evolution (adding fields without breaking old decoders) typically use:

- **`protobufjs`** or **`@bufbuild/protobuf`** — compile `.proto` files to typed TS classes; `encode`/`decode` produce `Uint8Array`
- **`msgpack-lite`** or **`@msgpack/msgpack`** — MessagePack over `Uint8Array`; TS types are manual or schema-derived
- **`flatbuffers`** — zero-copy reads from a `ByteBuffer`; generated TS builder/accessor classes

Unlike Lean's manual `ByteArray` encoding, these libraries handle field tagging, wire-type encoding, and backward compatibility. Use them when JSON payload size or parse latency is a bottleneck, or when you need cross-language schema contracts.

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

**Discriminated unions** (Pattern E) are the right model for any union where each variant has a literal tag field. Prefer `z.discriminatedUnion()` over `z.union()` — it is faster (O(1) tag lookup), produces clearer errors, and gives TypeScript the narrowing information it needs.

**Field-level control** (Pattern F) — use `.transform()` for renaming between wire and domain representations, `.default()` for missing fields, `.partial()` for PATCH payloads, and `.strip()` to drop unknown keys before persistence.

**Custom serializers** (Pattern G) — reach for `toJSON()` + a Zod `.transform()` schema when a domain class has a non-trivial wire representation (e.g., `Money`, `URL`, `Temporal.Instant`). Keep `toJSON` and the parse schema in the same file to prevent drift.

**Binary formats** — use `@bufbuild/protobuf` or `msgpack` when payload size or cross-language schema contracts matter. Protobuf's field tagging provides backward compatibility that hand-written JSON schemas do not.

## When to Use

### Use serialization safety when:

**You have untrusted input** — API requests, file uploads, environment config. The runtime validator acts as a security boundary.

```typescript
// Boundary: validate before trusting
const QuerySchema = z.object({
  limit:  z.number().int().min(1).max(100).default(10),
  filter: z.string().regex(/^[a-z0-9-]+$/).optional(),
});

function handleRequest(req: Request) {
  const query = QuerySchema.parse(req.query); // trust only after this line
  // ... use query safely
}
```

**You need round-trip preservation** — complex nested types with `Date`, `bigint`, or custom types.

```typescript
type Order = { createdAt: Date; amount: bigint };
type WireOrder = Serialized<Order>; // Date → string, bigint → string

function save(o: Order): void { db.save(JSON.stringify(toWire(o))); }
function load(): Order { return fromWire(JSON.parse(db.get())); }
```

**You want exhaustiveness checking** — discriminated unions with literal tags.

```typescript
// Switch is exhaustive — compiler warns if you miss a case
const e = EventSchema.parse(raw);
switch (e.kind) {
  case "created":   // e has createdAt
  case "deleted":   // e has deletedAt
}
```

**You need to prevent unvalidated values** — branded types ensure the parser is the only gate.

```typescript
type Email = Parsed<string>;

function validateEmail(s: string): Email {
  return z.string().email().parse(s) as Email;
}

function sendTo(email: Email) { /* ... */ }
sendTo("not-an-email"); // compile error
sendTo(validateEmail("user@example.com")); // OK
```

## When Not to Use

### Avoid serialization safety when:

**Input is already trusted** — internal data structures with no external input.

```typescript
// Redundant: no external input
type InternalState = { count: number; active: boolean };

// No need for schema — just use the type
function updateState(s: InternalState): InternalState {
  return { ...s, count: s.count + 1 };
}
```

**Performance-critical hot path** — every parse adds runtime overhead.

```typescript
// Bottleneck: parsing 100k times/sec
loop: for (let i = 0; i < 1_000_000; i++) {
  const x = NumberSchema.parse(raw[i]); // slow
}

// Better: parse once at boundary, use trusted values in loop
const numbers = raw.map(n => NumberSchema.parse(n));
for (let i = 0; i < numbers.length; i++) {
  const x = numbers[i]; // fast: no parse here
}
```

**Schema changes frequently** — heavy validation logic adds to maintenance burden.

```typescript
// Bad: schema changes weekly, validation logic bloats
const FormSchema = z.object({
  field1: z.string().min(3).max(50).regex(/foo/),
  field2: z.number().int().positive().finite(),
  // ... 100 more fields
});
```

**Simple primitives** — no need for validation.

```typescript
// Overkill for primitives
const id = z.string().uuid().parse(rawId); // just use: const id: string = rawId;
```

## Antipatterns

### Serialization antipatterns:

**Double validation** — parsing at boundary AND inside domain functions.

```typescript
// Wrong: parsing twice
const user = UserSchema.parse(req.body); // parse 1 (boundary)
const email = z.string().email().parse(user.email); // parse 2 (domain)

// Right: parse once at boundary
const user = UserSchema.parse(req.body);
sendEmail(user.email); // no re-parse here
```

**Ignoring parse errors** — `.parse()` with no error handling.

```typescript
// Wrong: crash on invalid input
const data = Schema.parse(req.body); // throws → 500

// Right: safeParse with proper error response
const result = Schema.safeParse(req.body);
if (!result.success) return respond(400, result.error);
```

**Mixing raw and parsed types** — treating unvalidated data as validated.

```typescript
// Wrong: raw data bypasses validation
function createOrder(raw) {
  return { id: raw.id, amount: raw.amount }; // no parse!
}

// Right: enforce validation first
function createOrder(raw) {
  const order = OrderSchema.parse(raw); // validation required
  return order;
}
```

**Schema in wrong layer** — validation in domain or persistence, not boundary.

```typescript
// Wrong: deep in domain logic
function calculateTax(order: Order) {
  const validated = OrderSchema.parse(order); // shouldn't be here
  return validated.amount * 0.1;
}

// Right: validate at API boundary only
const order = OrderSchema.parse(req.body);
calculateTax(order); // clean, no validation needed
```

**Overly strict schemas** — blocking valid data.

```typescript
// Wrong: rejects valid inputs
const PhoneSchema = z.string().regex(/^\+\d{3}-\d{3}-\d{4}$/); // too rigid

// Right: allow multiple formats
const PhoneSchema = z.string().regex(/^\+?\d[\d\s\-()]{6,}$/);
```

### Antipatterns replaced by serialization:

**Manual type guards** — error-prone runtime checks instead of schema validation.

```typescript
// Wrong: manual checks everywhere
function isUser(obj: unknown): obj is User {
  return obj !== null &&
         typeof obj === "object" &&
         "id" in obj && typeof obj.id === "string" &&
         "email" in obj && typeof obj.email === "string";
}
if (isUser(raw)) { /* ... */ }

// Right: schema handles all checks
const user = UserSchema.parse(raw); // single source of truth
```

**Partial validation** — checking some fields, missing others.

```typescript
// Wrong: partial validation
if (typeof raw.email === "string") {
  /* process */ // id, age not checked!
}

// Right: full schema validation
const user = UserSchema.parse(raw); // all fields validated
```

**JSON.stringify assumptions** — assuming types serialize correctly.

```typescript
// Wrong: Date becomes timestamp string (not ISO)
const order: Order = { createdAt: new Date() };
JSON.stringify(order); // "createdAt": 1234567890 (not what API expects)

// Right: mapped type + transform
type WireOrder = Serialized<Order>;
function toWire(o: Order): WireOrder {
  return { ...o, createdAt: o.createdAt.toISOString() };
}
```

**Forgetting to update parallel types** — drift between wire and domain types.

```typescript
// Wrong: two definitions that drift
type User = { id: string; email: string; age: number };
interface ApiUser { id: string; email: string } // missing age!

// Right: derive from single schema
type User = z.infer<typeof UserSchema>;
type WireUser = z.input<typeof UserSchema>; // both from schema
```

**No validation on JSON.parse** — trusting parsed JSON directly.

```typescript
// Wrong: JSON.parse + no validation
const data = JSON.parse(req.body);
database.save(data); // could save malicious data

// Right: parse + validate
const data = UserSchema.parse(JSON.parse(req.body));
database.save(data); // validated
```
