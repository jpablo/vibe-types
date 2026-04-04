# Functor / Monad via fp-ts

> **Since:** fp-ts library (not native TypeScript)

> **Note:** TypeScript has no native higher-kinded types or type class dispatch. The patterns described here are achieved via the fp-ts or Effect library.

## 1. What It Is

TypeScript cannot directly express higher-kinded types (HKT) — you cannot write `Functor<F>` where `F` is itself a type constructor that takes a type parameter. The **fp-ts** library (and the newer **Effect** library, also called effect-ts) work around this by encoding type constructors as URI strings and using declaration merging to associate the URI with its concrete type. This machinery is mostly invisible to end users: you work with concrete types like `Option<A>`, `Either<E, A>`, `Task<A>`, and `TaskEither<E, A>`, and compose them using `pipe` and combinators like `map`, `flatMap` (`chain`), `ap`, and `fold`. `Option<A>` is a type-safe alternative to nullable values. `Either<E, A>` represents a computation that may fail with an error `E` or succeed with `A`. `Task<A>` is a lazy async computation. `TaskEither<E, A>` combines both. The `pipe` function from fp-ts applies a sequence of transformations left-to-right, enabling a flat, readable style that avoids deep nesting.

## 2. What Constraint It Lets You Express

**~Achievable — via fp-ts or Effect, compose effectful computations (optional values, typed errors, async) in a type-safe, chainable pipeline; the compiler tracks the error channel and the success channel separately throughout the composition.**

- `map` transforms the success value while leaving the error channel untouched; the error type is preserved exactly.
- `chain` (flatMap) sequences computations that may themselves fail; the combined error type is the union of both error types.
- `fold` / `match` forces handling of both the success and failure cases before extracting a plain value.
- The compiler rejects using a raw `A` where `Option<A>` is expected, preventing accidental null-like access.

## 3. Minimal Snippet

```typescript
import * as O from "fp-ts/Option";
import * as E from "fp-ts/Either";
import * as TE from "fp-ts/TaskEither";
import { pipe } from "fp-ts/function";

// --- Option: safe nullable alternative ---
const maybeUser: O.Option<string> = O.some("Alice");
const missing:   O.Option<string> = O.none;

const greeting = pipe(
  maybeUser,
  O.map(name => `Hello, ${name}`),            // OK — transforms the value if present
  O.getOrElse(() => "Hello, stranger"),        // OK — provide fallback if absent
);
// greeting: string

const noGreeting = pipe(
  missing,
  O.map(name => `Hello, ${name}`),            // OK — map is a no-op on none
  O.getOrElse(() => "Hello, stranger"),        // OK — fallback fires
);
// noGreeting: "Hello, stranger"

// --- Either: typed error channel ---
type ParseError = { kind: "ParseError"; message: string };

function parseInt(s: string): E.Either<ParseError, number> {
  const n = Number(s);
  return isNaN(n)
    ? E.left({ kind: "ParseError", message: `"${s}" is not a number` })
    : E.right(n);
}

const doubled = pipe(
  parseInt("21"),
  E.map(n => n * 2),            // OK — transforms success value
  E.mapLeft(err => err.message), // OK — transforms error value
);
// doubled: Either<string, number>

// --- TaskEither: async with typed errors ---
type HttpError = { status: number; body: string };

function fetchData(url: string): TE.TaskEither<HttpError, string> {
  return TE.tryCatch(
    () => fetch(url).then(r => r.text()),
    (e): HttpError => ({ status: 500, body: String(e) }),
  );
}

const program = pipe(
  fetchData("https://api.example.com/data"),
  TE.map(text => text.trim()),
  TE.mapLeft(err => `HTTP ${err.status}: ${err.body}`),
  TE.fold(
    errMsg => async () => { console.error(errMsg); return ""; },
    data   => async () => { console.log(data); return data; },
  ),
);
// program: Task<string>  — error channel fully handled, result is plain async
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Effect Tracking** [-> T12](T12-effect-tracking.md) | fp-ts `TaskEither` and Effect's `Effect<R, E, A>` type track effects (async, error) in the type; the type system prevents using a `Task<A>` value as a plain `A` without awaiting. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | `pipe` and combinators like `map`, `chain` are higher-order functions; their types rely on precise callable typing and generic inference to compose correctly without losing type information. |
| **Variance & Subtyping** [-> T08](T08-variance-subtyping.md) | The error channel `E` in `Either<E, A>` is covariant; TypeScript's structural subtyping means a `Either<NetworkError, A>` is assignable to `Either<AppError, A>` when `NetworkError extends AppError`. |

## 5. Gotchas and Limitations

1. **No native HKT support** — the URI-based encoding in fp-ts is an approximation; the compiler cannot enforce that a function written for `Functor<F>` works for *any* functor; you must specialize to a concrete type.
2. **Learning curve** — the `pipe`-centric style and the sheer number of combinators (`chainFirst`, `apSecond`, `sequenceArray`, …) has a steep learning curve for developers coming from imperative TypeScript.
3. **Bundle size** — fp-ts is tree-shakeable but large projects importing many modules will see non-trivial bundle additions; the Effect library is even larger.
4. **Interop with `async`/`await`** — `Task<A>` is a thunk `() => Promise<A>`; mixing `async`/`await` style with fp-ts pipelines is awkward and requires careful discipline to avoid leaking `Promise` without the error channel.
5. **Error union growth** — sequencing many `TaskEither` computations with different error types can produce deeply nested or wide error unions; the `mapLeft` combinator is needed frequently to normalise them.
6. **Effect (effect-ts) vs fp-ts** — Effect offers a richer type (`Effect<R, E, A>` with a context/dependency layer `R`) and better ergonomics but is a larger commitment; fp-ts is smaller and more established.

## 6. Recommended Libraries

- **fp-ts** — the original; widely used, stable, tree-shakeable.
- **Effect (effect-ts)** — modern alternative with dependency injection layer; more ergonomic for large codebases.
- **neverthrow** — lightweight `Result<T, E>` type only; good for teams that only want typed errors without full FP.

## 7. Use-Case Cross-References

- [-> UC-08](../usecases/UC08-error-handling.md) Type-safe error handling with typed error channels instead of thrown exceptions
- [-> UC-21](../usecases/UC21-async-concurrency.md) Composing async computations with tracked error types and lazy evaluation
