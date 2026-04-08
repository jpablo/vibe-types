# Callable Contracts

## The Constraint

Constrain function signatures so that invalid call patterns — wrong argument types, wrong number of arguments, mismatched return types — are compile errors. Overloads let a single function present different signatures for different input combinations without losing type precision.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Callable types and overloads** | Multiple signatures for one function; each call site resolves to the most specific matching signature | [-> T22](../catalog/T22-callable-typing.md) |
| **Generic functions** | A uniform transformation whose return type depends on the input type | [-> T04](../catalog/T04-generics-bounds.md) |
| **Variadic tuple types** | Type-safe rest parameters; spread and concatenation of typed tuples | [-> T45](../catalog/T45-paramspec-variadic.md) |
| **ReturnType / Parameters** | Derive downstream types from an existing function type without duplication | [-> T49](../catalog/T49-associated-types.md) |

## Patterns

### Pattern E — Higher-order functions and simple callback typing

Functions are first-class values in TypeScript. Use a function type `(arg: T) => U` to constrain callbacks, transformations, and predicates. The checker verifies both argument types and the return type at every call site.

```typescript
// Constrain a callback — wrong argument or return type is a compile error:
function applyTwice<T>(f: (x: T) => T, value: T): T {
  return f(f(value));
}

applyTwice((n: number) => n + 1, 10);        // OK — returns 12
applyTwice((s: string) => s.toUpperCase(), "hi"); // OK — returns "HI"
applyTwice((n: number) => String(n), 10);    // error: string not assignable to number

// Functions as return values — partial application via closure:
function adder(n: number): (x: number) => number {
  return (x) => x + n;
}

const add10 = adder(10);
[1, 2, 3].map(add10);   // [11, 12, 13] — type: number[]

// Storing callbacks in objects:
interface EventHandler {
  onClick: (x: number, y: number) => void;
  onHover?: (target: Element) => void;
}

function makeHandler(onClick: (x: number, y: number) => void): EventHandler {
  return { onClick };
}
```

### Pattern F — Interface call signatures for complex callable shapes

`(arg: T) => U` cannot express keyword-style optional parameters, additional properties, or multiple call forms on the same callable value. Use an interface with a call signature instead — TypeScript's structural analog to Python's `Protocol __call__`.

```typescript
// A callable that also carries metadata:
interface Formatter {
  (value: string, options?: { width?: number; align?: "left" | "right" }): string;
  readonly displayName: string;
}

function render(text: string, fmt: Formatter): string {
  return fmt(text, { width: 80, align: "right" });
}

const padRight: Formatter = Object.assign(
  (value: string, opts?: { width?: number; align?: "left" | "right" }) =>
    value.padEnd(opts?.width ?? 0),
  { displayName: "padRight" },
);

render("hello", padRight);   // OK — structurally matches Formatter
render("hello", (v: string) => v); // error: missing displayName

// Multiple call forms on one callable (overloaded call signature):
interface Converter {
  (value: string): number;
  (value: number): string;
}

declare const convert: Converter;
const n: number = convert("42");   // OK
const s: string = convert(42);     // OK
const bad: number = convert(42);   // error: string not assignable to number
```

### Pattern A — Function overloads for createElement

Overloads give different return types for different tag names, exactly like the DOM's `document.createElement`. Each overload signature is checked individually; the implementation signature is not visible to callers.

```typescript
// Overload signatures (visible to callers):
function createElement(tag: "input"):  HTMLInputElement;
function createElement(tag: "button"): HTMLButtonElement;
function createElement(tag: "select"): HTMLSelectElement;
function createElement(tag: "canvas"): HTMLCanvasElement;
function createElement(tag: string):   HTMLElement;

// Implementation signature (not directly callable):
function createElement(tag: string): HTMLElement {
  return document.createElement(tag);
}

const input  = createElement("input");   // type: HTMLInputElement
const button = createElement("button");  // type: HTMLButtonElement
const div    = createElement("div");     // type: HTMLElement — falls through to string overload

// Callers get precise types without casting:
input.value = "hello";                   // OK — HTMLInputElement has .value
button.disabled = true;                  // OK — HTMLButtonElement has .disabled
input.disabled = true;                   // OK
button.value = "submit";                 // OK — both have .value

// Overloads also work for call signatures on types:
type Formatter = {
  (value: number): string;
  (value: Date, format: string): string;
};

const fmt: Formatter = (value: number | Date, format?: string): string => {
  if (typeof value === "number") return value.toFixed(2);
  return value.toLocaleDateString("en-US", { dateStyle: "short" });
};

fmt(3.14159);                   // type: string
fmt(new Date(), "YYYY-MM-DD");  // type: string
fmt("hello");                   // error: no overload matches (string, undefined)
```

### Pattern B — Generic function with constraint

A generic function adapts its return type to its input type while enforcing a structural constraint. The constraint is checked at each call site, not inside the implementation.

```typescript
interface HasId { readonly id: string; }

// Map an array, preserving the element type precisely:
function indexById<T extends HasId>(items: readonly T[]): Map<string, T> {
  const map = new Map<string, T>();
  for (const item of items) {
    map.set(item.id, item);
  }
  return map;
}

type Product = { id: string; name: string; price: number };
type Tag     = { id: string; label: string; color: string };

const products: Product[] = [
  { id: "p1", name: "Widget", price: 9_99 },
  { id: "p2", name: "Gadget", price: 24_99 },
];

const productIndex = indexById(products); // type: Map<string, Product>
const p = productIndex.get("p1");         // type: Product | undefined
p?.price;                                 // OK — inferred as Product, not a weaker type

// A type without `id` is rejected:
type Metric = { timestamp: Date; value: number };
indexById([] as Metric[]); // error: Metric does not satisfy HasId
```

### Pattern C — ReturnType and Parameters to derive downstream types

`ReturnType<F>` and `Parameters<F>` extract type information from an existing function type, keeping downstream type declarations in sync automatically when the source function signature changes.

```typescript
async function fetchUser(id: string, includeRoles: boolean): Promise<{
  id: string;
  name: string;
  email: string;
  roles?: string[];
}> {
  const response = await fetch(`/api/users/${id}?roles=${includeRoles}`);
  return response.json();
}

// Derive the return type without repeating it:
type FetchUserResult = Awaited<ReturnType<typeof fetchUser>>;
// { id: string; name: string; email: string; roles?: string[] }

// Derive parameter types to build wrappers:
type FetchUserParams = Parameters<typeof fetchUser>;
// [id: string, includeRoles: boolean]

function cachedFetchUser(...args: FetchUserParams): ReturnType<typeof fetchUser> {
  const [id] = args;
  // Check cache, then delegate:
  return fetchUser(...args);
}

// Utility: make all parameters optional for partial application:
type PartialParams<F extends (...args: unknown[]) => unknown> = Partial<Parameters<F>>;
type OptionalFetchParams = PartialParams<typeof fetchUser>; // [id?: string, includeRoles?: boolean]
```

### Pattern D — Variadic tuple types for type-safe pipelines

Variadic tuples let you type functions that accept or return a spread of arguments whose number and types are known at compile time.

```typescript
// Type-safe pipe: take a value and apply a sequence of functions, threading the result through:
type Pipe<T, Fns extends readonly ((arg: never) => unknown)[]> =
  Fns extends readonly []
    ? T
    : Fns extends readonly [(arg: T) => infer R, ...infer Rest]
      ? Rest extends readonly ((arg: never) => unknown)[]
        ? Pipe<R, Rest>
        : never
      : never;

function pipe<T>(value: T): T;
function pipe<T, A>(value: T, fn1: (x: T) => A): A;
function pipe<T, A, B>(value: T, fn1: (x: T) => A, fn2: (x: A) => B): B;
function pipe<T, A, B, C>(value: T, fn1: (x: T) => A, fn2: (x: A) => B, fn3: (x: B) => C): C;
function pipe(value: unknown, ...fns: Array<(x: unknown) => unknown>): unknown {
  return fns.reduce((acc, fn) => fn(acc), value);
}

const result = pipe(
  "  Hello World  ",
  (s: string)  => s.trim(),
  (s: string)  => s.toLowerCase(),
  (s: string)  => s.split(" "),
  (a: string[]) => a.join("-"),
);
// type: string

const bad = pipe(
  42,
  (n: number) => n * 2,
  (s: string) => s.toUpperCase(), // error: number is not assignable to string
);
```

### Pattern G — Signature-preserving wrappers

TypeScript has no `ParamSpec` (Python) or `Fn` trait (Rust), but `Args extends unknown[]` combined with `ReturnType` achieves the same goal: a wrapper whose call signature is exactly the wrapped function's signature, kept in sync automatically.

```typescript
// The wrapper's parameter and return types mirror the wrapped function exactly:
function withLogging<Args extends unknown[], R>(
  fn: (...args: Args) => R,
): (...args: Args) => R {
  return (...args: Args): R => {
    console.log(`calling ${fn.name} with`, args);
    const result = fn(...args);
    console.log(`→`, result);
    return result;
  };
}

function fetchUser(id: string, includeRoles: boolean): Promise<{ id: string; name: string }> {
  return fetch(`/api/users/${id}`).then((r) => r.json());
}

const loggedFetch = withLogging(fetchUser);
loggedFetch("u1", true);   // OK — checker sees (id: string, includeRoles: boolean) => Promise<...>
loggedFetch(42, true);     // error: number not assignable to string

// Compose multiple wrappers without losing the signature:
function withRetry<Args extends unknown[], R>(
  fn: (...args: Args) => Promise<R>,
  attempts = 3,
): (...args: Args) => Promise<R> {
  return async (...args: Args): Promise<R> => {
    for (let i = 0; i < attempts; i++) {
      try { return await fn(...args); }
      catch (err) { if (i === attempts - 1) throw err; }
    }
    throw new Error("unreachable");
  };
}

const resilientFetch = withRetry(withLogging(fetchUser));
// type still: (id: string, includeRoles: boolean) => Promise<{ id: string; name: string }>
```

> **Note:** TypeScript does not have a first-class `ParamSpec`. Named parameter labels are not preserved through the wrapper (callers see positional types, not names), and the approach requires `any` at the implementation boundary when the wrapper is not strictly variance-compatible. For most decorators this is an acceptable tradeoff.

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Simple callbacks | `function map(items, fn)` — `fn` is untyped; callers get `any[]` back | `(fn: (x: T) => U)` — argument type and return type checked at every call site |
| Complex callable shapes | No way to enforce keyword arguments or attached properties | Interface call signatures — structural match enforced by the checker |
| Overloaded functions | Single implementation with `typeof` guards; callers get the union of all possible returns; no narrowing | Overload signatures give callers precise return types per input combination; narrowing is automatic |
| Generic transformation | `function map(items, fn) { … }` — returns `any[]`; callers must cast | `function map<T, U>(items: T[], fn: (x: T) => U): U[]` — return type derived from inputs |
| Signature-preserving wrappers | Decorators and wrappers erase parameter types; consumers must look at source | `Args extends unknown[]` + `ReturnType<F>` — wrapper's type tracks the wrapped function exactly |
| Derived types | Type annotations duplicated manually; drift when the source function changes | `ReturnType<F>` and `Parameters<F>` — always in sync with the source |
| Variadic arguments | `function pipe(value, ...fns)` — no type safety; errors discovered at runtime | Overloaded pipe signatures or conditional types — wrong step types are caught at compile time |

## When to Use Which Feature

**Simple callback typing** (Pattern E) is the default for event handlers, sort keys, map/filter predicates, and any function that accepts another function. Use `(arg: T) => U` for straightforward cases.

**Interface call signatures** (Pattern F) are the right choice when a callable has keyword-style optional parameters, carries additional properties (like a `displayName`), or needs multiple call forms on the same value. Reach for these before reaching for overloads.

**Overloads** (Pattern A) are the right choice when a function's return type depends on the specific value of one of its arguments — not on a type parameter, but on a string literal or boolean discriminant. Keep the overload count small (2–5 signatures); if it grows beyond that, consider a discriminated union input type instead.

**Generic functions** (Pattern B) are better than overloads when the relationship between input and output types is uniform and structural. A generic function scales to any type that satisfies the constraint without adding new signatures.

**ReturnType / Parameters** (Pattern C) belong in any codebase where several parts depend on the same function's signature. Deriving types from the source of truth eliminates an entire class of type-drift bugs during refactoring.

**Signature-preserving wrappers** (Pattern G) belong in decorator, middleware, and instrumentation code — anywhere a wrapper must not widen or erase the wrapped function's type. Use `Args extends unknown[]` instead of `any[]` to keep the checker engaged.

**Variadic tuples** (Pattern D) are an advanced tool for pipeline, curry, and compose utilities. Use them in framework or library code; in application code, prefer explicit overloads or simpler composition patterns.
