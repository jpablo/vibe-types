# Immutability Markers

> **Since:** TypeScript 2.0 (`readonly`); `as const` since TypeScript 3.4

## 1. What It Is

TypeScript provides several compile-time mechanisms for expressing immutability. The **`readonly`** modifier on a property or parameter prevents reassignment after initialization — it does not guarantee deep immutability of the referenced value. **`ReadonlyArray<T>`** (equivalently `readonly T[]`) removes all mutating methods (`push`, `pop`, `splice`, etc.) from the array type. **`as const`** is an assertion that narrows an object literal or array to its most precise literal type and marks all properties and elements as `readonly`, making it the idiomatic way to declare compile-time constants. The **`Readonly<T>`** utility type wraps all properties of an object type with `readonly` in one step. Note that `Object.freeze()` enforces immutability at runtime, but TypeScript does not automatically infer `readonly` from a `freeze()` call unless paired with `as const`.

## 2. What Constraint It Lets You Express

**Prevent reassignment of properties and array mutations after construction at compile time; `as const` narrows literals to their exact types so they cannot be widened.**

- A `readonly` property on a class can be assigned in the constructor but not anywhere else; the compiler rejects all post-construction assignments.
- `readonly T[]` prevents `push`, `pop`, `sort`, and other in-place mutations on the array type; values can still be read and iterated.
- `as const` on a string literal (`"GET" as const`) preserves the exact literal type `"GET"` rather than widening to `string`, which is essential for discriminated unions and `Record<K, V>` exhaustiveness.

## 3. Minimal Snippet

```typescript
// --- readonly property ---
interface Point {
  readonly x: number;
  readonly y: number;
}

const p: Point = { x: 1, y: 2 };
// p.x = 3; // error — cannot assign to 'x' because it is a read-only property

// --- ReadonlyArray ---
function sum(nums: readonly number[]): number {
  // nums.push(4); // error — push does not exist on readonly number[]
  return nums.reduce((a, b) => a + b, 0);
}

const xs = [1, 2, 3];
console.log(sum(xs)); // OK — mutable arrays are assignable to readonly

// --- as const: literal narrowing + readonly ---
const METHODS = ["GET", "POST", "PUT", "DELETE"] as const;
// METHODS is: readonly ["GET", "POST", "PUT", "DELETE"]
type HttpMethod = (typeof METHODS)[number]; // OK — "GET" | "POST" | "PUT" | "DELETE"

const CONFIG = {
  host: "localhost",
  port: 8080,
} as const;
// CONFIG.host is "localhost" (literal), not string
// CONFIG.port is 8080 (literal), not number
// CONFIG.host = "other"; // error — readonly

// --- Readonly<T> utility type ---
interface Config {
  host: string;
  port: number;
  timeout?: number;
}

type FrozenConfig = Readonly<Config>;
// Equivalent to: { readonly host: string; readonly port: number; readonly timeout?: number }

function processConfig(cfg: FrozenConfig) {
  // cfg.host = "other"; // error — readonly
  return `${cfg.host}:${cfg.port}`;
}
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Literal Types** [-> T52](T52-literal-types.md) | `as const` is the bridge between immutability and literal types: it simultaneously marks properties `readonly` and narrows their types to exact literals, preventing widening. |
| **Record Types & Interfaces** [-> T31](T31-record-types.md) | `readonly` fields on record types and `Readonly<T>` compose naturally; `as const` applied to object literals produces `Readonly`-equivalent types with literal-precision values. |
| **Encapsulation** [-> T21](T21-encapsulation.md) | `readonly` is a form of encapsulation: it allows external code to read a property but not modify it, expressing the ownership model of an object without hiding the field entirely. |

## 5. Gotchas and Limitations

1. **`readonly` is shallow** — `readonly items: string[]` prevents reassigning the `items` reference but does not prevent `items.push("x")`; use `readonly string[]` or `ReadonlyArray<string>` to make the contents immutable at the type level.
2. **`Readonly<T>` is also shallow** — `Readonly<{ nested: { x: number } }>` makes `nested` readonly (cannot reassign the reference) but not `nested.x`; use a recursive `DeepReadonly<T>` for deep immutability.
3. **`Object.freeze` is not inferred as `readonly`** — TypeScript does not propagate `readonly` from `Object.freeze(obj)` calls; use `as const` for literal objects or `Object.freeze` + explicit `Readonly<T>` annotation if runtime immutability is also needed.
4. **Mutable arrays are assignable to `readonly` but not vice versa** — `number[]` is assignable to `readonly number[]` (you can pass a mutable array where a readonly is expected), but `readonly number[]` is not assignable to `number[]` (you cannot give a readonly array to a function that mutates it).
5. **`as const` widens on re-assignment** — `let x = "hello" as const` does not work as expected because `let` allows reassignment; use `const x = "hello" as const` or annotate the variable explicitly.
6. **`as const` on deeply nested objects** — `as const` is fully recursive; all nested properties are marked `readonly` and their types narrowed to literals, which can be surprising for large configuration objects where some values are meant to be runtime-variable.

## 6. Use-Case Cross-References

- [-> UC-06](../usecases/UC06-immutability.md) Use `readonly`, `as const`, and `ReadonlyArray` to encode immutability constraints in data structures and function signatures
- [-> UC-02](../usecases/UC02-domain-modeling.md) Model domain constants and value objects with `as const` and `Readonly<T>` to prevent accidental mutation of core domain data
