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
| **User-defined type predicates** | `(x): x is T` return annotation lets custom logic participate in narrowing — useful when there is no discriminant field | [-> T14](../catalog/T14-type-narrowing.md) |

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

### Pattern D — User-defined type predicates

When variants share no common discriminant field, or when the narrowing condition is not a simple equality check, a function with an `x is T` return type teaches the compiler how to narrow.

```typescript
// No discriminant field — structural distinction only
interface Cat   { meow: () => void }
interface Dog   { bark: () => void }
type Animal = Cat | Dog;

function isCat(a: Animal): a is Cat {
  return typeof (a as Cat).meow === "function";
}

function makeSound(a: Animal): string {
  if (isCat(a)) {
    a.meow();       // narrowed to Cat
    return "meow";
  } else {
    a.bark();       // narrowed to Dog — negative branch is also narrowed
    return "woof";
  }
}
```

A common variant: validating a container's contents, where `instanceof` does not reach inside the items.

```typescript
function isStringArray(val: unknown[]): val is string[] {
  return val.every((item) => typeof item === "string");
}

function joinWords(data: unknown[]): string {
  if (isStringArray(data)) {
    return data.join(", "); // narrowed to string[]
  }
  return "(mixed types)";
}
```

> **Limitation.** A type predicate is one-directional: if `isCat(a)` returns `false`, TypeScript narrows `a` to `Dog` only because `Animal = Cat | Dog` and `Cat` is eliminated. In more complex unions the negative branch may widen rather than narrow. Use discriminants when possible; fall back to predicates for structural or content-based checks.

### Pattern E — Intentionally partial handling (open unions)

Sometimes you want to handle known variants but accept future ones gracefully — for example, consuming an external API that may add new event types. This is the TypeScript equivalent of Rust's `#[non_exhaustive]` or Scala's `@nowarn`.

The mechanism is simply omitting `assertNever` in the default branch, accepting that the branch is reachable.

```typescript
type KnownEventKind = "click" | "keydown" | "resize";

type DomEvent =
  | { kind: "click";   x: number; y: number }
  | { kind: "keydown"; key: string }
  | { kind: "resize";  width: number; height: number };

// This function is intentionally open: a future "scroll" variant is not an error.
// Do NOT use assertNever here — the default branch must remain reachable.
function logEvent(e: DomEvent): void {
  switch (e.kind) {
    case "click":
      console.log(`click at (${e.x}, ${e.y})`);
      break;
    case "keydown":
      console.log(`key: ${e.key}`);
      break;
    case "resize":
      console.log(`resize: ${e.width}×${e.height}`);
      break;
    default:
      // Intentionally not assertNever — forward-compatible by design.
      // Leave a comment so reviewers understand the choice.
      console.log("unrecognised event, ignoring");
  }
}
```

If strict completeness matters locally but the union is shared and evolving, extract the exhaustive part into a helper:

```typescript
// Exhaustive handler for variants known today — assertNever guards against drift.
function handleKnown(e: DomEvent): string {
  switch (e.kind) {
    case "click":   return "click";
    case "keydown": return "keydown";
    case "resize":  return "resize";
    default:        return assertNever(e); // compile error if DomEvent gains a case
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

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| `switch` + `assertNever` (A) | Standard and familiar; provides a runtime safety net via the thrown error | Requires the switch to live in one place; verbose for many-variant types |
| Object dispatch map (B) | Data-driven; easy to extend at runtime; natural parallel structure | Needs a cast at dispatch time; less idiomatic for control flow |
| if-else + `never` assertion (C) | Works for non-literal discriminants and multi-field conditions | Most verbose; easier to accidentally omit the final branch |
| User-defined type predicates (D) | Custom narrowing for structural checks and container validation | One-directional for complex unions; predicate must be kept in sync with the type |
| Intentionally partial default (E) | Forward-compatible; safe to consume evolving external APIs | Compile-time completeness is lost; missing branches surface only at runtime |

## When to Use Which Feature

**Switch with assertNever** (Pattern A) is the standard pattern. Use it when the handling logic for each variant is substantially different and reads naturally as a series of cases. The `assertNever` helper should live in a shared utilities module.

**Object dispatch map** (Pattern B) is better when each handler has a uniform signature and the dispatch is data-driven — for example, when handlers are registered by plugins or loaded from configuration. The `[K in UnionKey]` mapped type provides compile-time completeness and is more amenable to runtime introspection.

**if-else chain** (Pattern C) is a last resort when the discriminant is not a simple literal (e.g., it is computed, or the condition checks multiple fields). The final `never` assignment preserves exhaustiveness guarantees even in this unstructured form.

**User-defined type predicates** (Pattern D) are the right tool when variants have no shared discriminant field, or when narrowing depends on the contents of a container rather than the container's own type. Prefer discriminants where possible; reach for predicates only when structural inspection is unavoidable.

**Intentionally partial handling** (Pattern E) is appropriate when consuming external or versioned data where new variants may arrive at runtime. Leave an explicit comment in the default branch so reviewers understand the choice is deliberate, not an oversight. Never silently swallow unknown cases without logging.

## Source Anchors

- TypeScript Handbook — [Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- TypeScript Handbook — [Discriminated Unions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions)
- TypeScript Handbook — [Using type predicates](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#using-type-predicates)
- TypeScript Handbook — [The `never` type](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#the-never-type)
