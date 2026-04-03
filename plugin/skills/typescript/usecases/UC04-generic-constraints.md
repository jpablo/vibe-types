# Generic Constraints

## The Constraint

Accept only types that satisfy a required shape or capability. The compiler rejects type arguments — and call-site values — that do not meet the constraint, so a generic function never receives a value it cannot safely use.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Generics and bounds** | `<T extends Shape>` restricts which types may be substituted for `T` | [-> T04](../catalog/T04-generics-bounds.md) |
| **Interfaces** | Name a structural contract that a type parameter must satisfy | [-> T05](../catalog/T05-type-classes.md) |
| **Structural typing** | Any type with the required fields satisfies a constraint without explicit `implements` | [-> T07](../catalog/T07-structural-typing.md) |
| **Conditional types** | Derive or validate constraints from other type-level computations | [-> T41](../catalog/T41-match-types.md) |

## Patterns

### Pattern A — Requiring a specific field shape

The simplest constraint: `T extends { id: string }` ensures the generic function can always access `value.id` regardless of what other fields `T` carries.

```typescript
function findById<T extends { id: string }>(
  items: readonly T[],
  id: string
): T | undefined {
  return items.find((item) => item.id === id);
}

type User    = { id: string; name: string; email: string };
type Product = { id: string; sku: string; price: number };
type Metric  = { timestamp: Date; value: number }; // no id field

const users: User[] = [{ id: "u1", name: "Alice", email: "alice@example.com" }];
const found = findById(users, "u1"); // OK — User extends { id: string }; found: User | undefined

const metrics: Metric[] = [{ timestamp: new Date(), value: 42 }];
findById(metrics, "x"); // error: Metric does not satisfy { id: string }
```

### Pattern B — Interface bound for a named capability

Define an interface that describes a capability, then constrain `T` to that interface. Because TypeScript uses structural typing, any type with the required methods satisfies the constraint — no explicit `implements` keyword is needed.

```typescript
interface Comparable<T> {
  compareTo(other: T): number; // negative = less, 0 = equal, positive = greater
}

function max<T extends Comparable<T>>(a: T, b: T): T {
  return a.compareTo(b) >= 0 ? a : b;
}

function sort<T extends Comparable<T>>(items: T[]): T[] {
  return [...items].sort((a, b) => a.compareTo(b));
}

class Temperature implements Comparable<Temperature> {
  constructor(readonly celsius: number) {}
  compareTo(other: Temperature): number {
    return this.celsius - other.celsius;
  }
}

class Version implements Comparable<Version> {
  constructor(readonly major: number, readonly minor: number) {}
  compareTo(other: Version): number {
    return this.major !== other.major
      ? this.major - other.major
      : this.minor - other.minor;
  }
}

const hottest = max(new Temperature(36.6), new Temperature(38.1)); // Temperature
const latest  = max(new Version(2, 0), new Version(1, 9));         // Version

// A type without compareTo cannot be passed:
max("a", "b"); // error: string does not satisfy Comparable<string>
```

### Pattern C — Constraining with keyof and Record

Use `keyof` and `Record` constraints to build type-safe property accessors and mappers that operate only on object types.

```typescript
// Pick one or more known keys from an object:
function pick<T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: readonly K[]
): Pick<T, K> {
  return Object.fromEntries(
    keys.map((k) => [k, obj[k]])
  ) as Pick<T, K>;
}

type Config = { host: string; port: number; timeout: number; retries: number };
const cfg: Config = { host: "localhost", port: 8080, timeout: 5000, retries: 3 };

const conn = pick(cfg, ["host", "port"] as const); // { host: string; port: number }
const bad  = pick(cfg, ["host", "missing"]);        // error: "missing" is not a key of Config

// Constrain to types that are serialisable to JSON:
type JsonPrimitive = string | number | boolean | null;
type JsonValue     = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };

function toJson<T extends JsonValue>(value: T): string {
  return JSON.stringify(value);
}

toJson({ host: "localhost", port: 8080 }); // OK
toJson(new Date());                        // error: Date does not satisfy JsonValue
```

### Pattern D — Conditional type constraint

Use a conditional type to derive a stricter constraint from a broader one — for example, accepting only those members of a union that satisfy a shape.

```typescript
// Extract only the keys of T whose values extend U:
type KeysOfType<T, U> = {
  [K in keyof T]: T[K] extends U ? K : never;
}[keyof T];

type Form = {
  username: string;
  age: number;
  email: string;
  active: boolean;
  score: number;
};

type StringKeys  = KeysOfType<Form, string>;  // "username" | "email"
type NumberKeys  = KeysOfType<Form, number>;  // "age" | "score"

// Generic function that only accepts keys mapping to a given type:
function getStringField<T, K extends KeysOfType<T, string>>(
  obj: T,
  key: K
): string {
  return String(obj[key as keyof T]);
}

declare const form: Form;
getStringField(form, "username"); // OK
getStringField(form, "age");      // error: "age" does not extend KeysOfType<Form, string>
```

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Required fields | `if (!item.id) throw new Error('missing id')` — runtime guard repeated everywhere | `<T extends { id: string }>` — compile-time constraint; no runtime guard needed |
| Named capability | Duck-typing comment: `// obj must have a compareTo method`; forgotten silently | `T extends Comparable<T>` — missing method is a compile error at the call site |
| Property access | `obj[key]` — any key, any value, no type information | `K extends keyof T` — only valid keys; return type is `T[K]` |
| Union filtering | Manual runtime `typeof` or `instanceof` checks | Conditional type `KeysOfType<T, U>` — computed at compile time with no runtime cost |

## When to Use Which Feature

**Structural field constraint** (`T extends { id: string }`, Pattern A) is the simplest and most common form. Use it whenever a generic function needs access to one or a few named properties. Prefer this over a named interface when the constraint is local to one function.

**Interface bound** (Pattern B) is better when the same constraint is shared across many functions or when the capability has a meaningful name in the domain (`Comparable`, `Serialisable`, `Pageable`). Because TypeScript is structural, existing types satisfy the bound without any change.

**keyof / Record constraint** (Pattern C) is the right tool for property-manipulation utilities — pickers, omitters, mappers, and serialisers. Pairing it with `as const` at call sites gives the narrowest possible return type.

**Conditional type constraint** (Pattern D) is for advanced cases where the constraint itself must be computed from another type. Use it in library code and utility types, not in everyday application code where simpler constraints suffice.
