# Structural Contracts

## The Constraint

Enforce that values have a required shape without requiring explicit inheritance or class hierarchies. Any type that carries the right fields and methods satisfies the contract — structural compatibility is checked at compile time, not via `instanceof` at runtime.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Structural typing** | Compatibility is determined by shape, not by name or class ancestry | [-> T07](../catalog/T07-structural-typing.md) |
| **Interfaces** | Named, reusable structural contracts that describe required fields and methods | [-> T05](../catalog/T05-type-classes.md) |
| **Intersection types** | Combine multiple contracts into a single requirement without subclassing | [-> T02](../catalog/T02-union-intersection.md) |
| **Type narrowing** | Refine a broad structural type to a more specific shape inside a branch | [-> T14](../catalog/T14-type-narrowing.md) |

## Patterns

### Pattern A — Interface without implements

A plain object literal satisfies an interface if it has the required shape. No class, no `implements`, no runtime overhead. Different domains can contribute types that satisfy the same interface without knowing about each other.

```typescript
interface Renderable {
  render(): string;
}

interface Measurable {
  width: number;
  height: number;
}

// Functions accept any shape that satisfies the interface:
function display(item: Renderable): void {
  console.log(item.render());
}

function computeArea(item: Measurable): number {
  return item.width * item.height;
}

// Plain object literals qualify automatically:
const card = { render: () => "<div>Card</div>", width: 200, height: 150 };
display(card);      // OK — has render()
computeArea(card);  // OK — has width and height

// A class also qualifies without explicit `implements Renderable`:
class Button {
  constructor(private label: string) {}
  render(): string { return `<button>${this.label}</button>`; }
}

const btn = new Button("Submit");
display(btn); // OK — Button has render()

// An object missing the required field is rejected:
const bare = { width: 100 };
display(bare);      // error: Property 'render' is missing
computeArea(bare);  // error: Property 'height' is missing
```

### Pattern B — Intersection type for combining multiple contracts

An intersection type `A & B` requires both contracts simultaneously. This is the structural alternative to multiple interface inheritance and works on any type, including objects from external libraries.

```typescript
interface Identifiable {
  readonly id: string;
}

interface Timestamped {
  readonly createdAt: Date;
  readonly updatedAt: Date;
}

interface Serialisable {
  toJSON(): Record<string, unknown>;
}

// Combine: a type must satisfy all three contracts
type Entity = Identifiable & Timestamped & Serialisable;

function persist(entity: Entity): void {
  console.log(`Saving ${entity.id} updated at ${entity.updatedAt.toISOString()}`);
  const data = entity.toJSON();
  // … write to DB
}

// Any object with all required fields qualifies:
const order = {
  id: "ord_001",
  createdAt: new Date("2025-01-01"),
  updatedAt: new Date("2025-06-15"),
  total: 4999,
  toJSON() {
    return { id: this.id, total: this.total };
  },
};

persist(order); // OK

// Missing one contract field is an error:
const partial = { id: "x", createdAt: new Date(), updatedAt: new Date() };
persist(partial); // error: Property 'toJSON' is missing
```

### Pattern C — satisfies operator (TypeScript 4.9+)

The `satisfies` operator checks that a value matches a contract while preserving the narrowest literal type inferred from the expression. Use it for configuration objects and lookup tables where you want both shape-checking and precise types.

```typescript
type RouteConfig = {
  path: string;
  method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  auth: boolean;
};

type AppRoutes = Record<string, RouteConfig>;

// satisfies checks the shape but keeps the literal type of each field:
const routes = {
  getUser:    { path: "/users/:id", method: "GET",    auth: true },
  createUser: { path: "/users",     method: "POST",   auth: true },
  health:     { path: "/health",    method: "GET",    auth: false },
} satisfies AppRoutes;

// Each field retains its literal type — routes.health.method is "GET", not the full union:
const method = routes.health.method; // type: "GET" (not "GET" | "POST" | …)
const bad    = routes.unknown;       // error: Property 'unknown' does not exist

// Without satisfies (using type annotation), literal types are widened:
const routesAnnotated: AppRoutes = {
  health: { path: "/health", method: "GET", auth: false },
};
const m = routesAnnotated.health.method; // type: "GET" | "POST" | "PUT" | "DELETE" | "PATCH"
```

### Pattern D — Type guard for structural narrowing

When a value arrives as a broad type (e.g., `unknown` from an API response), a type guard narrows it to a structural contract.

```typescript
interface ApiUser {
  id: string;
  name: string;
  email: string;
}

function isApiUser(value: unknown): value is ApiUser {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as Record<string, unknown>).id === "string" &&
    typeof (value as Record<string, unknown>).name === "string" &&
    typeof (value as Record<string, unknown>).email === "string"
  );
}

async function fetchUser(id: string): Promise<ApiUser> {
  const response = await fetch(`/api/users/${id}`);
  const json: unknown = await response.json();
  if (!isApiUser(json)) {
    throw new Error("Unexpected API response shape");
  }
  return json; // narrowed to ApiUser — safe to use
}
```

### Pattern E — Generic structural bounds

Constrain a type parameter to require specific members. The function preserves the concrete type of the argument (`T`) while enforcing a structural capability at compile time. This is the TypeScript analogue of Scala's `T <: { def length: Int }` or Python's `Protocol + TypeVar`.

```typescript
// Accept any T that has a numeric length — return type is still T, not a widened type
function logLength<T extends { length: number }>(value: T): T {
  console.log(`Length: ${value.length}`);
  return value;
}

const s = logLength("hello");          // T = string; return type is string
const a = logLength([1, 2, 3]);        // T = number[]; return type is number[]
const m = logLength(new Map());        // error: Map has no .length property

// Compose multiple structural requirements on a single generic parameter:
function snapshot<T extends { id: string; toJSON(): Record<string, unknown> }>(
  entity: T,
): { snapshotId: string; data: Record<string, unknown> } {
  return { snapshotId: entity.id, data: entity.toJSON() };
}
```

The key difference from a plain interface parameter (`item: { length: number }`) is that the return type and downstream types stay as specific as the caller's type, not widened to the structural bound.

### Pattern F — Interface (structural) vs abstract class (nominal)

TypeScript supports both structural contracts (interfaces) and nominal ones (abstract classes). The difference mirrors Python's `Protocol` vs `ABC`: structural accepts any matching shape; nominal requires explicit opt-in.

```typescript
// --- Structural: interface ---
interface Renderable {
  render(): string;
}

// --- Nominal: abstract class ---
abstract class RenderableBase {
  abstract render(): string;
  // Can provide default implementations and shared state:
  protected tag = "div";
}

// This class does NOT extend either:
class HtmlWidget {
  render(): string { return "<div>widget</div>"; }
}

function showStructural(r: Renderable): string { return r.render(); }
function showNominal(r: RenderableBase): string { return r.render(); }

showStructural(new HtmlWidget()); // OK — structural match: has render(): string
showNominal(new HtmlWidget());    // error: Argument of type 'HtmlWidget' is not assignable
                                  //        to parameter of type 'RenderableBase'
```

Prefer `interface` when you want to accept shapes from libraries you do not control. Use `abstract class` when you need to enforce an explicit inheritance relationship, provide default implementations, or protect shared state.

### Pattern G — Heterogeneous collections via a common interface

When you need a single array (or map) that holds values of different concrete types, declare the structural contract they share and collect values through it. This is TypeScript's equivalent of Rust's `Vec<Box<dyn Trait>>`.

```typescript
interface Plugin {
  readonly name: string;
  execute(context: Record<string, unknown>): void;
}

class LogPlugin implements Plugin {
  readonly name = "log";
  execute(ctx: Record<string, unknown>): void {
    console.log("[log]", ctx);
  }
}

class MetricsPlugin implements Plugin {
  readonly name = "metrics";
  execute(ctx: Record<string, unknown>): void {
    // record metrics …
  }
}

// Because Plugin is a structural contract, any object with the right shape qualifies:
const adhocPlugin: Plugin = {
  name: "ad-hoc",
  execute(ctx) { console.log("ad-hoc", ctx); },
};

const registry: Plugin[] = [new LogPlugin(), new MetricsPlugin(), adhocPlugin];

function runAll(plugins: Plugin[], ctx: Record<string, unknown>): void {
  for (const p of plugins) {
    console.log(`Running plugin: ${p.name}`);
    p.execute(ctx);
  }
}

runAll(registry, { requestId: "abc" });
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **Interface (Pattern A)** | Works with any matching shape; no inheritance required; zero runtime cost | Cannot enforce invariants, provide default implementations, or carry shared state |
| **Intersection type (Pattern B)** | Combines independent contracts without subclassing; works across library boundaries | Error messages can be verbose; over-intersecting creates unmatchable types |
| **satisfies operator (Pattern C)** | Shape-checked at definition site; literal types preserved; catches typos in config | TypeScript 4.9+ only; only useful for constant/config values, not function parameters |
| **Type guard (Pattern D)** | Bridges compile-time contracts and runtime validation; narrows `unknown` safely | Boilerplate; must be kept in sync with the interface manually |
| **Generic structural bound (Pattern E)** | Preserves the concrete type through generic calls while requiring structural capability | More complex signatures; inference can fail with overloaded or union input types |
| **Abstract class (Pattern F)** | Explicit opt-in; enables default implementations and shared state | Requires inheritance; cannot accept third-party types that happen to match the shape |
| **Common interface collection (Pattern G)** | Heterogeneous containers with full static typing; works with ad-hoc objects | All items must be known to satisfy the interface at compile time; no runtime duck-typing |

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Structural compatibility | Duck typing at runtime: `if (typeof obj.render === 'function')` — checked lazily | Interface or intersection type — checked at compile time; missing fields are errors in the editor |
| Multiple contracts | Manual runtime check for each required method/field | Intersection type `A & B & C` — all requirements in one type; compiler checks completeness |
| Configuration objects | No shape enforcement; typos in option names silently ignored | `satisfies AppRoutes` — shape-checked at the point of definition; literal types preserved |
| API response validation | Full manual validation every time; easy to miss a field | Type guard narrows `unknown` to a structural type once; downstream code uses the typed value |

## When to Use Which Feature

**Interface without `implements`** (Pattern A) is the everyday tool. Define interfaces for the capabilities functions need, not for the classes that implement them. This keeps function signatures narrow and composable.

**Intersection type** (Pattern B) is best when a value must satisfy several independent contracts at once. Prefer intersection over extending one interface from another when the contracts come from different domains or third-party libraries.

**satisfies operator** (Pattern C) is the right choice for configuration objects and constant tables where you want shape-checking at the definition site but need literal types to flow through to call sites. It is strictly more informative than a plain type annotation on such values.

**Type guard** (Pattern D) belongs at trust boundaries — API responses, user input, `JSON.parse` output, and inter-process messages. Parse once at the edge; use the structural type everywhere else.

**Generic structural bound** (Pattern E) is the right tool when a generic function needs to both preserve the caller's concrete type and require structural capabilities (e.g., `T extends { length: number }`). If you only need to accept the shape without preserving the specific type, a plain interface parameter is simpler.

**Abstract class** (Pattern F) is appropriate when you control the code and want to enforce explicit opt-in, provide shared default implementations, or carry protected state. For third-party or cross-library types, always prefer an interface.

**Common interface collection** (Pattern G) is the idiomatic approach for plugin systems, middleware pipelines, and registries that hold values of different concrete types under a shared structural contract.

## When to Use It

Use structural contracts when you want to accept any matching shape without requiring inheritance or explicit opt-in.

- **Accepting third-party types**: You cannot modify a library to implement your interface, but you can define what shape you need
- **Loose coupling between modules**: Different teams can provide implementations without knowing about the interface definition
- **Testing and mocking**: Any object with the right shape works, no need to create mock classes
  ```typescript
  interface Logger { log(msg: string): void }
  function withLogging(logger: Logger, fn: () => void) { /* ... */ }
  withLogging(console, () => {}); // console has .log()
  ```
- **Ad-hoc objects**: Quick one-off implementations without boilerplate
  ```typescript
  interface Handler { handle(event: unknown): void }
  const handlers: Handler[] = [
    { handle: (e) => console.log(e) },
    { handle: (e) => /* ... */ },
  ];
  ```

## When Not to Use It

Avoid structural contracts when you need explicit membership, shared state, or runtime identity.

- **Need default implementations**: Interfaces cannot provide method bodies
  ```typescript
  interface Service {
    connect(): void;
    disconnect(): void;
  }
  // Cannot share common connect/disconnect logic
  ```
- **Need protected/private state**: No encapsulation, all properties must be public
- **Need runtime type checking**: Structural types are compile-time only; `instanceof` doesn't work
  ```typescript
  interface Drawable { draw(): void }
  const obj = { draw: () => {} };
  obj instanceof Drawable; // error: not a constructor
  ```
- **Need to distinguish incompatible implementations**: Two different classes with the same interface are indistinguishable
  ```typescript
  interface Serializer { serialize(v: unknown): string }
  const csv: Serializer = { serialize: (v) => "" };
  const json: Serializer = { serialize: (v) => "" };
  // Cannot tell them apart at runtime
  ```

## Antipatterns When Using It

### Antipattern A — God interface

Defining one large interface with many optional properties creates loose coupling and loses the benefits of type safety.

```typescript
// ❌ Bad: massive interface with optional fields
interface Config {
  host?: string;
  port?: number;
  timeout?: number;
  retries?: number;
  logger?: Logger;
  cache?: Cache;
  // ... many more
}

// Any combination gets through, errors surface at runtime
const config: Config = {}; // OK but useless at runtime
```

```typescript
// ✅ Good: split into focused interfaces
interface NetworkConfig {
  host: string;
  port: number;
  timeout: number;
}

interface RetryConfig {
  retries: number;
  backoff?: number;
}

type FullConfig = NetworkConfig & RetryConfig & { logger: Logger };
```

### Antipattern B — Overusing intersection types

Creating deeply nested intersections makes types unreadable and error messages cryptic.

```typescript
// ❌ Bad: unreadable type
type Complex = A & B & C & D & E & F & { extra: string };

function process(x: Complex) { /* ... */ }
// Error message spans multiple lines naming all 7 parts
```

```typescript
// ✅ Good: compose via named intermediate types
type Core = A & B & C;
type WithExtras = Core & D & E & { extra: string };
```

### Antipattern C — Ignoring excess property checks

Object literals assigned to variables with structural types can accidentally have extra properties.

```typescript
// ❌ Bad: extra properties silently accepted via variable
interface Point { x: number; y: number }
const p: Point = { x: 1, y: 2, z: 3 }; // OK! z is ignored

// Later code fails because it expected only x and y
```

```typescript
// ✅ Good: use satisfies or direct arrow return
const p = { x: 1, y: 2, z: 3 } satisfies Point; // error: 'z' is not allowed
```

### Antipattern D — Structural type as runtime guard

Using structural type annotations for runtime validation fails because types are erased.

```typescript
// ❌ Bad: assumes type annotation validates at runtime
function parseUser(json: unknown): { id: string; name: string } {
  return json as any; // NO runtime check happens here
}

parseUser({ id: 123 }); // runtime error when accessing name
```

```typescript
// ✅ Good: use type guard for runtime validation
function isUser(v: unknown): v is { id: string; name: string } {
  return (
    typeof v === "object" &&
    v !== null &&
    typeof (v as any).id === "string" &&
    typeof (v as any).name === "string"
  );
}
```

## Antipatterns with Other Techniques

### Antipattern A — Nominal class when structural would work

Forcing inheritance when structural typing would suffice creates unnecessary coupling.

```typescript
// ❌ Bad: requires explicit inheritance
abstract class Handler {
  abstract handle(event: unknown): void;
}

function register(h: Handler) { /* ... */ }

// Third-party library with compatible shape but no inheritance
class ExternalHandler {
  handle(event: unknown): void { /* ... */ }
}
register(new ExternalHandler()); // error: not a Handler

// Must wrap or modify external code
```

```typescript
// ✅ Good: structural interface accepts any matching shape
interface Handler {
  handle(event: unknown): void;
}

function register(h: Handler) { /* ... */ }
register(new ExternalHandler()); // OK
```

### Antipattern B — Discriminated union when interface suffices

Adding discriminants when you don't need to distinguish types adds complexity without benefit.

```typescript
// ❌ Bad: overkill when all implementations behave the same
type Shape =
  | { kind: "circle"; r: number; area(): number }
  | { kind: "rect"; w: number; h: number; area(): number }
  | { kind: "triangle"; b: number; h: number; area(): number };

function totalArea(shapes: Shape[]): number {
  return shapes.reduce((sum, s) => sum + s.area(), 0);
}
// Must switch on kind even though not needed
```

```typescript
// ✅ Good: simple interface when behavior is uniform
interface Shape {
  area(): number;
}

function totalArea(shapes: Shape[]): number {
  return shapes.reduce((sum, s) => sum + s.area(), 0);
}
```

### Antipattern C — Multiple type annotations instead of one structural type

Repeating type annotations in multiple places instead of using a single structural contract creates drift.

```typescript
// ❌ Bad: same type defined in multiple places
function createConfig(c: { host: string; port: number }) { /* ... */ }
function applyConfig(c: { host: string; port: number }) { /* ... */ }
function validateConfig(c: { host: string; port: number }) { /* ... */ }
// Change one, forget others -> bugs

const config1 = { host: "localhost", port: 8080, debug: true };
createConfig(config1); // debug ignored, no error
```

```typescript
// ✅ Good: single structural contract
interface Config {
  host: string;
  port: number;
}

function createConfig(c: Config) { /* ... */ }
function applyConfig(c: Config) { /* ... */ }

const config = { host: "localhost", port: 8080 } satisfies Config; // OK
const bad = { host: "localhost", port: 8080, debug: true } satisfies Config; // error
```

## Source Anchors

- [TypeScript Handbook — Interfaces](https://www.typescriptlang.org/docs/handbook/2/objects.html)
- [TypeScript Handbook — Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html)
- [TypeScript Handbook — Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [TypeScript 4.9 release notes — satisfies operator](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html#the-satisfies-operator)
- [TypeScript Handbook — Classes (abstract)](https://www.typescriptlang.org/docs/handbook/2/classes.html#abstract-classes-and-members)
