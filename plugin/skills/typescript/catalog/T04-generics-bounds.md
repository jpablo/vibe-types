# Generics & Bounded Polymorphism

> **Since:** TypeScript 1.0

## 1. What It Is

TypeScript generics let you write functions, classes, and types that are parameterized over one or more types, with optional **bounds** (`extends`) that constrain what types may be substituted. A bound `<T extends Constraint>` causes the compiler to reject any call site where `T` does not satisfy `Constraint`. Multiple bounds are expressed as intersections: `<T extends A & B>`. The `keyof` operator produces the union of an object type's known keys, and `T[K]` is the **lookup type** (index access) that gives the type of property `K` on `T`. TypeScript 2.3 added **default type parameters** (`<T = string>`). TypeScript 2.8 introduced **conditional types** (`T extends U ? X : Y`) and `infer`, enabling generic types that inspect and extract parts of their type arguments at compile time.

## 2. What Constraint It Lets You Express

**Generic code compiles only when the type argument satisfies the declared bound; accessing properties or calling methods on a type parameter is only permitted when the bound guarantees their presence.**

- `<T extends { length: number }>` guarantees `T` has a numeric `length` property; `obj.length` inside the function is allowed.
- `<T, K extends keyof T>` guarantees `K` is a valid key of `T`; `obj[key]` returns `T[K]`, not `any`.
- Conditional types enable type-level branching: `type IsArray<T> = T extends any[] ? true : false`.

## 3. Minimal Snippet

```typescript
// Classic keyof bound: safe property access
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key]; // OK — K is guaranteed to be a key of T
}

const user = { name: "Alice", age: 30 };
const name = getProperty(user, "name");  // OK — inferred as string
const age  = getProperty(user, "age");   // OK — inferred as number
// getProperty(user, "email");           // error — "email" is not keyof typeof user

// Multiple bounds via intersection
interface Named  { name: string }
interface Aged   { age: number }

function greet<T extends Named & Aged>(entity: T): string {
  return `${entity.name} is ${entity.age}`; // OK — both properties guaranteed
}

// Default type parameter
type Box<T = string> = { value: T };
const strBox: Box = { value: "hello" }; // OK — T defaults to string
const numBox: Box<number> = { value: 42 }; // OK

// Conditional type with infer
type UnpackPromise<T> = T extends Promise<infer U> ? U : T;
type A = UnpackPromise<Promise<number>>;  // number
type B = UnpackPromise<string>;          // string

// Lookup type chaining
type DeepValue<T, K1 extends keyof T, K2 extends keyof T[K1]> = T[K1][K2];
type Config = { server: { port: number } };
type Port = DeepValue<Config, "server", "port">; // number
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Match Types** [-> T41](T41-match-types.md) | Match types are built on conditional types with `infer`; they are the recursive, pattern-matching extension of the conditional type system that `T extends U ? X : Y` makes possible. |
| **Mapped Types** [-> T62](T62-mapped-types.md) | `{ [K in keyof T]: F<T[K]> }` is the primary use of `keyof` and lookup types together; mapped types iterate over the keys produced by a bound. |
| **Variadic / ParamSpec** [-> T45](T45-paramspec-variadic.md) | Variadic tuple types (`[...T]`) extend generic bounds to rest-parameter and tuple scenarios; `T extends any[]` is the canonical bound for variadic generics. |
| **Associated Types** [-> T49](T49-associated-types.md) | Conditional types with `infer` simulate associated types by extracting components of a complex type: `type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never`. |
| **Interfaces & Structural Contracts** [-> T05](T05-type-classes.md) | Bounds are most commonly interface types; `<T extends Serializable>` requires the structural shape defined by the `Serializable` interface. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | Generic call signatures `<T>(arg: T): T` and generic interfaces with call signatures compose naturally; overloaded generics use multiple call signatures on the same type. |

## 5. Gotchas and Limitations

1. **Bounds are not refined inside the function body** — inside `<T extends string>`, `T` is treated as `string`; you cannot use a string literal type feature like `Template<T>` unless you use conditional types to check.
2. **Default type parameters are not inferred** — if a generic has `<T = string>` and the caller passes an argument that could infer `T`, TypeScript still infers from the argument; the default is used only when inference fails entirely.
3. **Circular type references in conditional types cause depth errors** — deeply recursive conditional types hit TypeScript's instantiation depth limit; use mapped types or interface merging as alternatives.
4. **`keyof any`** — in non-strict mode, `keyof any` is `string | number | symbol`; this can appear in generic bounds and produce unexpected results when mixing index signatures.
5. **Inference from complex bounds may fail** — TypeScript cannot always infer `T` when it appears only in a nested position like `T extends Promise<infer U>`; explicit type arguments may be required.
6. **Type parameter shadowing** — a nested generic function can shadow an outer type parameter with the same name, silently hiding the outer one; use distinct names.

## Coming from JavaScript

JavaScript has no generics at all — functions simply operate on untyped values. TypeScript generics are entirely erased at runtime; they exist purely to give the compiler enough information to verify correctness. This is analogous to Java/C# generics but without runtime reification (no `T.class` equivalent).

## 6. Use-Case Cross-References

- [-> UC-04](../usecases/UC04-generic-constraints.md) Constrain generic type parameters to shapes with required operations
- [-> UC-05](../usecases/UC05-structural-contracts.md) Structural contract enforcement via `extends` bounds
- [-> UC-07](../usecases/UC07-callable-contracts.md) Generic call signatures for type-safe higher-order functions
