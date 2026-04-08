# Type Aliases

> **Since:** TypeScript 1.5 (`type` keyword); recursive type aliases since TypeScript 3.7

## 1. What It Is

A **type alias** (`type Foo = ...`) gives a name to any type expression — primitives, unions, intersections, tuples, function types, conditional types, mapped types, and template literal types. Unlike `interface`, a type alias can represent any type, not just object shapes. Aliases are purely compile-time: they are erased after type checking and produce no JavaScript output. Type aliases are **not nominally distinct** from their right-hand side — `type UserId = string` and `string` are interchangeable without any cast (for nominal distinctness, see branded types in T03). Recursive type aliases work via deferred evaluation introduced in TypeScript 3.7, enabling self-referential structures like `type Json = string | number | boolean | null | Json[] | { [key: string]: Json }`. The key distinction between `type` and `interface` is that interfaces support **declaration merging** (the same interface name can be extended across files), while type aliases are **closed** (they cannot be reopened).

## 2. What Constraint It Lets You Express

**Name and reuse complex type expressions; make type code more readable by extracting intermediate types; build utility abstractions over conditional and mapped types.**

- A union alias documents the intent of a type alongside its structure: `type HttpMethod = "GET" | "POST" | "PUT" | "DELETE"` is more descriptive than the raw union inline.
- Recursive aliases represent recursive data structures (trees, JSON, linked lists) without any special syntax or library support.
- Aliases over mapped or conditional types create reusable higher-kinded-like utilities (`type Nullable<T> = T | null`) that can be applied repeatedly.

## 3. Minimal Snippet

```typescript
// --- Primitive union alias ---
type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";

function request(url: string, method: HttpMethod): Promise<Response> {
  return fetch(url, { method });
}

request("/api/users", "GET");    // OK
// request("/api/users", "PATCH"); // error — not in HttpMethod

// --- Recursive JSON type alias ---
type Json =
  | string
  | number
  | boolean
  | null
  | Json[]
  | { [key: string]: Json };

const data: Json = { name: "Alice", scores: [10, 20], active: true }; // OK
// const bad: Json = undefined; // error — undefined is not assignable to Json

// --- Type alias over mapped type (utility alias) ---
type Nullable<T> = T | null;
type Maybe<T> = T | null | undefined;
type Pairs<T> = { [K in keyof T]: [K, T[K]] }[keyof T];

interface User { name: string; age: number }
type UserPairs = Pairs<User>; // OK — ["name", string] | ["age", number]

// --- type vs interface: aliases are closed ---
type Point = { x: number; y: number };
// type Point = { z: number }; // error — duplicate identifier (aliases cannot be reopened)

interface IPoint { x: number; y: number }
interface IPoint { z: number }           // OK — interfaces merge
```

## 4. Beginner Mental Model

Think of a type alias as a **nickname**. When you write `type UserId = string`, you are telling both the compiler and other developers: "wherever you see `UserId`, read it as `string`." The nickname makes code more readable and lets you change the underlying type in one place.

The nickname provides **zero protection** against mixing up values. `type Meters = number` and `type Seconds = number` are both `number` to the compiler — passing `Seconds` where `Meters` is expected compiles without error. If you want the compiler to reject that mix-up, you need a branded type [-> T03](T03-newtypes-opaque.md), not an alias.

## 5. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Branded / Opaque Types** [-> T03](T03-newtypes-opaque.md) | Branded types are the "type-safe sibling" of aliases. Use a transparent alias for convenience naming; use a branded type when you need the compiler to reject accidental mixing (`type UserId = string & { readonly __brand: "UserId" }`). |
| **Union & Intersection Types** [-> T02](T02-union-intersection.md) | Union types are almost always given names via type aliases; the alias makes a union reusable across the codebase and documents intent beyond the raw structural expression. |
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | Type aliases can be generic: `type Pair<T> = [T, T]`. The alias is expanded at each use site. Generic aliases are the building block for reusable utility types such as `Nullable<T>`, `Result<T, E>`, and the entire `lib.es5.d.ts` utility library. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | Complex callback or handler signatures benefit greatly from aliases: `type Handler = (event: MouseEvent) => void` is far more readable than repeating the full function type everywhere. |
| **Conditional Types** [-> T41](T41-match-types.md) | Conditional types are exclusively expressed as type aliases; without `type =`, there is no way to name a conditional type for reuse. |
| **Mapped Types** [-> T62](T62-mapped-types.md) | Mapped types are similarly alias-dependent; the standard library's `Partial<T>`, `Required<T>`, `Record<K, V>` are all type aliases over mapped type expressions. |
| **Record Types & Interfaces** [-> T31](T31-record-types.md) | `type` and `interface` overlap for object shapes; the choice affects whether the shape can be reopened (interface) or is forever closed (alias). Prefer `interface` for public API shapes that may need extension; prefer `type` for unions, intersections, and complex compositions. |

## 6. Gotchas and Limitations

1. **Aliases are transparent, not nominal** — `type UserId = string` does not create a new type; a function expecting `UserId` accepts any `string`; for nominal distinctness, use branded types (`type UserId = string & { readonly __brand: unique symbol }`).
2. **Recursive aliases require deferred evaluation** — TypeScript 3.7+ supports recursive type aliases, but only when the recursion goes through an object property or array; directly recursive aliases like `type Foo = Foo` are an error.
3. **Aliases do not appear in error messages** — TypeScript often expands type aliases in error output, making error messages verbose and hard to read; using `interface` instead of `type` for object shapes often produces cleaner errors because the interface name is preserved.
4. **Declaration merging is not possible** — unlike `interface`, a `type` alias cannot be augmented after declaration; this makes aliases unsuitable for extensible plugin APIs or library augmentation patterns.
5. **`typeof` in aliases** — `type T = typeof someValue` is legal and useful, but creates a tight coupling between the alias and the runtime value's inferred shape; renaming the value changes the alias.
6. **Circular aliases can cause `Type alias circularly references itself`** — some circular alias patterns that look valid are rejected by the compiler depending on whether TypeScript can defer evaluation; if this occurs, introduce an intermediate interface.
7. **Generic aliases require all type arguments** — `type Pair<T> = [T, T]` must be used as `Pair<number>`, never as bare `Pair`. TypeScript does not support partially applied generic aliases (unlike Haskell or Scala type lambdas); workarounds involve conditional types or explicit type lambdas.

## 7. Example A — Simplifying complex callback signatures

```typescript
// Without aliases — repetitive and hard to scan
function on(event: string, handler: (e: MouseEvent) => void): void { /* ... */ }
function off(event: string, handler: (e: MouseEvent) => void): void { /* ... */ }

// With aliases — one change propagates everywhere
type MouseHandler = (e: MouseEvent) => void;

function on(event: string, handler: MouseHandler): void { /* ... */ }
function off(event: string, handler: MouseHandler): void { /* ... */ }

// Layered aliases for an event system
type Listener<E> = (event: E) => void;
type AsyncListener<E> = (event: E) => Promise<void>;
type AnyListener<E> = Listener<E> | AsyncListener<E>;
type ListenerMap<E> = Map<string, AnyListener<E>[]>;

class EventEmitter<E> {
  private listeners: ListenerMap<E> = new Map();

  on(name: string, fn: AnyListener<E>): void {
    const fns = this.listeners.get(name) ?? [];
    this.listeners.set(name, [...fns, fn]);
  }

  async emit(name: string, event: E): Promise<void> {
    for (const fn of this.listeners.get(name) ?? []) {
      await fn(event);                        // OK — Promise<void> or void both awaitable
    }
  }
}
```

The layered aliases keep the complex `Map<string, Array<((e: E) => void) | ((e: E) => Promise<void>)>>` type readable and centralise the definition.

## 8. Example B — Recursive domain types

```typescript
// Self-referential tree without any library or special syntax
type TreeNode<T> = {
  value: T;
  children: TreeNode<T>[];  // OK since TypeScript 3.7
};

function mapTree<A, B>(node: TreeNode<A>, fn: (a: A) => B): TreeNode<B> {
  return {
    value: fn(node.value),
    children: node.children.map(child => mapTree(child, fn)),  // OK — recursive call
  };
}

const numbers: TreeNode<number> = {
  value: 1,
  children: [
    { value: 2, children: [] },
    { value: 3, children: [{ value: 4, children: [] }] },
  ],
};

const strings = mapTree(numbers, n => String(n));  // OK — TreeNode<string>

// Mutually recursive aliases (also supported since 3.7)
type JsonPrimitive = string | number | boolean | null;
type JsonArray = JsonValue[];
type JsonObject = { [key: string]: JsonValue };
type JsonValue = JsonPrimitive | JsonArray | JsonObject;

const config: JsonValue = { host: "localhost", ports: [3000, 3001], debug: false }; // OK
```

## 9. Common Type-Checker Errors

### `error TS2456: Type alias 'X' circularly references itself`

```typescript
// Error — direct self-reference without indirection
type BadTree = BadTree[];       // TS2456

// Fix — go through an object property (TypeScript can defer evaluation)
type Tree = { value: number; children: Tree[] };  // OK since TS 3.7
```

### `error TS2304: Cannot find name 'X'` (forward reference in alias)

TypeScript evaluates type alias right-hand sides eagerly in some contexts. If an alias references a type declared later in the same file in a way the compiler cannot resolve, use an interface instead or reorder the declarations.

### Alias expanded in error, making it unreadable

```typescript
type DeepPartial<T> = { [K in keyof T]?: DeepPartial<T[K]> };
interface Config { db: { host: string; port: number }; debug: boolean }

declare function configure(c: DeepPartial<Config>): void;
configure({ db: { host: 42 } });
// error: Type 'number' is not assignable to type 'string | undefined'
// TypeScript may fully expand DeepPartial<Config> in the message
// Fix: use an interface for Config so the name is preserved in errors
```

TypeScript expands aliases in error messages more aggressively than it preserves interface names. For complex utility types applied to large shapes, wrapping the result in an `interface extends` can produce cleaner diagnostics.

## 10. Use-Case Cross-References

- [-> UC-02](../usecases/UC02-domain-modeling.md) Name domain concepts as type aliases to make the type vocabulary of the codebase match the ubiquitous language
- [-> UC-04](../usecases/UC04-generic-constraints.md) Create reusable generic utility aliases that constrain type parameters and encode domain invariants

## Source Anchors

- [TypeScript Handbook — Type Aliases](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-aliases)
- [TypeScript Handbook — Aliases and Interfaces](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#differences-between-type-aliases-and-interfaces)
- [TypeScript 3.7 release notes — Recursive type aliases](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-7.html#more-recursive-type-aliases)
- TypeScript source: `src/compiler/checker.ts` — `getTypeFromTypeAliasReference`
