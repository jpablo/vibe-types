# Mapped Types & keyof/typeof

> **Since:** TypeScript 2.1 (mapped types); key remapping `as` clause since TypeScript 4.1

## 1. What It Is

Mapped types are a TypeScript-specific construct that transforms every property of an existing type into a new type using the syntax `{ [K in keyof T]: NewType }`. The iteration variable `K` ranges over all property name literal types of `T`, and the value type can be any expression involving `T[K]` or other type-level operations. Property modifiers can be added (`readonly`, `?`) or removed (`-readonly`, `-?`) in the mapped type. The `keyof T` operator produces the union of all string, number, and symbol property name literal types of `T`. The `typeof x` operator, used at the type level, produces the TypeScript type inferred for the value `x`. Since TypeScript 4.1, an `as` clause enables key remapping: `{ [K in keyof T as NewKey]: T[K] }`, where `NewKey` is computed from `K` — commonly using template literal types to rename properties.

## 2. What Constraint It Lets You Express

**Transform all properties of a type uniformly; adding new properties to the source automatically reflects in the derived mapped type.**

- `Partial<T>` makes every field optional — adding a field to `T` automatically makes it optional in `Partial<T>`.
- `Readonly<T>` prevents mutation of all fields — no manual duplication of the field list.
- Custom mapped types can enforce invariants across every property simultaneously (e.g., all values must be validators, all keys must have a companion `get` method).
- `keyof T` in a generic bound constrains a parameter to only valid property names of `T`, preventing typos at compile time.

## 3. Minimal Snippet

```typescript
// Custom mapped type: make all properties optional (same as Partial<T>)
type Optional<T> = { [K in keyof T]?: T[K] };

interface User {
  id: number;
  name: string;
  email: string;
}

type PartialUser = Optional<User>;
// { id?: number; name?: string; email?: string }

function updateUser(id: number, patch: Optional<User>): void { /* ... */ } // OK

// keyof to constrain a generic parameter — only valid property names accepted
function getField<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user: User = { id: 1, name: "Alice", email: "a@example.com" };
const name = getField(user, "name");  // OK — type is string
// const bad = getField(user, "age"); // error — "age" is not keyof User

// Key remapping with template literal (TypeScript 4.1+)
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

type UserGetters = Getters<User>;
// { getId: () => number; getName: () => string; getEmail: () => string }

// typeof at the type level
const defaultConfig = { host: "localhost", port: 3000, debug: false };
type Config = typeof defaultConfig;
// { host: string; port: number; debug: boolean }
```

### 3a. Adding and removing modifiers

The `?` and `readonly` modifiers can be added explicitly (`+?`, `+readonly`) or removed with a `-` prefix. The `+` is optional when adding — `{ [K in keyof T]?: T[K] }` and `{ [K in keyof T]+?: T[K] }` are identical.

```typescript
// -? removes optionality from every property (same as Required<T>)
type Required<T> = { [K in keyof T]-?: T[K] };

interface Config {
  host?: string;
  port?: number;
}

type StrictConfig = Required<Config>;
// { host: string; port: number }  — no longer optional

// -readonly strips the readonly modifier (mutable copy)
type Mutable<T> = { -readonly [K in keyof T]: T[K] };

type MutablePoint = Mutable<Readonly<{ x: number; y: number }>>;
// { x: number; y: number }  — writable again
```

### 3b. Key filtering with `never`

Returning `never` from the `as` clause removes that key from the output entirely. This is the standard way to build `Pick`/`Omit`-style utilities and to filter properties by value type.

```typescript
// Exclude a specific key (conceptually similar to Omit)
type OmitId<T> = { [K in keyof T as K extends "id" ? never : K]: T[K] };

type UserWithoutId = OmitId<User>;
// { name: string; email: string }

// Keep only properties whose value extends a given type
type PickByValue<T, V> = {
  [K in keyof T as T[K] extends V ? K : never]: T[K];
};

type StringFields = PickByValue<User, string>;
// { name: string; email: string }

type NumericFields = PickByValue<User, number>;
// { id: number }
```

### 3c. Non-homomorphic mapped types (iterating an explicit union)

When the `in` clause iterates a union that is **not** derived from `keyof T`, the mapped type is non-homomorphic: optional and readonly modifiers from the source type are **not** automatically copied.

```typescript
// Homomorphic — modifiers preserved from source
type Copy<T> = { [K in keyof T]: T[K] };

// Non-homomorphic — iterates an explicit union, modifiers NOT preserved
type Record<K extends PropertyKey, V> = { [P in K]: V };

// Practical example: build a type-safe event map from a union of event names
type EventNames = "click" | "focus" | "blur";

type Handlers = { [E in EventNames]: (e: Event) => void };
// { click: (e: Event) => void; focus: ...; blur: ... }
// No source type to inherit modifiers from, so all keys are required and mutable.
```

### 3d. How built-in utility types are implemented

Understanding the underlying mapped types makes it easier to build custom variants:

```typescript
// Partial<T> — all properties optional
type Partial<T> = { [K in keyof T]?: T[K] };

// Required<T> — all properties required
type Required<T> = { [K in keyof T]-?: T[K] };

// Readonly<T> — all properties readonly
type Readonly<T> = { readonly [K in keyof T]: T[K] };

// Record<K, V> — non-homomorphic, maps union K to value V
type Record<K extends PropertyKey, V> = { [P in K]: V };

// Pick<T, K> — keep only keys K from T
type Pick<T, K extends keyof T> = { [P in K]: T[P] };

// Omit<T, K> — drop keys K from T (uses key filtering via Exclude)
type Omit<T, K extends PropertyKey> = Pick<T, Exclude<keyof T, K>>;
```

### 3e. Recursive (deep) mapped types

Mapped types can be made recursive to transform nested structures. TypeScript evaluates them lazily, so self-referential types are allowed as long as the recursion is guarded by a conditional.

```typescript
type DeepReadonly<T> = {
  readonly [K in keyof T]: T[K] extends object ? DeepReadonly<T[K]> : T[K];
};

interface Nested {
  id: number;
  address: { city: string; zip: string };
}

type FrozenNested = DeepReadonly<Nested>;
// { readonly id: number; readonly address: { readonly city: string; readonly zip: string } }

// Deep partial — useful for nested patch/merge operations
type DeepPartial<T> = {
  [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K];
};
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Conditional types** [-> T41](T41-match-types.md) | Conditional types compose inside mapped type values: `{ [K in keyof T]: T[K] extends string ? "text" : "other" }` |
| **Record types** [-> T31](T31-record-types.md) | Records are the primary input shape; mapped types derive structural variants without duplicating field lists |
| **Template literal types** [-> T63](T63-template-literal-types.md) | The `as` key-remapping clause uses template literals to rename properties (e.g., `get${Capitalize<K>}`) |
| **Generics & bounds** [-> T04](T04-generics-bounds.md) | `K extends keyof T` is the idiomatic bound for a generic parameter constrained to property names |
| **Immutability markers** [-> T32](T32-immutability-markers.md) | The `readonly` and `-readonly` modifiers in mapped types add or strip immutability from all properties at once |

## 5. Gotchas and Limitations

1. **Homomorphic vs. non-homomorphic** — mapped types that use `keyof T` are "homomorphic" and automatically preserve optional/readonly modifiers from the source; non-homomorphic mapped types (using a separate union) do not preserve modifiers.
2. **`keyof` on `any`** — `keyof any` is `string | number | symbol`, not a useful constraint; accidentally typing a generic as `any` silently eliminates key safety.
3. **Symbol keys** — `keyof T` includes symbol keys; `string & keyof T` filters to only string keys, which is required for template literal key remapping.
4. **`as` clause cannot produce duplicate keys** — if the remapping expression produces the same key for two different `K` values, the properties are merged (last wins), which may silently lose information.
5. **`typeof` on functions** — `typeof fn` captures the full overloaded signature, but mapped types over function-valued properties may not preserve overloads correctly.
6. **`+` modifier is implicit** — `{ [K in keyof T]+?: T[K] }` and `{ [K in keyof T]?: T[K] }` are identical; the `+` prefix exists for symmetry with `-` but is rarely written explicitly.
7. **Recursive mapped types and arrays** — `DeepReadonly<T>` applied naively to `T[K] extends object` will recurse into arrays and `Date` objects, converting them to odd shapes. Guard with `T[K] extends object ? (T[K] extends any[] ? T[K] : DeepReadonly<T[K]>) : T[K]` or check for specific types to exclude.
8. **`PickByValue` and distributivity** — filtering keys by value type works when `T[K] extends V` is a simple check, but union value types can produce unexpected results because the `extends` check distributes over unions. Use `[T[K]] extends [V]` (wrapped) to suppress distribution when needed.

## 6. Use-Case Cross-References

- [-> UC-19](../usecases/UC19-serialization.md) Repository `patch` parameters use `Partial<Entity>` derived via mapped types
- [-> UC-06](../usecases/UC06-immutability.md) Builder pattern derives optional/required config variants from a single interface
- [-> UC-02](../usecases/UC02-domain-modeling.md) AST node transformer maps over every node type uniformly
- [-> UC-07](../usecases/UC07-callable-contracts.md) Event handler maps use key remapping to derive `on${EventName}` handler types
