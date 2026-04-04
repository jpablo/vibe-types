# Exhaustiveness Checking

## The Constraint

The compiler enforces that every variant of a discriminated union is handled. Adding a new variant to the union causes a compile error at every switch, dispatch map, or if-chain that does not yet handle it — so no case is silently dropped.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Discriminated unions** | Union of variants, each with a literal discriminant that drives narrowing | [-> T01](../catalog/T01-algebraic-data-types.md) |
| **Type narrowing** | Compiler tracks which variant is active inside each branch | [-> T14](../catalog/T14-type-narrowing.md) |
| **never / exhaustiveness** | After all variants are handled, the remaining type is `never`; assigning to `never` fails if any variant is unhandled | [-> T34](../catalog/T34-never-bottom.md) |
| **Literal discriminants** | `kind: "A" | "B" | "C"` fields that identify each variant uniquely | [-> T52](../catalog/T52-literal-types.md) |

## Patterns

### Pattern A — switch with assertNever in the default branch

`assertNever` accepts `never`. After all variants are handled, the type of `x` is `never`; if a variant is missing, the type is not `never` and the call is a compile error.

```typescript
type Shape =
  | { kind: "Circle";    radius: number }
  | { kind: "Rectangle"; width: number; height: number }
  | { kind: "Triangle";  base: number; height: number };

function assertNever(x: never, message?: string): never {
  throw new Error(message ?? `Unhandled variant: ${JSON.stringify(x)}`);
}

function area(shape: Shape): number {
  switch (shape.kind) {
    case "Circle":
      return Math.PI * shape.radius ** 2;
    case "Rectangle":
      return shape.width * shape.height;
    case "Triangle":
      return 0.5 * shape.base * shape.height;
    default:
      return assertNever(shape); // error if a new variant is added and not handled above
  }
}

// If "Pentagon" is added to Shape and area() is not updated:
// Argument of type '{ kind: "Pentagon"; … }' is not assignable to parameter of type 'never'.
```

### Pattern B — Object dispatch map

Map each variant's discriminant to a handler function. The type annotation on the map ensures that every key of the union's discriminant is present; a missing key is a compile error. This pattern is data-driven and easy to extend.

```typescript
type NotificationKind = "Email" | "SMS" | "Push";

type Notification =
  | { kind: "Email"; address: string; subject: string; body: string }
  | { kind: "SMS";   phone: string; text: string }
  | { kind: "Push";  deviceToken: string; title: string; payload: unknown };

type NotificationHandlers = {
  [K in NotificationKind]: (n: Extract<Notification, { kind: K }>) => Promise<void>;
};

const handlers: NotificationHandlers = {
  Email: async (n) => { console.log(`Emailing ${n.address}: ${n.subject}`); },
  SMS:   async (n) => { console.log(`Texting ${n.phone}: ${n.text}`); },
  Push:  async (n) => { console.log(`Pushing to ${n.deviceToken}: ${n.title}`); },
  // error if any key is missing: Property 'Push' is missing
};

async function dispatch(n: Notification): Promise<void> {
  const handler = handlers[n.kind] as (n: Notification) => Promise<void>;
  await handler(n);
}
```

### Pattern C — if-else chain with never final branch

For cases where a switch is awkward (e.g., non-literal discriminants or complex conditions), an if-else chain followed by a `never` assertion achieves the same exhaustiveness guarantee.

```typescript
type LogLevel = "debug" | "info" | "warn" | "error";

type LogEntry =
  | { level: "debug"; message: string; context?: Record<string, unknown> }
  | { level: "info";  message: string }
  | { level: "warn";  message: string; code: number }
  | { level: "error"; message: string; code: number; stack: string };

function formatEntry(entry: LogEntry): string {
  if (entry.level === "debug") {
    return `[DEBUG] ${entry.message}${entry.context ? ` ${JSON.stringify(entry.context)}` : ""}`;
  } else if (entry.level === "info") {
    return `[INFO] ${entry.message}`;
  } else if (entry.level === "warn") {
    return `[WARN:${entry.code}] ${entry.message}`;
  } else if (entry.level === "error") {
    return `[ERROR:${entry.code}] ${entry.message}\n${entry.stack}`;
  } else {
    // entry has type never here — if a new level is added, this is a compile error
    const _: never = entry;
    throw new Error(`Unhandled log level: ${JSON.stringify(_)}`);
  }
}
```

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| switch statement | `default: console.warn('Unknown kind', x)` — silently drops unhandled variants | `default: assertNever(x)` — compile error if any variant is unhandled |
| Adding a variant | New variant silently falls through to `default`; no indication which handlers need updating | Compile error at every handler that lacks the new case — the compiler lists affected files |
| Dispatch map | Plain object with no key coverage check; missing keys cause `undefined` at runtime | Mapped type keyed on the union's discriminant; missing keys are compile errors |
| if-else chain | Final `else` either does nothing or logs; easy to forget in large chains | Final `else` assigns to `never`; type error if the branch is ever reachable |

## When to Use Which Feature

**Switch with assertNever** (Pattern A) is the standard pattern. Use it when the handling logic for each variant is substantially different and reads naturally as a series of cases. The `assertNever` helper should live in a shared utilities module.

**Object dispatch map** (Pattern B) is better when each handler has a uniform signature and the dispatch is data-driven — for example, when handlers are registered by plugins or loaded from configuration. The `[K in UnionKey]` mapped type provides compile-time completeness and is more amenable to runtime introspection.

**if-else chain** (Pattern C) is a last resort when the discriminant is not a simple literal (e.g., it is computed, or the condition checks multiple fields). The final `never` assignment preserves exhaustiveness guarantees even in this unstructured form.
