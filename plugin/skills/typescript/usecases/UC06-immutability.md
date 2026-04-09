# Immutability

## The Constraint

Prevent mutation of values after construction. The compiler rejects assignments to readonly properties and mutations of readonly arrays, making accidental in-place modification a compile error rather than a runtime surprise.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **const / let** | Prevent rebinding of a variable; baseline immutability for bindings | [-> T32](../catalog/T32-immutability-markers.md) |
| **readonly / as const** | Mark individual properties or entire object trees as immutable | [-> T32](../catalog/T32-immutability-markers.md) |
| **Readonly record properties** | Declare each field of a type as non-writable | [-> T31](../catalog/T31-record-types.md) |
| **Mapped types** | Derive `DeepReadonly<T>` that recursively marks every nested property readonly | [-> T62](../catalog/T62-mapped-types.md) |

## Patterns

### Pattern A — const bindings

`const` is the lowest level of immutability: it prevents a binding from being reassigned. Prefer `const` over `let` everywhere; reach for `let` only when the binding must be updated.

```typescript
const x = 10;
// x = 20; // error: Cannot assign to 'x' because it is a constant.

let y = 10;
y = 20; // OK — let allows reassignment

// IMPORTANT: const only prevents rebinding — it does NOT prevent mutation of the value:
const arr = [1, 2, 3];
arr.push(4);   // OK — const does not freeze the array contents
// arr = [5];  // error: Cannot assign to 'arr' because it is a constant.

// For true immutability, combine const with a readonly type:
const frozen: readonly number[] = [1, 2, 3];
// frozen.push(4); // error: Property 'push' does not exist on type 'readonly number[]'
```

### Pattern B — readonly properties on an interface

Mark individual fields with `readonly`. Assignment after construction is a compile error. The `readonly` modifier also applies to array elements via `readonly T[]` or `ReadonlyArray<T>`.

```typescript
interface Point {
  readonly x: number;
  readonly y: number;
}

const p: Point = { x: 3, y: 4 };
p.x = 10; // error: Cannot assign to 'x' because it is a read-only property

function translate(p: Point, dx: number, dy: number): Point {
  // Must create a new value — cannot mutate the argument:
  return { x: p.x + dx, y: p.y + dy };
}

interface Config {
  readonly host: string;
  readonly port: number;
  readonly allowedOrigins: readonly string[];
}

const cfg: Config = {
  host: "localhost",
  port: 8080,
  allowedOrigins: ["https://example.com"],
};

cfg.host = "remote";          // error: read-only property
cfg.allowedOrigins.push("x"); // error: push does not exist on ReadonlyArray<string>
```

### Pattern C — Functional updates with spread

The TypeScript equivalent of Lean's `{ s with field := val }` or Scala's `copy()` is the object spread syntax. It produces a new object with one or more fields overridden, leaving the original untouched.

```typescript
interface Config {
  readonly host: string;
  readonly port: number;
  readonly ssl: boolean;
}

const devConfig: Config = { host: "localhost", port: 8080, ssl: false };

// Spread produces a new object — devConfig is never mutated:
const prodConfig: Config = { ...devConfig, host: "prod.example.com", ssl: true };

console.log(devConfig.host);  // "localhost"
console.log(prodConfig.host); // "prod.example.com"
```

For arrays, use methods that return new arrays instead of mutating in place:

```typescript
const xs = [1, 2, 3] as const;

// Append — instead of xs.push(4):
const ys = [...xs, 4];                           // [1, 2, 3, 4]; xs unchanged

// Replace element — instead of xs[1] = 99:
const zs = xs.map((v, i) => (i === 1 ? 99 : v)); // [1, 99, 3]; xs unchanged

// Remove element — instead of xs.splice(1, 1):
const ws = xs.filter((_, i) => i !== 1);          // [1, 3]; xs unchanged
```

> **Deep nesting**: spread is a shallow copy. For deeply nested structures, each level must be spread explicitly, or use a helper such as [immer](https://immerjs.github.io/immer/) which applies mutations to a draft and returns a new immutable value.

### Pattern D — as const for configuration objects

`as const` freezes an expression: every field becomes `readonly`, and string/number values are narrowed to their literal types. Use it for configuration objects, lookup tables, and constant arrays.

```typescript
const HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"] as const;
type HttpMethod = (typeof HTTP_METHODS)[number]; // "GET" | "POST" | "PUT" | "DELETE" | "PATCH"

const SERVER_CONFIG = {
  host: "api.example.com",
  port: 443,
  tls: true,
  timeouts: {
    connect: 5_000,
    read:   30_000,
  },
} as const;

// Every field and nested field is readonly and has a literal type:
SERVER_CONFIG.port;             // type: 443 (not number)
SERVER_CONFIG.host = "other";   // error: read-only property
SERVER_CONFIG.timeouts.read = 0; // error: read-only property

// Derive a type from the constant:
type ServerConfig = typeof SERVER_CONFIG;
// { readonly host: "api.example.com"; readonly port: 443; readonly tls: true; … }
```

### Pattern E — Readonly<T> utility type

`Readonly<T>` shallowly wraps any type, making all its direct properties readonly. Use it to communicate at function-signature level that an argument will not be mutated.

```typescript
type User = {
  id: string;
  name: string;
  roles: string[];
};

// Function promises not to mutate the user object:
function displayUser(user: Readonly<User>): string {
  user.name = "changed"; // error: read-only property
  return `${user.name} (${user.roles.join(", ")})`;
}

// Readonly<T> is shallow — nested arrays are not recursively readonly:
function addRole(user: Readonly<User>, role: string): void {
  user.roles.push(role); // OK — Readonly<User> only freezes direct properties
  // To prevent this, use DeepReadonly (Pattern F) or readonly string[] in the type definition
}
```

### Pattern F — Deep readonly with a recursive mapped type

A recursive mapped conditional type makes every property at every depth readonly. This is the full structural immutability guarantee.

```typescript
type Primitive = string | number | boolean | bigint | symbol | null | undefined;

type DeepReadonly<T> =
  T extends Primitive
    ? T
    : T extends Array<infer U>
      ? ReadonlyArray<DeepReadonly<U>>
      : T extends ReadonlyArray<infer U>
        ? ReadonlyArray<DeepReadonly<U>>
        : T extends object
          ? { readonly [K in keyof T]: DeepReadonly<T[K]> }
          : T;

type AppState = {
  users: Array<{
    id: string;
    profile: { name: string; avatar: string };
    roles: string[];
  }>;
  settings: {
    theme: "light" | "dark";
    notifications: boolean;
  };
};

type ImmutableState = DeepReadonly<AppState>;

declare const state: ImmutableState;

state.settings.theme = "light";       // error: read-only property
state.users.push({ id: "x", profile: { name: "y", avatar: "z" }, roles: [] });
                                       // error: push does not exist on ReadonlyArray
state.users[0].profile.name = "Bob";  // error: read-only property
```

### Pattern G — Sealing classes (limited)

TypeScript has no `final` class keyword (unlike Scala's `final case class` or Python's `@final`). The idiomatic workarounds are a private constructor combined with a static factory, or a `declare abstract` trick — but neither is enforced by the runtime.

```typescript
// Private constructor prevents external subclassing in practice:
class Coordinate {
  private constructor(
    readonly x: number,
    readonly y: number,
  ) {}

  static of(x: number, y: number): Coordinate {
    return new Coordinate(x, y);
  }

  translate(dx: number, dy: number): Coordinate {
    return Coordinate.of(this.x + dx, this.y + dy);
  }
}

// class Derived extends Coordinate {}  // error: constructor is private

const origin = Coordinate.of(0, 0);
const moved  = origin.translate(3, 4);
```

> If preventing subclassing is critical (e.g., security-sensitive classes or singletons), prefer composition over inheritance so the constraint never arises.

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| `const` binding | Prevents rebinding; zero cost; universal baseline | Does not prevent value mutation; requires `readonly` types for full effect |
| `readonly` fields | Compile-time, zero runtime cost; IDE highlights violations instantly | Shallow by default — nested objects need explicit `readonly` or `DeepReadonly<T>` |
| Spread `{ ...obj, field }` | Functional updates without mutation; idiomatic and readable | Shallow copy — deep nesting requires manual spreading at each level |
| `as const` | Literal types + full tree readonly; ideal for constants and lookup tables | Cannot be applied to values with computed/dynamic parts; not updatable |
| `Readonly<T>` | Documents non-mutation contracts at function boundaries | Shallow — only direct properties; does not guard nested mutable arrays |
| `DeepReadonly<T>` | Full structural guarantee at every depth | Verbose; may conflict with libraries that expect mutable types |
| Private constructor | Approximates sealed/final classes | Runtime does not enforce it; no language-level guarantee |

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Property immutability | `Object.freeze()` — runtime enforcement, throws in strict mode, silent otherwise; not recursive by default | `readonly` field — compile-time enforcement; no runtime cost; IDE highlights violations immediately |
| Constant configuration | `const obj = { … }` — only the binding is const; `obj.port = 99` works silently | `as const` — every field is readonly and has a literal type; mutations are compile errors |
| Function non-mutation contract | JSDoc comment `@param {Object} user - do not mutate` — ignored by the engine | `Readonly<User>` parameter type — mutation inside the function is a compile error |
| Deep immutability | `deepFreeze()` utility — runtime only, missed in tests, no type feedback | `DeepReadonly<T>` — full structural compile-time guarantee at zero runtime cost |
| Functional updates | Spread `{ ...obj, field: val }` — works but no type-level check that the original is immutable | Spread on `readonly`-typed objects — spread still creates a new object; compiler prevents in-place mutation of the source |

## When to Use Which Feature

**`const` for every binding** (Pattern A) is the baseline — use `let` only when a binding genuinely must be reassigned. This alone eliminates a large class of accidental mutations.

**readonly on interface fields** (Pattern B) is the next default. Apply it to every field of a domain type unless mutation is explicitly required. Pair `readonly` on the property with `readonly T[]` for array fields to prevent both reassignment and in-place mutation.

**Spread `{ ...obj }` / `[...arr]`** (Pattern C) is the idiomatic way to produce updated values without mutating the original. Reach for it any time you would be tempted to write `obj.field = newValue`.

**as const** (Pattern D) is the right tool for all compile-time constants: enum-like string arrays, configuration objects, and routing tables. It is lighter than a full type annotation and gives the narrowest possible literal types for free.

**Readonly<T>** (Pattern E) belongs on function parameter types when the function should not mutate its argument but the type itself is defined elsewhere (e.g., a mutable ORM entity). It documents the contract at the call site without changing the type definition.

**DeepReadonly<T>** (Pattern F) is the right choice for Redux-style application state, configuration loaded once at startup, and any deeply nested value that must be treated as immutable throughout a codebase. Define it once in a shared utilities module and apply it to state types.

**Private constructor** (Pattern G) is a pragmatic substitute for `final` when you need to prevent subclassing. Prefer it only when the class is a value object or singleton; otherwise, favour composition over inheritance so sealing is never needed.

---

## When to Use It

- **Application state** shared across components (Redux, Zustand, Context)
- **Configuration objects** loaded at startup from env/JSON
- **Value objects** where equality by content matters (money, coordinates)
- **API responses** you want to treat as immutable after fetch
- **Function parameters** when you want to guarantee non-mutation
- **Event handlers** that receive data they should not alter

```typescript
// When: Shared state across components
interface AppState {
  readonly user: User;
  readonly items: readonly Item[];
}

function updateUser(state: DeepReadonly<AppState>, newUser: User): AppState {
  return { ...state, user: newUser }; // ✅ creates new state
}
```

```typescript
// When: Configuration from build time
const API_CONFIG = {
  baseUrl: "https://api.example.com",
  timeout: 5000,
} as const;

// ✅ Cannot accidentally change at runtime
```

```typescript
// When: Value objects for domain logic
class Money {
  constructor(
    readonly amount: number,
    readonly currency: string
  ) {}

  add(other: Money): Money {
    return new Money(this.amount + other.amount, this.currency);
  }
}
```

## When NOT to Use It

- **High-frequency updates** where object churn causes GC pressure (game rendering, real-time charts)
- **Large binary/blob data** where copying is expensive
- **Third-party mutable APIs** that require mutation (ORMs, DOM manipulation)
- **Streams/buffers** where incremental updates are required
- **Prototyping** when you're exploring and need quick mutations

```typescript
// When NOT: Game rendering loop (60fps with 1000+ objects)
// ❌ Avoid: creating new objects every frame
function updateEntities(entities: ReadonlyArray<Entity>): ReadonlyArray<Entity> {
  return entities.map(e => ({ ...e, x: e.x + e.vx })); // GC pressure!
}

// ✅ Use mutable arrays for performance-critical code
function updateEntitiesMutable(entities: Entity[]): void {
  for (let i = 0; i < entities.length; i++) {
    entities[i].x += entities[i].vx;
  }
}
```

```typescript
// When NOT: Working with mutable third-party APIs
class UserRepository {
  // ❌ Readonly conflicts with ORM expectations
  async save(entity: Readonly<UserEntity>): Promise<void> {
    // entity.updatedAt = new Date(); // error: read-only
  }
}
```

---

## Antipatterns When Using Immutability

### Antipattern 1: Shallow spread on deeply nested data

```typescript
interface State {
  readonly user: {
    readonly profile: {
      readonly settings: { theme: string };
    };
  };
}

function toggleTheme(state: State): State {
  // ❌ Only copies user, profile, settings — theme mutation affects original
  return { ...state, user: { ...state.user } };
  // state.user.profile.settings.theme = "dark"; // still mutates original!
}

// ✅ Explicitly spread each level
function toggleThemeFixed(state: State): State {
  return {
    ...state,
    user: {
      ...state.user,
      profile: {
        ...state.user.profile,
        settings: { ...state.user.profile.settings, theme: "dark" },
      },
    },
  };
}
```

### Antipattern 2: Forgetting `readonly` on array values

```typescript
interface Config {
  readonly allowedHosts: string[]; // ❌ Array itself is mutable
}

const cfg: Config = { allowedHosts: ["example.com"] };
cfg.allowedHosts.push("evil.com"); // ✅ Compiles! Mutation still possible
```

```typescript
interface Config {
  readonly allowedHosts: readonly string[]; // ✅ Array is also readonly
}

const cfg: Config = { allowedHosts: ["example.com"] };
cfg.allowedHosts.push("evil.com"); // ❌ Error: Property 'push' does not exist
```

### Antipattern 3: Mixing mutable state inside `Readonly<T>`

```typescript
interface MutableCounter {
  value: number;
  increment(): void;
}

interface State {
  readonly counters: ReadonlyArray<MutableCounter>;
}

// ❌ Array can't be mutated, but counter objects inside still have methods
function badIncrement(state: State): void {
  state.counters[0].increment(); // ✅ Compiles! Internal state still mutable
}
```

### Antipattern 4: Using `as const` on runtime-computed values

```typescript
function getConfig(environment: string) {
  // ❌ as const on dynamic data — types don't match runtime
  const config = {
    apiUrl: environment === "prod" ? "https://prod.api.com" : "http://localhost",
  } as const;
  // Type suggests literal values, but they're dynamic!
}
```

### Antipattern 5: Overusing `DeepReadonly` causing type hell

```typescript
// ❌ DeepReadonly breaks library function compatibility
function submitForm(data: FormData) {
  const readonlyData = DeepReadonly(formData);
  handleSubmit(readonlyData); // error: Type not assignable (expected mutables)
}

// ✅ Use partial readonly only where needed
function submitForm(formData: FormData) {
  handleSubmit({ ...formData, locked: true }); // Spread, let function handle typing
}
```

---

## Antipatterns Fixed by Immutability

### Pattern 1: Race conditions with shared mutable state

```typescript
// ❌ Without immutability: race condition in async code
let total = 0;
const invoices = [{ amount: 100 }, { amount: 200 }];

async function processInvoices() {
  const promises = invoices.map(inv =>
    fetch(`/api/process/${inv.amount}`).then(() => {
      total += inv.amount; // ❌ Race condition!
    }),
  );
  await Promise.all(promises);
  console.log(total); // Unpredictable
}

// ✅ With immutability: no shared mutable state
async function processInvoicesSafe(invoices: readonly Invoice[]): Promise<number> {
  const results = await Promise.all(
    invoices.map(inv => fetch(`/api/process/${inv.amount}`)),
  );
  return invoices.reduce((sum, inv) => sum + inv.amount, 0);
}
```

### Pattern 2: Accidental mutation in callbacks

```typescript
// ❌ Without immutability: callback mutates original
function applyDiscounts(items: Item[], discount: number) {
  return items.map(item => {
    item.price *= discount; // ❌ Mutates original!
    return item;
  });
}

const shoppingCart = [{ name: "A", price: 100 }];
const discounted = applyDiscounts(shoppingCart, 0.9);
console.log(shoppingCart[0].price); // 90 — shoppingCart was mutated!

// ✅ With readonly: mutation is a compile error
function applyDiscountsSafe(items: ReadonlyArray<Item>, discount: number): Item[] {
  return items.map(item => ({ ...item, price: item.price * discount }));
  // item.price *= discount; // ❌ Error: Cannot assign to 'price'
}
```

### Pattern 3: Stale closures capturing mutated objects

```typescript
// ❌ Without immutability: event handler captures mutated state
function createComponent(data: { value: number }) {
  const state = { data };
  let handler: () => void;

  // First handler captures reference to state.data
  handler = () => console.log(state.data.value);

  // State mutation affects all handlers
  state.data.value = 100;
  return handler;
}

const comp1 = createComponent({ value: 10 });
const comp2 = createComponent({ value: 20 });
comp1(); // Unpredictable! Shared reference

// ✅ With immutability: each creation returns new immutable value
function createComponent(data: Readonly<{ value: number }>) {
  function handler(): void {
    return console.log(data.value); // ✅ Captures immutable reference
  }
  return handler;
}
```

### Pattern 4: Debugging hell with time-travel debugging

```typescript
// ❌ Without immutability: debug state differs from runtime state
const state = { user: { name: "Alice" } };
function logState(label: string) {
  console.log(`${label}:`, state); // Log takes snapshot
}
logState("Before");
state.user.name = "Bob"; // Mutation
logState("After");
// Logs show mutated values — cannot reconstruct initial state!

// ✅ With immutability: state changes create new objects
let state: ImmutableState = { user: { name: "Alice" } };
function logState(label: string) {
  console.log(`${label}:`, state); // Each snapshot is immutable
}
logState("Before");
state = { ...state, user: { ...state.user, name: "Bob" } }; // New object
logState("After");
// Can reconstruct exact state at any point
```
