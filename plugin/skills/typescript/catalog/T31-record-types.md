# Record Types & Object Shapes

> **Since:** TypeScript 1.0

## 1. What It Is

TypeScript represents named-field data through several related constructs. An **`interface`** is an open, declaration-mergeable object shape: `interface User { name: string; age: number }`. A **type alias object literal** (`type User = { name: string; age: number }`) is closed and cannot be reopened. **`Record<K, V>`** is a homogeneous map where every key of type `K` maps to a value of type `V` — a shorthand for `{ [key in K]: V }`. **Index signatures** (`{ [key: string]: V }`) describe objects with an arbitrary number of string or number keys, all mapping to `V`. Object shapes support **optional properties** (`?`), **readonly properties** (`readonly`), method signatures, and the ability to be composed via intersection (`TypeA & TypeB`). The built-in **utility types** `Pick<T, K>`, `Omit<T, K>`, `Partial<T>`, `Required<T>`, and `NonNullable<T>` operate on object shapes to produce new derived types.

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

## 5. Gotchas and Limitations

1. **Excess property checking only applies to object literals** — assigning an object literal with extra fields to a typed variable is a compile error, but assigning a variable of a broader type is not; this is a common source of "why does this not error?" confusion.
2. **Index signatures conflict with specific fields** — if an object type has both specific fields and an index signature, the specific field types must be assignable to the index signature's value type (`{ [key: string]: unknown; host: string }` is fine; `{ [key: string]: number; host: string }` is an error because `host` is `string`, not `number`).
3. **`Record<string, V>` is not the same as `{ [key: string]: V }`** — they are structurally equivalent but `Record<K, V>` with a union key requires all keys; `Record<string, V>` is equivalent to the index signature.
4. **Optional vs `| undefined`** — `timeout?: number` means the key may be absent entirely; `timeout: number | undefined` means the key must be present but its value may be `undefined`; these differ when iterating keys or using `"timeout" in obj`.
5. **`Partial<T>` is shallow** — it makes the top-level fields optional but does not recurse into nested object types; deeply nested optional types require a custom recursive `DeepPartial<T>` utility type.
6. **Declaration merging pitfalls** — `interface` merging allows external code to add fields to a library's interface; this is intentional for augmentation but can break exhaustiveness checks if a switch over all fields was assumed to be complete.

## 6. Use-Case Cross-References

- [-> UC-02](../usecases/UC02-domain-modeling.md) Model domain entities as named record types with required and optional fields that enforce the shape of valid domain objects
- [-> UC-05](../usecases/UC05-structural-contracts.md) Define structural contracts as interfaces so that any conforming object satisfies the contract without explicit registration
- [-> UC-19](../usecases/UC19-serialization.md) Use record types with index signatures and `Record<K, V>` to type JSON-shaped serialization contracts
