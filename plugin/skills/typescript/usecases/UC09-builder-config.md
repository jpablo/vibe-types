# Builder and DSL Patterns

## The Constraint

DSL and builder patterns must make invalid compositions or missing required steps into compile errors. A builder that has not completed all required stages must not expose the terminal method; calling steps out of order must be rejected by the type checker before the code runs.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Typestate** | Encode builder stage in a phantom type parameter; each transition changes the type | [-> T57](../catalog/T57-typestate.md) |
| **Phantom types** | Carry stage information in the type without a runtime representation | [-> T27](../catalog/T27-erased-phantom.md) |
| **Polymorphic `this`** | Fluent chains on subclasses return the subclass type, not the base type | [-> T33](../catalog/T33-self-type.md) |
| **Literal types** | Config keys typed as string literals enable autocomplete and prevent typos | [-> T52](../catalog/T52-literal-types.md) |
| **Template literal types** | Compose route or path strings from parts with full type-level checking | [-> T63](../catalog/T63-template-literal-types.md) |

## Patterns

### Pattern A — Config defaults with `Partial<T>` and object spread

The most common TypeScript configuration pattern: define a complete defaults object, accept `Partial<T>` overrides, and merge with spread. Callers supply only what they need to change.

```typescript
interface ServerConfig {
  host: string;
  port: number;
  maxConnections: number;
  logLevel: "debug" | "info" | "warn" | "error";
}

const SERVER_DEFAULTS: ServerConfig = {
  host: "127.0.0.1",
  port: 8080,
  maxConnections: 100,
  logLevel: "info",
};

function createServer(overrides: Partial<ServerConfig> = {}): ServerConfig {
  return { ...SERVER_DEFAULTS, ...overrides };
}

const dev      = createServer({ port: 3000, logLevel: "debug" });
const prod     = createServer({ host: "0.0.0.0", maxConnections: 10_000 });
const defaults = createServer(); // all defaults

// Analogous to Rust's `Default` + struct update `{ port: 3000, ..Default::default() }`.
```

For nested config objects, a `DeepPartial` utility type avoids requiring callers to spell out every nested field:

```typescript
type DeepPartial<T> = T extends object
  ? { [K in keyof T]?: DeepPartial<T[K]> }
  : T;

interface AppConfig {
  server: ServerConfig;
  db: { host: string; port: number; poolSize: number };
  debug: boolean;
}

const APP_DEFAULTS: AppConfig = {
  server: SERVER_DEFAULTS,
  db: { host: "localhost", port: 5432, poolSize: 10 },
  debug: false,
};

function mergeConfig(overrides: DeepPartial<AppConfig>): AppConfig {
  return {
    server: { ...APP_DEFAULTS.server, ...overrides.server },
    db:     { ...APP_DEFAULTS.db,     ...overrides.db },
    debug:  overrides.debug ?? APP_DEFAULTS.debug,
  };
}

const staging = mergeConfig({
  server: { host: "staging.example.com" },
  db:     { dbName: "app_staging", poolSize: 5 },  // error: 'dbName' does not exist
  debug:  true,
});
```

Note: `DeepPartial` is a convenience utility, not in the standard library. For production use prefer `zod` or similar to get runtime validation alongside the type.

### Pattern B — Validated smart constructor

Combine a branded type with a factory function to enforce invariants at construction time. The return type is a discriminated union so callers must handle the error case.

```typescript
declare const __brand: unique symbol;
type Brand<T, B> = T & { readonly [__brand]: B };

type Port = Brand<number, "Port">;
type Host = Brand<string, "Host">;

type ListenConfig = { host: Host; port: Port };

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function mkPort(n: number): Port | null {
  return n > 0 && n < 65_536 ? (n as Port) : null;
}

function mkHost(s: string): Host | null {
  return s.length > 0 ? (s as Host) : null;
}

function mkListenConfig(
  host = "localhost",
  port = 8080,
): Result<ListenConfig> {
  const h = mkHost(host);
  if (!h) return { ok: false, error: "host cannot be empty" };
  const p = mkPort(port);
  if (!p) return { ok: false, error: `invalid port: ${port}` };
  return { ok: true, value: { host: h, port: p } };
}

const result = mkListenConfig("0.0.0.0", 443);
if (result.ok) {
  result.value.port; // Port — branded; cannot be an arbitrary number
}

mkListenConfig("localhost", 0).ok;  // false — "invalid port: 0"
mkListenConfig("", 8080).ok;        // false — "host cannot be empty"

// A raw number cannot be passed where Port is expected:
function listen(cfg: ListenConfig) { /* ... */ }
listen({ host: "localhost" as Host, port: 8080 }); // error: 8080 not assignable to Port
```

### Pattern C — Fluent builder with `this` return type

Using `this` as the return type of each builder method lets subclasses participate in the fluent chain without losing their specific type. The derived class's extra methods remain visible after each chained call.

```typescript
class QueryBuilder {
  protected _table  = "";
  protected _where  = "";
  protected _limit  = 0;

  from(table: string): this {
    this._table = table;
    return this;
  }

  where(condition: string): this {
    this._where = condition;
    return this;
  }

  limit(n: number): this {
    this._limit = n;
    return this;
  }

  build(): string {
    let sql = `SELECT * FROM ${this._table}`;
    if (this._where) sql += ` WHERE ${this._where}`;
    if (this._limit)  sql += ` LIMIT ${this._limit}`;
    return sql;
  }
}

class AuditedQueryBuilder extends QueryBuilder {
  private _auditUser = "";

  auditedBy(user: string): this {
    this._auditUser = user;
    return this;
  }

  build(): string {
    return super.build() + ` /* audited by ${this._auditUser} */`;
  }
}

const query = new AuditedQueryBuilder()
  .from("orders")
  .where("status = 'open'")
  .auditedBy("alice")  // OK — still AuditedQueryBuilder after .where()
  .limit(100)
  .build();
// "SELECT * FROM orders WHERE status = 'open' LIMIT 100 /* audited by alice */"

// Base builder does not have auditedBy:
const base = new QueryBuilder()
  .from("orders")
  .auditedBy("alice"); // error: Property 'auditedBy' does not exist on type 'QueryBuilder'
```

### Pattern D — Typestate builder enforcing required stages

A phantom type parameter tracks which stages have been completed. The terminal method `send()` only exists on `RequestBuilder<WithUrl & WithMethod>`. Attempting to call it before setting both URL and method is a compile error.

```typescript
declare const __state: unique symbol;
type HasState<S> = { readonly [__state]: S };

// Stage markers (erased at runtime):
type NoUrl     = HasState<"NoUrl">;
type WithUrl   = HasState<"WithUrl">;
type NoMethod  = HasState<"NoMethod">;
type WithMethod = HasState<"WithMethod">;

// Intersection encodes "both stages completed":
type Ready = WithUrl & WithMethod;

class RequestBuilder<Stage> {
  private _url    = "";
  private _method = "GET";
  private _body: unknown = undefined;

  // Each setter returns a new stage — the intersection accumulates:
  url(u: string): RequestBuilder<Stage & WithUrl> {
    this._url = u;
    return this as unknown as RequestBuilder<Stage & WithUrl>;
  }

  method(m: "GET" | "POST" | "PUT" | "DELETE"): RequestBuilder<Stage & WithMethod> {
    this._method = m;
    return this as unknown as RequestBuilder<Stage & WithMethod>;
  }

  body(data: unknown): this {
    this._body = data;
    return this;
  }
}

// send() only exists when both url() and method() have been called:
interface ReadyRequestBuilder extends RequestBuilder<Ready> {
  send(): Promise<Response>;
}

function makeRequest(): RequestBuilder<NoUrl & NoMethod> {
  return new RequestBuilder<NoUrl & NoMethod>();
}

function withSend(b: RequestBuilder<Ready>): ReadyRequestBuilder {
  return Object.assign(b, {
    send(): Promise<Response> {
      return fetch((b as any)._url, { method: (b as any)._method });
    },
  }) as ReadyRequestBuilder;
}

const builder = makeRequest();

// Must set both url and method before calling send:
const ready = withSend(
  builder
    .url("https://api.example.com/users")
    .method("POST")
    .body({ name: "Alice" })
);
ready.send(); // OK

// Missing url — Stage does not extend Ready:
const incomplete = builder.method("GET");
withSend(incomplete); // error: RequestBuilder<WithMethod> is not assignable to RequestBuilder<Ready>
```

### Pattern E — Config object with `satisfies` for literal preservation

`satisfies` validates that a value matches a type while preserving the literal types of its fields. Autocomplete works on the specific literals; the schema enforces no unknown keys.

```typescript
type HttpMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
type LogLevel   = "debug" | "info" | "warn" | "error";

type ServerConfig = {
  readonly host: string;
  readonly port: number;
  readonly allowedMethods: readonly HttpMethod[];
  readonly logLevel: LogLevel;
  readonly features: Record<string, boolean>;
};

// satisfies: validates shape AND preserves literal types:
const config = {
  host: "0.0.0.0",
  port: 8080,
  allowedMethods: ["GET", "POST", "PUT"] as const,
  logLevel: "info",
  features: {
    rateLimit: true,
    cors: false,
    compression: true,
  },
} satisfies ServerConfig;

// Literal types are preserved (not widened to string):
config.logLevel;            // type: "info"    (not LogLevel)
config.allowedMethods[0];   // type: "GET"     (not HttpMethod)
config.features.rateLimit;  // type: boolean

// Invalid values caught at the satisfies site:
const bad = {
  host: "localhost",
  port: 3000,
  allowedMethods: ["CONNECT"] as const, // error: "CONNECT" is not assignable to HttpMethod
  logLevel: "verbose",                  // error: "verbose" is not assignable to LogLevel
  features: {},
} satisfies ServerConfig;

// Template literal types compose route paths with type safety:
type ApiVersion = "v1" | "v2";
type Resource   = "users" | "orders" | "products";
type ApiRoute   = `/api/${ApiVersion}/${Resource}`;

const route: ApiRoute = "/api/v1/users";    // OK
const bad2: ApiRoute  = "/api/v3/users";    // error: "v3" is not a valid ApiVersion
const bad3: ApiRoute  = "/api/v1/invoices"; // error: "invoices" is not a valid Resource
```

### Pattern F — Discriminated-union expression DSL

When a DSL needs to represent a typed expression tree (rather than mutating builder state), discriminated unions play the role that GADTs fill in Scala or Lean. Each node carries its result type as a generic parameter, and the evaluator is total and type-safe.

```typescript
// Each variant is tagged and carries its type parameter in the shape of the value:
type Expr<A> =
  | { kind: "lit";    value: number }    // Expr<number>
  | { kind: "str";    value: string }    // Expr<string>
  | { kind: "gt";     lhs: Expr<number>; rhs: Expr<number> }  // Expr<boolean>
  | { kind: "if";     cond: Expr<boolean>; yes: Expr<A>; no: Expr<A> }
  | { kind: "concat"; a: Expr<string>; b: Expr<string> };     // Expr<string>

// Smart constructors prevent misuse without extra runtime checks:
const lit    = (value: number): Expr<number>  => ({ kind: "lit", value });
const str    = (value: string): Expr<string>  => ({ kind: "str", value });
const gt     = (lhs: Expr<number>, rhs: Expr<number>): Expr<boolean> => ({ kind: "gt", lhs, rhs });
const ifExpr = <A>(cond: Expr<boolean>, yes: Expr<A>, no: Expr<A>): Expr<A> =>
  ({ kind: "if", cond, yes, no });
const concat = (a: Expr<string>, b: Expr<string>): Expr<string> => ({ kind: "concat", a, b });

function evaluate<A>(expr: Expr<A>): A {
  switch (expr.kind) {
    case "lit":    return expr.value as A;
    case "str":    return expr.value as A;
    case "gt":     return (evaluate(expr.lhs) > evaluate(expr.rhs)) as A;
    case "if":     return evaluate(expr.cond) ? evaluate(expr.yes) : evaluate(expr.no);
    case "concat": return (evaluate(expr.a) + evaluate(expr.b)) as A;
  }
}

const program: Expr<string> = ifExpr(
  gt(lit(10), lit(5)),
  str("big"),
  str("small"),
);

const result: string = evaluate(program); // "big"

// Type mismatch caught at construction time:
// ifExpr(gt(lit(1), lit(2)), lit(0), str("x")); // error: Expr<number> not assignable to Expr<string>
```

TypeScript lacks true GADTs: the `as A` casts in `evaluate` are necessary because the compiler cannot yet narrow a generic through a discriminant. The smart constructors compensate by preventing ill-typed trees from being built in the first place.

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| `Partial<T>` + spread defaults (A) | Zero boilerplate; familiar to all JS/TS developers | No validation; deep nesting needs a `DeepPartial` utility |
| Validated smart constructor (B) | Invariants enforced at construction; branded types prevent misuse downstream | Callers must unwrap `Result`; more boilerplate than plain objects |
| `this` return type fluent builder (C) | Subclass-safe chaining; lightest-weight | No required-field enforcement; all methods always accessible |
| Typestate builder (D) | Missing required fields are compile errors | Verbose; combinatorial state types for many required fields |
| `satisfies` config (E) | Validates shape AND preserves literal types; no type widening | Requires TypeScript 4.9+; only catches structural mismatches, not semantic ones |
| Discriminated-union expression DSL (F) | Typed tree structure; total evaluator; ill-typed programs rejected at construction | `as A` casts needed in evaluator; TypeScript cannot fully narrow generics via discriminants |

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Config defaults | Spread + object merge; typos in override keys silently ignored | `Partial<T>` constrains overrides to known keys; unknown keys are type errors |
| Config validation | Runtime checks in a factory function; errors surface at runtime | Smart constructors + branded types; invalid configs cannot be passed to functions expecting the branded type |
| Fluent builder | Methods return `this`; subclass methods invisible after base methods return `this` typed as base | `this` return type preserves the subclass; derived methods remain callable throughout the chain |
| Required builder stages | `send()` always present; throws at runtime if `url` was never set | Typestate phantom parameter; `send()` only exists on the fully-staged type; missing stage is a compile error |
| Config objects | Plain object literals; typos in keys discovered at runtime; no autocomplete on string fields | `satisfies` validates shape and preserves literals; autocomplete on known keys; bad values caught immediately |
| Route paths | Strings constructed by concatenation; wrong path components discovered by the server | Template literal types constrain each path segment; invalid combinations are type errors |

## When to Use Which Feature

**`Partial<T>` + spread** (Pattern A) is the default for any API that accepts optional overrides of a known config shape. Add `DeepPartial` when nesting is deep. Use `satisfies` alongside the defaults object to catch typos on the defaults themselves.

**Validated smart constructor** (Pattern B) when a config has invariants — valid port ranges, non-empty strings, mutually dependent fields. Pair with branded types so validated values cannot be substituted with raw unvalidated ones downstream.

**`this` return type** (Pattern C) is the lightest-weight fluent builder option. Use it for simple fluent builders where all methods are always valid regardless of call order. It composes naturally with inheritance.

**Typestate builder** (Pattern D) is the right choice when there is a strictly ordered protocol — certain methods must be called before others become available. The phantom type accumulates completed stages as an intersection; the terminal method is gated on the full intersection.

**`satisfies`** (Pattern E) is best for configuration objects: it provides schema validation without widening the literal types that autocomplete and downstream code depend on. Pair it with `as const` on array fields to preserve tuple and literal element types.

**Template literal types** belong on any configuration or DSL where strings are built from a known set of parts. The type system validates each segment independently, turning runtime 404s and misrouted requests into compile-time errors.

**Discriminated-union expression DSL** (Pattern F) when you need a typed expression tree — a query language, a rule engine, or a filter pipeline — where ill-typed expressions must be rejected at construction time. Use smart constructors to compensate for TypeScript's lack of full GADT support.

**Combine patterns**: a `Partial<T>` merge (A) for the outer config shape, smart constructors with branded types (B) for fields with invariants, and `satisfies` (E) to validate the defaults object itself.
