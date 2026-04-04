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

### Pattern E — Parse, don't validate

Instead of validating a raw string and throwing, return a branded type. Callers who need an `Email` must go through the parser; raw strings never satisfy the `Email` type. See [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/) for the full motivation.

```typescript
type Email = Branded<string, "Email">;

function parseEmail(raw: string): Email {
  const trimmed = raw.trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
    throw new Error(`Invalid email: ${raw}`);
  }
  return trimmed as Email;
}

function sendWelcome(to: Email): void {
  console.log(`Sending welcome to ${to}`);
}

const email = parseEmail("alice@example.com"); // Email — validated once at the boundary
sendWelcome(email);                            // OK
sendWelcome("alice@example.com");              // error: string is not assignable to Email
```

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Payment state | Single object with all optional fields; guarded with `if (payment.transactionId)` at every call site | Discriminated union — impossible fields absent from each variant; narrowing replaces guards |
| Port validation | `function connect(host, port) { if (port < 1 \|\| port > 65535) throw … }` — repeated at every call site | Branded `Port`; validation once in `makePort`, enforced by types everywhere else |
| State machines | Documented conventions (`door.state === 'locked'`); wrong transitions discovered at runtime | Phantom type parameter; invalid transitions are type errors before the code runs |
| Email handling | `validate(email)` returns boolean; caller may forget to call it or may pass the raw string anyway | `parseEmail` returns `Email` branded type; unvalidated strings are not assignable |

## When to Use Which Feature

**Discriminated union** (Pattern A) is the default tool when a value can be in one of several mutually exclusive states. Use it when each state has different data associated with it — the compiler will prevent accessing fields from the wrong variant.

**Branded type** (Pattern B) is best for primitive values that have domain-level restrictions (port ranges, positive integers, validated strings). Validation happens once at the boundary; everything downstream trusts the type.

**Phantom type** (Pattern C) is the right choice when you need to enforce sequential or restricted protocols — state machines, connection lifecycles, builder stages — without duplicating data structures for each state. The phantom parameter is erased at runtime, so there is zero overhead.
