# Functor, Applicative, and Monad

> **Since:** fp-ts library (not native TypeScript); built-in analogues (Array, Promise) since ES5/ES6

> **Note:** TypeScript has no native higher-kinded types or type-class dispatch. The full abstraction hierarchy requires fp-ts or Effect. However, TypeScript's built-in types encode these patterns without naming them explicitly.

## What It Is

**Functor**, **Applicative**, and **Monad** form a hierarchy of abstractions for working with values in a computational context (`F<A>`).

- A **Functor** provides `map`: transform the value inside a context without changing the context's shape.
- An **Applicative** extends Functor with `pure` (lift a plain value into the context) and `ap` (apply a function inside a context to a value inside a context). Crucially, Applicative allows *independent* computations — it can accumulate errors rather than short-circuiting.
- A **Monad** extends Applicative with `flatMap` / `chain`: sequence computations where each step depends on the previous result, short-circuiting on failure.

TypeScript cannot directly express higher-kinded types (HKT) — you cannot write `Functor<F>` where `F` is itself a type constructor. The **fp-ts** library (and the newer **Effect** library) work around this with URI-based encoding. This machinery is mostly invisible to end users: you work with concrete types like `Option<A>`, `Either<E, A>`, `Task<A>`, and `TaskEither<E, A>`, and compose them with `pipe` and combinators like `map`, `chain`, `ap`, and `fold`.

Built-in TypeScript types already encode these patterns without naming them:
- `Array.prototype.map` / `Array.prototype.flatMap` — Functor and Monad over sequences
- `Promise.prototype.then` — Monad over async computations (`then` is both `map` and `flatMap`)
- Optional chaining (`?.`) — approximates `Option.map` / `Option.flatMap` inline

## What Constraint It Lets You Express

**~Achievable — via fp-ts or Effect, compose effectful computations (optional values, typed errors, async) in a type-safe, chainable pipeline; the compiler tracks the error channel and the success channel separately throughout the composition.**

- `map` transforms the success value while leaving the error channel untouched; the error type is preserved exactly.
- `chain` (flatMap) sequences computations that may themselves fail; the combined error type is the union of both error types.
- `ap` combines independent computations; with `Validated`/`These`, errors accumulate rather than short-circuiting.
- `fold` / `match` forces handling of both the success and failure cases before extracting a plain value.
- The compiler rejects using a raw `A` where `Option<A>` is expected, preventing accidental null-like access.

## Beginner Mental Model

Think of `F<A>` as a **container or context**: `Option<A>` is a box that might be empty, `Either<E, A>` is a box holding either a value or an error, `Task<A>` is a box containing a deferred async computation.

- **Functor (`map`)**: transform the value inside without opening the box manually — if the box is empty/failed, `map` is a no-op.
- **Applicative (`ap`, `pure`)**: combine multiple *independent* boxes — run both sides, collect both errors.
- **Monad (`chain`/`flatMap`)**: chain steps where each step *depends on* the previous result — any failure short-circuits the rest.

`pipe` from fp-ts is the syntactic glue: it applies a sequence of transformations left-to-right, replacing nested function calls with a flat, readable chain.

Coming from `async/await`: `await` is essentially `flatMap` for Promises. `then` on a Promise is `map` when you return a plain value, and `flatMap` when you return another Promise. `async/await` is TypeScript's built-in do-notation for the Promise monad.

## Minimal Snippet

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
  O.map(name => `Hello, ${name}`),            // Functor: transforms the value if present
  O.getOrElse(() => "Hello, stranger"),        // extract with fallback
);
// greeting: string

const noGreeting = pipe(
  missing,
  O.map(name => `Hello, ${name}`),            // map is a no-op on none
  O.getOrElse(() => "Hello, stranger"),        // fallback fires
);
// noGreeting: "Hello, stranger"

// --- Either: typed error channel ---
type ParseError = { kind: "ParseError"; message: string };

function parseIntSafe(s: string): E.Either<ParseError, number> {
  const n = Number(s);
  return isNaN(n)
    ? E.left({ kind: "ParseError", message: `"${s}" is not a number` })
    : E.right(n);
}

const doubled = pipe(
  parseIntSafe("21"),
  E.map(n => n * 2),             // Functor: transforms success value
  E.mapLeft(err => err.message), // Functor over the error channel
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

## Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Effect Tracking** [-> T12](T12-effect-tracking.md) | fp-ts `TaskEither` and Effect's `Effect<R, E, A>` type track effects (async, error) in the type; the type system prevents using a `Task<A>` value as a plain `A` without awaiting. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | `pipe` and combinators like `map`, `chain` are higher-order functions; their types rely on precise callable typing and generic inference to compose correctly without losing type information. |
| **Variance & Subtyping** [-> T08](T08-variance-subtyping.md) | The error channel `E` in `Either<E, A>` is covariant; TypeScript's structural subtyping means `Either<NetworkError, A>` is assignable to `Either<AppError, A>` when `NetworkError extends AppError`. |
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | Without HKT, you cannot write a single `map<F, A, B>(fa: F<A>, f: (a: A) => B): F<B>` that works for any functor; each type has its own `map`. Partial workarounds use overloaded functions or conditional types. |
| **Null Safety** [-> T13](T13-null-safety.md) | `Option<A>` is a type-safe alternative to `T \| null \| undefined`; optional chaining (`?.`) is the inline equivalent of `Option.flatMap` but doesn't compose as cleanly. |

## Gotchas and Limitations

1. **No native HKT support** — the URI-based encoding in fp-ts is an approximation; the compiler cannot enforce that a function written for `Functor<F>` works for *any* functor; you must specialize to a concrete type.

2. **Applicative vs Monad** — `Applicative` allows independent computations that can be parallelized or accumulate errors; `Monad` implies sequencing that short-circuits. Using `chain`/`flatMap` when `ap` suffices over-constrains your code. For error accumulation use `E.bindTo`/`E.bind` with `Applicative` sequencing, or `cats.Validated`-equivalent `fp-ts/These`.

3. **No automatic Applicative error accumulation** — `chain` in fp-ts short-circuits on the first `left`. For accumulating multiple validation errors, use `fp-ts/These` or the `sequenceT`/`sequenceS` combinators with `Applicative`.

4. **Learning curve** — the `pipe`-centric style and the sheer number of combinators (`chainFirst`, `apSecond`, `sequenceArray`, …) has a steep learning curve for developers coming from imperative TypeScript.

5. **Bundle size** — fp-ts is tree-shakeable but large projects importing many modules will see non-trivial bundle additions; the Effect library is even larger.

6. **Interop with `async`/`await`** — `Task<A>` is a thunk `() => Promise<A>`; mixing `async`/`await` style with fp-ts pipelines is awkward and requires careful discipline to avoid leaking `Promise` without the error channel.

7. **Error union growth** — sequencing many `TaskEither` computations with different error types can produce deeply nested or wide error unions; `mapLeft` is needed frequently to normalise them.

8. **Law compliance is not enforced by the compiler** — nothing prevents writing an `Option`-like type whose `map` violates the identity law. fp-ts provides `fp-ts-laws` for testing law compliance, but it is opt-in.

9. **Effect (effect-ts) vs fp-ts** — Effect offers a richer type (`Effect<R, E, A>` with a context/dependency layer `R`) and better ergonomics but is a larger commitment; fp-ts is smaller and more established.

## `pipe` + `chain` as Do-Notation

Scala's for-comprehensions and Lean's `do`-notation both desugar to `flatMap`/`bind`. TypeScript has no such syntax for arbitrary monads, but two patterns serve as equivalents:

**1. `async/await` — built-in do-notation for Promise**

```typescript
// This async/await block:
async function processOrder(orderId: string): Promise<Receipt> {
  const order   = await findOrder(orderId);   // flatMap
  const payment = await chargeCard(order.total); // flatMap
  const receipt = await generateReceipt(order, payment); // map
  return receipt;
}

// Is equivalent to:
function processOrderChained(orderId: string): Promise<Receipt> {
  return findOrder(orderId)
    .then(order => chargeCard(order.total)
      .then(payment => generateReceipt(order, payment)));
}
```

`async`/`await` is TypeScript's do-notation for the Promise monad. Each `await` is a monadic bind — an unhandled rejection short-circuits the chain, exactly like `None` short-circuits `Option.chain`.

**2. `pipe` + `chain` — explicit do-notation for fp-ts types**

```typescript
import * as TE from "fp-ts/TaskEither";
import { pipe } from "fp-ts/function";

// Monadic pipeline using pipe + chain:
const result = pipe(
  findUser(userId),                         // TE.TaskEither<DbError, User>
  TE.chain(user => fetchProfile(user.id)),  // flatMap: User -> TE<..., Profile>
  TE.chain(profile => enrich(profile)),     // flatMap: Profile -> TE<..., EnrichedProfile>
  TE.map(enriched => enriched.summary),    // map: EnrichedProfile -> string
);

// Equivalent desugaring (what pipe + chain expand to):
// findUser(userId)
//   .then(userResult => userResult._tag === "Left" ? userResult : fetchProfile(userResult.right.id))
//   .then(profileResult => profileResult._tag === "Left" ? profileResult : enrich(profileResult.right))
//   ...
```

Unlike `async/await`, `pipe`+`chain` keeps the error channel typed throughout. Use `TE.Do` + `TE.bind` for a style closer to for-comprehensions when results of multiple steps are needed together:

```typescript
const program = pipe(
  TE.Do,
  TE.bind("user",    () => findUser(userId)),
  TE.bind("profile", ({ user }) => fetchProfile(user.id)),
  TE.map(({ user, profile }) => `${user.name}: ${profile.bio}`),
);
```

## Built-In Functor / Monad Patterns

TypeScript's standard library already encodes these patterns without naming them:

```typescript
// Array as Functor and Monad
const doubled = [1, 2, 3].map(n => n * 2);           // Functor
const flat    = [[1, 2], [3, 4]].flatMap(xs => xs);  // Monad (flatten)
const pairs   = [1, 2].flatMap(a => [10, 20].map(b => a + b)); // [11, 21, 12, 22]

// Promise as Monad (then = map + flatMap)
const result = fetch("/api/data")
  .then(r => r.json())           // flatMap (then flattens Promises automatically)
  .then(data => data.name)      // map (plain value, not a Promise)
  .catch(err => "fallback");    // handles the error channel

// Optional chaining as inline Option.flatMap
const city = user?.address?.city ?? "unknown";
// Equivalent fp-ts:
// pipe(optUser, O.chain(u => u.address), O.chain(a => a.city), O.getOrElse(() => "unknown"))
```

## Example A — Applicative Validation (Error Accumulation)

Unlike `chain` (which short-circuits), Applicative combinators can accumulate multiple errors. fp-ts's `sequenceS` runs independent validations and collects all failures:

```typescript
import * as E from "fp-ts/Either";
import { sequenceS } from "fp-ts/Apply";

type ValidationError = string;
type V<A> = E.Either<ValidationError[], A>;

function validateName(name: string): V<string> {
  return name.length >= 2
    ? E.right(name)
    : E.left([`Name too short: "${name}"`]);
}

function validateAge(age: number): V<number> {
  return age >= 0 && age <= 150
    ? E.right(age)
    : E.left([`Age out of range: ${age}`]);
}

const applicativeValidation = E.getApplicativeValidation({
  concat: (a: ValidationError[], b: ValidationError[]) => [...a, ...b],
});

const result = sequenceS(applicativeValidation)({
  name: validateName(""),    // fails
  age:  validateAge(200),   // also fails
});
// Left(["Name too short: \"\"", "Age out of range: 200"])
// Both errors accumulated — unlike chain, which would stop at the first

const ok = sequenceS(applicativeValidation)({
  name: validateName("Alice"),
  age:  validateAge(30),
});
// Right({ name: "Alice", age: 30 })
```

## Example B — Generic Monadic Pipeline

Without HKT, you cannot write a single function generic over *any* monad. But you can write functions generic over the *concrete type's* operations by accepting them as parameters:

```typescript
import * as O from "fp-ts/Option";
import * as E from "fp-ts/Either";
import { pipe } from "fp-ts/function";

// Generic pipeline over Option
function parseAndHalve(
  parse: (s: string) => O.Option<number>,
  halve: (n: number) => O.Option<number>,
) {
  return (input: string): O.Option<number> =>
    pipe(input, parse, O.chain(halve));
}

const parseNat = (s: string): O.Option<number> => {
  const n = parseInt(s, 10);
  return isNaN(n) ? O.none : O.some(n);
};
const halve = (n: number): O.Option<number> =>
  n % 2 === 0 ? O.some(n / 2) : O.none;

const transform = parseAndHalve(parseNat, halve);
console.log(transform("42"));  // Some(21)
console.log(transform("7"));   // None (odd)
console.log(transform("abc")); // None (parse failure)
```

For *true* HKT abstraction, Effect's approach uses a unified `Effect<Requirements, Error, Value>` type that subsumes Option, Either, and Task into one — avoiding the need for separate `Option.chain`, `Either.chain`, `TaskEither.chain` by unifying them under a single `Effect.flatMap`.

## Recommended Libraries

- **fp-ts** — the original; widely used, stable, tree-shakeable.
- **Effect (effect-ts)** — modern alternative with dependency injection layer; more ergonomic for large codebases.
- **neverthrow** — lightweight `Result<T, E>` type only; good for teams that only want typed errors without full FP.

## Use-Case Cross-References

- [-> UC-01](../usecases/UC01-invalid-states.md) Monadic chaining in `Option`/`Either` prevents operating on absent or invalid values
- [-> UC-08](../usecases/UC08-error-handling.md) Type-safe error handling with typed error channels instead of thrown exceptions
- [-> UC-21](../usecases/UC21-async-concurrency.md) Composing async computations with tracked error types and lazy evaluation

## Source Anchors

- [fp-ts documentation](https://gcanti.github.io/fp-ts/)
- [fp-ts Option module](https://gcanti.github.io/fp-ts/modules/Option.ts.html)
- [fp-ts Either module](https://gcanti.github.io/fp-ts/modules/Either.ts.html)
- [Effect documentation](https://effect.website/docs/getting-started/introduction)
- *Functional design: combinators* — Giulio Canti's blog series on fp-ts patterns
