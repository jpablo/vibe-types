# Type Narrowing & Exhaustiveness

> **Since:** TypeScript 2.0 (type guards); TypeScript 4.4 (control-flow analysis for aliased conditions)

## 1. What It Is

**Type narrowing** is TypeScript's control-flow analysis: the compiler tracks which types are possible at each point in the code based on the checks performed before that point. After an `if (x !== null)` check, `x` is typed as the non-null version for the rest of the `if` block. After a `switch (shape.kind)` on a discriminated union, each `case` branch has `shape` narrowed to the exact variant. Narrowing mechanisms include: `typeof` (primitive type), `instanceof` (class prototype chain), `in` operator (property presence), discriminant property checks (literal equality), truthiness narrowing, equality narrowing (`=== / !==`), user-defined **type guards** (`function isString(x: unknown): x is string`), and **assertion functions** (`function assert(x: unknown): asserts x is string`). **Exhaustiveness** is enforced by assigning the value in the `default` branch to a `never`-typed variable: if any variant is unhandled, the value is not `never`, causing a compile error.

## 2. What Constraint It Lets You Express

**After a check, the type in each branch is narrowed to the most specific type consistent with the check; a `switch` over all discriminated union variants fails to compile if any variant is missing a case.**

- The compiler understands that `if (typeof x === "string")` makes `x` a `string` in the `then` branch and narrows the `else` branch by removing `string` from the union.
- User-defined type guards encode arbitrary runtime checks as compile-time narrowing, extending control-flow analysis beyond built-in predicates.
- The `never` exhaustiveness check turns adding a new variant into a compile error at every unupdated switch site.

## 3. Minimal Snippet

```typescript
// Discriminated union with exhaustive switch
type Shape =
  | { kind: "circle";    radius: number }
  | { kind: "rectangle"; width: number; height: number }
  | { kind: "triangle";  base: number; height: number };

// Idiomatic exhaustiveness helper — throws at runtime if a new variant slips past
function assertNever(x: never, msg?: string): never {
  throw new Error(msg ?? `Unhandled variant: ${JSON.stringify(x)}`);
}

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2;     // narrowed to circle variant
    case "rectangle":
      return shape.width * shape.height;       // narrowed to rectangle variant
    case "triangle":
      return 0.5 * shape.base * shape.height; // narrowed to triangle variant
    default:
      return assertNever(shape); // compile error if a new variant is added without a case
  }
}

// typeof narrowing
function stringify(x: string | number | boolean): string {
  if (typeof x === "string")  return x.toUpperCase();  // string
  if (typeof x === "number")  return x.toFixed(2);     // number
  return x ? "yes" : "no";                             // boolean
}

// instanceof narrowing
class Circle { constructor(public radius: number) {} }
class Rectangle { constructor(public w: number, public h: number) {} }

function describeShape(s: Circle | Rectangle): string {
  if (s instanceof Circle) {
    return `circle r=${s.radius}`;       // narrowed to Circle
  }
  return `rect ${s.w}×${s.h}`;          // narrowed to Rectangle
}

// User-defined type guard
interface Cat { meow(): void }
interface Dog { bark(): void }

function isCat(animal: Cat | Dog): animal is Cat {
  return "meow" in animal; // runtime check
}

function speak(animal: Cat | Dog): void {
  if (isCat(animal)) {
    animal.meow(); // OK — narrowed to Cat
  } else {
    animal.bark(); // OK — narrowed to Dog in the else branch
  }
}

// Assertion function
function assertString(x: unknown): asserts x is string {
  if (typeof x !== "string") throw new TypeError("Expected string");
}

function process(raw: unknown): string {
  assertString(raw); // throws if not string; after this line, raw is string
  return raw.toUpperCase(); // OK — narrowed to string
}
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Discriminated Unions & ADTs** [-> T01](T01-algebraic-data-types.md) | Discriminated union narrowing is the primary consumer of control-flow analysis; the discriminant field is the cue that drives the `switch` narrowing. |
| **Union Types** [-> T02](T02-union-intersection.md) | Every narrowing step progressively eliminates union members; after all members are handled the remainder is `never`. |
| **Null Safety** [-> T13](T13-null-safety.md) | Null narrowing is the most common narrowing operation: `x !== null` removes `null` from `x`'s type in the true branch. |
| **Never / Bottom** [-> T34](T34-never-bottom.md) | `never` is the type that results when all union members have been narrowed away; the exhaustiveness trick exploits the fact that assigning to `never` is only valid when the type is actually `never`. |
| **Literal Types** [-> T52](T52-literal-types.md) | Discriminant fields must be literal types; literal equality checks are the trigger for discriminated-union narrowing. |

## 5. Gotchas and Limitations

1. **Narrowing does not survive function boundaries** — passing a narrowed value to another function loses the narrowing; the callee sees the original union type. Use type guards or assertion functions to re-establish narrowing inside the callee.

2. **Type predicates only narrow the positive branch when the parameter is broad** — when the parameter type is `unknown` or a supertype wider than the union, TypeScript does *not* narrow the `else` branch. When the parameter is already a concrete union, both branches are narrowed (similar to Python's `TypeIs`):

   ```typescript
   // parameter is unknown → else branch is still unknown
   function isString(x: unknown): x is string {
     return typeof x === "string";
   }
   function f(x: unknown): void {
     if (isString(x)) {
       x.toUpperCase(); // OK — x is string
     } else {
       // x is still unknown here, NOT narrowed to "not-string"
     }
   }

   // parameter is a concrete union → else branch IS narrowed
   function isStringInUnion(x: string | number): x is string {
     return typeof x === "string";
   }
   function g(x: string | number): void {
     if (isStringInUnion(x)) {
       x.toUpperCase(); // string
     } else {
       x.toFixed(2);   // number — correctly narrowed in else
     }
   }
   ```

3. **Type aliases for conditions (TS 4.4)** — before TypeScript 4.4, assigning a narrowing condition to a `const` alias (`const isString = typeof x === "string"`) and then using the alias in an `if` did not narrow; TypeScript 4.4 fixed this for `const` discriminant aliases.

   ```typescript
   function process(x: string | null): string {
     const hasValue = x !== null; // const alias — works in TS 4.4+
     if (hasValue) return x.toUpperCase(); // OK
     return "";
   }
   ```

4. **`in` narrowing requires the property to be optional or missing** — `"x" in obj` narrows correctly when `x` is optional; if `x` is present on all members of the union, the `in` check does not meaningfully narrow.

5. **Type guards are trust-based** — the body of a user-defined type guard is not verified; `function isString(x: unknown): x is string { return true; }` compiles without error but is incorrect. Tests are the only safety net.

6. **Assertion functions require `asserts` in the return type annotation** — without the explicit annotation, TypeScript does not treat the function as an assertion and no narrowing occurs.

7. **Mutation and closures can invalidate narrowing** — TypeScript knows that a callback or async continuation could mutate a captured `let` variable, so it widens the type back to the declared type inside the callback even when you narrowed it before:

   ```typescript
   function fetchUser(id: string): void {
     let data: string | null = getData(id);

     if (data !== null) {
       // TS sees data as string here...
       setTimeout(() => {
         console.log(data.toUpperCase()); // error: data is string | null
         // ...because data could have been reassigned to null between
         // the check and the callback execution
       }, 0);
     }
   }
   // Fix: capture in a const at narrowing point
   // const safeData = data; — safeData stays string inside the callback
   ```

8. **Narrowing through truthiness is imprecise with `0`, `""`, and `false`** — `if (x)` narrows out `null`, `undefined`, `0`, `""`, and `false`; if `0` is a valid value for `x: number | null`, use `!== null` instead.

## Coming from JavaScript

JavaScript developers use `typeof`, `instanceof`, and property checks at runtime for the same purpose. TypeScript's innovation is making the compiler understand these runtime checks and use them to narrow the *static* type — so that after the check, you get compile-time autocomplete and error detection appropriate to the narrowed type, not just the original broad type.

## Example A — Narrowing raw API responses into domain types

```typescript
// Raw payload from a REST endpoint
type ApiResponse =
  | { status: "ok";    data: { id: string; name: string } }
  | { status: "error"; code: number; message: string }
  | { status: "pending" };

function assertNever(x: never): never {
  throw new Error(`Unhandled status: ${JSON.stringify(x)}`);
}

function handleResponse(res: ApiResponse): string {
  switch (res.status) {
    case "ok":
      // narrowed: res.data is available, code/message are not
      return `User: ${res.data.name} (${res.data.id})`;
    case "error":
      // narrowed: res.code and res.message are available
      return `Error ${res.code}: ${res.message}`;
    case "pending":
      return "Request in progress…";
    default:
      return assertNever(res); // compile error if a new status is added
  }
}
```

If the `ApiResponse` union grows (e.g., a new `"rate-limited"` variant is added), the `default` branch fails to compile at every unupdated `switch` site, and `assertNever` provides a runtime guard in case the compiled JavaScript receives an unexpected value from a legacy endpoint.

## Example B — Type guard pipeline for validating external data

Custom type guards bridge the gap between runtime validation and compile-time narrowing. Because TypeScript does not verify the guard body, pair guards with a runtime validation library (Zod, Valibot) or explicit field checks:

```typescript
interface Point2D { x: number; y: number }
interface Point3D { x: number; y: number; z: number }

// Guard narrows from a broad base to a specific interface.
// Parameter is a concrete union, so the else branch is narrowed too.
function is3D(p: Point2D | Point3D): p is Point3D {
  return "z" in p;
}

function distance(p: Point2D | Point3D): number {
  if (is3D(p)) {
    return Math.sqrt(p.x ** 2 + p.y ** 2 + p.z ** 2); // p.z available
  }
  return Math.sqrt(p.x ** 2 + p.y ** 2);               // narrowed to Point2D; p.z absent
}

// When the input is truly unknown (from JSON.parse etc.),
// combine with an assertion function that throws on bad input:
function assertPoint2D(raw: unknown): asserts raw is Point2D {
  if (
    typeof raw !== "object" || raw === null ||
    typeof (raw as Record<string, unknown>).x !== "number" ||
    typeof (raw as Record<string, unknown>).y !== "number"
  ) {
    throw new TypeError("Expected Point2D");
  }
}

function parsePoint(json: string): Point2D {
  const raw = JSON.parse(json);
  assertPoint2D(raw);   // throws if invalid; after this, raw is Point2D
  return raw;           // OK — narrowed
}
```

## Common Type-Checker Errors

### `Type 'X' is not assignable to type 'never'` (in an exhaustiveness default)

The `default` branch of a `switch` (or the final `else`) received a value of type `X`, meaning variant `X` is not handled earlier. Add a `case "x":` branch for it.

### `Property 'y' does not exist on type 'A | B'` after a type guard

The narrowing did not produce the type you expected. Common causes: (a) the guard parameter type was `unknown`/`any` and the `else` branch was not narrowed; (b) the `in` guard checked a property that exists on all members of the union; (c) the variable is `let` and TypeScript widened it back because a callback could reassign it.

### `Argument of type 'string | null' is not assignable to parameter of type 'string'`

Narrowing was not applied or was lost. Check that: the variable is `const` (or narrowed inside the same scope), no callback or async gap separates the check from the use, and the check is an exact equality (`=== null`) rather than a truthiness test when `""` / `0` are valid values.

### `Not all code paths return a value`

Often accompanies an incomplete union narrowing: a `switch` missing a case means TypeScript considers a code path where nothing is returned. Add the missing `case` or a `default: return assertNever(x)`.

### `Unreachable code detected`

TypeScript has determined that a branch is dead because earlier narrowing already eliminated all matching types. This is usually a sign that the union declaration is more specific than you thought, or that a type guard is always true/false.

## 6. Use-Case Cross-References

- [-> UC-03](../usecases/UC03-exhaustiveness.md) Exhaustive variant handling with the `never` check pattern
- [-> UC-01](../usecases/UC01-invalid-states.md) Narrowing prevents access to variant-specific fields on the wrong variant
- [-> UC-16](../usecases/UC16-nullability.md) Null narrowing as the primary mechanism for safe nullable value access

## When to Use It

- **Handling discriminated unions**: Use `switch` on the discriminant to safely access variant-specific fields.

  ```typescript
  type Op = { type: "add"; a: number } | { type: "mul"; a: number; b: number };

  function evaluate(op: Op): number {
    switch (op.type) {
      case "add": return op.a + 1;
      case "mul": return op.a * op.b;
      default: throw new Error("unreachable");
    }
  }
  ```

- **Validating external data**: Use type guards or assertion functions to transition from `unknown` to a known structure.

  ```typescript
  function isUser(x: unknown): x is { id: string } {
    return typeof x === "object" && x !== null && typeof (x as any).id === "string";
  }

  function load(raw: unknown) {
    if (isUser(raw)) return raw.id;
  }
  ```

- **Ensuring exhaustiveness**: Use `assertNever` in the `default` branch to catch missing cases at compile time.

  ```typescript
  type Status = "idle" | "loading" | "done";

  function render(s: Status) {
    switch (s) {
      case "idle": return "Idle";
      case "loading": return "Loading…";
      case "done": return "Done";
      default: throw new Error(`Unreachable: ${s as never}`);
    }
  }
  ```

- **Guarding nullable values**: Use `!== null` or `!= null` to remove `null`/`undefined` from unions.

  ```typescript
  function firstChar(s: string | null) {
    if (s != null) return s[0];
    return " ";
  }
  ```

## When Not to Use It

- **When the union is too broad**: Narrowing `unknown` or `any` doesn't help; those types short-circuit type checking.

  ```typescript
  // Bad: input is any
  function process(x: any) {
    if (typeof x === "string") {
      x.toUpperCase(); // No safety, `any` bypasses checks
    }
  }
  ```

- **Inside callbacks after a `let` check**: Narrowing is lost; use a `const` copy instead.

  ```typescript
  // Bad: narrowing lost in callback
  function render(value: string | null) {
    if (value != null) {
      setTimeout(() => console.log(value.length), 0); // Error
    }
  }

  // Good: capture in const
  function renderFixed(value: string | null) {
    if (value != null) {
      const v = value;
      setTimeout(() => console.log(v.length), 0); // OK
    }
  }
  ```

- **When a simple default is acceptable**: Exhaustiveness checks are overkill for fall-through logic.

  ```typescript
  // Bad: overengineered for non-exhaustive fallback
  function colorToHex(c: "red" | "blue" | string): string {
    switch (c) {
      case "red": return "#f00";
      case "blue": return "#00f";
      default: throw new Error(`Unreachable: ${c as never}`); // Wrong
    }
  }

  // Good: use fallback for open string values
  function colorToHexFixed(c: "red" | "blue" | string): string {
    switch (c) {
      case "red": return "#f00";
      case "blue": return "#00f";
      default: return "#000"; // Fallback for arbitrary strings
    }
  }
  ```

## Antipatterns When Using Type Narrowing

### 1. Truthiness narrowing for `0` or `""`

```typescript
// Bad: loses valid 0/""/false values
function process(n: number | null) {
  if (n) console.log(n.toFixed(2)); // Misses n === 0
}

// Good: explicit null check
function processFixed(n: number | null) {
  if (n !== null) console.log(n.toFixed(2));
}
```

### 2. Repeated redundant narrowing

```typescript
// Bad: redundant checks
function describe(x: string | number) {
  if (typeof x === "string") {
    if (typeof x === "string") { // Redundant
      console.log(x.toUpperCase());
    }
  }
}

// Good: single check
function describeFixed(x: string | number) {
  if (typeof x === "string") console.log(x.toUpperCase());
}
```

### 3. Type guard on a non-discriminative property

```typescript
// Bad: property exists on all variants
interface Cat { name: string; meow(): void }
interface Dog { name: string; bark(): void }

function isCatByName(a: Cat | Dog): a is Cat {
  return "meow" in a; // OK, but this doesn't work:
}

function isCatByNameWrong(a: Cat | Dog): a is Cat {
  return "name" in a; // Always true, never narrows
}
```

### 4. Assertion function without proper throw

```typescript
// Bad: no runtime guard
function assertString(x: unknown): asserts x is string {
  // Empty body: type is string, but runtime is anything
}

// Good: explicit check
function assertStringFixed(x: unknown): asserts x is string {
  if (typeof x !== "string") throw new TypeError("string expected");
}
```

## Antipatterns Fixed by Type Narrowing

### 1. Type assertion (`as`) instead of guards

```typescript
// Bad: unsafe cast, no runtime check
function parseUser(json: unknown): string {
  const u = JSON.parse(json) as { id: string }; // Runtime risk
  return u.id;
}

// Good: assertion with validation
function parseUserFixed(json: unknown): string {
  const raw = JSON.parse(json);
  if (typeof raw !== "object" || raw === null || typeof raw.id !== "string") {
    throw new TypeError("invalid user");
  }
  return raw.id; // Safe, narrowed
}
```

### 2. `any` for "external data"

```typescript
// Bad: loses all type safety
function render(api: any) {
  return api.status + ": " + api.data;
}

// Good: discriminated union + narrowing
type ApiResult = { status: string; data: string };
function renderFixed(api: ApiResult) {
  return api.status + ": " + api.data;
}
```

### 3. Runtime `typeof` without narrowing

```typescript
// Bad: runtime check only, no type benefit
function describe(x: string | number) {
  if (typeof x == "string") {
    console.log(x.toUpperCase()); // TS still sees union
  }
}

// Good: TypeScript narrows after `===`
function describeFixed(x: string | number) {
  if (typeof x === "string") {
    console.log(x.toUpperCase()); // x is string
  }
}
```

### 4. Partial switch without exhaustiveness

```typescript
// Bad: silently ignores new variants
type Message = { type: "a" } | { type: "b" } | { type: "c" };

function handle(msg: Message) {
  switch (msg.type) {
    case "a": break; // Missing "b" and "c"
  }
}

// Good: exhaustive
function handleFixed(msg: Message) {
  switch (msg.type) {
    case "a": break;
    case "b": break;
    case "c": break;
    default: throw new Error(`Unreachable: ${msg as never}`);
  }
}
```
