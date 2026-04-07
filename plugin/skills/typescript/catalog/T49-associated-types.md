# Type Inference Utilities & `infer`

> **Since:** TypeScript 2.8 (`infer`); utility types built in since TypeScript 2.1

## 1. What It Is

TypeScript's `infer` keyword is used inside the `extends` clause of a conditional type to extract a type component and bind it to a fresh type variable. This is the closest TypeScript equivalent to associated types or type projections in languages like Rust or Haskell: given a type `F`, you can refer to "the type that `F` returns" without repeating or manually tracking it. The built-in utility types `ReturnType<F>`, `Parameters<F>`, `InstanceType<C>`, `ConstructorParameters<C>`, and `Awaited<T>` are all implemented with `infer`. The pattern generalises: `type GetElement<T> = T extends Array<infer E> ? E : never` extracts the element type of any array; `type Unbox<T> = T extends { value: infer V } ? V : never` extracts the value from a box. Downstream code can refer to `ReturnType<typeof someFunction>` instead of duplicating the return annotation — when the function signature changes, all derived types update automatically.

## 2. What Constraint It Lets You Express

**~Achievable — refer to derived types (return type, element type, parameter types) without repeating them; changes to the source type propagate automatically to every site that uses the utility type.**

- `ReturnType<typeof fn>` is always the exact return type of `fn`; no manual synchronization needed.
- `Parameters<typeof fn>[0]` is the type of the first argument; safe to use in wrapper function signatures.
- `Awaited<T>` recursively unwraps nested `Promise<Promise<T>>` to `T`, tracking async composition automatically.
- Custom `infer` patterns let library authors expose derived types without leaking implementation details.

## 3. Minimal Snippet

```typescript
// --- ReturnType implementation ---
type ReturnType<F extends (...args: any[]) => any> =
  F extends (...args: any[]) => infer R ? R : never;

function fetchUser(): Promise<{ id: number; name: string }> {
  return Promise.resolve({ id: 1, name: "Alice" });
}

type UserPromise = ReturnType<typeof fetchUser>; // Promise<{ id: number; name: string }>

// --- Parameters ---
type Parameters<F extends (...args: any[]) => any> =
  F extends (...args: infer P) => any ? P : never;

function save(id: number, data: string, timestamp: Date): void {}

type SaveArgs = Parameters<typeof save>; // [number, string, Date]
type FirstArg = SaveArgs[0];            // number

// --- Awaited: recursive promise unwrapping ---
type MyAwaited<T> = T extends Promise<infer U> ? MyAwaited<U> : T;

type A = MyAwaited<Promise<Promise<number>>>; // number
type B = MyAwaited<string>;                  // string (identity — not a promise)

// --- Custom: extract element type from any array ---
type GetElement<T> = T extends Array<infer E> ? E : never;

type Elem = GetElement<string[]>; // string
// type Elem2 = GetElement<number>; // never — not an array

// --- Custom: extract the resolved value from a thunk ---
type Unthunk<T> = T extends () => infer R ? R : T;

type C = Unthunk<() => number>; // number
type D = Unthunk<string>;       // string

// --- Using ReturnType to keep wrapper in sync ---
function computeScore(input: string): { score: number; label: string } {
  return { score: input.length, label: input[0] ?? "" };
}

// No need to repeat { score: number; label: string } here
function cachedScore(input: string): ReturnType<typeof computeScore> {
  return computeScore(input); // OK
}
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Conditional Types** [-> T41](T41-match-types.md) | `infer` only exists inside conditional types; every use of `infer` is embedded in a `T extends Pattern<infer R> ? Use<R> : Fallback` conditional. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | `ReturnType<F>` and `Parameters<F>` are the primary tools for introspecting function types; they allow wrapper and decorator types to stay in sync with the wrapped function's signature. |
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | The outer generic parameter (`F`, `T`) must be a type variable for `infer` to bind meaningfully; bounds like `F extends (...args: any[]) => any` constrain the pattern and enable the extraction. |

## 5. Gotchas and Limitations

1. **`infer` only fires when `T` is assignable to the pattern** — if `T` does not match `Array<infer E>`, the conditional type resolves to the false branch (`never` in most utility patterns), not an error; silent mismatches can be hard to debug.
2. **Multiple `infer` positions are independent** — in `T extends Map<infer K, infer V>`, TypeScript infers `K` and `V` separately; if the same variable name appears twice, TypeScript infers an intersection for contravariant positions.
3. **Deferred evaluation** — when `T` is an unresolved type parameter, conditional types (and therefore `infer`) are deferred; the result is opaque and cannot be further narrowed in the same scope.
4. **`ReturnType<typeof overloadedFn>`** — for overloaded functions, TypeScript resolves to the last overload signature; this is often the most permissive and may not match what you expect.
5. **`InstanceType` requires a constructor type** — passing a plain object type (not a class constructor) to `InstanceType<C>` results in `never`; the bound `new (...args: any[]) => any` is required.
6. **Recursive `infer` depth** — deeply recursive unwrapping (like a full `DeepAwaited`) can hit TypeScript's instantiation depth limit; use explicit max-depth bounds or rely on the built-in `Awaited<T>` which handles common cases.

## 6. Use-Case Cross-References

- [-> UC-07](../usecases/UC07-callable-contracts.md) Derive parameter and return types of wrapped functions to keep adapters in sync
- [-> UC-19](../usecases/UC19-serialization.md) Extract payload types from codec/schema functions without duplicating type annotations
