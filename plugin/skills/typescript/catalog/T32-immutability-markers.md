# Immutability Markers

> **Since:** TypeScript 2.0 (`readonly`); `as const` since TypeScript 3.4

## 1. What It Is

TypeScript provides several compile-time mechanisms for expressing immutability. The **`readonly`** modifier on a property or parameter prevents reassignment after initialization — it does not guarantee deep immutability of the referenced value. **`ReadonlyArray<T>`** (equivalently `readonly T[]`) removes all mutating methods (`push`, `pop`, `splice`, etc.) from the array type. **`as const`** is an assertion that narrows an object literal or array to its most precise literal type and marks all properties and elements as `readonly`, making it the idiomatic way to declare compile-time constants. The **`Readonly<T>`** utility type wraps all properties of an object type with `readonly` in one step. Note that `Object.freeze()` enforces immutability at runtime and its *return type* is `Readonly<T>` (`readonly T[]` for arrays), but freezing a value in place does not retype the existing binding, and `freeze` never narrows values to literal types — that still requires `as const`.

**`const` vs `readonly`** — these solve different problems. `const` is a binding-level guarantee: `const x = obj` means `x` cannot be rebound to a different object, but `obj`'s properties remain mutable. `readonly` is a property-level guarantee: `readonly x: T` means the `x` property of a specific object cannot be reassigned. The two compose: a `const` binding to an object with `readonly` properties gives you both.

## 2. What Constraint It Lets You Express

**Prevent reassignment of properties and array mutations after construction at compile time; `as const` narrows literals to their exact types so they cannot be widened.**

- A `readonly` property on a class can be assigned in the constructor but not anywhere else; the compiler rejects all post-construction assignments.
- `readonly T[]` prevents `push`, `pop`, `sort`, and other in-place mutations on the array type; values can still be read and iterated.
- `as const` on a string literal (`"GET" as const`) preserves the exact literal type `"GET"` rather than widening to `string`, which is essential for discriminated unions and `Record<K, V>` exhaustiveness.

## 3. Minimal Snippet

```typescript
// --- readonly property ---
interface Point {
  readonly x: number;
  readonly y: number;
}

const p: Point = { x: 1, y: 2 };
// p.x = 3; // error — cannot assign to 'x' because it is a read-only property

// --- ReadonlyArray ---
function sum(nums: readonly number[]): number {
  // nums.push(4); // error — push does not exist on readonly number[]
  return nums.reduce((a, b) => a + b, 0);
}

const xs = [1, 2, 3];
console.log(sum(xs)); // OK — mutable arrays are assignable to readonly

// --- as const: literal narrowing + readonly ---
const METHODS = ["GET", "POST", "PUT", "DELETE"] as const;
// METHODS is: readonly ["GET", "POST", "PUT", "DELETE"]
type HttpMethod = (typeof METHODS)[number]; // OK — "GET" | "POST" | "PUT" | "DELETE"

const CONFIG = {
  host: "localhost",
  port: 8080,
} as const;
// CONFIG.host is "localhost" (literal), not string
// CONFIG.port is 8080 (literal), not number
// CONFIG.host = "other"; // error — readonly

// --- Readonly<T> utility type ---
interface Config {
  host: string;
  port: number;
  timeout?: number;
}

type FrozenConfig = Readonly<Config>;
// Equivalent to: { readonly host: string; readonly port: number; readonly timeout?: number }

function processConfig(cfg: FrozenConfig) {
  // cfg.host = "other"; // error — readonly
  return `${cfg.host}:${cfg.port}`;
}
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Literal Types** [-> T52](T52-literal-types.md) | `as const` is the bridge between immutability and literal types: it simultaneously marks properties `readonly` and narrows their types to exact literals, preventing widening. |
| **Record Types & Interfaces** [-> T31](T31-record-types.md) | `readonly` fields on record types and `Readonly<T>` compose naturally; `as const` applied to object literals produces `Readonly`-equivalent types with literal-precision values. Functional updates via spread (`{ ...obj, field: newVal }`) are the idiomatic alternative to mutation. |
| **Encapsulation** [-> T21](T21-encapsulation.md) | `readonly` is a form of encapsulation: it allows external code to read a property but not modify it, expressing the ownership model of an object without hiding the field entirely. |
| **ADTs & Discriminated Unions** [-> T01](T01-algebraic-data-types.md) | `as const` on tagged literals (`{ kind: "circle" as const, ... }`) preserves the literal type of the discriminant, enabling exhaustive narrowing. Without `as const` or a `readonly` annotation, the discriminant widens to `string` and narrowing breaks. |
| **Generics & Utility Types** [-> T04](T04-generics-bounds.md) | `Readonly<T>` is a generic mapped type: `type Readonly<T> = { readonly [K in keyof T]: T[K] }`. It composes with other mapped types, and you can build a recursive `DeepReadonly<T>` on the same pattern. |
| **Effect Tracking** [-> T12](T12-effect-tracking.md) | TypeScript has no effect-tracking equivalent to Lean's monadic types or Rust's `&mut` — mutation is unchecked at runtime. `readonly` only enforces at the type level and only for reassignment; imperative mutation of object internals (array `.push`, Map `.set`) is invisible to the type system unless the type itself is a readonly variant. |

## 5. Gotchas and Limitations

1. **`readonly` is shallow** — `readonly items: string[]` prevents reassigning the `items` reference but does not prevent `items.push("x")`; use `readonly string[]` or `ReadonlyArray<string>` to make the contents immutable at the type level.
2. **`Readonly<T>` is also shallow** — `Readonly<{ nested: { x: number } }>` makes `nested` readonly (cannot reassign the reference) but not `nested.x`; use a recursive `DeepReadonly<T>` for deep immutability.
3. **`Object.freeze` retypes its return value, not its argument** — `const frozen = Object.freeze(obj)` gives `frozen` the type `Readonly<typeof obj>` (and `readonly T[]` for arrays), so `frozen.host = "x"` is a compile error. But calling `Object.freeze(obj)` as a bare statement leaves the original binding's type mutable: `const o = { a: 1 }; Object.freeze(o); o.a = 2;` compiles cleanly and fails only at runtime. `freeze` also does not narrow to literal types — pair it with `as const` when you need literal precision as well.
4. **Mutable arrays are assignable to `readonly` but not vice versa** — `number[]` is assignable to `readonly number[]` (you can pass a mutable array where a readonly is expected), but `readonly number[]` is not assignable to `number[]` (you cannot give a readonly array to a function that mutates it).
5. **`readonly` property modifiers are ignored in structural assignability** — this is the single biggest hole, and it does *not* parallel gotcha 4. `ReadonlyArray<T>` is a distinct type that the assignability check enforces, but `readonly` on an object property is discarded when checking whether one object type is assignable to another. A `Readonly<T>` value can be passed straight into a parameter typed `T` and mutated, with no error:
   ```typescript
   interface P { x: number }
   function mutate(p: P) { p.x = 99; }
   const rp: Readonly<P> = { x: 1 };
   mutate(rp); // no error — the readonly modifier is silently dropped
   ```
   Treat `readonly` on properties as intent-documenting and locally enforced, not as a guarantee that survives an API boundary. Use `readonly T[]`/`ReadonlyMap`/`ReadonlySet` for collections, where the guarantee *is* enforced.
6. **`as const` on a `let` binding pins the type, which is rarely what you want** — `let x = "hello" as const` gives `x` the type `"hello"`, not `string`; the assertion is not weakened by `let`, so `x = "world"` fails with `Type '"world"' is not assignable to type '"hello"'`. If you want a reassignable variable ranging over a fixed set, annotate the union explicitly: `let x: "hello" | "world" = "hello"`.
7. **`as const` on deeply nested objects** — `as const` is fully recursive; all nested properties are marked `readonly` and their types narrowed to literals, which can be surprising for large configuration objects where some values are meant to be runtime-variable.
8. **`const` does not imply `readonly` on properties** — `const config = { port: 8080 }` infers `{ port: number }` and `config.port = 9090` is valid. `const` only prevents rebinding `config` itself. Use `as const` or `Readonly<T>` to lock the properties.
9. **`ReadonlyMap` and `ReadonlySet`** — TypeScript ships `ReadonlyMap<K, V>` and `ReadonlySet<T>` interfaces that remove all mutating methods, parallel to `ReadonlyArray<T>`. Prefer these over raw `Map`/`Set` in function parameters that should not mutate the collection.
10. **`readonly` on index signatures** — `{ readonly [key: string]: number }` prevents writing through any key. This is rarer but important for cache-like structures that should not be mutated outside a specific module.

## 6. Beginner Mental Model

Think of TypeScript's immutability as **two separate padlocks on different doors**:

- **`const`** locks the **name**: once `const x = something`, the name `x` cannot be pointed at a different value. But if the value is an object, its interior remains unlocked.
- **`readonly`** locks a specific **property door**: `readonly port: number` means no one can open that door to change what is inside, even if they got through the outer door.
- **`as const`** locks **everything at once**: it snaps `readonly` onto every property, recursively, and also shrinks each value's type down to its exact literal. It is like laminating the whole object — nothing inside can change and the type reflects every detail exactly.
- **`Readonly<T>`** is a **blueprint converter**: give it any interface and it stamps `readonly` onto all properties, producing a new type for passing data somewhere that should not mutate it.

Coming from Rust: TypeScript's `const` is analogous to Rust's immutable `let` binding; `readonly` on properties is analogous to Rust having no `mut` on a struct field. Unlike Rust, TypeScript has no borrow checker — `readonly` is a type-level promise, not a runtime or ownership guarantee.

Coming from Python: `Final` is the closest analogue — `MAX: Final = 100` for a module-level constant, and `self.id: Final` for an attribute that may only be assigned in `__init__`, which mirrors `readonly` on a class field. (Python's `@final` decorator is unrelated: it blocks subclassing and method overriding, not assignment.) Both `Final` and `readonly` enforce only at the type-checker level, not at runtime.

## 7. Example A — Application constants and discriminated unions

```typescript
// Discriminant fields must be literal types — as const preserves them
const STATUS = {
  PENDING: "pending",
  ACTIVE: "active",
  CLOSED: "closed",
} as const;
type Status = (typeof STATUS)[keyof typeof STATUS]; // "pending" | "active" | "closed"

type Order =
  | { status: typeof STATUS.PENDING; createdAt: Date }
  | { status: typeof STATUS.ACTIVE; activatedAt: Date }
  | { status: typeof STATUS.CLOSED; closedAt: Date; reason: string };

function describeOrder(order: Order): string {
  switch (order.status) {
    case STATUS.PENDING:
      return `Pending since ${order.createdAt.toISOString()}`;
    case STATUS.ACTIVE:
      return `Active since ${order.activatedAt.toISOString()}`;
    case STATUS.CLOSED:
      return `Closed: ${order.reason}`;
    // No default needed — the type checker knows all cases are covered
  }
}

// Module-level constants with readonly arrays
const ALLOWED_ROLES = ["admin", "editor", "viewer"] as const;
type Role = (typeof ALLOWED_ROLES)[number];

function isAllowedRole(role: string): role is Role {
  return (ALLOWED_ROLES as readonly string[]).includes(role);
}
```

**Why this matters:** Without `as const`, `STATUS.PENDING` widens to `string`, the `Order` union loses its discriminant precision, and the exhaustiveness check in `switch` breaks. `as const` makes the literals load-bearing parts of the type.

## 8. Example B — Functional updates and DeepReadonly

```typescript
// Functional update: spread creates a new object, the original is unchanged
interface Address {
  readonly city: string;
  readonly zip: string;
}

interface Person {
  readonly name: string;
  readonly address: Address;
}

function relocate(person: Person, newCity: string): Person {
  return {
    ...person,
    address: { ...person.address, city: newCity },
  };
}

const alice: Person = { name: "Alice", address: { city: "NY", zip: "10001" } };
const moved = relocate(alice, "LA");
// alice is unchanged; moved is a new object
// alice.address.city  →  "NY"
// moved.address.city  →  "LA"

// DeepReadonly — recursive mapped type for deep immutability
type DeepReadonly<T> = T extends (infer U)[]
  ? ReadonlyArray<DeepReadonly<U>>
  : T extends Map<infer K, infer V>
  ? ReadonlyMap<K, DeepReadonly<V>>
  : T extends Set<infer U>
  ? ReadonlySet<DeepReadonly<U>>
  : T extends object
  ? { readonly [K in keyof T]: DeepReadonly<T[K]> }
  : T;

interface AppConfig {
  server: {
    host: string;
    ports: number[];
  };
  features: Record<string, boolean>;
}

type FrozenAppConfig = DeepReadonly<AppConfig>;
// server.host — readonly string
// server.ports — ReadonlyArray<number>
// features — { readonly [x: string]: boolean }

declare const cfg: FrozenAppConfig;
// cfg.server.host = "other";    // error — readonly
// cfg.server.ports.push(9090);  // error — ReadonlyArray has no push
```

**Pattern:** `DeepReadonly<T>` is not in the standard library but is easy to define. Prefer it at module or API boundaries where you want to guarantee that configuration or domain objects are never mutated downstream.

## 9. When to Use

- **Configuration objects**: When values are set once and should never change
  ```typescript
  const DB_CONFIG = { host: "localhost", port: 5432 } as const;
  ```
  Pair `as const` with `satisfies` (TypeScript 4.9+) when the constant must also conform to a schema: `satisfies` checks the object against the type without widening it, so you keep the literal types *and* get an error if a field is missing or misspelled. A plain `: DbConfig` annotation would discard the literals.
  ```typescript
  interface DbConfig { host: string; port: number }
  const DB = { host: "localhost", port: 5432 } as const satisfies DbConfig;
  // DB.port is 5432 (literal), and a typo in a key is still a compile error
  ```

- **Discriminated unions**: When tag values must remain literal types for exhaustiveness
  ```typescript
  type Msg = { type: "add"; value: number } | { type: "remove" };
  const msg: Msg = { type: "add" as const, value: 1 };
  ```

- **Function parameters**: When the function should not mutate its inputs
  ```typescript
  function copyItems(items: readonly string[]): string[] {
    return [...items];
  }
  ```

- **Domain constants**: When enumerating fixed sets of values
  ```typescript
  const HTTP_METHODS = ["GET", "POST", "PUT"] as const;
  type HttpMethod = (typeof HTTP_METHODS)[number];
  ```

## 10. When NOT to Use

- **Mutable collections in functions**: When the function needs to modify arrays in place
  ```typescript
  function sortInPlace(items: number[]) {
    items.sort(); // ❌ Cannot use readonly number[]
  }
  ```

- **Runtime-modified state**: When object properties change based on runtime logic
  ```typescript
  class Counter {
    count = 0; // ❌ Should not be readonly, will increment
    increment() { this.count++; }
  }
  ```

- **Shared mutable configs**: When config needs runtime flexibility
  ```typescript
  const config = { theme: "light" }; // ❌ Use without as const
  config.theme = "dark"; // Must allow mutation later
  ```

- **Hot loops that would otherwise copy**: `readonly` itself is erased and costs nothing at runtime — the cost comes from the functional-update idiom it pushes you toward. Accumulating into a `readonly` array by spreading reallocates on every iteration (O(n²) copying); build with a local mutable array and return it as `readonly`, which is free because mutable arrays are assignable to readonly ones.
  ```typescript
  declare function transform(n: number): string;

  // ❌ Spreading into a readonly accumulator copies the whole array each step
  function collectSlow(rows: readonly number[]): readonly string[] {
    let acc: readonly string[] = [];
    for (const r of rows) acc = [...acc, transform(r)];
    return acc;
  }

  // ✅ Mutate locally, expose readonly at the boundary
  function collect(rows: readonly number[]): readonly string[] {
    const acc: string[] = [];
    for (const r of rows) acc.push(transform(r));
    return acc; // callers still cannot mutate it
  }
  ```

## 11. Antipatterns

### ❌ Shallow readonly without deep immutability
```typescript
interface Node {
  readonly children: Node[]; // ❌ children.array mutation still possible
}
const root: Node = { children: [] };
root.children.push({ children: [] }); // Compiles but breaks immutability intent
// ✅ Make the element type readonly too: `readonly children: readonly Node[]`,
//    or wrap the whole tree with DeepReadonly<Node>
```

### ❌ Relying on `readonly` properties to protect a value you hand to someone else
```typescript
interface Point { x: number; y: number }
function normalize(p: Point) { p.x = 0; } // mutates its argument

const origin: Readonly<Point> = { x: 3, y: 4 };
normalize(origin); // ❌ compiles — readonly modifiers are dropped by assignability
// ✅ Use a readonly-enforcing type the check respects (readonly T[], ReadonlyMap,
//    ReadonlySet), or pass a defensive copy: normalize({ ...origin })
```

### ❌ as const on runtime values that change
```typescript
declare function fetchKey(): string;
// @ts-expect-error — as const cannot be applied to a function call result, only literals
let apiKey = fetchKey() as const; // ❌ fetchKey returns string, not literal
apiKey = "new-key"; // Runtime changes break the as const guarantee
// ✅ Use regular string type for runtime values
```

### ❌ Nesting as const too deeply
```typescript
const API = {
  endpoints: {
    users: { id: 123, name: "users" }
  }
} as const; // ❌ Everything locked, even transient data
// ✅ Split: use as const only for static config parts
```

## 12. When This Technique Improves Other Patterns

### ❌ Without as const (the discriminant widens and narrowing is lost)
```typescript
const actionTypes = { ADD: "ADD", REMOVE: "REMOVE" };
// inferred as { ADD: string; REMOVE: string } — the values widen

type Action =
  | { type: typeof actionTypes.ADD }
  | { type: typeof actionTypes.REMOVE };
// ❌ both members are { type: string }; the union collapses, the discriminant is gone

function handle(action: Action): string {
  switch (action.type) {
    case actionTypes.ADD: return "added";
    case actionTypes.REMOVE: return "removed";
  }
  return "unreachable"; // ❌ required — no narrowing, so the compiler sees a fallthrough
}
```

### ✅ With as const (literal discriminants restore exhaustiveness)
```typescript
const ActionTypes = { ADD: "ADD", REMOVE: "REMOVE" } as const;

type Action =
  | { type: typeof ActionTypes.ADD }
  | { type: typeof ActionTypes.REMOVE };

function handle(action: Action): string {
  switch (action.type) {
    case ActionTypes.ADD: return "added";
    case ActionTypes.REMOVE: return "removed";
  }
  // ✅ no trailing return needed — the compiler proves both cases are covered,
  //    and adding a third Action member makes this function an error
}
```

Note that the exhaustiveness check only bites because `handle` has an explicit `: string` return type. A switch in a function with an inferred (or `void`) return type never reports a missing case, no matter how precise the discriminant is.

### ❌ Without readonly (accidental mutation in callbacks)
```typescript
function process(items: string[]) {
  items.forEach(x => items.push(x + "!")); // ❌ Unintended mutation
}
```

### ✅ With readonly (mutation prevented)
```typescript
function process(items: readonly string[]) {
  // @ts-expect-error — push does not exist on readonly string[]
  items.forEach(x => items.push(x + "!")); // ✅ Compile error
}
```

### ❌ Without readonly (interface allows mutation of return value)
```typescript
interface Service {
  getUser(): { id: number; name: string };
}
const svc: Service = { getUser() { return { id: 1, name: "Alice" }; } };
const user = svc.getUser();
user.name = "Bob"; // ❌ Changes shared data
```

### ✅ With readonly (return immutability enforced)
```typescript
interface Service {
  getUser(): { readonly id: number; readonly name: string };
}
const svc: Service = { getUser() { return { id: 1, name: "Alice" }; } };
const user = svc.getUser();
// @ts-expect-error — cannot assign to 'name' because it is a read-only property
user.name = "Bob"; // ✅ Compile error
```

## 13. Common Type-Checker Errors

### `Cannot assign to 'x' because it is a read-only property`

```typescript
interface Point {
  readonly x: number;
  readonly y: number;
}
const p: Point = { x: 1, y: 2 };
// @ts-expect-error — cannot assign to 'x' because it is a read-only property
p.x = 3; // error
```

**Meaning:** The property is marked `readonly`. Create a new object with spread (`{ ...p, x: 3 }`) instead of mutating in place.

### `Property 'push' does not exist on type 'readonly number[]'`

```typescript
function bad(nums: readonly number[]): void {
  // @ts-expect-error — push does not exist on readonly number[]
  nums.push(4); // error
}
```

**Meaning:** The array parameter is typed as `ReadonlyArray`. Either remove `readonly` from the parameter if mutation is intended, or use a non-mutating operation (`[...nums, 4]`).

### `The type 'readonly string[]' is 'readonly' and cannot be assigned to the mutable type 'string[]'`

```typescript
const frozen: readonly string[] = ["a", "b"];
// @ts-expect-error — readonly string[] is not assignable to mutable string[]
const mutable: string[] = frozen; // error
```

**Meaning:** A `readonly` array is not assignable where a mutable array is expected, because the callee might mutate it. Use spread to copy: `const mutable: string[] = [...frozen]`.

### `Cannot assign to 'x' because it is a read-only property` (on class field)

```typescript
class Foo {
  readonly id: string;
  constructor(id: string) { this.id = id; }
  // @ts-expect-error — cannot assign to 'id' because it is a read-only property
  rename(newId: string) { this.id = newId; } // error
}
```

**Meaning:** `readonly` class fields can only be assigned in the constructor or at the declaration site. Move initialization to the constructor; all other assignment sites are errors.

## 14. Use-Case Cross-References

- [-> UC-06](../usecases/UC06-immutability.md) Use `readonly`, `as const`, and `ReadonlyArray` to encode immutability constraints in data structures and function signatures
- [-> UC-02](../usecases/UC02-domain-modeling.md) Model domain constants and value objects with `as const` and `Readonly<T>` to prevent accidental mutation of core domain data
- [-> UC-01](../usecases/UC01-invalid-states.md) `readonly` properties and `as const` discriminants prevent accidental state transitions that would create invalid domain states

## Source Anchors

- [TypeScript Handbook — readonly Properties](https://www.typescriptlang.org/docs/handbook/2/objects.html#readonly-properties)
- [TypeScript Handbook — const Assertions](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-4.html#const-assertions)
- [TypeScript Handbook — Readonly Utility Type](https://www.typescriptlang.org/docs/handbook/utility-types.html#readonlytype)
- [TypeScript FAQ — Why are readonly arrays not assignable to mutable arrays?](https://github.com/microsoft/TypeScript/wiki/FAQ#why-are-readonly-arrays-not-assignable-to-mutable-arrays)
