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

## 4. Beginner Mental Model

Think of typestate as a **laminated badge system** in a building. A visitor with a `Lobby` badge cannot enter the server room — the method doesn't appear on their type. Handing the badge to security (`connect()`) swaps it for a `ServerRoom` badge. You can't enter the server room with the old badge, and you can't use the new badge where a `Lobby` badge is required. The compiler is the door scanner: it checks the badge type at every doorway. At runtime the badges are invisible — they cost nothing and leave no trace in the emitted JavaScript.

Coming from Rust: TypeScript has no ownership, so calling a transition method does **not** consume the old value. The old variable still exists with the old type in scope, and nothing prevents using it. Discipline (rebinding the variable) is required instead.

## 5. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Phantom / Erased Types** [-> T27](T27-erased-phantom.md) | Phantom type parameters are the mechanism that carries state information; they exist only in the type checker and are erased at runtime, adding zero overhead. |
| **Newtypes & Opaque Types** [-> T03](T03-newtypes-opaque.md) | Branded types (a technique from the newtype pattern) make phantom state parameters structurally distinct so TypeScript's structural typing cannot accidentally treat one state as another. |
| **Literal Types** [-> T52](T52-literal-types.md) | String literal types (e.g., `"open"`, `"closed"`) can serve as state tags when used as a discriminant field (`readonly _state: "open"`). They are simpler than brands but require a runtime-visible field. |
| **Generics and Bounds** [-> T04](T04-generics-bounds.md) | The state phantom is a generic parameter. `impl`-like specialization is done with overloaded interfaces or conditional types restricted to a particular state extends-bound. |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | After a state-transition function returns the new state type, the checker narrows the variable to the new state. Discriminated-union state models use narrowing directly; phantom-type models rely on the transition return type. |
| **Union / Intersection Types** [-> T02](T02-union-intersection.md) | A method that is valid in multiple states can accept a union: `db: Db<Connected \| Authenticated>`. Union state tags express "either state is acceptable" without duplicating the method. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | State-dependent methods are expressed as method signatures that appear only on the type parameterized to a specific state; conditional availability is encoded in the type, not via runtime guards. |
| **Algebraic Data Types** [-> T01](T01-algebraic-data-types.md) | An alternative to phantom types: represent each state as a separate discriminated union variant, with state-specific methods implemented as freestanding functions that accept the correct variant. |

## 6. Gotchas and Limitations

1. **Structural typing undermines phantom safety** — if two state types are structurally identical (e.g., both are `{}`), TypeScript will treat them as interchangeable, defeating the typestate guarantee. Always use unique brands.
2. **No linear types — stale references survive transitions.** Unlike Rust, TypeScript has no ownership. After `const conn2 = conn.connect()`, the old `conn` variable still exists with type `Connection<Disconnected>`. Nothing prevents accidentally calling methods on it. Always rebind: `let conn = conn.connect()` and avoid keeping references to the old value.
3. **Interface merging trick is fragile** — the pattern of adding methods via `interface RequestBuilder<State extends ...>` relies on declaration merging; it is not always intuitive and can produce confusing error messages.
4. **No runtime enforcement** — typestate is purely a type-level fiction; a cast (`as any as RequestBuilder<WithBody>`) bypasses all safety. The pattern trusts that the API is not misused via unsound casts.
5. **Cannot store in homogeneous collections** — `Connection<Connected>` and `Connection<Authenticated>` are different types. A `Connection<Connected>[]` cannot hold authenticated connections. Use a discriminated-union wrapper or a base interface to hold mixed states, at the cost of losing state-specific method availability.
6. **Combinatorial state explosion** — multiple independent state dimensions (e.g., `Conn<Auth, Encrypted, Pooled>`) multiply the number of phantom type combinations. Prefer a single phantom union type or split state into separate helper builders when dimensions grow.
7. **Generic state parameters complicate type inference** — TypeScript sometimes widens the inferred state parameter; explicit type annotations at creation or cast-like helper functions (`as RequestBuilder<Unset>`) may be needed.
8. **Error messages are poor** — when a method is missing due to a wrong state, the error says "property does not exist," not "you must call `setUrl` first"; documentation and naming conventions are essential.

## 7. Example A — File Handle with Read/Write Mode Enforcement

```typescript
declare const _brand: unique symbol;
type Brand<B> = { readonly [_brand]: B };

type ReadMode  = Brand<"read">;
type WriteMode = Brand<"write">;

class TypedFile<Mode> {
  private constructor(private readonly path: string) {}

  static openRead(path: string): TypedFile<ReadMode> {
    return new TypedFile<ReadMode>(path);
  }
  static openWrite(path: string): TypedFile<WriteMode> {
    return new TypedFile<WriteMode>(path);
  }
}

// Mode-specific operations live on separate overloaded interfaces
interface TypedFile<Mode extends ReadMode> {
  readLine(): string;
}
interface TypedFile<Mode extends WriteMode> {
  writeLine(line: string): void;
}

const rf = TypedFile.openRead("data.txt");
rf.readLine();         // OK
// rf.writeLine("x");  // error: writeLine does not exist on TypedFile<ReadMode>

const wf = TypedFile.openWrite("out.txt");
wf.writeLine("hello"); // OK
// wf.readLine();       // error: readLine does not exist on TypedFile<WriteMode>
```

## 8. Example B — Connection Protocol with Three-Phase Lifecycle

```typescript
declare const _state: unique symbol;
type StateTag<S extends string> = { readonly [_state]: S };

type Idle          = StateTag<"idle">;
type Connected     = StateTag<"connected">;
type Authenticated = StateTag<"authenticated">;

class HttpConn<S> {
  private constructor(private readonly host: string) {}

  static create(host: string): HttpConn<Idle> {
    return new HttpConn<Idle>(host);
  }
}

interface HttpConn<S extends Idle> {
  connect(): HttpConn<Connected>;
}
interface HttpConn<S extends Connected> {
  authenticate(token: string): HttpConn<Authenticated>;
  disconnect(): HttpConn<Idle>;
}
interface HttpConn<S extends Authenticated> {
  fetch(path: string): Promise<string>;
  disconnect(): HttpConn<Idle>;
}

// Valid sequence:
async function example() {
  const data = await HttpConn.create("api.example.com")
    .connect()
    .authenticate("tok-abc")
    .fetch("/users");
  // HttpConn.create("x").fetch("/")  // error: fetch does not exist on HttpConn<Idle>
}
```

## 9. Use-Case Cross-References

- [-> UC-01](../usecases/UC01-invalid-states.md) Prevent invalid states by making them unrepresentable in the type system
- [-> UC-08](../usecases/UC08-error-handling.md) Protocol violations become compile-time errors instead of runtime exceptions
- [-> UC-09](../usecases/UC09-builder-config.md) Builder APIs that enforce required configuration steps before building
- [-> UC-11](../usecases/UC11-effect-tracking.md) Track resource lifecycle (open/closed, connected/authenticated) at the type level
- [-> UC-13](../usecases/UC13-state-machines.md) Encode state machine valid transitions so invalid transitions are compile errors

## Source Anchors

- [TypeScript Handbook — Declaration Merging](https://www.typescriptlang.org/docs/handbook/declaration-merging.html) (interface merging used for per-state methods)
- [TypeScript Handbook — Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html)
- [TypeScript Deep Dive — Nominal Typing](https://basarat.gitbook.io/typescript/main-1/nominaltyping) (branded type technique)
- [Rust Design Patterns — Typestate](https://rust-unofficial.github.io/patterns/patterns/behavioural/typestate.html) (for comparison; same concept, stricter via ownership)
