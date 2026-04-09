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
| **Interface per state** | Define a separate interface for each state exposing only the methods valid in that state | [-> T05](../catalog/T05-structural-typing.md) |
| **Overloads + Literal types** | Return a different type from a transition function depending on the string-literal state argument | [-> T52](../catalog/T52-literal-types.md) |
| **`Symbol.dispose` / `using`** | Scope a stateful resource to a block; the runtime calls teardown automatically on block exit | [-> T57](../catalog/T57-typestate.md) |

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

### Pattern D — Interface per state (expose only valid operations)

Define a separate interface for each protocol state. Each interface advertises only the methods valid in that state, so callers cannot invoke an out-of-state operation regardless of the underlying implementation. No phantom parameter needed — structural typing enforces the constraint.

```typescript
// One interface per state — each exposes only its valid operations:
interface ClosedSocket {
  readonly state: "Closed";
  open(): OpenSocket;
}

interface OpenSocket {
  readonly state: "Open";
  authenticate(token: string): AuthenticatedSocket;
  close(): ClosedSocket;
}

interface AuthenticatedSocket {
  readonly state: "Authenticated";
  query(sql: string): Promise<string[]>;
  close(): ClosedSocket;
}

// Separate concrete class per state — each satisfies exactly one interface:
class ClosedSocketImpl implements ClosedSocket {
  readonly state = "Closed" as const;
  constructor(private readonly host: string) {}
  open(): OpenSocket {
    console.log(`opening ${this.host}`);
    return new OpenSocketImpl(this.host);
  }
}

class OpenSocketImpl implements OpenSocket {
  readonly state = "Open" as const;
  constructor(private readonly host: string) {}
  authenticate(token: string): AuthenticatedSocket {
    console.log(`auth with ${token}`);
    return new AuthenticatedSocketImpl(this.host);
  }
  close(): ClosedSocket {
    return new ClosedSocketImpl(this.host);
  }
}

class AuthenticatedSocketImpl implements AuthenticatedSocket {
  readonly state = "Authenticated" as const;
  constructor(private readonly host: string) {}
  async query(sql: string): Promise<string[]> {
    console.log(`query: ${sql}`);
    return [];
  }
  close(): ClosedSocket {
    return new ClosedSocketImpl(this.host);
  }
}

function makeSocket(host: string): ClosedSocket {
  return new ClosedSocketImpl(host);
}

// The returned interface restricts what's callable at each stage:
const closed = makeSocket("db.example.com");  // ClosedSocket
const opened  = closed.open();                // OpenSocket
const authed  = opened.authenticate("tok");   // AuthenticatedSocket
const rows    = await authed.query("SELECT 1"); // OK

opened.query("SELECT 1");  // error: Property 'query' does not exist on type 'OpenSocket'
closed.authenticate("tok"); // error: Property 'authenticate' does not exist on type 'ClosedSocket'
```

**Why this over phantom typestate**: no casting required inside the implementation; structural compatibility is verified by the compiler at the `implements` clause. The tradeoff is that nothing prevents the implementation from returning `this` cast to the wrong interface — encapsulation requires a factory function that returns the narrowest interface type.

### Pattern E — Overloaded transitions with Literal state arguments

When state is represented as a string value (Redux-style stores, configuration objects, serialized state machines), overloaded functions with `Literal` argument types give the checker distinct return types per state value. The caller gets a precisely typed result without any generic parameter.

```typescript
type Idle      = { readonly status: "idle" };
type Fetching  = { readonly status: "fetching"; readonly abortController: AbortController };
type Success<T> = { readonly status: "success"; readonly data: T };
type Failure   = { readonly status: "failure"; readonly error: Error };

type FetchState<T> = Idle | Fetching | Success<T> | Failure;

// Overloads give the checker the exact return type per input state:
function startFetch(state: Idle): Fetching;
function startFetch(state: FetchState<unknown>): FetchState<unknown>;
function startFetch(_state: FetchState<unknown>): FetchState<unknown> {
  return { status: "fetching", abortController: new AbortController() };
}

function succeed<T>(state: Fetching, data: T): Success<T>;
function succeed<T>(state: FetchState<unknown>, data: T): FetchState<T>;
function succeed<T>(_state: FetchState<unknown>, data: T): FetchState<T> {
  return { status: "success", data };
}

function fail(state: Fetching, error: Error): Failure;
function fail(state: FetchState<unknown>, error: Error): FetchState<unknown>;
function fail(_state: FetchState<unknown>, error: Error): FetchState<unknown> {
  return { status: "failure", error };
}

const idle: Idle = { status: "idle" };
const fetching = startFetch(idle);          // inferred: Fetching
const done     = succeed(fetching, [1, 2]); // inferred: Success<number[]>

startFetch(fetching); // error: Fetching is not assignable to Idle
succeed(idle, []);    // error: Idle is not assignable to Fetching
```

This pattern integrates cleanly with React state (`useState<FetchState<T>>`) and state machines that live in a serializable store.

### Pattern F — Scoped resource protocol with `using` / `Symbol.dispose`

When a resource must be acquired before use and released after — a connection, a lock, a transaction — the `using` declaration (TC39 Explicit Resource Management, TypeScript 5.2+) enforces the lifecycle. The compiler guarantees the cleanup method is called on block exit, including on exception. This is the TypeScript analogue of Scala's context functions for scoped capabilities.

```typescript
interface Disposable { [Symbol.dispose](): void; }

// A "session" token that is only valid inside the `using` block:
class DbSession implements Disposable {
  private closed = false;

  constructor(private readonly connStr: string) {
    console.log(`[db] open ${connStr}`);
  }

  query(sql: string): string[] {
    if (this.closed) throw new Error("Session already closed");
    console.log(`[db] query: ${sql}`);
    return [];
  }

  [Symbol.dispose](): void {
    this.closed = true;
    console.log(`[db] closed ${this.connStr}`);
  }
}

function openSession(connStr: string): DbSession {
  return new DbSession(connStr);
}

// The session is automatically closed when the block exits:
{
  using session = openSession("postgres://localhost/mydb");
  const rows = session.query("SELECT 1"); // OK inside block
} // session[Symbol.dispose]() called here — even if query() threw

// session is not accessible outside the block (block-scoped `using`).
```

For async teardown, use `Symbol.asyncDispose` with `await using`:

```typescript
interface AsyncDisposable { [Symbol.asyncDispose](): Promise<void>; }

class AsyncDbSession implements AsyncDisposable {
  constructor(private readonly connStr: string) {}

  async query(sql: string): Promise<string[]> { return []; }

  async [Symbol.asyncDispose](): Promise<void> {
    await flushPendingWrites();
    console.log("closed");
  }
}

async function run() {
  await using session = new AsyncDbSession("postgres://...");
  await session.query("SELECT 1");
} // asyncDispose called automatically
```

**Encapsulation note**: to prevent callers from constructing a `DbSession` with `this.closed = true` directly, keep the constructor private and expose only the factory function. The factory's return type can be an interface that does not include `[Symbol.dispose]`, hiding teardown from callers and ensuring only the `using` declaration can invoke it.

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| State enforcement | Runtime checks: `if (this.state !== "Open") throw new Error(…)` — discovered on the wrong call | Phantom typestate or function protocol — wrong-state calls are compile errors before the program runs |
| Invalid transitions | Throws an exception that may propagate far from the call site | The caller's code does not compile — the error is at the call site, not a runtime stack trace |
| Discriminated state data | `switch (obj.type)` with no guarantee all cases are handled | `never` exhaustiveness check — unhandled variants are type errors when new states are added |
| FP-style protocol | Functions accept any object; wrong state passed silently | Distinct state types per stage; wrong type passed is a type error at the call site |

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **Phantom typestate** (A) | Invalid transitions are compile errors; zero runtime cost | Requires casts inside the implementation; one phantom type per state |
| **Discriminated union** (B) | States carry their own data; exhaustive matching via `never` | No method-level restriction — all methods are always visible on the union |
| **Function-based protocol** (C) | Immutable; FP-friendly; distinct types per stage | Cannot prevent reuse of a "consumed" state — TS has no linear types |
| **Interface per state** (D) | No casts; structural compatibility checked at `implements` | Implementation can lie; encapsulation requires a factory hiding the concrete type |
| **Overloaded Literals** (E) | Works with string-valued state (Redux, config); no new types needed | Overload count grows with states; runtime must validate the exhaustive implementation |
| **`using` / `Symbol.dispose`** (F) | Lifecycle enforced by the runtime; works with exceptions | Requires TypeScript 5.2+ and `"esnext.disposable"` in `tsconfig` `lib`; only scopes lifetime, not state transitions |

## When to Use Which Feature

**Phantom typestate** (Pattern A) fits OOP-style code where a stateful object moves through a lifecycle. The phantom parameter costs nothing at runtime. Use it when the object's identity is important (same object, different state) and transitions are sequential.

**Discriminated union** (Pattern B) is the best choice for data-first modeling — when the state is the data and you want pattern matching via `switch`. It is straightforward to add new states (though all switches must be updated), and the `never` check enforces exhaustiveness.

**Function-based protocol** (Pattern C) is idiomatic in functional-style TypeScript. Each state is an immutable value; transitions produce new values. It integrates naturally with `pipe` and `Result` chains. Use it when states carry different data shapes and you want the compiler to enforce that consumed states cannot be reused.

**Interface per state** (Pattern D) is the right choice when you want structural safety without phantom casts. It works well for public APIs where callers must not see methods irrelevant to the current state, and the implementation can be a single class satisfying all interfaces.

**Overloaded Literals** (Pattern E) applies when state is already a string value in a store or configuration object and you need precise return types from a transition function without introducing new classes or phantom parameters. Common in React `useReducer` and Redux-style architectures.

**`using` / `Symbol.dispose`** (Pattern F) is the right tool when the constraint is lifecycle (acquire before use, release after) rather than step ordering. Combine with phantom typestate or interface per state to enforce both scope and transition rules.

## Source Anchors

- TypeScript Handbook — [Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- TypeScript Handbook — [Discriminated Unions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions)
- TypeScript Handbook — [Function Overloads](https://www.typescriptlang.org/docs/handbook/2/functions.html#function-overloads)
- TypeScript 5.2 release notes — [Using Declarations and Explicit Resource Management](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-2.html)
- TC39 Proposal — [Explicit Resource Management (`using`)](https://github.com/tc39/proposal-explicit-resource-management)
- *Programming TypeScript* (O'Reilly) — Ch. 6 "Advanced Types", typestate pattern

## When to Use It

Use state machines when your domain has **sequential invariants** — conditions that must hold in order across operations:

```typescript
// ✅ Use: file handle lifecycle with strict ordering
declare const __state: unique symbol;
class File<S> {
  constructor(private readonly path: string, private readonly [__state]: S = {} as any) {}
  static open(path: string): File<Open> { return new File(path); }
}
function read(f: File<Open>): File<Closed> { /* ... */ return f as any; }
function write(f: File<Open>, data: string): File<Open> { /* ... */ return f; }
// read(File.open("x")); // ✅ error if not Open state
```

Use state machines when **field availability depends on state** — some data only exists in certain states:

```typescript
// ✅ Use: form with conditional fields
type LoginForm =
  | { state: "idle"; email?: never; password?: never }
  | { state: "email_entered"; email: string; password?: never }
  | { state: "password_entered"; email: string; password: string };
// password field only valid in password_entered variant
```

Use state machines when **wrong sequencing causes data loss or corruption**:

```typescript
// ✅ Use: database transaction with strict ordering
type Txn<State> = State extends "begin" ? { begin(): Txn<"active"> }
  : State extends "active" ? { commit(): Txn<"done">; rollback(): Txn<"done"> }
  : State extends "done" ? {} : never;
// commit() on a Txn<"begin"> should be a compile error
```

## When Not to Use It

Avoid state machines for **simple flags** where ordering doesn't matter:

```typescript
// ❌ Don't use: boolean flags with no sequencing
interface UserSettings {
  darkMode: boolean;
  notificationsEnabled: boolean;
  language: string;
}
// No need for state machine — these are independent!

// ✅ Keep it simple:
type Settings = { darkMode: boolean; notificationsEnabled: boolean; language: string };
```

Avoid state machines for **high-churn state graphs** with many transient states:

```typescript
// ❌ Don't use: 50+ states with complex transitions
type ParserState =
  | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9
  | S10 | S11 | ...; // 50+ states
// Consider a runtime state machine library instead

// ✅ Better: use XState or similar for complex state graphs
```

Avoid state machines for **shared mutable state** where typestate breaks:

```typescript
// ❌ Don't use: shared objects passed across threads/processes
interface SharedCache<S> {
  get(key: string): string | undefined;
  set(key: string, value: string): SharedCache<S>;
}
// Phantom states don't track real-world shared state

// ✅ Better: use runtime checks + proper concurrency primitives
```

## Antipatterns When Using State Machines

### Antipattern 1: State explosion via over-refinement

```typescript
// ❌ Anti-pattern: too many states for simple logic
type ButtonState =
  | "idle" | "clicked" | "clicked_once" | "clicked_twice" | "clicked_three_times" /* ... */
  | "hovered_idle" | "hovered_clicked" | "hovered_clicked_once" /* exponential growth */;

// ✅ Better: separate concerns
type ClickCount = 0 | 1 | 2 | 3 | "many";
type HoverState = { clicked: ClickCount; hovered: boolean };
```

### Antipattern 2: Runtime state vs typestate mismatch

```typescript
// ❌ Anti-pattern: runtime state not reflected in type
class Editor<S> {
  private actualState: "draft" | "review" | "published" = "draft";
  publish(): Editor<Published> {
    this.actualState = "published"; // ✅ runtime
    return this as any; // ❌ cast needed — typestate is lie
  }
  // actualState can diverge from phantom S!

// ✅ Better: keep typestate + runtime state together, or remove one
class Editor<S> {
  constructor(private state: S extends Published ? "published" : "draft") {}
}
```

### Antipattern 3: `as any` everywhere

```typescript
// ❌ Anti-pattern: state machine becomes no-op
function transition<V>(obj: Obj<A>): Obj<B> {
  // No real validation — just cast
  return obj as any; // "trust me bro"
}

// ✅ Better: validate runtime state in the transition
function transition(obj: Obj<A>): Obj<B> {
  if (!obj.isValidForB()) throw new Error("Cannot transition to B");
  return obj as unknown as Obj<B>; // cast is safe now
}
```

### Antipattern 4: Forgetting to update all switch branches

```typescript
// ❌ Anti-pattern: new state added, old switch not updated
type Order = { status: "pending" | "shipped" } | /* forgot "cancelled"! */

function render(order: Order) {
  switch (order.status) {
    case "pending": return "Awaiting...";
    case "shipped": return "On the way";
    // Missing "cancelled" case!
  }
}

// ✅ Better: use exhaustiveness check
function render(order: Order) {
  switch (order.status) {
    case "pending": return "Awaiting...";
    case "shipped": return "On the way";
    case "cancelled": return "Cancelled";
    default: const _exhaustive: never = order; return _exhaustive;
  }
}
```

## Antipatterns with Other Techniques (where State Machines Help)

### Antipattern 1: Nested if/else chains for state

```typescript
// ❌ Anti-pattern: if/else cascade
function handleSubmit(form: Form) {
  if (form.status === "empty") return { error: "Required fields missing" };
  else if (form.status === "validating") return { error: "Still validating..." };
  else if (form.status === "invalid") return { error: form.errors.join(", ") };
  else if (form.status === "submitting") return { error: "Already submitting..." };
  else if (form.status === "success") return { error: "Already submitted" };
  else if (form.status === "error") return { error: "Previous error not cleared" };
  // Falls through to submit...
}

// ✅ Better: discriminated union + exhaustive match
type FormStatus =
  | { status: "empty" }
  | { status: "invalid"; errors: string[] }
  | { status: "valid"; values: Record<string, string> };

function handleSubmit(form: FormStatus) {
  switch (form.status) {
    case "empty": return { error: "Required fields missing" };
    case "invalid": return { error: form.errors.join(", ") };
    case "valid": return doSubmit(form.values);
    default: const _exhaustive: never = form; throw new Error("Unreachable");
  }
}
```

### Antipattern 2: Union of boolean flags

```typescript
// ❌ Anti-pattern: flag combinations impossible to validate
interface Payment {
  hasCard: boolean;
  hasToken: boolean;
  isProcessing: boolean;
  isCompleted: boolean;
}
// Can have hasCard=true AND isCompleted=true (inconsistent!)

// ✅ Better: state machine enforces mutually exclusive states
type Payment =
  | { state: "empty" }
  | { state: "has_card"; card: Card }
  | { state: "processing" }
  | { state: "completed"; receipt: Receipt };
// Exactly one state at a time — no flag combinations
```

### Antipattern 3: Magic string state values

```typescript
// ❌ Anti-pattern: string state with no type safety
interface Workflow {
  state: string; // "draft" | "review" | "approved" | "published" | "..."
}
function approve(w: Workflow) {
  if (w.state !== "draft") return { error: "Can only approve drafts" };
  // Runtime error on typo: w.state === "drafft" (!= "draft")
}

// ✅ Better: literal types enforce correct values
interface Workflow {
  state: "draft" | "review" | "approved" | "published";
}
function approve(w: Workflow): Workflow {
  if (w.state !== "draft") throw new Error("Can only approve drafts");
  return { ...w, state: "review" };
}
```

### Antipattern 4: Mutable state object with runtime guards

```typescript
// ❌ Anti-pattern: runtime guards throughout
class Document {
  state: "draft" | "published" = "draft";
  edit(content: string) {
    if (this.state !== "draft") throw new Error("Cannot edit published doc");
    this.content = content;
  }
  publish() {
    if (this.state !== "draft") throw new Error("Already published");
    this.state = "published";
  }
}
const d = new Document();
d.publish();
d.edit("oops"); // Runtime error! Thrown at the wrong call site

// ✅ Better: phantom typestate catches error before runtime
class Document<S> {
  private constructor(private content: string, private _state: S = {} as any) {}
  static create(content: string): Document<Draft> { return new Document(content); }
}
function edit(doc: Document<Draft>, content: string): Document<Draft> {
  return new Document(content);
}
function publish(doc: Document<Draft>): Document<Published> {
  return new Document(doc.content) as any;
}
const d = Document.create("hello");
publish(d);
edit(d, "oops"); // ❌ Compile error: d is Document<Published>, not Document<Draft>
```
