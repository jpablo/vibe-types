# Type-Safe Error Channels

## The Constraint

Callers cannot ignore error cases at compile time. An operation that may fail must expose that failure in its return type; swallowing the error or forgetting to handle it is a type error, not a runtime surprise.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Union types** | Encode `Result<T, E>` as a discriminated union of success and failure variants | [-> T02](../catalog/T02-union-intersection.md) |
| **Effect tracking** | `Promise` encodes async effect; the resolved type can carry errors via `TaskEither` | [-> T12](../catalog/T12-effect-tracking.md) |
| **Null safety** | `T \| null` for simple optionality where no error detail is needed | [-> T13](../catalog/T13-null-safety.md) |
| **fp-ts Either** | Composable, typed error channel — chainable without nested conditionals | [-> T54](../catalog/T54-functor-applicative-monad.md) |
| **Type narrowing** | Refine a `Result` union to its success or failure variant inside a branch | [-> T14](../catalog/T14-type-narrowing.md) |

## Patterns

### Pattern A — `Result<T, E>` discriminated union

A `Result` is a union of two variants. The discriminant field `ok` lets TypeScript narrow to `value` or `error` inside each branch. Callers who want the value must handle the failure case — there is no way to access `value` without first checking `ok`.

```typescript
type Result<T, E> =
  | { readonly ok: true;  readonly value: T }
  | { readonly ok: false; readonly error: E };

// Smart constructors (no unsafe casts at call sites):
const ok  = <T>(value: T): Result<T, never> => ({ ok: true,  value });
const err = <E>(error: E): Result<never, E> => ({ ok: false, error });

// Domain errors as a discriminated union so callers can handle each case:
type DbError =
  | { kind: "NotFound";    id: string }
  | { kind: "Unauthorized" }
  | { kind: "Timeout";     ms: number };

function findUser(id: string): Result<{ id: string; name: string }, DbError> {
  if (id === "") return err({ kind: "NotFound", id });
  return ok({ id, name: "Alice" });
}

const result = findUser("u1");

if (result.ok) {
  console.log(result.value.name); // OK — narrowed to success variant
} else {
  // result.error is DbError here; each case has its own fields
  switch (result.error.kind) {
    case "NotFound":     console.error(`Not found: ${result.error.id}`); break;
    case "Unauthorized": console.error("Unauthorized"); break;
    case "Timeout":      console.error(`Timed out after ${result.error.ms}ms`); break;
    default:             assertNever(result.error); // Adding a new DbError variant → compile error here
  }
}

// Accessing value without checking is a compile error:
result.value; // error: Property 'value' does not exist on type '{ ok: false; error: DbError }'
```

### Pattern B — `T | null` for simple optionality

When a caller only needs to know whether a value is present — and the absence carries no diagnostic information — `T | null` is the simplest typed error channel. `--strictNullChecks` forces the caller to handle `null` before using the value.

```typescript
function findById(id: string, store: Map<string, string>): string | null {
  return store.get(id) ?? null;
}

const store = new Map([["a", "Alice"]]);
const name = findById("a", store);

// Caller must narrow before using:
if (name !== null) {
  console.log(name.toUpperCase()); // OK
}

name.toUpperCase(); // error: Object is possibly 'null'

// Optional chaining composes well with T | null:
const upper = name?.toUpperCase() ?? "(not found)";
```

### Pattern C — fp-ts `Either<E, A>` for composable error chains

`Either` from fp-ts lets you chain multiple fallible operations using `pipe` and `chain` without nesting `if/else` blocks. Each step in the pipeline short-circuits on `Left` (error) and passes the unwrapped value into the next step on `Right` (success).

```typescript
import { pipe } from "fp-ts/function";
import * as E from "fp-ts/Either";

type ParseError = { tag: "ParseError"; input: string };
type NotFound   = { tag: "NotFound";   id: number };
type AppError   = ParseError | NotFound;

function parseId(raw: string): E.Either<ParseError, number> {
  const n = parseInt(raw, 10);
  return isNaN(n)
    ? E.left({ tag: "ParseError", input: raw })
    : E.right(n);
}

const userDb = new Map([[1, { id: 1, name: "Alice" }]]);

function lookupUser(id: number): E.Either<NotFound, { id: number; name: string }> {
  const user = userDb.get(id);
  return user ? E.right(user) : E.left({ tag: "NotFound", id });
}

function greet(user: { name: string }): string {
  return `Hello, ${user.name}!`;
}

// Compose: parse → lookup → transform — each step typed; error short-circuits:
const greeting = pipe(
  parseId("1"),
  E.chain(lookupUser),
  E.map(greet),
);
// Type: E.Either<AppError, string>

if (E.isRight(greeting)) {
  console.log(greeting.right); // "Hello, Alice!"
} else {
  const error = greeting.left; // AppError — exhaustively typed
  switch (error.tag) {
    case "ParseError": console.error(`Cannot parse: ${error.input}`); break;
    case "NotFound":   console.error(`No user with id ${error.id}`);   break;
  }
}
```

### Pattern D — `never` for throw utilities and exhaustiveness guards

`never` is TypeScript's bottom type: a function that returns `never` never returns normally. This serves two purposes that other typed languages call `NoReturn`: (1) utility helpers that always throw, and (2) exhaustiveness guards that turn missing branches into compile errors.

```typescript
// A function returning never tells the compiler: control flow stops here.
function assertNever(x: never): never {
  throw new Error(`Unhandled case: ${JSON.stringify(x)}`);
}

function fail(message: string): never {
  throw new Error(message);
}

// fail() narrows downstream types — the ?? operand resolves to string, not string | never:
function getConfig(key: string, env: Record<string, string>): string {
  return env[key] ?? fail(`Missing required config key: ${key}`);
}

// assertNever() as the default branch turns unhandled union variants into compile errors:
type ApiError =
  | { code: "NOT_FOUND";    resource: string }
  | { code: "UNAUTHORIZED" }
  | { code: "RATE_LIMITED"; retryAfterMs: number };

function describeError(e: ApiError): string {
  switch (e.code) {
    case "NOT_FOUND":    return `${e.resource} not found`;
    case "UNAUTHORIZED": return "access denied";
    case "RATE_LIMITED": return `retry in ${e.retryAfterMs}ms`;
    default:             return assertNever(e);
    // If a new variant is added to ApiError without updating this switch,
    // the compiler reports: Argument of type 'NewVariant' is not assignable to parameter of type 'never'.
  }
}

// The same pattern works with if-else chains:
function handleResult(r: Result<string, ApiError>): string {
  if (!r.ok) return describeError(r.error);
  if (r.value === "") return fail("unexpected empty success");
  return r.value;
}
```

`assertNever` from the TypeScript standard library: `import { assertNever } from "node:assert"` is not the same — roll your own as above, or use the one from a utility library. The key is the `never` parameter: if any runtime value reaches it, a variant was not handled.

### Pattern E — Parse, don't validate

Instead of a `validateEmail(raw): boolean` that callers may forget to call, return a `Result<Email, ValidationError>`. Callers who need an `Email` are forced through the parser; an unvalidated `string` is not assignable to `Email`. See [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/).

```typescript
declare const __brand: unique symbol;
type Brand<B>      = { readonly [__brand]: B };
type Branded<T, B> = T & Brand<B>;

type Email = Branded<string, "Email">;

type ValidationError =
  | { kind: "EmptyInput" }
  | { kind: "InvalidFormat"; input: string };

function parseEmail(raw: string): Result<Email, ValidationError> {
  const trimmed = raw.trim().toLowerCase();
  if (trimmed === "") return err({ kind: "EmptyInput" });
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
    return err({ kind: "InvalidFormat", input: raw });
  }
  return ok(trimmed as Email);
}

function sendInvite(to: Email): void {
  console.log(`Sending invite to ${to}`);
}

const result = parseEmail("alice@example.com");
if (result.ok) {
  sendInvite(result.value); // OK — Email, validated once at the boundary
}

sendInvite("alice@example.com"); // error: string is not assignable to Email
```

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Fallible operations | `throw` on failure; callers use `try/catch` with an `any`-typed `catch (e)` — no enforcement | `Result<T, E>` union; callers must unwrap; error type is precise and exhaustively checkable |
| Optional lookup | Return `undefined`; callers use `if (result)` by convention; silent `undefined` dereference common | `T \| null` with `--strictNullChecks`; dereference without null check is a compile error |
| Chained fallible ops | Nested `try/catch` blocks or callback-style with `(err, value)` — no type safety on error shape | fp-ts `Either` with `pipe` and `chain` — each step typed; error union grows automatically |
| Validated values | `isValidEmail(s)` returns `boolean`; caller may pass the raw string anyway | `parseEmail` returns `Result<Email, …>`; `Email` branded type enforces parsing at all call sites |

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| `Result<T, E>` union | Zero deps; typed error; narrowing enforced by the compiler | Callers must explicitly unwrap; no `?`-style propagation |
| `T \| null` | Simplest; idiomatic for lookups | No error detail — caller only knows "absent" |
| fp-ts `Either` | Composable pipelines; error union grows automatically | Requires fp-ts; steeper learning curve |
| `never` helpers (`assertNever`, `fail`) | Exhaustiveness enforced at compile time; cleans up nullable assertions | Just utility functions — not a standalone error strategy |
| Branded types + `Result` | Unvalidated values cannot reach domain functions | Boilerplate; cast at the parse boundary |

## When to Use Which Feature

**`Result<T, E>` union** (Pattern A) is the right default for any operation with a meaningful error. It is zero-dependency, readable, and integrates naturally with TypeScript's narrowing. Use it when error detail matters and the codebase does not already use fp-ts.

**`T | null`** (Pattern B) is appropriate when absence is the only failure mode — lookups, optional configuration, find operations — and callers do not need to know *why* the value is absent.

**fp-ts `Either`** (Pattern C) pays off in pipelines of three or more chained fallible steps. The `pipe` + `chain` pattern eliminates nesting and keeps error types accumulating in a union without manual merging. Adopt it only if the team is comfortable with functional style.

**`never` utilities** (Pattern D) do not replace a Result strategy — they reinforce it. Add `assertNever` as the `default` branch in every discriminated-union switch to make unhandled variants a compile error. Use `fail()` to eliminate `T | undefined` casts in non-null assertions.

**Parse, don't validate** (Pattern E) applies whenever unvalidated primitives must be prevented from flowing into domain functions. Combine it with branded types and `Result` to create a single, trustworthy entry point for each validation rule.

## Source anchors

- [TypeScript Handbook — Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [TypeScript Handbook — `never` type](https://www.typescriptlang.org/docs/handbook/2/functions.html#never)
- [TypeScript Handbook — Discriminated unions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions)
- [fp-ts `Either` documentation](https://gcanti.github.io/fp-ts/modules/Either.ts.html)
- [Parse, don't validate — Alexis King](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)
