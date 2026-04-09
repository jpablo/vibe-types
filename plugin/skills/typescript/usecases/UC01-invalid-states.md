# Make Illegal States Unrepresentable

## The Constraint

If a value exists at runtime, the type system guarantees it is valid. Invalid combinations of fields, out-of-range numbers, and impossible state transitions are rejected at compile time — not discovered at runtime through guards or asserts.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Discriminated unions** | One variant per valid state; impossible cross-variant field access caught at compile time | [-> T01](../catalog/T01-algebraic-data-types.md) |
| **Branded types** | Wrap a primitive so that raw, unvalidated values are not assignable to the branded type | [-> T03](../catalog/T03-newtypes-opaque.md) |
| **Phantom types** | Carry state information in a type parameter that has no runtime representation | [-> T27](../catalog/T27-erased-phantom.md) |
| **Type narrowing** | Refine a union to a specific variant inside a branch | [-> T14](../catalog/T14-type-narrowing.md) |
| **never / exhaustiveness** | Make unhandled variants a compile-time error | [-> T34](../catalog/T34-never-bottom.md) |

## Patterns

### Pattern A — Discriminated union for payment status

Each payment state carries only the fields that are meaningful for that state. There is no `refundAmount?: number` field sitting on a `Pending` record where it makes no sense.

```typescript
type PaymentStatus =
  | { kind: "Pending" }
  | { kind: "Charged"; transactionId: string; amount: number }
  | { kind: "Refunded"; transactionId: string; refundedAt: Date }
  | { kind: "Failed"; reason: string };

function describe(status: PaymentStatus): string {
  switch (status.kind) {
    case "Pending":   return "Awaiting payment";
    case "Charged":   return `Charged ${status.amount} (tx: ${status.transactionId})`;
    case "Refunded":  return `Refunded on ${status.refundedAt.toISOString()}`;
    case "Failed":    return `Failed: ${status.reason}`;
    default: {
      // If a new variant is added and this switch is not updated,
      // the compiler reports an error here.
      const _exhaustive: never = status; // error on unhandled variant
      return _exhaustive;
    }
  }
}

// Impossible cross-variant access is caught at compile time:
declare const s: PaymentStatus;
s.transactionId; // error: property does not exist on type 'PaymentStatus'
```

### Pattern B — Branded type for port number

A `number` and a `Port` are structurally different to the type checker after branding. A raw, unvalidated `number` cannot flow into a function expecting `Port`.

```typescript
declare const __brand: unique symbol;
type Brand<B> = { readonly [__brand]: B };
type Branded<T, B> = T & Brand<B>;

type Port = Branded<number, "Port">;

function makePort(n: number): Port {
  if (n < 1 || n > 65535) {
    throw new RangeError(`Invalid port: ${n}`);
  }
  return n as Port;
}

function connect(host: string, port: Port): void {
  console.log(`Connecting to ${host}:${port}`);
}

const p = makePort(8080);         // OK — validated, returns Port
connect("localhost", p);          // OK
connect("localhost", 8080);       // error: Argument of type 'number' is not assignable to parameter of type 'Port'
connect("localhost", -1 as Port); // still compiles — caller asserts validity
```

### Pattern C — Phantom type for door state machine

The door's open/closed/locked state lives only in the type; the runtime value is a plain object. Invalid transitions (locking an already-locked door, unlocking without closing) become compile errors.

```typescript
declare const __state: unique symbol;
type DoorState = { readonly [__state]: never };

type Open   = DoorState & { readonly __open: never };
type Closed = DoorState & { readonly __closed: never };
type Locked = DoorState & { readonly __locked: never };

type Door<S extends DoorState> = { readonly _phantom: S };

declare function openDoor(door: Door<Closed>): Door<Open>;
declare function closeDoor(door: Door<Open>): Door<Closed>;
declare function lockDoor(door: Door<Closed>): Door<Locked>;
declare function unlockDoor(door: Door<Locked>): Door<Closed>;

declare const closed: Door<Closed>;
const opened  = openDoor(closed);   // OK
const relocked = lockDoor(opened);  // error: Door<Open> is not assignable to Door<Closed>
const locked  = lockDoor(closeDoor(opened)); // OK — must close before locking
openDoor(locked); // error: Door<Locked> is not assignable to Door<Closed>
```

### Pattern D — Literal union for closed value sets

When states carry no associated data, a union of string literals is simpler than a discriminated union and provides the same exhaustiveness guarantees with less boilerplate.

```typescript
type Direction = "north" | "south" | "east" | "west";

function move(direction: Direction, steps: number): void {
  console.log(`Moving ${steps} steps ${direction}`);
}

move("north", 5);  // OK
move("up", 5);     // error: Argument of type '"up"' is not assignable to parameter of type 'Direction'

// `as const` objects act as lightweight enums that preserve literal types:
const HTTP_METHODS = {
  GET:    "GET",
  POST:   "POST",
  PUT:    "PUT",
  DELETE: "DELETE",
} as const;

type HttpMethod = (typeof HTTP_METHODS)[keyof typeof HTTP_METHODS];
// inferred as: "GET" | "POST" | "PUT" | "DELETE"

function request(url: string, method: HttpMethod): void { /* ... */ }

request("/api/users", HTTP_METHODS.GET);  // OK
request("/api/users", "PATCH");           // error: Argument of type '"PATCH"' is not assignable
```

TypeScript also has a native `enum` keyword. Prefer `as const` + union in most modern codebases:

```typescript
// Native enum — emits a runtime object with bidirectional name/value mapping
enum Direction {
  North = "north",
  South = "south",
  East  = "east",
  West  = "west",
}

move(Direction.North, 5);  // OK
// Iterable at runtime: Object.values(Direction)

// const enum — erased entirely at compile time; members become inlined literals
const enum LogLevel { Debug = 0, Info = 1, Warn = 2, Error = 3 }
// No runtime object; cannot use Object.values(LogLevel)
```

Prefer `as const` when: the values must be plain strings/numbers in JSON, the enum is used across module boundaries, or you want full tree-shaking. Prefer native `enum` when you need runtime iteration (`Object.values`) or named members by convention. Avoid numeric `enum` without explicit values — implicit ordinals break when members are reordered.

Prefer a discriminated union (Pattern A) when variants carry different data. Use a literal union when the state itself is all the information.

### Pattern E — Parse, don't validate

A parser is a function that converts less-structured input into more-structured output. Functions that *validate* check a condition and return void or throw — the caller gains no type-level guarantee. Functions that *parse* check a condition and return a refined type — the caller holds typed evidence that the value is valid.

```typescript
type Email = Branded<string, "Email">;

// Validation: checks and throws — caller gains no type-level info
function validateEmail(raw: string): void {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(raw.trim())) {
    throw new Error(`Invalid email: ${raw}`);
  }
  // raw is still `string` after this call; nothing flows into the type system
}

// Parsing: checks and returns a refined type (or null on failure)
function parseEmail(raw: string): Email | null {
  const trimmed = raw.trim().toLowerCase();
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)
    ? (trimmed as Email)
    : null;
}

function sendWelcome(to: Email): void {
  console.log(`Sending welcome to ${to}`);
}

const email = parseEmail("alice@example.com");
if (email !== null) {
  sendWelcome(email);  // OK — TypeScript narrows to Email here
}
sendWelcome("alice@example.com");  // error: string is not assignable to Email
```

TypeScript's structural type system enables another form of parsing: encoding structural invariants in tuple types. A non-empty array is representable without a wrapper class:

```typescript
// Structural refinement: tuple rest type encodes "at least one element"
type NonEmptyArray<T> = [T, ...T[]];

function parseNonEmpty<T>(xs: T[]): NonEmptyArray<T> | null {
  return xs.length > 0 ? (xs as NonEmptyArray<T>) : null;
}

// first() is total — the compiler knows xs[0] always exists
function first<T>(xs: NonEmptyArray<T>): T {
  return xs[0];
}

const items = parseNonEmpty([1, 2, 3]);
if (items !== null) {
  console.log(first(items));  // OK
}

first([]);  // error: Argument of type 'never[]' is not assignable to '[T, ...T[]]'
```

Unlike a branded primitive, a `NonEmptyArray<T>` is a real `T[]` at runtime — no wrapper class, no `.value` accessor, no boxing. The invariant lives entirely in the type.

**Key insight:** `validateEmail` discards the information — the caller still holds a `string` and must remember to call the validator again later. `parseEmail` preserves the information — the returned `Email | null` forces the caller to handle the failure case exactly once, and downstream code never needs to re-validate. Prefer parsing.

See: [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Payment state | Single object with all optional fields; guarded with `if (payment.transactionId)` at every call site | Discriminated union — impossible fields absent from each variant; narrowing replaces guards |
| Port validation | `function connect(host, port) { if (port < 1 \|\| port > 65535) throw … }` — repeated at every call site | Branded `Port`; validation once in `makePort`, enforced by types everywhere else |
| State machines | Documented conventions (`door.state === 'locked'`); wrong transitions discovered at runtime | Phantom type parameter; invalid transitions are type errors before the code runs |
| Email handling | `validate(email)` returns boolean; caller may forget to call it or may pass the raw string anyway | `parseEmail` returns `Email` branded type; unvalidated strings are not assignable |

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **Discriminated union** | Each variant holds only its own fields; exhaustive matching enforced; no impossible field access | Requires a `kind`/`tag` discriminant field; more boilerplate than a literal union for data-free states |
| **Branded type** | Zero runtime overhead; validation once at boundary; works for any primitive | TypeScript-level only — `as Brand` casts can bypass it; no runtime enforcement |
| **Phantom type** | Encodes state machines and protocols; erased at runtime (zero overhead) | Setup is verbose; type errors can be hard to read; no runtime safety if `as` casts are used |
| **Literal union** | Simplest closed set; no extra class or discriminant needed | No associated data per variant; no built-in runtime iteration (unlike a real enum) |
| **Native `enum`** | Runtime-iterable object; named members by convention; familiar to Java/C# devs | Emits runtime code; bidirectional mapping surprises; numeric enums unsound without explicit values |
| **`NonEmptyArray<T>` tuple** | Structural invariant with zero runtime cost; no wrapper class | Requires a cast at the parse boundary; only expresses length-based constraints |
| **Parse, don't validate** | Invalid values cannot flow downstream; callers never re-validate | Callers must handle `null` / error path; requires discipline at every system boundary |

## When to Use Which Feature

**Discriminated union** (Pattern A) is the default tool when a value can be in one of several mutually exclusive states and each state carries different data. The compiler prevents accessing fields from the wrong variant.

**Branded type** (Pattern B) is best for primitive values with domain-level restrictions (port ranges, positive integers, validated strings). Validate once at the boundary; everything downstream trusts the type.

**Phantom type** (Pattern C) is the right choice when you need to enforce a sequential protocol or state machine — connection lifecycles, builder stages, access-controlled resources — without duplicating data structures per state. The phantom parameter is erased at runtime.

**Literal union** (Pattern D) is the simplest tool when states carry no associated data and the set of values is small and stable. Reach for a discriminated union only when variants need their own fields. Use a native `enum` only when you need to iterate over members at runtime (`Object.values`) or when the codebase convention demands named enum members; otherwise the `as const` + union pattern is idiomatic and avoids the pitfalls of TypeScript's enum emission.

**Parse, don't validate** (Pattern E) applies at every system boundary — HTTP request bodies, configuration files, user input. Return a refined type so that callers hold typed evidence of validity rather than a boolean promise.

## When to Use This Technique

Use this technique when your domain has invariants that should be enforced by the type system rather than runtime checks:

```typescript
// ✅ Use when: state transitions must be valid
type Order = "pending" | "paid" | "shipped" | "cancelled";

function transitionTo(order: Order, newStatus: Order): void {
  if (order === "cancelled" && newStatus !== "cancelled") {
    throw new Error("Cannot transition from cancelled");
  }
}
```

Use when data depends on state:

```typescript
// ✅ Use when: some fields only exist in certain states
type FormState = 
  | { status: "idle"; data?: FormData }
  | { status: "loading"; data: FormData }
  | { status: "success"; data: FormData; result: Result }
  | { status: "error"; data: FormData; error: string };
```

Use at system boundaries where untrusted input enters:

```typescript
// ✅ Use when: external data must be validated
function parseUserId(raw: string): User | null {
  const id = raw.trim();
  return id.length >= 3 ? (id as User) : null;
}
```

## When NOT to Use This Technique

Do NOT use when the cost of type complexity exceeds the benefit:

```typescript
// ❌ Don't use for: trivial or transient values
function addTax(amount: number, rate: number): number {
  return amount * (1 + rate);
}
// Tax rate validation can be a simple runtime check
```

Do NOT use when runtime flexibility is required:

```typescript
// ❌ Don't use for: dynamically typed configs
interface Config {
  [key: string]: unknown; // Runtime flexibility needed
}
// Phantom types or branded types add no value here
```

Do NOT use when performance is critical and type checks add overhead:

```typescript
// ❌ Don't use in: tight numerical loops
function process(buffer: Float32Array): void {
  for (let i = 0; i < buffer.length; i++) {
    buffer[i] = Math.sin(buffer[i]);
  }
}
// Branded types would require boxing/unboxing
```

## Antipatterns When Using This Technique

### Antipattern 1 — Over-nesting unions

```typescript
// ❌ Anti: deeply nested unions become unreadable
type Response = 
  | { kind: "ok"; data: { kind: "list" | "item"; items?: Item[] } | null }
  | { kind: "error"; code: number; msg: string | undefined };

// ✅ Better: flatten with meaningful state names
type Response =
  | { kind: "ok-list"; items: Item[] }
  | { kind: "ok-item"; item: Item }
  | { kind: "empty" }
  | { kind: "error"; code: number; msg: string };
```

### Antipattern 2 — Bypassing with `any`

```typescript
// ❌ Anti: defeats the entire purpose
function parseEmail(raw: string): Email | null {
  return (raw as any) as Email; // no validation!
}

// ✅ Better: validate or return null
function parseEmail(raw: string): Email | null {
  return isValid(raw) ? (raw as Email) : null;
}
```

### Antipattern 3 — Overusing phantom types

```typescript
// ❌ Anti: phantom types for simple state
type Door<State extends "open" | "closed"> = { _state: State };
function open(d: Door<"closed">): Door<"open"> { /* ... */ }
// Works, but a literal type is simpler:

// ✅ Better: use literal union when possible
type DoorState = "open" | "closed";
```

### Antipattern 4 — Using optional fields instead of state

```typescript
// ❌ Anti: optional fields create invalid states
interface User {
  id: string;
  name?: string;
  email?: string;
}
// Invalid: { id: "1" } is a valid User

// ✅ Better: use discriminated union
type User = 
  | { kind: "anonymized"; id: string }
  | { kind: "full"; id: string; name: string; email: string };
```

### Antipattern 5 — Validating downstream instead of at boundary

```typescript
// ❌ Anti: validation scattered across call sites
function sendEmail(raw: string): void {
  if (!isValidEmail(raw)) throw new Error();
  // ...
}

// ✅ Better: parse at boundary, types enforce validity
function sendEmail(email: Email): void {
  // email is guaranteed valid — no check needed
}
```

## Antipatterns Other Techniques Create (That This Fixes)

### Runtime guards repeated everywhere

```typescript
// ❌ Anti: checking port validity at every call site
function connect(host: string, port: number) {
  if (port < 1 || port > 65535) throw new Error();
  // ...
}
function bind(host: string, port: number) {
  if (port < 1 || port > 65535) throw new Error(); // duplicate!
  // ...
}

// ✅ Fix: branded type validates once
function connect(host: string, port: Port) { /* always valid */ }
function bind(host: string, port: Port) { /* always valid */ }
```

### Boolean returns lose information

```typescript
// ❌ Anti: boolean validators don't refine types
function isValidEmail(s: string): boolean { 
  return /.+@.+\..+/.test(s); 
}
const ok = isValidEmail("test");
send(to: "test"); // still string, no guarantee

// ✅ Fix: parser returns refined type
function parseEmail(s: string): Email | null { /* ... */ }
const email = parseEmail("test");
if (email) send(to: email); // typed Email
```

### Interface with optional fields

```typescript
// ❌ Anti: optional fields allow invalid combinations
interface Payment {
  amount: number;
  txId?: string;
  refundAt?: Date;
}
// Invalid state: both txId and refundAt present

// ✅ Fix: discriminated union enforces valid states
type Payment =
  | { kind: "unpaid"; amount: number }
  | { kind: "paid"; amount: number; txId: string }
  | { kind: "refunded"; amount: number; txId: string; refundAt: Date };
```

### Documentation as spec

```typescript
// ❌ Anti: state documented but not enforced
type Request = { method: string; body: unknown };
// @method must be "GET"|"POST"|"PUT"|"DELETE"
// @body required when method is "POST"

// ✅ Fix: types enforce the spec
type Request =
  | { method: "GET"; body?: never }
  | { method: "POST"; body: unknown }
  | { method: "PUT"; body: unknown }
  | { method: "DELETE"; body?: never };
```

## Source Anchors

- [TypeScript Handbook — Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [TypeScript Handbook — Discriminated Unions](https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes-func.html#discriminated-unions)
- [TypeScript Handbook — Literal Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#literal-types)
- [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/) — Alexis King
