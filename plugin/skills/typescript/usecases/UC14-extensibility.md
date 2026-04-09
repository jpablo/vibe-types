# Extensibility

## The Constraint

New variants or implementations must integrate without modifying existing code. The type system enforces the integration contract; passing an object that does not satisfy the contract is a compile error.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Interfaces for open extension** | Any object that structurally satisfies the interface is accepted — no registration required | [-> T07](../catalog/T07-structural-typing.md) |
| **Runtime polymorphism** | Interface references dispatch to the concrete implementation at runtime | [-> T36](../catalog/T36-trait-objects.md) |
| **Union types** | Closed, exhaustive set of variants — new members require a source change and update of all switches | [-> T02](../catalog/T02-union-intersection.md) |
| **Type narrowing** | Narrow a union to a specific variant before accessing variant-specific members | [-> T14](../catalog/T14-type-narrowing.md) |
| **Generic interfaces** | Parameterize extension points over the data types they handle; checker verifies consistency end-to-end | [-> T04](../catalog/T04-generics-bounds.md) |
| **Abstract classes** | Framework extension points with enforced implementation and optional shared behavior | [-> T36](../catalog/T36-trait-objects.md) |

## Patterns

### Pattern A — Interface-based plugin system

Any object that implements the `Plugin` interface is accepted by the plugin host. Third-party code adds plugins without modifying the host. TypeScript's structural typing means no explicit `implements` keyword is required — the shape is sufficient.

```typescript
interface Plugin {
  readonly name: string;
  readonly version: string;
  initialize(context: PluginContext): void | Promise<void>;
  teardown?(): void | Promise<void>;
}

interface PluginContext {
  readonly config: Record<string, unknown>;
  log(level: "info" | "warn" | "error", message: string): void;
  emit(event: string, payload: unknown): void;
}

class PluginHost {
  private readonly plugins: Plugin[] = [];

  register(plugin: Plugin): this {
    this.plugins.push(plugin);
    return this;
  }

  async start(context: PluginContext): Promise<void> {
    for (const plugin of this.plugins) {
      context.log("info", `Initializing plugin: ${plugin.name}@${plugin.version}`);
      await plugin.initialize(context);
    }
  }

  async stop(): Promise<void> {
    for (const plugin of this.plugins.slice().reverse()) {
      await plugin.teardown?.();
    }
  }
}

// Third-party plugin — no import from host required, just match the shape:
const metricsPlugin: Plugin = {
  name: "metrics",
  version: "1.2.0",
  initialize(ctx) {
    ctx.log("info", "Metrics plugin started");
    ctx.emit("metrics:ready", { timestamp: Date.now() });
  },
  teardown() {
    console.log("Metrics plugin stopped");
  },
};

// Anonymous object — no class needed, structural typing suffices:
const healthPlugin: Plugin = {
  name: "health",
  version: "0.1.0",
  initialize(ctx) {
    ctx.log("info", "Health check plugin started");
  },
  // teardown is optional — omitting is fine
};

// Missing required field caught at compile time:
const badPlugin: Plugin = {
  name: "broken",
  // error: Property 'version' is missing in type '...' but required in type 'Plugin'
  initialize() {},
};

const host = new PluginHost();
host.register(metricsPlugin).register(healthPlugin);
```

### Pattern B — Declaration merging for interface extension

A library exports an interface; consumers extend it in their own module via declaration merging. The library code picks up the merged definition without any change.

```typescript
// --- framework/types.ts (library — not modified) ---
export interface AppConfig {
  readonly name: string;
  readonly version: string;
}

export interface RequestContext {
  readonly requestId: string;
  readonly startedAt: Date;
}

// --- app/types.ts (consumer — extends the library interface) ---
import "framework/types"; // side-effect import to trigger merging

declare module "framework/types" {
  interface AppConfig {
    readonly dbUrl: string;       // added by the app
    readonly featureFlags: Record<string, boolean>;
  }

  interface RequestContext {
    readonly userId?: string;     // added by the app
    readonly traceId: string;
  }
}

// Now AppConfig has name, version, dbUrl, featureFlags — all type-checked:
import { AppConfig, RequestContext } from "framework/types";

const config: AppConfig = {
  name: "my-app",
  version: "2.0.0",
  dbUrl: "postgres://localhost/app",
  featureFlags: { newCheckout: true },
};

// Missing merged field is a compile error:
const bad: AppConfig = {
  name: "my-app",
  version: "2.0.0",
  // error: Property 'dbUrl' is missing
  featureFlags: {},
};
```

### Pattern C — Union for closed exhaustive sets vs interface for open extensible sets

The choice between a union and an interface determines whether the set of variants is open or closed. Unions are exhaustive — the compiler flags unhandled cases; interfaces are open — new implementations require no central change.

```typescript
// ----- Closed set: union -----
// Adding a new shape requires updating every switch. That is a feature, not a bug:
// the compiler finds all the places that need updating.
type Shape =
  | { kind: "Circle";    radius: number }
  | { kind: "Rectangle"; width: number; height: number }
  | { kind: "Triangle";  base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "Circle":    return Math.PI * shape.radius ** 2;
    case "Rectangle": return shape.width * shape.height;
    case "Triangle":  return 0.5 * shape.base * shape.height;
    default: {
      const _exhaustive: never = shape; // compile error when a new variant is added
      return _exhaustive;
    }
  }
}

// ----- Open set: interface -----
// Adding a new renderer requires zero changes to existing code:
interface Renderer {
  render(element: { tag: string; children: unknown[] }): string;
}

function renderPage(
  root: { tag: string; children: unknown[] },
  renderer: Renderer,
): string {
  return renderer.render(root);
}

const htmlRenderer: Renderer = {
  render(el) {
    return `<${el.tag}>${el.children.join("")}</${el.tag}>`;
  },
};

const markdownRenderer: Renderer = {
  render(el) {
    return el.children.join("\n");
  },
};

// Both integrate without modifying renderPage:
renderPage({ tag: "div", children: ["Hello"] }, htmlRenderer);
renderPage({ tag: "div", children: ["Hello"] }, markdownRenderer);

// A future SvgRenderer needs no changes to renderPage or any existing code.
```

### Pattern D — Generic plugin interfaces

Parameterize the plugin interface over the data types it handles. The checker
verifies that the implementation and call site agree on types end-to-end.

```typescript
interface Serializer<T> {
  serialize(value: T): string;
  deserialize(raw: string): T;
}

// Concrete implementation — T is inferred as User at call sites:
interface User { name: string; age: number }

const userSerializer: Serializer<User> = {
  serialize(user) {
    return JSON.stringify(user);
  },
  deserialize(raw) {
    return JSON.parse(raw) as User; // boundary: validate in real code
  },
};

function roundTrip<T>(serializer: Serializer<T>, value: T): T {
  return serializer.deserialize(serializer.serialize(value));
}

const alice: User = { name: "Alice", age: 30 };
const result = roundTrip(userSerializer, alice); // T inferred as User
//    ^? User

// Type mismatch caught at compile time:
roundTrip(userSerializer, 42);
// error: Argument of type 'number' is not assignable to parameter of type 'User'

// Compose a caching layer generically — works with any Serializer<T>:
function withCache<T>(
  serializer: Serializer<T>,
  cache: Map<string, string>,
): Serializer<T> {
  return {
    serialize(value) {
      const raw = serializer.serialize(value);
      cache.set(raw, raw);
      return raw;
    },
    deserialize(raw) {
      return serializer.deserialize(cache.get(raw) ?? raw);
    },
  };
}
```

### Pattern E — Abstract classes for framework extension points

Use an `abstract class` when framework extensions must inherit shared behavior
and the compiler must enforce implementation of required methods. The `abstract`
keyword prevents instantiation of the base class and flags missing overrides at
compile time.

```typescript
abstract class Middleware {
  // Required — subclasses must implement:
  abstract processRequest(req: Request): Request | Promise<Request>;
  abstract processResponse(res: Response): Response | Promise<Response>;

  // Shared behavior — inherited by all subclasses:
  protected log(message: string): void {
    console.log(`[${this.constructor.name}] ${message}`);
  }
}

class AuthMiddleware extends Middleware {
  constructor(private readonly secret: string) {
    super();
  }

  processRequest(req: Request): Request {
    this.log("verifying token");
    // attach auth header, validate JWT, etc.
    return req;
  }

  processResponse(res: Response): Response {
    return res;
  }
}

// Incomplete subclass — compile error, not a runtime surprise:
class IncompleteMiddleware extends Middleware {
  processRequest(req: Request): Request {
    return req;
  }
  // error: Non-abstract class 'IncompleteMiddleware' does not implement
  //        abstract member 'processResponse' from class 'Middleware'.
}

new Middleware();
// error: Cannot create an instance of an abstract class.

new AuthMiddleware("s3cr3t"); // OK

// Abstract classes can also provide default implementations that subclasses
// may override:
abstract class BaseExporter {
  abstract export(data: Record<string, unknown>): Uint8Array;

  contentType(): string {
    return "application/octet-stream"; // default — override as needed
  }

  filename(): string {
    return `export-${Date.now()}`;
  }
}

class JsonExporter extends BaseExporter {
  export(data: Record<string, unknown>): Uint8Array {
    return new TextEncoder().encode(JSON.stringify(data));
  }

  override contentType(): string {
    return "application/json"; // specialized — replaces the default
  }
  // filename() is inherited; no override needed
}
```

**Interface vs abstract class — when to choose which:**

- Prefer an **interface** when consumers may not own a base class and
  structural compatibility is enough (third-party code, duck-typed adapters).
- Prefer an **abstract class** when the framework needs to share concrete
  behavior with all extensions and you want nominal enforcement via `extends`.
- Use `implements` explicitly on a class when you want the compiler to lock
  the class to an interface contract regardless of structural matches:
  ```typescript
  class RedisStorage implements StorageBackend {
    // compiler reports every missing or mistyped member immediately
  }
  ```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| **Interface (structural)** | No coupling; third-party objects satisfy it without importing it | No shared behavior; silent satisfaction can mask intent |
| **Abstract class** | Shared base behavior; nominal contract; prevents direct instantiation | Requires `extends`; ties consumers to the class hierarchy |
| **Generic interface** | Type-safe parameterization; checker verifies data types end-to-end | More complex signatures; callers must satisfy `T` constraints |
| **Declaration merging** | Library augmentation without forking; idiomatic for framework types | Only works across module boundaries; cannot merge class members |
| **Union (closed)** | Exhaustiveness checking; compiler finds every unhandled case | Adding a variant forces updates across all consuming switch statements |

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Plugin contract | Documented convention — plugins that miss a method fail at runtime, far from the call site | Interface contract — missing or mistyped methods are compile errors when the plugin is constructed |
| Interface extension | Monkey-patching the prototype or config object; conflicts are silent | Declaration merging — merges are type-checked; conflicts between modules are reported |
| Closed variants | `switch` on a string field; unhandled cases return `undefined` silently | Discriminated union with `never` exhaustiveness — unhandled variants are compile errors |
| Open polymorphism | Duck typing at runtime; wrong shape discovered only when the method is called | Structural interface — shape is checked at assignment; all call sites are safe |

## When to Use Which Feature

**Interface-based extension** (Pattern A) is the default for plugin systems, middleware, adapters, and any point where third-party code must integrate. TypeScript's structural typing means consumers do not need to import the interface to satisfy it — any object with the right shape works.

**Declaration merging** (Pattern B) is the right tool when a library must be extended by consumers without forking. It is idiomatic in TypeScript for augmenting `express.Request`, environment variable types, and framework config shapes.

**Union** (Pattern C — closed) is best when the set of variants is known and finite, and when every switch over those variants must be exhaustive. Prefer it for domain modeling within a bounded context where adding variants intentionally requires updating all consumers.

**Interface** (Pattern C — open) is best when the set of implementations is open-ended and new ones must not require touching existing code. The tradeoff is that there is no exhaustiveness check — you cannot `switch` over all implementations.

**Generic interface** (Pattern D) is the right choice when a plugin or adapter must be parameterized over the data types it handles and you want the checker to verify consistency from the implementation through all call sites.

**Abstract class** (Pattern E) is the right choice for internal framework extension points that need to share concrete behavior across all implementations. Use `implements` on concrete classes when you want the compiler to verify conformance to an interface explicitly rather than relying on structural inference.

## When to Use

Use extensibility patterns when third-party code must integrate without modifying existing code. The type system enforces the integration contract at compile time instead of at runtime.

**Use interfaces (Pattern A)** for plugin systems where consumers cannot import the interface:

```typescript
interface Handler { handle(event: "click" | "hover"): void }

// Any object with the right shape works:
const handler: Handler = {
  handle(e) { console.log(e); }
};
```

**Use declaration merging (Pattern B)** to extend a library's interface without forking:

```typescript
declare module "lib" {
  interface Config { authToken: string }
}
```

**Use unions (Pattern C)** when the variant set is closed and exhaustive:

```typescript
type Status = "pending" | "active" | "closed";

function label(s: Status) {
  switch (s) {
    case "pending": return "new";
    case "active": return "running";
    case "closed": return "done";
    default: const _: never = s; // compile error if variant added
  }
}
```

## When Not to Use

**Don't use interfaces** when runtime exhaustiveness is required. Interfaces are open — you cannot enumerate all implementations:

```typescript
interface Strategy { run(): number }

// No compile error if you forget to call a strategy:
const strategies: Strategy[] = [s1];
// Forgot s2? Runtime surprise.
```

**Don't use declaration merging** for runtime behavior. It only affects types:

```typescript
declare module "lib" {
  interface Config { extra: string } // type change only
}

const config = { name: "app" }; // runtime: no `extra` needed
```

**Don't use unions** for open sets. Adding variants requires touching all existing switches:

```typescript
// Adding "archived" to Status requires updating every switch
type Status = "pending" | "active" | "closed" | "archived";
//                          ^^^^^^^^ compiler error in all switches
```

**Don't use abstract classes** for third-party extensions. They require `extends`:

```typescript
abstract class Base { abstract run(): void }

class ThirdParty extends Base { run() {} } // requires import of Base
```

## Antipatterns When Using Extensibility

**Over-generic interfaces** — too much parametrization hides intent:

```typescript
// Hard to understand, impossible to reuse correctly:
interface Repo<T, K, O extends T & Record<string, K>> {
  get(id: K): T | null;
  save(o: O): K;
}

// Better — specific and reusable:
interface UserRepo {
  get(id: string): User | null;
  save(user: User): void;
}
```

**Delegating type safety** — interfaces without runtime validation at boundaries:

```typescript
interface User { name: string; age: number }

// API response — no runtime check:
const user: User = response.json(); // age could be "N/A" string

// Better:
const user: User = { name: data.name, age: parseInt(data.age) };
```

**Unbounded plugin registration** — allowing duplicate or conflicting plugins:

```typescript
class Host {
  plugins: Plugin[] = [];
  register(p: Plugin) { this.plugins.push(p); } // no dedup
}

// Better:
class Host {
  private plugins = new Map<string, Plugin>();
  register(p: Plugin) {
    if (this.plugins.has(p.name)) throw new Error("duplicate");
    this.plugins.set(p.name, p);
  }
}
```

**Merging in the wrong scope** — global pollution across modules:

```typescript
// app.ts:
declare global {
  interface Window { auth: Auth } // affects entire project
}
```

**Abstract class overkill** — using abstract classes for simple contracts:

```typescript
// Overkill:
abstract class SimpleHandler {
  abstract handle(x: number): string;
}

// Better:
interface SimpleHandler { handle(x: number): string }
```

## Antipatterns With Other Techniques

**String discriminants instead of unions** — loses exhaustiveness:

```typescript
// Bad:
interface Shape { kind: "circle" | "rect"; ... }
function area(s: Shape) {
  if (s.kind === "circle") return ...
  // forgot "rect"? No compile error
}

// Good:
type Shape = { kind: "circle"; r: number } | { kind: "rect"; w: number; h: number };
function area(s: Shape) {
  switch (s.kind) {
    case "circle": return Math.PI * s.r ** 2;
    case "rect": return s.w * s.h;
    default: const _: never = s; // compile error if missed
  }
}
```

**Type assertions instead of narrowing** — silent runtime errors:

```typescript
// Bad:
function handle(s: Shape) {
  const r = (s as any).radius; // no type safety
  return Math.PI * r ** 2;
}

// Good with narrowing:
function area(s: Shape) {
  if (s.kind === "circle") return Math.PI * s.radius ** 2;
  throw new Error("not a circle");
}
```

**Dynamic `any` in plugin context** — defeats structural typing:

```typescript
// Bad:
interface Plugin {
  run(ctx: any): any; // type safety lost
}

// Good:
interface PluginContext {
  log(msg: string): void;
  config: { apiUrl: string };
}
interface Plugin {
  run(ctx: PluginContext): Promise<void>;
}
```

**Mutable state in interface implementations** — hidden dependencies:

```typescript
// Bad:
interface Counter {
  inc(): number;
}
const counter: Counter = {
  inc() { return ++n; } // closes over external `n`
};

// Good:
class Counter {
  private n = 0;
  inc() { return ++this.n; }
}
```

**Nested generics without extraction** — uncomposable interfaces:

```typescript
// Bad:
interface Result<T, E> {
  map<U>(f: (t: T) => U): Result<U, E>;
  flatMap<U>(f: (t: T) => Result<U, E>): Result<U, E>;
}

// Good:
interface Result<T, E> {
  map<U>(f: (t: T) => U): Result<U, E>;
}
interface Ok<T> {
  flatMap<U>(f: (t: T) => Ok<U>): Ok<U>;
}
```
