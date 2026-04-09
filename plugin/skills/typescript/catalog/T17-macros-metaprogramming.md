
# Decorators & Metaprogramming

> **Since:** TypeScript 5.0 (stage-3 decorators, stable); experimental decorator syntax available since TypeScript 1.5 with `--experimentalDecorators`

## 1. What It Is

TypeScript's metaprogramming surface has two distinct layers. At runtime, **stage-3 decorators** (standardized in TypeScript 5.0) annotate classes, methods, accessors, and fields with functions that execute at class definition time — they can wrap methods, replace property initializers, or register metadata. The legacy experimental decorator API (`--experimentalDecorators`) still exists for compatibility with Angular and NestJS but differs from the standard. At the type level, TypeScript has no macro system; instead, **conditional types**, **mapped types**, and **template literal types** serve as a compile-time type transformation layer — the closest TypeScript equivalent to type-level code generation.

TypeScript has no syntax-level macro system equivalent to Lean's `macro_rules`, Rust's `macro_rules!`, or Scala 3's quotes and splices. There is no way to introduce new syntax at the parser level. External tooling (ts-morph, ts-patch, babel transforms) can perform code generation and AST transformation outside the compiler, but this happens before or after `tsc`, not as a first-class language feature.

## 2. What Constraint It Lets You Express

**Decorators transform class definitions at definition time; conditional and mapped types transform type expressions at compile time — together they cover most metaprogramming needs without an explicit macro system.**

- A method decorator can wrap an implementation (e.g., logging, memoization, access control) without touching the call sites.
- A class decorator can register the class in a DI container, add metadata, or replace the constructor.
- Conditional types (`T extends U ? A : B`) compute new types from input types, enabling type-level pattern matching.
- Mapped types transform the shape of an object type key-by-key, enabling generic utilities like `Partial<T>`, `Required<T>`, and `Readonly<T>`.
- **Distributive conditional types** apply the condition to each member of a union, distributing across it: `string | number extends unknown ? T[] : never` produces `string[] | number[]`.
- **Recursive conditional types** can traverse nested structures (arrays of arrays, deeply optional objects) at the type level.

## 3. Minimal Snippet

```typescript
// --- Stage-3 method decorator (TypeScript 5.0+) ---
function log(target: unknown, context: ClassMethodDecoratorContext) {
  const name = String(context.name);
  return function (this: unknown, ...args: unknown[]) {
    console.log(`Calling ${name} with`, args);
    return (target as Function).apply(this, args);
  };
}

class Calculator {
  @log
  add(a: number, b: number): number {
    return a + b;
  }
}

// --- Stage-3 class decorator ---
function sealed(target: unknown, context: ClassDecoratorContext) {
  context.addInitializer(function (this: unknown) {
    Object.seal(this);
  });
}

@sealed
class Config {
  host = "localhost";
  port = 3000;
}

// --- Type-level metaprogramming: conditional type with infer ---
// Unwrap a Promise type to its inner value type
type Awaited<T> = T extends Promise<infer U> ? U : T;

type A = Awaited<Promise<string>>;  // OK — string
type B = Awaited<number>;           // OK — number

// --- Type-level metaprogramming: mapped type with key remapping ---
// Make every property in T a getter (function returning T[K])
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

interface User { name: string; age: number }
type UserGetters = Getters<User>;
// OK — { getName: () => string; getAge: () => number }
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|-|
| **Conditional Types** [-> T41](T41-match-types.md) | Conditional types are the primary type-level metaprogramming tool; they allow computing new types based on structural relationships, mirroring what macros do at the value level in other languages. |
| **Mapped Types** [-> T62](T62-mapped-types.md) | Mapped types iterate over the keys of a type and transform each one, enabling bulk type transformations equivalent to code generation. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | Method decorators wrap callable types; the decorator must preserve the signature of the original method to avoid breaking callers. |
| **Template Literal Types** [-> T63](T63-template-literal-types.md) | Template literal types compose with mapped types to rename keys (e.g., `get${Capitalize<K>}`) — a common metaprogramming pattern for generating getter/setter shapes. |
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | Decorator factories and type-level utilities are generic functions; bounding type parameters constrains what the transformer accepts or produces. |

## 5. Beginner Mental Model

Think of a **decorator** as a wrapper function applied at class-definition time. `@log` on a method is roughly `method = log(method, context)` — the decorator receives the original function and returns (or modifies) a replacement. The class author writes the behavior once; every call site benefits automatically. **Decorator factories** are decorators that take configuration arguments: `@retry(3)` is a function call that returns a decorator.

**Type-level metaprogramming** is different: it operates entirely at compile time with no runtime effect. Think of conditional types as `if`/`else` for types, and mapped types as `map()` for the keys of an object type. Combined with `infer`, you can extract parts of a type the way pattern matching extracts parts of a value. The compiler evaluates these at type-check time; the emitted JavaScript contains no trace of them.

The key difference from languages with true macro systems (Lean, Rust, Scala): TypeScript cannot generate *new syntax* or *new definitions* at compile time from user code. What decorators and type utilities cover in practice is the vast majority of real-world metaprogramming needs — the gap shows up mainly in DSL authoring and staged code optimization.

## 6. Decorator Deep-Dive

### Decorator kinds and their context types

TypeScript 5.0 stage-3 decorators provide a typed context object whose shape varies by target:

```typescript
// Class decorator — can add initializers, access metadata
function register(target: unknown, ctx: ClassDecoratorContext) {
  ctx.addInitializer(function (this: unknown) {
    console.log(`${String(ctx.name)} constructed`);
  });
}

// Method decorator — wrap or replace the method
function memoize<T, A extends unknown[], R>(
  method: (this: T, ...args: A) => R,
  ctx: ClassMethodDecoratorContext<T, (this: T, ...args: A) => R>,
): (this: T, ...args: A) => R {
  const cache = new Map<string, R>();
  return function (this: T, ...args: A): R {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key)!;
    const result = method.apply(this, args);
    cache.set(key, result);
    return result;
  };
}

// Accessor decorator — intercept get/set of auto-accessors
function clamp(min: number, max: number) {
  return function (
    _: ClassAccessorDecoratorTarget<unknown, number>,
    ctx: ClassAccessorDecoratorContext,
  ): ClassAccessorDecoratorResult<unknown, number> {
    return {
      get() { return _.get.call(this); },
      set(v: number) { _.set.call(this, Math.min(max, Math.max(min, v))); },
    };
  };
}

class Sensor {
  @clamp(0, 100)
  accessor value = 50;  // auto-accessor requires `accessor` keyword
}

// Field decorator — called once with undefined, returns initializer replacement
function withDefault<T>(defaultValue: T) {
  return function (_: undefined, ctx: ClassFieldDecoratorContext): () => T {
    return () => defaultValue;
  };
}

class Options {
  @withDefault(8080)
  port!: number;
}
```

### Decorator factories (parameterized decorators)

A decorator factory is a function that accepts configuration and returns a decorator. The inner function must have the decorator signature:

```typescript
function retry(attempts: number) {
  return function <T, A extends unknown[], R>(
    method: (this: T, ...args: A) => Promise<R>,
    _ctx: ClassMethodDecoratorContext,
  ): (this: T, ...args: A) => Promise<R> {
    return async function (this: T, ...args: A): Promise<R> {
      let lastError: unknown;
      for (let i = 0; i < attempts; i++) {
        try { return await method.apply(this, args); }
        catch (e) { lastError = e; }
      }
      throw lastError;
    };
  };
}

class ApiClient {
  @retry(3)
  async fetchUser(id: string): Promise<{ id: string; name: string }> {
    const res = await fetch(`/users/${id}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }
}
```

## 7. Type-Level Metaprogramming Patterns

### Extracting types with `infer`

```typescript
// Extract return type of any function
type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

// Extract the element type of an array or Promise
type Unpack<T> =
  T extends (infer U)[]   ? U :
  T extends Promise<infer U> ? U :
  T;

type E1 = Unpack<string[]>;         // string
type E2 = Unpack<Promise<number>>;  // number
type E3 = Unpack<boolean>;          // boolean
```

### Distributive conditional types

When the checked type is a naked type parameter, the condition distributes over unions:

```typescript
type IsString<T> = T extends string ? true : false;

type A = IsString<string | number>;  // true | false  (distributes!)
type B = IsString<[string | number]>;  // false  (not naked — no distribution)

// Use [T] extends [U] to prevent distribution:
type IsExactlyString<T> = [T] extends [string] ? true : false;
type C = IsExactlyString<string | number>;  // false
```

### Recursive conditional types

```typescript
// Deep-readonly: make every nested property readonly
type DeepReadonly<T> =
  T extends (infer U)[]
    ? ReadonlyArray<DeepReadonly<U>>
    : T extends object
      ? { readonly [K in keyof T]: DeepReadonly<T[K]> }
      : T;

type Config = { db: { host: string; port: number }; flags: boolean[] };
type FrozenConfig = DeepReadonly<Config>;
// { readonly db: { readonly host: string; readonly port: number }; readonly flags: readonly boolean[] }
```

### Mapped types with key remapping and filtering

```typescript
// Remove all optional properties
type RequiredKeys<T> = {
  [K in keyof T]-?: undefined extends T[K] ? never : K;
}[keyof T];

// Build a type with only the required keys
type OnlyRequired<T> = Pick<T, RequiredKeys<T>>;

interface FormValues {
  name: string;
  email: string;
  phone?: string;
}
type RequiredFormValues = OnlyRequired<FormValues>;
// { name: string; email: string }
```

## 8. Gotchas and Limitations

1. **Stage-3 vs experimental decorators are incompatible** — `--experimentalDecorators` and the new stage-3 decorators have different APIs and cannot be used together in the same project; Angular/NestJS still require the experimental API as of early 2025.
2. **No `reflect-metadata` in stage-3** — the new decorator standard does not automatically emit type metadata; runtime reflection for DI frameworks still requires `reflect-metadata` and the experimental decorator mode. The TC39 decorator metadata proposal (`context.metadata`) is a partial replacement but not yet widely supported.
3. **Decorators are not type-level** — decorators cannot change the TypeScript-visible type of a decorated class or method; you cannot use a decorator to add properties to a class's inferred type (you can work around this with explicit interface merging or module augmentation).
4. **Conditional type complexity** — deeply nested conditional types become unreadable and can hit TypeScript's instantiation depth limits; prefer named intermediate type aliases to keep them tractable.
5. **Distributive conditional types are surprising** — a bare type parameter in `T extends U ? A : B` distributes over unions automatically. Wrap in a tuple `[T] extends [U]` to opt out. Forgetting this is a common source of unexpected `never` or union-expanded results.
6. **No hygienic macros** — TypeScript has no syntax-level macro system; there is no way to introduce new syntax or generate code that appears as if hand-written. Tools like `ts-morph` or compiler plugins (e.g., via `ts-patch`) exist but are fragile and unsupported by the core compiler.
7. **`addInitializer` ordering** — multiple decorators on the same target execute bottom-up (the decorator closest to the declaration runs first); `addInitializer` callbacks run in declaration order, which can produce surprising sequencing bugs.
8. **`accessor` keyword required for accessor decorators** — `ClassAccessorDecoratorContext` only applies to fields declared with the `accessor` keyword (which synthesizes a private backing field with a getter/setter pair). Plain field decorators (`ClassFieldDecoratorContext`) have a different, more limited API.

## 9. Example A — Typed decorator factory preserving method signature

Unlike Python's `ParamSpec` equivalent, TypeScript uses generic type parameters on the decorator function directly to preserve and enforce the wrapped method's signature:

```typescript
// A decorator that enforces the method is only called when authenticated.
// The generic parameters preserve the exact this-type and argument types.
function requireAuth<T extends { isAuthenticated(): boolean }, A extends unknown[], R>(
  method: (this: T, ...args: A) => R,
  _ctx: ClassMethodDecoratorContext<T>,
): (this: T, ...args: A) => R {
  return function (this: T, ...args: A): R {
    if (!this.isAuthenticated()) throw new Error("Unauthorized");
    return method.apply(this, args);
  };
}

class UserService {
  private loggedIn = false;

  isAuthenticated() { return this.loggedIn; }

  @requireAuth
  deleteUser(id: number): void {
    console.log(`Deleting user ${id}`);
  }
}

const svc = new UserService();
svc.deleteUser(1);          // throws — not authenticated
svc.deleteUser("x");        // type error: expected number
```

## 10. Example B — Compile-time type derivation via mapped + conditional types

This pattern generates a full "patch" type from an existing model — analogous to what `derive` macros produce in Rust or Scala, but expressed entirely through the type system:

```typescript
// Given any model type, produce a partial-update (patch) type where:
//   - scalar fields become T | undefined
//   - nested object fields become Patch<T> recursively
//   - array fields become replacement arrays (full replace, not append)
type Patch<T> = {
  [K in keyof T]?: T[K] extends object
    ? T[K] extends (infer _U)[]
      ? T[K]           // arrays: full replacement
      : Patch<T[K]>    // nested objects: recursive patch
    : T[K];            // scalars: optional override
};

interface Address { street: string; city: string; zip: string }
interface Profile { name: string; age: number; address: Address; tags: string[] }

type ProfilePatch = Patch<Profile>;
// {
//   name?: string;
//   age?: number;
//   address?: Patch<Address>;  — { street?: string; city?: string; zip?: string }
//   tags?: string[];
// }

function applyPatch<T extends object>(base: T, patch: Patch<T>): T {
  return { ...base, ...patch } as T;  // simplified; real impl recurses
}

const profile: Profile = { name: "Alice", age: 30, address: { street: "1 Main", city: "Springfield", zip: "12345" }, tags: ["admin"] };
const updated = applyPatch(profile, { age: 31, address: { city: "Shelbyville" } });
// OK — type-safe partial update
```

## 11. Use-Case Cross-References

- [-> UC-19](../usecases/UC19-serialization.md) Use class decorators and metadata to drive JSON serialization/deserialization without hand-written schemas
- [-> UC-09](../usecases/UC09-builder-config.md) Method decorators enforce config validation or transformation in builder-pattern classes

## 12. When to Use It

Use decorators and type-level metaprogramming when:

### Cross-cutting behavior needs to be centralized

Multiple methods share the same wrapper behavior (logging, retry, metrics, auth).

```typescript
function metrics<T, A extends unknown[], R>(
  method: (this: T, ...args: A) => R,
  ctx: ClassMethodDecoratorContext
): (this: T, ...args: A) => R {
  return function (this: T, ...args: A): R {
    const start = Date.now();
    try { return method.apply(this, args); }
    finally { console.log(`${String(ctx.name)}: ${Date.now() - start}ms`); }
  };
}

class Service {
  @metrics
  process(a: number): number { return a * 2; }
  
  @metrics
  validate(x: string): boolean { return x.length > 0; }
}
```

### Generating boilerplate types from primitives

You have a base type and need derived variations (partial, readonly, pick-by-suffix, etc.).

```typescript
type CamelToSnake<T extends string> = T extends `${infer U}${infer Lower}${infer Rest}`
  ? `${U extends Lowercase<U> ? "" : `${U}_`}${Lower}${CamelToSnake<Rest>}`
  : T;

type CreateUserRequest = CamelToSnake<"CreateUserRequest">;  
// "create_user_request"
```

### Runtime behavior depends on parameterized configuration

Decorator factories allow passing config at decoration time.

```typescript
function validateRange(min: number, max: number) {
  return function <T, A extends unknown[], R>(
    method: (this: T, ...args: A) => R,
    _ctx: ClassMethodDecoratorContext
  ): (this: T, ...args: A) => R {
    return function (this: T, ...args: A): R {
      const val = args[0] as number;
      if (val < min || val > max) throw new RangeError("Out of range");
      return method.apply(this, args);
    };
  };
}

class Temperature {
  @validateRange(-273.15, 5000)
  setKelvin(k: number) { this.k = k; }
}
```

### Type constraints are too complex for inline types

The type logic involves pattern-matching, recursion, or conditional branching.

```typescript
type ApiResponse<T> =
  | { status: 200; data: T }
  | { status: 401; error: "Unauthorized" }
  | { status: 404; error: "NotFound" };

type SuccessData<R> = R extends { status: 200 } ? R["data"] : never;
type Data = SuccessData<ApiResponse<User>>;  // User
```

## 13. When NOT to Use It

Avoid decorators and complex type-level metaprogramming when:

### Logic is simple enough to be inline

The wrapper behavior is specific to one method.

```typescript
// ❌ Over-engineering
function singleMethodLogger(method: Function, ctx: ClassMethodDecoratorContext) {
  return function (this: unknown, ...args: unknown[]) {
    console.log(`Calling ${String(ctx.name)}`);
    return method.apply(this, args);
  };
}

class Foo {
  @singleMethodLogger
  bar() { return 42; }
}

// ✅ Simpler
class Foo {
  bar() {
    console.log("Calling bar");
    return 42;
  }
}
```

### Type-level computation exceeds compiler limits

Deeply recursive types hit `_INST_0444` errors.

```typescript
// ❌ May hit depth limits on deep structures
type DeepNth<T, N extends number, Acc extends unknown[] = []> =
  Acc["length"] extends N ? Acc : DeepNth<T, N, [...Acc, T]>;

// ✅ Use a simpler approach or runtime code
const arr: string[] = ["a", "b", "c"];
type Third = typeof arr[2];  // string
```

### You need to modify the TypeScript-inferred type of a class

Decorators cannot add properties to the type checker's view.

```typescript
// ❌ Won't work as expected
function addId(target: unknown, ctx: ClassDecoratorContext) {
  Object.defineProperty(target, "id", { value: Math.random() });
}

@addId
class Entity {}

const e = new Entity();
e.id;  // ❌ Property 'id' does not exist on type 'Entity'
```

### You need to generate new syntax or declarations

TypeScript has no macro system for AST-level code generation.

```typescript
// ❌ Impossible: cannot generate new types/functions at compile time
// There is no way to write `macro! { type Foo = Bar; }`

// ✅ Use codegen tools instead
// • TypeScript utilities: ts-morph, ts-patch
// • External codegen: build scripts, AST transformers
```

### The metaprogramming creates a "magic" codebase

Junior developers cannot understand how types or behavior are derived.

```typescript
// ❌ Too indirection-heavy
type A<T> = B<C<T>, D>;
type B<X, Y> = X extends infer U ? E<U, Y> : never;
type C<T> = T extends object ? F<T> : G;
type D = { [K in keyof H]: I<J, K> };
// ... 15 more lines of indirection ...

// ✅ Use clearer names or simplify
type CreateUserInput = Pick<CreateUserRequest, "name" | "email">;
```

## 14. Antipatterns When Using This Technique

### Overusing distributive conditional types

Forgetting that `T extends U ?:` distributes, creating unexpected result types.

```typescript
// ❌ Wrong: distributes union
type AddPrefix<T> = `item/${T}`;
type Items = AddPrefix<"a" | "b">;  // "item/a" | "item/b"

// ✅ Prevent distribution when treating as single union
type AddPrefix<T> = `item/${T & {}}`;  // or
type NoDistribute<T> = [T] extends [unknown] ? AddPrefix<T> : never;
```

### Deep nesting without intermediate types

Complex conditional chains become unreadable.

```typescript
// ❌ Unmaintainable depth
type F<T> = T extends (infer A)[]
  ? A extends (infer B)[]
    ? B extends (infer C)[]
      ? C extends (infer D)[]
        ? D[]
        : never
      : never
    : never
  : never;

// ✅ Extract with named types
type UnwrapLevel1<T> = T extends (infer U)[] ? U : never;
type UnwrapLevel2<T> = UnwrapLevel1<UnwrapLevel1<T>>;
type UnwrapLevel4<T> = UnwrapLevel2<UnwrapLevel2<T>>;
```

### Using decorators for state management

Decorators are for behavior transformation, not state mutation.

```typescript
// ❌ Decorator holds external state
let callCount = 0;
function counter(method: Function, _ctx: ClassMethodDecoratorContext) {
  return function (...args: unknown[]) {
    callCount++;
    return method(...args);
  };
}

// ✅ State is class-local
class Service {
  private callCount = 0;
  
  withCounter<T, A extends unknown[], R>(
    method: (this: T, ...args: A) => R
  ): (this: T, ...args: A) => R {
    return function (this: T, ...args: A) {
      this.callCount++;
      return method.apply(this, args);
    };
  }
}
```

### Mixing stage-3 and experimental decorators

APIs are incompatible; TypeScript will error or behavior will be surprising.

```typescript
// ❌ Incompatible mix
// tsconfig.json: { "compilerOptions": { "experimentalDecorators": true } }

function stage3Decorator(target: any, ctx: ClassDecoratorContext) {}
function experimentalDecorator(target: typeof Foo) {}

@experimentalDecorator  // experimental API
@stage3Decorator        // stage-3 API
class Foo {}  // ❌ runtime error or wrong behavior
```

### Type-only transforms with runtime expectations

Type-level transformations don't generate runtime code.

```typescript
// ❌ Type trick has no runtime effect
type RequiredProperties<T> = {
  [K in keyof T]-?: T[K];
};
type R = RequiredProperties<{ a?: number; b: string }>;
// R = { a: number; b: string }

const obj: R = { b: "test" };  // Compiles! `a` is still optional at runtime
```

## 15. Antipatterns With Other Techniques (Fixed Using This Technique)

### Repetitive property transformation with manual mapping

Manually creating similar types for each object.

```typescript
// ❌ Manual repetition
type User { name: string; email: string; age: number; }
type PartialUser { name: string | undefined; email: string | undefined; age: number | undefined; }
type Product { id: string; price: number; stock: number; }
type PartialProduct { id: string | undefined; price: number | undefined; stock: number | undefined; }

// ✅ Use mapped type
type MyPartial<T> = {
  [K in keyof T]?: T[K];
};

type PartialUser = MyPartial<User>;
type PartialProduct = MyPartial<Product>;
```

### Repetitive parameter validation across methods

Duplicating validation logic in multiple method bodies.

```typescript
// ❌ Inline repetition
class Service {
  create(name: string, email: string) {
    if (!name || !email) throw new Error("Validation failed");
    // ...
  }
  update(id: number, name: string, email: string) {
    if (!name || !email) throw new Error("Validation failed");
    // ...
  }
  delete(id: number) {
    if (typeof id !== "number") throw new Error("Validation failed");
    // ...
  }
}

// ✅ Decorator factory
function validateRequired(keys: string[]) {
  return function <T, A extends unknown[], R>(
    method: (this: T, ...args: A) => R,
    ctx: ClassMethodDecoratorContext
  ): (this: T, ...args: A) => R {
    return function (this: T, ...args: A): R {
      const argsObj = Object.fromEntries(keys.map((k, i) => [k, args[i]]));
      if (keys.some(k => !argsObj[k])) throw new Error("Validation failed");
      return method.apply(this, args);
    };
  };
}

class Service {
  @validateRequired(["name", "email"])
  create(name: string, email: string) {}
  
  @validateRequired(["name", "email"])
  update(id: number, name: string, email: string) {}
}
```

### Manual deep cloning instead of type-level deep types

Repeating deep readonly or deep partial patterns manually.

```typescript
// ❌ Manual deep readonly
type Config = {
  database: {
    host: string;
    port: number;
  };
  cache: {
    enabled: boolean;
    ttl: number;
  };
};

type ReadonlyConfig = {
  readonly database: {
    readonly host: string;
    readonly port: number;
  };
  readonly cache: {
    readonly enabled: boolean;
    readonly ttl: number;
  };
};

// ✅ Recursive type
type DeepReadonly<T> = T extends object
  ? { readonly [K in keyof T]: DeepReadonly<T[K]> }
  : T;

type ReadonlyConfig = DeepReadonly<Config>;
```

### Verbose type extraction without `infer`

Using conditional types without extracting type parameters.

```typescript
// ❌ Manual type picking
type Event = { type: "user:created"; payload: User };
type ErrorEvent = { type: "error"; payload: ErrorData };

type ExtractUserPayload<T extends Event | ErrorEvent> = T extends { type: "user:created" } ? { payload: User } : never;
type ExtractErrorPayload<T extends Event | ErrorEvent> = T extends { type: "error" } ? { payload: ErrorData } : never;

// ✅ Use infer
type EventPayload<T> = T extends { payload: infer P } ? P : never;
type UserPayload = EventPayload<Event>;       // User
type ErrorPayload = EventPayload<ErrorEvent>; // ErrorData
```

## Recommended Libraries

| Library | Description |
|---|---|
| [ts-morph](https://ts-morph.com/) | TypeScript Compiler API wrapper for reading, transforming, and writing TypeScript source files — the primary tool for code generation outside the compiler |
| [ts-patch](https://github.com/nonara/ts-patch) | Patches the TypeScript compiler to support custom transformers, enabling compiler-plugin-style code generation hooks |
| [reflect-metadata](https://www.npmjs.com/package/reflect-metadata) | Polyfill for the Metadata Reflection API used by DI frameworks (NestJS, inversify) with `--experimentalDecorators` |
| [typia](https://typia.io/) | Compile-time type validator/serializer that uses a custom TypeScript transformer to generate runtime validation code from types |

## Source Anchors

- [TypeScript 5.0 release notes — Decorators](https://devblogs.microsoft.com/typescript/announcing-typescript-5-0/#decorators)
- [TC39 Decorator Proposal](https://github.com/tc39/proposal-decorators)
- [TypeScript Handbook — Decorators](https://www.typescriptlang.org/docs/handbook/decorators.html) (covers experimental; stage-3 docs in release notes)
- [TypeScript Handbook — Conditional Types](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html)
- [TypeScript Handbook — Mapped Types](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)
- [TypeScript Handbook — Template Literal Types](https://www.typescriptlang.org/docs/handbook/2/template-literal-types.html)
