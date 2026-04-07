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

### Pattern A — Fluent builder with `this` return type

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

### Pattern B — Typestate builder enforcing required stages

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

### Pattern C — Config object with `satisfies` for literal preservation

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

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Fluent builder | Methods return `this`; subclass methods invisible after base methods return `this` typed as base | `this` return type preserves the subclass; derived methods remain callable throughout the chain |
| Required builder stages | `send()` always present; throws at runtime if `url` was never set | Typestate phantom parameter; `send()` only exists on the fully-staged type; missing stage is a compile error |
| Config objects | Plain object literals; typos in keys discovered at runtime; no autocomplete on string fields | `satisfies` validates shape and preserves literals; autocomplete on known keys; bad values caught immediately |
| Route paths | Strings constructed by concatenation; wrong path components discovered by the server | Template literal types constrain each path segment; invalid combinations are type errors |

## When to Use Which Feature

**`this` return type** (Pattern A) is the lightest-weight option. Use it for simple fluent builders where all methods are always valid regardless of call order. It composes naturally with inheritance.

**Typestate builder** (Pattern B) is the right choice when there is a strictly ordered protocol — certain methods must be called before others become available. The phantom type accumulates completed stages as an intersection; the terminal method is gated on the full intersection.

**`satisfies`** (Pattern C) is best for configuration objects: it provides schema validation without widening the literal types that autocomplete and downstream code depend on. Pair it with `as const` on array fields to preserve tuple and literal element types.

**Template literal types** belong on any configuration or DSL where strings are built from a known set of parts. The type system validates each segment independently, turning runtime 404s and misrouted requests into compile-time errors.
