# Generics & Bounded Polymorphism

> **Since:** TypeScript 1.0

## 1. What It Is

TypeScript generics let you write functions, classes, and types that are parameterized over one or more types, with optional **bounds** (`extends`) that constrain what types may be substituted. A bound `<T extends Constraint>` causes the compiler to reject any call site where `T` does not satisfy `Constraint`. Multiple bounds are expressed as intersections: `<T extends A & B>`. The `keyof` operator produces the union of an object type's known keys, and `T[K]` is the **lookup type** (index access) that gives the type of property `K` on `T`. TypeScript 2.3 added **default type parameters** (`<T = string>`). TypeScript 2.8 introduced **conditional types** (`T extends U ? X : Y`) and `infer`, enabling generic types that inspect and extract parts of their type arguments at compile time. TypeScript 4.7 added **explicit variance annotations** (`in`/`out`) for type parameters in generic types.

**F-bounded polymorphism** (`<T extends Comparable<T>>`) is a self-referential bound: the type parameter appears in its own constraint. This is the TypeScript idiom for methods that must return the concrete subtype, not just the declared supertype — useful for fluent builder APIs and self-referential comparisons.

**Explicit type arguments** can be supplied at any call site when inference fails or when you need to override what the compiler would infer: `identity<string>("hello")`, `parse<User>(json)`. The syntax attaches to the function or method name, before the argument list.

## 2. What Constraint It Lets You Express

**Generic code compiles only when the type argument satisfies the declared bound; accessing properties or calling methods on a type parameter is only permitted when the bound guarantees their presence.**

- `<T extends { length: number }>` guarantees `T` has a numeric `length` property; `obj.length` inside the function is allowed.
- `<T, K extends keyof T>` guarantees `K` is a valid key of `T`; `obj[key]` returns `T[K]`, not `any`.
- `<T extends Comparable<T>>` (F-bound) guarantees operations like `compareTo` return the concrete type, not just the base constraint.
- Conditional types enable type-level branching: `type IsArray<T> = T extends any[] ? true : false`.
- An explicit type variable shared across parameters (`<T>(a: T, b: T)`) requires both arguments to unify to the same type; a plain union parameter (`a: string | number, b: string | number`) does not.

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
7. **Conditional `extends` vs bound `extends`** — `<T extends string>` in a type parameter list restricts which types may be substituted; `T extends string ? X : Y` inside a conditional type is a type-level predicate evaluated by the compiler. Same keyword, entirely different roles.
8. **Shared type parameter vs union** — `<T>(a: T, b: T)` forces both arguments to resolve to the same type `T`; replacing `T` with a union like `string | number` allows each argument to vary independently. Use an explicit type variable when two parameters must share a concrete type.
9. **F-bounds and inference** — TypeScript can infer `T` in `<T extends Builder<T>>` from a single argument, but deeply nested F-bounds sometimes confuse inference. Supply explicit type arguments when the compiler reports that `T` was not inferred.

## Beginner Mental Model

Think of `<T>` as a **blank on a form** the caller fills in. Bounds are the **fine print**: "must have a `length`", "must be a key of this object". The compiler is a strict clerk — it rejects the form if the value does not meet the requirements, and the function body can only use operations the fine print guarantees.

A **default** (`<T = string>`) is the pre-filled default answer if the caller leaves the blank empty. An **F-bound** (`<T extends Comparable<T>>`) is a fine-print clause that refers back to the blank itself — "the value must be comparable to others of its own kind."

Inference fills in the blank automatically from the argument types. Explicit type arguments (`foo<MyType>(arg)`) let you override that inference when needed.

## Coming from JavaScript

JavaScript has no generics at all — functions simply operate on untyped values. TypeScript generics are entirely erased at runtime; they exist purely to give the compiler enough information to verify correctness. This is analogous to Java/C# generics but without runtime reification (no `T.class` equivalent).

## Examples

### Example A — Generic class preserving element type

```typescript
class Stack<T> {
  private items: T[] = [];

  push(item: T): void    { this.items.push(item); }
  pop():  T | undefined  { return this.items.pop(); }
  peek(): T | undefined  { return this.items[this.items.length - 1]; }
}

const nums = new Stack<number>();
nums.push(1);
nums.push(2);
// nums.push("x"); // error: Argument of type 'string' is not assignable to parameter of type 'number'
const top: number | undefined = nums.peek(); // OK — return type is number | undefined

const strs = new Stack<string>();
strs.push("a");
```

### Example B — F-bounded polymorphism (self-referential bound)

```typescript
interface Rankable<T extends Rankable<T>> {
  rank(): number;
  // Returns the concrete type, not just Rankable<T>
  best(other: T): T;
}

class Score implements Rankable<Score> {
  constructor(readonly value: number) {}
  rank(): number { return this.value; }
  best(other: Score): Score { return this.value >= other.value ? this : other; }
}

function top<T extends Rankable<T>>(items: T[]): T {
  return items.reduce((a, b) => a.best(b));
}

const winner: Score = top([new Score(3), new Score(7), new Score(2)]);
// Return type is Score, not Rankable<Score>
```

### Example C — Explicit type arguments when inference falls short

```typescript
// inference works fine here
function identity<T>(x: T): T { return x; }
const n = identity(42);           // T inferred as 42 (literal)
const n2 = identity<number>(42);  // T forced to number

// inference cannot determine T when the argument provides no evidence
function empty<T>(): T[] { return []; }
// const xs = empty();            // error: cannot infer T
const xs = empty<string>();       // OK — explicit argument required

// narrowing vs widening: inferred literal vs explicit base type
const a = identity("hello");      // T = "hello" (string literal)
const b = identity<string>("hello"); // T = string (widened)
```

### Example D — Shared type parameter vs. plain union

```typescript
// Both arguments must resolve to the same type T
function pickLarger<T extends number | string>(a: T, b: T): T {
  return a > b ? a : b;
}

pickLarger(1, 2);          // OK — T = number
pickLarger("a", "b");      // OK — T = string
// pickLarger(1, "b");     // error — T cannot simultaneously be number and string

// Without the type variable, arguments are independently typed
function pickLargerLoose(a: number | string, b: number | string): number | string {
  return a > b ? a : b;
}
pickLargerLoose(1, "b");   // OK at type level — each param is independently number | string
```

Use an explicit type variable (`<T>`) when two parameters or a parameter and the return value must share the same concrete type. When that coupling is not needed, a plain union is simpler and more flexible.

## Common Type-Checker Errors

### `Type 'X' does not satisfy the constraint 'Y'`

The type argument (or inferred type) does not match the `extends` bound.

```
error TS2344: Type 'RegExp' does not satisfy the constraint '{ length: number }'.
  Property 'length' is missing in type 'RegExp'.
```

**Fix:** Pass a type that satisfies the constraint, or widen/relax the bound if the restriction is too tight.

### `Generic type 'Foo' requires between N and M type arguments`

A generic type was used without supplying required type arguments and inference did not resolve them.

```
error TS2314: Generic type 'Stack<T>' requires 1 type argument(s).
```

**Fix:** Supply the argument explicitly (`Stack<number>`) or add a default (`<T = unknown>`).

### `Type 'T' cannot be used to index type 'U'`

A type variable was used as an index but was not bounded to `keyof U`.

```
error TS2536: Type 'T' cannot be used to index type '{ name: string }'.
```

**Fix:** Add `K extends keyof T` to the signature and use `K` as the index type.

### `Cannot find name 'T'` inside a class body

A method references a class-level type parameter that was accidentally shadowed or not in scope.

**Fix:** Check that the method does not redeclare `<T>` unnecessarily (shadowing the class parameter), or move the type parameter to the class level.

### Implicit `any` on unconstrained parameters

In `strict` mode, TypeScript infers `any` for an unconstrained type variable used in a position where no argument provides evidence.

```
error TS7006: Parameter 'x' implicitly has an 'any' type.
```

**Fix:** Annotate the parameter, add a bound, or supply an explicit type argument at the call site.

## 6. Use-Case Cross-References

- [-> UC-04](../usecases/UC04-generic-constraints.md) Constrain generic type parameters to shapes with required operations
- [-> UC-05](../usecases/UC05-structural-contracts.md) Structural contract enforcement via `extends` bounds
- [-> UC-07](../usecases/UC07-callable-contracts.md) Generic call signatures for type-safe higher-order functions

## When to Use

### Enforcing structural requirements across multiple types

```typescript
function toJson<T extends { id: string }>(obj: T): string {
  return JSON.stringify({ id: obj.id, type: 'entity' });
}
```

### Preserving type relationships between parameters

```typescript
function pair<T>(a: T, b: T): [T, T] { return [a, b]; }
// pair(1, "x") error — must share same type
```

### Safe property access with dynamic keys

```typescript
function get<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}
```

### Extracting types from complex structures

```typescript
type ArrayType<T> = T extends readonly (infer U)[] ? U : never;
type Item = ArrayType<string[]>; // string
```

## When Not to Use

### When unions suffice

```typescript
// BAD: generic overkill for simple case
function log<T extends { toString: () => string }>(val: T): void {
  console.log(val.toString());
}

// GOOD: union is simpler
function log(val: string | number | Date): void {
  console.log(val.toString());
}
```

### When the constraint is too broad

```typescript
// BAD: unconstrained generic adds no safety
function wrapper<T>(value: T): T { return value; }

// GOOD: specific type is clearer
function wrapper(value: string): string { return value; }
```

### When you need runtime type information

```typescript
// BAD: generic erased at runtime
function create<T>(data: T): T { return data; }
create({}).constructor // no type info

// GOOD: use instanceof or type guards
function createObject(data: object): object { return data; }
```

## Antipatterns When Using This Technique

### Overly complex bound intersections

```typescript
// BAD: hard to understand and maintain
interface Requirements<T> {
  new(): T;
  prototype: {
    id: string;
    createdAt: Date;
    toJSON: () => string;
  };
}

function process<T extends Requirements<T>>(x: T): void {}
```

### Circular F-bounds in data structures

```typescript
// BAD: inference fails, causes confusion
type Node<T> = {
  value: T;
  next: Node<T> | null;
  previous: Node<T> | null;
};

function link<T extends Node<T>>(a: T, b: T): void {
  a.next = b;
  b.previous = a;
}
// Types cannot be inferred properly
```

### Conditional types with excessive nesting

```typescript
// BAD: hits compilation limits, hard to debug
type DeepExtract<T> = T extends {
  data: infer U
}
  ? U extends {
    value: infer V
  }
    ? V extends {
      result: infer W
    }
      ? W
      : never
    : never
  : never
  // Type instantiation is excessively deep
```

## Antipatterns with Other Techniques (Where This Helps)

### Union types without type coupling

```typescript
// BAD: parameters can be different types
function sum(a: number | string, b: number | string): number {
  return Number(a) + Number(b);
}
sum(1, "2"); // compiles but runtime may surprise

// GOOD: generics force type coupling
function sum<T>(a: T, b: T): T {
  // both args must be same type
}
```

### `any` in utility functions

```typescript
// BAD: no type safety
function clone(data: any): any {
  return JSON.parse(JSON.stringify(data));
}
const result = clone({ x: 1 });
result.nonexistent; // no error!

// GOOD: generic preserves type
function clone<T>(data: T): T {
  return JSON.parse(JSON.stringify(data));
}
const result = clone({ x: 1 });
result.nonexistent; // error!
```

### Repeated type annotations

```typescript
// BAD: verbose and error-prone
type GetUserName = (user: { name: string; age: number }) => string;
type GetUserAge = (user: { name: string; age: number }) => number;
type GetUserId = (user: { name: string; age: number }) => string;

// GOOD: generic with bounds
function selector<T, K extends keyof T>(
  fn: (obj: T) => T[K]
): (obj: T) => T[K] {
  return fn;
}
```

### Nested callbacks with callback-specific types

```typescript
// BAD: callback types lose connection
function fetch<T>(): Promise<T> {
  return {} as T;
}

fetch().then((data) => {
  // data is implicitly 'any' without explicit annotation
  return data.id;
});

// GOOD: generic preserves connection
function pipe<T, U>(fn: (t: T) => U, value: T): Promise<U> {
  return Promise.resolve(fn(value));
}
```

## Source Anchors

- [TypeScript Handbook: Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html)
- [TypeScript Handbook: Conditional Types](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html)
- [TypeScript Handbook: Keyof Type Operator](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html)
- [TypeScript Handbook: Indexed Access Types](https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html)
- [TypeScript 2.3 release notes: Generic parameter defaults](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-2-3.html)
- [TypeScript 2.8 release notes: Conditional types](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-2-8.html)
- [TypeScript 4.7 release notes: Variance annotations](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-7.html)
