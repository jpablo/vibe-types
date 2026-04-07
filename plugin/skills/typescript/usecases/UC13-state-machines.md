# State Machines

## The Constraint

Valid state transitions are enforced at compile time. Operations that are only meaningful in a specific state cannot be called when the object is in a different state; invalid call orderings are type errors, not runtime exceptions.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Typestate** | Phantom type parameter encodes current state; transition functions change the phantom | [-> T57](../catalog/T57-typestate.md) |
| **Phantom brands** | State marker types that are erased at runtime — zero overhead | [-> T27](../catalog/T27-erased-phantom.md) |
| **Discriminated union states** | Each state is a distinct variant; the discriminant field gates which operations are valid | [-> T01](../catalog/T01-algebraic-data-types.md) |
| **Type narrowing** | Narrow a union to the correct state variant inside a branch before calling state-specific operations | [-> T14](../catalog/T14-type-narrowing.md) |

## Patterns

### Pattern A — Phantom typestate for OOP-style objects

State is encoded in a phantom type parameter. Each transition function returns the connection in a new state. Methods like `authenticate()` are only callable on `Connection<Open>` — calling them on `Connection<Closed>` or `Connection<Authenticated>` is a compile error.

```typescript
declare const __state: unique symbol;
type PhantomState<S> = { readonly [__state]: S };

// State markers (no runtime representation):
type Closed        = PhantomState<"Closed">;
type Open          = PhantomState<"Open">;
type Authenticated = PhantomState<"Authenticated">;

// The phantom parameter S is erased; the class holds no state field:
class Connection<S> {
  private constructor(
    private readonly host: string,
    private readonly port: number,
  ) {}

  static create(host: string, port: number): Connection<Closed> {
    return new Connection<Closed>(host, port);
  }
}

// Transition functions live outside the class to avoid exposing a method
// with a wrong state on the type (TypeScript does not support conditional methods natively):
function open(conn: Connection<Closed>): Connection<Open> {
  console.log("Opening connection...");
  return conn as unknown as Connection<Open>;
}

function authenticate(conn: Connection<Open>, token: string): Connection<Authenticated> {
  console.log(`Authenticating with token ${token}`);
  return conn as unknown as Connection<Authenticated>;
}

function query(conn: Connection<Authenticated>, sql: string): string[] {
  console.log(`Executing: ${sql}`);
  return [];
}

function close(conn: Connection<Open> | Connection<Authenticated>): Connection<Closed> {
  console.log("Closing connection");
  return conn as unknown as Connection<Closed>;
}

// Correct sequence:
const closed = Connection.create("db.example.com", 5432);
const opened  = open(closed);
const authed  = authenticate(opened, "secret-token");
const rows    = query(authed, "SELECT * FROM users");
const done    = close(authed);

// Invalid transitions are compile errors:
authenticate(closed, "token"); // error: Connection<Closed> is not assignable to Connection<Open>
query(opened, "SELECT 1");     // error: Connection<Open> is not assignable to Connection<Authenticated>
open(authed);                  // error: Connection<Authenticated> is not assignable to Connection<Closed>
```

### Pattern B — Discriminated union state machine

State is modeled as a data-first discriminated union. The `kind` field is the discriminant; narrowing inside a switch exposes only the operations and fields relevant to that state. Adding a new state and forgetting to handle it in a switch is a compile error via the `never` exhaustiveness check.

```typescript
type TrafficLight =
  | { kind: "Red";    durationMs: number }
  | { kind: "Yellow"; durationMs: number }
  | { kind: "Green";  durationMs: number; pedestrianCrossing: boolean };

function nextState(light: TrafficLight): TrafficLight {
  switch (light.kind) {
    case "Red":    return { kind: "Green",  durationMs: 30_000, pedestrianCrossing: false };
    case "Green":  return { kind: "Yellow", durationMs: 5_000 };
    case "Yellow": return { kind: "Red",    durationMs: 20_000 };
    default: {
      const _exhaustive: never = light; // compile error if a new variant is added
      return _exhaustive;
    }
  }
}

function describe(light: TrafficLight): string {
  switch (light.kind) {
    case "Red":
      return `STOP — red for ${light.durationMs / 1000}s`;
    case "Yellow":
      return `CAUTION — yellow for ${light.durationMs / 1000}s`;
    case "Green":
      return `GO — green for ${light.durationMs / 1000}s` +
        (light.pedestrianCrossing ? " (pedestrian crossing active)" : "");
  }
}

// Cross-variant field access is a compile error:
declare const light: TrafficLight;
light.pedestrianCrossing; // error: does not exist on type 'TrafficLight'

// Narrowed access is fine:
if (light.kind === "Green") {
  light.pedestrianCrossing; // OK — narrowed to Green variant
}
```

### Pattern C — Function-based protocol (FP-style)

Each state is a distinct type. Transition functions accept only the correct state type and return the next state type. The protocol is encoded entirely in the function signatures — no class, no mutation, no runtime state field needed.

```typescript
// State types — distinct, non-interchangeable:
type IdleOrder     = { readonly kind: "Idle";     readonly cartItems: readonly string[] };
type PendingOrder  = { readonly kind: "Pending";  readonly cartItems: readonly string[]; readonly orderId: string };
type PaidOrder     = { readonly kind: "Paid";     readonly orderId: string; readonly paidAt: Date };
type ShippedOrder  = { readonly kind: "Shipped";  readonly orderId: string; readonly trackingCode: string };
type CancelledOrder = { readonly kind: "Cancelled"; readonly orderId: string; readonly reason: string };

// Transitions: each function accepts exactly the required state:
function addItem(order: IdleOrder, item: string): IdleOrder {
  return { ...order, cartItems: [...order.cartItems, item] };
}

function placeOrder(order: IdleOrder): PendingOrder {
  if (order.cartItems.length === 0) throw new Error("Cart is empty");
  return { kind: "Pending", cartItems: order.cartItems, orderId: `ord_${Date.now()}` };
}

function payOrder(order: PendingOrder, _paymentToken: string): PaidOrder {
  return { kind: "Paid", orderId: order.orderId, paidAt: new Date() };
}

function shipOrder(order: PaidOrder, trackingCode: string): ShippedOrder {
  return { kind: "Shipped", orderId: order.orderId, trackingCode };
}

function cancelOrder(order: IdleOrder | PendingOrder, reason: string): CancelledOrder {
  const orderId = order.kind === "Idle" ? "none" : order.orderId;
  return { kind: "Cancelled", orderId, reason };
}

// Correct sequence:
const idle     = addItem({ kind: "Idle", cartItems: [] }, "widget");
const pending  = placeOrder(idle);
const paid     = payOrder(pending, "tok_abc");
const shipped  = shipOrder(paid, "TRACK-001");

// Invalid transitions caught at compile time:
shipOrder(pending, "TRACK-002"); // error: PendingOrder is not assignable to PaidOrder
payOrder(idle, "tok_abc");       // error: IdleOrder is not assignable to PendingOrder
cancelOrder(paid, "changed mind"); // error: PaidOrder is not assignable to IdleOrder | PendingOrder

// No way to accidentally reuse a consumed state:
payOrder(pending, "tok_xyz");    // would double-charge — type system does not prevent this alone
                                 // but typestate or linear types (not in TS) would
```

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| State enforcement | Runtime checks: `if (this.state !== "Open") throw new Error(…)` — discovered on the wrong call | Phantom typestate or function protocol — wrong-state calls are compile errors before the program runs |
| Invalid transitions | Throws an exception that may propagate far from the call site | The caller's code does not compile — the error is at the call site, not a runtime stack trace |
| Discriminated state data | `switch (obj.type)` with no guarantee all cases are handled | `never` exhaustiveness check — unhandled variants are type errors when new states are added |
| FP-style protocol | Functions accept any object; wrong state passed silently | Distinct state types per stage; wrong type passed is a type error at the call site |

## When to Use Which Feature

**Phantom typestate** (Pattern A) fits OOP-style code where a stateful object moves through a lifecycle. The phantom parameter costs nothing at runtime. Use it when the object's identity is important (same object, different state) and transitions are sequential.

**Discriminated union** (Pattern B) is the best choice for data-first modeling — when the state is the data and you want pattern matching via `switch`. It is straightforward to add new states (though all switches must be updated), and the `never` check enforces that exhaustiveness.

**Function-based protocol** (Pattern C) is idiomatic in functional-style TypeScript. Each state is an immutable value; transitions produce new values. It integrates naturally with `pipe` and `Result` chains. Use it when states carry different data shapes and you want the compiler to enforce that consumed states cannot be reused.
