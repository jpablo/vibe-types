# Gradual Typing & `any`

> **Since:** TypeScript 1.0; `unknown` since TypeScript 3.0; `--strict` since TypeScript 2.3; `satisfies` since TypeScript 4.9

> **Status:** Requires `--strict` (or individual flags) to maximize enforcement

## 1. What It Is

TypeScript is a **gradually typed** language: every JavaScript value is valid TypeScript, and the type system can be engaged at whatever granularity you choose. At one extreme, `any` turns off all type checking for a value — it is assignable to every type and every type is assignable to it, making it a hole in the type system. At the other extreme, `--strict` enables a bundle of flags (`--strictNullChecks`, `--strictFunctionTypes`, `--strictBindCallApply`, `--strictPropertyInitialization`, `--noImplicitAny`, `--noImplicitThis`, `--useUnknownInCatchVariables`) that make the type system as sound as TypeScript's design allows. The `unknown` type (TypeScript 3.0) is the type-safe counterpart to `any`: it accepts all values on input but requires narrowing before any operation. The `@ts-ignore` directive suppresses the next line's errors; `@ts-expect-error` suppresses and also errors if the line is *not* an error (useful for tests). Individual files can opt out with `// @ts-nocheck`.

**Type inference** reduces annotation burden: TypeScript infers types for local variables, array literals, object literals, and function return types wherever possible. For plain JavaScript files, `// @ts-check` at the top of a `.js` file enables the checker via JSDoc annotations, enabling gradual migration without converting to `.ts`.

**Declaration files** (`.d.ts`) add types to untyped libraries — analogous to Python's `.pyi` stub files. Publishing a package with a `types` field in `package.json` or a bundled `.d.ts` makes it fully typed for consumers; the `@types/*` namespace on npm provides community-maintained stubs for untyped packages.

## 2. What Constraint It Lets You Express

**`unknown` forces you to prove the shape of a value before using it; `any` disables all proofs; `--strict` makes unannotated code default to the safest interpretation rather than silently guessing.**

- A function accepting `unknown` cannot call methods on it without a type guard — the compiler rejects `value.trim()` until `typeof value === "string"` is confirmed.
- `--noImplicitAny` turns every implicit `any` (unannotated parameter, unresolvable inference) into a compile error, forcing explicit annotations at the boundary.
- `--strictNullChecks` makes `null` and `undefined` non-assignable to non-nullable types, catching the billion-dollar mistake.
- Per-file `@ts-ignore` / `@ts-expect-error` allow surgical suppressions without disabling the whole project.

## 3. Beginner Mental Model

Think of TypeScript's type system as a **dimmer switch**, not an on/off toggle. Plain JavaScript has no checking. Adding a `.ts` extension and a `tsconfig.json` turns the dial partway up. Enabling `--strict` turns it all the way up. You can set the dial anywhere in between.

`any` is a **hall pass** — it lets a value skip all type checks. `unknown` is the **responsible version**: it accepts any value, but you must prove its shape before doing anything with it. The goal of gradual adoption is to replace `any` with precise types (or at minimum `unknown`) over time, shrinking the unchecked surface.

```
No types         Partial types         --strict
    |<------ JS ------->|<----- TS ------>|
  any everywhere     mix of any         no implicit any
  no checking        and typed code     unknown required
```

## 4. Minimal Snippet

```typescript
// --- any: no checks at all ---
let danger: any = fetchSomething();
danger.foo.bar.baz(); // OK at compile time — may explode at runtime

// --- unknown: must narrow before use ---
let safe: unknown = fetchSomething();
// safe.trim(); // error — Object is of type 'unknown'

if (typeof safe === "string") {
  safe.trim(); // OK — narrowed to string
}

// --- strictNullChecks: null is not assignable to string ---
// (requires --strictNullChecks or --strict)
function greet(name: string): string {
  return `Hello, ${name.toUpperCase()}`; // OK — name cannot be null
}
// greet(null); // error — Argument of type 'null' is not assignable to parameter of type 'string'

// --- noImplicitAny: unannotated parameters must be explicit ---
// (requires --noImplicitAny or --strict)
// function process(x) { return x; } // error — x has implicit 'any' type
function process(x: unknown): unknown { return x; } // OK — explicit

// --- @ts-expect-error: document a known type violation ---
// @ts-expect-error: legacy API returns untyped object
const raw = legacyApi() as { id: number };

// --- unknown in catch (TypeScript 4.0 useUnknownInCatchVariables, default in --strict) ---
try {
  JSON.parse("{bad json}");
} catch (e) {
  // e is unknown — must narrow before use
  const message = e instanceof Error ? e.message : String(e); // OK
}
```

## 5. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Null Safety** [-> T13](T13-null-safety.md) | `--strictNullChecks` is the primary null-safety mechanism; it is part of `--strict` and makes `null`/`undefined` distinct types rather than assignable to everything. |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | `unknown` is only useful when paired with narrowing; `typeof`, `instanceof`, and custom type guards are the tools that unlock `unknown` values for actual use. |
| **Conversions & Coercions** [-> T18](T18-conversions-coercions.md) | `as any` followed by `as TargetType` (the double-cast "escape hatch") is the standard way to force a type cast that the compiler would otherwise reject; this erases all safety. |
| **Record Types** [-> T31](T31-record-types.md) | `Record<string, unknown>` is the safe alternative to `Record<string, any>` for dynamic key/value shapes; values must be narrowed before use. |
| **Type Aliases** [-> T23](T23-type-aliases.md) | Type aliases composed with `any` propagate looseness; replacing `any` with a precise type in the alias tightens the whole chain. |

## 6. Gotchas and Limitations

1. **`any` is contagious** — a single `any` value in a computation poisons its result; `(anyValue as string[]).map(x => x.toUpperCase())` type-checks but `x` is still `any` inside the callback if inference is imprecise.
2. **`unknown` from JSON.parse** — `JSON.parse` returns `any`, not `unknown`; in a strict codebase, immediately cast to `unknown` and narrow with a validator library (Zod, io-ts) before use.
3. **`--strict` is not retroactively safe** — enabling `--strict` on an existing codebase often reveals hundreds of errors; incremental adoption using `// @ts-ignore` or per-directory `tsconfig.json` with `"strict": true` is the common migration path.
4. **`@ts-ignore` vs `@ts-expect-error`** — prefer `@ts-expect-error`; it fails if the suppression is no longer necessary (e.g., after a dependency upgrade fixes the type), preventing stale suppressions from silently hiding real errors.
5. **Type inference fills gaps silently** — TypeScript infers `any` for some unresolvable positions without an error unless `--noImplicitAny` is on; turning on `--strict` after the fact can surface many of these.
6. **`unknown[]` for rest parameters** — variadic rest parameters typed as `...args: any[]` accept anything; typing them as `...args: unknown[]` is stricter but requires callers to narrow before use, which may be impractical for generic adapters.
7. **`object` is not `unknown`** — `object` excludes primitives (`string`, `number`, `boolean`, `symbol`, `bigint`) but still allows arbitrary property access on the type level (with `--noUncheckedIndexedAccess`, less so). `unknown` is the real "accept everything, check before use" type.

   ```typescript
   function f(x: object): void {
     // x.foo; // error — Property 'foo' does not exist on type 'object'
   }
   function g(x: unknown): void {
     // x.foo; // error — Object is of type 'unknown' — same guard needed
   }
   // Both require narrowing; neither is a free pass, but object rejects primitives.
   f(42);       // error — 42 is not assignable to object
   g(42);       // OK   — unknown accepts primitives
   ```

8. **Inferring literal vs widened types** — TypeScript widens `let x = "hello"` to `string`, not `"hello"`. Use `as const` or an explicit literal annotation to preserve narrowness: `const x = "hello" as const` infers `"hello"`.

9. **`satisfies` preserves inference while checking shape (TS 4.9+)** — `value satisfies T` checks that `value` matches `T` without widening the variable to `T`, so excess-property and narrowness information is retained. Useful for configuring objects where you want both precise type inference and a shape check.

   ```typescript
   const palette = {
     red: [255, 0, 0],
     green: "#00ff00",
   } satisfies Record<string, string | number[]>;
   // palette.red is inferred as number[], not string | number[]
   // palette.green is inferred as string, not string | number[]
   ```

## 7. Inspecting Inferred Types

TypeScript has no `reveal_type()` built-in, but several alternatives exist:

- **IDE hover** — hovering a variable in VS Code / WebStorm shows the inferred type in a tooltip; this is the primary development-time tool.
- **`satisfies never` trick** — assigning to `never` produces an error whose message includes the inferred type:

  ```typescript
  const x = [1, 2, 3];
  // @ts-expect-error
  const _: never = x; // Error: Type 'number[]' is not assignable to type 'never'
  //                               ^^^^^^^^ — this tells you the inferred type
  ```

- **`tsc --noEmit`** — running the compiler with `--noEmit` shows all type errors without producing output; combine with `@ts-expect-error` annotations to test that a specific expression has or does not have a particular type.

## 8. Example A — Gradual Adoption Strategy: Typing a Module Boundary

```typescript
// --- Phase 1: Untyped / implicit any (plain JS or no annotations) ---

function parseConfig(path: string) {    // return type inferred as any (from JSON.parse)
  const fs = require("fs");
  return JSON.parse(fs.readFileSync(path, "utf-8"));
}

function getDbUrl(config: any) {         // explicit any — caller opted out
  return config.database.url;            // any — no checking
}

// No errors in non-strict mode, no safety. A typo in "database" is a runtime crash.


// --- Phase 2: Type the public API boundary with partial any ---

interface AppConfig {
  database: { url: string; poolSize: number };
  debug: boolean;
}

function parseConfig2(path: string): AppConfig {
  const fs = require("fs");
  // JSON.parse returns any — cast is unchecked but narrows outward interface
  return JSON.parse(fs.readFileSync(path, "utf-8")) as AppConfig;
}

function getDbUrl2(config: AppConfig): string {
  return config.database.url;            // OK — string, fully checked
}

// The checker now catches callers passing wrong shapes to getDbUrl2.
// JSON.parse still returns any internally — the cast is the trust boundary.


// --- Phase 3: Replace the cast with a runtime validator ---
import { z } from "zod";

const AppConfigSchema = z.object({
  database: z.object({ url: z.string(), poolSize: z.number() }),
  debug: z.boolean(),
});
type AppConfig3 = z.infer<typeof AppConfigSchema>;   // derived, no duplication

function parseConfig3(path: string): AppConfig3 {
  const fs = require("fs");
  const raw: unknown = JSON.parse(fs.readFileSync(path, "utf-8"));
  return AppConfigSchema.parse(raw);     // throws at runtime if shape is wrong
}

// Now both compile-time and runtime are safe.
// The checker enforces AppConfig3 shape; Zod validates at the JSON boundary.
```

Each phase adds more type information. The boundary between typed and untyped code moves inward toward external I/O.

## 9. Example B — `--strict` Catching Implicit Any

```typescript
// tsconfig.json: { "compilerOptions": { "strict": true } }

// --- Unannotated parameter → implicit any → error under noImplicitAny ---
// function add(a, b) { return a + b; }
// error TS7006: Parameter 'a' implicitly has an 'any' type.

function add(a: number, b: number): number {  // OK
  return a + b;
}

// --- JSON.parse returning any → Returning any from typed function ---
function loadName(path: string): string {
  const fs = require("fs");
  const data = JSON.parse(fs.readFileSync(path, "utf-8")); // data: any
  return data.name;
  // Not an error by default — TS does not warn on 'any' return from typed fn
  // Use eslint @typescript-eslint/no-unsafe-return for this protection
}

// --- useUnknownInCatchVariables (TS 4.0, on by default under --strict) ---
function loadNameSafe(path: string): string {
  try {
    const fs = require("fs");
    const raw: unknown = JSON.parse(fs.readFileSync(path, "utf-8"));
    if (
      typeof raw === "object" && raw !== null &&
      "name" in raw && typeof (raw as { name: unknown }).name === "string"
    ) {
      return (raw as { name: string }).name;  // OK — narrowed
    }
    throw new Error("Missing name field");
  } catch (e) {
    // e is unknown under --strict / useUnknownInCatchVariables
    throw new Error(`Failed to load: ${e instanceof Error ? e.message : String(e)}`);
  }
}

// --- @ts-check in plain JS files (gradual migration) ---
// Place this at the top of a .js file to enable type checking via JSDoc:
//
// // @ts-check
// /** @type {number} */
// let count = 0;
// count = "hello"; // error in JS file — @ts-check caught it
```

## 10. Common Type-Checker Errors and How to Read Them

### `error TS7006: Parameter 'x' implicitly has an 'any' type`

Emitted under `--noImplicitAny` (part of `--strict`). A function parameter has no annotation and TypeScript cannot infer a type. Add an explicit annotation: `x: string`, `x: unknown`, or the appropriate type.

### `error TS2345: Argument of type 'null' is not assignable to parameter of type 'string'`

Emitted under `--strictNullChecks`. A nullable value (possibly `null` or `undefined`) is passed where a non-nullable type is expected. Either widen the parameter type to `string | null` or narrow the argument with a null check.

### `error TS18046: 'e' is of type 'unknown'`

Emitted under `--useUnknownInCatchVariables` (default in `--strict` since TS 4.4). The catch variable `e` is `unknown`; you must narrow it before accessing properties. Use `e instanceof Error` or `typeof e === "string"`.

### `error TS2352: Conversion of type 'X' to type 'Y' may be a mistake`

Emitted when using `as` for a cast TypeScript considers unsafe (neither type is assignable to the other). Use the double-cast `value as unknown as TargetType` to force it — but this is a signal to add a runtime validator instead.

### `error TS2578: Unused '@ts-expect-error' directive`

The suppression is no longer needed — the code no longer has an error on that line. Remove the directive, or investigate whether a dependency upgrade silently changed the types.

### `error TS2339: Property 'foo' does not exist on type 'unknown'`

You accessed a property on an `unknown` value without narrowing first. Add a type guard (`typeof`, `instanceof`, or a custom predicate) before the access.

## 11. Use-Case Cross-References

- [-> UC-04](../usecases/UC04-generic-constraints.md) Use bounds instead of `any` to write generic code that is still type-safe
- [-> UC-16](../usecases/UC16-nullability.md) Enforce non-nullability at the type level via `--strictNullChecks`

## Source Anchors

- [TypeScript Handbook — The `any` type](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#any)
- [TypeScript Handbook — `unknown`](https://www.typescriptlang.org/docs/handbook/2/functions.html#unknown)
- [TypeScript `--strict` flag reference](https://www.typescriptlang.org/tsconfig#strict)
- [TypeScript 4.9 release notes — `satisfies` operator](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html#the-satisfies-operator)
- [TypeScript declaration files guide](https://www.typescriptlang.org/docs/handbook/declaration-files/introduction.html)
- [TS Config reference — `noImplicitAny`](https://www.typescriptlang.org/tsconfig#noImplicitAny)
