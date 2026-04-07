# Domain Modeling

## The Constraint

Model a domain so that invalid combinations of values are unrepresentable at the type level. The shape of the data reflects the business rules: an order that has shipped always has a tracking number; a monetary amount is never a raw `number` that could be confused with a user ID.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Discriminated unions** | One variant per order lifecycle stage, each carrying exactly the right fields | [-> T01](../catalog/T01-algebraic-data-types.md) |
| **Branded primitives** | Distinguish `UserId`, `Email`, and `Money` even though all are `string` or `number` at runtime | [-> T03](../catalog/T03-newtypes-opaque.md) |
| **Record types** | Group related fields into named, typed shapes | [-> T31](../catalog/T31-record-types.md) |
| **Literal discriminants** | Type-safe `kind` or `status` fields that drive narrowing | [-> T52](../catalog/T52-literal-types.md) |
| **Type aliases** | Give meaningful names to complex composed types without introducing new runtime values | [-> T23](../catalog/T23-type-aliases.md) |

## Patterns

### Pattern A — Order status lifecycle as discriminated union

Each stage in the order lifecycle carries exactly the data it needs and nothing more. A `Shipped` order always has a `trackingNumber`; a `Pending` order never does.

```typescript
type OrderId = string & { readonly __brand: "OrderId" };

type Order =
  | { status: "Pending";   id: OrderId; createdAt: Date }
  | { status: "Confirmed"; id: OrderId; confirmedAt: Date; totalAmount: Money }
  | { status: "Shipped";   id: OrderId; shippedAt: Date; trackingNumber: string }
  | { status: "Delivered"; id: OrderId; deliveredAt: Date }
  | { status: "Cancelled"; id: OrderId; cancelledAt: Date; reason: string };

function getTrackingInfo(order: Order): string {
  if (order.status === "Shipped") {
    return order.trackingNumber; // OK — narrowed to Shipped variant
  }
  return "No tracking info available";
}

declare const o: Order;
o.trackingNumber; // error: property does not exist on type 'Order'
```

### Pattern B — Branded domain primitives

`UserId`, `Email`, and `Money` are all strings or numbers at runtime, but the type system treats them as distinct. Passing a `UserId` where an `Email` is expected is a compile error.

```typescript
declare const __brand: unique symbol;
type Brand<B> = { readonly [__brand]: B };
type Branded<T, B> = T & Brand<B>;

type UserId = Branded<string, "UserId">;
type Email  = Branded<string, "Email">;
type Money  = Branded<number, "Money">;  // stored as cents

// Smart constructors — the only place `as Brand` casts appear
function makeUserId(id: string): UserId   { return id as UserId; }
function makeEmail(raw: string): Email    {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(raw)) throw new Error("Invalid email");
  return raw.toLowerCase() as Email;
}
function makeMoney(cents: number): Money  {
  if (!Number.isInteger(cents) || cents < 0) throw new RangeError("Invalid amount");
  return cents as Money;
}

function chargeUser(userId: UserId, amount: Money): void { /* … */ }

const uid   = makeUserId("usr_42");
const email = makeEmail("alice@example.com");
const price = makeMoney(1999); // $19.99

chargeUser(uid, price);  // OK
chargeUser(email, price); // error: Email is not assignable to UserId
chargeUser(uid, 1999);    // error: number is not assignable to Money
```

### Pattern C — Combining branded primitives into a rich domain type

A `Customer` record uses branded primitives throughout, so there is no ambiguity about which string field is which.

```typescript
type CustomerId = Branded<string, "CustomerId">;

type Address = {
  readonly street: string;
  readonly city: string;
  readonly country: string;
  readonly postalCode: string;
};

type Customer = {
  readonly id: CustomerId;
  readonly email: Email;
  readonly billingAddress: Address;
  readonly createdAt: Date;
};

type OrderLine = {
  readonly productId: Branded<string, "ProductId">;
  readonly quantity: number;
  readonly unitPrice: Money;
};

type ConfirmedOrder = {
  readonly id: OrderId;
  readonly customer: Customer;
  readonly lines: readonly OrderLine[];
  readonly total: Money;
  readonly confirmedAt: Date;
};

// totalAmount must be Money, not a plain number:
function applyDiscount(total: Money, discountCents: Money): Money {
  return Math.max(0, total - discountCents) as Money;
}
```

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Order lifecycle | Single object with all optional fields (`trackingNumber?: string`); `undefined` checks scattered throughout | Discriminated union — each variant contains exactly its fields; narrowing replaces runtime checks |
| Domain primitives | Raw `string` for userId, email, productId; mix-ups found only at runtime or in tests | Branded types; swapping `UserId` for `Email` is a compile error caught in the editor |
| Data shapes | Plain object literals with no enforced structure; shape validated only in tests or at API boundaries | `type Customer = { … }` enforces the shape at every assignment and function call |
| Money arithmetic | Raw `number`; easy to accidentally operate in dollars vs cents or mix currency fields | `Money` branded type; arithmetic helpers keep the brand; mixed operations are type errors |

## When to Use Which Feature

**Discriminated union** (Pattern A) is the right tool when an entity's data changes meaningfully as it moves through a lifecycle — use it when different stages have different required fields. The `status` literal discriminant makes narrowing automatic.

**Branded primitives** (Pattern B) are essential when multiple primitive-typed IDs, codes, or amounts coexist in the same domain. The branding cost is a single smart constructor per type; the benefit is that cross-field confusion becomes a compile error.

**Record types with readonly** (Pattern C) should be used for all aggregate domain objects. Combine them with branded primitives for fields and discriminated unions for lifecycle so that the type structure mirrors the domain rules exactly.
