# Effect Tracking

> **Since:** TypeScript 1.0 (Promise); fp-ts for full effect types

## 1. What It Is

TypeScript has no native effect system. The language tracks one effect natively: **asynchrony**, via the `Promise<T>` return type and `async`/`await` syntax. Any function that performs I/O asynchronously must declare `Promise<T>` as its return type; the compiler enforces that callers `await` or chain the result. For richer effect tracking — side effects, error effects, environment dependencies, non-determinism — the community uses libraries such as **fp-ts** (which provides `IO<A>`, `Task<A>`, `TaskEither<E, A>`, `ReaderTaskEither<R, E, A>`) and **Effect** (the `Effect<A, E, R>` type). These encode effectful computations as values in the return type, making the effects visible to callers and composable via monadic chaining. The `Result<T, E>` / `Either<E, A>` pattern (also from fp-ts or hand-rolled) is the minimal form of error effect tracking.

## 2. What Constraint It Lets You Express

**Effectful computations are encoded in return types so callers cannot ignore the effect; the compiler enforces that `Promise` values are awaited and that `IO`/`Task`/`Either` values are explicitly run or composed.**

- `async function fetchUser(): Promise<User>` cannot be called as if it returns `User`; forgetting `await` yields `Promise<User>`, which is incompatible with `User`.
- `type Task<A> = () => Promise<A>` defers execution; the type communicates that the computation is lazy and asynchronous.
- `TaskEither<E, A>` signals both asynchrony and the possibility of a typed error, forcing callers to handle both.
- `Effect<A, E, R>` (Effect library) encodes three orthogonal effects: success type `A`, typed error `E`, and required environment/dependencies `R`.

## 3. Minimal Snippet

```typescript
// Native effect tracking: async/await with Promise<T>
async function fetchUser(id: string): Promise<{ name: string }> {
  const response = await fetch(`/users/${id}`);
  return response.json();
}

// Caller must await — ignoring the Promise gives Promise<{name:string}>, not {name:string}
const user = await fetchUser("42"); // OK
// const user2: { name: string } = fetchUser("42"); // error — Promise<...> not assignable to {name:string}

// Minimal hand-rolled Result type for error effects
type Result<T, E> =
  | { ok: true;  value: T }
  | { ok: false; error: E };

async function parseUser(raw: string): Promise<Result<{ name: string }, string>> {
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed.name !== "string") return { ok: false, error: "missing name" };
    return { ok: true, value: parsed };
  } catch {
    return { ok: false, error: "invalid JSON" };
  }
}

// fp-ts style: IO<A> — synchronous side-effectful computation as a value
type IO<A> = () => A;

const readLine: IO<string> = () => "input from console"; // deferred execution
const result: string = readLine(); // explicitly run

// fp-ts TaskEither pattern (abbreviated without library import)
type Task<A> = () => Promise<A>;
type Either<E, A> = { _tag: "Left"; left: E } | { _tag: "Right"; right: A };
type TaskEither<E, A> = Task<Either<E, A>>;

function fetchOrError(url: string): TaskEither<string, Response> {
  return async () => {
    try {
      const r = await fetch(url);
      return { _tag: "Right", right: r };
    } catch (e) {
      return { _tag: "Left", left: String(e) };
    }
  };
}
```

## Beginner Mental Model

Think of `Promise<T>` as a **stamped envelope**. The stamp says "this isn't ready yet — you must `await` it before reading." Every function that touches the envelope must acknowledge the stamp. For errors, think of `Result<T, E>` as a **branching door**: either you walk through the `ok` door (success) or the `error` door — the compiler prevents you from acting as if only one door exists without checking first.

There is no `?` operator like Rust. Instead, TypeScript callers either use a `match`-like `if`/`switch` on the discriminant, or use combinator methods (`.map`, `.andThen`, `.chain`) provided by neverthrow or fp-ts to thread results through a pipeline without nested checks.

Coming from JavaScript: `Promise` already tracks asynchrony at runtime, but nothing prevents you from calling an async function and discarding the result. TypeScript's `Promise<T>` return type makes the async effect visible at compile time. Richer effect tracking (errors, environment) requires library support.

## Example A — Error propagation with Result and combinators

```typescript
import { ok, err, Result } from "neverthrow";

type ParseError = "empty" | "not-a-number" | "out-of-range";

function parsePort(raw: string): Result<number, ParseError> {
  if (!raw) return err("empty");
  const n = Number(raw);
  if (Number.isNaN(n)) return err("not-a-number");
  if (n < 1 || n > 65535) return err("out-of-range");
  return ok(n);
}

function buildUrl(host: string, rawPort: string): Result<string, ParseError> {
  return parsePort(rawPort).map((port) => `${host}:${port}`);
  // .map is only called on Ok — Err passes through untouched
}

const result = buildUrl("localhost", "8080");
if (result.isOk()) {
  console.log("Connecting to", result.value); // "Connecting to localhost:8080"
} else {
  console.error("Bad port:", result.error);   // narrowed to ParseError
}
```

Rust users: `.map` / `.andThen` fill the role of `?` — they thread success values through a pipeline and short-circuit on the first error.

## Example B — Combining async + error effects (TaskEither / Effect)

```typescript
// Using fp-ts TaskEither to stack async + error effects
import * as TE from "fp-ts/TaskEither";
import * as E from "fp-ts/Either";
import { pipe } from "fp-ts/function";

type FetchError = { kind: "network"; message: string } | { kind: "decode"; message: string };

const fetchJson = (url: string): TE.TaskEither<FetchError, unknown> =>
  TE.tryCatch(
    () => fetch(url).then((r) => r.json()),
    (e) => ({ kind: "network", message: String(e) }),
  );

const decodeUser = (raw: unknown): E.Either<FetchError, { name: string }> => {
  if (typeof (raw as any)?.name === "string") return E.right(raw as { name: string });
  return E.left({ kind: "decode", message: "missing name field" });
};

// pipe sequences operations; errors short-circuit the chain
const getUser = (url: string): TE.TaskEither<FetchError, { name: string }> =>
  pipe(fetchJson(url), TE.chainEitherK(decodeUser));

// --- Alternative: Effect library, which stacks A / E / R explicitly ---
import { Effect } from "effect";

interface HttpClient { fetch(url: string): Effect.Effect<unknown, FetchError> }

// Effect<{ name: string }, FetchError, HttpClient>
//   ↑ success      ↑ typed error    ↑ required dependency (injected at the edge)
const getUserEffect = (url: string): Effect.Effect<{ name: string }, FetchError, HttpClient> =>
  Effect.gen(function* () {
    const client = yield* Effect.service<HttpClient>(HttpClient);
    const raw    = yield* client.fetch(url);
    if (typeof (raw as any)?.name !== "string")
      yield* Effect.fail<FetchError>({ kind: "decode", message: "missing name" });
    return raw as { name: string };
  });
```

The `Effect<A, E, R>` type encodes three orthogonal effects in one position. `R` is the environment (dependency injection), `E` is the typed error, and `A` is the success value. This mirrors Lean's `ReaderT`/`ExceptT`/`IO` monad transformer stack, but without manual stacking order decisions.

## Recommended Libraries

| Library | Role | Link |
|---|---|---|
| fp-ts | Full functional effect stack: `IO`, `Task`, `Either`, `TaskEither`, `ReaderTaskEither` | https://gcanti.github.io/fp-ts/ |
| Effect | Modern `Effect<A, E, R>` type with structured concurrency, dependency injection, and streaming | https://effect.website |
| neverthrow | Lightweight `Result<T, E>` type with chaining methods | https://github.com/supermacro/neverthrow |

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Callable Typing** [-> T22](T22-callable-typing.md) | `Task<A> = () => Promise<A>` is a zero-argument call signature; the effect is encoded in the return type of a callable. Generic call signatures express effectful higher-order functions. |
| **Variance & Subtyping** [-> T08](T08-variance-subtyping.md) | `Promise<T>` is covariant in `T`; `Awaited<T>` (TypeScript 4.5) recursively unwraps nested promises, used with `ReturnType` to infer the resolved type of an async function. |
| **Associated Types** [-> T49](T49-associated-types.md) | `Awaited<T>`, `ReturnType<T>`, and `Parameters<T>` are built-in conditional types that extract components of function types, including their effect wrappers. |
| **Functor / Applicative / Monad** [-> T54](T54-functor-applicative-monad.md) | fp-ts encodes `IO`, `Task`, and `Either` as functor/monad instances; `map`, `chain`, and `ap` are the composition operators that replace `await` chaining at the type level. |
| **Never / bottom** [-> T34](T34-never-bottom.md) | A function that always throws can return `never`, signaling to the checker that subsequent code is unreachable. `Result<T, never>` means the operation is infallible — error handling becomes a no-op. |
| **Union types** [-> T02](T02-union-intersection.md) | `Result<T, E>` is a discriminated union; TypeScript's type narrowing on the `ok` discriminant (or `_tag`) gives exhaustiveness checking analogous to Rust's `match`. |

## 5. Gotchas and Limitations

1. **`Promise` is not tracked at the call site** — TypeScript does not warn if a `Promise` is returned by a function but never `await`ed or `.then()`ed; the `@typescript-eslint/no-floating-promises` lint rule fills this gap.
2. **`async` always returns `Promise`** — an `async` function that never `await`s and always returns synchronously still has return type `Promise<T>`; there is no way to express "sync or async" in the native type system without overloading.
3. **`Awaited<T>` flattens nested promises** — `Awaited<Promise<Promise<number>>>` is `number`, which matches runtime behavior but can surprise callers who expect `Promise<number>`.
4. **fp-ts has a steep learning curve** — the full monadic effect stack requires understanding functor/monad combinators; teams unfamiliar with FP often find `neverthrow` or a plain `Result` union more approachable.
5. **Effect library introduces a runtime dependency** — unlike fp-ts's nearly zero-cost abstractions, the Effect library has a runtime with a fiber scheduler; factor this into bundle-size considerations for browser code.
6. **No compiler enforcement of `IO` execution** — `IO<A>` is just `() => A`; the compiler cannot distinguish "this `IO` was run" from "this `IO` was not run". Discipline (or a more opaque type) is required.
7. **Async function coloring** — once a function is `async`, every caller that wants its result must also be `async` (or use `.then()` / `Promise.resolve().then()`). This propagates up the call stack; there is no way to call an async function synchronously without a blocking runtime primitive (which browsers do not expose). This is the same "function coloring" problem as in Rust.
8. **`as unknown as T` is an effect escape hatch** — type assertions bypass the type system entirely, analogous to Lean's `unsafe` or Rust's `unsafe`. Unlike those languages, TypeScript has no syntax to make the unsafe boundary visible at the call site. ESLint rules (`@typescript-eslint/no-explicit-any`, `@typescript-eslint/no-unsafe-*`) can enforce discipline here.
9. **No `?` operator for Result** — TypeScript has no built-in early-return sugar for `Result<T, E>`. Every call site needs explicit narrowing or library combinators. This is more boilerplate than Rust's `?` but keeps the propagation visible.

## Common TypeScript Errors

### `Type 'Promise<T>' is not assignable to type 'T'`

```
Type 'Promise<{ name: string }>' is not assignable to type '{ name: string }'.
```

**Meaning:** You called an `async` function without `await`. Add `await` at the call site, or change the variable's type to `Promise<T>` and chain `.then()`.

### `Property 'value' does not exist on type 'Result<T, E>'`

```
Property 'value' does not exist on type '{ ok: false; error: E }'.
```

**Meaning:** You accessed `.value` without first narrowing the `ok` discriminant. Add `if (result.ok)` or a `switch` before accessing `.value`.

### `Object is possibly 'undefined'` inside an effect pipeline

```
Object is possibly 'undefined'.
```

**Meaning:** Often appears when mixing nullable returns with a `Result` pipeline. Ensure intermediate values are fully unwrapped (`ok()` / `err()`) before passing them into the next stage.

## 6. Use-Case Cross-References

- [-> UC-08](../usecases/UC08-error-handling.md) Typed error effects via `Result<T, E>`, `Either<E, A>`, or `TaskEither<E, A>`
- [-> UC-21](../usecases/UC21-async-concurrency.md) Async concurrency with `Promise<T>`, `Task<A>`, and structured effect types

## Source Anchors

- TypeScript Handbook — [Promises and async/await](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-2-1.html)
- TypeScript 4.5 release notes — `Awaited<T>` utility type
- fp-ts documentation — `IO`, `Task`, `Either`, `TaskEither`, `ReaderTaskEither`
- Effect documentation — `Effect<A, E, R>` and the fiber runtime
- neverthrow README — `Result<T, E>` with `.map`, `.andThen`, `.mapErr`
- `@typescript-eslint/no-floating-promises` — ESLint rule for unhandled promises
