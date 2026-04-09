# Encapsulation

## The Constraint

Internal representations must be hidden; only a controlled public surface is exposed. Code outside the module cannot read private fields, construct internal objects directly, or bypass invariants established at creation time.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **`#private` fields** | Runtime-enforced privacy; survives `as any` and JavaScript callers | [-> T21](../catalog/T21-encapsulation.md) |
| **`private` keyword** | Compile-time-only privacy; appears in `.d.ts`; lighter than `#` | [-> T21](../catalog/T21-encapsulation.md) |
| **`private` constructor + static factory** | Force all construction through a validation path; block subclassing | [-> T21](../catalog/T21-encapsulation.md) |
| **Readonly** | Prevent mutation of exposed properties after construction | [-> T32](../catalog/T32-immutability-markers.md) |
| **Branded / opaque types** | Opaque handles — callers receive a typed token but cannot construct or inspect it without going through the module | [-> T03](../catalog/T03-newtypes-opaque.md) |
| **Interface as public API** | Export only an interface; keep the class an implementation detail | [-> T05](../catalog/T05-type-classes.md) |
| **Sealed interface via unexported symbol** | Prevent external implementations of an interface; own a closed set of implementors | [-> T21](../catalog/T21-encapsulation.md) |

## Patterns

### Pattern A — Class with `#private` fields and a public interface

ECMAScript private fields (`#`) are enforced at runtime by the JavaScript engine, not just by the TypeScript type checker. External code cannot reach the field even through `any` or reflection hacks.

```typescript
interface Account {
  readonly id: string;
  readonly owner: string;
  readonly balance: number;
  deposit(amount: number): void;
  withdraw(amount: number): void;
  statement(): string;
}

class BankAccount implements Account {
  readonly id: string;
  readonly owner: string;

  // Runtime-enforced: external code cannot read or write #balance:
  #balance: number;
  #transactions: Array<{ type: "credit" | "debit"; amount: number; at: Date }> = [];

  constructor(id: string, owner: string, initialBalance: number) {
    if (initialBalance < 0) throw new RangeError("Initial balance cannot be negative");
    this.id     = id;
    this.owner  = owner;
    this.#balance = initialBalance;
  }

  get balance(): number {
    return this.#balance; // read-only access via getter
  }

  deposit(amount: number): void {
    if (amount <= 0) throw new RangeError("Deposit amount must be positive");
    this.#balance += amount;
    this.#transactions.push({ type: "credit", amount, at: new Date() });
  }

  withdraw(amount: number): void {
    if (amount <= 0) throw new RangeError("Withdrawal amount must be positive");
    if (amount > this.#balance) throw new RangeError("Insufficient funds");
    this.#balance -= amount;
    this.#transactions.push({ type: "debit", amount, at: new Date() });
  }

  statement(): string {
    return this.#transactions
      .map(t => `${t.type === "credit" ? "+" : "-"}${t.amount} @ ${t.at.toISOString()}`)
      .join("\n");
  }
}

const acc = new BankAccount("acct-1", "Alice", 1000);
acc.deposit(500);
acc.balance;       // OK — 1500, read via getter
acc.#balance;      // SyntaxError — '#balance' outside class body is a parse error (enforced at JS syntax level)

// 'as any' does not help — the # syntax is rejected by the parser before runtime:
(acc as any).#balance; // SyntaxError — same parse error; the compiler never emits this
```

### Pattern B — Module boundary encapsulation — export interface, not the class

By exporting only the interface (and a factory function), consumers can never import the class, construct it directly, or depend on internal implementation details. The class is an implementation detail, free to be replaced.

```typescript
// user-store.ts

export interface UserStore {
  findById(id: string): { id: string; name: string; email: string } | null;
  save(user: { name: string; email: string }): string;
  count(): number;
}

// Not exported — callers cannot new InMemoryUserStore() or reference its fields:
class InMemoryUserStore implements UserStore {
  private readonly users = new Map<string, { id: string; name: string; email: string }>();
  private nextId = 1;

  findById(id: string) {
    return this.users.get(id) ?? null;
  }

  save(user: { name: string; email: string }): string {
    const id = `u${this.nextId++}`;
    this.users.set(id, { id, ...user });
    return id;
  }

  count(): number {
    return this.users.size;
  }
}

// Only this factory is exported:
export function createUserStore(): UserStore {
  return new InMemoryUserStore();
}

// ------------------------------------------------------------
// consumer.ts

import { createUserStore, UserStore } from "./user-store";

const store: UserStore = createUserStore();
const id = store.save({ name: "Alice", email: "alice@example.com" });
const user = store.findById(id); // { id, name, email } | null

// Cannot access internals:
// store.users       // error: Property 'users' does not exist on type 'UserStore'
// store.nextId      // error: Property 'nextId' does not exist on type 'UserStore'
// new InMemoryUserStore() // error: Cannot find name 'InMemoryUserStore'
```

### Pattern C — Private constructor with static factory

Making the constructor `private` forces all callers through a controlled creation path. The static factory can validate, normalise, or return `null`/a result type — no caller can bypass the invariants by calling `new` directly.

```typescript
// token.ts

export class Token {
  // Private constructor — only reachable inside the class body:
  private constructor(private readonly value: string) {}

  /** Returns null when the raw string is empty or whitespace-only. */
  static create(raw: string): Token | null {
    const trimmed = raw.trim();
    if (trimmed.length === 0) return null;
    return new Token(trimmed);
  }

  toString(): string {
    return this.value;
  }
}

// Consumer:
const t = Token.create("  hello  "); // OK — normalised to "hello"
const bad = Token.create("   ");     // null — rejected at the boundary

// new Token("hello"); // error: Constructor of class 'Token' is private and only accessible within the class declaration

// Subclassing is also blocked — the subclass constructor must call super(),
// but super() is private here:
// class SpecialToken extends Token {} // error: Cannot extend a class 'Token'.
//                                     // Class constructor is marked as private.
```

This is the TypeScript equivalent of Lean's `private mk ::` or Rust's `pub struct Cents(u64)` with a private inner field — the only construction path goes through the module's own validation logic.

### Pattern D — Sealed interface via unexported symbol

TypeScript has no `sealed` keyword, but an unexported unique symbol as a required interface property creates the same effect: external code cannot implement the interface because it cannot reference the symbol.

```typescript
// codec.ts

// Not exported — external code cannot name or satisfy this property:
declare const _sealed: unique symbol;

export interface Codec {
  readonly [_sealed]: never;
  encode(data: unknown): Uint8Array;
  decode(bytes: Uint8Array): unknown;
}

// Only implementations in this file can satisfy Codec:
class JsonCodec implements Codec {
  readonly [_sealed]!: never;
  encode(data: unknown): Uint8Array {
    return new TextEncoder().encode(JSON.stringify(data));
  }
  decode(bytes: Uint8Array): unknown {
    return JSON.parse(new TextDecoder().decode(bytes));
  }
}

export const json: Codec = new JsonCodec();

// ------------------------------------------------------------
// consumer.ts

import { Codec, json } from "./codec";

function roundtrip(codec: Codec, value: unknown): unknown {
  return codec.decode(codec.encode(value));
}

// External code cannot add new Codec implementations:
// const custom: Codec = { encode: ..., decode: ..., [???]: ... };
// error — _sealed is not accessible outside codec.ts
```

This mirrors Rust's sealed trait pattern (hiding the supertrait in a private module) and Scala's approach of restricting extension. Use it when you own a set of implementations and want the type system to prevent ad-hoc third-party implementations that might violate unstated contracts.

### Pattern E — Branded opaque handle

The caller receives a `UserId` value — a branded string — but cannot construct one without calling `createUser`. The internal implementation (the actual string format, database key strategy) is invisible. The brand prevents a raw `string` from being used anywhere `UserId` is expected.

```typescript
// user-service.ts

declare const __brand: unique symbol;
type Brand<B>      = { readonly [__brand]: B };
type Branded<T, B> = T & Brand<B>;

export type UserId = Branded<string, "UserId">;

type UserRecord = {
  readonly id: UserId;
  readonly name: string;
  readonly createdAt: Date;
};

// Internal storage — not exported:
const store = new Map<string, UserRecord>();
let counter = 0;

// Only way to obtain a UserId is through this module:
export function createUser(name: string): UserId {
  const id = `usr_${++counter}` as UserId; // cast is inside the module
  store.set(id, { id, name, createdAt: new Date() });
  return id;
}

export function getUser(id: UserId): UserRecord | null {
  return store.get(id) ?? null;
}

export function deleteUser(id: UserId): boolean {
  return store.delete(id);
}

// ------------------------------------------------------------
// consumer.ts

import { UserId, createUser, getUser } from "./user-service";

const id: UserId = createUser("Alice"); // OK — returned from module
const user = getUser(id);               // OK

// Cannot forge a UserId:
const fakeId = "usr_999" as UserId;    // error: Conversion of type 'string' to type 'UserId' may be a mistake
getUser("usr_999");                     // error: Argument of type 'string' is not assignable to parameter of type 'UserId'

// Cannot mix up UserId with other branded handles:
declare const __orderBrand: unique symbol;
type OrderId = Branded<string, "OrderId">;
declare const orderId: OrderId;

getUser(orderId); // error: OrderId is not assignable to UserId
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **`#private` fields** (A) | Runtime-enforced; survives `as any` and JavaScript callers | Only hides the value inside the class, not the class shape itself |
| **Export interface + factory** (B) | Class is invisible to consumers; implementation freely replaceable | Interface must be kept in sync with the class manually |
| **Private constructor + factory** (C) | Forces all construction through validation; subclassing is also blocked | `private` constructor is a TypeScript-only check; JS callers can still call `new` |
| **Sealed interface via symbol** (D) | Prevents third-party implementations; enforced structurally, no runtime cost | Can be worked around with `as unknown as Codec`; the sealing is a convention, not a language primitive |
| **Branded opaque handle** (E) | Primitive-typed IDs become type-safe; wrong brand caught at compile time | The `as Brand` cast inside the module is a loophole — discipline required |

### `private` keyword vs `#` ECMAScript private fields

Both suppress external access in TypeScript, but they differ at runtime:

| | `private` keyword | `#field` syntax |
|---|---|---|
| Enforcement | Compile-time only | Runtime (JS engine) |
| Bypassed by `as any` | Yes | No — parser rejects `obj.#field` entirely |
| Accessible in subclasses | No (same as `#`) | No |
| Visible via `Object.keys` / serialisation | Yes — the property exists on the object | No — truly absent from the object |
| Use in `.d.ts` / interfaces | Yes | No — `#` fields cannot appear in interfaces |

Prefer `#` when runtime privacy matters (library code, security boundaries). Use `private` when you need the field to appear in the emitted `.d.ts` shape or when targeting environments that do not yet support private fields.

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Private fields | `_balance` convention; any code can read and write it; ignored by the runtime | `#balance` is enforced by the JS engine at runtime; TypeScript also catches it at compile time |
| Hiding the class | Export everything; consumers couple to implementation; refactoring breaks callers | Export only the interface and factory; class is invisible to consumers; implementation is freely replaceable |
| Opaque handles | Plain strings used as IDs everywhere; wrong ID type passed silently; no enforcement | Branded `UserId`; raw strings not assignable; different branded IDs not interchangeable |
| Invariant protection | Public fields mutated after construction; invariants checked inconsistently | `readonly` fields; private setters; mutation only through controlled methods that re-validate |

## When to Use Which Feature

**`#private` fields** (Pattern A) are the strongest encapsulation primitive. Use them for fields that maintain invariants — balances, internal counters, mutable collections — where external mutation would corrupt the object's state. The runtime enforcement means even JavaScript callers (bypassing TypeScript) cannot access these fields.

**Module non-export** (Pattern B) is the right tool when the entire class is an implementation detail. Exporting only the interface decouples consumers from the implementation completely: you can swap `InMemoryUserStore` for `PostgresUserStore` without touching any consumer file.

**Private constructor + static factory** (Pattern C) applies when the object itself is the public type but all valid instances must be validated at creation time. The constructor block enforces the invariant; no caller can bypass it by calling `new`. Subclassing is automatically blocked as a bonus.

**Sealed interface via unexported symbol** (Pattern D) is the right tool when you want to own a closed set of implementations. Consumers can accept and use the interface, but they cannot add new implementations that might violate unstated protocol invariants. Use it for plugin systems, backend adapters, or format types where the implementor list is intentionally fixed.

**Branded opaque handles** (Pattern E) apply when callers need to hold a reference to an entity — pass it around, store it, send it back — but must not construct, inspect, or forge that reference. The brand makes the type system enforce the module boundary even for primitive-typed identifiers.

## When to Use

### When protecting invariants

```typescript
class Transaction {
  #balance: number;
  
  deposit(amount: number) {
    if (amount <= 0) throw new Error("Amount must be positive");
    this.#balance += amount;
  }
}
```

**Why**: The invariant `amount > 0` prevents corrupted state; callers can't bypass validation.

### When hiding implementation details

```typescript
export interface Cache { get: () => T | null; set: (v: T) => void; }

class MapBackedCache<T> implements Cache {
  private map = new Map(); // hidden from consumers
  // ...
}
```

**Why**: Consumers depend only on the interface; you can swap to Redis without breaking them.

### When preventing object forgery

```typescript
class Token {
  private constructor(private readonly _value: string) {}
  static create(input: string): Token | null {
    return input.length > 0 ? new Token(input) : null;
  }
}

// new Token("") // compile error
```

**Why**: All instances pass validation; the constructor can't be called directly.

### When preventing external implementations

```typescript
declare const _sealed: unique symbol;

export interface Driver {
  readonly [_sealed]: never;
  connect(): void;
}

class PostgresDriver implements Driver {
  [_sealed]!: never;
  connect() { /* ... */ }
}
```

**Why**: Only you control implementations; prevents broken third-party adapters.

## When NOT to Use

### For simple data carriers

```typescript
// ❌ Over-engineered
class Config {
  #host: string;
  #port: number;
  
  private constructor(host: string, port: number) {
    this.#host = host;
    this.#port = port;
  }
}

// ✅ Simple object
type Config = { readonly host: string; readonly port: number };
```

**Why**: No invariants to protect; adds complexity without benefit.

### In performance-critical hot paths

```typescript
// ❌ Extra indirection
class Counter {
  #count = 0;
  increment() { this.#count++; }
  get() { return this.#count; }
}

for (let i = 0; i < 1_000_000; i++) {
  counter.increment(); // method call overhead
}

// ✅ Direct field
let count = 0;
for (let i = 0; i < 1_000_000; i++) {
  count++; // faster
}
```

**Why**: Getter/setter overhead matters in tight loops.

### When mocking is required

```typescript
// ❌ Can't mock — #private fields can't be observed
class Service {
  #repo: Repository;
  async load() {
    return this.#repo.find();
  }
}

// ✅ Dependency injection
class Service {
  async load(repo: Repository) {
    return repo.find(); // easily mocked
  }
}
```

**Why**: Encapsulation makes testing harder when you need to observe internal state.

### For utility functions

```typescript
// ❌ Unnecessary class
class MathUtils {
  private constructor() {}
  static add(a: number, b: number): number {
    return a + b;
  }
}

// ✅ Simple functions
function add(a: number, b: number): number {
  return a + b;
}
```

**Why**: Pure functions have no state to protect.

## Antipatterns When Using

### Public getters that expose internals

```typescript
// ❌ Leaks internal structure
class Document {
  #metadata: { author: string; tags: string[] };
  
  get internals() {
    return this.#metadata; // exposes mutable object
  }
}

const d = new Document();
d.internals.tags.push("hack"); // mutated internal state

// ✅ Return immutable view
get tags(): readonly string[] {
  return this.#metadata.tags;
}
```

### Mutable returns from getters

```typescript
// ❌ Returns internal array directly
class ShoppingCart {
  #items = new Set<string>();
  
  get items() {
    return this.#items; // consumer can mutate internals
  }
}

// ✅ Return snapshot
get items() {
  return Array.from(this.#items);
}
```

### Accepting mutable params

```typescript
// ❌ External caller can mutate after passing
class User {
  private setName(data: { name: string }) {
    this.#name = data.name;
  }
}

const input = { name: "Alice" };
user.setName(input);
input.name = "Bob"; // now what?

// ✅ Extract only needed values
private setName(name: string) {
  this.#name = name; // no reference kept
}
```

### Overusing sealed interfaces

```typescript
// ❌ Makes evolution painful
declare const _sealed: unique symbol;

export interface Payment {
  readonly [_sealed]: never;
  charge(amount: number): Promise<void>;
}

// Need to add refund()? Must change interface, break all implementations

// ✅ Use standard interface when evolution needed
export interface Payment {
  charge(amount: number): Promise<void>;
  refund?(): Promise<void>; // optional, backward compatible
}
```

### Private constructor with no validation

```typescript
// ❌ What's the point?
class Email {
  private constructor(private readonly value: string) {}
  
  static create(value: string): Email {
    return new Email(value); // no validation
  }
}

// ✅ Add actual invariant
static create(value: string): Email | null {
  return /.+@.+\..+/.test(value) ? new Email(value) : null;
}
```

## Antipatterns Where Encapsulation Helps

### Public state mutation everywhere

```typescript
// ❌ Anyone can corrupt state
type Account = {
  balance: number;
  transactions: string[];
};

function withdraw(account: Account, amount: number) {
  account.balance -= amount; // no validation
  account.transactions.push(`-$${amount}`);
}

withdraw({ balance: 100, transactions: [] }, 200); // negative balance!

// ✅ Encapsulation enforces invariants
class Account {
  #balance = 0;
  
  withdraw(amount: number): void {
    if (amount > this.#balance) throw new Error("Insufficient funds");
    this.#balance -= amount;
  }
  
  get balance(): number { return this.#balance; } // read-only
}
```

### Partially constructed objects

```typescript
// ❌ Object exists in invalid state
class User {
  id: string = "";
  email: string = "";
  
  set(data: Partial<{ id: string; email: string }>) {
    this.id = data.id ?? "";
    this.email = data.email ?? "";
  }
}

const u = new User();
u.set({ id: "123" }); // no email yet! but object is usable

// ✅ Private constructor ensures completeness
class User {
  readonly id: string;
  readonly email: string;
  
  private constructor(id: string, email: string) {
    this.id = id;
    this.email = email;
  }
  
  static create(id: string, email: string): User | null {
    if (!id || !email) return null;
    return new User(id, email);
  }
}
```

### Magic strings as IDs

```typescript
// ❌ Wrong ID types mix silently
function getUser(id: string) { /* ... */ }
function getOrder(id: string) { /* ... */ }

getUser(getOrder("123")); // Oops, passed order ID to getUser

// ✅ Branded types catch errors
type UserId = string & { readonly brand: unique symbol };
type OrderId = string & { readonly brand: unique symbol };

function getUser(id: UserId) { /* ... */ }
function getOrder(id: OrderId) { /* ... */ }

// getUser("123"); // type error
```

### Global mutable registry

```typescript
// ❌ Any code can pollute the registry
const plugins = new Map<string, Plugin>();

plugins.set("auth", authPlugin);
plugins.set("auth", brokenPlugin); // overwrites!

// ✅ Module-level encapsulation
declare const _registry: unique symbol;

export interface PluginManager {
  readonly [_registry]: never;
  register(id: string, plugin: Plugin): void;
  get(id: string): Plugin | null;
}
#registry = new Map();
// Internal-only map, controlled access
```

### Exposed algorithm internals

```typescript
// ❌ Callers depend on internal array
class Sorter {
  buffer: number[] = [];
  
  sort(nums: number[]) {
    this.buffer.push(...nums);
    this.buffer.sort();
    return this.buffer;
  }
}

const s = new Sorter();
s.buffer = [1000]; // bypassed the sort

// ✅ Internal state hidden
class Sorter {
  #buffer: number[] = [];
  
  sort(nums: number[]) {
    return nums.slice().sort(); // no mutation, no exposure
  }
}
```

## Summary

| Situation | Use Encapsulation | Use Simpler Alternative |
|---|---|-|
| Invariants must be protected | ✅ `#private` + validation | ❌ Public fields |
| Implementation may change | ✅ Interface + factory | ❌ Export class |
| Object requires validation | ✅ Private constructor | ❌ Public constructor |
| You own all implementations | ✅ Sealed interface | ❌ Open interface |
| IDs need type safety | ✅ Branded types | ❌ Plain strings |
| Simple data transfer | ❌ Over-engineering | ✅ Plain object |
| Hot path performance | ❌ Extra indirection | ✅ Direct access |
| Need extensive mocking | ❌ Hard to observe | ✅ Function params |
