# Extensibility

## The Constraint

New variants or implementations must integrate without modifying existing code. The type system enforces the integration contract; passing an object that does not satisfy the contract is a compile error.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Interfaces for open extension** | Any object that structurally satisfies the interface is accepted — no registration required | [-> T05](../catalog/T05-type-classes.md) |
| **Runtime polymorphism** | Interface references dispatch to the concrete implementation at runtime | [-> T36](../catalog/T36-trait-objects.md) |
| **Union types** | Closed, exhaustive set of variants — new members require a source change and update of all switches | [-> T02](../catalog/T02-union-intersection.md) |
| **Type narrowing** | Narrow a union to a specific variant before accessing variant-specific members | [-> T14](../catalog/T14-type-narrowing.md) |

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
