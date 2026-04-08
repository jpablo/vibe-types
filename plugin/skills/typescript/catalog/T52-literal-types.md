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
| **Callable Typing / Overloads** [-> T22](T22-callable-typing.md) | Function overload signatures keyed on literal parameters give different return types per literal value — the compiler selects the matching overload at the call site. |
| **Never / Bottom** [-> T34](T34-never-bottom.md) | After narrowing every literal branch in a `switch`, the residual type is `never`. `assertNever()` proves exhaustiveness: the compiler errors if any case is unhandled. |

## 5. Gotchas and Limitations

1. **Object literal widening** — `const obj = { status: "pending" }` infers `{ status: string }` even with `const`; only primitive bindings stay literal. Use `as const` or annotate with the literal type explicitly.
2. **Freshness / excess property checking** — literal types interact with freshness: a freshly created object literal undergoes excess property checking, but widening happens before the type flows to most positions.
3. **Template literal types can explode** — a union of many string literals combined with a template produces the full Cartesian product; very large unions cause compiler slowdowns.
4. **Numeric literal enum pitfall** — TypeScript's `enum` does not produce numeric literal types in the same way; `enum Color { Red = 0 }` gives `Color.Red`, not `0`. Use `as const` objects for true literal enum patterns.
5. **Const type parameters require TypeScript 5.0** — in older codebases, callers must use `as const` or the function must use complex conditional type tricks to preserve literals.
6. **`satisfies` vs annotation** — `const cfg = { mode: "production" } satisfies Config` preserves the literal type of `mode` while checking assignability; a plain annotation `const cfg: Config = ...` widens the literal.

## 6. Beginner Mental Model

Think of a literal type as a **name badge that IS the value itself**. The type `string` is "anyone with text can enter." The type `"GET" | "POST"` is "only these two exact strings may enter — the compiler is the bouncer." When TypeScript sees `=== "GET"` in a conditional, it narrows the type in that branch by striking that option from the remaining alternatives.

Compared to other languages: Scala 3's singleton types work the same way (`42 <: Int`). Python's `Literal["GET"]` is structurally identical but enforced only by the type checker, not the runtime — same as TypeScript. Rust has no literal types; it uses enums instead.

## 7. Concrete Examples

### Example A — Overload dispatch keyed on a literal

```typescript
// Different return type depending on which literal is passed
function openFile(mode: "r"): string;
function openFile(mode: "rb"): Uint8Array;
function openFile(mode: "r" | "rb"): string | Uint8Array {
  if (mode === "r") return "text content";
  return new Uint8Array(0);
}

const text = openFile("r");    // type: string
const data = openFile("rb");   // type: Uint8Array
// openFile("w");               // error — No overload matches "Literal['w']"
```

### Example B — Boolean literal discrimination

`true` and `false` are distinct singleton types, enabling overloads that mirror Python's `Literal[True]` / `Literal[False]` pattern:

```typescript
function fetch(url: string, raw: true): Uint8Array;
function fetch(url: string, raw?: false): string;
function fetch(url: string, raw?: boolean): string | Uint8Array {
  const bytes = new Uint8Array(0);
  return raw ? bytes : "decoded content";
}

const page = fetch("https://example.com");           // type: string
const blob = fetch("https://example.com", true);     // type: Uint8Array
```

### Example C — Exhaustive `switch` with `assertNever`

After narrowing every branch the residual type is `never`. Passing it to `assertNever` proves exhaustiveness at compile time:

```typescript
type Status = "pending" | "fulfilled" | "rejected";

function assertNever(x: never): never {
  throw new Error(`Unhandled status: ${JSON.stringify(x)}`);
}

function describe(status: Status): string {
  switch (status) {
    case "pending":   return "In progress";
    case "fulfilled": return "Done";
    case "rejected":  return "Failed";
    default:          return assertNever(status);
    // Adding a new Status member without updating this switch is a compile error
  }
}
```

## 8. Common Type-Checker Errors

### `Type 'string' is not assignable to type '"north" | "south" | ...`

```typescript
let dir = "north";          // inferred as string (let widens)
move(dir);                  // error: string is not assignable to Direction
```

**Cause:** A plain `string` variable was passed where a literal union is expected.
**Fix:** Annotate with the literal type (`const dir: Direction = "north"`), use `as const`, or pass the literal directly.

### `Argument of type '"up"' is not assignable to parameter of type 'Direction'`

**Cause:** The specific literal is not a member of the union.
**Fix:** Use one of the declared values, or add the new value to the union type definition.

### `No overload matches this call`

**Cause:** The literal passed doesn't match any overload signature.
**Fix:** Add an overload for the new value, widen the accepted literal set, or correct the call site.

## 9. Use-Case Cross-References

- [-> UC-03](../usecases/UC03-exhaustiveness.md) Exhaustive handling of a closed set of string or numeric values
- [-> UC-02](../usecases/UC02-domain-modeling.md) Model domain status codes and event names as literal union types
- [-> UC-07](../usecases/UC07-callable-contracts.md) Overload dispatch keyed on literal parameters for return-type narrowing
- [-> UC-09](../usecases/UC09-builder-config.md) Builder and config objects that constrain option values to specific literals

## 10. Source Anchors

- [TypeScript Handbook — Literal Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#literal-types)
- [TypeScript Handbook — `as const`](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#the-as-const-assertion)
- [TypeScript 5.0 — Const Type Parameters](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#const-type-parameters)
- [TypeScript Deep Dive — Literal Types](https://basarat.gitbook.io/typescript/type-system/literal-types)
