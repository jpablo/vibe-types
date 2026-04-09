# Callable Types & Overloads

> **Since:** TypeScript 1.0

## 1. What It Is

TypeScript models functions as first-class types in several ways. A **function type** `(a: A, b: B) => C` describes the shape of a function inline. A **call signature** in an interface `{ (a: A): B; label: string }` allows objects that are both callable and have properties. A **construct signature** `{ new (a: A): B }` describes a class constructor as a type. **Overload signatures** express that a single function has multiple valid input/output combinations: you write several signature-only declarations above the single implementation signature, and TypeScript ensures callers can only use the listed overloads. Generic functions (`<T>(x: T) => T`) abstract over types while preserving the relationship between inputs and outputs. The utility types `ReturnType<F>`, `Parameters<F>`, `ConstructorParameters<F>`, and `ThisParameterType<F>` extract type information from function types.

## 2. What Constraint It Lets You Express

**Constrain which input/output type combinations are valid for a function; overload signatures make impossible or undefined argument combinations into compile errors.**

- Overloads document and enforce which argument combinations are meaningful — for example, `createElement("div")` returning `HTMLDivElement` and `createElement("canvas")` returning `HTMLCanvasElement`, but not `createElement(unknown)` returning `HTMLElement`.
- Generic functions preserve the relationship between input and output types — `identity<T>(x: T): T` guarantees the return type equals the input type, not just `unknown`.
- Call signatures on interfaces allow typed callable objects with additional properties (e.g., middleware chains, event emitters).

## 3. Minimal Snippet

```typescript
// --- Overloaded function: createElement ---
function createElement(tag: "div"): HTMLDivElement;
function createElement(tag: "canvas"): HTMLCanvasElement;
function createElement(tag: "input"): HTMLInputElement;
function createElement(tag: string): HTMLElement {
  return document.createElement(tag);
}

const div = createElement("div");       // OK — HTMLDivElement
const canvas = createElement("canvas"); // OK — HTMLCanvasElement
// const unknown = createElement("span"); // error — not an overloaded signature

// --- Generic identity: preserves input type ---
function identity<T>(x: T): T {
  return x;
}
const s = identity("hello"); // OK — string (not widened to unknown)
const n = identity(42);      // OK — number

// --- Callable interface with properties ---
interface Formatter {
  (value: unknown): string;
  locale: string;
}

const fmt: Formatter = Object.assign(
  (v: unknown) => String(v),
  { locale: "en-US" }
);
console.log(fmt(42), fmt.locale); // OK

// --- ReturnType / Parameters utility types ---
function fetchUser(id: string, token: string): Promise<User> {
  return fetch(`/users/${id}`).then(r => r.json());
}

type FetchParams = Parameters<typeof fetchUser>; // OK — [id: string, token: string]
type FetchReturn = ReturnType<typeof fetchUser>;  // OK — Promise<User>
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | Generic function types are the most common use of generics; bounds (`<T extends Comparable>`) restrict which types can be substituted, combining callable typing with constraint enforcement. |
| **Variadic Tuple Types** [-> T45](T45-paramspec-variadic.md) | `...args: T[]` and `ParameterSpec` (via `infer` in conditional types) allow generic functions that forward or wrap arbitrary parameter lists, enabling typed middleware and decorator patterns. |
| **Associated Types / Utility Types** [-> T49](T49-associated-types.md) | `ReturnType<F>`, `Parameters<F>`, and `ConstructorParameters<F>` are built-in type-level functions that extract type information from callable types, acting as TypeScript's associated-type analogs. |
| **Polymorphic `this`** [-> T33](T33-self-type.md) | Methods with a `this` return type use `this` as an implicit callable type; the receiver's type flows through call chains, composing with overloads in fluent builders. |
| **Variance & Subtyping** [-> T08](T08-variance-subtyping.md) | Function types are contravariant in parameter types and covariant in return types under `strictFunctionTypes`. A `(animal: Animal) => void` is assignable where `(dog: Dog) => void` is expected, but not vice versa. |

## 5. Gotchas and Limitations

1. **Overload implementation is not a public overload** — the implementation signature (the last one with a body) is not visible to callers; only the preceding signature-only declarations are; the implementation signature must be broad enough to accept all listed overloads.
2. **Overloads are checked top-to-bottom** — TypeScript picks the first matching overload; if a broader overload appears before a narrower one, the narrower one is unreachable; always order from most-specific to least-specific.
3. **Generic inference can fail with overloads** — when a generic function is passed as a callback, TypeScript may not be able to infer the type parameter through overload resolution; explicit type arguments may be required.
4. **`Function` type is too broad** — using `Function` as a parameter type accepts any callable but loses all parameter and return type information; prefer explicit function types or generics over `Function`.
5. **Call signatures in interfaces vs `type`** — call signatures can be written in both `interface` and `type` aliases; prefer `type` for plain function types (cleaner syntax) and `interface` only when you need declaration merging or a callable-with-properties shape.
6. **Optional and rest parameters in overloads** — rest parameters in overloads interact with inference in subtle ways; a rest overload `(...args: string[])` can shadow more specific earlier overloads if types overlap.
7. **`strictFunctionTypes` and bivariance** — with `strict` mode (which enables `strictFunctionTypes`), function type parameters are contravariant; however, method signatures in interfaces and classes remain **bivariant** for historical compatibility. This means using `fn: (x: T) => void` in an interface gives stronger checking than `method(x: T): void`:

   ```typescript
   // Method position — bivariant (weaker, historical compatibility)
   interface BivariantBox<T> {
     method(arg: T): void;
   }

   // Function property — contravariant (stronger, correct)
   interface ContravariantBox<T> {
     fn: (arg: T) => void;
   }

   interface Animal { name: string }
   interface Dog extends Animal { breed: string }

   const box: ContravariantBox<Dog> = {
     fn: (a: Animal) => console.log(a.name), // OK — contravariance
   };
   // const box2: ContravariantBox<Animal> = {
   //   fn: (d: Dog) => console.log(d.breed), // error — Dog not assignable to Animal param
   // };
   ```

8. **No `FnOnce`/`FnMut` distinction** — unlike Rust, TypeScript has no concept of a closure that can only be called once or that requires exclusive mutable access. All callable types are freely callable and copyable; ownership and mutation constraints are not tracked by the type system.

## 6. Named Examples

### Example A — Returning function types (factory pattern)

TypeScript analog of Rust's `impl Fn(...)` return — a function that returns a typed function:

```typescript
type Predicate<T> = (value: T) => boolean;

function greaterThan(threshold: number): Predicate<number> {
  return (value) => value > threshold;
}

function inRange(min: number, max: number): Predicate<number> {
  return (value) => value >= min && value <= max;
}

const isAdult = greaterThan(17);
const isValidScore = inRange(0, 100);

console.log(isAdult(20));        // true
console.log(isValidScore(105));  // false

// Composing predicates with generic higher-order functions
function both<T>(p1: Predicate<T>, p2: Predicate<T>): Predicate<T> {
  return (value) => p1(value) && p2(value);
}

const isHighAdultScore = both(isAdult, greaterThan(50));
console.log([18, 45, 70, 99].filter(isHighAdultScore)); // [70, 99]
```

### Example B — Overloads for event emitter dispatch

Overloads model a real-world API where the return type (or callback signature) narrows based on a literal string argument:

```typescript
type EventMap = {
  click: MouseEvent;
  keydown: KeyboardEvent;
  resize: UIEvent;
};

interface TypedEmitter {
  on<K extends keyof EventMap>(event: K, handler: (e: EventMap[K]) => void): this;
  emit<K extends keyof EventMap>(event: K, data: EventMap[K]): boolean;
}

// Overloaded free function variant (pre-TypeScript-2.8 style):
function listen(event: "click", handler: (e: MouseEvent) => void): void;
function listen(event: "keydown", handler: (e: KeyboardEvent) => void): void;
function listen(event: string, handler: (e: Event) => void): void {
  document.addEventListener(event, handler);
}

listen("click", (e) => console.log(e.clientX));    // OK — e: MouseEvent
listen("keydown", (e) => console.log(e.key));       // OK — e: KeyboardEvent
// listen("click", (e: KeyboardEvent) => {});        // error — wrong handler type
```

### Example C — Callable interface vs plain function type

When a callable also carries properties (e.g., a tagged transform or middleware with metadata), a call signature in an interface is the right tool:

```typescript
interface Transform<A, B> {
  (input: A): B;
  readonly name: string;
  compose<C>(other: Transform<B, C>): Transform<A, C>;
}

function makeTransform<A, B>(
  name: string,
  fn: (input: A) => B
): Transform<A, B> {
  const t = Object.assign(fn, {
    name,
    compose<C>(other: Transform<B, C>): Transform<A, C> {
      return makeTransform(`${name} >> ${other.name}`, (a: A) => other(fn(a)));
    },
  });
  return t as Transform<A, B>;
}

const trim = makeTransform("trim", (s: string) => s.trim());
const length = makeTransform("length", (s: string) => s.length);
const trimLength = trim.compose(length);

console.log(trimLength("  hello  ")); // 5
console.log(trimLength.name);          // "trim >> length"
```

## 7. Common Type-Checker Errors

### `No overload matches this call`

TypeScript reports this when no declared overload signature accepts the given arguments.

```typescript
function parse(raw: string): number;
function parse(raw: number): string;
function parse(raw: string | number): string | number {
  return typeof raw === "string" ? parseInt(raw, 10) : raw.toString();
}

parse(true);
// error: No overload matches this call.
//   Overload 1 of 2, '(raw: string): number', gave the following error.
//     Argument of type 'boolean' is not assignable to parameter of type 'string'.
//   Overload 2 of 2, '(raw: number): string', gave the following error.
//     Argument of type 'boolean' is not assignable to parameter of type 'number'.
```

**Fix:** check the argument type against each overload and either add a new overload or fix the call site.

### `This overload signature is not compatible with its implementation signature`

The implementation signature must be a supertype of all overload signatures.

```typescript
function wrap(x: string): string[];
function wrap(x: number): number[];
// error — implementation returns (string | number)[] which is not string[] or number[]
function wrap(x: string | number): (string | number)[] { return [x]; }

// Fix: widen the implementation signature
function wrap(x: string): string[];
function wrap(x: number): number[];
function wrap(x: string | number): string[] | number[] { return [x] as any; }
```

### `Argument of type '(x: Dog) => void' is not assignable to parameter of type '(x: Animal) => void'`

With `strictFunctionTypes`, function parameter types are contravariant. A handler that only handles `Dog` cannot substitute where a handler for any `Animal` is required.

```typescript
interface Animal { name: string }
interface Dog extends Animal { breed: string }

function callWithAnimal(fn: (a: Animal) => void) { fn({ name: "generic" }); }

callWithAnimal((d: Dog) => console.log(d.breed));
// error — Property 'breed' does not exist on type 'Animal'
// (would be a runtime crash if allowed)
```

### `Type 'void' is not assignable to type 'string'` in callbacks

Forgetting `return` in a callback body when the callback type expects a return value.

```typescript
const lengths = ["a", "bb", "ccc"].map((s): number => {
  s.length; // forgot `return`
  // error: A function whose declared type is neither 'undefined', 'void',
  //        nor 'any' must return a value.
});
```

## 8. Beginner Mental Model

Think of function types as **shape labels for functions**: any function whose parameter types and return type match the label fits, regardless of its name or where it was defined. Overloads add **multiple labels** to the same function so the type checker can narrow the return type based on which label matches the arguments at a given call site.

Compared to Rust: TypeScript has no `Fn`/`FnMut`/`FnOnce` hierarchy because TypeScript does not track ownership or mutation. Any function type can be called any number of times; there is no concept of "consuming" a closure.

Compared to Python: TypeScript's function types encode parameter names, optional parameters, and rest parameters directly in the type — you do not need a separate `Protocol` with `__call__` to express keyword arguments. The `interface` with a call signature is the equivalent of Python's callable Protocol.

## 9. Use-Case Cross-References

- [-> UC-07](../usecases/UC07-callable-contracts.md) Enforce callable contracts with precise input/output type pairings via overloads and generic function types
- [-> UC-04](../usecases/UC04-generic-constraints.md) Express generic algorithms that preserve the relationship between parameter types and return types

## 10. When to Use

Use callable typing and overloads when you need to:

- **Narrow return types by literal arguments**: Overloads make invalid combinations compile errors.

  ```typescript
  function getShape(kind: "circle", r: number): Circle;
  function getShape(kind: "rect", w: number, h: number): Rect;
  function getShape(kind: string, ...args: number[]) { /* ... */ }

  const c = getShape("circle", 5);     // Circle
  // getShape("circle", 5, 10);        // error — wrong overload
  ```

- **Preserve input-output type relationships**: Generic functions keep the connection between arguments and results.

  ```typescript
  function first<T>(arr: T[]): T { return arr[0]!; }
  const s = first(["a", "b"]); // string, not any
  ```

- **Create callable objects with properties**: Use call signatures when the function needs state or metadata.

  ```typescript
  interface Logger {
    (msg: string): void;
    level: "debug" | "info";
  }
  ```

- **Extract types from functions**: Utility types (`ReturnType`, `Parameters`) for inference propagation.

  ```typescript
  type UserId = ReturnType<typeof extractId>; // inferred from function
  ```

## 11. When Not to Use

Avoid callable typing and overloads when:

- **The function has a single straightforward signature**: Overengineering with overloads adds maintenance cost.

  ```typescript
  // Unnecessary overloads
  function add(a: number, b: number): number;
  function add(a: number, b: number): number { return a + b; }

  // Prefer
  function add(a: number, b: number): number { return a + b; }
  ```

- **Arguments are truly interchangeable**: Use optional parameters or overloading is not needed.

  ```typescript
  // Overkill
  function connect(host: string, port?: number): Connection;
  function connect(config: ConnectionConfig): Connection;
  // ... impl

  // Simpler with optional
  function connect(host: string, port = 80): Connection { /* ... */ }
  ```

- **You're modeling unrelated operations**: Separate functions are clearer than overloaded ambiguity.

  ```typescript
  // Confusing: same name, unrelated behavior
  function parse(s: string): number;
  function parse(n: number): string;

  // Clearer: distinct functions
  function parseString(s: string): number { /* ... */ }
  function toString(n: number): string { /* ... */ }
  ```

- **Type inference can solve it**: Sometimes generics alone suffice without extra signatures.

  ```typescript
  // Overcomplicated
  function map<T>(arr: T[], fn: (x: T) => number): number[];
  function map<T, U>(arr: T[], fn: (x: T) => U): U[];
  function map<T, U>(arr: T[], fn: (x: T) => U): U[] { return arr.map(fn); }

  // Simpler: one generic overload handles both
  function map<T, U>(arr: T[], fn: (x: T) => U): U[] { return arr.map(fn); }
  ```

## 12. Antipatterns When Using Callable Typing

### Overload ordering mistake

Broad overload before narrow one makes the narrow unreachable.

```typescript
// ❌ Wrong: narrow overload unreachable
function f(x: string | number): string;
function f(x: number): number;
function f(x) { /* ... */ }

// Correct: narrow first
function f(x: number): number;
function f(x: string): string;
function f(x: string | number): string { return String(x); }
```

### Implementation narrows return type

Implementation must be a supertype of all overloads.

```typescript
// ❌ Wrong: implementation is too narrow
function get(x: string): string;
function get(x: number): number;
function get(x) { return "always string"; } // error — violates number overload

// Correct: widen implementation
function get(x: string): string;
function get(x: number): number;
function get(x: string | number): string | number {
  return typeof x === "string" ? x : x.toString();
}
```

### Shadowing overloads with rest

Rest parameters can shadow all previous overloads.

```typescript
// ❌ Wrong: rest param makes everything "any"
function create(arg: string): A;
function create(arg1: string, arg2: number): B;
function create(...args: any[]) { return null; }

// Correct: typed rest
function create(arg: string): A;
function create(arg1: string, arg2: number): B;
function create(...args: (string | number)[]) { return null as any; }
```

### Using `Function` instead of explicit types

Loses all type information.

```typescript
// ❌ Wrong
type Fn = Function; // accepts any callable, no checking

// Correct
type Fn = (x: number) => string; // precise checking
```

### Overloading for control flow

Overloads are for typing, not runtime behavior routing.

```typescript
// ❌ Wrong: runtime logic in overload resolution
function process(x: number): void { /* ... */ }
function process(x: string): void { /* different logic */ }
function process(x) {
  if (typeof x === "number") /* a */
  else if (typeof x === "string") /* b */
}

// Better: single implementation with internal dispatch
function process(x: number): void;
function process(x: string): void;
function process(x: number | string): void {
  if (typeof x === "number") handleNumber(x);
  else handleString(x);
}
```

## 13. Antipatterns with Other Techniques (Solved by Callable Typing)

### Using union types instead of generics

Union types lose input-output relationships.

```typescript
// ❌ Wrong: loses connection between array and element
function head(arr: string[] | number[]): string | number {
  return arr[0];
}
const s = head(["a", "b"]); // string | number, narrowed incorrectly

// ✅ With generics: preserves relationship
function head<T>(arr: T[]): T { return arr[0]; }
const s = head(["a", "b"]); // string
```

### Using `any` instead of proper types

Defeats the purpose of type checking.

```typescript
// ❌ Wrong
function wrap<T>(x: any): any { return { value: x }; }

// ✅ With proper generic callable
function wrap<T>(x: T): { value: T } { return { value: x }; }
```

### Manual type assertions instead of inference

Breaks refactoring safety.

```typescript
// ❌ Wrong
const result = fetch("/user").then(r => r.json()) as Promise<User>;

// ✅ With ReturnType inference
function fetchUser(): Promise<User> { return fetch("/user").then(r => r.json()); }
type UserPromise = ReturnType<typeof fetchUser>;
```

### Using callback type `(...args: any[]) => any`

Losse s all param and return type information.

```typescript
// ❌ Wrong
type Handler = (...args: any[]) => any;

// ✅ With explicit callable type
type Handler = (event: MouseEvent) => void;
```

### Duplicate overloads via union in parameter position

Unions in parameter positions often signal missing overloads.

```typescript
// ❌ Wrong: ambiguous, loses precision
function connect(host: string, port: number | string): void;

// ✅ With overloads: precise
function connect(host: string, port: number): void;
function connect(config: { host: string; port: number }): void;
function connect(hostOrConfig: string | object, port?: number) { /* ... */ }
```

## Source Anchors

- [TypeScript Handbook — More on Functions](https://www.typescriptlang.org/docs/handbook/2/functions.html) — function types, overloads, generics, `this` parameter
- [TypeScript Handbook — Object Types](https://www.typescriptlang.org/docs/handbook/2/objects.html) — call signatures and construct signatures in interfaces
- [TypeScript 2.6 release notes — `strictFunctionTypes`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-2-6.html) — contravariance for function type parameters
- [`lib.es5.d.ts` — `ReturnType`, `Parameters`, `ConstructorParameters`](https://github.com/microsoft/TypeScript/blob/main/src/lib/es5.d.ts) — utility type implementations
