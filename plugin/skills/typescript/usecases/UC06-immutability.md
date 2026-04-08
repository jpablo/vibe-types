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
