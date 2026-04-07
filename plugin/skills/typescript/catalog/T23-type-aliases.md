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

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Union & Intersection Types** [-> T02](T02-union-intersection.md) | Union types are almost always given names via type aliases; the alias makes a union reusable across the codebase and documents intent beyond the raw structural expression. |
| **Conditional Types** [-> T41](T41-match-types.md) | Conditional types are exclusively expressed as type aliases; without `type =`, there is no way to name a conditional type for reuse. |
| **Mapped Types** [-> T62](T62-mapped-types.md) | Mapped types are similarly alias-dependent; the standard library's `Partial<T>`, `Required<T>`, `Record<K, V>` are all type aliases over mapped type expressions. |
| **Record Types & Interfaces** [-> T31](T31-record-types.md) | `type` and `interface` overlap for object shapes; the choice affects whether the shape can be reopened (interface) or is forever closed (alias). Prefer `interface` for public API shapes that may need extension; prefer `type` for unions, intersections, and complex compositions. |

## 5. Gotchas and Limitations

1. **Aliases are transparent, not nominal** — `type UserId = string` does not create a new type; a function expecting `UserId` accepts any `string`; for nominal distinctness, use branded types (`type UserId = string & { readonly __brand: unique symbol }`).
2. **Recursive aliases require deferred evaluation** — TypeScript 3.7+ supports recursive type aliases, but only when the recursion goes through an object property or array; directly recursive aliases like `type Foo = Foo` are an error.
3. **Aliases do not appear in error messages** — TypeScript often expands type aliases in error output, making error messages verbose and hard to read; using `interface` instead of `type` for object shapes often produces cleaner errors because the interface name is preserved.
4. **Declaration merging is not possible** — unlike `interface`, a `type` alias cannot be augmented after declaration; this makes aliases unsuitable for extensible plugin APIs or library augmentation patterns.
5. **`typeof` in aliases** — `type T = typeof someValue` is legal and useful, but creates a tight coupling between the alias and the runtime value's inferred shape; renaming the value changes the alias.
6. **Circular aliases can cause `Type alias circularly references itself`** — some circular alias patterns that look valid are rejected by the compiler depending on whether TypeScript can defer evaluation; if this occurs, introduce an intermediate interface.

## 6. Use-Case Cross-References

- [-> UC-02](../usecases/UC02-domain-modeling.md) Name domain concepts as type aliases to make the type vocabulary of the codebase match the ubiquitous language
- [-> UC-04](../usecases/UC04-generic-constraints.md) Create reusable generic utility aliases that constrain type parameters and encode domain invariants
