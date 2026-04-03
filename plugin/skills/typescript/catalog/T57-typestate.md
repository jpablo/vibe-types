# Typestate Pattern

> **Since:** TypeScript community pattern; phantom types via branded types

## 1. What It Is

The typestate pattern encodes **valid state transitions in the type system** using phantom type parameters. A generic type `Builder<State>` carries a phantom type parameter `State` that tracks which step of a protocol has been completed. Each method returns a *new* builder type with the phantom parameter advanced to the next state. Methods that are only valid in a particular state are simply absent from the type (or constrained to that state), so calling them in the wrong state is a compile-time error rather than a runtime exception. Because TypeScript uses structural typing, the phantom parameter must be **genuinely structurally distinct** to prevent accidental assignability across states — a bare type alias is not enough. The standard technique is to use branded types (an intersection with a unique `readonly _brand` property) or, for simplicity, an object type with a discriminant-like field that exists only in the type and not at runtime (erased phantom). The pattern is especially useful for builder APIs, connection lifecycle management, and multi-step workflows where skipping or repeating a step is a logic error.

## 2. What Constraint It Lets You Express

**~Achievable — the compiler prevents calling methods out of order and prevents skipping required steps; invalid sequences are type errors with no runtime overhead.**

- A `Connection<Closed>` value does not have a `query()` method in its type; calling it is an error.
- Advancing state is explicit: `connect()` returns `Connection<Open>`, and only `Connection<Open>` has `query()`.
- `send()` on an HTTP request builder is only accessible after `setUrl()` has been called, enforced structurally.

## 3. Minimal Snippet

```typescript
// --- Phantom state brands (erased at runtime) ---
declare const _brand: unique symbol;
type Brand<B> = { readonly [_brand]: B };

// State markers — exist only at the type level
type Unset    = Brand<"Unset">;
type WithUrl  = Brand<"WithUrl">;
type WithBody = Brand<"WithBody">;
type Ready    = Brand<"Ready">;

// Request builder with phantom state parameter
class RequestBuilder<State> {
  // The phantom parameter is never stored; it is purely for the type checker
  private constructor(
    private readonly _url: string = "",
    private readonly _body: string = "",
  ) {}

  static create(): RequestBuilder<Unset> {
    return new RequestBuilder<Unset>();
  }

  // Only callable when State = Unset; returns a new type with WithUrl state
  setUrl(url: string): RequestBuilder<WithUrl> {
    return new RequestBuilder<WithUrl>(url, this._body);
  }
}

// Separate interface for the "URL is set" state — adds setBody
interface RequestBuilder<State extends WithUrl | WithBody | Ready> {
  setBody(body: string): RequestBuilder<WithBody>;
}

// Separate interface for the "body is set" state — adds send
interface RequestBuilder<State extends WithBody | Ready> {
  send(): Promise<Response>;
}

// Usage
const req = RequestBuilder.create()  // RequestBuilder<Unset>
  .setUrl("https://api.example.com") // RequestBuilder<WithUrl>
  .setBody('{"key":"value"}')        // RequestBuilder<WithBody>
  .send();                           // Promise<Response>  // OK

// const bad = RequestBuilder.create().send(); // error — send() does not exist on RequestBuilder<Unset>
// const bad2 = RequestBuilder.create().setBody("x"); // error — setBody requires WithUrl state

// --- Simpler pattern: separate types per state ---
type DbClosed = { readonly _state: "closed" };
type DbOpen   = { readonly _state: "open"; query(sql: string): Promise<unknown[]> };

function openDb(): DbOpen {
  return { _state: "open", query: async (sql) => [] };
}

function closeDb(db: DbOpen): DbClosed {
  return { _state: "closed" };
}

const db = openDb();          // DbOpen
const result = db.query("SELECT 1"); // OK
const closed = closeDb(db);   // DbClosed
// closed.query("SELECT 1");  // error — query does not exist on DbClosed
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Phantom / Erased Types** [-> T27](T27-erased-phantom.md) | Phantom type parameters are the mechanism that carries state information; they exist only in the type checker and are erased at runtime, adding zero overhead. |
| **Newtypes & Opaque Types** [-> T03](T03-newtypes-opaque.md) | Branded types (a technique from the newtype pattern) make phantom state parameters structurally distinct so TypeScript's structural typing cannot accidentally treat one state as another. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | State-dependent methods are expressed as method signatures that appear only on the type parameterized to a specific state; conditional availability is encoded in the type, not via runtime guards. |
| **Algebraic Data Types** [-> T01](T01-algebraic-data-types.md) | An alternative to phantom types: represent each state as a separate discriminated union variant, with state-specific methods implemented as freestanding functions that accept the correct variant. |

## 5. Gotchas and Limitations

1. **Structural typing undermines phantom safety** — if two state types are structurally identical (e.g., both are `{}`), TypeScript will treat them as interchangeable, defeating the typestate guarantee. Always use unique brands.
2. **Interface merging trick is fragile** — the pattern of adding methods via `interface RequestBuilder<State extends ...>` relies on declaration merging; it is not always intuitive and can produce confusing error messages.
3. **No runtime enforcement** — typestate is purely a type-level fiction; a cast (`as any as RequestBuilder<WithBody>`) bypasses all safety. The pattern trusts that the API is not misused via unsound casts.
4. **Builder instances are not reusable across states** — returning `new RequestBuilder<NextState>(...)` creates a new object; the old object still exists but its type at the variable declaration is now stale. Reassigning the variable is idiomatic.
5. **Generic state parameters complicate type inference** — TypeScript sometimes widens the inferred state parameter; explicit type annotations at creation or cast-like helper functions (`as RequestBuilder<Unset>`) may be needed.
6. **Error messages are poor** — when a method is missing due to a wrong state, the error says "property does not exist," not "you must call `setUrl` first"; documentation and naming conventions are essential.

## 6. Use-Case Cross-References

- [-> UC-13](../usecases/UC13-state-machines.md) Encode state machine valid transitions so invalid transitions are compile errors
- [-> UC-09](../usecases/UC09-builder-config.md) Builder APIs that enforce required configuration steps before building
- [-> UC-01](../usecases/UC01-invalid-states.md) Prevent invalid states by making them unrepresentable in the type system
