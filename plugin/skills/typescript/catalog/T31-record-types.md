# Record Types & Object Shapes

> **Since:** TypeScript 1.0

## 1. What It Is

TypeScript represents named-field data through several related constructs. An **`interface`** is an open, declaration-mergeable object shape: `interface User { name: string; age: number }`. A **type alias object literal** (`type User = { name: string; age: number }`) is closed and cannot be reopened. **`Record<K, V>`** is a homogeneous map where every key of type `K` maps to a value of type `V` — a shorthand for `{ [key in K]: V }`. **Index signatures** (`{ [key: string]: V }`) describe objects with an arbitrary number of string or number keys, all mapping to `V`. Object shapes support **optional properties** (`?`), **readonly properties** (`readonly`), method signatures, and the ability to be composed via intersection (`TypeA & TypeB`). The built-in **utility types** `Pick<T, K>`, `Omit<T, K>`, `Partial<T>`, `Required<T>`, and `NonNullable<T>` operate on object shapes to produce new derived types.

The **`satisfies`** operator (TypeScript 4.9+) validates that a value matches a type without widening its inferred type. This is especially useful for exhaustive `Record<Union, ...>` tables where you want both type-safety and the narrowest possible inference on each value.

## 2. What Constraint It Lets You Express

**Named fields are statically checked: missing required fields, wrong field types, and excess properties at object literal sites are all compile errors.**

- Required fields without a `?` must be present in every object literal assigned to the type; omitting them is a compile error.
- `readonly` fields prevent reassignment after object construction.
- `Record<K, V>` with a union key (`Record<HttpMethod, Handler>`) ensures that every member of the union has an entry — a common exhaustiveness pattern for lookup tables.
- Excess property checking at object literal sites catches typos in optional field names.

## 3. Minimal Snippet

```typescript
// --- Interface with required, optional, readonly fields ---
interface Config {
  readonly host: string;
  readonly port: number;
  timeout?: number;          // optional
  retries?: number;          // optional
}

const cfg: Config = { host: "localhost", port: 8080 };         // OK
// const bad: Config = { host: "localhost" };                   // error — port is required
// cfg.host = "other";                                           // error — readonly

// --- Record<K, V>: exhaustive lookup table ---
type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";

const handlers: Record<HttpMethod, (req: Request) => Response> = {
  GET:    req => new Response("ok"),
  POST:   req => new Response("created"),
  PUT:    req => new Response("updated"),
  DELETE: req => new Response("deleted"),
  // PATCH: ... // error — PATCH is not a key of HttpMethod
};
// Missing a key would also be a compile error

// --- Index signature: arbitrary string keys ---
const scores: { [playerId: string]: number } = {};
scores["alice"] = 42; // OK

// --- Utility types ---
type PartialConfig = Partial<Config>;         // all fields optional
type RequiredConfig = Required<Config>;       // timeout and retries become required
type HostOnly = Pick<Config, "host">;         // { readonly host: string }
type WithoutHost = Omit<Config, "host">;      // { readonly port: number; ... }

// --- Intersection as composition ---
interface Timestamped { createdAt: Date; updatedAt: Date }
type TimestampedConfig = Config & Timestamped; // OK — both shapes required
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Mapped Types** [-> T62](T62-mapped-types.md) | Mapped types transform object shapes key-by-key; `Partial<T>`, `Required<T>`, and `Readonly<T>` are all mapped types over object shapes. Mapped types are the engine behind most utility types. |
| **Immutability Markers** [-> T32](T32-immutability-markers.md) | `readonly` on individual fields and the `Readonly<T>` utility type make object shapes immutable at the type level; both operate on record types as their primary input. |
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | Generic object types (`interface Repository<T>`) parameterize record shapes; bounds (`<T extends Config>`) constrain which object shapes can be substituted. |
| **Structural Typing** [-> T07](T07-structural-typing.md) | TypeScript checks object type compatibility structurally: any object with at least the required fields is assignable to a record type, regardless of how it was declared; extra fields are allowed in assignments from variables (but not object literals). |
| **Algebraic Data Types** [-> T01](T01-algebraic-data-types.md) | Record types serve as the product cases of discriminated unions. A `type Shape = Circle \| Rect` where each member is a record type with a `kind` discriminant field is the standard TypeScript ADT pattern. |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | Narrowing via `in` checks, discriminant field comparisons, and type predicates all operate on record types to refine which fields are known to exist in a given branch. |

## 5. Gotchas and Limitations

1. **Excess property checking only applies to object literals** — assigning an object literal with extra fields to a typed variable is a compile error, but assigning a variable of a broader type is not; this is a common source of "why does this not error?" confusion.
2. **Index signatures conflict with specific fields** — if an object type has both specific fields and an index signature, the specific field types must be assignable to the index signature's value type (`{ [key: string]: unknown; host: string }` is fine; `{ [key: string]: number; host: string }` is an error because `host` is `string`, not `number`).
3. **`Record<string, V>` is not the same as `{ [key: string]: V }`** — they are structurally equivalent but `Record<K, V>` with a union key requires all keys; `Record<string, V>` is equivalent to the index signature.
4. **Optional vs `| undefined`** — `timeout?: number` means the key may be absent entirely; `timeout: number | undefined` means the key must be present but its value may be `undefined`; these differ when iterating keys or using `"timeout" in obj`.
5. **`Partial<T>` is shallow** — it makes the top-level fields optional but does not recurse into nested object types; deeply nested optional types require a custom recursive `DeepPartial<T>` utility type.
6. **Declaration merging pitfalls** — `interface` merging allows external code to add fields to a library's interface; this is intentional for augmentation but can break exhaustiveness checks if a switch over all fields was assumed to be complete.
7. **`readonly` on index signatures** — `{ readonly [key: string]: number }` prevents writing to any key. Without `readonly`, the index signature is mutable even if the binding itself is `const`.
8. **`as const` produces a readonly literal type, not a record type** — `const cfg = { host: "localhost", port: 8080 } as const` infers `{ readonly host: "localhost"; readonly port: 8080 }`, widening is suppressed. This is useful for exhaustive lookup objects but the inferred type is structural, not nominal.
9. **`Object.freeze` is not the same as `readonly`** — `Object.freeze(obj)` enforces immutability at runtime but TypeScript only infers a `Readonly<T>` wrapper if you call it through a typed wrapper; a raw `Object.freeze(obj)` call does not automatically widen `obj`'s type to `Readonly<typeof obj>`.
10. **`satisfies` does not change the type of the binding** — it validates compatibility but the variable is still inferred at its narrowest type, not at the constraint type. Combine with an explicit annotation if you want the widened type to be the declared type.

## 6. Beginner Mental Model

Think of a TypeScript record type as a **blueprint for an object's slots**. The blueprint specifies exactly which named slots exist, what type of value fills each slot, and which slots are required vs. optional. The compiler acts as a blueprint enforcer: constructing an object with a missing required slot, putting the wrong type of value in a slot, or misspelling an optional field name in an object literal are all compile errors.

Unlike Lean structures, Rust named-field structs, or Scala case classes — all of which are **nominal** (two types with the same fields are still distinct types) — TypeScript uses **structural typing**: any object with at least the required fields is assignable to a record type, regardless of how it was declared. Two separately-declared `interface Point { x: number; y: number }` definitions are interchangeable because they have the same shape.

The closest analogue from other languages:
- `interface` / `type` ≈ Python's `TypedDict` (structural shape checking), or Scala's named tuples (structural), but with methods and generics.
- `Record<UnionKey, V>` ≈ Rust's exhaustive `match` arms: every key in the union must have an entry.
- Spread copy (`{ ...base, field: newValue }`) ≈ Rust's `..base` struct update syntax and Scala's `.copy()`.

## 7. Examples

### Example A — Creating modified copies with spread

TypeScript's equivalent of Rust's struct update syntax (`..other`) and Scala's `.copy()` is the object spread operator:

```typescript
interface ServerConfig {
  readonly host: string;
  readonly port: number;
  timeout?: number;
  retries?: number;
}

const defaults: ServerConfig = { host: "localhost", port: 5432 };

// Create a modified copy — original is untouched
const prod: ServerConfig = { ...defaults, host: "db.prod.example.com", timeout: 5_000 };
const dev: ServerConfig  = { ...defaults, port: 5433 };

// Spread is shallow: nested objects are still shared by reference.
// For deep immutability, use a recursive Readonly<T> or a library.
```

### Example B — Destructuring in function parameters

Object destructuring in function parameters works directly against the record type:

```typescript
interface Rect {
  width: number;
  height: number;
  label?: string;
}

// Destructure named fields directly in the signature
function area({ width, height }: Rect): number {
  return width * height;
}

// Destructure with a default for an optional field
function describe({ label = "unnamed", width, height }: Rect): string {
  return `${label}: ${width}×${height}`;
}

const r: Rect = { width: 10, height: 5 };
area(r);          // 50
describe(r);      // "unnamed: 10×5"
```

### Example C — `satisfies` for exhaustive lookup tables

`satisfies` validates the type without widening the inferred literal types of each value:

```typescript
type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";

// Record<HttpMethod, ...> ensures all keys are present.
// satisfies checks this while keeping the narrowest inferred type per value.
const statusCodes = {
  GET:    200,
  POST:   201,
  PUT:    200,
  DELETE: 204,
  // PATCH: 200  // error if uncommented: not a key of HttpMethod
} satisfies Record<HttpMethod, number>;

// statusCodes.GET is still inferred as 200 (literal), not number
type GetCode = typeof statusCodes["GET"];  // 200

// vs. an explicit annotation, which widens:
const statusCodesWide: Record<HttpMethod, number> = { GET: 200, POST: 201, PUT: 200, DELETE: 204 };
type GetCodeWide = typeof statusCodesWide["GET"];  // number
```

### Example D — Discriminated union of record types

Record types serve as the product cases in TypeScript's standard ADT pattern:

```typescript
interface Circle {
  kind: "circle";
  radius: number;
}

interface Rect {
  kind: "rect";
  width: number;
  height: number;
}

type Shape = Circle | Rect;

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle": return Math.PI * shape.radius ** 2;   // narrowed to Circle
    case "rect":   return shape.width * shape.height;    // narrowed to Rect
    // Missing a case here is not a compile error by default;
    // use a never-check or a linter rule for exhaustiveness [-> T01]
  }
}
```

## 8. Common Type-Checker Errors

### Missing required field

```
Type '{ host: string; }' is missing the following properties from type 'Config': port
```

**Cause:** A required field was omitted from the object literal.
**Fix:** Add the missing field, or mark it optional with `?` in the type declaration.

### Excess property on object literal

```
Object literal may only specify known properties, and 'typo' does not exist in type 'Config'
```

**Cause:** An unknown field was added directly in an object literal. This check only triggers at the object literal site, not on variable assignments [→ gotcha 1].
**Fix:** Remove the extra field, or add it to the type if it is intentional.

### Readonly violation

```
Cannot assign to 'host' because it is a read-only property.
```

**Cause:** A `readonly` field was reassigned after construction.
**Fix:** Use a spread copy (`{ ...original, host: newValue }`) to derive a new object instead.

### Wrong value type

```
Type 'string' is not assignable to type 'number'.
  Types of property 'port' are incompatible.
```

**Cause:** The value assigned to a field does not match the declared type.
**Fix:** Correct the value type or update the type annotation.

### Index signature / specific field conflict

```
Property 'host' of type 'string' is not assignable to 'string' index type 'number'.
```

**Cause:** A named field's type is incompatible with the object's index signature value type.
**Fix:** Make the named field's type assignable to the index signature value type (e.g., use `unknown` or `string | number` as the index value type), or remove the index signature.

## 9. Use-Case Cross-References

- [-> UC-02](../usecases/UC02-domain-modeling.md) Model domain entities as named record types with required and optional fields that enforce the shape of valid domain objects
- [-> UC-05](../usecases/UC05-structural-contracts.md) Define structural contracts as interfaces so that any conforming object satisfies the contract without explicit registration
- [-> UC-19](../usecases/UC19-serialization.md) Use record types with index signatures and `Record<K, V>` to type JSON-shaped serialization contracts

## 10. Source Anchors

- [TypeScript Handbook — Object Types](https://www.typescriptlang.org/docs/handbook/2/objects.html)
- [TypeScript Handbook — Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html)
- [TypeScript 4.9 Release Notes — `satisfies` operator](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html#the-satisfies-operator)
- [TypeScript Deep Dive — Index Signatures](https://basarat.gitbook.io/typescript/type-system/index-signatures)
