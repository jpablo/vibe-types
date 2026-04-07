# Variadic Tuples & Spread Types

> **Since:** TypeScript 4.0 (variadic tuple types)

## 1. What It Is

TypeScript 4.0 introduced **variadic tuple types**: a generic type parameter constrained to `extends unknown[]` can be spread inside a tuple literal, producing tuples of statically known but variable length. The syntax `[A, ...T, B]` where `T extends unknown[]` means "a tuple that starts with `A`, ends with `B`, and has whatever elements `T` contributes in the middle." Combined with `infer` in tuple position, this enables type-level list operations: extracting the first element, the rest, the last, or the init. Variadic tuples also underlie rest parameters in function types, enabling strongly-typed `bind`, `partial`, `curry`, and `concat` operations that preserve precise per-position element types. Unlike Python's `ParamSpec` (which captures a whole parameter list as a unit), TypeScript achieves parameter-list manipulation through variadic tuples directly in function signatures; decorator signature preservation uses conditional types or overloads.

## 2. What Constraint It Lets You Express

**Express typed operations over tuples of statically unknown but bounded length; every element's type is preserved individually through transformations rather than collapsed to a union or `any[]`.**

- `type Tail<T extends unknown[]> = T extends [unknown, ...infer R] ? R : never` — the return type is exactly "T without its first element," preserving all remaining positions.
- A typed `concat<A extends unknown[], B extends unknown[]>(a: A, b: B): [...A, ...B]` — the compiler knows the result has exactly `A.length + B.length` elements, typed individually.
- Rest parameters typed as `...args: T` where `T extends unknown[]` allow forwarding all arguments to another function with full type safety.

## 3. Minimal Snippet

```typescript
// --- Tuple decomposition via infer ---
type Head<T extends unknown[]> = T extends [infer H, ...unknown[]] ? H : never;
type Tail<T extends unknown[]> = T extends [unknown, ...infer R] ? R : never;
type Last<T extends unknown[]> = T extends [...unknown[], infer L] ? L : never;

type H = Head<[string, number, boolean]>; // string
type T = Tail<[string, number, boolean]>; // [number, boolean]
type L = Last<[string, number, boolean]>; // boolean

// --- Typed concat ---
function concat<A extends unknown[], B extends unknown[]>(
  a: [...A],
  b: [...B],
): [...A, ...B] {
  return [...a, ...b] as [...A, ...B]; // OK
}

const result = concat([1, "two"] as [number, string], [true] as [boolean]);
// result: [number, string, boolean]

// error: concat(1, [2]); // error — first arg must be an array

// --- Prepend: add an element at the front ---
type Prepend<T, Arr extends unknown[]> = [T, ...Arr];
type WithId = Prepend<number, [string, boolean]>; // [number, string, boolean]

// --- Strongly-typed partial application ---
type DropFirst<T extends unknown[]> = T extends [unknown, ...infer R] ? R : never;

function partial<F extends (...args: any[]) => any>(
  fn: F,
  first: Parameters<F>[0],
): (...args: DropFirst<Parameters<F>>) => ReturnType<F> {
  return (...rest) => fn(first, ...rest);
}

function add(a: number, b: number): number { return a + b; }
const add5 = partial(add, 5);
const sum = add5(3); // OK — number
// add5("x"); // error — "x" is not assignable to number
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Callable Typing** [-> T22](T22-callable-typing.md) | Rest parameters typed as `...args: T extends unknown[]` directly use variadic tuples; `Parameters<F>` returns the parameter tuple, which variadic patterns can then deconstruct. |
| **Conditional Types** [-> T41](T41-match-types.md) | `infer` inside a tuple pattern (`T extends [infer H, ...infer R]`) is a conditional type; the two features are inseparable for tuple-level operations. |
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | The canonical bound for variadic generics is `T extends unknown[]`; without this constraint the spread `...T` is not permitted inside a tuple literal. |

## 5. Gotchas and Limitations

1. **Spread must be at most one rest element** — a tuple type can contain at most one variadic (`...T`) spread; `[...A, ...B]` is only valid in a *value* spread or as a function return type built from two separate generics, not as a type literal with two `...infer` positions simultaneously.
2. **Length inference fails for generic tuples** — TypeScript knows the length of concrete tuples but not of `T extends unknown[]`; code that branches on `T["length"]` will not narrow correctly in the general case.
3. **Optional and rest elements interact subtly** — mixing optional elements (`T?`) and rest elements in the same tuple can produce surprising assignability behavior; TypeScript 4.2+ relaxed some restrictions but ordering still matters.
4. **Inference from `[...A]` vs `A`** — wrapping an argument in `[...A]` (the "rest tuple" trick) hints to TypeScript to infer a tuple type rather than an array type; omitting it may cause TypeScript to infer `string[]` instead of `[string, number]`.
5. **Deep nesting hits recursion limits** — recursive tuple manipulation types (`Reverse<T>`, `Zip<A, B>`) can exceed TypeScript's instantiation depth for long tuples; keep tuple lengths bounded in practice.

## 6. Use-Case Cross-References

- [-> UC-07](../usecases/UC07-callable-contracts.md) Type-safe higher-order functions that forward arguments with full per-position typing
- [-> UC-04](../usecases/UC04-generic-constraints.md) Generic constraints that preserve tuple structure through transformations
