# Nullability

## The Constraint

`null` and `undefined` cannot be silently ignored. Any value that may be absent must be handled explicitly before it is used; dereference without a null check is a compile error.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Null safety / strictNullChecks** | Opt-in compiler flag that makes `null` and `undefined` distinct types that cannot flow into non-nullable positions | [-> T13](../catalog/T13-null-safety.md) |
| **Type narrowing** | Refine `T \| null` to `T` inside a null-check branch | [-> T14](../catalog/T14-type-narrowing.md) |
| **Union types** | `T \| null` and `T \| undefined` are explicit union types — absence is encoded in the type | [-> T02](../catalog/T02-union-intersection.md) |
| **`never` bottom type** | Reaching a `never` position after exhaustive null handling confirms the type checker agrees the path is impossible | [-> T34](../catalog/T34-never-bottom.md) |

## Patterns

### Pattern A — `--strictNullChecks` basic: explicit `string | null`

With `--strictNullChecks` enabled, `null` and `undefined` are not assignable to any type by default. A variable that may be null must be declared as `T | null`; using it without a check is a compile error.

```typescript
// tsconfig.json: { "compilerOptions": { "strict": true } }
// strict: true implies strictNullChecks: true

function getDisplayName(user: { name: string | null; email: string }): string {
  // Dereference without check is a compile error:
  return user.name.toUpperCase(); // error: Object is possibly 'null'

  // Must narrow first:
  if (user.name !== null) {
    return user.name.toUpperCase(); // OK — narrowed to string
  }
  return user.email;
}

// null is not assignable to a non-nullable type:
const name: string = null; // error: Type 'null' is not assignable to type 'string'
const safeName: string | null = null; // OK

// Functions that return null are explicit about it:
function findConfig(key: string, env: Record<string, string>): string | null {
  return env[key] ?? null;
}

const value = findConfig("DB_URL", process.env as Record<string, string>);
value.startsWith("postgres://"); // error: Object is possibly 'null'

if (value !== null) {
  value.startsWith("postgres://"); // OK
}
```

### Pattern B — Optional chaining `?.` for nested nullable access

`?.` short-circuits the entire chain to `undefined` at the first `null` or `undefined` link. No runtime error is thrown; the result type is automatically widened to `T | undefined`.

```typescript
type Address = {
  street: string;
  city: string;
  country?: {
    code: string;
    name: string;
  };
};

type User = {
  id: string;
  name: string;
  address?: Address;
};

type Order = {
  id: string;
  user?: User;
};

function getCountryCode(order: Order): string | undefined {
  // Each ?. is a guarded access — no null check boilerplate:
  return order.user?.address?.country?.code;
}

// Equivalent without optional chaining (the old way):
function getCountryCodeVerbose(order: Order): string | undefined {
  if (order.user === undefined) return undefined;
  if (order.user.address === undefined) return undefined;
  if (order.user.address.country === undefined) return undefined;
  return order.user.address.country.code;
}

// Optional method calls:
type Logger = { log?: (msg: string) => void };
declare const logger: Logger;
logger.log?.("hello"); // calls log if present; does nothing if absent — no error
```

### Pattern C — Nullish coalescing `??` for default values

`??` provides a default only for `null` and `undefined` — unlike `||`, it does not trigger on `0`, `""`, or `false`. Use it to collapse `T | null | undefined` down to `T`.

```typescript
function buildConnectionString(
  host: string | null,
  port: number | null | undefined,
  database: string | undefined,
): string {
  const h = host     ?? "localhost";  // null → default; "db.prod" → "db.prod"
  const p = port     ?? 5432;         // undefined → default; 0 → 0 (not || behavior)
  const db = database ?? "app";

  return `postgres://${h}:${p}/${db}`;
}

buildConnectionString(null, undefined, undefined); // "postgres://localhost:5432/app"
buildConnectionString("db.prod", 0, "mydb");       // "postgres://db.prod:0/mydb"
// Note: port 0 is preserved because ?? checks null/undefined, not falsiness

// Chained coalescing:
declare const primary: string | null;
declare const secondary: string | null;
declare const fallback: string;

const value: string = primary ?? secondary ?? fallback; // type is string — null eliminated
```

### Pattern D — Non-null assertion `!` as an escape hatch

The `!` postfix operator tells the type checker "I know this is not null or undefined." It is an escape hatch — no runtime check is performed. Use it only at boundaries where context guarantees non-nullness but the type system cannot infer it.

```typescript
// Acceptable: DOM lookup that is guaranteed by the page structure:
const rootEl = document.getElementById("app")!; // HTMLElement, not HTMLElement | null
rootEl.innerHTML = "<p>Hello</p>"; // OK — no null check needed

// Acceptable: value initialized lazily, accessed only after initialization:
class Config {
  private _dsn!: string; // definite assignment assertion — set in init()

  init(dsn: string): void {
    this._dsn = dsn;
  }

  getDsn(): string {
    return this._dsn; // safe only if init() was called first
  }
}

// Avoid: using ! to paper over a genuine nullability problem:
function processUser(user: User | null): string {
  return user!.name; // bad — crashes if user is actually null
  // Better:
  // if (user === null) throw new Error("user is required");
  // return user.name;
}

// Rule of thumb: if you find yourself using ! frequently, restructure so that
// the non-null value is guaranteed by the type — use a Result or narrow earlier.
```

### Pattern E — Parse, don't validate — return `T | null` from lookup

Instead of throwing on a missing value, return `T | null`. Callers who need the value are forced to handle the null case. This is the optionality equivalent of the broader parse-don't-validate principle. See [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/).

```typescript
type User = { id: string; name: string; role: "admin" | "member" };

// Returns null on miss — callers cannot pretend the user always exists:
function findUser(id: string, users: readonly User[]): User | null {
  return users.find(u => u.id === id) ?? null;
}

function requireUser(id: string, users: readonly User[]): User {
  const user = findUser(id, users);
  if (user === null) throw new Error(`User not found: ${id}`);
  return user; // type is User — the null has been handled
}

const users: User[] = [
  { id: "u1", name: "Alice", role: "admin" },
  { id: "u2", name: "Bob",   role: "member" },
];

const alice = findUser("u1", users);
alice.name;   // error: Object is possibly 'null'

if (alice !== null) {
  alice.name; // OK — narrowed to User
  alice.role; // OK
}

// requireUser for call sites that genuinely cannot proceed without the user:
const admin = requireUser("u1", users); // User — throws if missing
admin.name; // OK — no null check needed
```

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Missing value | Returns `undefined` silently; `TypeError: Cannot read property 'x' of undefined` at runtime | `T \| null` or `T \| undefined`; dereference without null check is a compile error |
| Nested access | `obj && obj.a && obj.a.b && obj.a.b.c` — verbose and easy to mis-order | `obj?.a?.b?.c` — type is automatically `T \| undefined`; short-circuits cleanly |
| Default values | `value \|\| default` — triggers on `0`, `""`, `false` — silently wrong | `value ?? default` — triggers only on `null` / `undefined`; type collapses to `T` |
| Avoiding nulls | `throw` on miss — caller uses try/catch; error type is `any` | Return `T \| null`; caller must narrow; no try/catch needed for optionality |
| Non-null assertion | Always treated as possibly undefined | `!` postfix explicitly overrides the null check; intention is visible in the source |

## When to Use Which Feature

**Always enable `--strictNullChecks`** (via `"strict": true` in tsconfig). Without it, none of the other patterns provide safety — `null` is assignable everywhere.

**`T | null` vs `T | undefined`**: use `null` for intentional absence (a field that may not have a value); use `undefined` for missing object properties and unset optional parameters. Both require narrowing before use.

**Optional chaining `?.`** (Pattern B) replaces nested null guards. Use it on property chains, method calls, and index accesses. Prefer it over manual `&&` chains.

**Nullish coalescing `??`** (Pattern C) replaces `|| default` for nullable values. Use it instead of `||` whenever the value could legitimately be `0`, `""`, or `false`.

**Non-null assertion `!`** (Pattern D) is an escape hatch for boundaries where context guarantees non-nullness. Use sparingly — each `!` is a claim that the type system cannot verify; a wrong claim crashes at runtime.

**Return `T | null` from lookups** (Pattern E) rather than throwing on miss. The caller decides whether a miss is an error or a normal case; the type forces them to decide rather than letting `undefined` propagate silently.
