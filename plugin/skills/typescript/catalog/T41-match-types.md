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

## 3. Beginner Mental Model

Think of a conditional type as a **lookup table where the keys are type shapes and the results are types**. When you look up `Array<string>`, you get `string`. When you look up `number`, you get `number` unchanged. The compiler consults this table during type checking to determine the result type at each use site.

Coming from Scala 3: TypeScript's `T extends U ? X : Y` is TypeScript's equivalent of Scala 3's `T match { case U => X; case _ => Y }`. The `infer` keyword corresponds to a binding pattern in Scala's match case, e.g. `case Array[t] => t`.

Coming from Haskell / Lean: TypeScript conditional types are not dependent types — they dispatch on type structure, not runtime values. There is no equivalent to Lean's `match tag with | "number" => 3.14` where the *value* determines the type. The closest analogue is a discriminated union with a function overloaded on the discriminant literal type.

## 4. Minimal Snippet

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

## 5. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Union & Intersection Types** [-> T02](T02-union-intersection.md) | Distributive conditional types automatically split unions, apply the condition to each member, and re-union the results; wrapping `T` in `[T]` suppresses distribution when you need non-distributive behavior. |
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | `infer` binds a fresh type variable in the same way a generic parameter does; conditional types are nearly always inside a generic alias or function to make `T` a type variable and trigger distributivity. |
| **Type Inference Utilities & `infer`** [-> T49](T49-associated-types.md) | Built-in utilities like `ReturnType`, `Parameters`, and `Awaited` are conditional types using `infer`; custom utilities follow exactly the same pattern. |
| **Mapped Types** [-> T62](T62-mapped-types.md) | Conditional types are commonly used as the value expression inside a mapped type: `{ [K in keyof T]: T[K] extends string ? "str" : "other" }`, giving per-property type-level decisions. |
| **Type Aliases** [-> T23](T23-type-aliases.md) | Conditional types are always written as `type` aliases; they cannot appear as standalone expressions; the alias name is the callable entry point for instantiation. |

## 6. Gotchas and Limitations

1. **Distributivity surprises** — `T extends string ? X : Y` distributes when `T` is a bare type parameter, so `never extends string ? X : Y` produces `never` (empty union mapped over). Wrap in a tuple `[T] extends [string]` to prevent this.
2. **`infer` only works in `extends` clauses** — you cannot use `infer` outside a conditional type; attempts produce a parse error.
3. **Recursion depth limits** — TypeScript aborts recursive conditional types that exceed the instantiation depth (roughly 100 levels). Keep recursive types shallow or use mapped-type alternatives.
4. **Deferred / stuck evaluation** — when `T` is an unresolved type variable, TypeScript defers the conditional type and the result is opaque. You cannot branch on it or narrow inside the same scope. This is the analogue of Scala's "stuck" match type: `type Elem<T> = T extends Array<infer E> ? E : T` stays stuck as `Elem<T>` until `T` is concrete.

   ```typescript
   function bad<T>(x: T): T extends string ? number : boolean {
     // Error: TypeScript cannot verify that `42` satisfies `T extends string ? number : boolean`
     // because T is still abstract here.
     return 42 as any;
   }
   // Workaround: use overloads or cast via `any` in the implementation.
   ```

5. **`infer` variance** — the inferred type `R` is inferred in covariant position by default; in contravariant positions (function parameters), inference produces an intersection, not a union.
6. **`NoInfer` is TypeScript 5.4+** — using `NoInfer<T>` in older projects requires a manual workaround: `type NoInfer<T> = T & {}` (approximate; does not fully suppress inference in all positions).
7. **No guards** — unlike Scala 3 match types or value-level `switch`, conditional type cases cannot have guards. All dispatch must be structural, based on assignability alone.
8. **Termination** — recursive conditional types can exceed TypeScript's instantiation depth limit (~100) and produce a "Type instantiation is excessively deep" error. Declare an upper-bound result type or refactor into a mapped type if this occurs.

## 7. Example A — Recursive leaf-element extraction

```typescript
// Drill down through nested arrays to the scalar element type
type LeafElem<T> =
  T extends string      ? string         // string is iterable but not "array-like" here
  : T extends Array<infer E> ? LeafElem<E>
  : T;

type L1 = LeafElem<number[][][]>;        // number
type L2 = LeafElem<string[][]>;          // string[]  — hits the string branch first
type L3 = LeafElem<boolean>;             // boolean

// Recursive unwrap of a Promise chain
type DeepAwaited<T> =
  T extends Promise<infer U> ? DeepAwaited<U> : T;

type P = DeepAwaited<Promise<Promise<Promise<number>>>>; // number
```

## 8. Example B — Dependently-typed function (return type varies by argument)

TypeScript does not have true dependent types, but a function can declare a conditional return type, achieving the same pattern for concrete literal types:

```typescript
type JsonTag = "number" | "string" | "boolean";

// Type-level lookup: tag → runtime type
type JsonType<Tag extends JsonTag> =
  Tag extends "number"  ? number
  : Tag extends "string"  ? string
  : boolean;

// The return type is determined by the literal type of `tag`
function parseJson<Tag extends JsonTag>(tag: Tag, raw: string): JsonType<Tag> {
  switch (tag) {
    case "number":  return Number(raw) as JsonType<Tag>;
    case "string":  return raw as JsonType<Tag>;
    default:        return (raw === "true") as JsonType<Tag>;
  }
}

const n = parseJson("number", "3.14");   // number
const s = parseJson("string", "hello");  // string
const b = parseJson("boolean", "true");  // boolean
```

This mirrors Lean's `JsonType` / `parse` pair and Scala's dependently-typed method pattern: `Tag` narrows to a literal type at the call site, the conditional type reduces, and the caller receives the precise type.

## 9. Example C — `infer` in multiple positions

`infer` can appear multiple times in a single pattern, binding different parts of a complex type simultaneously:

```typescript
// Extract both the key and value types from a Map
type MapKV<T> =
  T extends Map<infer K, infer V> ? { key: K; value: V } : never;

type M = MapKV<Map<string, number>>; // { key: string; value: number }

// Extract argument and return type of a single-parameter function
type Fn1Shape<T> =
  T extends (arg: infer A) => infer R ? { arg: A; ret: R } : never;

type S = Fn1Shape<(x: string) => number>; // { arg: string; ret: number }
```

## 10. Example D — Conditional types inside mapped types

```typescript
// Mark each property "required" (string) or "optional" (string | undefined) based on its type
type Requiredness<T> = {
  [K in keyof T]: undefined extends T[K] ? "optional" : "required";
};

interface Config {
  host: string;
  port?: number;
  debug?: boolean;
}

type ConfigMeta = Requiredness<Config>;
// { host: "required"; port: "optional"; debug: "optional" }
```

## 11. Use-Case Cross-References

- [-> UC-04](../usecases/UC04-generic-constraints.md) Derive precise return types for generic higher-order functions
- [-> UC-07](../usecases/UC07-callable-contracts.md) Extract parameter and return types from callable shapes for strongly-typed adapters
- [-> UC-19](../usecases/UC19-serialization.md) Compute serialized/deserialized types from source types without duplication

## 12. When to Use It

- **Type extraction from complex shapes**: Pull element types from arrays, return types from functions, value types from maps.

  ```typescript
  type Elem<T> = T extends Array<infer E> ? E : never;
  type X = Elem<string[]>; // string
  ```

- **Conditional return types**: Function return type depends on argument type.

  ```typescript
  type MaybeString<T> = T extends string ? T : T | null;
  function f<T>(x: T): MaybeString<T> { return x; }
  ```

- **Distributive transformations**: Apply different rules to each union member automatically.

  ```typescript
  type Wrap<T> = T extends string ? `prefix-${T}` : T;
  type X = Wrap<"a" | "b" | number>; // `prefix-a` | `prefix-b` | number
  ```

- **Recursive type processing**: Unwrap nested structures like `Promise<Promise<T>>`.

  ```typescript
  type DeepUnwrap<T> = T extends Promise<infer U> ? DeepUnwrap<U> : T;
  ```

## 13. When NOT to Use It

- **For simple property access**: Use index types or direct access instead.

  ```typescript
  // Avoid
  type GetProp<T, K> = T extends { [P in K]: infer V } ? V : never;

  // Prefer
  type GetProp<T, K> = T[K];
  ```

- **When the condition is value-based**: Conditional types only work on types, not runtime values.

  ```typescript
  // Does NOT work - `len` is a value, not a type
  type Result<T, len extends number> = len extends 0 ? "empty" : "non-empty";
  ```

- **For branching function implementations**: Use runtime conditionals, not types.

  ```typescript
  // Wrong: type cannot control runtime
  type Branch<T> = T extends string ? "yes" : "no";

  // Right: runtime if-else
  function branch(x: unknown) {
    return typeof x === "string" ? "yes" : "no";
  }
  ```

- **When union distribution is unwanted**: Wrap in tuple to make non-distributive.

  ```typescript
  // Distributive (surprising)
  type Bad<T> = T extends string ? readonly T[] : T;
  type X = Bad<"a" | "b">; // readonly "a"[] | readonly "b"[]

  // Non-distributive
  type Good<T> = [T] extends [string] ? readonly T[] : T;
  type Y = Good<"a" | "b">; // "a" | "b"
  ```

## 14. Antipatterns When Using It

- **Deeply nested conditionals**: Hard to read and maintain.

  ```typescript
  // Bad: hard to follow
  type Messy<T> = T extends string
    ? T extends `http://${infer P}` ? { kind: "url"; path: P }
    : T extends `https://${infer P}` ? { kind: "url"; path: P }
    : { kind: "string" }
  : T extends Array<infer E>
    ? { kind: "array"; elem: E }
  : T extends object
    ? { kind: "object" }
  : { kind: "other" };

  // Better: split into smaller types
  type UrlParse<T> = T extends `http://${infer P}` | `https://${infer P}`
    ? { kind: "url"; path: P }
    : never;

  type Messy<T> = T extends string
    ? UrlParse<T> | { kind: "string" }
  : T extends Array<infer E>
    ? { kind: "array"; elem: E }
  : T extends object
    ? { kind: "object" }
  : { kind: "other" };
  ```

- **Overly generic without constraints**: Type becomes `any` or `never` unexpectedly.

  ```typescript
  // Bad: unconstrained infer can match anything
  type Bad<T> = T extends infer E ? E : never; // Always T

  // Better: constrain the pattern
  type Good<T> = T extends string | number ? T : never;
  ```

- **Using conditional types for runtime checks**: Types are erased at runtime.

  ```typescript
  // Bad: this type doesn't help at runtime
  type IsArray<T> = T extends any[] ? true : false;
  const isArray: IsArray<string[]> = true; // type-only check

  // Better: use Array.isArray()
  const isArray = Array.isArray(x);
  ```

- **Redundant identity branches**: Adds noise without value.

  ```typescript
  // Bad: unnecessary complexity
  type Identity<T> = T extends infer E ? E : T; // Always T

  // Better: just T or type alias
  type Identity<T> = T;
  ```

## 15. Antipatterns with Other Techniques (Fixed by This)

- **Overloads for simple transformations**: Conditional types eliminate overload duplication.

  ```typescript
  // Bad: many overloads for type variation
  function first<T>(arr: readonly [T, ...T[]]): T;
  function first<T>(arr: readonly T[]): T | undefined;
  function first<T>(arr: readonly T[]) { return arr[0]; }

  // Better: single function with conditional return
  function first<T>(arr: readonly T[]): T extends readonly [any, ...any] ? T[0] : T[0] | undefined {
    return arr[0] as any;
  }
  ```

- **Union result with manual enumeration**: Distributive conditionals auto-handle unions.

  ```typescript
  // Bad: manually enumerate all union possibilities
  type ToStatus<T> =
    T extends "pending" ? StatusPending
    : T extends "success" ? StatusSuccess
    : T extends "error" ? StatusError
    : T extends "pending" | "success" | "error" ? StatusPending | StatusSuccess | StatusError
    : never;

  // Better: distributive conditional handles unions automatically
  type Status<T extends string> =
    T extends "pending" ? StatusPending
    : T extends "success" ? StatusSuccess
    : StatusError;
  // Status<"pending" | "success"> → StatusPending | StatusSuccess
  ```

- **Manual type guards for every variant**: Conditional types create precise types.

  ```typescript
  // Bad: repetitive unions and guards
  type Payload = { kind: "user"; id: number } | { kind: "post"; title: string };
  function handle(p: Payload) {
    if (p.kind === "user" && typeof p.id === "number") { /* ... */ }
    if (p.kind === "post" && typeof p.title === "string") { /* ... */ }
  }

  // Better: conditional type + discriminated union
  type Payload<K extends "user" | "post"> =
    K extends "user" ? { kind: "user"; id: number }
    : { kind: "post"; title: string };
  function handle<K extends "user" | "post">(p: Payload<K>) {
    // p is already precisely typed by K
  }
  ```

- **Intersection for conditional properties**: Use conditional types for per-property decisions.

  ```typescript
  // Bad: intersection loses precision
  type PartialWithRequired<T, K extends keyof T> =
    Partial<T> & { [P in K]: T[P] };

  // Better: conditional in mapped type
  type PartialWithRequired<T, K extends keyof T> = {
    [P in keyof T]: P extends K ? T[P] : T[P] | undefined;
  };
  ```
