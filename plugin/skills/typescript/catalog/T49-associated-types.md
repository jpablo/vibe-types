# Associated Types (via Generics and `infer`)

> **Since:** TypeScript 1.0 (generic interfaces); TypeScript 2.1 (utility types); TypeScript 2.8 (`infer`)

## 1. What It Is

TypeScript has no dedicated "associated type" syntax like Rust's `type Item;` inside a trait, but the same patterns arise through two complementary mechanisms:

1. **Generic interfaces / classes where the type parameter is fixed per implementation.** `interface Repository<T>` lets each implementing class pin `T` to a concrete type (`User`, `Product`, etc.), exactly like Rust's associated type — the implementor decides. The caller does not pick `T`; the implementation does. This is the "who owns the type" pattern.

2. **`infer` in conditional types — type projection.** The `infer` keyword, used inside the `extends` clause of a conditional type, extracts a type component and binds it to a fresh type variable. `ReturnType<F>`, `Parameters<F>`, `InstanceType<C>`, and `Awaited<T>` are all implemented this way. This is TypeScript's answer to "given a type, derive its associated output type without repeating it."

The two patterns address different sides of the associated-type idea:

| Concern | Mechanism | Analogous to |
|---------|-----------|-------------|
| **Implementor fixes the output type** | `interface Repo<T>` implemented as `class UserRepo implements Repo<User>` | Rust `impl Iterator for Lines { type Item = String; }` |
| **Caller derives a related type** | `ReturnType<typeof fn>`, custom `infer` patterns | Rust `<T as Trait>::Output` projections, Haskell type families |

## 2. What Constraint It Lets You Express

**Generic interfaces** — each implementing class commits to one concrete type argument, and the compiler enforces consistency across all methods of that implementation:

- `class UserRepo implements Repository<User>` must return `User | undefined` from `get()`, not `Product`.
- Writing a function that accepts `Repository<T>` is generic over `T`; the function body works the same regardless of which entity type the repo handles.

**`infer` projections** — derived types stay automatically in sync with their source:

- `ReturnType<typeof fn>` is always the exact return type of `fn`; no manual synchronization needed.
- `Parameters<typeof fn>[0]` is the type of the first argument; safe to use in wrapper function signatures.
- `Awaited<T>` recursively unwraps nested `Promise<Promise<T>>` to `T`.
- Custom `infer` patterns let library authors expose derived types without leaking implementation details.

## 3. Minimal Snippets

### Generic interface (implementor fixes the type)

```typescript
// The "associated type" is T — each implementation pins it to a concrete type
interface Repository<T> {
  get(id: number): T | undefined;
  save(entity: T): void;
  all(): T[];
}

type User = { id: number; name: string };
type Product = { id: number; title: string };

class UserRepo implements Repository<User> {
  private store = new Map<number, User>();
  get(id: number) { return this.store.get(id); }
  save(entity: User) { this.store.set(entity.id, entity); }
  all() { return [...this.store.values()]; }
}

class ProductRepo implements Repository<Product> {
  private store = new Map<number, Product>();
  get(id: number) { return this.store.get(id); }
  save(entity: Product) { this.store.set(entity.id, entity); }
  all() { return [...this.store.values()]; }
}

// Generic function — T is determined by the repo, not the caller
function countAll<T>(repo: Repository<T>): number {
  return repo.all().length;
}

countAll(new UserRepo());    // OK — T inferred as User
countAll(new ProductRepo()); // OK — T inferred as Product
```

### `infer` (type projection)

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

## 4. Generic Interface vs Generic Parameter — Design Guidance

The key question when designing an interface is: **who picks the type — the caller or the implementor?**

| Criterion | Single generic (associated-type style) | Multiple implementations of same interface |
|-----------|----------------------------------------|-------------------------------------------|
| **Who chooses** | Implementor pins `T` once | Caller may supply different `T` to the same class |
| **Example** | `class UserRepo implements Repo<User>` | `class MultiRepo<T> implements Repo<T>` |
| **Multiple impls on one class** | One natural answer per class | A class can implement `Repo<User>` AND `Repo<Product>` (different type args) |
| **Best for** | Output/entity type tied to the class | Classes generic over the entity, chosen at construction time |

Unlike Rust, TypeScript does not prevent a class from implementing the same generic interface twice with different type arguments (e.g., `implements Repo<User>` and `implements Repo<Product>` simultaneously, via union tricks or overloads). For the cleanest associated-type semantics, pin `T` at the class level.

## 5. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Conditional Types** [-> T41](T41-match-types.md) | `infer` only exists inside conditional types; every use of `infer` is embedded in a `T extends Pattern<infer R> ? Use<R> : Fallback` conditional. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | `ReturnType<F>` and `Parameters<F>` are the primary tools for introspecting function types; they allow wrapper and decorator types to stay in sync with the wrapped function's signature. |
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | The outer generic parameter (`F`, `T`) must be a type variable for `infer` to bind meaningfully; bounds like `F extends (...args: any[]) => any` constrain the pattern and enable the extraction. Generic interfaces use bounds to constrain what the associated type `T` can be. |
| **Structural Typing** [-> T07](T07-structural-typing.md) | TypeScript's structural type system means `Repository<User>` is satisfied by any object with the right shape — no `implements` declaration required. This makes the generic interface pattern work with duck typing. |
| **Type Aliases** [-> T23](T23-type-aliases.md) | `type Output<F> = F extends (...args: any[]) => infer R ? R : never` packages an `infer` projection into a reusable type alias, making it callable like an associated type projection. |

## 6. Gotchas and Limitations

1. **`infer` only fires when `T` is assignable to the pattern** — if `T` does not match `Array<infer E>`, the conditional type resolves to the false branch (`never` in most utility patterns), not an error; silent mismatches can be hard to debug.

2. **Multiple `infer` positions are independent** — in `T extends Map<infer K, infer V>`, TypeScript infers `K` and `V` separately; if the same variable name appears twice, TypeScript infers an intersection for contravariant positions.

3. **Deferred evaluation** — when `T` is an unresolved type parameter, conditional types (and therefore `infer`) are deferred; the result is opaque and cannot be further narrowed in the same scope.

4. **`ReturnType<typeof overloadedFn>`** — for overloaded functions, TypeScript resolves to the last overload signature; this is often the most permissive and may not match what you expect.

5. **`InstanceType` requires a constructor type** — passing a plain object type (not a class constructor) to `InstanceType<C>` results in `never`; the bound `new (...args: any[]) => any` is required.

6. **Recursive `infer` depth** — deeply recursive unwrapping (like a full `DeepAwaited`) can hit TypeScript's instantiation depth limit; use explicit max-depth bounds or rely on the built-in `Awaited<T>` which handles common cases.

7. **No type-member projection syntax.** TypeScript has no equivalent of Rust's `<T as Iterator>::Item` or Scala's `iter.Item` path-dependent access. To "project" the associated type out of a generic, you must use `infer` in a conditional type, or accept the generic parameter and extract it manually.

8. **Variance of the "associated" generic parameter.** If the type parameter `T` in `interface Serializer<T>` appears only in return positions, mark it covariant with `out T` (TypeScript 4.7+). Getting variance wrong causes confusing assignability errors when composing serializers.

   ```typescript
   interface Producer<out T> {   // TypeScript 4.7+ explicit variance
     produce(): T;
   }
   // Producer<number> is assignable to Producer<number | string> (covariant)
   ```

9. **No associated constants.** Rust and Scala allow associated constants (`const ID: u32`). TypeScript's closest equivalent is a `readonly` static property on a class or a constant in the interface, but there is no language-enforced "one constant per implementation" guarantee the way Rust's `const` in a trait provides.

## 7. Beginner Mental Model

**For generic interfaces:** Think of the interface as a **contract with a blank to fill in**. `Repository<T>` says "a data store for *some* entity type — fill in the blank." Each implementing class writes its entity type in the blank: `UserRepo` writes `User`, `ProductRepo` writes `Product`. Once the blank is filled by the class, every method uses the same concrete type. Generic functions that accept `Repository<T>` work with any filled-in form and track which type is in the blank.

**For `infer`:** Think of an `infer` pattern as a **type-level regex capture group**. `F extends (...args: any[]) => infer R` matches any function type and captures its return type into `R`. The capture is automatic — you provide the function type, and TypeScript fills in the captured type. `ReturnType<typeof fn>` is just a named capture.

The key design question: **who picks the type?**
- Implementor picks → use a generic interface and let the class fix the type argument.
- Derive from an existing type → use `infer` in a conditional type.

## 8. Example A — Serializer with multiple associated types

```typescript
// Two "associated" type parameters: Input and Output
interface Codec<Input, Output> {
  encode(value: Input): Output;
  decode(raw: Output): Input;
}

class JsonCodec implements Codec<object, string> {
  encode(value: object): string { return JSON.stringify(value); }
  decode(raw: string): object { return JSON.parse(raw); }
}

class Base64Codec implements Codec<string, string> {
  encode(value: string): string { return btoa(value); }
  decode(raw: string): string { return atob(raw); }
}

// Generic round-trip — both Input and Output are determined by the codec
function roundTrip<I, O>(codec: Codec<I, O>, value: I): I {
  return codec.decode(codec.encode(value));
}

const obj = roundTrip(new JsonCodec(), { x: 1 }); // typed as object
const str = roundTrip(new Base64Codec(), "hello"); // typed as string
```

## 9. Example B — Iterator-like interface

```typescript
interface Iter<T> {
  next(): { done: false; value: T } | { done: true; value: undefined };
}

class RangeIter implements Iter<number> {
  constructor(private start: number, private end: number) {}
  next() {
    if (this.start < this.end) {
      return { done: false as const, value: this.start++ };
    }
    return { done: true as const, value: undefined };
  }
}

// T is determined by the iterator, not the caller
function collectAll<T>(iter: Iter<T>): T[] {
  const result: T[] = [];
  let step = iter.next();
  while (!step.done) {
    result.push(step.value);
    step = iter.next();
  }
  return result;
}

const nums = collectAll(new RangeIter(0, 5)); // number[]
```

## 12. When to Use Associated Types

**Use generic interfaces (implementor fixes type) when:**

1. **You have a contract with a per-implementation type**: Each implementation should commit to one concrete type.

```typescript
interface Handler<T> {
  handle(input: T): T;
}

class UpperHandler implements Handler<string> {
  handle(input: string): string { return input.toUpperCase(); }
}
// T is fixed as string — clean separation
```

2. **You need type-safe generic combinators**: Functions that compose implementations should preserve the associated type.

```typescript
function compose<T>(a: Handler<T>, b: Handler<T>): Handler<T> {
  return { handle: (x) => b.handle(a.handle(x)) };
}
```

3. **You model domain entities**: Repository, Service, Codec patterns where the entity type defines the implementation.

**Use `infer` projections when:**

1. **Deriving types from existing types**: Extract return types, parameters, or nested types without duplication.

```typescript
type ResponseType<T> = T extends () => infer R ? R : never;
// Automatically stays in sync with the function
```

2. **Creating reusable type utilities**: Library authors exposing derived types.

```typescript
type Element OfArray<T> = T extends readonly unknown[] ? T[number] : never;
```

3. **Adapters and wrappers**: Keeping wrapper signatures synced with wrapped functions.

## 13. When NOT to Use Associated Types

**Avoid generic interfaces when:**

1. **A single class needs multiple type associations**: Prefer separate interfaces or type parameters per role.

```typescript
// Bad: trying to encode multiple associated types in one interface
interface Transform<T, U> { transform(t: T): U }
// Hard to reason about when T and U both vary independently

// Prefer separate roles
interface Source<T> { next(): T }
interface Sink<T> { write(t: T): void }
```

2. **The "associated" type varies per call, not per implementation**: Use regular generic method parameters.

```typescript
// Bad: entity type varies per call
interface Cache<T> { get(): T }

class MultiCache<T> implements Cache<T> {
  get(): T { /* which T? */ }
}

// Prefer: generic method
class Cache {
  get<T>(key: string): T { /* T determined at call site */ }
}
```

3. **You need associated types on function types**: Use tuples or intersection types.

```typescript
// Bad: TypeScript has no "function-associated types"
type Factory = {
  create(): unknown;
  type: unknown; // cannot tie to create's return
}
```

**Avoid `infer` when:**

1. **A simple type alias suffices**: Don't use conditional types for straightforward mappings.

```typescript
// Overkill
type StringOrNumber<T> = T extends string | number ? T : never;

// Simpler
type StringOrNumber = string | number;
```

2. **You're inferring from unknown/unconstrained types**: Results are often `any` or `never`.

```typescript
// Problem: T is not constrained
type Extract<T> = T extends infer U ? U : never;
type X = Extract<any>; // any — inference fails
```

3. **Performance matters with deep recursion**: Recursive `infer` can hit instantiation limits.

## 14. Antipatterns When Using Associated Types

**Antipattern 1: Overly broad generic constraints**

```typescript
// Bad: T can be anything, weakening type safety
interface Box<T> {
  value: T;
}

class AnyBox implements Box<any> {
  value: any = {}; // type safety lost
}

// Prefer: constrain T meaningfully
interface Box<T extends { id: number }> {
  value: T;
}
```

**Antipattern 2: Leaking implementation details in projections**

```typescript
// Bad: exposes internal Promise wrapper
type Handler<F> = F extends () => Promise<infer R> ? R : never;

async function loadData(): Promise<{ data: string }> { ... }
type Result = Handler<typeof loadData>; // { data: string } — good

// But if implementation changes from async to Promise constructor:
function loadData2(): Promise<{ data: string }> {
  return new Promise<...>; // still works — Projection is fragile
}
```

**Antipattern 3: Using `infer` on non-matching types yields `never` silently**

```typescript
type First<T> = T extends [infer A, ...infer _] ? A : never;

type A = First<[1, 2, 3]>; // 1 — works
type B = First<number[]>;   // never — silent failure
type C = First<string>;     // never — silent failure
```

**Antipattern 4: Nested `infer` creates hard-to-read types**

```typescript
// Bad: hard to understand the extraction
type Deep<T> = T extends { data: Promise<{ value: infer V }> } ? V : never;

// Prefer: decompose
type Unwrap<T> = T extends { data: infer D } ? D : never;
type Resolve<T> = T extends Promise<infer V> ? V : T;
type Deep2<T> = Resolve<Unwrap<T>>;
```

## 15. Antipatterns Solved by Associated Types

**Pattern 1: Duplicated return types (solved by `infer`)**

```typescript
// Bad: duplicated return type
function fetchUser(): Promise<User> { ... }
function cacheFetch(): Promise<User> { ... } // duplicated

// Good: derive return type
type User = { id: number; name: string };
function fetchUser(): Promise<User> { ... }

function cacheFetch(): ReturnType<typeof fetchUser> { ... }
// Automatically stays in sync
```

**Pattern 2: Manual type repetition in generic functions**

```typescript
// Bad: must repeat the return type
function retry<F>(fn: F, max: number): F extends () => infer R ? R : never {
  // Error: cannot return type inferred from fn's signature
}

// Good: use ReturnType projection
function retry<F extends () => unknown>(fn: F, max: number): ReturnType<F> {
  return fn();
}
```

**Pattern 3: Uncoupled producer-consumer types**

```typescript
// Bad: disconnected types
type ProducerOutput = string;
interface Producer { produce(): string }

type ConsumerInput = number;
interface Consumer { consume(x: number): void }

// Types can drift apart

// Good: coupled via associated type
interface Pipeline<T> {
  producer: () => T;
  consumer: (x: T) => void;
}

function makePipeline<T>(p: () => T, c: (x: T) => void): Pipeline<T> {
  return { producer: p, consumer: c };
}
```

**Pattern 4: Type assertions in generic code**

```typescript
// Bad: requires type assertions
function clone<T>(obj: T): any {
  const o = Object.assign({}, obj);
  return o as T; // assertion needed
}

// Good: inference handles it
function clone<T>(obj: T): T {
  return Object.assign({}, obj);
}
```

## 16. Example C — `infer` for type-level projections

```typescript
// Extract the value type from any Promise-like
type Resolved<T> = T extends PromiseLike<infer U> ? U : T;

// Extract the key and value types from a Map
type MapKey<T> = T extends Map<infer K, any> ? K : never;
type MapValue<T> = T extends Map<any, infer V> ? V : never;

type M = Map<string, number>;
type K = MapKey<M>;   // string
type V = MapValue<M>; // number

// Build a "type dictionary" — all projection utilities share the same shape
type ProjectionMap<T extends (...args: any[]) => any> = {
  return: ReturnType<T>;
  params: Parameters<T>;
  firstParam: Parameters<T>[0];
};

function greet(name: string, age: number): string { return `${name} is ${age}`; }

type GreetProjections = ProjectionMap<typeof greet>;
// { return: string; params: [string, number]; firstParam: string }
```

## 17. Use-Case Cross-References

- [-> UC-07](../usecases/UC07-callable-contracts.md) Derive parameter and return types of wrapped functions to keep adapters in sync
- [-> UC-19](../usecases/UC19-serialization.md) Extract payload types from codec/schema functions without duplicating type annotations
- [-> UC-04](../usecases/UC04-generic-constraints.md) Generic interfaces with a fixed type parameter encode per-implementation type constraints
- [-> UC-02](../usecases/UC02-domain-modeling.md) Repository and codec patterns where the entity/output type is associated with each implementation class
