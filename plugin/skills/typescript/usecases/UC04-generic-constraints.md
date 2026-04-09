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

### Pattern B — Interface bound for a named capability (F-bounded)

Define an interface that describes a capability, then constrain `T` to that interface. Because TypeScript uses structural typing, any type with the required methods satisfies the constraint — no explicit `implements` keyword is needed.

`Comparable<T>` is an example of an **F-bounded** (self-referential) constraint: `T extends Comparable<T>`. The bound refers to `T` itself, ensuring that `compareTo` always receives the same concrete type rather than the raw base interface. This prevents mixing `Temperature` with `Version` in a single `max` call even though both satisfy `Comparable`.

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

// Cross-type calls are rejected even though both satisfy Comparable:
max(new Temperature(36.6), new Version(2, 0)); // error: Version is not assignable to Temperature
```

### Pattern C — Multiple constraints via intersection

Combine unrelated capabilities into a single bound using `&`. TypeScript has no dedicated multi-constraint syntax (unlike Scala's `[A: Ordering : Eq]`), but intersection types serve the same role.

```typescript
interface Serializable {
  serialize(): string;
}

interface Validatable {
  isValid(): boolean;
}

// T must satisfy both capabilities simultaneously:
function saveIfValid<T extends Serializable & Validatable>(item: T): string | null {
  return item.isValid() ? item.serialize() : null;
}

class FormField implements Serializable, Validatable {
  constructor(readonly name: string, readonly value: string) {}
  serialize(): string { return JSON.stringify({ [this.name]: this.value }); }
  isValid(): boolean  { return this.name.length > 0 && this.value.length > 0; }
}

class RawPayload {
  serialize(): string { return "{}"; }
  // no isValid() — structurally incomplete
}

saveIfValid(new FormField("email", "alice@example.com")); // OK — string | null
saveIfValid(new RawPayload()); // error: RawPayload does not satisfy Validatable

// Inline intersections work in utility signatures too:
function audit<T extends { id: string } & { createdAt: Date }>(record: T): string {
  return `${record.id} created at ${record.createdAt.toISOString()}`;
}
```

Intersection constraints compose freely: `T extends A & B & C` is valid. Each additional `&` narrows the set of types that may be substituted, so keep the list short enough to remain meaningful.

### Pattern D — Constraining with keyof and Record

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

### Pattern E — Conditional type constraint

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

### Pattern F — Conditional method availability via `this` typing

Make a method available only when the class is instantiated with a specific type argument. This is TypeScript's equivalent of Scala's `using ev: A =:= B` evidence parameters — no separate wrapper type or cast is required.

```typescript
class Container<A> {
  constructor(readonly value: A) {}

  // flatten is only callable when A is itself a Container<B>
  flatten<B>(this: Container<Container<B>>): Container<B> {
    return this.value;
  }

  // toArray is only callable when A extends readonly unknown[]
  toArray(this: Container<readonly unknown[]>): unknown[] {
    return [...this.value];
  }
}

const nested = new Container(new Container(42));
const flat: Container<number> = nested.flatten(); // OK

const plain = new Container(42);
plain.flatten(); // error: 'this' constraint — Container<number> is not Container<Container<B>>

const boxedList = new Container([1, 2, 3] as const);
boxedList.toArray(); // OK — readonly number[] extends readonly unknown[]
```

The trick is the explicit `this` parameter (erased at runtime). The method exists on every instance of `Container<A>` in the type system, but TypeScript only allows calling it when the `this` type constraint is satisfied. Combined with generics, it avoids the need to duplicate the class into narrowed wrapper types.

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Required fields | `if (!item.id) throw new Error('missing id')` — runtime guard repeated everywhere | `<T extends { id: string }>` — compile-time constraint; no runtime guard needed |
| Named capability | Duck-typing comment: `// obj must have a compareTo method`; forgotten silently | `T extends Comparable<T>` — missing method is a compile error at the call site |
| Multiple capabilities | Comment listing requirements; no enforcement | `T extends A & B` — both enforced structurally at compile time |
| Self-referential bound | N/A | F-bounded: `T extends Comparable<T>` ensures `compareTo` always matches the concrete type |
| Property access | `obj[key]` — any key, any value, no type information | `K extends keyof T` — only valid keys; return type is `T[K]` |
| Union filtering | Manual runtime `typeof` or `instanceof` checks | Conditional type `KeysOfType<T, U>` — computed at compile time with no runtime cost |
| Conditional methods | Separate subclass or manual check | `this` typing — method callable only when type argument satisfies a constraint |
| Lower bounds | N/A | Not available in TypeScript — use union types or overloads as an alternative |

## When to Use Which Feature

**Structural field constraint** (`T extends { id: string }`, Pattern A) is the simplest and most common form. Use it whenever a generic function needs access to one or a few named properties. Prefer this over a named interface when the constraint is local to one function.

**Interface bound** (Pattern B) is better when the same constraint is shared across many functions or when the capability has a meaningful name in the domain (`Comparable`, `Serialisable`, `Pageable`). Because TypeScript is structural, existing types satisfy the bound without any change. Use an **F-bounded interface** (`T extends Comparable<T>`) when the constraint must reference the concrete type itself — fluent builder APIs and self-referencing protocols are the primary use cases.

**Multiple constraints via intersection** (Pattern C, `T extends A & B`) is the right choice when a function requires unrelated capabilities at the same time. Prefer a dedicated named interface when the combination recurs frequently; use an inline `&` for one-off call sites or utility functions.

**keyof / Record constraint** (Pattern D) is the right tool for property-manipulation utilities — pickers, omitters, mappers, and serialisers. Pairing it with `as const` at call sites gives the narrowest possible return type.

**Conditional type constraint** (Pattern E) is for advanced cases where the constraint itself must be computed from another type. Use it in library code and utility types, not in everyday application code where simpler constraints suffice.

**`this`-typed conditional methods** (Pattern F) make individual methods on a generic class available only for specific type instantiations. Prefer this over separate narrowed subclasses when the core logic is shared and only one or two operations should be conditionally available.

**Lower bounds** do not exist in TypeScript. Scala's `B >: A` and similar constructs have no direct equivalent. Common workarounds are union types (`A | Base`) or multiple overloads.

## When to Use

Use generic constraints when:

1. **A function needs to invoke members that not all types have** — require `T extends { parse(): string }` instead of runtime checks.
2. **Type safety should scale with reuse** — constrain once, then any caller gets full type checking without duplication.
3. **You need to preserve the full type through transformations** — `find<T extends { id: string }>(items: T[])` returns `T`, narrowing at the call site.
4. **The constraint captures a real domain concept** — name it (`Comparable`, `Serializable`) when it appears in multiple places.

```typescript
// Before: runtime check, no narrowing
function getId(items: any[], id: string) {
  return items.find(x => x.id === id); // returns any
}

// After: compile-time constraint, preserves type
function getId<T extends { id: string }>(items: T[], id: string): T | undefined {
  return items.find(x => x.id === id); // returns T | undefined
}
```

## When Not to Use

Avoid generic constraints when:

1. **The constraint is too narrow for real use** — `T extends User` is less reusable than `T extends { id: string; name: string }`.
2. **You're constraining only to please the type system** — if the function never uses the constrained members, drop the constraint.
3. **A simpler type works** — `function first<T>(arr: T[]): T` needs no constraint.
4. **You need runtime polymorphism over many unrelated types** — prefer function overloads or a union type.

```typescript
// Over-constrained: only works for exact User type
function printName<T extends User>(x: T) { console.log(x.name); }

// Better: structural constraint
function printName<T extends { name: string }>(x: T) { console.log(x.name); }

// Unnecessary constraint
function double(x: number): number { return x * 2; }
// Don't do: function double<T extends { val: number }>(x: T): number
```

## Antipatterns When Using Constraints

### Antipattern A — Constrained but unused

The constraint adds no value if the generic function doesn't use the required members.

```typescript
// Unused constraint
function log<T extends { id: string; secret: string }>(x: T) {
  console.log("logged"); // never accesses id or secret
}

// Remove the constraint
function log<T>(x: T) { console.log("logged"); }
```

### Antipattern B — Overly specific type bound

Using a concrete type as the bound reduces reuse and defeats the purpose of generics.

```typescript
// Overly specific
function save<T extends User>(x: T) { db.insert(x); }

// Better: structural bound
function save<T extends { id: string; createdAt: Date }>(x: T) { db.insert(x); }
```

### Antipattern C — Contravariant confusion

Constraints don't reverse variance. A function `f<T extends Base>` does not accept `f<Derived>` if the caller passes `Base[]`.

```typescript
function sortByName<T extends { name: string }>(items: T[]): T[] {
  return items.sort((a, b) => a.name.localeCompare(b.name));
}

type Employee = { name: string; dept: string };
type Person = { name: string };

const people: Person[] = [{ name: "Alice" }];
sortByName(people); // OK, returns Person[]

const employees: Employee[] = [{ name: "Bob", dept: "Eng" }];
// You cannot pass employees to a generic that only promises { name: string }
```

### Antipattern D — Complex intersection for simple cases

Using `T extends A & B & C` when a single structural bound suffices.

```typescript
// Over-engineered
interface CanId { id: string; }
interface CanName { name: string; }
function findUser<T extends CanId & CanName>(items: T[], id: string): T | undefined {
  return items.find(x => x.id === id);
}

// Simpler
function findUser<T extends { id: string; name: string }>(items: T[], id: string): T | undefined {
  return items.find(x => x.id === id);
}
```

## Antipatterns with Other Techniques (Where Constraints Help)

### Antipattern A — Runtime type guards instead of constraints

Using `typeof` or `instanceof` at runtime when a constraint would enforce the shape at compile time.

```typescript
// Runtime guards
function process(x: any) {
  if (typeof x !== "object" || !x.id) throw new Error("bad");
  return x.id.toUpperCase();
}

// Compile-time constraint
function process<T extends { id: string }>(x: T): string {
  return x.id.toUpperCase();
}
```

### Antipattern B — `any` to bypass type errors

Using `any` or `as` casts instead of expressing the required shape with constraints.

```typescript
// Bad: any
function firstItem(items: any[]): any {
  return items[0];
}

// Better: constrained
function firstItem<T>(items: readonly T[]): T | undefined {
  return items[0];
}

// Bad: cast
function getId(obj: { data: any }) {
  return (obj.data as { id: string }).id;
}

// Better: constrained
function getId<T extends { id: string }>(obj: { data: T }): string {
  return obj.data.id;
}
```

### Antipattern C — Duplicate functions for each type

Writing separate functions instead of one generic with a constraint.

```typescript
// Duplication
function findUserById(users: User[], id: string): User | undefined {
  return users.find(u => u.id === id);
}
function findProductById(products: Product[], id: string): Product | undefined {
  return products.find(p => p.id === id);
}

// Single generic
function findById<T extends { id: string }>(items: readonly T[], id: string): T | undefined {
  return items.find(x => x.id === id);
}
```

### Antipattern D — Separate utility types that duplicate constraints

Creating utility types that each restate the same constraint instead of sharing it.

```typescript
// Duplicated constraint
type PickId<T> = T extends { id: string } ? T["id"] : never;
type LogId<T>  = T extends { id: string } ? T["id"] : never;
type SaveId<T> = T extends { id: string } ? T["id"] : never;

// Share the constraint
type HasId = { id: string };
type PickId<T> = T extends HasId ? T["id"] : never;
type LogId<T>  = T extends HasId ? T["id"] : never;
type SaveId<T> = T extends HasId ? T["id"] : never;
```
