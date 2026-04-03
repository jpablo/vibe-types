# Encapsulation

## The Constraint

Internal representations must be hidden; only a controlled public surface is exposed. Code outside the module cannot read private fields, construct internal objects directly, or bypass invariants established at creation time.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Private fields and `private`** | `#field` enforces runtime privacy; `private` enforces compile-time-only privacy | [-> T21](../catalog/T21-encapsulation.md) |
| **Readonly** | Prevent mutation of exposed properties after construction | [-> T32](../catalog/T32-immutability-markers.md) |
| **Branded / opaque types** | Opaque handles — callers receive a typed token but cannot construct or inspect it without going through the module | [-> T03](../catalog/T03-newtypes-opaque.md) |
| **Interface as public API** | Export only an interface; keep the class an implementation detail | [-> T05](../catalog/T05-type-classes.md) |

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
acc.#balance;      // error: Property '#balance' is not accessible outside class 'BankAccount'

// Even with 'any', the runtime blocks access:
(acc as any).#balance; // SyntaxError at runtime — private fields are not enumerable
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

### Pattern C — Branded opaque handle

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

**Branded opaque handles** (Pattern C) apply when callers need to hold a reference to an entity — pass it around, store it, send it back — but must not construct, inspect, or forge that reference. The brand makes the type system enforce the module boundary even for primitive-typed identifiers.
