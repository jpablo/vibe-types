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
| **`Object.is`** | Built-in value equality that handles `NaN` and `-0` correctly — prefer over `===` inside equality implementations | MDN |

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

### Pattern D — Reference equality vs. value equality for plain objects

`===` on objects tests identity (same reference in memory), not structural equality. Two objects with identical fields are not `===` equal. This is the most common source of silent bugs when working with plain record types.

```typescript
// Plain objects — reference equality:
const a = { x: 1, y: 2 };
const b = { x: 1, y: 2 };

a === b;    // false — different objects in memory
a === a;    // true  — same reference

// This bites in Set and Map, which also use reference equality:
const points = new Set([a, b]);
points.size;  // 2 — both entered, even though they look identical

const map = new Map([[a, "point A"]]);
map.has(b);   // false — b is a different reference

// The fix: use a typed deep-equals helper for structural comparison.
// For simple flat records, a field-by-field function is idiomatic:
type Point = { x: number; y: number };

function pointEq(a: Point, b: Point): boolean {
  return a.x === b.x && a.y === b.y;
}

pointEq({ x: 1, y: 2 }, { x: 1, y: 2 });  // true

// For nested plain records, a recursive structural equals.
// Limitation: only handles plain objects — non-plain objects (Date, RegExp, Map, Set,
// arrays, class instances, etc.) are rejected so they cannot silently compare as equal
// due to having no enumerable own keys.
function isPlainObject(v: unknown): v is Record<string, unknown> {
  if (v === null || typeof v !== "object") return false;
  const proto = Object.getPrototypeOf(v) as unknown;
  return proto === Object.prototype || proto === null;
}

function deepEq(a: unknown, b: unknown): boolean {
  if (Object.is(a, b)) return true;
  if (!isPlainObject(a) || !isPlainObject(b)) return false;
  const ka = Object.keys(a);
  const kb = Object.keys(b);
  if (ka.length !== kb.length) return false;
  return ka.every((k) => deepEq(a[k], b[k]));
}

deepEq({ x: 1, nested: { z: 3 } }, { x: 1, nested: { z: 3 } });  // true
deepEq({ x: 1, nested: { z: 3 } }, { x: 1, nested: { z: 9 } });  // false
```

> **Collection footgun:** `Set<Point>` and `Map<Point, V>` use reference equality — two structurally identical `Point` objects are treated as distinct keys. If you need value-keyed collections, normalise to a primitive key (e.g. `"${x},${y}"`) or use a library that supports custom equality (`Map`-backed with string keys is the most portable solution in plain TypeScript).

### Pattern E — Float / NaN equality and `Object.is`

JavaScript has two quirks that make `===` wrong inside equality implementations:
- `NaN !== NaN` (so `x === x` is `false` when `x` is `NaN`)
- `-0 === +0` (so storing signed zeros loses the distinction)

`Object.is` fixes both. Use it inside any equality function that may receive floating-point values.

```typescript
// === pitfalls:
NaN === NaN;   // false — despite being the same conceptual value
-0  === +0;    // true  — despite being distinct IEEE 754 values

// Object.is is the correct primitive equality:
Object.is(NaN, NaN);  // true
Object.is(-0,  +0);   // false

// This matters when implementing custom equals for numeric domain types:
type Latitude  = number & { readonly _brand: "Latitude" };
type Longitude = number & { readonly _brand: "Longitude" };

function latEq(a: Latitude, b: Latitude): boolean {
  return Object.is(a, b);  // correct for all IEEE 754 values
}

// Tolerance-based equality for approximate floats:
function nearlyEq(a: number, b: number, epsilon = 1e-9): boolean {
  if (!Number.isFinite(a) || !Number.isFinite(b)) return Object.is(a, b);
  return Math.abs(a - b) <= epsilon;
}

nearlyEq(0.1 + 0.2, 0.3);          // true  — floating-point sum is close enough
nearlyEq(0.1 + 0.2, 0.3, 1e-20);  // false — too tight a tolerance
```

> **Rule of thumb:** use `===` for business-logic comparisons of branded primitives (where NaN is an invalid input you'd reject earlier). Use `Object.is` inside the implementation of generic equals helpers, where the full range of IEEE 754 values may appear.

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| **Branded types + `eq` helper** | Cross-domain identity comparisons are type errors | Does not intercept bare `===`; requires discipline or linting to enforce |
| **Discriminated unions** | Variant-level equality enforced structurally | Requires explicit narrowing before field comparison; more verbose |
| **Field-by-field `equals` method** | Full control over comparison semantics | Must be kept in sync with type changes; no automatic derivation |
| **`deepEq` helper** | Works on any plain record without boilerplate | Slower; loses type specificity; no way to exclude computed/internal fields |
| **`Object.is`** | Correct for NaN and -0; no surprises | Not structural — still reference equality for objects |
| **String-keyed maps** | Value-based keyed collections without a library | Serialisation / deserialisation overhead; key collisions if format is ambiguous |

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

**Field-by-field equals function** (Pattern D) when comparing plain object records — never rely on `===` for structural equality of objects. For deeply nested records use a recursive `deepEq`; for flat records a specific function is clearer and faster.

**`Object.is` inside equality implementations** (Pattern E) for any code that may receive floating-point values, including inside generic helpers. Prefer `Object.is` over `===` as the inner comparison primitive; use a tolerance-based helper (`nearlyEq`) for approximate float comparison.

**Acknowledge the limitation**: TypeScript does not have multiversal equality (cf. Scala's `CanEqual`, Rust's `PartialEq`, Haskell's `Eq`). The patterns above prevent most accidental cross-type comparisons but cannot intercept every use of the `===` operator. Teams should establish a convention of using the typed `equals` helper for domain value comparisons and enforce it via linting if needed.

## When to Use

- **Domain identifiers**: Brand all IDs (`UserId`, `OrderId`, `ProductId`) to prevent accidental cross-domain comparison or assignment
- **Structured domain values**: Use discriminated unions for values with mutually exclusive forms (e.g., `PaymentStatus`, `Measurement`)
- **Custom equality semantics**: Use typed `equals<T>` helpers when you need compile-time enforcement that both operands are the same type
- **Value objects with structure**: Implement field-by-field equality for plain objects instead of relying on reference equality
- **Float comparisons**: Use `Object.is` for exact float equality (handles `NaN` and `-0`); use tolerance-based helpers for approximate comparisons

## When Not to Use

- **Performance-critical tight loops**: Generic typed helpers add function call overhead; inline comparisons when performance matters and types are already safe
- **Unbranded primitives**: Boxing every `string` or `number` as a branded type adds verbosity without benefit for simple scripts or throwaway code
- **External API integration**: Don't brand types returned from uncontrolled external sources; use adapters at the boundary instead
- **Deep equality on complex objects**: Recursive `deepEq` is slow and error-prone on deeply nested or circular structures; prefer dedicated libraries for that

## Antipatterns When Using This Technique

### Antipattern 1 — Comparing branded types with bare `===`

```typescript
type UserId = Branded<string, "UserId">;
type OrderId = Branded<string, "OrderId">;

declare const uid: UserId;
declare const oid: OrderId;

// ❌ Compiles but semantically meaningless
if (uid === oid) { /* ... */ }

// ✅ Type-safe comparison
if (equals(uid, oid)) { /* compile error */ }
```

### Antipattern 2 — Using `any` to bypass branded types

```typescript
declare const id: any;

// ❌ Branding protection is lost
function findUser(userId: UserId) { /* ... */ }
findUser(id as any);  // bypasses type checking
```

### Antipattern 3 — Forgetting to narrow before comparing discriminated unions

```typescript
type Measurement =
  | { kind: "Temperature"; celsius: number }
  | { kind: "Pressure"; pascal: number };

function same(a: Measurement, b: Measurement): boolean {
  // ❌ Accessing fields without narrowing
  return a.celsius === b.celsius; // errors: celsius may not exist
}

// ✅ Proper narrowing
if (a.kind !== b.kind) return false;
if (a.kind === "Temperature") {
  return a.celsius === (b as typeof a).celsius;
}
```

### Antipattern 4 — Reference equality for value types

```typescript
type Point = { x: number; y: number };

const a = { x: 1, y: 2 };
const b = { x: 1, y: 2 };

// ❌ Reference equality — false even though values match
a === b;  // false

// ✅ Value equality
function pointEq(a: Point, b: Point): boolean {
  return a.x === b.x && a.y === b.y;
}
```

### Antipattern 5 — `===` for NaN comparisons

```typescript
// ❌ NaN never equals itself with ===
const val: number = NaN;
val === NaN;  // false

// ✅ Object.is handles NaN correctly
Object.is(val, NaN);  // true
```

## Antipatterns Solved by This Technique

### Problem A — Cross-type ID comparison with unbranded strings

```typescript
// ❌ Without branding — compiles but is semantically wrong
type UserId = string;
type OrderId = string;

function findUser(id: UserId) { /* ... */ }
const orderId = "ORD123";
findUser(orderId);  // compiles — orderId incorrectly accepted as UserId

// ✅ With branding — type error at compile time
type UserId = Branded<string, "UserId">;
type OrderId = Branded<string, "OrderId">;

const userId = "USR123" as UserId;
const orderId = "ORD123" as OrderId;
findUser(orderId);  // error: OrderId not assignable to UserId
```

### Problem B — Comparing different variants of a discriminated union

```typescript
// ❌ Without discriminated union — manual equality is error-prone
interface Temperature { celsius: number }
interface Pressure { pascal: number }

function equals(a: Temperature | Pressure, b: Temperature | Pressure): boolean {
  // runtime check required, no compile-time help
  if (typeof (a as any).celsius === 'number' && typeof (b as any).celsius === 'number') {
    return (a as Temperature).celsius === (b as Temperature).celsius;
  }
  // ... messy
}

// ✅ With discriminated union — type system enforces correct comparison
type Measurement =
  | { kind: "Temperature"; celsius: number }
  | { kind: "Pressure"; pascal: number };

function tempEq(
  a: Extract<Measurement, { kind: "Temperature" }>,
  b: Extract<Measurement, { kind: "Temperature" }>,
): boolean {
  return a.celsius === b.celsius;
}

const t: Extract<Measurement, { kind: "Temperature" }> = { kind: "Temperature", celsius: 25 };
const p: Extract<Measurement, { kind: "Pressure" }> = { kind: "Pressure", pascal: 101325 };
tempEq(t, p);  // error: Pressure not assignable to Temperature
```

### Problem C — Mixing reference and value equality in collections

```typescript
// ❌ Set uses reference equality — duplicates slip through
type User = { id: string; name: string };

const users = new Set<User>();
users.add({ id: "u1", name: "Alice" });
users.has({ id: "u1", name: "Alice" });  // false — different reference

// ✅ Use branded ID as key, or implement custom equality
type UserId = Branded<string, "UserId">;
const userMap = new Map<UserId, { name: string }>();
userMap.set("u1" as UserId, { name: "Alice" });
userMap.has("u1" as UserId);  // true — same ID
```

### Problem D — Inconsistent equality across codebase

```typescript
// ❌ Inconsistent approaches scattered through code
function sameUser1(a: User, b: User) { return a.id === b.id; }
function sameUser2(a: User, b: User) { return a === b; }  // reference!
function sameUser3(a: User, b: User) { return JSON.stringify(a) === JSON.stringify(b); }

// ✅ Centralized typed equality
function equals<T>(a: T, b: T): boolean {
  return Object.is(a, b);  // or delegate to a.equals(b) for value objects
}

class User {
  constructor(readonly id: UserId, readonly name: string) {}
  equals(other: User): boolean {
    return equals(this.id, other.id);
  }
}

equals(new User("u1" as UserId, "Alice"), new User("u1" as UserId, "Bob"));  // true
```
