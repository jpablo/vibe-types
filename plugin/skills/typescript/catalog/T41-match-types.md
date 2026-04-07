# Conditional Types

> **Since:** TypeScript 2.8

## 1. What It Is

Conditional types are TypeScript's type-level if-expression: `T extends U ? X : Y` evaluates to `X` when `T` is assignable to `U`, and `Y` otherwise. The `infer R` keyword, used inside the `extends` clause, extracts a type component from a pattern and binds it to `R` for use in the true branch. This is the mechanism behind `ReturnType<F>`, `Parameters<F>`, `Awaited<T>`, and many other built-in utility types. When the checked type `T` is a **bare type parameter**, the conditional type is **distributive**: it is applied to each member of a union individually and the results are re-unioned. TypeScript 4.1 extended conditional types to support recursive self-reference with tail-position optimization. TypeScript 5.4 added `NoInfer<T>` to suppress inference from a specific argument position without otherwise changing the type.

## 2. What Constraint It Lets You Express

**Compute a different output type depending on the shape of the input type; the compiler selects the branch at compile time so callsites receive precisely typed results rather than a supertype.**

- Different argument types produce different return types without overloads: `type Unpack<T> = T extends Array<infer E> ? E : T`.
- Distributivity over unions means `Unpack<string[] | number>` resolves to `string | number` automatically.
- `infer` extracts embedded types (return type, element type, promise payload) without repeating them.
- Recursive conditional types process type-level lists and deeply nested structures.

## 3. Minimal Snippet

```typescript
// --- Basic conditional type ---
type IsString<T> = T extends string ? true : false;

type A = IsString<"hello">; // true
type B = IsString<42>;      // false

// --- infer: extract the element type of an array ---
type Flatten<T> = T extends Array<infer E> ? E : T;

type C = Flatten<string[]>; // string
type D = Flatten<number>;   // number   (not an array — identity)

// --- Distributivity over unions ---
type E = Flatten<string[] | boolean>; // string | boolean
//   Flatten<string[]>  → string
//   Flatten<boolean>   → boolean
//   union             → string | boolean

// --- ReturnType implementation ---
type ReturnType<F> = F extends (...args: any[]) => infer R ? R : never;

function greet(name: string): string { return `Hello ${name}`; }
type Greeting = ReturnType<typeof greet>; // string

// --- Awaited: recursive unwrapping ---
type Awaited<T> =
  T extends null | undefined ? T
  : T extends object & { then(onfulfilled: infer F, ...args: any[]): any }
    ? F extends (value: infer V, ...args: any[]) => any
      ? Awaited<V>
      : never
    : T;

type F = Awaited<Promise<Promise<number>>>; // number

// --- Non-distributive (wrapped in a tuple) ---
type UnionToIntersection<U> =
  (U extends any ? (x: U) => void : never) extends (x: infer I) => void
    ? I
    : never;

type G = UnionToIntersection<{ a: number } | { b: string }>; // { a: number } & { b: string }

// --- NoInfer (TypeScript 5.4): pin inference site ---
function clamp<T>(value: T, min: NoInfer<T>, max: NoInfer<T>): T {
  return value; // min/max do not widen the inferred T
}
const result = clamp(3, 1, 10); // T inferred as number from first arg only  // OK
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Union & Intersection Types** [-> T02](T02-union-intersection.md) | Distributive conditional types automatically split unions, apply the condition to each member, and re-union the results; wrapping `T` in `[T]` suppresses distribution when you need non-distributive behavior. |
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | `infer` binds a fresh type variable in the same way a generic parameter does; conditional types are nearly always inside a generic alias or function to make `T` a type variable and trigger distributivity. |
| **Type Inference Utilities & `infer`** [-> T49](T49-associated-types.md) | Built-in utilities like `ReturnType`, `Parameters`, and `Awaited` are conditional types using `infer`; custom utilities follow exactly the same pattern. |
| **Mapped Types** [-> T62](T62-mapped-types.md) | Conditional types are commonly used as the value expression inside a mapped type: `{ [K in keyof T]: T[K] extends string ? "str" : "other" }`, giving per-property type-level decisions. |
| **Type Aliases** [-> T23](T23-type-aliases.md) | Conditional types are always written as `type` aliases; they cannot appear as standalone expressions; the alias name is the callable entry point for instantiation. |

## 5. Gotchas and Limitations

1. **Distributivity surprises** — `T extends string ? X : Y` distributes when `T` is a bare type parameter, so `never extends string ? X : Y` produces `never` (empty union mapped over). Wrap in a tuple `[T] extends [string]` to prevent this.
2. **`infer` only works in `extends` clauses** — you cannot use `infer` outside a conditional type; attempts produce a parse error.
3. **Recursion depth limits** — TypeScript aborts recursive conditional types that exceed the instantiation depth (roughly 100 levels). Keep recursive types shallow or use mapped-type alternatives.
4. **Deferred evaluation** — when `T` is still an unresolved type variable, TypeScript defers evaluation of the conditional type; the result is opaque and cannot be used for further narrowing inside the same scope.
5. **`infer` variance** — the inferred type `R` is inferred in covariant position by default; in contravariant positions (function parameters), inference produces an intersection, not a union.
6. **`NoInfer` is TypeScript 5.4+** — using `NoInfer<T>` in older projects requires a manual workaround: `type NoInfer<T> = T & {}` (approximate; does not fully suppress inference in all positions).

## 6. Use-Case Cross-References

- [-> UC-04](../usecases/UC04-generic-constraints.md) Derive precise return types for generic higher-order functions
- [-> UC-07](../usecases/UC07-callable-contracts.md) Extract parameter and return types from callable shapes for strongly-typed adapters
- [-> UC-19](../usecases/UC19-serialization.md) Compute serialized/deserialized types from source types without duplication
