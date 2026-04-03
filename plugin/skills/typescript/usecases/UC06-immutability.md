# Immutability

## The Constraint

Prevent mutation of values after construction. The compiler rejects assignments to readonly properties and mutations of readonly arrays, making accidental in-place modification a compile error rather than a runtime surprise.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **readonly / as const** | Mark individual properties or entire object trees as immutable | [-> T32](../catalog/T32-immutability-markers.md) |
| **Readonly record properties** | Declare each field of a type as non-writable | [-> T31](../catalog/T31-record-types.md) |
| **Mapped types** | Derive `DeepReadonly<T>` that recursively marks every nested property readonly | [-> T62](../catalog/T62-mapped-types.md) |

## Patterns

### Pattern A — readonly properties on an interface

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

### Pattern B — as const for configuration objects

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

### Pattern C — Readonly<T> utility type

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
  // To prevent this, use DeepReadonly (Pattern D) or readonly string[] in the type definition
}
```

### Pattern D — Deep readonly with a recursive mapped type

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

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Property immutability | `Object.freeze()` — runtime enforcement, throws in strict mode, silent otherwise; not recursive by default | `readonly` field — compile-time enforcement; no runtime cost; IDE highlights violations immediately |
| Constant configuration | `const obj = { … }` — only the binding is const; `obj.port = 99` works silently | `as const` — every field is readonly and has a literal type; mutations are compile errors |
| Function non-mutation contract | JSDoc comment `@param {Object} user - do not mutate` — ignored by the engine | `Readonly<User>` parameter type — mutation inside the function is a compile error |
| Deep immutability | `deepFreeze()` utility — runtime only, missed in tests, no type feedback | `DeepReadonly<T>` — full structural compile-time guarantee at zero runtime cost |

## When to Use Which Feature

**readonly on interface fields** (Pattern A) is the default. Apply it to every field of a domain type unless mutation is explicitly required. Pair `readonly` on the property with `readonly T[]` for array fields to prevent both reassignment and in-place mutation.

**as const** (Pattern B) is the right tool for all compile-time constants: enum-like string arrays, configuration objects, and routing tables. It is lighter than a full type annotation and gives the narrowest possible literal types for free.

**Readonly<T>** (Pattern C) belongs on function parameter types when the function should not mutate its argument but the type itself is defined elsewhere (e.g., a mutable ORM entity). It documents the contract at the call site without changing the type definition.

**DeepReadonly<T>** (Pattern D) is the right choice for Redux-style application state, configuration loaded once at startup, and any deeply nested value that must be treated as immutable throughout a codebase. Define it once in a shared utilities module and apply it to state types.
