# Type Assertions & Coercions

> **Since:** TypeScript 1.0 (`as` assertions); `satisfies` since TypeScript 4.9

## 1. What It Is

TypeScript provides several explicit mechanisms for bridging between types. **Type assertions** (`value as T`) instruct the compiler to treat a value as a given type, bypassing structural compatibility checks — no runtime conversion occurs. The **double assertion** idiom (`value as unknown as T`) sidesteps even the overlap requirement for unrelated types, making it the escape hatch of last resort. **User-defined type predicates** (`function isEmail(x: unknown): x is Email`) narrow the type in the calling scope when the function returns `true`. **Assertion functions** (`function assert(cond: boolean): asserts cond`) narrow the type of subsequent code when they do not throw. The **`satisfies` operator** (TypeScript 4.9) validates that an expression conforms to a type without widening it to that type, preserving the literal or inferred type for downstream use.

**Runtime conversions** are a separate concern from compile-time assertions. JavaScript built-ins — `Number(x)`, `String(x)`, `Boolean(x)`, `parseInt(s, 10)`, `parseFloat(s)` — perform actual value conversion at runtime. TypeScript types these correctly (e.g., `Number(x)` always returns `number`), but the type system does not track *whether* a conversion is lossless — `Number("abc")` types as `number` while producing `NaN`.

**Type aliases** (`type Meters = number`) are fully transparent synonyms. They introduce no distinct type — the compiler treats `Meters` and `number` as identical everywhere. For domain-level safety, use opaque/branded types instead [→ T03](T03-newtypes-opaque.md).

**`as const`** (const assertions) are a special form of assertion that instructs the compiler to infer the narrowest possible literal type for an expression rather than widening it. `[1, 2, 3] as const` produces `readonly [1, 2, 3]` rather than `number[]`; `{ kind: "circle" } as const` produces `{ readonly kind: "circle" }` rather than `{ kind: string }`. This is the canonical way to freeze a value into its most precise type without assigning a manual annotation.

**Custom primitive coercion** in JavaScript is controlled by `valueOf()` and `Symbol.toPrimitive`. TypeScript models these structurally: objects with `valueOf(): number` are accepted where `number` is expected by many built-in operators, even though the type system does not automatically widen the static type.

## 2. What Constraint It Lets You Express

**All conversions are explicit and opt-in; TypeScript has no implicit coercions between types — every boundary crossing is visible in source code.**

- `as T` is a compile-time-only assertion; it cannot convert a `string` to a `number` at runtime — if the runtime value does not match `T`, behavior is undefined.
- `satisfies T` checks shape conformance at the point of use without widening; the variable keeps its most precise type rather than being boxed into `T`.
- `as const` narrows a value to its most precise literal type, preventing widening; it does not freeze the value at runtime (only `Object.freeze` does that).
- Type predicates and assertion functions are the correct way to narrow at runtime boundaries (JSON parsing, API responses) because they tie runtime checks to type narrowing.
- **`unknown` is the safe conversion boundary; `any` is the unsafe one.** At an untyped boundary (JSON, external APIs), prefer `unknown` over `any`. An `unknown` value forces an explicit assertion or guard before use; an `any` value silently infects the type system because every operation on `any` returns `any`.

## 3. Minimal Snippet

```typescript
// --- as T: bypass structural check (no runtime effect) ---
const raw: unknown = fetchJson();
const user = raw as { name: string; age: number }; // OK — trust the caller
// (user as string) // error — no overlap between object and string
const forced = raw as unknown as string;            // OK — double assertion always compiles

// --- satisfies: validate shape without widening ---
const palette = {
  red: [255, 0, 0],
  green: "#00ff00",
} satisfies Record<string, string | number[]>;
// palette.red is still number[], not string | number[]  // OK — literal type preserved
// palette.missing                                        // error — key does not exist

// --- User-defined type predicate ---
interface Cat { meow(): void }
interface Dog { bark(): void }

function isCat(animal: Cat | Dog): animal is Cat {
  return "meow" in animal;
}

function greet(animal: Cat | Dog) {
  if (isCat(animal)) {
    animal.meow(); // OK — narrowed to Cat
  } else {
    animal.bark(); // OK — narrowed to Dog
  }
}

// --- Assertion function ---
function assertDefined<T>(val: T | null | undefined, msg: string): asserts val is T {
  if (val == null) throw new Error(msg);
}

const maybeUser: string | null = getUser();
assertDefined(maybeUser, "User must be present");
maybeUser.toUpperCase(); // OK — narrowed to string after assertion
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | Type predicates and assertion functions are the user-extensible extension points of the narrowing system; built-in narrowing handles `typeof`/`instanceof`, while predicates cover domain-specific runtime checks. |
| **Gradual Typing** [-> T47](T47-gradual-typing.md) | `as unknown as T` is the primary escape hatch when integrating untyped or weakly-typed code; it is the explicit bridge from the `unknown` boundary into the typed world. |
| **Null Safety** [-> T13](T13-null-safety.md) | The non-null assertion operator `x!` is a shorthand assertion that `x` is not `null` or `undefined`; assertion functions (`asserts val is T`) are the principled alternative that proves the non-null condition. |
| **Structural Typing** [-> T07](T07-structural-typing.md) | `as T` requires structural overlap between the source and target types; structurally unrelated types require the double-assertion escape hatch, signaling a dangerous boundary. |
| **Opaque / Branded Types** [-> T03](T03-newtypes-opaque.md) | Type aliases are transparent (`type Meters = number` — no safety); branded types (`type Meters = number & { _brand: "Meters" }`) give the domain separation that Rust newtypes or Python `NewType` provide. |
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | A generic function can express "accepts anything convertible to T" by taking a callback or using an interface with a conversion method, mirroring Rust's `Into<T>` bound or Python's `SupportsFloat`. |
| **Algebraic Data Types** [-> T01](T01-algebraic-data-types.md) | Pattern matching via discriminated unions is the principled alternative to casting between variants — prefer narrowing over `as`. |
| **`as const` and literal types** | `as const` is the narrowing counterpart to widening assertions; it prevents TypeScript from generalizing `"red"` to `string` or `[1, 2]` to `number[]`, and is the idiomatic way to produce tuple types and string-literal union members. |

## 5. Gotchas and Limitations

1. **`as` has no runtime effect** — asserting `x as T` does not convert or validate `x`; if `x` is not actually a `T` at runtime, downstream code will silently operate on the wrong type.
2. **`satisfies` does not narrow variables** — `satisfies` checks the expression at the point of use but does not change the declared type of the variable; it is most useful for inline objects and `const` declarations.
3. **Double assertion is an escape hatch, not a tool** — `x as unknown as T` compiles unconditionally; use it only at genuine type boundaries (e.g., FFI, deserialized JSON) and add a comment explaining why the assertion is safe.
4. **Predicate purity is not enforced** — TypeScript trusts that a `x is T` function accurately reflects the runtime check; a predicate that lies (always returns `true`) will produce unsound types silently.
5. **`asserts` functions must be declared separately** — arrow functions cannot have `asserts` return types in all TypeScript versions; prefer `function` declarations for assertion functions.
6. **`satisfies` and type widening** — `satisfies` does not help when a value is passed to a function expecting the wide type; the parameter's type is still widened at the call site.
7. **Type aliases are transparent — they provide zero type safety.** `type Meters = number` and `type Seconds = number` are the same type. The compiler will not catch `speed(seconds, meters)` if the arguments are swapped. Use a branded type when domain separation matters:

   ```typescript
   // Unsafe — aliases are synonyms
   type Meters = number;
   type Seconds = number;
   function speed(d: Meters, t: Seconds): number { return d / t; }
   const t: Seconds = 10;
   const d: Meters = 100;
   speed(t, d); // compiles — arguments swapped, bug undetected

   // Safe — brands are distinct at the type level
   type Meters  = number & { readonly _brand: "Meters" };
   type Seconds = number & { readonly _brand: "Seconds" };
   const mkMeters  = (n: number): Meters  => n as Meters;
   const mkSeconds = (n: number): Seconds => n as Seconds;
   speed(mkSeconds(10), mkMeters(100)); // error: Seconds is not assignable to Meters
   ```

8. **Runtime conversions can produce surprising values.** `Number("abc")` returns `NaN`, `Number(true)` returns `1`, `Boolean("")` returns `false`. TypeScript types all of these as `number` or `boolean` respectively — it cannot reason about runtime value validity. Validate after conversion when the input source is untrusted.
9. **JavaScript implicit coercions still happen at runtime.** TypeScript prevents many type mismatches at compile time, but JS's implicit coercions fire at runtime: `"5" - 3` yields `2` (JS coerces the string), `[] + {}` yields `"[object Object]"`. Strict mode (`"use strict"`) and `===` do not prevent arithmetic coercions. TypeScript's type system only checks the static picture; it cannot block coercions that arise from `any` or external data.
10. **`valueOf()` and `Symbol.toPrimitive` affect operator behavior, not static types.** If a class defines `valueOf(): number`, JavaScript's `+`, `-`, `*`, and comparison operators will call it implicitly. TypeScript models the return type of explicit calls like `x.valueOf()` but does not automatically widen `x` to `number` in a type-level sense — `let n: number = myObj` still errors. The coercion is invisible in the type system but very real at runtime.

11. **`bigint` and `number` are mutually exclusive — explicit conversion is required.** TypeScript treats `bigint` and `number` as incompatible types; there is no implicit promotion between them. To convert: use `BigInt(n)` (number → bigint) or `Number(b)` (bigint → number, potentially losing precision for values beyond `Number.MAX_SAFE_INTEGER`). Arithmetic between the two types is a compile-time error.

    ```typescript
    const big: bigint = 100n;
    const num: number = 5;

    big + num;              // error TS2365: Operator '+' cannot be applied to 'bigint' and 'number'
    big + BigInt(num);      // OK — 105n
    Number(big) + num;      // OK — 105 (but lossy for large BigInts)

    const id: bigint = BigInt("9007199254740993"); // > Number.MAX_SAFE_INTEGER
    Number(id) === 9007199254740993;               // false — precision lost
    ```

12. **`as const` vs. explicit annotation — they compose differently.** `as const` keeps the inferred type; an explicit annotation widens it. For object literals used as lookup tables or discriminated union payloads, `as const` is usually the right choice. Use `satisfies T` together with `as const` to get both validation and literal narrowing.

    ```typescript
    const ACTIONS = {
      increment: "INCREMENT",
      decrement: "DECREMENT",
    } as const satisfies Record<string, string>;
    // type: { readonly increment: "INCREMENT"; readonly decrement: "DECREMENT" }
    // — narrowed to literals AND validated as Record<string, string>
    ```

## 6. Examples

### Example A — Explicit runtime conversions

```typescript
// String → number
const raw = "42.7";
const n1 = Number(raw);           // 42.7  (float)
const n2 = parseInt(raw, 10);     // 42    (truncates — always pass radix)
const n3 = parseFloat(raw);       // 42.7

// Failure cases the type system cannot see
Number("abc");                     // NaN — typed as `number`, value is invalid
parseInt("", 10);                  // NaN — not a RangeError, not an exception
Number(null);                      // 0
Number(undefined);                 // NaN
Number(true);                      // 1

// number → string
const s1 = String(42);            // "42"
const s2 = (42).toString(16);     // "2a" — hex

// Explicit boolean conversion (prefer this over !! in new code)
const b = Boolean("");            // false
const b2 = Boolean(0);            // false
const b3 = Boolean([]);           // true — empty array is truthy!

// Safe numeric parsing with validation
function parsePositiveInt(s: string): number {
  const n = parseInt(s, 10);
  if (!Number.isInteger(n) || n <= 0) throw new RangeError(`Not a positive integer: "${s}"`);
  return n;
}

// Shorthand coercive operators — idiomatic but implicit
const x1 = +"42";         // 42      (unary + coerces to number — same as Number())
const x2 = +true;         // 1
const x3 = +"";           // 0       (not NaN — empty string → 0)
const x4 = !!0;           // false   (double negation → boolean)
const x5 = !!"hello";     // true
const x6 = `${42}`;       // "42"    (template literal coerces via toString/toPrimitive)
const x7 = `${null}`;     // "null"  — explicit awareness required for nullable values

// TypeScript types all shorthand results correctly:
//   +expr → number, !!expr → boolean, `${expr}` → string
// But the same runtime-validity caveat applies: +untrustedInput may be NaN.
```

### Example B — Type alias transparency vs. branded types

```typescript
// ❌ Aliases provide no safety — they are transparent synonyms
type UserId  = string;
type OrderId = string;

function getUser(id: UserId): { name: string } { return { name: "Alice" }; }

const orderId: OrderId = "order-123";
getUser(orderId); // compiles — OrderId IS string IS UserId at the type level

// ✅ Branded types are nominally distinct
declare const _brand: unique symbol;
type Brand<T, B extends string> = T & { readonly [_brand]: B };

type UserId2  = Brand<string, "UserId">;
type OrderId2 = Brand<string, "OrderId">;

const mkUserId  = (s: string): UserId2  => s as UserId2;
const mkOrderId = (s: string): OrderId2 => s as OrderId2;

function getUser2(id: UserId2): { name: string } { return { name: "Alice" }; }

getUser2(mkUserId("user-1"));    // OK
getUser2(mkOrderId("order-1"));  // error: OrderId2 is not assignable to UserId2
```

### Example C — valueOf and Symbol.toPrimitive for custom primitive coercion

```typescript
class Celsius {
  constructor(readonly value: number) {}

  // Called by JS arithmetic operators implicitly
  valueOf(): number {
    return this.value;
  }

  // Fine-grained control per hint: "number", "string", "default"
  [Symbol.toPrimitive](hint: "number" | "string" | "default"): number | string {
    if (hint === "string") return `${this.value}°C`;
    return this.value;
  }
}

const temp = new Celsius(100);

// Runtime: valueOf() fires — result is 100 + 32 = 132 (a number)
// TypeScript types the + expression as `number` because valueOf returns number
const shifted = temp + 32;   // 132
console.log(`${temp}`);      // "100°C" — Symbol.toPrimitive("string")

// But the static type of `temp` is still Celsius, not number:
const n: number = temp;      // error: Type 'Celsius' is not assignable to type 'number'
const m: number = temp.valueOf(); // OK — explicit call
```

### Example D — Generic "convertible to" interface (Rust's Into<T> analogue)

```typescript
// TypeScript has no built-in Into<T> trait, but you can express the pattern:
interface IntoString {
  toString(): string;
}

function renderLabel(value: IntoString): string {
  return value.toString();
}

renderLabel(42);           // OK — number has toString()
renderLabel(new Date());   // OK — Date has toString()
renderLabel({ toString: () => "custom" }); // OK — structural match

// For domain conversions, use explicit converter interfaces:
interface ToJson {
  toJSON(): unknown;
}

function serialize<T extends ToJson>(value: T): string {
  return JSON.stringify(value.toJSON());
}
```

### Example E — Fallible conversion pattern (`TryFrom` / `TryInto` analogue)

TypeScript has no built-in `TryFrom`/`TryInto` traits, but the pattern is expressed via functions that return a discriminated union or a `Result`-like type. This is the principled alternative to asserting with `as` at validation boundaries.

```typescript
// A minimal Result type — or use a library like neverthrow / oxide.ts
type Result<T, E> = { ok: true; value: T } | { ok: false; error: E };

// Domain type with a validated constructor
class Percentage {
  private constructor(readonly value: number) {}

  static tryFrom(raw: number): Result<Percentage, string> {
    if (!Number.isFinite(raw) || raw < 0 || raw > 100) {
      return { ok: false, error: `${raw} is not a valid percentage (0–100)` };
    }
    return { ok: true, value: new Percentage(raw) };
  }
}

const r1 = Percentage.tryFrom(85);
if (r1.ok) {
  console.log(r1.value.value); // 85 — type narrowed to Percentage
} else {
  console.error(r1.error);
}

const r2 = Percentage.tryFrom(120);
// r2.ok === false → r2.error === "120 is not a valid percentage (0–100)"
```

Contrast with the `as` escape hatch — the `tryFrom` pattern forces callers to handle the failure case and avoids lying to the type system about values that may not satisfy domain invariants.

### Example F — Structural "convertibility" interfaces (`SupportsFloat` analogue)

Python's `SupportsFloat` and `SupportsInt` protocols let generic code accept *any type that can be converted*, rather than requiring the concrete type. TypeScript achieves the same effect through structural interfaces:

```typescript
// Mirrors Python's SupportsFloat / Rust's Into<f64>
interface SupportsFloat {
  valueOf(): number;
}

interface SupportsString {
  toString(): string;
}

// Generic function that accepts any float-compatible value
function normalize(values: SupportsFloat[]): number[] {
  const nums = values.map(v => v.valueOf());
  const lo = Math.min(...nums);
  const hi = Math.max(...nums);
  const span = hi - lo;
  if (span === 0) return nums.map(() => 0);
  return nums.map(n => (n - lo) / span);
}

class Temperature {
  constructor(private readonly celsius: number) {}
  valueOf(): number { return this.celsius; }
}

normalize([1, 2.5, 3]);                           // OK — number has valueOf()
normalize([new Temperature(0), new Temperature(100)]); // OK — structural match
// normalize(["a", "b"]);                          // error — string.valueOf() returns string

// For domain-specific convertibility, name the interface after the contract:
interface Serializable {
  toJSON(): unknown;
}

function toJsonString<T extends Serializable>(value: T): string {
  return JSON.stringify(value.toJSON());
}
```

This mirrors the `SupportsFloat` / `SupportsInt` pattern from Python's `typing` module and Rust's `AsRef<T>` trait — write the bound once on the interface, accept anything that satisfies it structurally.

## 7. When to Use

- **`satisfies`** — Validate shape without widening at definition sites
- **`as const`** — Preserve literal types from inline values
- **Type predicates** (`x is T`) — Narrow at runtime boundaries with explicit checks
- **Assertion functions** (`asserts`) — Validate preconditions and eliminate nullables
- **`as T`** — When you control both sides and know the cast is safe (e.g., narrowing `any`/`unknown`)
- **Explicit conversions** (`Number()`, `String()`, `Boolean()`) — Convert runtime values from external sources
- **Branded types** — Enforce domain boundaries for primitives

```typescript
// ✅ satisfies: validate config without widening
const config = {
  apiUrl: "https://api.example.com",
  timeout: 5000,
} satisfies { apiUrl: string; timeout: number };
// type: { readonly apiUrl: "https://api.example.com"; readonly timeout: 5000 }

// ✅ as const: freeze literal types
const STATUS_CODES = { OK: 200, NotFound: 404 } as const;
// type: { readonly OK: 200; readonly NotFound: 404 }

// ✅ type predicate: narrow JSON response
function isUser(obj: unknown): obj is { id: string; name: string } {
  return typeof obj === "object" && obj !== null && "id" in obj && "name" in obj;
}
const data: unknown = JSON.parse(response.body);
if (isUser(data)) {
  console.log(data.name); // safe
}

// ✅ assertion function: eliminate nullable
function assertString(s: string | null): asserts s is string {
  if (s == null) throw new Error("string required");
}
assertString(maybeStr);
maybeStr.toUpperCase(); // safe
```

## 7. When NOT to Use

- **`as T`** — Never to bypass type checks without runtime validation at API/JSON boundaries
- **`as unknown as T`** — Avoid unless at genuine untyped boundaries (FFI, external APIs)
- **Type aliases** — Never for domain safety between similarly-typed values
- **`any`** — Never as a conversion boundary; use `unknown` instead
- **Shorthand coercions** (`+"str"`, `!!`, `${}`) — Avoid with untrusted or complex inputs

```typescript
// ❌ as to skip validation at boundary
const data: unknown = JSON.parse(request.body);
const user = data as { name: string };
user.name.toUpperCase(); // crash if data is not an object

// ❌ double assertion without comment or justification
const raw: unknown = fetchData();
const user = raw as unknown as User; // no runtime check

// ❌ type alias for domain separation
type Seconds = number;
type Minutes = number;
const s: Seconds = 60;
const m: Minutes = s; // compiles but semantically wrong

// ❌ any instead of unknown
const payload: any = fetchJson();
payload.uncheckedProp; // no type safety at all
```

## 8. Antipatterns

### Antipatterns When Using This Technique

- **Blind `as` casts on untrusted data**

```typescript
// ❌ no runtime validation
const json: unknown = JSON.parse(input);
const user = json as { name: string };
user.name.toUpperCase(); // crashes if name is missing
```

- **Using `as` instead of proper narrowing**

```typescript
// ❌ assertion instead of guard
function handle(x: string | number) {
  const s = x as string;
  s.toUpperCase(); // crashes if x was number
}

// ✅ proper narrowing
function handle(x: string | number) {
  if (typeof x === "string") {
    x.toUpperCase(); // safe
  }
}
```

- **Type aliases for domain safety**

```typescript
// ❌ provides no safety
type Miles = number;
type Kilometers = number;
const d: Miles = 10;
const k: Kilometers = d; // should error
```

- **Shorthand coercions on untrusted input**

```typescript
// ❌ loses error information
const age = +(query.age || "0"); // invalid input → 0 silently

// ✅ explicit validation
const ageStr = query.age;
const age = ageStr ? parseInt(ageStr, 10) : 0;
if (isNaN(age) || age <= 0) throw new Error("invalid age");
```

### Antipatterns Where This Technique Fixes Other Approaches

- **`any` pollution**

```typescript
// ❌ any everywhere
const api = fetch("/api").then(r => r.json()) as any;
const name = api.data.user.name; // if structure changes, no warning

// ✅ unknown boundary + predicate
type User = { name: string };
function isUser(o: unknown): o is User {
  return typeof o === "object" && o !== null && "name" in o;
}
const api = await fetchJson();
if (isUser(api.data.user)) {
  console.log(api.data.user.name); // safe
}
```

- **Excessive type annotations**

```typescript
// ❌ verbose manual annotation
const COLORS = {
  primary: "red",
  secondary: "blue",
} as { primary: string; secondary: string };

// ✅ as const
const COLORS = {
  primary: "red",
  secondary: "blue",
} as const;
```

- **Premature abstraction with type aliases**

```typescript
// ❌ type alias requires runtime wrapper
type Age = number;
function createAge(n: number): Age { return n; }

// ✅ branded type enforces explicit boundary
type Age = number & { readonly _brand: "Age" };
function createAge(n: number): Age { return n as Age; }
const invalid: Age = 10; // error: not branded
```

- **Missing runtime checks on primitives**

```typescript
// ❌ direct conversion, no validation
const id = parseInt(request.query.id, 10); // can be NaN

// ✅ Result-like fallible conversion
function tryParseId(s: string): { ok: true; value: number } | { ok: false } {
  const n = parseInt(s, 10);
  return Number.isInteger(n) && n > 0 ? { ok: true, value: n } : { ok: false };
}
```

## 9. Common Compiler Errors and How to Read Them

### `Conversion of type 'X' to type 'Y' may be a mistake`

```
error TS2352: Conversion of type 'string' to type 'number' may be a mistake
because neither type sufficiently overlaps with the other.
If this was intentional, convert the expression to 'unknown' first.
```

**Meaning:** You wrote `x as T` where `x` and `T` have no structural overlap. TypeScript requires at least partial overlap for a direct `as` assertion.

**How to fix:** If you genuinely need the cast (e.g., FFI boundary), use the double assertion: `x as unknown as T`. If you don't need a cast, fix the type mismatch.

### `Type 'X' is not assignable to type 'Y'`

```
error TS2322: Type 'string' is not assignable to type 'number'.
```

**Meaning:** You provided a value whose static type does not match the expected type, and no implicit conversion exists. Unlike JavaScript at runtime, TypeScript never implicitly converts between types.

**How to fix:** Use an explicit runtime conversion (`Number(x)`, `String(x)`, `parseInt(x, 10)`, etc.) or fix the source/target type.

### `Type 'X' is not assignable to type 'Y'. Type 'string' is not assignable to type '"literal"'`

```
error TS2322: Type 'string' is not assignable to type '"red" | "green" | "blue"'.
```

**Meaning:** The value was widened to `string` (e.g., via `let` or by receiving it from a function) and can no longer satisfy a literal union. TypeScript widened the type and lost the literal information.

**How to fix:** Use `as const` to preserve literal types, or use `satisfies` to validate the shape without widening: `const color = "red" as const` or annotate the variable directly.

### `Property 'x' does not exist on type 'never'`

Often appears after `as` narrows a union to `never` through exhaustive narrowing. Indicates the code has dead branches or the assertion was wrong about which variant remains.

## 10. Use-Case Cross-References

- [-> UC-05](../usecases/UC05-structural-contracts.md) Use `satisfies` to validate structural contracts without losing literal precision at definition sites
- [-> UC-16](../usecases/UC16-nullability.md) Use assertion functions and non-null assertions to handle nullable values safely at checked boundaries
- [-> UC-01](../usecases/UC01-invalid-states.md) Branded types enforce that raw values pass through a validation/conversion boundary before entering the domain
- [-> UC-02](../usecases/UC02-domain-modeling.md) Runtime conversions (`Number()`, `parseInt()`) combined with branded wrapping form the explicit conversion boundary between external data and domain types

## Source Anchors

- [TypeScript Handbook — Type Assertions](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions)
- [TypeScript Handbook — Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [TypeScript 4.9 Release Notes — `satisfies` operator](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html#the-satisfies-operator)
- [MDN — `Number()` constructor](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/Number)
- [MDN — `Symbol.toPrimitive`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/toPrimitive)
- [TypeScript Deep Dive — Type Assertion](https://basarat.gitbook.io/typescript/type-system/type-assertion)
