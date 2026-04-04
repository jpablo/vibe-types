# Literal Types

> **Since:** TypeScript 1.8 (string literal types); numeric and boolean literals since TypeScript 2.0

## 1. What It Is

Every concrete literal value in TypeScript has a corresponding **singleton type** inhabited by exactly that one value. The string `"north"` has type `"north"`, the number `42` has type `42`, and `true` has type `true`. Literal types are subtypes of their respective primitive types: `"north"` is assignable to `string`, but `string` is not assignable to `"north"`. Unions of literal types — `"north" | "south" | "east" | "west"` — model closed enumerations. The `as const` assertion (TypeScript 3.4) infers literal types throughout an object or array, preventing the compiler from widening `{ direction: "north" }` to `{ direction: string }`. TypeScript 5.0 added **const type parameters** (`<const T>`), which infer literal types for generic arguments without requiring `as const` at the call site. Literal types are the foundation for discriminated unions, template literal types, and exhaustiveness checking.

## 2. What Constraint It Lets You Express

**Restrict a type to a specific set of values; the compiler rejects every other value at compile time without any runtime check.**

- `type Direction = "north" | "south" | "east" | "west"` — passing `"up"` is a compile error.
- `as const` on an array produces a `readonly` tuple of literal types, enabling typed lookup tables and `satisfies`-validated registries.
- Const type parameters allow generic functions to capture exact literal types passed by the caller without burdening the caller with `as const`.

## 3. Minimal Snippet

```typescript
// --- String literal union ---
type Direction = "north" | "south" | "east" | "west";

function move(direction: Direction): void {
  console.log(`Moving ${direction}`);
}

move("north"); // OK
move("south"); // OK
// move("up");  // error — "up" is not assignable to Direction

// --- Literal widening without as const ---
const dir1 = "north";        // type: "north"  (const — not widened)
let  dir2 = "north";         // type: string   (let — widened)
const obj = { dir: "north" }; // type: { dir: string } — object literal widens!

// --- as const: suppress widening throughout ---
const DIRECTIONS = ["north", "south", "east", "west"] as const;
//    type: readonly ["north", "south", "east", "west"]

type DirectionFromArray = typeof DIRECTIONS[number]; // "north" | "south" | "east" | "west"

// --- as const on object: preserve all literal types ---
const CONFIG = {
  host: "localhost",
  port: 8080,
  mode: "production",
} as const;
// type: { readonly host: "localhost"; readonly port: 8080; readonly mode: "production" }

// CONFIG.mode = "development"; // error — cannot assign to a readonly property

// --- Numeric literal type ---
type Bit = 0 | 1;
function xor(a: Bit, b: Bit): Bit {
  return (a ^ b) as Bit; // OK
}
// xor(2, 0); // error — 2 is not assignable to Bit

// --- const type parameter (TypeScript 5.0) ---
function first<const T extends readonly unknown[]>(arr: T): T[0] {
  return arr[0];
}
const val = first(["a", "b", "c"]); // type: "a"  (literal inferred without as const)
// Without <const T>, val would be: string

// --- Boolean literal ---
type Flag = true | false; // equivalent to boolean, but useful in conditional types
type IsTrue<T> = T extends true ? "yes" : "no";
type A = IsTrue<true>;  // "yes"
type B = IsTrue<false>; // "no"
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Algebraic Data Types** [-> T01](T01-algebraic-data-types.md) | Discriminant fields in discriminated unions must be literal types; without them, TypeScript cannot narrow the union in a `switch` statement. |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | Equality checks (`=== "north"`) narrow a union to the matching literal member; the compiler tracks which literals have been eliminated in each branch. |
| **Template Literal Types** [-> T63](T63-template-literal-types.md) | Template literal types are built by combining string literal types; `"get" | "set"` combined with `"Name" | "Age"` produces `"getName" | "getAge" | "setName" | "setAge"`. |
| **Immutability Markers** [-> T32](T32-immutability-markers.md) | `as const` simultaneously infers literal types and adds `readonly` to all properties and array elements; the two effects are inseparable. |

## 5. Gotchas and Limitations

1. **Object literal widening** — `const obj = { status: "pending" }` infers `{ status: string }` even with `const`; only primitive bindings stay literal. Use `as const` or annotate with the literal type explicitly.
2. **Freshness / excess property checking** — literal types interact with freshness: a freshly created object literal undergoes excess property checking, but widening happens before the type flows to most positions.
3. **Template literal types can explode** — a union of many string literals combined with a template produces the full Cartesian product; very large unions cause compiler slowdowns.
4. **Numeric literal enum pitfall** — TypeScript's `enum` does not produce numeric literal types in the same way; `enum Color { Red = 0 }` gives `Color.Red`, not `0`. Use `as const` objects for true literal enum patterns.
5. **Const type parameters require TypeScript 5.0** — in older codebases, callers must use `as const` or the function must use complex conditional type tricks to preserve literals.
6. **`satisfies` vs annotation** — `const cfg = { mode: "production" } satisfies Config` preserves the literal type of `mode` while checking assignability; a plain annotation `const cfg: Config = ...` widens the literal.

## 6. Use-Case Cross-References

- [-> UC-03](../usecases/UC03-exhaustiveness.md) Exhaustive handling of a closed set of string or numeric values
- [-> UC-02](../usecases/UC02-domain-modeling.md) Model domain status codes and event names as literal union types
- [-> UC-09](../usecases/UC09-builder-config.md) Builder and config objects that constrain option values to specific literals
