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
