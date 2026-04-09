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
|---|-|
| **Callable Typing** [-> T22](T22-callable-typing.md) | Rest parameters typed as `...args: T extends unknown[]` directly use variadic tuples; `Parameters<F>` returns the parameter tuple, which variadic patterns can then deconstruct. |
| **Conditional Types** [-> T41](T41-match-types.md) | `infer` inside a tuple pattern (`T extends [infer H, ...infer R]`) is a conditional type; the two features are inseparable for tuple-level operations. |
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | The canonical bound for variadic generics is `T extends unknown[]`; without this constraint the spread `...T` is not permitted inside a tuple literal. |
| **Variance & Subtyping** [-> T08](T08-variance-subtyping.md) | Tuple types are covariant in their element types; spreading generics preserves variance position-by-position, so a `[string, number]` is assignable to `[string \| null, number \| null]` but not vice versa. |

## 5. When to Use It

- **Function signature preservation**: When wrapping functions (decorators, HOFs) and you need to preserve exact parameter types.
- **Type-level list manipulation**: When extracting/modifying tuple elements (`Head`, `Tail`, `Reverse`) at the type level.
- **Typed array concatenation**: When merging tuples while preserving individual element types.
- **Partial application / currying**: When creating functions with reduced arity but precise typing.

```typescript
// ✅ Decorator preserving signature
function logArgs<F extends (...args: any[]) => any>(fn: F): F {
  return ((...args: Parameters<F>): ReturnType<F> => {
    console.log(args);
    return fn(...args);
  }) as F;
}

// ✅ Type-level tuple operations
type DropLast<T extends unknown[]> = 
  T extends [...infer Init, unknown] ? Init : never;
type Dropped = DropLast<[1, 2, 3]>; // [1, 2]

// ✅ Typed concatenation
function append<A extends unknown[], B>(arr: A, val: B): [...A, B] {
  return [...arr, val] as [...A, B];
}
```

## 6. When NOT to Use It

- **Simple array operations**: When you just need a homogeneous `T[]` or don't care about per-element types.
- **Runtime-only logic**: When the operation only happens at runtime with no type-level benefit.
- **Unbounded/unknown lengths**: When tuple length is truly dynamic and type-level tracking adds no value.
- **Simple collections**: When working with bags of items where order/position doesn't matter.

```typescript
// ❌ Overkill: just need T[]
function sum<T extends number[]>(arr: T): number {
  return arr.reduce((a, b) => a + b, 0);
}
// Prefer: function sum(arr: number[]): number { ... }

// ❌ Overkill: runtime-only filtering
function filterEven<T extends unknown[]>(arr: T): T {
  return arr.filter(x => typeof x === 'number' && x % 2 === 0) as T;
  // Type system can't express "subset of original" meaningfully
}
// Prefer: function filterEven(arr: number[]): number[] { ... }

// ❌ Overkill: order doesn't matter
function processItems<T extends unknown[]>(items: T): void {
  items.forEach(item => console.log(item));
  // No benefit tracking [A, B, C] vs [B, A, C]
}
// Prefer: function processItems(items: unknown[]): void { ... }
```

## 7. Antipatterns When Using It

```typescript
// ❌ Deeply recursive types hitting compiler limits
type BadReverse<T extends unknown[]> =
  T extends [infer H, ...infer R]
    ? [...BadReverse<R>, H]
    : [];
type R = BadReverse<[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]>;
// Error: Type instantiation is excessively deep

// ✅ Fix: Accept limitations, use arrays for long sequences
type Reverse<A extends unknown[], R extends unknown[] = []> =
  A extends [infer H, ...infer T]
    ? Reverse<T, [H, ...R]>
    : R;

// ❌ Excessive typing obscuring simple logic
type ComplexTransform<T extends unknown[]> = 
  T extends [infer H, ...infer R]
    ? H extends string
      ? [H.toUpperCase(), ...ComplexTransform<R>]
      : [H, ...ComplexTransform<R>]
    : [];
// Type-level computation with no runtime equivalent
// ✅ Prefer runtime implementation with simple types

// ❌ Forcing tuple types where array is natural
function badPush<T extends unknown[]>(arr: T, val: T[number]): [...T, T[number]] {
  return [...arr, val];
}
// Creates [number, number, number] instead of natural number[]
// ✅ Use: function push(arr: number[], val: number): number[]

// ❌ Ignoring variance causing assignability issues
type BadHead<T extends unknown[]> = T extends [infer H, ...unknown[]] ? H : never;
const arr: [string, number] = ["a", 1];
const h: BadHead<[string | number]> = arr; // May cause issues
// Be explicit about constraints: T extends [H, ...R]
```

## 8. Antipatterns Where This Technique Fixes Them

```typescript
// ❌ Antipattern: Loss of type information through AnyArray
function badMap<T>(arr: T[], fn: (item: any) => any): any[] {
  return arr.map(fn);
}
badMap(["a", 1], x => x); // Result is any[]

// ✅ Fix with variadic tuples
function map<A extends unknown[], B>(
  arr: A,
  fn: (item: A[number]) => B
): B[] {
  return arr.map(fn);
}
// Still loses per-position precision but no `any`

// ✨ Better: preserve tuple structure when mapping known-length tuples
function zipWith<A extends unknown[], B extends unknown[], C>(
  a: A,
  b: B,
  fn: (x: A[number], y: B[number]) => C
): C[] {
  return a.map((x, i) => fn(x, b[i] as B[number]));
}

// ❌ Antipattern: Function wrappers losing parameter types
function memoize(fn: Function): Function {
  const cache = new Map();
  return function(...args: any[]) {
    const key = JSON.stringify(args);
    return cache.has(key) ? cache.get(key) : cache.set(key, fn(...args)).get(key);
  };
}
const add = (a: number, b: number) => a + b;
const memoized = memoize(add);
memoized("x", "y"); // Should error but doesn't!

// ✅ Fix with variadic tuples
function memoize<F extends (...args: any[]) => any>(fn: F): F {
  const cache = new Map<string, unknown>();
  const wrapper = ((...args: Parameters<F>): ReturnType<F> => {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key) as ReturnType<F>;
    const result = fn(...args);
    cache.set(key, result);
    return result as ReturnType<F>;
  }) as F;
  return wrapper;
}
const memoizedAdd = memoize(add);
memoizedAdd("x", "y"); // Error: Argument of type 'string' is not assignable to parameter of type 'number'

// ❌ Antipattern: Array methods with incompatible return types
function head<T>(arr: T[]): T | undefined {
  return arr[0];
}
head(["a", 1, true]); // Type is (string | number | boolean) | undefined

// ✅ When you need to preserve the first element's exact type
type TupleHead<T extends unknown[]> = T extends [infer H, ...unknown[]] ? H : never;
function tupleHead<T extends unknown[]>(arr: T) {
  return arr[0] as TupleHead<T>;
}
tupleHead(["a", 1, true]); // Type is string

// ❌ Antipattern: Composing functions with incompatible signatures
const compose = (f: Function, g: Function) => (x: any) => f(g(x));
// No type safety in composition chain

// ✅ Fix with variadic tuples
function compose<A, B, C>(
  f: (b: B) => C,
  g: (...args: A) => B
): (...args: A) => C {
  return (...args: A): C => f(g(...args));
}
const inc = (x: number) => x + 1;
const toString = (x: number) => x.toString();
const addThenString = compose(toString, inc);
addThenString(21); // OK: "22"
```

## 11. Labeled Tuple Elements

TypeScript 4.0 also introduced **labeled tuple elements** — named positions in a tuple type that survive IDE hover, error messages, and destructuring:

```typescript
// Without labels: positional noise in tooltips
type Range = [number, number];

// With labels: intent is visible in editors and errors
type LabeledRange = [start: number, end: number];

// Labels propagate through variadic spreading
type WithTimestamp<T extends unknown[]> = [timestamp: number, ...T];
type TimestampedEvent = WithTimestamp<[event: string, payload: unknown]>;
// => [timestamp: number, event: string, payload: unknown]

// Useful for rest-parameter wrappers: the editor shows names, not just types
function createRange(start: number, end: number): LabeledRange {
  return [start, end];
}
const [s, e] = createRange(0, 100); // hover: "s: number" (named "start")
```

Labels are purely informational — they do not affect assignability. A `[start: number, end: number]` is interchangeable with `[number, number]` at the type level. Their value is ergonomic: better error messages and IDE completions in wrapper code.

## 12. Gotchas and Limitations

1. **Spread must be at most one rest element** — a tuple type can contain at most one variadic (`...T`) spread; `[...A, ...B]` is only valid in a *value* spread or as a function return type built from two separate generics, not as a type literal with two `...infer` positions simultaneously.
2. **Length inference fails for generic tuples** — TypeScript knows the length of concrete tuples but not of `T extends unknown[]`; code that branches on `T["length"]` will not narrow correctly in the general case.
3. **Optional and rest elements interact subtly** — mixing optional elements (`T?`) and rest elements in the same tuple can produce surprising assignability behavior; TypeScript 4.2+ relaxed some restrictions but ordering still matters.
4. **Inference from `[...A]` vs `A`** — wrapping an argument in `[...A]` (the "rest tuple" trick) hints to TypeScript to infer a tuple type rather than an array type; omitting it may cause TypeScript to infer `string[]` instead of `[string, number]`.
5. **Deep nesting hits recursion limits** — recursive tuple manipulation types (`Reverse<T>`, `Zip<A, B>`) can exceed TypeScript's instantiation depth for long tuples; keep tuple lengths bounded in practice.

## 13. Beginner Mental Model

Think of a variadic tuple as a **typed rubber band** stretched around a sequence of values. A regular generic (`T`) is one blank slot; a variadic generic (`T extends unknown[]`) is a row of blank slots whose length and per-slot types are determined at the call site.

The `[...T]` spread syntax "glues" those slots into a larger tuple. `[A, ...T, B]` means "start with one known type, stretch T in the middle, end with another known type" — and the compiler tracks each position individually rather than collapsing everything to `any[]` or a union.

TypeScript achieves what Python calls `ParamSpec` through this mechanism: `Parameters<F>` extracts a function's parameter tuple as a variadic type, and `ReturnType<F>` extracts its return type. Wrapping a function in a generic that constrains `F extends (...args: any[]) => any` and forwarding `...args: Parameters<F>` gives the same signature-preservation guarantee that Python's `ParamSpec` provides — without a dedicated syntax for it.

## 14. Example A — Decorator preserving wrapped function's signature

TypeScript has no built-in `ParamSpec`, but `Parameters<F>` and `ReturnType<F>` achieve the same result when combined with a generic constrained to `(...args: any[]) => any`:

```typescript
// Preserves the full call signature of the wrapped function.
// The inferred type of `timed(fetchUser)` is identical to `fetchUser`.
function timed<F extends (...args: any[]) => any>(fn: F): F {
  return (function (this: unknown, ...args: Parameters<F>): ReturnType<F> {
    const start = performance.now();
    const result = (fn as (...a: unknown[]) => unknown).apply(this, args);
    console.log(`${fn.name} took ${(performance.now() - start).toFixed(2)}ms`);
    return result as ReturnType<F>;
  }) as unknown as F;
}

function fetchUser(userId: number, options?: { includeDeleted?: boolean }): Record<string, unknown> {
  return { id: userId, deleted: options?.includeDeleted ?? false };
}

const timedFetch = timed(fetchUser);
timedFetch(42, { includeDeleted: true });  // OK — original signature preserved
timedFetch("not-an-id");                   // error: Argument of type 'string' is not
                                           //   assignable to parameter of type 'number'
timedFetch(42, { nonexistent: true });     // error: Object literal may only specify known properties

// --- Prepend a parameter (TypeScript analog of Python's Concatenate) ---
// Python: Callable[Concatenate[int, P], R]
// TypeScript: (retryCount: number, ...args: Parameters<F>) => ReturnType<F>

function withRetry<F extends (...args: any[]) => any>(
  fn: (retryCount: number, ...args: Parameters<F>) => ReturnType<F>,
): (...args: Parameters<F>) => ReturnType<F> {
  return (...args: Parameters<F>): ReturnType<F> => {
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        return fn(attempt, ...args);
      } catch (err) {
        if (attempt === 2) throw err;
      }
    }
    throw new Error("unreachable");
  };
}
```

**Key difference from Python:** TypeScript cannot infer the exact function type `F` when the wrapper is typed as `(...args: Parameters<F>) => ReturnType<F>` — that type is structurally equivalent to but not identical to `F`. Typing the return as `F` and casting with `as unknown as F` is the idiomatic escape hatch. The cast is safe here because the runtime behavior is identical; the checker just cannot prove it without the cast.

## 15. Example B — Strongly-typed higher-order functions

```typescript
// zip: pairs corresponding elements from two same-length tuples
type Zip<A extends unknown[], B extends unknown[]> =
  A extends [infer AH, ...infer AT]
    ? B extends [infer BH, ...infer BT]
      ? [[AH, BH], ...Zip<AT, BT>]
      : []
    : [];

type Zipped = Zip<[string, number], [boolean, Date]>;
// => [[string, boolean], [number, Date]]

// pipe: compose two functions where the output of the first feeds the second
function pipe<A extends unknown[], B, C>(
  f: (...args: A) => B,
  g: (b: B) => C,
): (...args: A) => C {
  return (...args: A): C => g(f(...args));
}

const parseAndDouble = pipe(
  (s: string) => parseInt(s, 10),
  (n: number) => n * 2,
);
parseAndDouble("21"); // => 42
parseAndDouble(21);   // error: Argument of type 'number' is not assignable to parameter of type 'string'

// Spreading into function calls: forwarding variadic args with full type safety
function logAndCall<T extends unknown[], R>(
  label: string,
  fn: (...args: T) => R,
  ...args: T
): R {
  console.log(label, args);
  return fn(...args);
}

logAndCall("add", (a: number, b: number) => a + b, 1, 2);      // OK — 3
logAndCall("add", (a: number, b: number) => a + b, 1, "two");  // error — "two" not number
```

## 16. Common Type-Checker Errors and How to Read Them

### `Type 'T' is not assignable to type 'unknown[]'`

The generic parameter is missing its `extends unknown[]` constraint, so TypeScript refuses to spread it inside a tuple.

```typescript
// Bad
function bad<T>(arr: T): [string, ...T] { ... }
//                                  ^^^ error

// Fix
function good<T extends unknown[]>(arr: T): [string, ...T] { ... }
```

### `A rest element type must be an array type`

Attempting to spread a non-array type inside a tuple or rest position.

```typescript
type Bad = [string, ...number]; // error: rest element type must be an array type
type Good = [string, ...number[]]; // OK — spreads an array
type Better = [string, ...Array<number>]; // same
```

### TypeScript infers `string[]` instead of `[string, number]`

Without the `[...A]` wrapping trick, TypeScript may widen an argument to an array rather than inferring a tuple.

```typescript
function identity<T extends unknown[]>(args: T): T { return args; }

// Infers string[] | number[], not [string, number]
const bad = identity(["hello", 42]);

// Fix: wrap in tuple spread or use `as const`
const good = identity(["hello", 42] as [string, number]);
const alsoGood = identity(["hello", 42] as const); // readonly ["hello", 42]
```

### `Type instantiation is excessively deep and possibly infinite`

Recursive tuple manipulation types hit TypeScript's instantiation depth limit on long or unbounded tuples.

```typescript
type Reverse<T extends unknown[]> =
  T extends [infer H, ...infer R] ? [...Reverse<R>, H] : T;

type R = Reverse<[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]>; // may error at depth

// Fix: keep tuple lengths bounded; for long sequences, use array operations at runtime
```

## 17. Use-Case Cross-References

- [-> UC-07](../usecases/UC07-callable-contracts.md) Type-safe higher-order functions that forward arguments with full per-position typing
- [-> UC-04](../usecases/UC04-generic-constraints.md) Generic constraints that preserve tuple structure through transformations

## Source Anchors

- [TypeScript 4.0 release notes — variadic tuple types](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-0.html#variadic-tuple-types)
- [TypeScript 4.0 release notes — labeled tuple elements](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-0.html#labeled-tuple-elements)
- [TypeScript Handbook — `Parameters<T>` utility type](https://www.typescriptlang.org/docs/handbook/utility-types.html#parameterstype)
- [Microsoft/TypeScript PR #39094 — variadic tuple types implementation](https://github.com/microsoft/TypeScript/pull/39094)
- [TypeScript deep dive — tuple types](https://basarat.gitbook.io/typescript/type-system/type-assertion)
