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
| **Builder pattern** | Incremental, validated construction of complex objects with required/optional fields | [-> UC09](UC09-builder-config.md) |
| **Zod schemas** | Co-locate static type inference with runtime validation; the TypeScript equivalent of Pydantic | [-> T26](../catalog/T26-refinement-types.md) |

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

### Pattern D — Builder pattern for complex construction

When construction involves many fields, optional configuration, or required-field validation, a builder accumulates state incrementally and validates at `build()` time.

```typescript
type ServerConfig = {
  readonly host: string;
  readonly port: number;
  readonly retries: number;
  readonly timeoutMs: number;
};

class ServerConfigBuilder {
  #host?: string;
  #port?: number;
  #retries = 3;
  #timeoutMs = 5_000;

  host(h: string): this      { this.#host = h;       return this; }
  port(p: number): this      { this.#port = p;       return this; }
  retries(r: number): this   { this.#retries = r;    return this; }
  timeout(ms: number): this  { this.#timeoutMs = ms; return this; }

  build(): ServerConfig {
    if (!this.#host)            throw new Error("host is required");
    if (this.#port === undefined) throw new Error("port is required");
    return {
      host:      this.#host,
      port:      this.#port,
      retries:   this.#retries,
      timeoutMs: this.#timeoutMs,
    };
  }
}

const config = new ServerConfigBuilder()
  .host("api.example.com")
  .port(443)
  .retries(5)
  .build();
```

For truly compile-time-enforced required fields, combine with phantom types (see [UC09](UC09-builder-config.md)). The pattern above moves the check to runtime but keeps the construction API clean and the final type fully typed.

### Pattern E — Runtime validation with Zod

Static types alone cannot validate values that arrive at runtime (API responses, form inputs, environment variables). Zod schemas derive a static type from a single declaration and validate at the boundary — the TypeScript equivalent of Python's `Annotated + Pydantic`.

```typescript
import { z } from "zod";

const ProductSchema = z.object({
  name:  z.string().min(1),
  price: z.number().positive(),
  sku:   z.string().regex(/^[A-Z]{3}-\d{4}$/),
});

// Static type is inferred from the schema — no duplication:
type Product = z.infer<typeof ProductSchema>;

// Throws ZodError on invalid input:
const p = ProductSchema.parse({ name: "Widget", price: 9.99, sku: "WDG-0001" });

// Safe parse — returns a discriminated union instead of throwing:
const result = ProductSchema.safeParse(unknownExternalData);
if (result.success) {
  result.data.name;   // typed as string
} else {
  result.error.issues; // ZodIssue[]
}
```

Zod integrates with branded types too — `.brand<"ProductId">()` produces a branded type while validating the raw value, letting smart constructors live inside the schema declaration:

```typescript
const ProductIdSchema = z.string().uuid().brand<"ProductId">();
type ProductId = z.infer<typeof ProductIdSchema>; // string & { __brand: "ProductId" }
```

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Order lifecycle | Single object with all optional fields (`trackingNumber?: string`); `undefined` checks scattered throughout | Discriminated union — each variant contains exactly its fields; narrowing replaces runtime checks |
| Domain primitives | Raw `string` for userId, email, productId; mix-ups found only at runtime or in tests | Branded types; swapping `UserId` for `Email` is a compile error caught in the editor |
| Data shapes | Plain object literals with no enforced structure; shape validated only in tests or at API boundaries | `type Customer = { … }` enforces the shape at every assignment and function call |
| Money arithmetic | Raw `number`; easy to accidentally operate in dollars vs cents or mix currency fields | `Money` branded type; arithmetic helpers keep the brand; mixed operations are type errors |

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **Discriminated union** | Compiler enforces exhaustiveness; each variant carries only its fields | Adding a variant requires updating every exhaustive switch |
| **Branded primitives** | Zero runtime cost; prevents accidental interchange of same-representation values | Cast (`as`) needed in smart constructors; no methods on the value itself |
| **Record types** | Full static shape checking; composable via intersection (`&`) | Structural typing — a compatible shape can satisfy the type unintentionally |
| **Builder** | Incremental construction; clean fluent API; easy defaults for optional fields | Extra boilerplate; required-field enforcement is runtime unless phantom types are added |
| **Zod schemas** | Single source of truth for static type and runtime validation; excellent for API boundaries | Runtime dependency; Zod type inference can become verbose for deeply nested schemas |

## When to Use Which Feature

**Discriminated union** (Pattern A) is the right tool when an entity's data changes meaningfully as it moves through a lifecycle — use it when different stages have different required fields. The `status` literal discriminant makes narrowing automatic.

**Branded primitives** (Pattern B) are essential when multiple primitive-typed IDs, codes, or amounts coexist in the same domain. The branding cost is a single smart constructor per type; the benefit is that cross-field confusion becomes a compile error.

**Record types with readonly** (Pattern C) should be used for all aggregate domain objects. Combine them with branded primitives for fields and discriminated unions for lifecycle so that the type structure mirrors the domain rules exactly.

**Builder pattern** (Pattern D) fits objects with many optional fields, required fields that depend on configuration decisions, or any case where direct object literals would be awkward. For required-field guarantees at compile time, see the phantom-type builder in [UC09](UC09-builder-config.md).

**Zod schemas** (Pattern E) are the right choice whenever values cross a system boundary — HTTP request bodies, environment variables, localStorage, file parsing. They also work well as smart constructors for branded primitives when the validation logic is non-trivial.

## When to Use It

Use domain modeling when you have business rules that should be enforced by the type system:

- **Entity lifecycles**: A document has different valid fields in `draft` vs `published` state
- **Unique domain values**: A `Temperature` shouldn't be accidentally compared to a `Pressure`, even if both are `number`
- **Invariant enforcement**: A `Rectangle` with width and height should never have negative dimensions

```typescript
// ✅ Good: shape reflects domain rules
type Transaction =
  | { kind: "outgoing"; amount: Money; recipient: AccountId }
  | { kind: "incoming"; amount: Money; sender: AccountId; verified: true }
  | { kind: "pending";  amount: Money; expiresAt: Date };
// outgoing can't have `sender`, pending always expires
```

Use it when the cost of confused types exceeds the boilerplate of brand wrappers. In a financial domain, paying `$100` to the wrong account because `userId` was swapped with `accountId` is catastrophic — branding prevents this.

## When Not to Use It

Skip domain modeling when:

- **Pass-through data**: You receive JSON and immediately forward it without interpreting its meaning
- **Simple configurations**: A flag like `{ darkMode: boolean }` has no domain invariants to enforce
- **Protoypes/exploratory code**: Rapid iteration with mutable, untyped shapes
- **Interfacing external SDKs**: A library's opaque `Response` type shouldn't be re-modeled

```typescript
// ❌ Don't brand this — just a configuration bag
interface AppConfig {
  apiKey: string;
  timeoutMs: number;
  debug: boolean;
}

// ✅ But brand this — it's a domain concept
type APIKey = Branded<string, "APIKey">;  // must never be logged raw, must be validated
```

If you find yourself writing a branded type but never checking values that violate the brand, you're solving a problem you don't have.

## Antipatterns When Using It

### Antipattern 1 — Over-branding

Branding every string field destroys readability without value.

```typescript
// ❌ Over-branding
type FirstName = Branded<string, "FirstName">;
type LastName  = Branded<string, "LastName">;
type Address   = Branded<string, "Address">;
type Phone     = Branded<string, "Phone">;

function greet(u: { first: FirstName; last: LastName }) {
  return `Hello ${u.last}, ${u.first}`;  // swapped — no semantic error!
}

// ✅ Brand only where confusion causes bugs
type UserId   = Branded<string, "UserId">;
type TeamId   = Branded<string, "TeamId">;  // both are IDs, easy to confuse
type UserName = string;  // no confusion risk
```

### Antipattern 2 — Empty discriminated unions

A union where every variant has identical fields defeats the purpose.

```typescript
// ❌ Useless variants
type Status = "idle" | "loading" | "ready" | "error";
type Widget = { status: Status; value: string };
// same shape — no narrowing benefit

// ✅ Discriminant drives shape
type Widget =
  | { status: "idle";   }
  | { status: "loading"; progress: number }
  | { status: "ready";   value: string }
  | { status: "error";   message: string };
```

### Antipattern 3 — Mutable domain objects

Domain shapes should be immutable once constructed.

```typescript
// ❌ Mutable domain object
type Order = {
  id: OrderId;
  amount: Money;
  status: OrderStatus;
};

function processOrder(o: Order) {
  o.amount = makeMoney(0);  // silently corrupted domain state
  o.status = "Cancelled";
}

// ✅ Immutable with transformation
type Order = {
  readonly id: OrderId;
  readonly amount: Money;
  readonly status: OrderStatus;
};

function cancelOrder(o: Order): Order {
  return { ...o, status: "Cancelled" };  // new instance
}
```

### Antipattern 4 — Runtime validation gaps

Using Zod at the boundary but accepting raw types internally.

```typescript
// ❌ Validation gap
const req = OrderSchema.parse(request.body);  // validated
function updateAmount(o: Order, amount: number) {  // raw number accepted!
  return { ...o, amount };  // domain invariant broken
}

// ✅ Consistent branding throughout
function updateAmount(o: Order, amount: Money) {  // branded
  return { ...o, amount };
}
```

## Antipatterns with Other Techniques (Where Domain Modeling Helps)

### Antipattern 1 — `any` for unknown shapes

```typescript
// ❌ Without domain modeling
function processItem(item: any) {
  return item.price * item.quantity;  // runtime errors possible
}

// ✅ With domain modeling
type Item = { price: Money; quantity: number };
function processItem(item: Item) {
  return item.price * item.quantity;  // type-checked
}
```

### Antipattern 2 — Partial types for optionality

```typescript
// ❌ Optional fields lead to runtime undefined checks
type User = {
  id: string;
  name?: string;
  email?: string;
};

function sendInvite(u: User) {
  if (!u.email) return;  // scattered runtime guards
  sendEmail(u.email, ...);
}

// ✅ Discriminated union replaces optional runtime checks
type User =
  | { id: string; status: "anonymous" }
  | { id: string; status: "registered"; name: string; email: string };

function sendInvite(u: User) {
  if (u.status === "registered") {
    sendEmail(u.email, ...);  // email guaranteed to exist
  }
}
```

### Antipattern 3 — Magic strings for states

```typescript
// ❌ Magic strings
type OrderState = string;
function isShipped(o: { state: OrderState }) {
  return o.state === "shipped" || o.state === "SHIPPED" || o.state === "shipped!";
}

// ✅ Literal types
type OrderState = "pending" | "shipped" | "cancelled";
function isShipped(o: { state: OrderState }) {
  return o.state === "shipped";  // exhaustive and type-safe
}
```

### Antipattern 4 — Validation in business logic

```typescript
// ❌ Validation scattered in business logic
function calculateTax(order: { items: Array<{ price: number }> }) {
  return order.items.reduce((sum, item) => {
    if (item.price < 0) throw new Error("negative price");  // validation leak
    return sum + item.price * 0.1;
  }, 0);
}

// ✅ Domain types enforce invariants at construction
type Price = Branded<number, "Price">;  // smart constructor rejects negatives
type Order = { items: Array<{ price: Price }> };

function calculateTax(order: Order) {
  return order.items.reduce((sum, item) => sum + item.price * 0.1, 0);  // no guards needed
}
```

## Source Anchors

- [TypeScript Handbook — Discriminated Unions](https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes-func.html#discriminated-unions)
- [TypeScript Handbook — Object Types](https://www.typescriptlang.org/docs/handbook/2/objects.html)
- [TypeScript Deep Dive — Nominal Typing](https://basarat.gitbook.io/typescript/main-1/nominaltyping)
- [Zod documentation](https://zod.dev)
