# Equality and Cross-Type Comparison

## The Constraint

Semantically meaningless comparisons — comparing a `UserId` with an `OrderId`, or comparing two structurally identical but conceptually distinct types — should be prevented at compile time. TypeScript's structural type system does not have a built-in multiversal equality mechanism, so the best approximation is deliberate type design.

> **Limitation:** TypeScript has no equivalent of Scala's `CanEqual` / multiversal equality or Haskell's `Eq` type class. The compiler does not reject `userId === orderId` if both are `string`. The patterns below are the closest practical approximations using branded types and discriminated unions.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Branded types** | Two branded strings are distinct types; cross-brand assignment is a type error even though both carry the same primitive | [-> T03](../catalog/T03-newtypes-opaque.md) |
| **Structural typing** | Two types with the same shape are structurally compatible — this is the source of accidental cross-type equality | [-> T07](../catalog/T07-structural-typing.md) |
| **Discriminated unions** | The discriminant field ensures comparisons only happen within the same variant | [-> T01](../catalog/T01-algebraic-data-types.md) |

## Patterns

### Pattern A — Branded types to prevent cross-domain comparison

Without branding, `UserId` and `OrderId` are both `string`. The type checker does not prevent passing one where the other is expected. Branding adds a nominal layer: a `UserId` is a different type from an `OrderId`, even though both are strings at runtime.

```typescript
declare const __brand: unique symbol;
type Brand<B>      = { readonly [__brand]: B };
type Branded<T, B> = T & Brand<B>;

type UserId  = Branded<string, "UserId">;
type OrderId = Branded<string, "OrderId">;
type ItemId  = Branded<string, "ItemId">;

// Smart constructors — the only legitimate way to create these types:
function toUserId(raw: string):  UserId  { return raw as UserId; }
function toOrderId(raw: string): OrderId { return raw as OrderId; }

declare const userId:  UserId;
declare const orderId: OrderId;

// Function that expects UserId must not accept OrderId:
function findUser(id: UserId): { name: string } | null {
  return null;
}

findUser(userId);   // OK
findUser(orderId);  // error: Argument of type 'OrderId' is not assignable to parameter of type 'UserId'

// Assignment is also blocked:
const id: UserId = orderId; // error: OrderId is not assignable to UserId

// Direct equality comparison: TypeScript does NOT block this at compile time.
// This is the fundamental limitation — the operator === accepts any two values.
// Mitigation: use a typed equals helper that constrains both arguments:
function eq<T>(a: T, b: T): boolean {
  return a === b;
}

eq(userId, userId);  // OK
eq(userId, orderId); // error: Argument of type 'OrderId' is not assignable to parameter of type 'UserId'
                     // (because T is inferred as UserId from the first argument)

// Note: plain === still compiles without the helper:
userId === orderId as unknown as UserId; // compiles — TypeScript does not intercept ===
// The typed `eq` function is the practical mitigation.
```

### Pattern B — Discriminated union to scope comparisons to the same variant

A discriminated union ensures that comparisons between records of different variants are structurally impossible — the variants have different shapes. Code that compares two union values must narrow both to the same variant before accessing shared fields.

```typescript
type Measurement =
  | { kind: "Temperature"; celsius: number }
  | { kind: "Pressure";    pascal: number }
  | { kind: "Humidity";    percent: number };

// Comparing two measurements of the same kind:
function sameMeasurement(a: Measurement, b: Measurement): boolean {
  if (a.kind !== b.kind) return false; // different variants — not equal
  switch (a.kind) {
    case "Temperature": {
      // b is narrowed to Temperature here too:
      const bTemp = b as Extract<typeof b, { kind: "Temperature" }>;
      return a.celsius === bTemp.celsius;
    }
    case "Pressure": {
      const bPress = b as Extract<typeof b, { kind: "Pressure" }>;
      return a.pascal === bPress.pascal;
    }
    case "Humidity": {
      const bHumid = b as Extract<typeof b, { kind: "Humidity" }>;
      return a.percent === bHumid.percent;
    }
  }
}

// A more type-safe approach: a generic equals for a specific variant:
function temperatureEq(
  a: Extract<Measurement, { kind: "Temperature" }>,
  b: Extract<Measurement, { kind: "Temperature" }>,
): boolean {
  return a.celsius === b.celsius;
}

declare const t1: Extract<Measurement, { kind: "Temperature" }>;
declare const p1: Extract<Measurement, { kind: "Pressure" }>;

temperatureEq(t1, t1); // OK
temperatureEq(t1, p1); // error: Pressure is not assignable to Temperature variant

// Branded discriminant for extra safety — prevents literal spoofing:
declare const __tempBrand: unique symbol;
type TemperatureId = string & { readonly [__tempBrand]: "Temperature" };
// (combine branding with discriminated unions for maximal safety)
```

### Pattern C — Typed equality helper as a CanEqual approximation

TypeScript has no `CanEqual` mechanism. The closest approximation is a generic `equals` function that requires both arguments to be the same type. Callers cannot pass two different branded types without a type error.

```typescript
// Generic equals — T is inferred from the first argument.
// If the second argument has a different type, it is a type error:
function equals<T>(a: T, b: T): boolean {
  // Works for primitives; for objects, delegates to a custom equality method if present:
  if (
    a !== null &&
    typeof a === "object" &&
    "equals" in a &&
    typeof (a as { equals: unknown }).equals === "function"
  ) {
    return (a as { equals(other: T): boolean }).equals(b);
  }
  return Object.is(a, b);
}

// Domain types:
type ProductId = Branded<string, "ProductId">;
type CategoryId = Branded<string, "CategoryId">;

declare const pid:  ProductId;
declare const cid:  CategoryId;
declare const pid2: ProductId;

equals(pid,  pid2); // OK — both ProductId
equals(pid,  cid);  // error: CategoryId is not assignable to ProductId
                    // (T inferred as ProductId from first arg)

// Value objects with structural equality:
class Money {
  constructor(
    readonly amount: number,
    readonly currency: string,
  ) {}

  equals(other: Money): boolean {
    return this.amount === other.amount && this.currency === other.currency;
  }
}

const usd10 = new Money(10, "USD");
const eur10 = new Money(10, "EUR");

equals(usd10, eur10);   // OK at compile time — both Money; false at runtime (different currency)
equals(usd10, "10 USD"); // error: string is not assignable to Money
```

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Cross-type ID comparison | `userId === orderId` — both strings, compiles and runs; produces incorrect results silently | Branded types + typed `eq` helper — cross-brand arguments are a type error at the call site |
| Variant equality | Manual checks: `a.kind === b.kind && a.value === b.value` — no enforcement | Discriminated union narrowing — accessing variant fields before narrowing is a compile error |
| Generic equality | Any two values comparable with `===`; wrong comparison silently returns `false` | Generic `equals<T>` — both arguments must be the same type; heterogeneous comparison is a type error |
| Multiversal equality | Not applicable | Not natively supported — branded types + typed helpers are the practical approximation |

## When to Use Which Feature

**Branded types + typed `equals` helper** (Patterns A, C) are the primary tool. Brand all domain identifiers; use a typed `equals` function rather than bare `===` for comparisons that should be type-checked. Bare `===` between two branded values will not be caught by the compiler — the typed helper is essential.

**Discriminated unions** (Pattern B) are best when comparing structured values that come in several mutually exclusive variants. Narrowing to the same variant before comparison is enforced by the type system.

**Acknowledge the limitation**: TypeScript does not have multiversal equality. The patterns above prevent most accidental cross-type comparisons but cannot intercept every use of the `===` operator. Teams should establish a convention of using the typed `equals` helper for domain value comparisons and enforce it via linting if needed.
